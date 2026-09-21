"""Deterministic pooling of model outputs. No LLM ever writes the final number.

Linear opinion pool: a weighted average of each model's distribution. Chosen over a
log-linear pool because the futures model legitimately puts 0 on most buckets, and a
log pool would let one model's zero veto every other model.
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP

# Weights are part of the recorded forecast config; models absent from a run are
# dropped and the rest renormalised. More models arrive in Phase 2b/3.
POOL_WEIGHTS: dict[str, float] = {
    "market_implied": 1.0,
}


def pool(model_probs: dict[str, dict[int, float]], weights: dict[str, float] = POOL_WEIGHTS) -> dict[int, float]:
    active = {name: w for name, w in weights.items() if name in model_probs and w > 0}
    if not active:
        raise ValueError("no weighted model produced output")
    total = sum(active.values())
    pooled = {o: sum(w / total * model_probs[name][o] for name, w in active.items()) for o in OUTCOMES_BP}
    if abs(sum(pooled.values()) - 1.0) > 1e-9:
        raise ValueError("pooled probabilities do not sum to 1")
    return pooled
