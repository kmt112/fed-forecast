"""Fetchers for market and macro data. Each returns plain JSON-able content for a snapshot item."""

from __future__ import annotations

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

def fetch_fred(series_id: str, api_key: str, as_of: date, n_obs: int = 36) -> dict:
    """Latest `n_obs` observations *as they were known on* `as_of` (ALFRED real-time period)."""
    data = http.get_json("https://api.stlouisfed.org/fred/series/observations", {
        "series_id": series_id, "api_key": api_key, "file_type": "json",
        "realtime_start": as_of.isoformat(), "realtime_end": as_of.isoformat(),
        "sort_order": "desc", "limit": str(n_obs),
    })
    obs = [{"date": o["date"], "value": None if o["value"] == "." else float(o["value"])}
           for o in data["observations"]]
    return {"series_id": series_id, "vintage": as_of.isoformat(), "observations": obs}


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
