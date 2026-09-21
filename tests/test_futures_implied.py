from datetime import date

import pytest

from fedcast.models.futures_implied import bucket_probabilities, implied_change_bp


def test_no_change_priced():
    # 30-day month, meeting on the 15th, month average equals the prevailing rate
    assert implied_change_bp(date(2026, 9, 15), 100 - 4.00, 4.00) == pytest.approx(0.0)


def test_full_cut_priced():
    # rate 4.00 for 15 days then 3.75 for 15 days -> month average 3.875
    assert implied_change_bp(date(2026, 9, 15), 100 - 3.875, 4.00) == pytest.approx(-25.0)


def test_partial_cut_splits_between_adjacent_buckets():
    probs = bucket_probabilities(-10.0)
    assert probs[-25] == pytest.approx(0.4)
    assert probs[0] == pytest.approx(0.6)
    assert sum(probs.values()) == pytest.approx(1.0)


def test_more_than_one_step():
    probs = bucket_probabilities(-30.0)
    assert probs[-50] == pytest.approx(0.2)
    assert probs[-25] == pytest.approx(0.8)


def test_beyond_grid_loads_end_bucket():
    assert bucket_probabilities(80.0)[50] == 1.0


def test_meeting_on_last_day_is_rejected():
    with pytest.raises(ValueError):
        implied_change_bp(date(2026, 9, 30), 96.0, 4.0)
