"""Load typed human inputs from the human/ folder."""

from __future__ import annotations

from pathlib import Path

import yaml

from fedcast.human.views import View


def load_views(path: Path) -> list[View]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    views = [View(**v) for v in raw.get("views") or []]
    ids = [v.id for v in views]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate view ids in " + path.name)
    return views
