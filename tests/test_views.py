from datetime import date, datetime

import pytest

from fedcast.human.views import View, apply_tilt, net_budget
from fedcast.scorecard import TILT_CAP

MACHINE = [0.0, 0.30, 0.65, 0.05, 0.0]


def tv(a, b):
    return 0.5 * sum(abs(x - y) for x, y in zip(a, b))


def view(id_, direction, strength, rationale="Chair's last three speeches stressed upside inflation risk"):
    return View(id=id_, author="t", created_at=datetime(2026, 9, 21, 9, 0),
                expires_on=date(2026, 10, 28), direction=direction, strength=strength,
                rationale=rationale)


def test_tilt_moves_exactly_the_budget_and_sums_to_one():
    out = apply_tilt(MACHINE, 0.10)
    assert sum(out) == pytest.approx(1.0)
    assert tv(MACHINE, out) == pytest.approx(0.10, abs=1e-6)


def test_hawkish_tilt_has_hawkish_sign():
    out = apply_tilt(MACHINE, 0.10)
    assert out[1] < MACHINE[1] and out[3] > MACHINE[3]


def test_dovish_tilt_mirrors():
    out = apply_tilt(MACHINE, -0.06)
    assert out[1] > MACHINE[1] and out[3] < MACHINE[3]


def test_tilt_never_creates_mass_in_zero_buckets():
    out = apply_tilt(MACHINE, 0.10)
    assert out[0] == 0.0 and out[4] == 0.0


def test_budget_above_cap_is_rejected():
    with pytest.raises(ValueError):
        apply_tilt(MACHINE, TILT_CAP + 0.01)


def test_stacked_views_are_clipped_to_cap():
    views = [view("H2-001", "hawkish", 3), view("H2-002", "hawkish", 3)]
    assert net_budget(views, date(2026, 10, 1)) == TILT_CAP


def test_opposing_views_net_out():
    views = [view("H2-001", "hawkish", 2), view("H2-002", "dovish", 2)]
    assert net_budget(views, date(2026, 10, 1)) == 0.0


def test_expired_view_moves_nothing():
    assert net_budget([view("H2-001", "hawkish", 3)], date(2026, 11, 1)) == 0.0


def test_rewording_rationale_cannot_change_the_tilt():
    a = view("H2-001", "hawkish", 2)
    b = view("H2-001", "hawkish", 2, rationale="Completely different wording of the same opinion here")
    d = date(2026, 10, 1)
    assert apply_tilt(MACHINE, net_budget([a], d)) == apply_tilt(MACHINE, net_budget([b], d))
