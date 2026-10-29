"""Score recorded forecasts once the decision is known. Outcome accuracy is logged here and never used to tune.

The decision is read from evidence, not typed: the New York Fed's overnight-rate row carries the target range in
force each day, so once the latest snapshot's row is dated after the meeting, its upper bound is the decision. The
realised change is that upper bound against the upper bound in the forecast's own snapshot, in 25 bp steps.

Two proper scores per probability vector:
  log score   ln p(outcome): higher is better, 0 is perfect, -inf if the outcome was given 0% (recorded as such)
  Brier       sum over outcomes of (p - 1[outcome])^2: lower is better, 0 is perfect, 2 is the worst possible

Scores go to an append-only, hash-chained file beside the forecast ledger, one record per decision scored.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone

from fedcast import config, OUTCOMES_BP
from fedcast.data.fomc_calendar import DECISION_TIME
from fedcast.scorecard import spec_hash
from fedcast.snapshot import Snapshot


def decision_from_snapshot(snap: Snapshot, meeting: date) -> dict | None:
    """The target range in force after `meeting`, if the snapshot already shows it; else None."""
    latest = snap.get("effr")["latest"]
    if date.fromisoformat(latest["date"]) <= meeting:
        return None
    out = {"date": latest["date"], "target_low": latest["target_low"], "target_high": latest["target_high"],
           "evidence": ["effr"]}
    if "history.target_rate" in snap.items:  # cross-check against the daily target series when it has caught up
        changes = snap.get("history.target_rate")["changes"]
        after = [c for c in changes if date.fromisoformat(c["date"]) > meeting]
        if after:
            out["history_target"] = after[0]["target"]
            out["history_agrees"] = abs(after[0]["target"] - latest["target_high"]) < 1e-9
            out["evidence"].append("history.target_rate")
    return out


def realised_change_bp(target_high_before: float, target_high_after: float) -> int:
    bp = round((target_high_after - target_high_before) * 100 / 25) * 25
    return int(max(OUTCOMES_BP[0], min(OUTCOMES_BP[-1], bp)))


def score_vector(probs: dict, realised_bp: int) -> dict:
    p = {int(k): float(v) for k, v in probs.items()}
    hit = p.get(realised_bp, 0.0)
    brier = sum((p.get(o, 0.0) - (1.0 if o == realised_bp else 0.0)) ** 2 for o in OUTCOMES_BP)
    return {"p_outcome": round(hit, 4), "log_score": round(math.log(hit), 4) if hit > 0 else None,
            "zero_probability": hit <= 0, "brier": round(brier, 4)}


def score_entries(entries: list[dict], meeting: date, decision: dict, target_high_before: float) -> dict:
    """One score record for a meeting: every ledger entry for that meeting, its tracks and its models."""
    realised = realised_change_bp(target_high_before, decision["target_high"])
    scored = []
    for e in entries:
        f = e["forecast"]
        if not recorded_before_decision(e, meeting):
            scored.append({"seq": e["seq"], "created_at": e["created_at"], "snapshot": f["snapshot_hash"][:12],
                           "spec_hash": e.get("spec_hash"), "tracks": {}, "models": {}, "after_decision": True,
                           "note": "recorded after the decision was announced: not scored"})
            continue
        tracks = {k: score_vector(f[k], realised) for k in ("pooled", "machine_only", "human_adjusted") if k in f}
        models = {name: score_vector(m["probabilities"], realised) for name, m in f["models"].items() if "probabilities" in m}
        scored.append({"seq": e["seq"], "created_at": e["created_at"], "snapshot": f["snapshot_hash"][:12],
                       "spec_hash": e.get("spec_hash"), "tracks": tracks, "models": models, "after_decision": False})
    before = [x for x in scored if not x["after_decision"]]
    return {"meeting": meeting.isoformat(), "realised_bp": realised,
            "decision": {**decision, "target_high_before": target_high_before},
            "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "spec_hash": spec_hash(),
            "entries": scored, "final_entry": before[-1]["seq"] if before else None}


def announced_at(meeting: date) -> datetime:
    """When the decision became public: 2:00 pm US Eastern on the meeting's decision day."""
    return datetime.combine(meeting, DECISION_TIME, tzinfo=config.DATA_TZ)


def recorded_before_decision(entry: dict, meeting: date) -> bool:
    """A forecast counts only if it was recorded before the decision was announced. An entry recorded after that
    (for example a snapshot pulled on the evening of the decision day while FRED's clock still read that date) stays
    in the ledger but is labelled and never scored."""
    created = datetime.fromisoformat(entry["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created < announced_at(meeting)


def score_meeting(meeting: date | None, ledger_path, scores_path, snap: Snapshot, find_snapshot) -> dict:
    """Score every ledger entry for `meeting` (default: the latest meeting in the ledger that the snapshot can
    decide) and append one record to the scores file. Raises ValueError when the decision is not in the evidence
    yet, or the meeting was already scored."""
    from fedcast import ledger

    entries = ledger.read(ledger_path)
    meetings = sorted({e["forecast"]["meeting"] for e in entries})
    if meeting is None:
        decided = [m for m in meetings if decision_from_snapshot(snap, date.fromisoformat(m))]
        if not decided:
            raise ValueError("the latest snapshot does not yet show a decision for any forecast meeting: "
                             "pull evidence the day after the decision, then score")
        meeting = date.fromisoformat(decided[-1])
    done = {r["meeting"] for r in ledger.read(scores_path)}
    if meeting.isoformat() in done:
        raise ValueError(f"the {meeting} decision is already scored")
    decision = decision_from_snapshot(snap, meeting)
    if decision is None:
        raise ValueError(f"the latest snapshot's overnight-rate row ({snap.get('effr')['latest']['date']}) is not after "
                         f"{meeting}: pull evidence the day after the decision, then score")
    mine = [e for e in entries if e["forecast"]["meeting"] == meeting.isoformat()]
    if not mine:
        raise ValueError(f"no ledger entry forecasts the {meeting} meeting")
    timely = [e for e in mine if recorded_before_decision(e, meeting)]
    if not timely:
        raise ValueError(f"every ledger entry for the {meeting} meeting was recorded after the decision was announced")
    before_snap = find_snapshot(timely[-1]["forecast"]["snapshot_hash"])
    if before_snap is None:
        raise ValueError("the final entry's snapshot is missing")
    target_before = before_snap.get("effr")["latest"]["target_high"]
    rec = score_entries(mine, meeting, decision, target_before)
    rec["baselines"] = naive_baselines(rec["realised_bp"])
    return ledger.append(scores_path, rec)


def naive_baselines(realised_bp: int) -> dict:
    """Yardsticks that need no model: always 'no change', and uniform over the five outcomes."""
    hold = {o: (1.0 if o == 0 else 0.0) for o in OUTCOMES_BP}
    uniform = {o: 0.2 for o in OUTCOMES_BP}
    return {"always_no_change": score_vector(hold, realised_bp), "uniform": score_vector(uniform, realised_bp)}
