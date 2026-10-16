"""ALFRED real-time panels: every vintage of a series in one request, and 'as known on' lookups.

FRED keeps the history of revisions. A single request with realtime_start=1776-07-04 and
realtime_end=9999-12-31 returns one row per (observation, vintage window), so the value a reader would
have seen on any past date can be reconstructed locally. This is what makes a backtest honest: the
probit sees what the committee saw, not today's revised numbers.
"""

from __future__ import annotations

from datetime import date

from fedcast.data import http

ALFRED_MIN = "1776-07-04"
ALFRED_MAX = "9999-12-31"


def fetch_realtime(series_id: str, api_key: str, observation_start: str = "1990-01-01") -> list[dict]:
    data = http.get_json("https://api.stlouisfed.org/fred/series/observations", {
        "series_id": series_id, "api_key": api_key, "file_type": "json",
        "realtime_start": ALFRED_MIN, "realtime_end": ALFRED_MAX,
        "observation_start": observation_start, "limit": "100000",
    }, user_agent=http.PLAIN_UA)
    rows = []
    for o in data["observations"]:
        if o["value"] == ".":
            continue
        rows.append({"date": o["date"], "value": float(o["value"]),
                     "realtime_start": o["realtime_start"], "realtime_end": o["realtime_end"]})
    return rows


def first_vintage(rows: list[dict]) -> str:
    return min(r["realtime_start"] for r in rows)


def as_known(rows: list[dict], on: date, n: int | None = None) -> list[tuple[str, float]]:
    """Observations as published on `on`, newest first. Each observation keeps the vintage whose window
    contains `on`; observations not yet published on that date are absent."""
    d = on.isoformat()
    best: dict[str, float] = {}
    for r in rows:
        if r["realtime_start"] <= d < r["realtime_end"]:
            best[r["date"]] = r["value"]
    out = sorted(best.items(), reverse=True)
    return out[:n] if n else out
