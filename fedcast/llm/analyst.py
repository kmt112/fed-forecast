"""LLM specialist analysts and the naive control, with a code verifier.

Harness rules, enforced here rather than asked for:
  * the model sees only snapshot items, deterministic pre-reads of the signals, and your typed inputs
    (the backend has no tools);
  * every claim must carry a verbatim quote and the id of the item it comes from; the verifier string-matches
    the quote against that item, so groundedness (S2) is a count, not an opinion;
  * numbers in a claim that do not occur in the quoted item are leakage (S3);
  * every active watch-out must be addressed by id;
  * the output is a bounded tilt in basis points, never the final number.

Specialists share one schema and one verifier; they differ in the question asked and the evidence shown:
  communications   statements, the diff, the press conference, policy speeches, the minutes
  minutes_digest   the minutes only: the balance of views in the committee's own weighting words
  inflation        the inflation-gap pre-read, the SEP inflation medians, the statement
  labour           the labour-slack pre-read, the SEP unemployment medians, the statement
  financial        the financial-conditions pre-read, the market data, the statement
The naive control (analyst 1) asks the question with no evidence at all; by construction it cannot
cite, so its groundedness is 0 and every number it gives is from memory.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fedcast import OUTCOMES_BP, config
from fedcast.llm.backend import Completion, LLMBackend, prompt_hash
from fedcast.signals import base_rates, comms, financial, inflation, labour, sep
from fedcast.snapshot import Snapshot

ANALYSES_DIR = config.ROOT / "analyses"
TILT_CAP_BP = 10
PROMPT_VERSION = "specialists-v3-repair"
REPAIR_ROUNDS = 1  # one retry when the verifier finds a quote it cannot locate or a number not in the evidence

SYSTEM = ("You are an analyst inside an audited Federal Reserve forecasting harness. You may use ONLY the evidence in "
          "the user message. Do not use anything you remember about the economy, the Fed or markets; if the evidence "
          "does not contain something, say it is not in the evidence. Every claim must quote the evidence verbatim "
          "(copy the exact characters of a contiguous passage) and name the item id it came from. Numbers may appear "
          "in a claim only if they appear in the quoted item. Output only JSON matching the schema.")

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

_POLICY_SPEECH = re.compile(r"econom|monetary|policy|outlook|inflation|labou?r|employment|mandate|rates?\b", re.I)


_QUOTE_MAP = str.maketrans({chr(0x2019): "'", chr(0x2018): "'", chr(0x201C): "", chr(0x201D): "", '"': "",
                            chr(0x2013): "-", chr(0x2014): "-", chr(0xA0): " ", chr(0xFFFD): "'"})  # typography and JSON quotes fold away


def _norm(s: str) -> str:
    """Whitespace-, case- and typography-insensitive form used for quote matching. Curly quotes, dashes and the
    replacement character that PDF extraction leaves for an apostrophe all fold to their plain equivalents."""
    return re.sub(r"\s+", " ", s.translate(_QUOTE_MAP)).strip().lower()


def render_signal(name: str, sig: dict) -> str:
    """Readable key: value lines. The same text is shown to the model and matched against by the verifier."""
    lines = []
    for k, v in sig.items():
        if k in ("signal", "evidence"):
            continue
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")
    return "\n".join(lines)


def _safe(fn: Callable, snap: Snapshot) -> dict | None:
    try:
        return fn(snap)
    except (ValueError, KeyError):
        return None


@dataclass
class Spec:
    name: str
    question: str
    items: Callable[[Snapshot], list[str]]
    pre_reads: Callable[[Snapshot], dict[str, str]] = field(default_factory=lambda: (lambda snap: {}))
    max_chars: int = 60000


def _docs(prefixes: tuple[str, ...]) -> Callable[[Snapshot], list[str]]:
    return lambda snap: sorted(i for i in snap.items if i.startswith(prefixes))


def _tone_pre(snap: Snapshot) -> dict[str, str]:
    t = _safe(comms.compute, snap)
    return {"signal.tone": json.dumps({"vote": t["vote"], "lexicon": t["lexicon"], "diff": t["diff"]}, ensure_ascii=False)} if t else {}


def _macro_pre(*fns: tuple[str, Callable]) -> Callable[[Snapshot], dict[str, str]]:
    def inner(snap: Snapshot) -> dict[str, str]:
        out = {}
        for name, fn in fns:
            s = _safe(fn, snap)
            if s:
                out[name] = render_signal(name, s)
        return out
    return inner


def _all_pre(snap: Snapshot) -> dict[str, str]:
    out = _tone_pre(snap)
    out.update(_macro_pre(("signal.inflation", inflation.compute), ("signal.labour", labour.compute),
                          ("signal.financial", financial.compute), ("signal.base_rates", base_rates.compute),
                          ("signal.projections", sep.compute))(snap))
    return out


def _all_docs(snap: Snapshot) -> list[str]:
    return (_docs(("fed.statement.", "fed.presconf.", "fed.minutes.", "fed.sep."))(snap)
            + (["fed.speeches"] if "fed.speeches" in snap.items else []) + _docs(("human.doc.",))(snap))


GENERALIST = Spec(
    "generalist",
    "From all of the evidence, which way does the next decision lean, and why?",
    _all_docs, _all_pre)

SPECIALISTS: dict[str, Spec] = {
    "communications": Spec(
        "communications",
        "From the committee's own communications (statements, the press conference, policy speeches, the minutes), "
        "which way does the next decision lean, and why?",
        lambda snap: _docs(("fed.statement.", "fed.presconf.", "fed.minutes."))(snap)
        + (["fed.speeches"] if "fed.speeches" in snap.items else []) + _docs(("human.doc.",))(snap),
        _tone_pre),
    "minutes_digest": Spec(
        "minutes_digest",
        "Digest the minutes: what did 'most', 'many', 'several', 'some' or 'a few' participants think about inflation, "
        "the labour market, the appropriate path of policy and the risks, and what did they say would change their "
        "minds? Each claim must quote the passage. Then give the net lean the minutes imply for the next decision.",
        _docs(("fed.minutes.",)), lambda snap: {}),
    "inflation": Spec(
        "inflation",
        "From the inflation evidence (the computed inflation-gap pre-read, the committee's inflation projections and "
        "what the statement says about inflation), is inflation arguing for a hike, a hold or a cut at the next "
        "meeting, and how strongly?",
        lambda snap: _docs(("fed.statement.", "fed.sep."))(snap) + _docs(("human.doc.",))(snap),
        _macro_pre(("signal.inflation", inflation.compute), ("signal.projections", sep.compute))),
    "labour": Spec(
        "labour",
        "From the labour-market evidence (the computed labour-slack pre-read, the committee's unemployment projections "
        "and what the statement says about employment), is the labour market arguing for a hike, a hold or a cut at "
        "the next meeting, and how strongly?",
        lambda snap: _docs(("fed.statement.", "fed.sep."))(snap) + _docs(("human.doc.",))(snap),
        _macro_pre(("signal.labour", labour.compute), ("signal.projections", sep.compute))),
    "financial": Spec(
        "financial",
        "From the financial-conditions evidence (the computed pre-read of the 2-year gap, breakevens and the NFCI, "
        "the base rates, and what the statement says about financial conditions), what is the bond market expecting "
        "and does it corroborate or contradict the other evidence?",
        lambda snap: _docs(("fed.statement.",))(snap) + _docs(("human.doc.",))(snap),
        _macro_pre(("signal.financial", financial.compute), ("signal.base_rates", base_rates.compute))),
}


def _item_text(snap: Snapshot, item_id: str, max_chars: int) -> str:
    content = snap.get(item_id)
    if item_id == "fed.speeches":
        parts = []
        for s in content["speeches"]:
            if _POLICY_SPEECH.search(s["title"]):
                parts.append(f"--- speech {s['date']} {s['speaker']}: {s['title']} ---\n{s['text'][:12000]}")
        return "\n".join(parts) or "(no policy-related speeches in the period)"
    if item_id.startswith("fed.sep."):
        return "Median projections (year: value) and the previous SEP's medians:\n" + render_signal("sep", {
            "medians": content["medians"], "previous": content["previous"]})
    if isinstance(content, dict) and "text" in content:
        return content["text"][:max_chars]
    return json.dumps(content, ensure_ascii=False)[:max_chars]


def build_prompt(snap: Snapshot, watchlist: list[dict], spec: Spec | None = None) -> str:
    spec = spec or SPECIALISTS["communications"]
    cal = snap.get("calendar")
    parts = [f"Snapshot date: {snap.as_of.isoformat()}. Next FOMC decision: {cal['next_meeting']}.",
             f"Question: {spec.question} Give a net tilt between -{TILT_CAP_BP} (strongly dovish) and +{TILT_CAP_BP} "
             "(strongly hawkish) basis points, with claims that each quote one item."]
    for name, text in spec.pre_reads(snap).items():
        parts += ["", f"=== DETERMINISTIC PRE-READ (item: {name}) ===", text]
    active = [w for w in watchlist if w.get("status") == "active"]
    parts += ["", "=== WATCH-OUTS (each must be addressed by id) ==="]
    parts += [f"{w['id']}: {w['directive']}" for w in active] or ["none"]
    for item_id in spec.items(snap):
        kind = snap.items[item_id].kind
        label = "your document: " + snap.get(item_id)["title"] if kind == "human_document" else kind
        parts += ["", f"=== ITEM {item_id} ({label}) ===", _item_text(snap, item_id, spec.max_chars)]
    return "\n".join(parts)


def _number_forms(n: str) -> set[str]:
    """A number as written, plus the same value with or without trailing decimals (77 <-> 77.0) and its percent
    and fraction forms (65.3 <-> 0.653, 3.75 <-> 375)."""
    forms = {n}
    try:
        v = float(n)
    except ValueError:
        return forms
    if v == 0:
        return {n, "0", "0.0"}  # a zero written by the model matches a zero in the evidence ("12-0", "against": 0)
    for alt in (v, v / 100, v * 100):
        for fmt in ("{:g}", "{:.1f}", "{:.2f}", "{:.3f}", "{:.4f}"):
            forms.add(fmt.format(alt))
    return {f for f in forms if f and f != "0"}  # a tiny non-zero number never matches the evidence's zeros


def _number_in_evidence(n: str, evidence_numbers: set[str]) -> bool:
    """True if the number, or its percent / fraction form, occurs as a whole number token in the evidence
    (so a claim's "6" is not excused by the 6 inside "2026")."""
    return any(f in evidence_numbers for f in _number_forms(n.replace(",", "")))


def verify(output: dict, snap: Snapshot, watchlist: list[dict], spec: Spec | None = None) -> dict:
    spec = spec or SPECIALISTS["communications"]
    texts = {}
    for item_id in snap.items:
        content = snap.get(item_id)
        if item_id == "fed.speeches":
            texts[item_id] = _norm("\n".join(s["text"] for s in content["speeches"]))
        elif item_id.startswith("fed.sep."):
            texts[item_id] = _norm(_item_text(snap, item_id, 10 ** 6))
        elif isinstance(content, dict) and "text" in content:
            texts[item_id] = _norm(content["text"])
        else:
            texts[item_id] = _norm(json.dumps(content, ensure_ascii=False))
    for name, text in spec.pre_reads(snap).items():
        texts[name] = _norm(text)
    if "signal.tone" not in texts:
        t = _safe(comms.compute, snap)
        if t:
            texts["signal.tone"] = _norm(json.dumps({"vote": t["vote"], "lexicon": t["lexicon"], "diff": t["diff"]}, ensure_ascii=False))

    evidence_numbers = set(re.findall(r"[0-9]+(?:[.][0-9]+)?", " ".join(texts.values()).replace(",", "")))
    claims = []
    for c in output.get("claims", []):
        item_text = texts.get(c.get("item", ""), "")
        quote_ok = bool(c.get("quote")) and _norm(c["quote"]) in item_text
        nums = set(re.findall(r"\d+(?:[.,]\d+)?", c.get("text", "")))
        leaked = sorted(n for n in nums if not _number_in_evidence(n, evidence_numbers))
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


def repair_reasons(v: dict) -> list[dict]:
    """What the verifier could not accept in an answer: a quote it could not find in the named item, or a number that
    appears nowhere in the evidence. Missing watch-outs and a clipped tilt are reported, not repaired."""
    out = []
    for c in v["claims"]:
        if not c["verified"]:
            out.append({"claim": c["text"], "item": c.get("item", ""), "quote": c.get("quote", ""), "problem": "quote not found"})
        if c["leaked_numbers"]:
            out.append({"claim": c["text"], "item": c.get("item", ""), "quote": c.get("quote", ""),
                        "problem": "numbers not in the evidence: " + ", ".join(c["leaked_numbers"])})
    return out


def repair_prompt(prompt: str, reasons: list[dict]) -> str:
    """The original prompt plus the verifier's report. The model may fix or drop the listed claims; it may not add
    new ones. The same schema applies, so the repaired answer is verified exactly like the first."""
    lines = ["", "=== VERIFIER REPORT (code checked your previous answer against the evidence) ===",
             "The following claims could not be verified. For each one, either replace the quote with a passage copied "
             "verbatim from the item named (or name the item the passage really comes from), remove any number that is not "
             "in the evidence, or drop the claim. Do not add new claims. Return the complete answer again in the same format."]
    for i, r in enumerate(reasons, 1):
        lines.append(f"{i}. [{r['problem']}] claim: {r['claim']} | item: {r['item']} | quote given: {r['quote']}")
    return prompt + "\n".join(lines)


def run_specialist(spec: Spec, snap: Snapshot, backend: LLMBackend, watchlist: list[dict], runs: int = 1,
                   log: Callable[[str], None] | None = None, repair: bool = True) -> dict:
    """Run one analyst `runs` times. With `repair` (the specialists, analysts 4 to 8), a run whose answer the verifier
    cannot fully accept is sent back once with the verifier's report; both answers are recorded, the repaired one counts."""
    say = log or (lambda m: print(m, file=sys.stderr, flush=True))
    prompt = build_prompt(snap, watchlist, spec)
    results = []
    for i in range(runs):
        t0 = time.time()
        say(f"  {spec.name} run {i + 1}/{runs}: calling {backend.name}…")
        c = backend.complete(SYSTEM, prompt, SCHEMA, run=i)
        v = verify(c.output, snap, watchlist, spec)
        say(f"  {spec.name} run {i + 1}/{runs}: done in {time.time() - t0:.0f}s, tilt {v['tilt_bp']:+.0f} bp, "
            f"{v['n_verified']}/{v['n_claims']} claims verified")
        result = {"completion": _dump(c), "verification": v}
        reasons = repair_reasons(v) if repair else []
        for _ in range(REPAIR_ROUNDS if reasons else 0):
            say(f"  {spec.name} run {i + 1}/{runs}: {len(reasons)} claim(s) sent back to the model once…")
            c2 = backend.complete(SYSTEM, repair_prompt(prompt, reasons), SCHEMA, run=i)
            v2 = verify(c2.output, snap, watchlist, spec)
            say(f"  {spec.name} run {i + 1}/{runs}: repaired, tilt {v['tilt_bp']:+.0f} -> {v2['tilt_bp']:+.0f} bp, "
                f"{v2['n_verified']}/{v2['n_claims']} claims verified")
            result = {"completion": _dump(c2), "verification": v2,
                      "repair": {"first": {"completion": _dump(c), "verification": v}, "reasons": reasons,
                                 "tilt_before_bp": v["tilt_bp"], "groundedness_before_pct": v["groundedness_pct"],
                                 "leakage_before": v["leakage_count"], "n_verified_before": v["n_verified"], "n_claims_before": v["n_claims"]}}
        results.append(result)
    tilts = [r["verification"]["tilt_bp"] for r in results]
    repaired = [r for r in results if "repair" in r]
    before_g = [r["repair"]["groundedness_before_pct"] if "repair" in r else r["verification"]["groundedness_pct"] for r in results]
    return {
        "analyst": spec.name, "analyst_no": ANALYST_NO[spec.name], "prompt_version": PROMPT_VERSION, "prompt_chars": len(prompt),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_hash": snap.hash, "backend": backend.name, "runs": results,
        "summary": {
            "runs": runs, "tilt_mean_bp": round(statistics.mean(tilts), 2),
            "tilt_std_bp": round(statistics.pstdev(tilts), 2) if runs > 1 else None,
            "groundedness_pct_mean": round(statistics.mean(r["verification"]["groundedness_pct"] for r in results), 1),
            "leakage_total": sum(r["verification"]["leakage_count"] for r in results),
            "watchouts_missing_total": sum(len(r["verification"]["watchouts_missing"]) for r in results),
            "repairs": len(repaired),
            "repair_tilt_changes": sum(1 for r in repaired if r["repair"]["tilt_before_bp"] != r["verification"]["tilt_bp"]),
            "groundedness_before_repair_pct_mean": round(statistics.mean(before_g), 1),
            "leakage_before_repair_total": sum(r["repair"]["leakage_before"] if "repair" in r else r["verification"]["leakage_count"] for r in results),
        },
    }


def run_comms(snap: Snapshot, backend: LLMBackend, watchlist: list[dict], runs: int = 1) -> dict:
    return run_specialist(SPECIALISTS["communications"], snap, backend, watchlist, runs)


def run_evidence_only(snap: Snapshot, backend: LLMBackend, runs: int = 1, log: Callable[[str], None] | None = None) -> dict:
    """Analyst 2: the full evidence is shown, but the model answers with a free-form distribution and
    reasoning; nothing is cited, so groundedness cannot be measured. Leakage can: numbers in the reasoning
    are checked against the evidence."""
    say = log or (lambda m: print(m, file=sys.stderr, flush=True))
    cal = snap.get("calendar")
    parts = [f"Snapshot date: {snap.as_of.isoformat()}. Next FOMC decision: {cal['next_meeting']}.",
             "Using ONLY the evidence below, give a probability for each outcome in basis points of change "
             "(-50, -25, 0, 25, 50), summing to 1, and a short reasoning."]
    for name, text in _all_pre(snap).items():
        parts += ["", f"=== DETERMINISTIC PRE-READ (item: {name}) ===", text]
    for item_id in _all_docs(snap):
        parts += ["", f"=== ITEM {item_id} ===", _item_text(snap, item_id, 60000)]
    prompt = "\n".join(parts)
    texts = {}
    for item_id in _all_docs(snap):
        texts[item_id] = _norm(_item_text(snap, item_id, 10 ** 6))
    for name, text in _all_pre(snap).items():
        texts[name] = _norm(text)
    evidence_numbers = set(re.findall(r"[0-9]+(?:[.][0-9]+)?", " ".join(texts.values()).replace(",", "")))
    results = []
    for i in range(runs):
        t0 = time.time()
        say(f"  evidence_only run {i + 1}/{runs}: calling {backend.name}…")
        c = backend.complete(SYSTEM, prompt, NAIVE_SCHEMA, run=i)
        say(f"  evidence_only run {i + 1}/{runs}: done in {time.time() - t0:.0f}s")
        probs = {str(o): float(c.output["probabilities"].get(str(o), 0.0)) for o in OUTCOMES_BP}
        z = sum(probs.values()) or 1.0
        probs = {k: v / z for k, v in probs.items()}
        nums = set(re.findall(r"\d+(?:[.,]\d+)?", c.output.get("reasoning", "")))
        leaked = sorted(n for n in nums if not _number_in_evidence(n, evidence_numbers))
        results.append({"completion": _dump(c), "probabilities": probs, "numbers_from_memory": len(leaked), "leaked_numbers": leaked})
    by_outcome = {str(o): [r["probabilities"][str(o)] for r in results] for o in OUTCOMES_BP}
    return {
        "analyst": "evidence_only", "analyst_no": 2, "prompt_version": "evidence-only-v1", "prompt_chars": len(prompt),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_hash": snap.hash, "backend": backend.name, "runs": results,
        "summary": {
            "runs": runs,
            "mean_probabilities": {k: round(statistics.mean(v), 4) for k, v in by_outcome.items()},
            "max_std_pp": round(100 * max(statistics.pstdev(v) for v in by_outcome.values()), 2) if runs > 1 else None,
            "groundedness_pct_mean": None,
            "leakage_total": sum(r["numbers_from_memory"] for r in results),
        },
    }


def run_naive(snap: Snapshot, backend: LLMBackend, runs: int = 1, log: Callable[[str], None] | None = None) -> dict:
    """Analyst 1: the same question with no evidence. Nothing to cite, so nothing can be verified."""
    say = log or (lambda m: print(m, file=sys.stderr, flush=True))
    cal = snap.get("calendar")
    prompt = (f"Today is {snap.as_of.isoformat()}. What will the FOMC decide at its {cal['next_meeting']} meeting? "
              "Give a probability for each outcome in basis points of change (-50, -25, 0, 25, 50), summing to 1, "
              "and a short reasoning.")
    results = []
    for i in range(runs):
        t0 = time.time()
        say(f"  naive run {i + 1}/{runs}: calling {backend.name}…")
        c = backend.complete("You are a Fed watcher. Output only JSON matching the schema.", prompt, NAIVE_SCHEMA, run=i)
        say(f"  naive run {i + 1}/{runs}: done in {time.time() - t0:.0f}s")
        probs = {str(o): float(c.output["probabilities"].get(str(o), 0.0)) for o in OUTCOMES_BP}
        z = sum(probs.values()) or 1.0
        probs = {k: v / z for k, v in probs.items()}
        nums = re.findall(r"\d+(?:[.,]\d+)?", c.output.get("reasoning", ""))
        results.append({"completion": _dump(c), "probabilities": probs, "numbers_from_memory": len(nums)})
    by_outcome = {str(o): [r["probabilities"][str(o)] for r in results] for o in OUTCOMES_BP}
    return {
        "analyst": "naive", "analyst_no": 1, "prompt_version": "naive-v1",
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


def reverify(rec: dict, snap: Snapshot, watchlist: list[dict]) -> dict:
    """Re-run the code verifier over a recorded analysis (after a verifier change); no model calls."""
    if rec["analyst"] in ("naive", "evidence_only"):
        return rec
    spec = GENERALIST if rec["analyst"] == "generalist" else SPECIALISTS[rec["analyst"]]
    for r in rec["runs"]:
        r["verification"] = verify(r["completion"]["output"], snap, watchlist, spec)
    tilts = [r["verification"]["tilt_bp"] for r in rec["runs"]]
    runs = len(rec["runs"])
    rec["summary"].update({
        "tilt_mean_bp": round(statistics.mean(tilts), 2),
        "tilt_std_bp": round(statistics.pstdev(tilts), 2) if runs > 1 else None,
        "groundedness_pct_mean": round(statistics.mean(r["verification"]["groundedness_pct"] for r in rec["runs"]), 1),
        "leakage_total": sum(r["verification"]["leakage_count"] for r in rec["runs"]),
        "watchouts_missing_total": sum(len(r["verification"]["watchouts_missing"]) for r in rec["runs"]),
    })
    rec["reverified_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return rec


def describe_agents(snap: Snapshot, watchlist: list[dict]) -> list[dict]:
    """The exact inputs each agent receives on this snapshot: question, evidence items, pre-reads, the full prompt
    text and its hash, the schema and the system prompt. Built by the same code that builds the real prompts."""
    cal = snap.get("calendar")
    out = []
    for name, spec in list(SPECIALISTS.items()) + [("generalist", GENERALIST)]:
        prompt = build_prompt(snap, watchlist, spec)
        out.append({"name": name, "analyst_no": ANALYST_NO[name], "question": spec.question,
                    "items": spec.items(snap), "pre_reads": list(spec.pre_reads(snap)), "system": SYSTEM,
                    "schema": SCHEMA, "prompt": prompt, "prompt_chars": len(prompt),
                    "prompt_hash": prompt_hash(SYSTEM, prompt, SCHEMA, 0), "output": "claims with quotes, watch-outs, an opinion from −10 to +10"})
    b_parts = [f"Snapshot date: {snap.as_of.isoformat()}. Next FOMC decision: {cal['next_meeting']}.",
               "Using ONLY the evidence below, give a probability for each outcome in basis points of change "
               "(-50, -25, 0, 25, 50), summing to 1, and a short reasoning."]
    for n_, text in _all_pre(snap).items():
        b_parts += ["", f"=== DETERMINISTIC PRE-READ (item: {n_}) ===", text]
    for item_id in _all_docs(snap):
        b_parts += ["", f"=== ITEM {item_id} ===", _item_text(snap, item_id, 60000)]
    b_prompt = "\n".join(b_parts)
    out.append({"name": "evidence_only", "analyst_no": 2, "question": b_parts[1], "items": _all_docs(snap),
                "pre_reads": list(_all_pre(snap)), "system": SYSTEM, "schema": NAIVE_SCHEMA, "prompt": b_prompt,
                "prompt_chars": len(b_prompt), "prompt_hash": prompt_hash(SYSTEM, b_prompt, NAIVE_SCHEMA, 0),
                "output": "probabilities and free-form reasoning"})
    n_system = "You are a Fed watcher. Output only JSON matching the schema."
    n_prompt = (f"Today is {snap.as_of.isoformat()}. What will the FOMC decide at its {cal['next_meeting']} meeting? "
                "Give a probability for each outcome in basis points of change (-50, -25, 0, 25, 50), summing to 1, "
                "and a short reasoning.")
    out.append({"name": "naive", "analyst_no": 1, "question": n_prompt, "items": [], "pre_reads": [], "system": n_system,
                "schema": NAIVE_SCHEMA, "prompt": n_prompt, "prompt_chars": len(n_prompt),
                "prompt_hash": prompt_hash(n_system, n_prompt, NAIVE_SCHEMA, 0), "output": "probabilities and free-form reasoning"})
    return out


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


def record_at(snapshot_hash: str, analyst: str, created_at: str) -> dict | None:
    """The one record a ledger entry says it used (its created_at), not the latest: a forecast must replay against the
    analyst runs it was made from, even after newer runs are recorded on the same snapshot."""
    folder = ANALYSES_DIR / snapshot_hash[:12]
    if not folder.exists():
        return None
    for path in folder.glob(f"*_{analyst}.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("created_at") == created_at:
            return rec
    return None


ALL_ANALYSTS = list(SPECIALISTS) + ["generalist", "evidence_only", "naive"]
# The eight analysts, numbered the way they appear everywhere: 1 to 3 read all the evidence with ever more harness,
# 4 to 8 are the specialists. The number is the rung on the ladder.
ANALYST_NO = {"naive": 1, "evidence_only": 2, "generalist": 3, "communications": 4, "minutes_digest": 5,
              "inflation": 6, "labour": 7, "financial": 8}


def latest_all(snapshot_hash: str) -> dict[str, dict | None]:
    return {name: latest(snapshot_hash, name) for name in ALL_ANALYSTS}


def _dump(c: Completion) -> dict:
    return {"output": c.output, "backend": c.backend, "model": c.model, "duration_s": c.duration_s,
            "prompt_hash": c.prompt_hash, "meta": c.meta}
