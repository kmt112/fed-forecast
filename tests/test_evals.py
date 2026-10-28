from fedcast import evals


def rec(**summary):
    return {"summary": summary}


def test_measure_scores_both_arms_against_thresholds():
    analyses = {
        "naive": rec(runs=5, max_std_pp=1.9, leakage_total=36, groundedness_pct_mean=0.0, mean_probabilities={}),
        "communications": rec(runs=5, tilt_mean_bp=4.2, tilt_std_bp=0.75, groundedness_pct_mean=100.0, leakage_total=0, watchouts_missing_total=0),
        "inflation": rec(runs=5, tilt_mean_bp=7.0, tilt_std_bp=1.2, groundedness_pct_mean=96.0, leakage_total=0, watchouts_missing_total=0),
        "labour": None,
    }
    rows = {(r["id"], r["scope"]): r for r in evals.measure(analyses)}
    assert rows[("S1", "1 naive")]["pass"] is True and rows[("S3", "1 naive")]["pass"] is False
    assert rows[("S2", "1 naive")]["pass"] is False
    assert rows[("S1", "4-8 specialists")]["value"] == 1.2 and rows[("S1", "4-8 specialists")]["pass"] is True
    assert rows[("S2", "4-8 specialists")]["value"] == 96.0 and rows[("S2", "4-8 specialists")]["pass"] is True
    assert rows[("S3", "4-8 specialists")]["value"] == 0 and rows[("S3", "4-8 specialists")]["pass"] is True
    assert rows[("S10", "4-8 specialists")]["pass"] is True


def test_single_run_specialists_have_no_s1_value():
    analyses = {"communications": rec(runs=1, tilt_mean_bp=4.0, tilt_std_bp=None, groundedness_pct_mean=91.0, leakage_total=0, watchouts_missing_total=0)}
    rows = {(r["id"], r["scope"]): r for r in evals.measure(analyses)}
    assert rows[("S1", "4-8 specialists")]["value"] is None and rows[("S1", "4-8 specialists")]["pass"] is None
    assert rows[("S2", "4-8 specialists")]["pass"] is False  # 91% < 95%


# --- the deterministic chain -------------------------------------------------------------------------------------

from datetime import datetime

from fedcast import forecast
from fedcast.human import prediction_markets as pm
from fedcast.scorecard import spec_hash
from fedcast.snapshot import Item
from tests.test_taylor_labour import macro_snapshot


def full_snapshot():
    snap = macro_snapshot()
    odds = pm.MarketOdds(id="H6-001", venue="polymarket", meeting="2026-10-28", observed_at=datetime(2026, 10, 1, 9, 0),
                         author="t", prices={"0": 60.0, "25": 40.0})
    snap.add(Item.make("human.pm.H6-001", "prediction_market", "t", odds.model_dump(mode="json")))
    snap.add(Item.make("fed.statement.2026-09-16", "document", "t", {"url": "u", "text": "Inflation remains elevated. The Committee raised."}))
    return snap


def test_shocks_move_the_pool_the_right_way_and_noise_does_not():
    snap = full_snapshot()
    shocks = evals.shock_tests(snap)
    assert len(shocks) == 7 and all(d["ok"] for d in shocks)
    assert shocks[0]["delta_bp"] > 0 > shocks[1]["delta_bp"]
    assert "10.00 pp" in shocks[5]["note"] and "3.00 pp" in shocks[6]["note"]
    noise = evals.noise_tests(snap)
    assert len(noise) == 5 and all(d["ok"] for d in noise) and max(d["shift_pp"] for d in noise) == 0.0
    assert evals.paraphrase_test(snap)[0]["shift_pp"] == 0.0


def test_odds_shock_perturbs_the_entry_the_model_uses():
    snap = full_snapshot()   # H6-001 observed 2026-10-01 09:00
    later = pm.MarketOdds(id="H6-002", venue="kalshi", meeting="2026-10-28", observed_at=datetime(2026, 10, 2, 9, 0),
                          author="t", prices={"0": 90.0, "25": 10.0})
    snap.add(Item.make("human.pm.H6-002", "prediction_market", "t", later.model_dump(mode="json")))
    shocks = evals.shock_tests(snap)
    assert shocks[4]["ok"] is True and shocks[4]["delta_bp"] > 0


def test_shocks_report_absent_inputs_as_not_applicable():
    from tests.test_snapshot import make_snapshot

    shocks = evals.shock_tests(make_snapshot())   # calendar, effr, futures only
    assert [d["ok"] for d in shocks[:5]] == [True, True, None, None, None]


def test_coherence_and_replay_over_a_ledger():
    snap = full_snapshot()
    good = forecast.run(snap, [])
    rows = {r["id"]: r for r in evals.deterministic(snap, [{"seq": 0, "entry_hash": "x", **good}], lambda h: snap, spec_hash())}
    assert rows["S4"]["value"] == 100.0 and rows["S5"]["value"] == 0.0 and rows["S6"]["value"] == 0.0
    assert rows["S7"]["value"] == 100.0 and rows["S9"]["value"] == 100.0
    # an entry whose published numbers no longer recompute fails S9; one under an earlier spec is labelled, not scored
    bad = json.loads(json.dumps(good)); bad["forecast"]["machine_only"]["0"] += 0.01; bad["forecast"]["machine_only"]["25"] -= 0.01
    old = json.loads(json.dumps(good)); old["spec_hash"] = "0000000000000000"
    det = evals.replay([{"seq": 0, **good}, {"seq": 1, **bad}, {"seq": 2, **old}], lambda h: snap, spec_hash())
    assert [d["ok"] for d in det] == [True, False, None]
    co = evals.coherence([{"seq": 1, **bad}])
    assert co[0]["ok"] is False and co[0]["sums_to_one"] is True and co[0]["adjusted_is_tilted_machine"] is False


import json  # noqa: E402
