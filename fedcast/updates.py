"""What is new at the sources since the latest snapshot was pulled.

One cheap request per source (latest observation only), compared with what the snapshot holds. The result
tells the owner whether a new pull would change the evidence, and what exactly has arrived: a macro release,
a new statement or minutes, a speech, or just daily market moves.
"""

from __future__ import annotations

import email.utils
import re
from datetime import datetime, timezone

from fedcast import config
from fedcast.data import http, sources
from fedcast.snapshot import Snapshot

_RSS_ITEM = re.compile(r"<item>(.*?)</item>", re.S)
LABELS = {"PCEPILFE": "Core PCE", "CPILFESL": "Core CPI", "UNRATE": "Unemployment", "PAYEMS": "Payrolls",
          "ICSA": "Jobless claims", "T5YIE": "5y breakeven", "DGS2": "2-year yield", "NFCI": "NFCI"}


def _feed_latest(url: str) -> tuple[str, str] | None:
    feed = http.get_text(url)
    items = _RSS_ITEM.findall(feed)
    if not items:
        return None
    item = items[0]
    pub = email.utils.parsedate_to_datetime(sources._rss_field(item, "pubDate")).date().isoformat()
    return pub, sources._rss_field(item, "title")


def check(snap: Snapshot) -> dict:
    changes: list[dict] = []
    notes: list[str] = []
    key = config.secret("FRED_API_KEY")
    today = config.today()

    def add(kind: str, label: str, before: str, now: str, detail: str = "") -> None:
        changes.append({"kind": kind, "label": label, "snapshot": before, "now": now, "detail": detail})

    for sid in config.FRED_SERIES:
        item = f"fred.{sid}"
        if item not in snap.items or not key:
            continue
        try:
            before = next(o for o in snap.get(item)["observations"] if o["value"] is not None)
            now = sources.fetch_fred(sid, key, today, n_obs=1)["observations"][0]
        except Exception as exc:
            notes.append(f"{sid}: {type(exc).__name__}")
            continue
        if now["date"] > before["date"]:
            kind = "release" if sid in ("PCEPILFE", "CPILFESL", "UNRATE", "PAYEMS", "ICSA") else "market"
            add(kind, LABELS.get(sid, sid), before["date"], now["date"], f"{before['value']} -> {now['value']}")

    try:
        effr_now = sources.fetch_effr(1)["latest"]
        effr_before = snap.get("effr")["latest"]
        if effr_now["date"] > effr_before["date"]:
            add("market", "Overnight rate (EFFR)", effr_before["date"], effr_now["date"], f"{effr_before['effr']} -> {effr_now['effr']}")
    except Exception as exc:
        notes.append(f"EFFR: {type(exc).__name__}")

    for item in sorted(i for i in snap.items if i.startswith("futures.")):
        try:
            c = snap.get(item)
            y, m = (int(x) for x in c["contract_month"].split("-"))
            now = sources.fetch_zq(y, m)
            if now["price"] != c["price"]:
                add("market", f"Futures {c['symbol']}", str(c["price"]), str(now["price"]),
                    f"implied {100 - c['price']:.3f}% -> {100 - now['price']:.3f}%")
        except Exception as exc:
            notes.append(f"{item}: {type(exc).__name__}")

    try:
        sp = snap.get("fed.speeches") if "fed.speeches" in snap.items else None
        latest = _feed_latest("https://www.federalreserve.gov/feeds/speeches.xml")
        if sp and latest and (not sp["speeches"] or latest[0] > max(x["date"] for x in sp["speeches"])):
            add("fed", "New speech", max(x["date"] for x in sp["speeches"]) if sp["speeches"] else "none", latest[0], latest[1])
    except Exception as exc:
        notes.append(f"speeches: {type(exc).__name__}")

    try:
        latest = _feed_latest("https://www.federalreserve.gov/feeds/press_monetary.xml")
        docs = [i for i in snap.items if i.startswith(("fed.statement.", "fed.minutes."))]
        newest_doc = max(i[-10:] for i in docs) if docs else "none"
        if latest and latest[0] > snap.as_of.isoformat():
            add("fed", "Monetary policy press release", newest_doc, latest[0], latest[1])
    except Exception as exc:
        notes.append(f"press releases: {type(exc).__name__}")

    return {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "snapshot": snap.hash[:12],
            "snapshot_as_of": snap.as_of.isoformat(), "changes": changes, "notes": notes,
            "releases": sum(1 for c in changes if c["kind"] == "release"),
            "fed": sum(1 for c in changes if c["kind"] == "fed"),
            "market": sum(1 for c in changes if c["kind"] == "market")}
