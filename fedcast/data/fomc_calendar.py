"""FOMC meeting dates and document links, parsed from the Fed's calendar page."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from fedcast.data import http

URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
BASE = "https://www.federalreserve.gov"

_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}
_MONTHS |= {m[:3]: i for m, i in list(_MONTHS.items())}

_YEAR = re.compile(r">(\d{4}) FOMC Meetings<")
_ROW = re.compile(
    r'fomc-meeting__month[^>]*><strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<(.*?)(?=fomc-meeting__month|\Z)',
    re.S)
_STATEMENT = re.compile(r'href="(/newsevents/pressreleases/monetary\d{8}a\.htm)"')
_MINUTES = re.compile(r'href="(/monetarypolicy/fomcminutes\d{8}\.htm)"')
_PRESCONF = re.compile(r'href="/monetarypolicy/fomcpres+conf(\d{8})\.htm"')  # the Fed's own URLs vary in spelling
_SEP = re.compile(r'href="(/monetarypolicy/fomcprojtabl\d{8}\.htm)"')


@dataclass(frozen=True)
class Meeting:
    decision_date: date
    statement_url: str | None
    minutes_url: str | None
    presconf_pdf_url: str | None = None  # transcript, published a day or two after the press conference
    sep_url: str | None = None           # Summary of Economic Projections table, quarterly meetings only


def parse(html: str) -> list[Meeting]:
    meetings: list[Meeting] = []
    year_marks = [(m.start(), int(m.group(1))) for m in _YEAR.finditer(html)]
    for idx, (start, year) in enumerate(year_marks):
        end = year_marks[idx + 1][0] if idx + 1 < len(year_marks) else len(html)
        for month_txt, day_txt, body in _ROW.findall(html[start:end]):
            if "notation" in day_txt.lower() or "unscheduled" in day_txt.lower():
                continue
            days = re.findall(r"\d+", day_txt)
            if not days:
                continue
            # "Apr/May" + "30-1": the decision falls on the last day, in the last month named
            month = _MONTHS.get(month_txt.strip().split("/")[-1].strip())
            if month is None:
                continue
            s, m = _STATEMENT.search(body), _MINUTES.search(body)
            pc, sep = _PRESCONF.search(body), _SEP.search(body)
            meetings.append(Meeting(date(year, month, int(days[-1])),
                                    BASE + s.group(1) if s else None,
                                    BASE + m.group(1) if m else None,
                                    f"{BASE}/mediacenter/files/FOMCpresconf{pc.group(1)}.pdf" if pc else None,
                                    BASE + sep.group(1) if sep else None))
    return sorted(meetings, key=lambda x: x.decision_date)


def fetch() -> list[Meeting]:
    return parse(http.get_text(URL))


def next_meeting(meetings: list[Meeting], as_of: date) -> Meeting:
    upcoming = [m for m in meetings if m.decision_date >= as_of]
    if not upcoming:
        raise LookupError("no scheduled FOMC meeting on or after " + as_of.isoformat())
    return upcoming[0]


def has_meeting_in_month(meetings: list[Meeting], year: int, month: int) -> bool:
    return any(m.decision_date.year == year and m.decision_date.month == month for m in meetings)
