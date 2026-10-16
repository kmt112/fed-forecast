"""Historical base-rate model: the next decision's distribution given the previous decision, from the record.

PRE-REGISTERED (2026-10-16): P(cut / hold / hike) = frequencies of what followed the previous decision's
class among scheduled decisions since 1994 (signals/base_rates.py conditional table); cut and hike mass split
into 25 bp and 50+ bp by the share of large moves in that direction over the same record. No parameters.
It is the yardstick every fitted model must beat on the expanding-window evaluation, and the obvious candidate
for the pool slot the surprise floor currently stands in for.
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP
from fedcast.signals import base_rates
from fedcast.snapshot import Snapshot


def historical_base_rates(snap: Snapshot) -> dict:
    hist = base_rates.compute(snap)
    g = hist["given_last"]
    meetings = [m for m in snap.get("history.meetings")["meetings"] if m["date"] <= hist["through"]]
    decided, _ = base_rates.decisions(meetings, snap.get("history.target_rate")["changes"])
    sched = [d for d in decided if d["scheduled"]]
    shares = {}
    for name, sign in (("cut", -1), ("hike", 1)):
        moves = [d for d in sched if d["change_bp"] != 0 and (d["change_bp"] > 0) == (sign > 0)]
        shares[name] = round(sum(1 for d in moves if abs(d["change_bp"]) >= 50) / len(moves), 3) if moves else 0.25
    probs = {-50: g["cut"] * shares["cut"], -25: g["cut"] * (1 - shares["cut"]), 0: g["hold"],
             25: g["hike"] * (1 - shares["hike"]), 50: g["hike"] * shares["hike"]}
    return {"model": "historical_base_rates", "meeting": snap.get("calendar")["next_meeting"],
            "conditioned_on": hist["last_decision"], "n_cases": hist["given_last_n"],
            "class_probabilities": g, "large_move_shares": shares,
            "probabilities": {o: probs[o] for o in OUTCOMES_BP},
            "evidence": base_rates.EVIDENCE + ["calendar"], "snapshot_hash": snap.hash}
