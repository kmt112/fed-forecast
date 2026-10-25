"""One forecast run: snapshot -> models -> pool -> human tilt -> ledger entry.

Everything here is deterministic given (snapshot, views, code), which is what makes
`replay` a bit-for-bit check (S9) and keeps the two tracks attributable (S7).
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from fedcast import OUTCOMES_BP, aggregate, config
from fedcast.human.views import View, apply_tilt, net_budget
from fedcast.models.base_model import historical_base_rates
from fedcast.models.baseline import market_implied
from fedcast.models.prediction_market import prediction_market
from fedcast.models.probit import ordered_probit
from fedcast.models.taylor import taylor_rule
from fedcast.scorecard import ANALYST_TILT, POOL_WEIGHTS, SURPRISE_FLOOR, spec_hash
from fedcast.snapshot import Snapshot

MODELS = (market_implied, taylor_rule, prediction_market, historical_base_rates, ordered_probit)  # the probit has no pool weight yet


def _code_version() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "fedcast"], cwd=config.ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def specialist_tilts(snap: Snapshot, analyses: dict | None = None) -> dict:
    """The specialists' recorded tilts on this snapshot (amendment #6). `analyses` may be passed explicitly (the evals do,
    so a perturbed copy of a snapshot is judged with the same analyst records); otherwise the latest record of each
    specialist for this snapshot hash is read from analyses/."""
    from fedcast.llm import analyst

    if analyses is None:
        analyses = {name: analyst.latest(snap.hash, name) for name in analyst.SPECIALISTS}
    recs = {name: rec for name, rec in analyses.items() if rec and name in analyst.SPECIALISTS}
    tilts = {name: rec["summary"]["tilt_mean_bp"] for name, rec in recs.items()}
    mean_bp = sum(tilts.values()) / len(tilts) if tilts else 0.0
    budget = max(-ANALYST_TILT["cap"], min(ANALYST_TILT["cap"], mean_bp * ANALYST_TILT["pp_per_bp"]))
    return {"tilts_bp": tilts, "mean_bp": round(mean_bp, 3), "applied_pp": round(budget * 100, 3), "budget": budget,
            "records": {name: {"created_at": rec["created_at"], "runs": rec["summary"]["runs"], "prompt_version": rec.get("prompt_version")}
                        for name, rec in recs.items()},
            "note": "" if tilts else "no specialist record on this snapshot: tilt 0"}


def compute(snap: Snapshot, views: list[View], analyses: dict | None = None) -> dict:
    """The deterministic core. Same inputs (snapshot, views, recorded analyst runs) -> identical output."""
    outputs, skipped = [], {}
    for model in MODELS:
        try:
            outputs.append(model(snap))
        except (ValueError, KeyError) as exc:  # a model that cannot run on this snapshot is recorded, not hidden
            skipped[model.__name__] = f"{type(exc).__name__}: {exc}"
    if not outputs:
        raise ValueError("no model could run on this snapshot: " + "; ".join(skipped.values()))
    pooled = aggregate.pool({o["model"]: o["probabilities"] for o in outputs})
    analysts = specialist_tilts(snap, analyses)
    machine = dict(zip(OUTCOMES_BP, apply_tilt([pooled[o] for o in OUTCOMES_BP], analysts.pop("budget"))))

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
        "pooled": pooled,
        "analysts": analysts,
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
