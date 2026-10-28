"""Amendment #7: the Taylor-rule family reads r* from the New York Fed DSGE model's natural rate."""

from fedcast.data import sources
from fedcast.models import taylor
from fedcast.snapshot import Item
from tests.test_taylor_labour import macro_snapshot

UPDATED = "Latest Release 9:00 a.m. EST September 18, 2026"
NATURAL = (
    "dates,90.0%_lb,90.0%_ub,80.0%_lb,80.0%_ub,70.0%_lb,70.0%_ub,68.0%_lb,68.0%_ub,60.0%_lb,60.0%_ub,50.0%_lb,50.0%_ub,mean_history,mean_forecast\n"
    "2026-06-30,-0.9,0.8,-0.7,0.6,-0.5,0.5,-0.4965,0.4774,-0.4,0.4,-0.3,0.3,-0.0082,-0.0082\n"
    "2026-09-30,-0.4,3.3,0.0,2.8,0.3,2.5,0.3068,2.4358,0.5,2.3,0.7,2.1,,1.3793\n"
    "2026-12-31,-0.1,3.9,0.3,3.4,0.6,3.1,0.6542,3.0554,0.8,2.9,1.0,2.6,,1.8610\n"
    "2027-03-31,,,,,,,,,,,,,,\n"
)
TABLE = (
    ",2026,2027,2028,2029\n"
    "GDP growth (Q4/Q4),1.2,0.1,0.5,1.2\n"
    "Real natural rate of interest (Q4),1.9,1.8,1.4,1.2\n"
)


def dsge_item():
    return Item.make("nyfed.dsge", "model_estimate", sources.DSGE_PAGE, sources.parse_dsge(UPDATED, NATURAL, TABLE))


def test_parse_dsge_reads_release_path_and_table():
    d = sources.parse_dsge(UPDATED, NATURAL, TABLE)
    assert d["release"] == "2026-09-18"
    assert [p["quarter_end"] for p in d["natural_rate"]] == ["2026-06-30", "2026-09-30", "2026-12-31"]
    assert d["natural_rate"][0]["kind"] == "estimate" and d["natural_rate"][1]["kind"] == "forecast"
    assert d["natural_rate"][2]["mean"] == 1.861 and d["natural_rate"][2]["band68"] == [0.654, 3.055]
    assert d["table"]["years"] == ["2026", "2027", "2028", "2029"]
    assert d["table"]["rows"]["Real natural rate of interest (Q4)"] == [1.9, 1.8, 1.4, 1.2]


def test_r_star_comes_from_the_meeting_quarter_when_the_item_is_present():
    snap = macro_snapshot()  # next meeting 2026-10-28, in the quarter ending 2026-12-31
    assert taylor.r_star_grid(snap)["source"] == "fixed grid"
    assert taylor.r_star_grid(snap)["grid"] == taylor.R_STAR_GRID
    snap.add(dsge_item())
    rs = taylor.r_star_grid(snap)
    assert rs["source"] == "nyfed.dsge" and rs["quarter_end"] == "2026-12-31" and rs["kind"] == "forecast"
    assert rs["grid"] == (0.65, 1.86, 3.06)


def test_a_higher_natural_rate_tilts_the_rules_toward_a_hike_and_is_recorded():
    base = taylor.taylor_rule(macro_snapshot())
    snap = macro_snapshot()
    snap.add(dsge_item())
    out = taylor.taylor_rule(snap)
    assert out["r_star"]["source"] == "nyfed.dsge" and "nyfed.dsge" in out["evidence"]
    # mean r* 1.86 vs 1.0 on the fixed grid: level rules prescribe (1 - rho) x 0.86 pp ~ 13 bp more
    assert out["expected_change_bp"] > base["expected_change_bp"] + 5
    assert out["probabilities"][25] > base["probabilities"][25]
    assert out["spread_bp"] > base["spread_bp"]  # the 68% band is wider than the old grid, and that is shown
