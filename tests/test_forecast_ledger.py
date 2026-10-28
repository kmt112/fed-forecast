import json
from datetime import date, datetime

import pytest

from fedcast import aggregate, forecast, ledger
from fedcast.human.views import View
from tests.test_snapshot import make_snapshot


def hawkish(strength=2):
    return View(id="H2-001", author="t", created_at=datetime(2026, 9, 21, 9, 0), expires_on=date(2026, 10, 28),
                direction="hawkish", strength=strength, rationale="Statement language shifted toward inflation risk")


def test_compute_is_deterministic():
    snap = make_snapshot()
    assert forecast.compute(snap, [hawkish()]) == forecast.compute(snap, [hawkish()])


def specialist_record(name, tilt):
    return {"analyst": name, "analyst_no": 4, "created_at": "2026-10-25T00:00:00+00:00", "prompt_version": "t",
            "summary": {"runs": 5, "tilt_mean_bp": tilt, "tilt_std_bp": 0.4, "groundedness_pct_mean": 100.0, "leakage_total": 0, "watchouts_missing_total": 0}}


def test_specialists_tilt_moves_the_machine_track_by_a_bounded_amount():
    snap = make_snapshot()
    none = forecast.compute(snap, [], analyses={})
    assert none["analysts"]["applied_pp"] == 0 and none["machine_only"] == none["pooled"] and "no specialist" in none["analysts"]["note"]
    an = {"communications": specialist_record("communications", 6.0), "labour": specialist_record("labour", -2.0), "naive": {"summary": {}}}
    fc = forecast.compute(snap, [], analyses=an)
    assert fc["analysts"]["tilts_bp"] == {"communications": 6.0, "labour": -2.0} and fc["analysts"]["mean_bp"] == 2.0
    assert fc["analysts"]["applied_pp"] == 2.0
    tv = 0.5 * sum(abs(fc["machine_only"][o] - fc["pooled"][o]) for o in fc["pooled"])
    assert tv == pytest.approx(0.02, abs=1e-6)
    big = {"communications": specialist_record("communications", 40.0)}
    assert forecast.compute(snap, [], analyses=big)["analysts"]["applied_pp"] == 10.0   # capped like a view


def test_tracks_are_identical_without_views():
    fc = forecast.compute(make_snapshot(), [])
    assert fc["machine_only"] == fc["human_adjusted"]


def test_delta_between_tracks_equals_view_budget():
    fc = forecast.compute(make_snapshot(), [hawkish(2)])
    tv = 0.5 * sum(abs(fc["machine_only"][o] - fc["human_adjusted"][o]) for o in fc["machine_only"])
    assert tv == pytest.approx(0.06, abs=1e-6)
    assert fc["human"]["net_budget"] == pytest.approx(0.06)


def test_pool_renormalises_over_present_models():
    a = {-50: 0, -25: 0, 0: 1.0, 25: 0, 50: 0}
    b = {-50: 0, -25: 0, 0: 0.0, 25: 1.0, 50: 0}
    pooled = aggregate.pool({"a": a, "b": b}, {"a": 3.0, "b": 1.0, "absent": 5.0}, floor=0.0)
    assert pooled[0] == pytest.approx(0.75) and pooled[25] == pytest.approx(0.25)


def test_ledger_chain_detects_edits(tmp_path):
    path = tmp_path / "l.jsonl"
    ledger.append(path, {"x": 1})
    ledger.append(path, {"x": 2})
    assert ledger.verify(path) == 2
    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0]); first["x"] = 99
    path.write_text("\n".join([json.dumps(first, sort_keys=True), lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ledger.verify(path)


def test_ledger_chain_detects_deletion(tmp_path):
    path = tmp_path / "l.jsonl"
    for i in range(3):
        ledger.append(path, {"x": i})
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ledger.verify(path)


def test_ledger_verifies_records_with_non_string_keys(tmp_path):
    path = tmp_path / "l.jsonl"
    ledger.append(path, {"probs": {-25: 0.4, 0: 0.6}})
    assert ledger.verify(path) == 1


def test_replay_uses_the_analyst_records_the_entry_names(tmp_path, monkeypatch):
    import json
    from fedcast import evals
    from fedcast.llm import analyst
    from fedcast.scorecard import spec_hash

    monkeypatch.setattr(analyst, "ANALYSES_DIR", tmp_path)
    snap = make_snapshot()
    first = dict(specialist_record("communications", 6.0), snapshot_hash=snap.hash, created_at="2026-10-25T00:00:00+00:00")
    analyst.save(first)
    entry = forecast.run(snap, [])  # reads the latest record: tilt +6 bp
    assert entry["forecast"]["analysts"]["tilts_bp"] == {"communications": 6.0}
    # a newer, different record lands on the same snapshot after the entry was published
    analyst.save(dict(specialist_record("communications", -8.0), snapshot_hash=snap.hash, created_at="2026-10-26T00:00:00+00:00"))
    assert analyst.latest(snap.hash, "communications")["summary"]["tilt_mean_bp"] == -8.0
    det = evals.replay([{"seq": 0, **json.loads(json.dumps(entry))}], lambda h: snap, spec_hash())
    assert det[0]["ok"] is True
    # an entry that names a record which no longer exists fails, and says which
    gone = json.loads(json.dumps(entry)); gone["forecast"]["analysts"]["records"]["communications"]["created_at"] = "2020-01-01T00:00:00+00:00"
    det = evals.replay([{"seq": 1, **gone}], lambda h: snap, spec_hash())
    assert det[0]["ok"] is False and "communications" in det[0]["note"]

