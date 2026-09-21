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
              "Share of human influence arriving via typed channels H1-H4 before the cutoff",
              100.0, "pct", "min"),
)

# Human view (H2) tilt settings, see fedcast/human/views.py.
TILT_CAP = 0.10  # max total probability that may change hands due to human views
TILT_BY_STRENGTH = {1: 0.03, 2: 0.06, 3: 0.10}


def spec_hash() -> str:
    payload = {
        "scorecard": [asdict(d) for d in SCORECARD],
        "tilt_cap": TILT_CAP,
        "tilt_by_strength": TILT_BY_STRENGTH,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
