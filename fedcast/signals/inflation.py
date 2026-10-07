"""Inflation gap: realised core PCE inflation against the Fed's 2% goal, with momentum and a nowcast.

Spec (pre-registered 2026-10-02):
  anchor    12-month core PCE inflation, the Fed's own yardstick; gap = anchor − 2.0
  momentum  3- and 6-month annualised core PCE, shown beside the anchor, never blended into it
  nowcast   PCE lags CPI by a month; the latest core-CPI monthly change stands in for the missing
            PCE month to give a 12-month nowcast, labelled as such
Everything is computed from the snapshot's FRED vintages, so revisions after the date cannot leak in.
"""

from __future__ import annotations

from fedcast.snapshot import Snapshot

GOAL = 2.0
EVIDENCE = ["fred.PCEPILFE", "fred.CPILFESL"]


def _series(snap: Snapshot, item_id: str) -> list[tuple[str, float]]:
    return [(o["date"], o["value"]) for o in snap.get(item_id)["observations"] if o["value"] is not None]


def annualised(series: list[tuple[str, float]], months: int) -> float | None:
    """Annualised % change over the last `months` observations of a monthly index (newest first)."""
    if len(series) <= months:
        return None
    return ((series[0][1] / series[months][1]) ** (12 / months) - 1) * 100


def compute(snap: Snapshot) -> dict:
    pce = _series(snap, "fred.PCEPILFE")
    cpi = _series(snap, "fred.CPILFESL")
    a12 = annualised(pce, 12)
    if a12 is None:
        raise ValueError("need at least 13 months of core PCE")

    out = {
        "signal": "inflation_gap",
        "goal": GOAL,
        "anchor_12m": round(a12, 3),
        "gap_pp": round(a12 - GOAL, 3),
        "momentum": {"3m": round(annualised(pce, 3), 3), "6m": round(annualised(pce, 6), 3)},
        "pce_through": pce[0][0],
        "cpi": {"12m": round(annualised(cpi, 12), 3), "3m": round(annualised(cpi, 3), 3), "through": cpi[0][0]},
        "nowcast": None,
        "evidence": EVIDENCE,
    }
    # CPI is one month fresher than PCE: carry PCE forward by CPI's latest monthly change.
    if cpi[0][0] > pce[0][0] and len(cpi) > 1:
        cpi_mom = cpi[0][1] / cpi[1][1]
        extended = [(cpi[0][0], pce[0][1] * cpi_mom)] + pce
        n12 = annualised(extended, 12)
        out["nowcast"] = {"month": cpi[0][0], "method": "core CPI monthly change applied to core PCE",
                          "anchor_12m": round(n12, 3), "gap_pp": round(n12 - GOAL, 3)}
    return out


def direction(sig: dict) -> str:
    """One-line reading: where inflation is against the goal and which way momentum points."""
    gap = sig["gap_pp"]
    m3 = sig["momentum"]["3m"]
    where = "above" if gap > 0.25 else "below" if gap < -0.25 else "near"
    trend = ("easing" if m3 < sig["anchor_12m"] - 0.25 else
             "firming" if m3 > sig["anchor_12m"] + 0.25 else "steady")
    return f"{where} goal, {trend}"
