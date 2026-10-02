from datetime import date

import pytest

from fedcast import aggregate, forecast
from fedcast.models import taylor
from fedcast.signals import labour
from fedcast.snapshot import Item, Snapshot
from tests.test_inflation import monthly


def weekly(values):
    out, y, m, d = [], 2026, 9, 25
    for v in values:
        out.append({"date": f"{y}-{m:02d}-{d:02d}", "value": v})
        d -= 7
        if d < 1:
            d, m = d + 28, m - 1
    return out


def macro_snapshot(pi=3.0, u=4.1, u_lag=4.3, effr=3.88, payroll_step=70.0, claims=200_000.0):
    r = (1 + pi / 100) ** (1 / 12)
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("calendar", "calendar", "t", {"next_meeting": "2026-10-28",
                                                      "meetings": ["2026-09-16", "2026-10-28", "2026-12-09"]}))
    snap.add(Item.make("effr", "effr", "t", {"latest": {"date": "2026-10-01", "effr": effr, "target_low": 3.75,
                                                        "target_high": 4.0}}))
    snap.add(Item.make("futures.ZQX26", "futures", "t", {"symbol": "ZQX26.CBT", "contract_month": "2026-11", "price": 96.07}))
    snap.add(Item.make("fred.PCEPILFE", "fred", "t", {"observations": monthly(2026, 7, [100 * r ** (13 - i) for i in range(14)])}))
    snap.add(Item.make("fred.CPILFESL", "fred", "t", {"observations": monthly(2026, 8, [200 * r ** (13 - i) for i in range(14)])}))
    u_path = [u] * 12 + [u_lag] + [u_lag]
    snap.add(Item.make("fred.UNRATE", "fred", "t", {"observations": monthly(2026, 8, u_path)}))
    snap.add(Item.make("fred.PAYEMS", "fred", "t", {"observations": monthly(2026, 8, [159000 - payroll_step * i for i in range(14)])}))
    snap.add(Item.make("fred.ICSA", "fred", "t", {"observations": weekly([claims] * 30)}))
    return snap


def test_labour_signal_reads_gap_sahm_payrolls_claims():
    sig = labour.compute(macro_snapshot())
    assert sig["gap_pp"] == pytest.approx(4.1 - 4.2)
    assert sig["sahm"] == pytest.approx(0.0)
    assert sig["payrolls_3m_avg_k"] == pytest.approx(70.0)
    assert sig["claims_4wk_k"] == pytest.approx(200.0)
    assert labour.direction(sig) == "balanced, steady"


def test_prescriptions_match_hand_calculation():
    pres = taylor.prescriptions(pi=3.0, u=4.1, u_lag=4.3, rate_before=3.88)
    t93 = next(p for p in pres if p["variant"] == "taylor93" and p["r_star"] == 1.0 and p["u_star"] == 4.2)
    # 1.0 + 3.0 + 0.5*1.0 + 1.0*(4.2-4.1) = 4.6 ; inertial change = 0.15 * (4.6-3.88) = +10.8 bp
    assert t93["rule_rate"] == pytest.approx(4.6)
    assert t93["change_bp"] == pytest.approx(10.8)
    fd = next(p for p in pres if p["variant"] == "first_diff" and p["u_star"] == 4.2)
    # (0.5*1.0 + (4.2-4.1) - (4.2-4.3)) * 0.5 = (0.5 + 0.1 + 0.1) * 0.5 = 0.35 -> +35 bp
    assert fd["change_bp"] == pytest.approx(35.0)
    assert len(pres) == 3 * 3 * 3 + 3


def test_normal_bucketing_sums_to_one_and_centres_correctly():
    probs = taylor.bucket_from_normal(0.0, 15.0)
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs[0] > 0.5 and probs[-25] == pytest.approx(probs[25])
    hawkish = taylor.bucket_from_normal(30.0, 15.0)
    assert hawkish[25] > hawkish[0] and hawkish[50] > hawkish[-25]


def test_taylor_model_output_and_direction():
    out = taylor.taylor_rule(macro_snapshot())
    assert out["model"] == "taylor_rule" and sum(out["probabilities"].values()) == pytest.approx(1.0)
    assert out["expected_change_bp"] > 0  # inflation 1 pp above goal, labour balanced -> leans hike
    hot = taylor.taylor_rule(macro_snapshot(pi=5.0))
    assert hot["expected_change_bp"] > out["expected_change_bp"]
    slack = taylor.taylor_rule(macro_snapshot(u=5.0, u_lag=4.0))
    assert slack["expected_change_bp"] < out["expected_change_bp"]


def test_pool_applies_weights_and_surprise_floor():
    market = {-50: 0, -25: 0, 0: 0.5, 25: 0.5, 50: 0}
    tay = {-50: 0.02, -25: 0.1, 0: 0.4, 25: 0.4, 50: 0.08}
    pooled = aggregate.pool({"market_implied": market, "taylor_rule": tay}, {"market_implied": 0.8, "taylor_rule": 0.2}, 0.015)
    assert sum(pooled.values()) == pytest.approx(1.0)
    assert all(p >= 0.015 - 1e-9 for p in pooled.values())
    assert pooled[0] > pooled[-25] > pooled[-50]


def test_forecast_runs_both_models_and_records_skips_honestly():
    fc = forecast.compute(macro_snapshot(), [])
    assert set(fc["models"]) == {"market_implied", "taylor_rule"} and fc["models_skipped"] == {}
    assert min(fc["machine_only"].values()) >= 0.015 - 1e-9
    from tests.test_snapshot import make_snapshot
    fc2 = forecast.compute(make_snapshot(), [])
    assert set(fc2["models"]) == {"market_implied"} and "taylor_rule" in fc2["models_skipped"]
