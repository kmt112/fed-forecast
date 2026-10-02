import json
from datetime import date, datetime

from fedcast import forecast, journey
from fedcast.human.views import View
from fedcast.snapshot import Item
from tests.test_snapshot import make_snapshot


def entry_for(snap, views):
    rec = {"seq": 0, "prev_hash": "0" * 16, "entry_hash": "x" * 16, "created_at": "2026-09-21T00:00:00+00:00",
           "spec_hash": "s", "code_version": "c", "forecast": forecast.compute(snap, views)}
    return json.loads(json.dumps(rec))  # as it comes back from the ledger


def full_snapshot():
    snap = make_snapshot()
    snap.items["effr"] = Item.make("effr", "effr", "test", {"latest": {
        "date": "2026-09-17", "effr": 3.88, "target_low": 3.75, "target_high": 4.0}})
    snap.items["futures.ZQX26"] = Item.make("futures.ZQX26", "futures", "test", {
        "symbol": "ZQX26.CBT", "contract_month": "2026-11", "price": 96.07})
    snap.add(Item.make("fred.UNRATE", "fred", "test", {"observations": []}))
    return snap


def test_journey_shows_the_actual_arithmetic():
    steps = journey.build(entry_for(full_snapshot(), []), full_snapshot())
    text = json.dumps(steps, ensure_ascii=False)
    assert "100 − 96.07 = 3.930%" in text
    assert "+5.0 bp" in text
    assert [s["n"] for s in steps] == list(range(1, len(steps) + 1))


def test_journey_lists_unused_evidence_honestly():
    steps = journey.build(entry_for(full_snapshot(), []), full_snapshot())
    unused = [r[0] for r in steps[-1]["rows"]]
    assert "fred.UNRATE" in unused and "effr" not in unused


def test_journey_names_applied_views():
    v = View(id="H2-001", author="t", created_at=datetime(2026, 9, 21, 9, 0), expires_on=date(2026, 10, 28),
             direction="hawkish", strength=2, rationale="Statement language shifted toward inflation risk")
    steps = journey.build(entry_for(full_snapshot(), [v]), full_snapshot())
    views_step = next(s for s in steps if s["title"] == "Apply your views")
    assert views_step["rows"][0][0] == "H2-001" and "+6 pp" in views_step["body"]


def test_ui_actions_write_typed_inputs(tmp_path, monkeypatch):
    import pytest
    from fedcast.human.store import load_views
    from fedcast.ui import server

    monkeypatch.setattr(server, "VIEWS", tmp_path / "views.yaml")
    monkeypatch.setattr(server, "WATCHLIST", tmp_path / "watchlist.yaml")

    server.act_add_view({"direction": "hawkish", "strength": "2", "expires_on": "2099-01-01",
                         "rationale": "Statement language shifted toward inflation risk"})
    server.act_add_view({"direction": "dovish", "strength": 1, "expires_on": "2099-01-01",
                         "rationale": "Claims are drifting up and hiring has slowed a lot"})
    views = load_views(server.VIEWS)
    assert [v.id for v in views] == ["H2-001", "H2-002"]
    assert all(v.is_active(date.today()) for v in views)

    server.act_expire_view({"id": "H2-001"})
    views = load_views(server.VIEWS)
    assert not views[0].is_active(date.today()) and views[1].is_active(date.today())

    with pytest.raises(Exception):  # free-form or out-of-range input is rejected by the View schema
        server.act_add_view({"direction": "very hawkish", "strength": 9, "expires_on": "2099-01-01",
                             "rationale": "x" * 30})

    server.act_add_directive({"directive": "Watch for dissents and their direction"})
    assert server._load_watchlist()[0]["id"] == "H1-001"


def test_dag_only_marks_live_what_is_in_the_number():
    from fedcast import dag

    g = dag.build(entry_for(full_snapshot(), []), full_snapshot(), [{"id": "H1-001", "directive": "x", "status": "active"}])
    by_id = {n["id"]: n for n in g["nodes"]}
    assert all(e["from"] in by_id and e["to"] in by_id for e in g["edges"])
    assert all(by_id[e["from"]]["col"] < by_id[e["to"]]["col"] for e in g["edges"]), "edges must only flow forward"
    assert by_id["fred.Labour data"]["status"] == "idle" and by_id["model.taylor"]["status"] == "planned"
    for e in g["edges"]:  # nothing non-live may feed a live node through a live edge
        if by_id[e["to"]]["status"] == "live" and e["status"] == "live":
            assert by_id[e["from"]]["status"] == "live"
    assert "100 − 96.07 = 3.930%" in json.dumps(g, ensure_ascii=False)
    # a computed signal may feed the planned models but must not feed anything live
    for e in g["edges"]:
        if by_id[e["from"]]["status"] == "computed":
            assert by_id[e["to"]]["status"] != "live"
    assert by_id["out"]["summary"] == "hold 80%"
