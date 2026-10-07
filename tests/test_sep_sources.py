from datetime import date

import pytest

from fedcast.data import fomc_calendar, sources
from fedcast.signals import sep
from fedcast.snapshot import Item, Snapshot

TABLE = """<table><tr><th>Variable</th><th>Median1</th><th>Central Tendency2</th><th>Range3</th></tr>
<tr><th>2026</th><th>2027</th><th>2028</th><th>2029</th><th>Longer run</th><th>2026</th><th>2027</th><th>2028</th><th>2029</th><th>Longer run</th></tr>
<tr><td>Unemployment rate</td><td>4.1</td><td>4.1</td><td>4.1</td><td>4.1</td><td>4.2</td><td>4.1&#8211;4.2</td><td>4.0&#8211;4.2</td></tr>
<tr><td>June projection</td><td>4.3</td><td>4.3</td><td>4.2</td><td>4.2</td><td>4.3&#8211;4.4</td></tr>
<tr><td>Core PCE inflation4</td><td>3.4</td><td>2.5</td><td>2.2</td><td>2.0</td><td>3.3&#8211;3.4</td></tr>
<tr><td>June projection</td><td>3.3</td><td>2.5</td><td>2.1</td><td>3.2&#8211;3.5</td></tr>
<tr><td>Memo: Projected appropriate policy path</td></tr>
<tr><td>Federal funds rate</td><td>4.1</td><td>4.1</td><td>3.9</td><td>3.6</td><td>3.2</td><td>4.1&#8211;4.4</td></tr>
<tr><td>June projection</td><td>3.8</td><td>3.6</td><td>3.4</td><td>3.1</td><td>3.6&#8211;4.1</td></tr></table>"""


def test_sep_table_parsing():
    d = sources.parse_sep("<html>" + TABLE + "</html>")
    assert d["years"] == ["2026", "2027", "2028", "2029", "Longer run"]
    assert d["medians"]["Federal funds rate"] == {"2026": 4.1, "2027": 4.1, "2028": 3.9, "2029": 3.6, "Longer run": 3.2}
    assert d["previous"]["Federal funds rate"]["2026"] == 3.8
    assert d["medians"]["Core PCE inflation"] == {"2026": 3.4, "2027": 2.5, "2028": 2.2, "2029": 2.0}
    assert d["previous"]["Unemployment rate"]["2026"] == 4.3


def test_projections_signal_implies_one_more_hike():
    snap = Snapshot(date(2026, 10, 7))
    snap.add(Item.make("calendar", "calendar", "t", {"next_meeting": "2026-10-28",
                                                      "meetings": ["2026-09-16", "2026-10-28", "2026-12-09", "2027-01-27"]}))
    snap.add(Item.make("effr", "effr", "t", {"latest": {"effr": 3.88, "target_low": 3.75, "target_high": 4.0}}))
    snap.add(Item.make("fed.sep.2026-09-16", "projections", "t", {"url": "u", **sources.parse_sep(TABLE)}))
    g = sep.compute(snap)
    assert g["current_midpoint"] == 3.875 and g["implied_change_bp"] == pytest.approx(22.5)
    assert g["implied_moves"] == pytest.approx(0.9) and g["remaining_meetings"] == ["2026-10-28", "2026-12-09"]
    assert g["per_meeting_bp"] == pytest.approx(11.2, abs=0.1) and g["revision_pp"] == pytest.approx(0.3)
    assert sep.direction(g) == "median implies about 0.9 more hike(s) by end-2026, revised up from the previous SEP"


def test_calendar_parses_presconf_and_sep_links():
    html = ('>2026 FOMC Meetings<<div class="fomc-meeting__month"><strong>September</strong></div>'
            '<div class="fomc-meeting__date">15-16*</div> <a href="/newsevents/pressreleases/monetary20260916a.htm">HTML</a>'
            '<a href="/monetarypolicy/fomcpresconf20260916.htm">Press Conference</a>'
            '<a href="/monetarypolicy/fomcprojtabl20260916.htm">HTML</a>'
            '<div class="fomc-meeting__month"><strong>January</strong></div><div class="fomc-meeting__date">27-28</div>'
            '<a href="/monetarypolicy/fomcpressconf20260128.htm">Press Conference</a>')
    ms = {m.decision_date: m for m in fomc_calendar.parse(html)}
    assert ms[date(2026, 9, 16)].presconf_pdf_url.endswith("/mediacenter/files/FOMCpresconf20260916.pdf")
    assert ms[date(2026, 9, 16)].sep_url.endswith("/monetarypolicy/fomcprojtabl20260916.htm")
    assert ms[date(2026, 1, 28)].presconf_pdf_url.endswith("FOMCpresconf20260128.pdf") and ms[date(2026, 1, 28)].sep_url is None


def test_rss_field_parsing():
    item = "<title><![CDATA[Jefferson, The U.S. Economy and Monetary Policy]]></title><pubDate><![CDATA[Thu, 1 Oct 2026 17:30:00 GMT]]></pubDate>"
    assert sources._rss_field(item, "title") == "Jefferson, The U.S. Economy and Monetary Policy"
    assert sources._rss_field(item, "pubDate").startswith("Thu, 1 Oct 2026")
