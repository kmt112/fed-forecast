"""One forecast run: snapshot -> models -> pool -> human tilt -> ledger entry.

Everything here is deterministic given (snapshot, views, code), which is what makes
`replay` a bit-for-bit check (S9) and keeps the two tracks attributable (S7).
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from fedcast import OUTCOMES_BP, aggregate, config
from fedcast.human.views import View, apply_tilt, net_budget
from fedcast.models.baseline import market_implied
from fedcast.models.prediction_market import prediction_market
from fedcast.models.taylor import taylor_rule
from fedcast.scorecard import POOL_WEIGHTS, SURPRISE_FLOOR, spec_hash
from fedcast.snapshot import Snapshot

MODELS = (market_implied, taylor_rule, prediction_market)


def _code_version() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "fedcast"], cwd=config.ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def compute(snap: Snapshot, views: list[View]) -> dict:
    """The deterministic core. Same inputs -> identical output."""
    outputs, skipped = [], {}
    for model in MODELS:
        try:
            outputs.append(model(snap))
        except (ValueError, KeyError) as exc:  # a model that cannot run on this snapshot is recorded, not hidden
            skipped[model.__name__] = f"{type(exc).__name__}: {exc}"
    if not outputs:
        raise ValueError("no model could run on this snapshot: " + "; ".join(skipped.values()))
    machine = aggregate.pool({o["model"]: o["probabilities"] for o in outputs})

    active = [v for v in views if v.is_active(snap.as_of)]
    budget = net_budget(active, snap.as_of)
    ordered = [machine[o] for o in OUTCOMES_BP]
    adjusted = dict(zip(OUTCOMES_BP, apply_tilt(ordered, budget)))

    return {
        "meeting": outputs[0]["meeting"],
        "snapshot_hash": snap.hash,
        "snapshot_complete": snap.complete,
        "models": {o["model"]: {k: v for k, v in o.items() if k not in ("model", "snapshot_hash")}
                   for o in outputs},
        "models_skipped": skipped,
        "pool_weights": POOL_WEIGHTS,
        "surprise_floor": SURPRISE_FLOOR,
        "machine_only": machine,
        "human": {"views_applied": [v.model_dump(mode="json") for v in active], "net_budget": budget},
        "human_adjusted": adjusted,
    }


def run(snap: Snapshot, views: list[View]) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "spec_hash": spec_hash(),
        "code_version": _code_version(),
        "forecast": compute(snap, views),
    }
