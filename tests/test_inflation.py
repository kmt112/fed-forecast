from datetime import date

import pytest

from fedcast.signals import inflation
from fedcast.snapshot import Item, Snapshot


def monthly(start_year, start_month, values):
    """Observations newest-first, as FRED returns them."""
    out = []
    y, m = start_year, start_month
    for v in values:
        out.append({"date": f"{y}-{m:02d}-01", "value": v})
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out


def snapshot_with(pce_values, cpi_values, cpi_newer=True):
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("fred.PCEPILFE", "fred", "t", {"observations": monthly(2026, 7, pce_values)}))
    snap.add(Item.make("fred.CPILFESL", "fred", "t", {"observations": monthly(2026, 8 if cpi_newer else 7, cpi_values)}))
    return snap


def test_gap_and_momentum_from_a_constant_3_percent_path():
    r = (1.03) ** (1 / 12)
    pce = [100 * r ** (13 - i) for i in range(14)]          # 3% a year, every month
    cpi = [200 * r ** (13 - i) for i in range(14)]
    sig = inflation.compute(snapshot_with(pce, cpi))
    assert sig["anchor_12m"] == pytest.approx(3.0, abs=1e-3)
    assert sig["gap_pp"] == pytest.approx(1.0, abs=1e-3)
    assert sig["momentum"]["3m"] == pytest.approx(3.0, abs=1e-3)
    assert sig["nowcast"]["anchor_12m"] == pytest.approx(3.0, abs=1e-3)
    assert sig["nowcast"]["month"] == "2026-08-01"
    assert inflation.direction(sig) == "above goal, steady"


def test_momentum_detects_easing():
    r_old, r_new = 1.04 ** (1 / 12), 1.02 ** (1 / 12)
    path = [100.0]
    for i in range(13):                                     # 4% a year, then 2% for the last 3 months
        path.append(path[-1] * (r_new if i >= 10 else r_old))
    sig = inflation.compute(snapshot_with(list(reversed(path)), list(reversed(path))))
    assert sig["momentum"]["3m"] == pytest.approx(2.0, abs=1e-3)
    assert sig["anchor_12m"] > sig["momentum"]["3m"]
    assert inflation.direction(sig).endswith("easing")


def test_no_nowcast_when_cpi_is_not_fresher():
    r = (1.03) ** (1 / 12)
    pce = [100 * r ** (13 - i) for i in range(14)]
    assert inflation.compute(snapshot_with(pce, pce, cpi_newer=False))["nowcast"] is None


def test_too_little_history_is_an_error():
    with pytest.raises(ValueError):
        inflation.compute(snapshot_with([100.0] * 6, [100.0] * 6))
