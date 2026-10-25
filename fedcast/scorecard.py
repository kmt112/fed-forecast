"""Pre-registered process scorecard (PLAN.md section 3 and S10 from section 7).

These constants are the yardstick the whole project is judged by. They may only be
changed together with a new entry in governance/AMENDMENTS.md; tests/test_scorecard.py
pins SPEC_HASH so a silent edit fails the suite.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class Dimension:
    id: str
    name: str
    metric: str
    threshold: float
    unit: Literal["pp", "pct", "count", "score"]
    direction: Literal["max", "min"]  # "max": value must be <= threshold; "min": >= threshold

    def passes(self, value: float) -> bool:
        return value <= self.threshold if self.direction == "max" else value >= self.threshold


SCORECARD: tuple[Dimension, ...] = (
    Dimension("S1", "Repeatability",
              "N=10 runs on one frozen snapshot: max std-dev of any outcome probability",
              2.0, "pp", "max"),
    Dimension("S2", "Groundedness",
              "Share of factual claims the verifier traces to a snapshot item",
              95.0, "pct", "min"),
    Dimension("S3", "Leakage control",
              "Numbers/facts in a trace that are not present in the snapshot",
              0, "count", "max"),
    Dimension("S4", "Directional sanity",
              "Metamorphic shock tests with the correct sign of forecast movement",
              100.0, "pct", "min"),
    Dimension("S5", "Noise invariance",
              "Max forecast shift under irrelevant perturbations",
              1.0, "pp", "max"),
    Dimension("S6", "Paraphrase stability",
              "Max forecast shift under reworded prompts",
              2.0, "pp", "max"),
    Dimension("S7", "Coherence",
              "Runs where probabilities sum to 1 and deltas are attributable to input diffs",
              100.0, "pct", "min"),
    Dimension("S8", "Reasoning quality",
              "Rubric-graded trace score (base rate first, both sides, uncertainties, pre-mortem)",
              4.0, "score", "min"),
    Dimension("S9", "Auditability",
              "Ledger entries that replay (bit-for-bit deterministic parts, within S1 for LLM parts)",
              100.0, "pct", "min"),
    Dimension("S10", "Human-input discipline",
              "Share of human influence arriving via typed channels H1-H6 before the cutoff",
              100.0, "pct", "min"),
)

# Human view (H2) tilt settings, see fedcast/human/views.py.
TILT_CAP = 0.10  # max total probability that may change hands due to human views
TILT_BY_STRENGTH = {1: 0.03, 2: 0.06, 3: 0.10}

# Pooling (amendment #1, 2026-10-02): the market is the anchor; the Taylor-rule family corroborates or
# dissents at a fifth of the weight. Models absent from a run are dropped and the rest renormalised.
# Amendment #2 (2026-10-02): hand-entered prediction-market odds join at a tenth of the weight, taken from the
# futures anchor: an independent crowd on the same question, but thin and fee-distorted.
# Amendment #6 (2026-10-25): historical base rates join at a tenth of the weight, taken from the futures anchor: the only
# model with no parameters, and the one that beat the fitted probit on the expanding-window evaluation.
POOL_WEIGHTS: dict[str, float] = {"market_implied": 0.6, "taylor_rule": 0.2, "prediction_market": 0.1, "historical_base_rates": 0.1}
# Amendment #6 (2026-10-25): the specialists' judgement enters the machine track as a bounded tilt, never as a weight.
# The mean of the five specialists' tilts (latest record of each on the snapshot, basis points) is mapped one basis
# point to one percentage point, capped like a human view, and applied by the same exponential tilt after the floor.
# No specialist record on the snapshot means a tilt of 0, recorded as such.
ANALYST_TILT: dict = {"source": "mean tilt_bp over the latest record of each arm-D specialist on the snapshot",
                      "pp_per_bp": 0.01, "cap": TILT_CAP, "applied": "after the surprise floor, before human views"}
# No outcome is ever below this after pooling: the Fed occasionally does what nobody priced, and a
# 0% bucket cannot be moved by a view or scored sensibly. Interim value until the base-rate table exists.
SURPRISE_FLOOR = 0.015


def model_rules() -> dict:
    """Every constant in a model or signal that can move the number. Amendment #5 (2026-10-25): these are part of
    the spec hash, so a rule change forces a new hash and an amendment entry, and ledger entries recorded under the
    earlier rule are labelled as such instead of silently failing to replay (as #7-#10 did after amendment #4)."""
    from fedcast.models import prediction_market, taylor
    from fedcast.signals import inflation, labour

    return {
        "market_implied": {"method": "next-month contract when the month after the meeting has no meeting, else the "
                                     "meeting-month contract by day count; expected change split linearly between the "
                                     "two adjacent 25 bp outcomes"},
        "taylor_rule": {"inflation_measure": "12-month core PCE", "rho": taylor.RHO, "r_star_grid": list(taylor.R_STAR_GRID),
                        "u_star_grid": list(taylor.U_STAR_GRID), "sigma_floor_bp": taylor.SIGMA_FLOOR_BP,
                        "first_diff_meeting_scale": taylor.FIRST_DIFF_MEETING_SCALE, "goal": taylor.GOAL},
        "prediction_market": {"stale_after_days": prediction_market.STALE_AFTER_DAYS, "stale_odds": "used and flagged, never skipped"},
        "signals": {"inflation_goal": inflation.GOAL, "u_star": labour.U_STAR, "breakeven_payrolls_k": labour.BREAKEVEN_PAYROLLS_K},
    }


def spec_hash() -> str:
    payload = {
        "scorecard": [asdict(d) for d in SCORECARD],
        "tilt_cap": TILT_CAP,
        "tilt_by_strength": TILT_BY_STRENGTH,
        "pool_weights": POOL_WEIGHTS,
        "surprise_floor": SURPRISE_FLOOR,
        "analyst_tilt": ANALYST_TILT,
        "model_rules": model_rules(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
