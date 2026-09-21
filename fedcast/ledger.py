"""Append-only forecast ledger (JSONL). Entries are chained by hash so edits and deletions show."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GENESIS = "0" * 16


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "entry_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify(path: Path) -> int:
    """Check the hash chain; returns the number of entries."""
    prev = GENESIS
    entries = read(path)
    for i, e in enumerate(entries):
        if e["prev_hash"] != prev or e["entry_hash"] != _digest(e):
            raise ValueError(f"ledger entry {i} fails the hash chain: the ledger has been altered")
        prev = e["entry_hash"]
    return len(entries)


def append(path: Path, record: dict) -> dict:
    verify(path)
    entries = read(path)
    record = json.loads(json.dumps(record))  # hash what will be read back (JSON turns int keys into strings)
    entry = {"seq": len(entries), "prev_hash": entries[-1]["entry_hash"] if entries else GENESIS, **record}
    entry["entry_hash"] = _digest(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry
