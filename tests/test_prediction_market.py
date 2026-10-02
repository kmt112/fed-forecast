from datetime import date, datetime

import pytest

from fedcast import forecast
from fedcast.human import prediction_markets as pm
from fedcast.models.prediction_market import prediction_market
from fedcast.snapshot import Item
from tests.test_taylor_labour import macro_snapshot


def odds(id_="H6-001", prices=None, observed=datetime(2026, 10, 2, 9, 0), meeting=date(2026, 10, 28)):
    return pm.MarketOdds(id=id_, venue="polymarket", meeting=meeting, observed_at=observed, author="t",
                         url="https://polymarket.com/event/fed-decision-october-2026",
                         prices=prices or {"0": 68.0, "25": 31.0, "-25": 2.0}, volume_usd=1_200_000)


def test_prices_are_validated_and_normalised():
    o = odds()
    n = o.normalised()
    assert sum(n.values()) == pytest.approx(1.0) and n[0] == pytest.approx(68 / 101)
    with pytest.raises(ValueError):
        odds(prices={"0": 30.0, "25": 10.0})          # sums to 40: not a real market
    with pytest.raises(ValueError):
        odds(prices={"hold": 60.0, "25": 40.0})       # unknown outcome key


def test_roundtrip_yaml(tmp_path):
    p = tmp_path / "m.yaml"
    pm.save_markets(p, [odds()])
    loaded = pm.load_markets(p)
    assert loaded == [odds()] and pm.next_id(loaded) == "H6-002"


def test_model_uses_latest_entry_for_the_next_meeting_only():
    snap = macro_snapshot()
    snap.add(Item.make("human.pm.H6-001", "prediction_market", "t", odds().model_dump(mode="json")))
    snap.add(Item.make("human.pm.H6-002", "prediction_market", "t",
                       odds("H6-002", {"0": 55.0, "25": 45.0}, datetime(2026, 10, 2, 15, 0)).model_dump(mode="json")))
    snap.add(Item.make("human.pm.H6-003", "prediction_market", "t",
                       odds("H6-003", {"0": 10.0, "25": 90.0}, datetime(2026, 10, 3), date(2026, 12, 9)).model_dump(mode="json")))
    out = prediction_market(snap)
    assert out["evidence"] == ["calendar", "human.pm.H6-002"]
    assert out["probabilities"][0] == pytest.approx(0.55)
    fc = forecast.compute(snap, [])
    assert "prediction_market" in fc["models"]


def test_model_is_skipped_without_an_entry():
    fc = forecast.compute(macro_snapshot(), [])
    assert "prediction_market" in fc["models_skipped"] and "prediction_market" not in fc["models"]
