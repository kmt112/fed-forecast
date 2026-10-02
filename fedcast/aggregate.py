"""Deterministic pooling of model outputs. No LLM ever writes the final number.

Linear opinion pool: a weighted average of each model's distribution, chosen over a log-linear
pool because the futures model legitimately puts 0 on most buckets and a log pool would let one
model's zero veto every other model. A surprise floor is then applied: no outcome is ever below
SURPRISE_FLOOR, because the Fed does occasionally do what nobody priced. Both the weights and the
floor are part of the pre-registered spec (fedcast/scorecard.py).
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP
from fedcast.scorecard import POOL_WEIGHTS, SURPRISE_FLOOR


def pool(model_probs: dict[str, dict[int, float]], weights: dict[str, float] = POOL_WEIGHTS,
         floor: float = SURPRISE_FLOOR) -> dict[int, float]:
    active = {name: w for name, w in weights.items() if name in model_probs and w > 0}
    if not active:
        raise ValueError("no weighted model produced output")
    total = sum(active.values())
    pooled = {o: sum(w / total * model_probs[name][o] for name, w in active.items()) for o in OUTCOMES_BP}
    out = _apply_floor(pooled, floor)
    if abs(sum(out.values()) - 1.0) > 1e-9:
        raise ValueError("pooled probabilities do not sum to 1")
    return out


def _apply_floor(probs: dict[int, float], floor: float) -> dict[int, float]:
    """Raise every bucket below `floor` to exactly `floor`, taking the mass proportionally from the rest."""
    if floor <= 0:
        return dict(probs)
    low = {o for o, p in probs.items() if p < floor}
    while True:
        rest = {o: p for o, p in probs.items() if o not in low}
        scale = (1.0 - floor * len(low)) / sum(rest.values())
        out = {o: (floor if o in low else p * scale) for o, p in probs.items()}
        newly_low = {o for o, p in out.items() if p < floor - 1e-12}
        if not newly_low:
            return out
        low |= newly_low
