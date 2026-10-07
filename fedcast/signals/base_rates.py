"""Base rates: what the Fed has actually done at scheduled meetings since 1994.

Spec (pre-registered 2026-10-02):
  decision at a meeting   change in the target (upper bound of the range since Dec 2008) from the day before
                          the decision to the day after, in bp; bucketed cut / hold / hike
  intermeeting moves      target changes on days that were not scheduled decision days
  conditional table       next scheduled decision given the previous scheduled decision (cut / hold / hike):
                          the Fed's tendency to continue, pause or reverse
  surprise evidence       share of moves of 50 bp or more, and reversals (a cut straight after a hike or the
                          other way round), which is what the surprise floor stands in for
What this cannot measure: how often the Fed surprised the *market*. That needs historical futures prices.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from datetime import date, timedelta

from fedcast.snapshot import Snapshot

EVIDENCE = ["history.meetings", "history.target_rate"]


def _bucket(change_bp: float) -> str:
    return "hike" if change_bp > 0 else "cut" if change_bp < 0 else "hold"


def decisions(meetings: list[dict], path: list[dict]) -> tuple[list[dict], list[dict]]:
    """Scheduled decisions and intermeeting moves, from meeting dates and a target-rate change path.

    `path` is [{"date", "target"}] at change points, oldest first; the target is in force from that date.
    """
    dates = [date.fromisoformat(p["date"]) for p in path]
    targets = [p["target"] for p in path]

    def target_on(d: date) -> float | None:
        i = bisect_left(dates, d + timedelta(days=1)) - 1
        return targets[i] if i >= 0 else None

    scheduled_dates = {date.fromisoformat(m["date"]) for m in meetings if m["scheduled"]}
    decided = []
    for m in meetings:
        d = date.fromisoformat(m["date"])
        before, after = target_on(d - timedelta(days=1)), target_on(d + timedelta(days=1))
        if before is None or after is None:
            continue
        change = round((after - before) * 100, 1)
        decided.append({"date": m["date"], "scheduled": m["scheduled"], "change_bp": change, "decision": _bucket(change)})
    intermeeting = []
    for i in range(1, len(path)):
        d = dates[i]
        near = any(abs((d - s).days) <= 1 for s in scheduled_dates)
        if not near:
            intermeeting.append({"date": path[i]["date"], "change_bp": round((targets[i] - targets[i - 1]) * 100, 1)})
    return decided, intermeeting


def compute(snap: Snapshot) -> dict:
    cutoff = (snap.as_of - timedelta(days=3)).isoformat()  # a decision needs the next day's target to be published
    meetings = [m for m in snap.get("history.meetings")["meetings"] if m["date"] <= cutoff]
    path = snap.get("history.target_rate")["changes"]
    decided, intermeeting = decisions(meetings, path)
    sched = [d for d in decided if d["scheduled"]]
    if len(sched) < 50:
        raise ValueError("too few scheduled decisions in the history")

    overall = Counter(d["decision"] for d in sched)
    n = len(sched)
    cond: dict[str, Counter] = {"cut": Counter(), "hold": Counter(), "hike": Counter()}
    for prev, nxt in zip(sched, sched[1:]):
        cond[prev["decision"]][nxt["decision"]] += 1
    moves = [d for d in sched if d["decision"] != "hold"]
    big = sum(1 for d in moves if abs(d["change_bp"]) >= 50)
    reversals = sum(1 for prev, nxt in zip(sched, sched[1:])
                    if {prev["decision"], nxt["decision"]} == {"cut", "hike"})
    last = sched[-1]
    cond_last = cond[last["decision"]]
    total_last = sum(cond_last.values())

    def share(c: Counter, k: str, total: int) -> float:
        return round(c[k] / total, 3) if total else 0.0

    return {
        "signal": "base_rates",
        "since": sched[0]["date"], "through": last["date"],
        "scheduled_decisions": n,
        "overall": {k: share(overall, k, n) for k in ("cut", "hold", "hike")},
        "last_decision": {"date": last["date"], "decision": last["decision"], "change_bp": last["change_bp"]},
        "given_last": {k: share(cond_last, k, total_last) for k in ("cut", "hold", "hike")},
        "given_last_n": total_last,
        "conditional": {p: {k: share(c, k, sum(c.values())) for k in ("cut", "hold", "hike")} for p, c in cond.items()},
        "moves": len(moves), "moves_50bp_or_more": big,
        "share_of_moves_50bp_or_more": round(big / len(moves), 3) if moves else 0.0,
        "reversals": reversals,
        "intermeeting_moves": len(intermeeting),
        "intermeeting_recent": [m for m in intermeeting if m["date"] >= "2000-01-01"],
        "evidence": EVIDENCE,
    }


def direction(sig: dict) -> str:
    g = sig["given_last"]
    best = max(g, key=g.get)
    return f"after a {sig['last_decision']['decision']}, next was {best} {g[best]:.0%} of the time"
