"""Financial conditions: what the bond market expects and how tight conditions are.

Spec (pre-registered 2026-10-02):
  2y gap       2-year Treasury yield minus the policy rate (EFFR), in bp. Roughly the average policy rate
               investors expect over two years versus today's: positive means hikes priced, negative cuts
  breakeven    5-year breakeven inflation (nominal minus TIPS yield) against the 2% goal, and its 4-week change,
               as the market's inflation expectation and whether it is drifting
  NFCI         Chicago Fed National Financial Conditions Index: 0 is average, negative is looser than average,
               positive tighter; its 4-week change shows whether conditions are tightening
Computed from the snapshot's FRED vintages. Daily series are read at their latest print and about 20
trading days (4 weeks) earlier; the weekly NFCI 4 observations earlier.
"""

from __future__ import annotations

from fedcast.snapshot import Snapshot

EVIDENCE = ["fred.DGS2", "fred.T5YIE", "fred.NFCI", "effr"]
GOAL = 2.0


def _series(snap: Snapshot, item_id: str) -> list[tuple[str, float]]:
    return [(o["date"], o["value"]) for o in snap.get(item_id)["observations"] if o["value"] is not None]


def _ago(series: list[tuple[str, float]], n: int) -> tuple[str, float]:
    return series[min(n, len(series) - 1)]


def compute(snap: Snapshot) -> dict:
    dgs2 = _series(snap, "fred.DGS2")
    bei = _series(snap, "fred.T5YIE")
    nfci = _series(snap, "fred.NFCI")
    if len(dgs2) < 10 or len(bei) < 10 or len(nfci) < 5:
        raise ValueError("need at least two weeks of yields and breakevens and five weeks of NFCI")
    effr = snap.get("effr")["latest"]["effr"]
    y_now, y_ago = dgs2[0], _ago(dgs2, 20)
    b_now, b_ago = bei[0], _ago(bei, 20)
    n_now, n_ago = nfci[0], _ago(nfci, 4)
    return {
        "signal": "financial_conditions",
        "policy_rate": effr,
        "two_year": {"yield": y_now[1], "date": y_now[0], "gap_bp": round((y_now[1] - effr) * 100, 1),
                     "change_4wk_bp": round((y_now[1] - y_ago[1]) * 100, 1), "ago_date": y_ago[0]},
        "breakeven": {"level": b_now[1], "date": b_now[0], "vs_goal_pp": round(b_now[1] - GOAL, 3),
                      "change_4wk_pp": round(b_now[1] - b_ago[1], 3)},
        "nfci": {"level": n_now[1], "date": n_now[0], "change_4wk": round(n_now[1] - n_ago[1], 3)},
        "evidence": EVIDENCE,
    }


def direction(sig: dict) -> str:
    gap = sig["two_year"]["gap_bp"]
    priced = "hikes priced" if gap > 25 else "cuts priced" if gap < -25 else "little change priced"
    anchored = abs(sig["breakeven"]["vs_goal_pp"]) <= 0.5
    cond = "loose" if sig["nfci"]["level"] < -0.3 else "tight" if sig["nfci"]["level"] > 0.3 else "average"
    return f"{priced}, expectations {'anchored' if anchored else 'drifting'}, conditions {cond}"
