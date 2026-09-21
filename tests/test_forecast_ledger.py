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
    pooled = aggregate.pool({"a": a, "b": b}, {"a": 3.0, "b": 1.0, "absent": 5.0})
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
