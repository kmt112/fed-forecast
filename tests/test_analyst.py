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
    # "6" in the fourth claim is not anywhere in the evidence ("six" is), so it counts as a number from outside
    assert v["leakage_count"] == 1 and v["claims"][3]["leaked_numbers"] == ["6"]
    assert v["watchouts_missing"] == [] and v["tilt_bp"] == 6


def test_numbers_in_percent_or_fraction_form_and_elsewhere_in_the_snapshot_are_not_leaks():
    assert analyst._number_in_evidence("65.3", {"0.653"})
    assert analyst._number_in_evidence("0.653", {"65.3"})
    assert analyst._number_in_evidence("3.75", {"3.75", "4.00"})
    assert not analyst._number_in_evidence("7.25", {"3.75", "4.00"})
    assert not analyst._number_in_evidence("6", {"2026", "16"})
    assert analyst._number_in_evidence("77", {"77.0"}) and analyst._number_in_evidence("77.0", {"77"})
    out = json.loads(json.dumps(GOOD))
    out["claims"][0]["text"] = "The committee raised rates to 3-3/4 to 4 percent."  # numbers in the other statement item
    v = analyst.verify(out, comms_snapshot(), WATCH)
    assert v["claims"][0]["leaked_numbers"] == []


def test_json_quotation_marks_do_not_break_quote_matching():
    assert analyst._norm('"given_last": {"cut": 0.0}') == analyst._norm("given_last: {cut: 0.0}")


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
    assert rec["analyst_no"] == 4 and rec["backend"] == "fake"


def test_naive_control_is_scored_as_ungrounded():
    naive = {"probabilities": {"-50": 0, "-25": 0.1, "0": 0.6, "25": 0.3, "50": 0}, "reasoning": "Inflation is 3.3% so a hike is likely."}
    rec = analyst.run_naive(comms_snapshot(), FakeBackend(naive), runs=2)
    assert rec["analyst_no"] == 1 and rec["summary"]["groundedness_pct_mean"] == 0.0
    assert rec["summary"]["leakage_total"] == 2 and rec["summary"]["max_std_pp"] == 0.0


def test_replay_backend_records_then_serves(tmp_path):
    inner = FakeBackend(GOOD)
    rb = ReplayBackend(tmp_path, inner)
    c1 = rb.complete("s", "p", {"type": "object"})
    c2 = rb.complete("s", "p", {"type": "object"})
    assert c1.output == c2.output and len(inner.calls) == 1 and c2.backend == "replay:fake"
    rb.complete("s", "p", {"type": "object"}, run=1)   # a deliberate repeat is a different call
    assert len(inner.calls) == 2
    with pytest.raises(LookupError):
        ReplayBackend(tmp_path).complete("s", "different", {"type": "object"})


def test_json_text_parsing_tolerates_fences():
    assert parse_json_text('```json\n{"a": 1}\n```') == {"a": 1}


def test_quote_matching_ignores_typography():
    assert analyst._norm("I’m not\ngoing to  prejudge – any") == "i'm not going to prejudge - any"
    assert analyst._norm("I�m") == "i'm"


def test_describe_agents_lists_every_agent_with_its_inputs():
    agents = analyst.describe_agents(comms_snapshot(), WATCH)
    names = [a["name"] for a in agents]
    assert set(names) >= {"naive", "evidence_only", "generalist", "communications", "minutes_digest", "inflation", "labour", "financial"}
    comm = next(a for a in agents if a["name"] == "communications")
    assert "fed.statement.2026-09-16" in comm["items"] and comm["prompt_chars"] == len(comm["prompt"]) and len(comm["prompt_hash"]) == 16
    naive = next(a for a in agents if a["name"] == "naive")
    assert naive["items"] == [] and naive["pre_reads"] == []


def test_zero_in_a_claim_matches_zero_in_the_evidence():
    from fedcast.llm.analyst import _number_in_evidence

    assert _number_in_evidence("0", {"12", "0"})          # "a 12-0 vote" against '"against": 0'
    assert not _number_in_evidence("0.004", {"12", "0"})  # a tiny number is not the evidence's zero
    assert not _number_in_evidence("0", {"12"})


def _bad():
    bad = json.loads(json.dumps(GOOD))
    bad["claims"][0]["quote"] = "raise the target range by 50 basis points"   # not in the statement
    return bad


def test_repair_loop_sends_the_answer_back_once_with_the_verifier_report_and_keeps_both():
    fb = FakeBackend([_bad(), GOOD])
    rec = analyst.run_comms(comms_snapshot(), fb, WATCH, runs=1)
    assert len(fb.calls) == 2
    prompt2 = fb.calls[1][1]
    assert "VERIFIER REPORT" in prompt2 and "raise the target range by 50 basis points" in prompt2 and "quote not found" in prompt2
    assert prompt2.startswith(fb.calls[0][1])  # the original prompt, unchanged, plus the report
    run = rec["runs"][0]
    assert run["verification"]["groundedness_pct"] == 100.0           # the repaired answer counts
    assert run["repair"]["first"]["verification"]["groundedness_pct"] == 75.0
    assert run["repair"]["n_verified_before"] == 3 and run["repair"]["reasons"][0]["problem"] == "quote not found"
    s = rec["summary"]
    assert s["repairs"] == 1 and s["groundedness_pct_mean"] == 100.0 and s["groundedness_before_repair_pct_mean"] == 75.0
    assert rec["prompt_version"] == "specialists-v3-repair"


def test_repair_is_one_round_only_and_a_still_bad_answer_stays_unverified():
    fb = FakeBackend([_bad(), _bad()])
    rec = analyst.run_comms(comms_snapshot(), fb, WATCH, runs=1)
    assert len(fb.calls) == 2
    assert rec["runs"][0]["verification"]["groundedness_pct"] == 75.0 and rec["summary"]["repairs"] == 1


def test_no_repair_when_the_verifier_accepts_the_answer_and_none_for_the_generalist():
    clean = json.loads(json.dumps(GOOD))
    clean["claims"][3]["text"] = "My note says claims rose for six weeks."   # GOOD carries a deliberate leaked "6"
    fb = FakeBackend(clean)
    rec = analyst.run_comms(comms_snapshot(), fb, WATCH, runs=2)
    assert len(fb.calls) == 2 and all("repair" not in r for r in rec["runs"]) and rec["summary"]["repairs"] == 0
    fb = FakeBackend([_bad(), clean])
    rec = analyst.run_specialist(analyst.GENERALIST, comms_snapshot(), fb, WATCH, runs=1, repair=False)
    assert len(fb.calls) == 1 and "repair" not in rec["runs"][0] and rec["runs"][0]["verification"]["groundedness_pct"] == 75.0

