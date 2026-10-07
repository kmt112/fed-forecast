"""Historical FOMC meeting dates, from the Fed's per-year history pages (1994 onward) plus the current
calendar page. Used for base rates: a decision can only be scored as a 'hold' on a day the committee met.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from fedcast.data import fomc_calendar, http

FIRST_YEAR = 1994  # the Fed began announcing decisions after each meeting in February 1994
HISTORY_URL = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"

_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}
# e.g. "January 29-30 Meeting - 2019", "March 15 Meeting - 2020 (unscheduled)", "April/May 30-1 Meeting - 1996"
_HEADING = re.compile(r"<h5[^>]*>\s*([A-Za-z]+(?:/[A-Za-z]+)?)\s+(\d{1,2})(?:-(\d{1,2}))?\s+Meeting\s*-\s*(\d{4})"
                      r"\s*(\([^)]*\))?", re.I)


@dataclass(frozen=True)
class HistoricalMeeting:
    decision_date: date
    scheduled: bool


def parse_history_page(html: str) -> list[HistoricalMeeting]:
    out = []
    for month_txt, d1, d2, year, note in _HEADING.findall(html):
        month = _MONTHS.get(month_txt.split("/")[-1])
        if month is None:
            continue
        day = int(d2) if d2 else int(d1)
        scheduled = not (note and ("unscheduled" in note.lower() or "conference" in note.lower()))
        out.append(HistoricalMeeting(date(int(year), month, day), scheduled))
    return out


def fetch(first_year: int = FIRST_YEAR, last_year: int | None = None) -> list[HistoricalMeeting]:
    """All meetings from `first_year` through the current calendar page, oldest first."""
    current = fomc_calendar.fetch()
    current_years = {m.decision_date.year for m in current}
    last_year = last_year or min(current_years) - 1
    meetings: list[HistoricalMeeting] = []
    for year in range(first_year, last_year + 1):
        meetings += parse_history_page(http.get_text(HISTORY_URL.format(year=year)))
    meetings += [HistoricalMeeting(m.decision_date, True) for m in current]
    seen, unique = set(), []
    for m in sorted(meetings, key=lambda x: x.decision_date):
        if m.decision_date not in seen:
            seen.add(m.decision_date)
            unique.append(m)
    return unique
