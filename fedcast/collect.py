"""Build a snapshot from live sources. The only module that touches the network."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fedcast import config
from fedcast.data import fomc_calendar, sources
from fedcast.human.documents import load_documents
from fedcast.snapshot import Item, Snapshot


def _add_months(year: int, month: int, k: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def build(as_of: date) -> Snapshot:
    snap = Snapshot(as_of)

    def attempt(item_id: str, kind: str, source: str, fn) -> None:
        try:
            snap.add(Item.make(item_id, kind, source, fn()))
        except Exception as exc:  # a missing source is recorded, never silently skipped
            snap.missing[item_id] = f"{type(exc).__name__}: {exc}"

    meetings = fomc_calendar.fetch()
    nxt = fomc_calendar.next_meeting(meetings, as_of)
    past = [m for m in meetings if m.decision_date < as_of]
    snap.add(Item.make("calendar", "calendar", fomc_calendar.URL, {
        "next_meeting": nxt.decision_date.isoformat(),
        "meetings": [m.decision_date.isoformat() for m in meetings
                     if abs((m.decision_date - as_of).days) < 400],
    }))

    attempt("effr", "effr", "markets.newyorkfed.org/api/rates/unsecured/effr", sources.fetch_effr)

    # contracts from the current month through the month after the meeting
    y, m = as_of.year, as_of.month
    end = _add_months(nxt.decision_date.year, nxt.decision_date.month, 1)
    while (y, m) <= end:
        sym = sources.zq_symbol(y, m)
        attempt(f"futures.{sym.split('.')[0]}", "futures", f"finance.yahoo.com/quote/{sym}",
                lambda y=y, m=m: sources.fetch_zq(y, m))
        y, m = _add_months(y, m, 1)

    key = config.secret("FRED_API_KEY")
    for sid in config.FRED_SERIES:
        if key:
            attempt(f"fred.{sid}", "fred", f"api.stlouisfed.org/fred/series/observations?series_id={sid}",
                    lambda sid=sid: sources.fetch_fred(sid, key, as_of))
        else:
            snap.missing[f"fred.{sid}"] = "FRED_API_KEY not set in .env"

    statements = [m for m in past if m.statement_url][-2:]  # latest and previous, for the word diff
    last_minutes = next((m for m in reversed(past) if m.minutes_url), None)
    for st in statements:
        attempt(f"fed.statement.{st.decision_date}", "document", st.statement_url,
                lambda st=st: sources.fetch_document(st.statement_url))
    if last_minutes:
        attempt(f"fed.minutes.{last_minutes.decision_date}", "document", last_minutes.minutes_url,
                lambda: sources.fetch_document(last_minutes.minutes_url))
    for doc in load_documents(config.ROOT / "human" / "documents"):
        if doc.status == "active":
            snap.add(Item.make(f"human.doc.{doc.id}", "human_document", f"human/documents/{doc.id}.md",
                               doc.model_dump(mode="json")))
    return snap
