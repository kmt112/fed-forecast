"""Local configuration. Secrets come from .env or the process environment, never from code."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "snapshots"

# Evidence is dated in the data's own timezone. FRED's real-time vintages and the Fed's releases follow the US
# day; a snapshot taken from Asia in the morning would otherwise be dated "tomorrow" and FRED rejects it.
DATA_TZ = ZoneInfo("America/New_York")


def today() -> date:
    return datetime.now(DATA_TZ).date()

# FRED series captured in every snapshot (id -> why it is there).
FRED_SERIES: dict[str, str] = {
    "PCEPILFE": "Core PCE price index (the Fed's preferred inflation gauge)",
    "CPILFESL": "Core CPI",
    "UNRATE": "Unemployment rate",
    "PAYEMS": "Nonfarm payrolls",
    "ICSA": "Initial jobless claims",
    "T5YIE": "5-year breakeven inflation",
    "NFCI": "Chicago Fed financial conditions index",
    "DGS2": "2-year Treasury yield",
}


def _read_dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def secret(name: str) -> str | None:
    return os.environ.get(name) or _read_dotenv().get(name) or None
