"""Committee projections (the SEP 'dot plot' medians): what the committee itself expects to do.

Spec (pre-registered 2026-10-07):
  The quarterly Summary of Economic Projections gives the median participant's expected federal funds rate
  at year-end. Against the current target-range midpoint, the median implies a number of 25 bp moves by
  year-end; divided over the scheduled meetings still to come, that is the committee's own average lean
  per meeting. The revision from the previous SEP shows which way the committee moved.
"""

from __future__ import annotations

from datetime import date

from fedcast.snapshot import Snapshot


def compute(snap: Snapshot) -> dict:
    sep_ids = sorted(i for i in snap.items if i.startswith("fed.sep."))
    if not sep_ids:
        raise ValueError("no projections in the snapshot")
    sep = snap.get(sep_ids[-1])
    effr = snap.get("effr")["latest"]
    midpoint = (effr["target_low"] + effr["target_high"]) / 2
    ffr = sep["medians"].get("Federal funds rate", {})
    prev = sep["previous"].get("Federal funds rate", {})
    years = [y for y in ffr if y.isdigit()]
    if not years:
        raise ValueError("no federal funds rate medians in the projections")
    year = years[0]  # the current year's end
    median = ffr[year]
    implied_bp = round((median - midpoint) * 100, 1)
    meetings = snap.get("calendar")["meetings"]
    remaining = [m for m in meetings if m > snap.as_of.isoformat() and m[:4] == year]
    return {
        "signal": "committee_projections",
        "sep_item": sep_ids[-1],
        "year": year,
        "median_end_year": median,
        "previous_median": prev.get(year),
        "revision_pp": round(median - prev[year], 2) if prev.get(year) is not None else None,
        "current_midpoint": midpoint,
        "implied_change_bp": implied_bp,
        "implied_moves": round(implied_bp / 25, 2),
        "remaining_meetings": remaining,
        "per_meeting_bp": round(implied_bp / len(remaining), 1) if remaining else None,
        "path": ffr,
        "other_medians": {k: v for k, v in sep["medians"].items() if k != "Federal funds rate"},
        "evidence": [sep_ids[-1], "effr", "calendar"],
    }


def direction(sig: dict) -> str:
    moves = sig["implied_moves"]
    what = (f"about {abs(moves):.1f} more hike(s)" if moves > 0.25 else
            f"about {abs(moves):.1f} cut(s)" if moves < -0.25 else "no further move")
    rev = sig["revision_pp"]
    how = ("" if rev is None else f", revised {'up' if rev > 0 else 'down' if rev < 0 else 'unchanged'} from the previous SEP")
    return f"median implies {what} by end-{sig['year']}{how}"
