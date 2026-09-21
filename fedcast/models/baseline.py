"""Market-implied baseline computed from a snapshot and nothing else."""

from __future__ import annotations

from datetime import date

from fedcast.data.sources import zq_symbol
from fedcast.models.futures_implied import (bucket_probabilities, implied_change_bp,
                                            implied_change_next_month_bp)
from fedcast.snapshot import Snapshot


def market_implied(snap: Snapshot) -> dict:
    cal = snap.get("calendar")
    meeting = date.fromisoformat(cal["next_meeting"])
    rate_before = snap.get("effr")["latest"]["effr"]

    ny, nm = (meeting.year + 1, 1) if meeting.month == 12 else (meeting.year, meeting.month + 1)
    next_month_has_meeting = any(d.startswith(f"{ny}-{nm:02d}") for d in cal["meetings"])

    used: list[str] = ["calendar", "effr"]
    if not next_month_has_meeting:
        item = f"futures.{zq_symbol(ny, nm).split('.')[0]}"
        change = implied_change_next_month_bp(snap.get(item)["price"], rate_before)
        method = "next_month_contract"
    else:
        item = f"futures.{zq_symbol(meeting.year, meeting.month).split('.')[0]}"
        change = implied_change_bp(meeting, snap.get(item)["price"], rate_before)
        method = "meeting_month_contract"
    used.append(item)

    return {"model": "market_implied", "method": method, "meeting": meeting.isoformat(),
            "rate_before": rate_before, "expected_change_bp": round(change, 2),
            "probabilities": bucket_probabilities(change), "evidence": used,
            "snapshot_hash": snap.hash}
