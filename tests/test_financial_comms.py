from datetime import date

import pytest

from fedcast.signals import comms, financial
from fedcast.snapshot import Item, Snapshot


def daily(values, start=(2026, 9, 24)):
    out, (y, m, d) = [], start
    for v in values:
        out.append({"date": f"{y}-{m:02d}-{d:02d}", "value": v})
        d -= 1
        if d == 0:
            d, m = 28, m - 1
    return out


def fin_snapshot():
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("effr", "effr", "t", {"latest": {"effr": 3.88}}))
    snap.add(Item.make("fred.DGS2", "fred", "t", {"observations": daily([4.87] * 10 + [4.60] * 15)}))
    snap.add(Item.make("fred.T5YIE", "fred", "t", {"observations": daily([2.34] * 10 + [2.20] * 15)}))
    snap.add(Item.make("fred.NFCI", "fred", "t", {"observations": daily([-0.55, -0.55, -0.55, -0.55, -0.40, -0.40])}))
    return snap


def test_financial_conditions_reads_gap_and_changes():
    sig = financial.compute(fin_snapshot())
    assert sig["two_year"]["gap_bp"] == pytest.approx(99.0)
    assert sig["two_year"]["change_4wk_bp"] == pytest.approx(27.0)
    assert sig["breakeven"]["vs_goal_pp"] == pytest.approx(0.34)
    assert sig["nfci"]["change_4wk"] == pytest.approx(-0.15)
    assert financial.direction(sig) == "hikes priced, expectations anchored, conditions loose"


PREV = """July 29, 2026
Federal Reserve issues FOMC statement
For release at 2:00 p.m. EDT
The Federal Open Market Committee approved the following statement for release by a 11 – 1 vote:
The Committee decided to maintain the target range for the federal funds rate at 3-1/2 to 3-3/4 percent.
Inflation remains somewhat elevated. Job gains have moderated.
Voting against this action was Jane Doe, who preferred to raise the target range.
For media inquiries, please email media@frb.gov."""

LATEST = """September 16, 2026
Federal Reserve issues FOMC statement
For release at 2:00 p.m. EDT
The Federal Open Market Committee approved the following statement for release by a 12 – 0 vote:
The Committee decided to raise the target range for the federal funds rate by 1/4 percentage point to 3-3/4 to 4 percent.
Inflation remains elevated. Job gains have kept pace with the workforce.
For media inquiries, please email media@frb.gov."""


def test_vote_and_dissenters():
    assert comms.vote(PREV) == {"for": 11, "against": 1, "dissenters": "Jane Doe, who preferred to raise the target range"}
    assert comms.vote(LATEST)["against"] == 0


def test_diff_reports_added_and_removed_phrases():
    d = comms.diff(PREV, LATEST)
    assert any("raise" in x for x in d["added"]) and any("maintain" in x for x in d["removed"])
    assert not any("the target range for the federal funds rate" in x for x in d["added"])  # unchanged text is not reported
    assert any("somewhat" in x for x in d["removed"])
    assert 0 < d["similarity"] < 1


def test_lexicon_and_signal_from_snapshot():
    snap = Snapshot(date(2026, 10, 2))
    snap.add(Item.make("fed.statement.2026-07-29", "document", "t", {"url": "u", "text": PREV}))
    snap.add(Item.make("fed.statement.2026-09-16", "document", "t", {"url": "u", "text": LATEST}))
    sig = comms.compute(snap)
    assert sig["previous"] == "fed.statement.2026-07-29" and sig["latest"] == "fed.statement.2026-09-16"
    assert sig["lexicon"]["score"] > 0  # "raise", "elevated" outweigh "moderated"
    assert comms.direction(sig).endswith("unanimous")
    assert comms.lexicon(PREV)["dovish"].get("moderated") == 1


def test_lexicon_matches_whole_words_only():
    assert comms.lexicon("for release by a vote")["dovish"] == {}
    assert comms.lexicon("The Committee decided to ease policy.")["dovish"] == {"ease": 1}
