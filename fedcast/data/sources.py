"""Fetchers for market and macro data. Each returns plain JSON-able content for a snapshot item."""

from __future__ import annotations

import email.utils
import html as htmllib
import re
from datetime import date

from fedcast.data import http

_MONTH_CODES = "FGHJKMNQUVXZ"


# --- fed funds futures (Yahoo delayed quotes) --------------------------------------------

def zq_symbol(year: int, month: int) -> str:
    return f"ZQ{_MONTH_CODES[month - 1]}{year % 100:02d}.CBT"


def fetch_zq(year: int, month: int) -> dict:
    symbol = zq_symbol(year, month)
    data = http.get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                         {"range": "5d", "interval": "1d"})
    meta = data["chart"]["result"][0]["meta"]
    return {
        "symbol": symbol,
        "contract_month": f"{year}-{month:02d}",
        "price": meta["regularMarketPrice"],
        "price_time_unix": meta["regularMarketTime"],
        "volume": meta.get("regularMarketVolume"),
    }


# --- effective fed funds rate and target range (NY Fed) -----------------------------------

def fetch_effr(last_n: int = 10) -> dict:
    data = http.get_json(f"https://markets.newyorkfed.org/api/rates/unsecured/effr/last/{last_n}.json")
    rows = [{"date": r["effectiveDate"], "effr": r["percentRate"],
             "target_low": r["targetRateFrom"], "target_high": r["targetRateTo"]}
            for r in data["refRates"]]
    return {"latest": rows[0], "history": rows}


# --- FRED with vintage control -------------------------------------------------------------

def fetch_fred(series_id: str, api_key: str, as_of: date, n_obs: int = 36,
               observation_start: str | None = None) -> dict:
    """Latest `n_obs` observations *as they were known on* `as_of` (ALFRED real-time period)."""
    params = {
        "series_id": series_id, "api_key": api_key, "file_type": "json",
        "realtime_start": as_of.isoformat(), "realtime_end": as_of.isoformat(),
        "sort_order": "desc", "limit": str(n_obs),
    }
    if observation_start:
        params["observation_start"] = observation_start
    data = http.get_json("https://api.stlouisfed.org/fred/series/observations", params, user_agent=http.PLAIN_UA)
    obs = [{"date": o["date"], "value": None if o["value"] == "." else float(o["value"])}
           for o in data["observations"]]
    return {"series_id": series_id, "vintage": as_of.isoformat(), "observations": obs}


def fetch_target_rate_path(api_key: str, as_of: date, start: str = "1990-01-01") -> dict:
    """The policy target as a list of change points: DFEDTAR (single target, to 2008-12-15) then DFEDTARU
    (upper bound of the range, from 2008-12-16). Daily values are collapsed to the days the target changed."""
    old = fetch_fred("DFEDTAR", api_key, as_of, n_obs=100000, observation_start=start)["observations"]
    new = fetch_fred("DFEDTARU", api_key, as_of, n_obs=100000, observation_start="2008-12-16")["observations"]
    daily = sorted(((o["date"], o["value"]) for o in old + new if o["value"] is not None))
    changes, last = [], None
    for d, v in daily:
        if v != last:
            changes.append({"date": d, "target": v})
            last = v
    return {"series": ["DFEDTAR", "DFEDTARU"], "measure": "target rate, upper bound of the range since 2008-12-16",
            "changes": changes}


# --- Fed documents ---------------------------------------------------------------------------

_ARTICLE = re.compile(r'<div id="article"[^>]*>(.*?)<div[^>]+(?:id="lastUpdate"|class="[^"]*lastUpdate)', re.S)
_TAGS = re.compile(r"<[^>]+>")


def html_to_text(page: str) -> str:
    m = _ARTICLE.search(page)
    body = m.group(1) if m else page
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S).replace("-->", " ")
    body = re.sub(r"</(p|div|h\d|li|tr)>|<br\s*/?>", "\n", body)
    text = htmllib.unescape(_TAGS.sub(" ", body))
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def fetch_document(url: str) -> dict:
    return {"url": url, "text": html_to_text(http.get_text(url))}


_PAGE_NO = re.compile(r"^\s*Page \d+ of \d+\s*$")


def strip_running_headers(text: str) -> str:
    """Remove page numbers and running headers (short lines repeated on many pages), so that a sentence
    broken across a page break is contiguous again and can be quoted verbatim."""
    lines = text.splitlines()
    from collections import Counter

    counts = Counter(ln.strip() for ln in lines if ln.strip())
    repeated = {ln for ln, n in counts.items() if n >= 3 and len(ln) < 90}
    kept = [ln for ln in lines if not _PAGE_NO.match(ln) and ln.strip() not in repeated]
    out = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def fetch_presconf(pdf_url: str) -> dict:
    """The press-conference transcript PDF, as text (code extraction, nothing summarised)."""
    from fedcast.human.extract import extract_text

    return {"url": pdf_url, "text": strip_running_headers(extract_text("transcript.pdf", http.get(pdf_url)))}


_CELL = re.compile(r"<t[hd].*?</t[hd]>", re.S)
_ROW = re.compile(r"<tr.*?</tr>", re.S)
_TABLE = re.compile(r"<table.*?</table>", re.S)
_SEP_VARS = ("Change in real GDP", "Unemployment rate", "PCE inflation", "Core PCE inflation", "Federal funds rate")


def parse_sep(page: str) -> dict:
    """Median projections by variable and year from the SEP table, plus the previous SEP's medians."""
    for tm in _TABLE.finditer(page):
        table = tm.group(0)
        if "Federal funds rate" not in table or "Median" not in table:
            continue
        rows = []
        for r in _ROW.findall(table):
            cells = [htmllib.unescape(_TAGS.sub("", c)).strip() for c in _CELL.findall(r)]
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)
        years = [c for c in rows[1] if c.isdigit() or c.lower() == "longer run"]
        years = years[:next((i for i, y in enumerate(years[1:], 1) if y == years[0]), len(years))]  # first block only
        medians, previous, current_var = {}, {}, None
        for cells in rows[2:]:
            name = re.sub(r"\d+$", "", cells[0]).strip()
            nums = []
            for c in cells[1:]:
                try:
                    nums.append(float(c))
                except ValueError:
                    break
            if name in _SEP_VARS:
                current_var = name
                medians[name] = {years[i]: v for i, v in enumerate(nums[:len(years)])}
            elif current_var and "projection" in name.lower():
                previous[current_var] = {years[i]: v for i, v in enumerate(nums[:len(years)])}
                current_var = None
        return {"years": years, "medians": medians, "previous": previous}
    raise ValueError("no projections table found")


def fetch_sep(url: str) -> dict:
    return {"url": url, **parse_sep(http.get_text(url))}


_RSS_ITEM = re.compile(r"<item>(.*?)</item>", re.S)


def _rss_field(item: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", item, re.S)
    return htmllib.unescape(m.group(1).strip()) if m else ""


def fetch_speeches(since: date, limit: int = 15, max_chars: int = 20000) -> dict:
    """Speeches by Board members since `since` (the previous decision), from the Fed's RSS feed, as text."""
    feed = http.get_text("https://www.federalreserve.gov/feeds/speeches.xml")
    out = []
    for item in _RSS_ITEM.findall(feed):
        pub = email.utils.parsedate_to_datetime(_rss_field(item, "pubDate")).date()
        if pub < since:
            continue
        title, link = _rss_field(item, "title"), _rss_field(item, "link")
        speaker = title.split(",")[0].strip()
        out.append({"date": pub.isoformat(), "speaker": speaker, "title": title.split(",", 1)[-1].strip(),
                    "url": link, "text": html_to_text(http.get_text(link))[:max_chars]})
        if len(out) >= limit:
            break
    return {"feed": "https://www.federalreserve.gov/feeds/speeches.xml", "since": since.isoformat(), "speeches": out}
