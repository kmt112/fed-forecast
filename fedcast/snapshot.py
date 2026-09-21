"""Frozen, content-hashed input bundles. Models and agents may read nothing else.

Layout:  snapshots/<as_of>_<hash12>/manifest.json + items/<item_id>.json
A snapshot is written once and never modified; `load` re-hashes everything and refuses
a bundle that has been touched.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


@dataclass(frozen=True)
class Item:
    id: str            # e.g. "futures.ZQV26", "fred.UNRATE", "fed.statement.2026-09-16"
    kind: str          # futures | effr | fred | calendar | document | human_view
    source: str        # where it came from, with any secret removed
    fetched_at: str    # UTC ISO timestamp
    content: Any
    sha256: str = ""

    @staticmethod
    def make(id: str, kind: str, source: str, content: Any) -> "Item":
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return Item(id, kind, source, now, content, _sha(content))


@dataclass
class Snapshot:
    as_of: date
    items: dict[str, Item] = field(default_factory=dict)
    missing: dict[str, str] = field(default_factory=dict)  # source id -> reason it is absent

    def add(self, item: Item) -> None:
        if item.id in self.items:
            raise ValueError(f"duplicate snapshot item {item.id}")
        self.items[item.id] = item

    def get(self, item_id: str) -> Any:
        return self.items[item_id].content

    @property
    def hash(self) -> str:
        return _sha({"as_of": self.as_of.isoformat(),
                     "items": {k: v.sha256 for k, v in sorted(self.items.items())},
                     "missing": self.missing})

    @property
    def complete(self) -> bool:
        return not self.missing

    def write(self, root: Path) -> Path:
        path = root / f"{self.as_of.isoformat()}_{self.hash[:12]}"
        if path.exists():
            raise FileExistsError(f"snapshot {path.name} already exists; snapshots are immutable")
        (path / "items").mkdir(parents=True)
        for item in self.items.values():
            (path / "items" / f"{item.id}.json").write_text(
                json.dumps(asdict(item), indent=1, ensure_ascii=False), encoding="utf-8")
        manifest = {"as_of": self.as_of.isoformat(), "hash": self.hash, "complete": self.complete,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "missing": self.missing,
                    "items": {k: {"kind": v.kind, "source": v.source, "sha256": v.sha256}
                              for k, v in sorted(self.items.items())}}
        (path / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        return path


def load(path: Path) -> Snapshot:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    snap = Snapshot(date.fromisoformat(manifest["as_of"]), missing=manifest["missing"])
    for item_id in manifest["items"]:
        raw = json.loads((path / "items" / f"{item_id}.json").read_text(encoding="utf-8"))
        item = Item(**raw)
        if _sha(item.content) != item.sha256 or item.sha256 != manifest["items"][item_id]["sha256"]:
            raise ValueError(f"snapshot item {item_id} has been modified")
        snap.items[item_id] = item
    if snap.hash != manifest["hash"]:
        raise ValueError("snapshot manifest hash mismatch")
    return snap


def latest(root: Path) -> Path:
    dirs = [p for p in root.iterdir() if (p / "manifest.json").exists()] if root.exists() else []
    if not dirs:
        raise FileNotFoundError("no snapshots yet; run `fedcast snapshot`")
    return max(dirs, key=lambda p: json.loads((p / "manifest.json").read_text(encoding="utf-8"))["created_at"])
