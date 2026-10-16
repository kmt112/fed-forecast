"""Prediction-market model: the most recent hand-entered odds for the next meeting, normalised.

Thin and fee-distorted compared with the futures, so it enters the pool at a small weight; its value
is as an independent read of the same question from a different crowd.
"""

from __future__ import annotations

from fedcast.human.prediction_markets import MarketOdds
from fedcast.snapshot import Snapshot

# Odds older than this at snapshot time are ignored: a hand-entered price from two weeks ago says nothing
# about today's market, and letting it linger in the pool would be a silent, stale nudge (audit 2026-10-16).
MAX_AGE_DAYS = 7


def prediction_market(snap: Snapshot) -> dict:
    meeting = snap.get("calendar")["next_meeting"]
    entries = [MarketOdds(**snap.get(i)) for i in snap.items if i.startswith("human.pm.")]
    entries = [e for e in entries if e.meeting.isoformat() == meeting and e.status == "active"]
    if not entries:
        raise ValueError(f"no prediction-market odds entered for the {meeting} meeting")
    latest = max(entries, key=lambda e: e.observed_at)
    age = (snap.as_of - latest.observed_at.date()).days
    if age > MAX_AGE_DAYS:
        raise ValueError(f"latest odds ({latest.id}) were observed {age} days before the snapshot; "
                         f"older than {MAX_AGE_DAYS} days, so not used. Enter fresh odds.")
    return {
        "model": "prediction_market",
        "meeting": meeting,
        "venue": latest.venue,
        "observed_at": latest.observed_at.isoformat(),
        "age_days": age,
        "raw_prices_pct": latest.prices,
        "raw_total_pct": round(sum(latest.prices.values()), 1),
        "volume_usd": latest.volume_usd,
        "probabilities": latest.normalised(),
        "evidence": ["calendar", f"human.pm.{latest.id}"],
        "snapshot_hash": snap.hash,
    }
