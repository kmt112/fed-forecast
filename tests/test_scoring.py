from datetime import date

import pytest

from fedcast import forecast, scoring
from fedcast.snapshot import Item, Snapshot
from tests.test_snapshot import make_snapshot

MEETING = date(2026, 10, 28)


def after_snapshot(target_high=4.25, row_date="2026-10-29", with_history=True):
    snap = Snapshot(date(2026, 10, 29))
    snap.add(Item.make("calendar", "calendar", "t", {"next_meeting": "2026-12-09", "meetings": ["2026-10-28", "2026-12-09"]}))
    snap.add(Item.make("effr", "effr", "t", {"latest": {"date": row_date, "effr": target_high - 0.12, "target_low": target_high - 0.25, "target_high": target_high}}))
    if with_history:
        snap.add(Item.make("history.target_rate", "history", "t", {"changes": [{"date": "2026-09-17", "target": 4.0}, {"date": "2026-10-29", "target": target_high}]}))
    return snap


def test_decision_is_read_only_once_the_rate_row_is_after_the_meeting():
    assert scoring.decision_from_snapshot(after_snapshot(row_date="2026-10-28"), MEETING) is None
    d = scoring.decision_from_snapshot(after_snapshot(), MEETING)
    assert d["target_high"] == 4.25 and d["history_agrees"] is True and d["evidence"] == ["effr", "history.target_rate"]


def test_realised_change_rounds_to_the_outcome_grid():
    assert scoring.realised_change_bp(4.0, 4.25) == 25
    assert scoring.realised_change_bp(4.0, 4.0) == 0
    assert scoring.realised_change_bp(4.0, 3.5) == -50
    assert scoring.realised_change_bp(4.0, 5.0) == 50   # clipped to the grid


def test_scores_are_proper_and_handle_zero_probability():
    probs = {"-50": 0.0, "-25": 0.0, "0": 0.9, "25": 0.1, "50": 0.0}
    hold = scoring.score_vector(probs, 0)
    assert hold["p_outcome"] == 0.9 and hold["log_score"] == pytest.approx(-0.1054, abs=1e-4) and hold["brier"] == pytest.approx(0.02)
    hike = scoring.score_vector(probs, 25)
    assert hike["log_score"] == pytest.approx(-2.3026, abs=1e-4) and hike["brier"] == pytest.approx(0.81 + 0.81)
    cut = scoring.score_vector(probs, -25)
    assert cut["log_score"] is None and cut["zero_probability"] is True and cut["brier"] == pytest.approx(0.81 + 0.01 + 1.0)


def test_score_entries_covers_tracks_models_and_names_the_final_entry():
    snap = make_snapshot()
    e1 = {"seq": 3, "spec_hash": "x", **forecast.run(snap, []), "created_at": "2026-10-20T00:00:00+00:00"}
    e2 = {"seq": 4, "spec_hash": "x", **forecast.run(snap, []), "created_at": "2026-10-26T00:00:00+00:00"}
    for e in (e1, e2):
        e["forecast"] = __import__("json").loads(__import__("json").dumps(e["forecast"]))
    rec = scoring.score_entries([e1, e2], MEETING, scoring.decision_from_snapshot(after_snapshot(), MEETING), target_high_before=4.0)
    assert rec["realised_bp"] == 25 and rec["final_entry"] == 4 and len(rec["entries"]) == 2
    s = rec["entries"][-1]
    assert set(s["tracks"]) >= {"machine_only", "human_adjusted"} and "market_implied" in s["models"]
    assert s["models"]["market_implied"]["p_outcome"] == pytest.approx(0.2)   # make_snapshot prices +5 bp: 80/20
    base = scoring.naive_baselines(25)
    assert base["always_no_change"]["zero_probability"] and base["uniform"]["log_score"] == pytest.approx(-1.6094, abs=1e-4)


def test_score_meeting_appends_once_and_refuses_before_the_decision(tmp_path, monkeypatch):
    from fedcast import ledger
    monkeypatch.setattr(scoring, "recorded_before_decision", lambda e, m: True)  # the entry is created now, after the real decision
    snap = make_snapshot()
    snap.items["effr"] = Item.make("effr", "effr", "test", {"latest": {"date": "2026-10-22", "effr": 3.88, "target_low": 3.75, "target_high": 4.0}})
    led, sc = tmp_path / "forecasts.jsonl", tmp_path / "scores.jsonl"
    ledger.append(led, forecast.run(snap, []))
    find = lambda h: snap  # noqa: E731
    with pytest.raises(ValueError, match="does not yet show a decision"):
        scoring.score_meeting(None, led, sc, after_snapshot(row_date="2026-10-28"), find)
    rec = scoring.score_meeting(None, led, sc, after_snapshot(), find)
    assert rec["meeting"] == "2026-10-28" and rec["realised_bp"] == 25 and rec["seq"] == 0 and ledger.verify(sc) == 1
    assert rec["decision"]["target_high_before"] == 4.0 and rec["baselines"]["uniform"]["p_outcome"] == 0.2
    with pytest.raises(ValueError, match="already scored"):
        scoring.score_meeting(None, led, sc, after_snapshot(), find)


def test_entries_recorded_after_the_announcement_are_labelled_not_scored():
    snap = make_snapshot()
    early = {"seq": 5, "spec_hash": "x", **forecast.run(snap, []), "created_at": "2026-10-28T12:00:00+00:00"}   # 8 am Eastern
    late = {"seq": 6, "spec_hash": "x", **forecast.run(snap, []), "created_at": "2026-10-29T04:49:15+00:00"}    # the evening after
    assert scoring.recorded_before_decision(early, MEETING) and not scoring.recorded_before_decision(late, MEETING)
    rec = scoring.score_entries([early, late], MEETING, scoring.decision_from_snapshot(after_snapshot(), MEETING), target_high_before=4.0)
    assert rec["final_entry"] == 5
    assert rec["entries"][1]["after_decision"] is True and rec["entries"][1]["tracks"] == {} and "not scored" in rec["entries"][1]["note"]
    assert rec["entries"][0]["after_decision"] is False and "pooled" in rec["entries"][0]["tracks"]


def test_decision_cutoff_moves_to_the_next_meeting_from_two_pm_eastern():
    from datetime import datetime
    from fedcast import config
    from fedcast.data import fomc_calendar as fc

    morning = datetime(2026, 10, 28, 13, 59, tzinfo=config.DATA_TZ)
    afternoon = datetime(2026, 10, 28, 14, 0, tzinfo=config.DATA_TZ)
    assert fc.decision_cutoff(morning) == date(2026, 10, 28)
    assert fc.decision_cutoff(afternoon) == date(2026, 10, 29)

