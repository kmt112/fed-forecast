import math
import random
from datetime import date

import pytest

from fedcast.data import alfred
from fedcast.models import probit


def test_as_known_picks_the_vintage_in_force():
    rows = [
        {"date": "2026-07-01", "value": 100.0, "realtime_start": "2026-08-28", "realtime_end": "2026-09-26"},
        {"date": "2026-07-01", "value": 100.5, "realtime_start": "2026-09-26", "realtime_end": "9999-12-31"},
        {"date": "2026-08-01", "value": 101.0, "realtime_start": "2026-09-26", "realtime_end": "9999-12-31"},
    ]
    assert alfred.as_known(rows, date(2026, 9, 1)) == [("2026-07-01", 100.0)]       # first print only
    assert alfred.as_known(rows, date(2026, 10, 1)) == [("2026-08-01", 101.0), ("2026-07-01", 100.5)]
    assert alfred.as_known(rows, date(2026, 8, 1)) == []                              # nothing published yet


def test_features_from_series():
    r = 1.03 ** (1 / 12)
    pce = [(f"m{i}", 100 * r ** (13 - i)) for i in range(14)]
    un = [(f"m{i}", 4.0 + (0.3 if i == 12 else 0)) for i in range(14)]
    pay = [(f"m{i}", 159000 - 60 * i) for i in range(5)]
    x = probit.features_from_series(pce, un, pay, dgs2_latest=4.8, target=4.0, prev=1)
    assert x["infl_gap"] == pytest.approx(1.0, abs=1e-3) and x["infl_mom"] == pytest.approx(0.0, abs=1e-3)
    assert x["u_chg12"] == pytest.approx(-0.3) and x["pay3"] == pytest.approx(60.0)
    assert x["y2_gap"] == pytest.approx(0.8) and x["prev"] == 1.0
    assert probit.features_from_series(pce[:5], un, pay, 4.8, 4.0, 0) is None


def synthetic_rows(n=400, seed=1):
    """Decisions generated from a known ordered-probit so the fit can be checked against the truth."""
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        x = {"infl_gap": rnd.gauss(0, 1), "infl_mom": rnd.gauss(0, 0.5), "u_level": rnd.gauss(5, 1),
             "u_chg12": rnd.gauss(0, 0.5), "pay3": rnd.gauss(100, 100), "y2_gap": rnd.gauss(0, 1), "prev": float(rnd.choice([-1, 0, 1]))}
        z = 1.2 * x["y2_gap"] + 0.6 * x["infl_gap"] - 0.8 * x["u_chg12"] + 0.5 * x["prev"] + rnd.gauss(0, 1)
        y = 0 if z < -1.0 else 1 if z < 1.0 else 2
        rows.append({"date": f"{2001 + i // 8:04d}-{(i % 8) + 1:02d}-15", "y": y,
                     "change_bp": {0: -25.0, 1: 0.0, 2: 25.0}[y], **x})
    return rows


def test_fit_recovers_signs_and_beats_base_rates():
    rows = synthetic_rows()
    m = probit.fit(rows)
    assert m["converged"]
    assert m["beta"]["y2_gap"] > 0 and m["beta"]["infl_gap"] > 0 and m["beta"]["u_chg12"] < 0 and m["beta"]["prev"] > 0
    assert m["cuts"][0] < m["cuts"][1]
    p = probit.predict_probs(m, rows[0])
    assert sum(p) == pytest.approx(1.0) and all(0 <= v <= 1 for v in p)
    ev = probit.evaluate(rows)
    assert ev["probit"]["log_score"] > ev["base_given_previous"]["log_score"] > ev["base_unconditional"]["log_score"] - 0.2
    assert ev["train_n"] + ev["test_n"] == len(rows)


def test_class_probs_sum_to_one():
    p = probit.class_probs(0.3, (-1.0, 1.0))
    assert sum(p) == pytest.approx(1.0) and p[1] > p[0] and p[1] > p[2]


def test_dataset_excludes_future_meetings():
    from tests.test_base_rates import synthetic_history

    meetings, path = synthetic_history()
    meetings += [{"date": "2026-10-28", "scheduled": True}, {"date": "2027-01-27", "scheduled": True}]
    r = 1.03 ** (1 / 12)
    months = [f"{y}-{m:02d}-01" for y in range(1993, 2003) for m in range(1, 13)]
    pce = [{"date": d, "value": 100 * r ** i, "realtime_start": "1990-01-01", "realtime_end": "9999-12-31"} for i, d in enumerate(months)]
    un = [{"date": d, "value": 5.0, "realtime_start": "1990-01-01", "realtime_end": "9999-12-31"} for d in months]
    pay = [{"date": d, "value": 100000 + 50 * i, "realtime_start": "1990-01-01", "realtime_end": "9999-12-31"} for i, d in enumerate(months)]
    dgs2 = [{"date": d, "value": 4.0} for d in months]
    rows = probit.build_dataset({"PCEPILFE": pce, "UNRATE": un, "PAYEMS": pay, "DGS2": dgs2}, meetings, path, date(2026, 10, 15))
    assert rows and max(r["date"] for r in rows) < "2026-10-12"
