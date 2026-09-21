"""Market-implied decision probabilities from 30-day fed funds futures (FedWatch-style).

A fed funds futures contract settles at 100 minus the month's average effective rate.
For a month containing an FOMC meeting, that average blends the pre-meeting rate and
the post-meeting rate by day count, so the post-meeting rate can be backed out.
"""

from __future__ import annotations

import calendar
import math
from datetime import date

from fedcast import OUTCOMES_BP


def implied_change_bp(meeting_date: date, meeting_month_price: float, rate_before: float) -> float:
    """Expected policy-rate change in bp implied by the meeting-month contract.

    meeting_date: decision day; the new rate applies from the following day.
    meeting_month_price: futures price for the meeting month (e.g. 95.905).
    rate_before: effective rate (percent) prevailing before the meeting, typically
        100 minus the price of the nearest prior no-meeting month, or the current EFFR.
    """
    days_in_month = calendar.monthrange(meeting_date.year, meeting_date.month)[1]
    days_before = meeting_date.day
    days_after = days_in_month - days_before
    if days_after == 0:
        raise ValueError("meeting on the last day of the month: use the next month's contract")
    month_avg = 100.0 - meeting_month_price
    rate_after = (month_avg * days_in_month - rate_before * days_before) / days_after
    return (rate_after - rate_before) * 100.0


def bucket_probabilities(change_bp: float) -> dict[int, float]:
    """Split an expected change across the two adjacent 25bp outcomes.

    -10bp -> 40% cut 25 / 60% hold.  Changes beyond the outcome grid load the end bucket.
    """
    lo_out, hi_out = OUTCOMES_BP[0], OUTCOMES_BP[-1]
    clipped = max(lo_out, min(hi_out, change_bp))
    steps = clipped / 25.0
    lower = math.floor(steps)
    frac = steps - lower
    probs = {o: 0.0 for o in OUTCOMES_BP}
    probs[int(lower * 25)] += 1.0 - frac
    if frac > 0:
        probs[int((lower + 1) * 25)] += frac
    return probs
