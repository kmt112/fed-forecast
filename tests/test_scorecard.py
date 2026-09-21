from fedcast.scorecard import SCORECARD, spec_hash

# Pinned pre-registration. If this fails you changed the yardstick: add an entry to
# governance/AMENDMENTS.md and update the pin in the same commit.
PINNED_SPEC_HASH = "74213ad4ceacab43"


def test_scorecard_is_unchanged_since_last_amendment():
    assert spec_hash() == PINNED_SPEC_HASH


def test_ten_dimensions_with_unique_ids():
    ids = [d.id for d in SCORECARD]
    assert ids == [f"S{i}" for i in range(1, 11)]


def test_pass_direction():
    s1 = SCORECARD[0]
    assert s1.passes(1.5) and not s1.passes(2.5)
    s2 = SCORECARD[1]
    assert s2.passes(97.0) and not s2.passes(90.0)
