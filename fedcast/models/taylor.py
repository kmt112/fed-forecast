"""Taylor-rule family, as the Fed's Monetary Policy Report defines it, turned into a next-meeting distribution.

Variants (the MPR's quarterly rules, read with monthly data; π = 12-month core PCE inflation, u = unemployment):
  taylor93     R = r* + π + 0.5(π − 2) + 1.0(u* − u)
  balanced     R = r* + π + 0.5(π − 2) + 2.0(u* − u)
  shortfalls   R = r* + π + 0.5(π − 2) + 2.0·min(u* − u, 0)      responds to slack only, not to tightness
  first_diff   ΔR = 0.5(π − 2) + (u* − u) − (u* − u_12m_ago)      a change rule, scaled from a quarter to one meeting

Level rules are applied with partial adjustment: prescribed change = (1 − ρ)(R − R_before), ρ = 0.85,
because the Fed moves toward a rule rate gradually rather than jumping to it.
The unknowable inputs run over a grid, r* ∈ {0.5, 1.0, 1.5} and u* ∈ {4.0, 4.2, 4.4}. All prescriptions
(variants × grid) are summarised by their mean and spread; σ = sqrt(spread² + 15 bp²); outcome probabilities
are the normal mass in each 25 bp bucket, with the end buckets taking the tails.

Pre-registered 2026-10-02. Not fitted to outcomes.
"""

from __future__ import annotations

import math
from statistics import mean, pstdev

from fedcast import OUTCOMES_BP
from fedcast.signals import inflation, labour
from fedcast.snapshot import Snapshot

RHO = 0.85
R_STAR_GRID = (0.5, 1.0, 1.5)
U_STAR_GRID = (4.0, 4.2, 4.4)
SIGMA_FLOOR_BP = 15.0
FIRST_DIFF_MEETING_SCALE = 0.5  # the rule is quarterly; there are about two meetings a quarter
GOAL = 2.0


def prescriptions(pi: float, u: float, u_lag: float, rate_before: float) -> list[dict]:
    out = []
    for u_star in U_STAR_GRID:
        gap = u_star - u
        for r_star in R_STAR_GRID:
            levels = {
                "taylor93": r_star + pi + 0.5 * (pi - GOAL) + 1.0 * gap,
                "balanced": r_star + pi + 0.5 * (pi - GOAL) + 2.0 * gap,
                "shortfalls": r_star + pi + 0.5 * (pi - GOAL) + 2.0 * min(gap, 0.0),
            }
            for name, rule_rate in levels.items():
                out.append({"variant": name, "r_star": r_star, "u_star": u_star, "rule_rate": round(rule_rate, 3),
                            "change_bp": round((1 - RHO) * (rule_rate - rate_before) * 100, 1)})
        fd = (0.5 * (pi - GOAL) + gap - (u_star - u_lag)) * FIRST_DIFF_MEETING_SCALE
        out.append({"variant": "first_diff", "r_star": None, "u_star": u_star, "rule_rate": round(rate_before + fd, 3),
                    "change_bp": round(fd * 100, 1)})
    return out


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bucket_from_normal(mean_bp: float, sigma_bp: float) -> dict[int, float]:
    edges = [o + 12.5 for o in OUTCOMES_BP[:-1]]  # −37.5, −12.5, 12.5, 37.5
    cdf = [_phi((e - mean_bp) / sigma_bp) for e in edges]
    probs = [cdf[0]] + [cdf[i] - cdf[i - 1] for i in range(1, len(cdf))] + [1 - cdf[-1]]
    return {o: p for o, p in zip(OUTCOMES_BP, probs)}


def taylor_rule(snap: Snapshot) -> dict:
    infl = inflation.compute(snap)
    lab = labour.compute(snap)
    rate_before = snap.get("effr")["latest"]["effr"]
    pres = prescriptions(infl["anchor_12m"], lab["unemployment"], lab["unemployment_year_ago"], rate_before)
    changes = [p["change_bp"] for p in pres]
    mu, spread = mean(changes), pstdev(changes)
    sigma = math.sqrt(spread ** 2 + SIGMA_FLOOR_BP ** 2)
    by_variant = {v: round(mean([p["change_bp"] for p in pres if p["variant"] == v]), 1)
                  for v in ("taylor93", "balanced", "shortfalls", "first_diff")}
    return {
        "model": "taylor_rule",
        "meeting": snap.get("calendar")["next_meeting"],
        "rate_before": rate_before,
        "inputs": {"inflation_12m": infl["anchor_12m"], "inflation_gap_pp": infl["gap_pp"],
                   "unemployment": lab["unemployment"], "unemployment_year_ago": lab["unemployment_year_ago"]},
        "expected_change_bp": round(mu, 2),
        "spread_bp": round(spread, 2),
        "sigma_bp": round(sigma, 2),
        "by_variant_bp": by_variant,
        "prescriptions": pres,
        "probabilities": bucket_from_normal(mu, sigma),
        "evidence": sorted(set(infl["evidence"] + lab["evidence"] + ["effr", "calendar"])),
        "snapshot_hash": snap.hash,
    }
