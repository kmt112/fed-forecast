from datetime import date

import pytest

from fedcast.data import fomc_history
from fedcast.signals import base_rates
from fedcast.snapshot import Item, Snapshot

PAGE = """<h5 class="panel-heading">January 29-30 Meeting - 2019</h5>
<h5 class="panel-heading">March 15 Meeting - 2020 (unscheduled)</h5>
<h5 class="panel-heading">April/May 30-1 Meeting - 1996</h5>
<h5 class="panel-heading">October 8 Meeting - 2008 (conference call)</h5>"""


def test_history_page_parsing():
    ms = fomc_history.parse_history_page(PAGE)
    assert [(m.decision_date, m.scheduled) for m in ms] == [
        (date(2019, 1, 30), True), (date(2020, 3, 15), False), (date(1996, 5, 1), True), (date(2008, 10, 8), False)]


def synthetic_history():
    """Twelve years of 8 meetings: a hiking cycle, holds, a cutting cycle, one intermeeting cut, one 50 bp hike."""
    meetings, path, target = [], [{"date": "1994-01-01", "target": 3.0}], 3.0
    pattern = (["hike"] * 10 + ["hold"] * 30 + ["cut"] * 8 + ["hold"] * 40 + ["hike"] * 8)
    y, m = 1994, 2
    for i, dec in enumerate(pattern):
        d = date(y, m, 15)
        meetings.append({"date": d.isoformat(), "scheduled": True})
        step = 0.5 if (dec == "hike" and i == 3) else 0.25
        if dec == "hike":
            target += step
        elif dec == "cut":
            target -= step
        if dec != "hold":
            path.append({"date": date(y, m, 16).isoformat(), "target": round(target, 2)})
        m += 1
        if m > 12:
            y, m = y + 1, 1
        if m == 7 and y == 1999:  # an intermeeting cut on a non-meeting day
            target -= 0.25
            path.append({"date": date(y, m, 3).isoformat(), "target": round(target, 2)})
    return meetings, path


def test_decisions_and_intermeeting_moves():
    meetings, path = synthetic_history()
    decided, inter = base_rates.decisions(meetings, path)
    assert len(decided) == 96
    assert [d["decision"] for d in decided[:3]] == ["hike", "hike", "hike"]
    assert decided[3]["change_bp"] == 50.0
    assert len(inter) == 1 and inter[0]["change_bp"] == -25.0


def test_base_rate_tables():
    meetings, path = synthetic_history()
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("history.meetings", "history", "t", {"meetings": meetings}))
    snap.add(Item.make("history.target_rate", "history", "t", {"changes": path}))
    sig = base_rates.compute(snap)
    assert sig["scheduled_decisions"] == 96
    assert sig["overall"]["hold"] == pytest.approx(70 / 96, abs=1e-3)
    assert sig["last_decision"]["decision"] == "hike"
    assert sig["conditional"]["hike"]["hike"] > sig["conditional"]["hike"]["cut"]
    assert sig["moves_50bp_or_more"] == 1 and sig["reversals"] == 0 and sig["intermeeting_moves"] == 1
    assert base_rates.direction(sig).startswith("after a hike, next was hike")


def test_future_meetings_are_not_counted_as_holds():
    meetings, path = synthetic_history()
    meetings += [{"date": "2026-10-28", "scheduled": True}, {"date": "2027-01-27", "scheduled": True}]
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("history.meetings", "history", "t", {"meetings": meetings}))
    snap.add(Item.make("history.target_rate", "history", "t", {"changes": path}))
    sig = base_rates.compute(snap)
    assert sig["scheduled_decisions"] == 96 and sig["through"] < "2026-10-02"
