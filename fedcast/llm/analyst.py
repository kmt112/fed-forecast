"""The first LLM analyst (communications) and the naive control, with a code verifier.

Harness rules, enforced here rather than asked for:
  * the model sees only snapshot items and your typed inputs (the backend has no tools);
  * every claim must carry a verbatim quote and the id of the item it comes from; the verifier string-matches
    the quote against that item, so groundedness (S2) is a count, not an opinion;
  * numbers in a claim that do not occur in the quoted item are leakage (S3);
  * every active watch-out must be addressed by id;
  * the output is a bounded tilt in basis points, never the final number.

The naive control (ablation arm A) asks the same question with no evidence at all; by construction it
cannot cite, so its groundedness is 0 and every number it gives is from memory.
"""

from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

from fedcast import OUTCOMES_BP, config
from fedcast.llm.backend import Completion, LLMBackend
from fedcast.signals import comms
from fedcast.snapshot import Snapshot

ANALYSES_DIR = config.ROOT / "analyses"
TILT_CAP_BP = 10
PROMPT_VERSION = "comms-v1"

SYSTEM = ("You are a Federal Reserve communications analyst inside an audited forecasting harness. You may use ONLY "
          "the evidence in the user message. Do not use anything you remember about the economy, the Fed or markets; "
          "if the evidence does not contain something, say it is not in the evidence. Every claim must quote the "
          "evidence verbatim (copy the exact characters) and name the item id it came from. Numbers may appear in a "
          "claim only if they appear in the quoted item. Output only JSON matching the schema.")

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {"type": "array", "items": {"type": "object", "properties": {
            "text": {"type": "string"}, "quote": {"type": "string"}, "item": {"type": "string"},
            "lean": {"type": "string", "enum": ["hawkish", "dovish", "neutral"]}},
            "required": ["text", "quote", "item", "lean"]}},
        "watchouts": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "status": {"type": "string", "enum": ["found", "not_found"]},
            "evidence": {"type": "string"}}, "required": ["id", "status", "evidence"]}},
        "tilt_bp": {"type": "number", "minimum": -TILT_CAP_BP, "maximum": TILT_CAP_BP},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string"},
    },
    "required": ["claims", "watchouts", "tilt_bp", "confidence", "summary"],
}

NAIVE_SCHEMA = {
    "type": "object",
    "properties": {"probabilities": {"type": "object", "properties": {str(o): {"type": "number"} for o in OUTCOMES_BP},
                                     "required": [str(o) for o in OUTCOMES_BP]},
                   "reasoning": {"type": "string"}},
    "required": ["probabilities", "reasoning"],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def build_prompt(snap: Snapshot, watchlist: list[dict], max_chars: int = 60000) -> str:
    cal = snap.get("calendar")
    tone = comms.compute(snap)
    parts = [f"Snapshot date: {snap.as_of.isoformat()}. Next FOMC decision: {cal['next_meeting']}.",
             "Question: from the committee's own communications, which way does the next decision lean, and why? "
             f"Give a net tilt between -{TILT_CAP_BP} (strongly dovish) and +{TILT_CAP_BP} (strongly hawkish) basis "
             "points relative to what a reader of these documents would expect, with claims that each quote one item.",
             "", "=== DETERMINISTIC PRE-READ (item: signal.tone) ===",
             json.dumps({"vote": tone["vote"], "lexicon": tone["lexicon"], "diff": tone["diff"]}, ensure_ascii=False)]
    active = [w for w in watchlist if w.get("status") == "active"]
    parts += ["", "=== WATCH-OUTS (each must be addressed by id) ==="]
    parts += [f"{w['id']}: {w['directive']}" for w in active] or ["none"]
    for item_id in sorted(snap.items):
        kind = snap.items[item_id].kind
        if kind in ("document", "human_document"):
            text = snap.get(item_id)["text"]
            parts += ["", f"=== ITEM {item_id} ({'your document: ' + snap.get(item_id)['title'] if kind == 'human_document' else kind}) ===",
                      text[:max_chars]]
    return "\n".join(parts)


def verify(output: dict, snap: Snapshot, watchlist: list[dict]) -> dict:
    texts = {}
    for item_id in snap.items:
        content = snap.get(item_id)
        texts[item_id] = _norm(content["text"]) if isinstance(content, dict) and "text" in content else _norm(json.dumps(content))
    tone_json = _norm(json.dumps(comms.compute(snap)))
    texts["signal.tone"] = tone_json

    claims = []
    for c in output.get("claims", []):
        item_text = texts.get(c.get("item", ""), "")
        quote_ok = bool(c.get("quote")) and _norm(c["quote"]) in item_text
        nums = set(re.findall(r"\d+(?:[.,]\d+)?", c.get("text", "")))
        leaked = sorted(n for n in nums if n.replace(",", "") not in item_text.replace(",", ""))
        claims.append({**c, "verified": quote_ok, "leaked_numbers": leaked})
    n = len(claims)
    verified = sum(c["verified"] for c in claims)
    active_ids = [w["id"] for w in watchlist if w.get("status") == "active"]
    addressed = {w.get("id") for w in output.get("watchouts", [])}
    tilt = max(-TILT_CAP_BP, min(TILT_CAP_BP, float(output.get("tilt_bp", 0))))
    return {
        "claims": claims,
        "n_claims": n, "n_verified": verified,
        "groundedness_pct": round(100 * verified / n, 1) if n else 0.0,
        "leakage_count": sum(len(c["leaked_numbers"]) for c in claims),
        "watchouts_required": active_ids,
        "watchouts_missing": [i for i in active_ids if i not in addressed],
        "tilt_bp": tilt, "tilt_clipped": tilt != float(output.get("tilt_bp", 0)),
    }


def run_comms(snap: Snapshot, backend: LLMBackend, watchlist: list[dict], runs: int = 1) -> dict:
    prompt = build_prompt(snap, watchlist)
    results = []
    for _ in range(runs):
        c = backend.complete(SYSTEM, prompt, SCHEMA)
        results.append({"completion": _dump(c), "verification": verify(c.output, snap, watchlist)})
    tilts = [r["verification"]["tilt_bp"] for r in results]
    rec = {
        "analyst": "communications", "arm": "D", "prompt_version": PROMPT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_hash": snap.hash, "backend": backend.name, "runs": results,
        "summary": {
            "runs": runs, "tilt_mean_bp": round(statistics.mean(tilts), 2),
            "tilt_std_bp": round(statistics.pstdev(tilts), 2) if runs > 1 else None,
            "groundedness_pct_mean": round(statistics.mean(r["verification"]["groundedness_pct"] for r in results), 1),
            "leakage_total": sum(r["verification"]["leakage_count"] for r in results),
            "watchouts_missing_total": sum(len(r["verification"]["watchouts_missing"]) for r in results),
        },
    }
    return rec


def run_naive(snap: Snapshot, backend: LLMBackend, runs: int = 1) -> dict:
    """Ablation arm A: the same question with no evidence. Nothing to cite, so nothing can be verified."""
    cal = snap.get("calendar")
    prompt = (f"Today is {snap.as_of.isoformat()}. What will the FOMC decide at its {cal['next_meeting']} meeting? "
              "Give a probability for each outcome in basis points of change (-50, -25, 0, 25, 50), summing to 1, "
              "and a short reasoning.")
    results = []
    for _ in range(runs):
        c = backend.complete("You are a Fed watcher. Output only JSON matching the schema.", prompt, NAIVE_SCHEMA)
        probs = {str(o): float(c.output["probabilities"].get(str(o), 0.0)) for o in OUTCOMES_BP}
        z = sum(probs.values()) or 1.0
        probs = {k: v / z for k, v in probs.items()}
        nums = re.findall(r"\d+(?:[.,]\d+)?", c.output.get("reasoning", ""))
        results.append({"completion": _dump(c), "probabilities": probs, "numbers_from_memory": len(nums)})
    by_outcome = {str(o): [r["probabilities"][str(o)] for r in results] for o in OUTCOMES_BP}
    return {
        "analyst": "naive", "arm": "A", "prompt_version": "naive-v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_hash": snap.hash, "backend": backend.name, "runs": results,
        "summary": {
            "runs": runs,
            "mean_probabilities": {k: round(statistics.mean(v), 4) for k, v in by_outcome.items()},
            "max_std_pp": round(100 * max(statistics.pstdev(v) for v in by_outcome.values()), 2) if runs > 1 else None,
            "groundedness_pct_mean": 0.0,
            "leakage_total": sum(r["numbers_from_memory"] for r in results),
        },
    }


def save(rec: dict) -> Path:
    folder = ANALYSES_DIR / rec["snapshot_hash"][:12]
    folder.mkdir(parents=True, exist_ok=True)
    stamp = rec["created_at"].replace(":", "").replace("-", "").replace("+0000", "Z")
    path = folder / f"{stamp}_{rec['analyst']}.json"
    path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    return path


def latest(snapshot_hash: str, analyst: str) -> dict | None:
    folder = ANALYSES_DIR / snapshot_hash[:12]
    if not folder.exists():
        return None
    files = sorted(folder.glob(f"*_{analyst}.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def _dump(c: Completion) -> dict:
    return {"output": c.output, "backend": c.backend, "model": c.model, "duration_s": c.duration_s,
            "prompt_hash": c.prompt_hash, "meta": c.meta}
