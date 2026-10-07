"""Prediction-market model: the most recent hand-entered odds for the next meeting, normalised.

Thin and fee-distorted compared with the futures, so it enters the pool at a small weight; its value
is as an independent read of the same question from a different crowd.
"""

from __future__ import annotations

from fedcast.human.prediction_markets import MarketOdds
from fedcast.snapshot import Snapshot


def prediction_market(snap: Snapshot) -> dict:
    meeting = snap.get("calendar")["next_meeting"]
    entries = [MarketOdds(**snap.get(i)) for i in snap.items if i.startswith("human.pm.")]
    entries = [e for e in entries if e.meeting.isoformat() == meeting and e.status == "active"]
    if not entries:
        raise ValueError(f"no prediction-market odds entered for the {meeting} meeting")
    latest = max(entries, key=lambda e: e.observed_at)
    return {
        "model": "prediction_market",
        "meeting": meeting,
        "venue": latest.venue,
        "observed_at": latest.observed_at.isoformat(),
        "raw_prices_pct": latest.prices,
        "raw_total_pct": round(sum(latest.prices.values()), 1),
        "volume_usd": latest.volume_usd,
        "probabilities": latest.normalised(),
        "evidence": ["calendar", f"human.pm.{latest.id}"],
        "snapshot_hash": snap.hash,
    }
