import json
from datetime import date

import pytest

from fedcast.llm import analyst
from fedcast.llm.backend import FakeBackend, ReplayBackend, parse_json_text
from fedcast.snapshot import Item, Snapshot
from tests.test_financial_comms import LATEST, PREV


def comms_snapshot():
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("calendar", "calendar", "t", {"next_meeting": "2026-10-28", "meetings": ["2026-10-28"]}))
    snap.add(Item.make("fed.statement.2026-07-29", "document", "t", {"url": "u", "text": PREV}))
    snap.add(Item.make("fed.statement.2026-09-16", "document", "t", {"url": "u", "text": LATEST}))
    snap.add(Item.make("human.doc.H5-001", "human_document", "t", {
        "id": "H5-001", "title": "My note", "relevance": "related", "text": "Claims have drifted up for six weeks."}))
    return snap


WATCH = [{"id": "H1-001", "directive": "Check for dissents", "status": "active"},
         {"id": "H1-002", "directive": "Mention of energy prices", "status": "active"}]

GOOD = {
    "claims": [
        {"text": "The committee raised rates by a quarter point.", "quote": "raise the target range for the federal funds rate by 1/4 percentage point",
         "item": "fed.statement.2026-09-16", "lean": "hawkish"},
        {"text": "Inflation is still described as elevated.", "quote": "Inflation remains elevated.",
         "item": "fed.statement.2026-09-16", "lean": "hawkish"},
        {"text": "In July one member dissented in favour of a hike.", "quote": "Voting against this action was Jane Doe",
         "item": "fed.statement.2026-07-29", "lean": "hawkish"},
        {"text": "My note says claims rose for 6 weeks.", "quote": "Claims have drifted up for six weeks.",
         "item": "human.doc.H5-001", "lean": "dovish"},
    ],
    "watchouts": [{"id": "H1-001", "status": "found", "evidence": "Jane Doe dissented in July"},
                  {"id": "H1-002", "status": "not_found", "evidence": "no mention of energy"}],
    "tilt_bp": 6, "confidence": "medium", "summary": "Hawkish communications.",
}


def test_prompt_contains_only_snapshot_evidence_and_watchouts():
    p = analyst.build_prompt(comms_snapshot(), WATCH)
    assert "H1-001: Check for dissents" in p and "ITEM fed.statement.2026-09-16" in p and "My note" in p
    assert "=== DETERMINISTIC PRE-READ" in p


def test_verifier_counts_quotes_numbers_and_watchouts():
    v = analyst.verify(GOOD, comms_snapshot(), WATCH)
    assert v["n_claims"] == 4 and v["n_verified"] == 4 and v["groundedness_pct"] == 100.0
    # "6" in the fourth claim is not in the item ("six" is), so it counts as a number from outside the evidence
    assert v["leakage_count"] == 1 and v["claims"][3]["leaked_numbers"] == ["6"]
    assert v["watchouts_missing"] == [] and v["tilt_bp"] == 6


def test_verifier_catches_fabricated_quotes_missing_watchouts_and_clips_tilt():
    bad = json.loads(json.dumps(GOOD))
    bad["claims"][0]["quote"] = "raise the target range by 50 basis points"   # not in the statement
    bad["watchouts"] = bad["watchouts"][:1]
    bad["tilt_bp"] = 25
    v = analyst.verify(bad, comms_snapshot(), WATCH)
    assert v["n_verified"] == 3 and v["groundedness_pct"] == 75.0
    assert v["watchouts_missing"] == ["H1-002"]
    assert v["tilt_bp"] == 10 and v["tilt_clipped"]


def test_comms_run_summarises_repeatability_over_runs():
    other = json.loads(json.dumps(GOOD)); other["tilt_bp"] = 2
    rec = analyst.run_comms(comms_snapshot(), FakeBackend([GOOD, other, GOOD]), WATCH, runs=3)
    s = rec["summary"]
    assert s["runs"] == 3 and s["tilt_mean_bp"] == pytest.approx(14 / 3, abs=0.01)
    assert s["tilt_std_bp"] > 0 and s["groundedness_pct_mean"] == 100.0 and s["watchouts_missing_total"] == 0
    assert rec["arm"] == "D" and rec["backend"] == "fake"


def test_naive_control_is_scored_as_ungrounded():
    naive = {"probabilities": {"-50": 0, "-25": 0.1, "0": 0.6, "25": 0.3, "50": 0}, "reasoning": "Inflation is 3.3% so a hike is likely."}
    rec = analyst.run_naive(comms_snapshot(), FakeBackend(naive), runs=2)
    assert rec["arm"] == "A" and rec["summary"]["groundedness_pct_mean"] == 0.0
    assert rec["summary"]["leakage_total"] == 2 and rec["summary"]["max_std_pp"] == 0.0


def test_replay_backend_records_then_serves(tmp_path):
    inner = FakeBackend(GOOD)
    rb = ReplayBackend(tmp_path, inner)
    c1 = rb.complete("s", "p", {"type": "object"})
    c2 = rb.complete("s", "p", {"type": "object"})
    assert c1.output == c2.output and len(inner.calls) == 1 and c2.backend == "replay:fake"
    with pytest.raises(LookupError):
        ReplayBackend(tmp_path).complete("s", "different", {"type": "object"})


def test_json_text_parsing_tolerates_fences():
    assert parse_json_text('```json\n{"a": 1}\n```') == {"a": 1}
