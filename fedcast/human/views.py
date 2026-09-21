"""H2 human views: structured, bounded, applied by code (PLAN.md section 7).

A view never edits probabilities directly. It contributes a signed tilt budget; the
net budget is clipped to TILT_CAP and applied by exponential tilting, which

  * moves exactly the budgeted amount of probability (total variation distance),
  * keeps the machine forecast's shape (smallest KL change for the shift achieved),
  * never creates probability in a bucket the machine gave 0.

The rationale text is for humans and the audit trail; it has no effect on the number,
so rewording it cannot change the forecast (S6).
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Literal, Sequence

from pydantic import BaseModel, Field

from fedcast.scorecard import TILT_BY_STRENGTH, TILT_CAP


class View(BaseModel):
    id: str = Field(pattern=r"^H2-\d{3,}$")
    author: str
    created_at: datetime
    expires_on: date
    direction: Literal["hawkish", "dovish"]
    strength: Literal[1, 2, 3]
    rationale: str = Field(min_length=20)

    def is_active(self, as_of: date) -> bool:
        return self.created_at.date() <= as_of <= self.expires_on

    def signed_budget(self) -> float:
        sign = 1.0 if self.direction == "hawkish" else -1.0
        return sign * TILT_BY_STRENGTH[self.strength]


def net_budget(views: Sequence[View], as_of: date) -> float:
    """Signed tilt budget from all active views, clipped to +/- TILT_CAP."""
    total = sum(v.signed_budget() for v in views if v.is_active(as_of))
    return max(-TILT_CAP, min(TILT_CAP, total))


def _tilted(probs: Sequence[float], lam: float) -> list[float]:
    mid = (len(probs) - 1) / 2
    weights = [p * math.exp(lam * (i - mid)) for i, p in enumerate(probs)]
    z = sum(weights)
    return [w / z for w in weights]


def _tv(a: Sequence[float], b: Sequence[float]) -> float:
    return 0.5 * sum(abs(x - y) for x, y in zip(a, b))


def apply_tilt(probs: Sequence[float], budget: float) -> list[float]:
    """Shift `probs` (ordered dovish -> hawkish) so that |budget| of probability changes hands.

    Positive budget tilts hawkish. If the distribution cannot absorb the full budget
    (e.g. all mass already in the most hawkish bucket), it moves as far as it can.
    """
    if abs(sum(probs) - 1.0) > 1e-9:
        raise ValueError("probs must sum to 1")
    if abs(budget) > TILT_CAP + 1e-12:
        raise ValueError(f"budget {budget} exceeds tilt cap {TILT_CAP}")
    if budget == 0:
        return list(probs)

    sign = 1.0 if budget > 0 else -1.0
    target = abs(budget)
    lo, hi = 0.0, 50.0
    if _tv(probs, _tilted(probs, sign * hi)) < target:
        return _tilted(probs, sign * hi)
    for _ in range(100):
        lam = (lo + hi) / 2
        if _tv(probs, _tilted(probs, sign * lam)) < target:
            lo = lam
        else:
            hi = lam
    return _tilted(probs, sign * hi)
