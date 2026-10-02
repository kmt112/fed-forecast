"""Communication tone, deterministic baseline: the statement's vote, what changed since the previous
statement, and a lexicon score. The LLM communications analyst (later) reads the same diff and must quote it;
this module is the floor it has to beat and the check it is held against.

Spec (pre-registered 2026-10-02):
  vote      parsed from "by a N – M vote"; dissenters from a "Voting against" sentence when present
  diff      word-level difference between the latest statement and the previous one, reported as the phrases
            added and removed (boilerplate such as the release line and media contact is stripped first)
  lexicon   counts of hawkish and dovish terms in the statement body; score = (hawk − dove) / (hawk + dove),
            so +1 is uniformly hawkish, −1 uniformly dovish, 0 balanced. Crude by design: it is a baseline.
"""

from __future__ import annotations

import difflib
import re

from fedcast.snapshot import Snapshot

HAWKISH = ("elevated", "raise", "raised", "firming", "tighten", "tightening", "restrictive", "upside risk",
           "upside risks", "strong", "solid", "robust", "persistent", "resilient", "higher for longer",
           "vigilant", "price stability", "timelier")
DOVISH = ("lower", "lowered", "cut", "ease", "easing", "accommodative", "downside risk", "downside risks",
          "slowed", "slowing", "softened", "softening", "weak", "weakened", "moderated", "moderating",
          "progress", "balanced", "cooling", "subdued", "eased")

_BOILER = re.compile(r"^(for release at.*|share|federal reserve issues fomc statement|for media inquiries.*|"
                     r"implementation note.*|last update.*|[a-z]+ \d{1,2}, \d{4})$", re.I)
_VOTE = re.compile(r"by a (\d+)\s*[–-]\s*(\d+) vote")
_AGAINST = re.compile(r"Voting against (?:this|the)(?: monetary policy)? action (?:was|were) (.+)", re.S)


def body(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    return " ".join(ln for ln in lines if ln and not _BOILER.match(ln))


def vote(text: str) -> dict:
    m = _VOTE.search(text)
    against = _AGAINST.search(text)
    names = ""
    if against:  # the Fed always writes "<names>, who preferred ..."; names may contain initials with periods
        names = against.group(1).split(", who")[0].splitlines()[0].strip().rstrip(".")
    return {"for": int(m.group(1)) if m else None, "against": int(m.group(2)) if m else None, "dissenters": names}


def lexicon(text: str) -> dict:
    low = body(text).lower()
    # whole words only: "ease" must not match "release"
    count = lambda t: len(re.findall("(?<![a-z])" + re.escape(t) + "(?![a-z])", low))
    hawk = {t: count(t) for t in HAWKISH if count(t)}
    dove = {t: count(t) for t in DOVISH if count(t)}
    h, d = sum(hawk.values()), sum(dove.values())
    return {"hawkish": hawk, "dovish": dove, "score": round((h - d) / (h + d), 3) if h + d else 0.0}


def diff(previous: str, latest: str) -> dict:
    a, b = body(previous).split(), body(latest).split()
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    added, removed = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("insert", "replace"):
            added.append(" ".join(b[j1:j2]))
        if op in ("delete", "replace"):
            removed.append(" ".join(a[i1:i2]))
    return {"added": [x for x in added if x], "removed": [x for x in removed if x],
            "similarity": round(sm.ratio(), 3)}


def compute(snap: Snapshot) -> dict:
    statements = sorted(i for i in snap.items if i.startswith("fed.statement."))
    if not statements:
        raise ValueError("no statement in the snapshot")
    latest_id = statements[-1]
    latest = snap.get(latest_id)["text"]
    out = {"signal": "communication_tone", "latest": latest_id, "vote": vote(latest), "lexicon": lexicon(latest),
           "previous": None, "diff": None, "evidence": [latest_id]}
    if len(statements) >= 2:
        prev_id = statements[-2]
        out["previous"] = prev_id
        out["diff"] = diff(snap.get(prev_id)["text"], latest)
        out["evidence"] = [prev_id, latest_id]
    return out


def direction(sig: dict) -> str:
    s = sig["lexicon"]["score"]
    tone = "hawkish" if s > 0.2 else "dovish" if s < -0.2 else "balanced"
    v = sig["vote"]
    unity = "unanimous" if v["against"] == 0 else f"{v['against']} dissent(s)" if v["against"] else "vote unknown"
    return f"{tone} wording, {unity}"
