"""Labour slack: unemployment against its sustainable level, payrolls against breakeven, claims against trend.

Spec (pre-registered 2026-10-02):
  unemployment gap  u − u*, with u* = 4.2% (close to the CBO and SEP longer-run estimates);
                    positive means slack, negative means a tight market
  Sahm indicator    3-month average unemployment minus its 12-month low; 0.5 is the recession trigger
  payrolls          3-month average monthly change against a 75k/month breakeven pace, and the 12-month average
  claims            4-week average initial claims against the 26-week average
Everything is computed from the snapshot's FRED vintages.
"""

from __future__ import annotations

from fedcast.snapshot import Snapshot

U_STAR = 4.2
BREAKEVEN_PAYROLLS_K = 75.0
EVIDENCE = ["fred.UNRATE", "fred.PAYEMS", "fred.ICSA"]


def _series(snap: Snapshot, item_id: str) -> list[tuple[str, float]]:
    return [(o["date"], o["value"]) for o in snap.get(item_id)["observations"] if o["value"] is not None]


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals)


def compute(snap: Snapshot) -> dict:
    u = _series(snap, "fred.UNRATE")
    p = _series(snap, "fred.PAYEMS")
    c = _series(snap, "fred.ICSA")
    if len(u) < 13 or len(p) < 13 or len(c) < 26:
        raise ValueError("need 13 months of unemployment and payrolls and 26 weeks of claims")
    u_vals = [v for _, v in u]
    u_3m = _mean(u_vals[:3])
    return {
        "signal": "labour_slack",
        "u_star": U_STAR,
        "unemployment": round(u_vals[0], 2),
        "unemployment_year_ago": round(u_vals[12], 2),
        "gap_pp": round(u_vals[0] - U_STAR, 3),
        "sahm": round(u_3m - min(u_vals[:12]), 3),
        "payrolls_3m_avg_k": round((p[0][1] - p[3][1]) / 3, 1),
        "payrolls_12m_avg_k": round((p[0][1] - p[12][1]) / 12, 1),
        "breakeven_payrolls_k": BREAKEVEN_PAYROLLS_K,
        "claims_4wk_k": round(_mean([v for _, v in c[:4]]) / 1000, 1),
        "claims_26wk_k": round(_mean([v for _, v in c[:26]]) / 1000, 1),
        "through": {"unemployment": u[0][0], "payrolls": p[0][0], "claims": c[0][0]},
        "evidence": EVIDENCE,
    }


def direction(sig: dict) -> str:
    gap = sig["gap_pp"]
    where = "slack" if gap > 0.2 else "tight" if gap < -0.2 else "balanced"
    if sig["sahm"] >= 0.5:
        return f"{where}, Sahm rule triggered"
    trend = ("loosening" if sig["payrolls_3m_avg_k"] < sig["breakeven_payrolls_k"] - 25
             or sig["claims_4wk_k"] > sig["claims_26wk_k"] * 1.1 else "steady")
    return f"{where}, {trend}"
