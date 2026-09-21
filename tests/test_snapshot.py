import json
from datetime import date

import pytest

from fedcast import snapshot
from fedcast.models.baseline import market_implied
from fedcast.snapshot import Item, Snapshot


def make_snapshot() -> Snapshot:
    snap = Snapshot(date(2026, 9, 21))
    snap.add(Item.make("calendar", "calendar", "test",
                       {"next_meeting": "2026-10-28", "meetings": ["2026-09-16", "2026-10-28", "2026-12-09"]}))
    snap.add(Item.make("effr", "effr", "test", {"latest": {"effr": 3.88}}))
    snap.add(Item.make("futures.ZQX26", "futures", "test", {"price": 96.07}))  # implies 3.93
    return snap


def test_roundtrip_preserves_hash(tmp_path):
    snap = make_snapshot()
    path = snap.write(tmp_path)
    assert snapshot.load(path).hash == snap.hash


def test_same_content_gives_same_hash_regardless_of_fetch_time():
    assert make_snapshot().hash == make_snapshot().hash


def test_snapshots_are_immutable(tmp_path):
    snap = make_snapshot()
    snap.write(tmp_path)
    with pytest.raises(FileExistsError):
        snap.write(tmp_path)


def test_tampering_is_detected(tmp_path):
    path = make_snapshot().write(tmp_path)
    f = path / "items" / "effr.json"
    raw = json.loads(f.read_text(encoding="utf-8"))
    raw["content"]["latest"]["effr"] = 3.63
    f.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        snapshot.load(path)


def test_missing_sources_make_snapshot_incomplete():
    snap = make_snapshot()
    snap.missing["fred.UNRATE"] = "no key"
    assert not snap.complete


def test_baseline_uses_next_month_contract_when_it_has_no_meeting():
    result = market_implied(make_snapshot())
    assert result["method"] == "next_month_contract"
    assert result["expected_change_bp"] == pytest.approx(5.0)
    assert result["probabilities"][25] == pytest.approx(0.2)
    assert result["probabilities"][0] == pytest.approx(0.8)
    assert result["evidence"] == ["calendar", "effr", "futures.ZQX26"]
