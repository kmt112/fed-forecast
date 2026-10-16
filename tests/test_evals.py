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
    rows = {(r["id"], r["arm"]): r for r in evals.measure(analyses)}
    assert rows[("S1", "A naive")]["pass"] is True and rows[("S3", "A naive")]["pass"] is False
    assert rows[("S2", "A naive")]["pass"] is False
    assert rows[("S1", "D specialists")]["value"] == 1.2 and rows[("S1", "D specialists")]["pass"] is True
    assert rows[("S2", "D specialists")]["value"] == 96.0 and rows[("S2", "D specialists")]["pass"] is True
    assert rows[("S3", "D specialists")]["value"] == 0 and rows[("S3", "D specialists")]["pass"] is True
    assert rows[("S10", "D specialists")]["pass"] is True


def test_single_run_specialists_have_no_s1_value():
    analyses = {"communications": rec(runs=1, tilt_mean_bp=4.0, tilt_std_bp=None, groundedness_pct_mean=91.0, leakage_total=0, watchouts_missing_total=0)}
    rows = {(r["id"], r["arm"]): r for r in evals.measure(analyses)}
    assert rows[("S1", "D specialists")]["value"] is None and rows[("S1", "D specialists")]["pass"] is None
    assert rows[("S2", "D specialists")]["pass"] is False  # 91% < 95%
