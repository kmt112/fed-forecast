"""H5 documents: your own write-ups, notes and analyses, entered as evidence rather than views.

A document is frozen into the *next* snapshot as a `human_document` item tagged human-sourced.
Only the LLM analysts may read it, and they must quote it like any other item. The quant
models never see it and it never tilts the number directly; if you want the number to move,
enter a view (H2). Added after a snapshot was taken, it waits for the next one: nothing
enters a forecast after its cutoff.

Stored as human/documents/H5-NNN.md: a YAML front-matter block followed by the text.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str = Field(pattern=r"^H5-\d{3,}$")
    title: str = Field(min_length=3)
    author: str
    added_on: date
    source: str = ""  # own analysis, a colleague's note, a URL, a broker report
    relevance: Literal["related", "unrelated", "unsure"] = "unsure"
    status: Literal["active", "withdrawn"] = "active"
    text: str = Field(min_length=20)


_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", re.S)


def parse(raw: str) -> Document:
    m = _FRONT_MATTER.match(raw)
    if not m:
        raise ValueError("document needs a front-matter block between --- lines")
    meta = yaml.safe_load(m.group(1)) or {}
    return Document(**meta, text=m.group(2).strip())


def render(doc: Document) -> str:
    meta = doc.model_dump(mode="json")
    text = meta.pop("text")
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n" + text + "\n"


def load_documents(folder: Path) -> list[Document]:
    if not folder.exists():
        return []
    docs = [parse(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("H5-*.md"))]
    ids = [d.id for d in docs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate document ids in " + str(folder))
    return docs


def next_id(docs: list[Document]) -> str:
    nums = [int(d.id.split("-")[1]) for d in docs]
    return f"H5-{max(nums, default=0) + 1:03d}"


def save(folder: Path, doc: Document, overwrite: bool = False) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{doc.id}.md"
    if path.exists() and not overwrite:
        raise FileExistsError(f"{doc.id} already exists")
    path.write_text(render(doc), encoding="utf-8")
    return path
