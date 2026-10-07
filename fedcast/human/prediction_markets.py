"""H6 prediction-market odds (Polymarket, Kalshi), entered by hand.

Why by hand: these venues block or rate-limit scripts, their contracts are worded differently from
meeting to meeting, and the odds are thin and fee-distorted, so a human should look at the page and
record what it showed, when, and where. The entry is frozen into the *next* snapshot as a
`prediction_market` item and read by the prediction_market model; it is evidence, not a view.

Prices are recorded exactly as the site shows them (percent per outcome). They rarely sum to 100
because of spreads and fees, so the raw prices are stored and the model normalises them.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from fedcast import OUTCOMES_BP

OUTCOME_KEYS = [str(o) for o in OUTCOMES_BP]


class MarketOdds(BaseModel):
    id: str = Field(pattern=r"^H6-\d{3,}$")
    venue: Literal["polymarket", "kalshi", "other"]
    meeting: date
    observed_at: datetime
    author: str
    url: str = ""
    prices: dict[str, float]  # outcome in bp as a string -> price in percent, as shown on the site
    volume_usd: float | None = None
    note: str = ""
    status: Literal["active", "withdrawn"] = "active"

    @field_validator("prices")
    @classmethod
    def _check_prices(cls, prices: dict[str, float]) -> dict[str, float]:
        bad = [k for k in prices if k not in OUTCOME_KEYS]
        if bad:
            raise ValueError(f"unknown outcomes {bad}; use {OUTCOME_KEYS}")
        if len(prices) < 2:
            raise ValueError("record at least two outcomes")
        if any(not 0 <= v <= 100 for v in prices.values()):
            raise ValueError("prices are percentages between 0 and 100")
        total = sum(prices.values())
        if not 80 <= total <= 120:
            raise ValueError(f"prices sum to {total:.0f}%; a real market sums to roughly 100")
        return prices

    def normalised(self) -> dict[int, float]:
        total = sum(self.prices.values())
        return {o: self.prices.get(str(o), 0.0) / total for o in OUTCOMES_BP}


def load_markets(path: Path) -> list[MarketOdds]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = [MarketOdds(**m) for m in raw.get("markets") or []]
    ids = [m.id for m in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate market ids in " + path.name)
    return items


def next_id(items: list[MarketOdds]) -> str:
    nums = [int(m.id.split("-")[1]) for m in items]
    return f"H6-{max(nums, default=0) + 1:03d}"


_HEADER = """# H6 prediction-market odds, entered by hand from Polymarket or Kalshi. Prices in percent as shown on the
# site; they need not sum to 100. Each entry is frozen into the next snapshot and read by the prediction_market
# model, which uses the most recent active entry for the next meeting.
"""


def save_markets(path: Path, items: list[MarketOdds]) -> None:
    data = {"markets": [m.model_dump(mode="json") for m in items]}
    path.write_text(_HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
