"""Scorecard measurements.

`measure` scores the LLM arms on one snapshot (S1, S2, S3, S10) from the recorded analyses.
`deterministic` scores the code part of the chain, the models, the pool and the ledger (S4, S5, S6, S7, S9), by
actually perturbing the snapshot and recomputing: shock tests must move the number the right way, irrelevant
changes must not move it at all, rewording a view's rationale must not move it, every ledger entry must be
coherent and attributable, and entries recorded under the current code must recompute bit-for-bit.

Each measurement names the arm or scope it applies to, the value, the pre-registered threshold and pass/fail.
S1 for an arm that outputs probabilities (the naive control) is in pp, as pre-registered. The specialists
output a bounded tilt in bp rather than a distribution, so their S1 is reported in bp of tilt as a proxy,
labelled as such; it becomes a pp measurement once a tilt-to-probability mapping is adopted by amendment.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Callable

from fedcast import OUTCOMES_BP
from fedcast.scorecard import SCORECARD, TILT_CAP
from fedcast.snapshot import Item, Snapshot

_DIM = {d.id: d for d in SCORECARD}


def _row(dim_id: str, arm: str, value, unit: str, note: str = "", runs: int | None = None,
         details: list[dict] | None = None) -> dict:
    d = _DIM[dim_id]
    ok = None if value is None else d.passes(value)
    return {"id": dim_id, "name": d.name, "arm": arm, "value": value, "unit": unit, "threshold": d.threshold,
            "direction": d.direction, "pass": ok, "runs": runs, "note": note, "details": details or []}


def measure(analyses: dict[str, dict | None]) -> list[dict]:
    rows: list[dict] = []
    naive = analyses.get("naive")
    if naive:
        s = naive["summary"]
        rows.append(_row("S1", "A naive", s.get("max_std_pp"), "pp", "max std of any outcome probability across runs", s["runs"]))
        rows.append(_row("S2", "A naive", 0.0, "pct", "nothing to cite: groundedness is 0 by construction", s["runs"]))
        rows.append(_row("S3", "A naive", s["leakage_total"], "count", "numbers in the reasoning, all from memory", s["runs"]))
    evid = analyses.get("evidence_only")
    if evid:
        s = evid["summary"]
        rows.append(_row("S1", "B evidence", s.get("max_std_pp"), "pp", "max std of any outcome probability across runs", s["runs"]))
        rows.append(_row("S2", "B evidence", None, "pct", "free-form answer: no quotes, so groundedness cannot be measured", s["runs"]))
        rows.append(_row("S3", "B evidence", s["leakage_total"], "count", "numbers in the reasoning not found in the evidence", s["runs"]))
    gen = analyses.get("generalist")
    if gen:
        s = gen["summary"]
        rows.append(_row("S1", "C structure", s["tilt_std_bp"], "bp of tilt (proxy)", "std of tilt across runs; needs 2+ runs", s["runs"]))
        rows.append(_row("S2", "C structure", s["groundedness_pct_mean"], "pct", "quote-verified share of claims", s["runs"]))
        rows.append(_row("S3", "C structure", s["leakage_total"], "count", "numbers not in the evidence, all runs", s["runs"]))
        rows.append(_row("S10", "C structure", 100.0 if s["watchouts_missing_total"] == 0 else 0.0, "pct", "every active watch-out addressed by id", s["runs"]))
    specialists = {k: v for k, v in analyses.items() if v and k not in ("naive", "evidence_only", "generalist")}
    if specialists:
        n_runs = min(v["summary"]["runs"] for v in specialists.values())
        stds = [v["summary"]["tilt_std_bp"] for v in specialists.values() if v["summary"]["tilt_std_bp"] is not None]
        rows.append(_row("S1", "D specialists", max(stds) if stds else None, "bp of tilt (proxy)",
                         "max std of tilt across runs, worst specialist; needs 2+ runs" if stds else "needs 2+ runs per specialist", n_runs))
        g = [v["summary"]["groundedness_pct_mean"] for v in specialists.values()]
        rows.append(_row("S2", "D specialists", round(min(g), 1), "pct", "quote-verified share, worst specialist", n_runs))
        rows.append(_row("S3", "D specialists", sum(v["summary"]["leakage_total"] for v in specialists.values()), "count",
                         "numbers not in the quoted evidence, all specialists and runs", n_runs))
        rows.append(_row("S10", "D specialists", 100.0 if all(v["summary"]["watchouts_missing_total"] == 0 for v in specialists.values()) else 0.0,
                         "pct", "every active watch-out addressed by id in every run", n_runs))
    return rows


# --- the deterministic chain: models, pool, views, ledger -------------------------------------------------------

def _with_item(snap: Snapshot, item_id: str, content=None, fetched_at: str | None = None, drop: bool = False) -> Snapshot:
    """A copy of the snapshot with one item replaced, re-stamped or removed. The original is never touched."""
    new = Snapshot(snap.as_of, missing=dict(snap.missing))
    for k, it in snap.items.items():
        if k == item_id:
            if drop:
                continue
            if content is not None:
                it = Item.make(k, it.kind, it.source, content)
            elif fetched_at:
                it = Item(it.id, it.kind, it.source, fetched_at, it.content, it.sha256)
        new.items[k] = it
    return new


def _expected_bp(probs: dict) -> float:
    return sum(float(o) * p for o, p in probs.items())


def _tv(a: dict, b: dict) -> float:
    return 0.5 * sum(abs(a[o] - b[o]) for o in a)


def _newest(obs: list[dict]) -> int:
    return next(i for i, o in enumerate(obs) if o["value"] is not None)


def _scaled_newest(content: dict, factor: float = 1.0, add: float = 0.0) -> dict:
    out = json.loads(json.dumps(content))
    i = _newest(out["observations"])
    out["observations"][i]["value"] = out["observations"][i]["value"] * factor + add
    return out


def _analyses(snap: Snapshot) -> dict:
    from fedcast.llm import analyst

    return {name: analyst.latest(snap.hash, name) for name in analyst.SPECIALISTS}


def _view(direction: str, strength: int, rationale: str, as_of: date):
    from fedcast.human.views import View

    return View(id="H2-999", author="eval", created_at=datetime(as_of.year, as_of.month, as_of.day, 0, 0),
                expires_on=as_of, direction=direction, strength=strength, rationale=rationale)


def shock_tests(snap: Snapshot) -> list[dict]:
    """S4. Each shock changes one input in a direction whose effect on the policy outlook is not in doubt; the pool's
    expected change in bp must move the same way. Shocks whose input is absent from the snapshot are reported as
    not applicable and left out of the share."""
    from fedcast import forecast

    an = _analyses(snap)
    base = forecast.compute(snap, [], an)
    e0 = _expected_bp(base["machine_only"])
    fut = next((i for i in base["models"].get("market_implied", {}).get("evidence", []) if i.startswith("futures.")), None)
    pm = next((i for i in snap.items if i.startswith("human.pm.") and snap.get(i).get("status") == "active"
               and snap.get(i).get("meeting") == base["meeting"]), None)
    shocks: list[tuple[str, int, Callable[[], Snapshot] | None]] = [
        ("futures price 0.10 lower (market prices 10 bp more tightening)", +1,
         (lambda: _with_item(snap, fut, {**snap.get(fut), "price": snap.get(fut)["price"] - 0.10})) if fut else None),
        ("futures price 0.10 higher (market prices 10 bp more easing)", -1,
         (lambda: _with_item(snap, fut, {**snap.get(fut), "price": snap.get(fut)["price"] + 0.10})) if fut else None),
        ("core PCE index 0.5% higher in its latest month (inflation gap wider)", +1,
         (lambda: _with_item(snap, "fred.PCEPILFE", _scaled_newest(snap.get("fred.PCEPILFE"), factor=1.005)))
         if "fred.PCEPILFE" in snap.items else None),
        ("unemployment 0.5 pp higher in its latest month (more slack)", -1,
         (lambda: _with_item(snap, "fred.UNRATE", _scaled_newest(snap.get("fred.UNRATE"), add=0.5)))
         if "fred.UNRATE" in snap.items else None),
        ("prediction-market odds move 20 points from no change to +25 bps", +1,
         (lambda: _with_item(snap, pm, _pm_shift(snap.get(pm), 20.0))) if pm else None),
    ]
    details = []
    for name, sign, make in shocks:
        if make is None:
            details.append({"shock": name, "delta_bp": None, "ok": None, "note": "input not in this snapshot"})
            continue
        got = forecast.compute(make(), [], an)
        delta = _expected_bp(got["machine_only"]) - e0
        details.append({"shock": name, "delta_bp": round(delta, 2), "ok": (delta > 1e-9) if sign > 0 else (delta < -1e-9)})
    # human views: a hawkish view must move the adjusted track hawkish by exactly its budget, a dovish one the reverse
    for direction, strength, sign in (("hawkish", 3, +1), ("dovish", 1, -1)):
        got = forecast.compute(snap, [_view(direction, strength, "Evaluation shock: a standing view of known direction.", snap.as_of)], an)
        delta = _expected_bp(got["human_adjusted"]) - _expected_bp(got["machine_only"])
        tv = _tv(got["human_adjusted"], got["machine_only"])
        budget = abs(got["human"]["net_budget"])
        ok = ((delta > 1e-9) if sign > 0 else (delta < -1e-9)) and abs(tv - budget) < 1e-6
        details.append({"shock": f"{direction} view, strength {strength} (budget {budget * 100:.0f} pp)", "delta_bp": round(delta, 2),
                        "ok": ok, "note": f"{tv * 100:.2f} pp of probability changed hands"})
    return details


def _pm_shift(content: dict, points: float) -> dict:
    out = json.loads(json.dumps(content))
    prices = out["prices"]
    move = min(points, prices.get("0", 0.0))
    prices["0"] = prices.get("0", 0.0) - move
    prices["25"] = prices.get("25", 0.0) + move
    return out


def noise_tests(snap: Snapshot) -> list[dict]:
    """S5. Changes that carry no information about the decision; the machine forecast must not move at all."""
    from fedcast import forecast

    an = _analyses(snap)
    base = forecast.compute(snap, [], an)["machine_only"]
    stamp = "2000-01-01T00:00:00+00:00"
    fut = next((i for i in snap.items if i.startswith("futures.")), None)
    stmt = max((i for i in snap.items if i.startswith("fed.statement.")), default=None)
    cases: list[tuple[str, Callable[[], Snapshot] | None]] = [
        ("an unrelated document added to the snapshot", lambda: _added(snap)),
        ("every item re-stamped with a different fetch time", lambda: _restamped(snap, stamp)),
        ("items loaded in reverse order", lambda: _reversed(snap)),
        ("futures quote volume changed", (lambda: _with_item(snap, fut, {**snap.get(fut), "volume": 1})) if fut else None),
        ("statement text with doubled spaces",
         (lambda: _with_item(snap, stmt, {**snap.get(stmt), "text": snap.get(stmt)["text"].replace(" ", "  ")})) if stmt else None),
    ]
    details = []
    for name, make in cases:
        if make is None:
            details.append({"perturbation": name, "shift_pp": None, "ok": None, "note": "input not in this snapshot"})
            continue
        got = forecast.compute(make(), [], an)["machine_only"]
        shift = max(abs(got[o] - base[o]) for o in OUTCOMES_BP) * 100
        details.append({"perturbation": name, "shift_pp": round(shift, 4), "ok": shift <= 1e-9})
    return details


def _added(snap: Snapshot) -> Snapshot:
    new = _with_item(snap, "__none__")
    new.add(Item.make("human.doc.H5-999", "human_document", "eval",
                      {"id": "H5-999", "title": "Unrelated note", "relevance": "none", "text": "The office plants were watered on Tuesday."}))
    return new


def _restamped(snap: Snapshot, stamp: str) -> Snapshot:
    new = Snapshot(snap.as_of, missing=dict(snap.missing))
    for k, it in snap.items.items():
        new.items[k] = Item(it.id, it.kind, it.source, stamp, it.content, it.sha256)
    return new


def _reversed(snap: Snapshot) -> Snapshot:
    new = Snapshot(snap.as_of, missing=dict(snap.missing))
    for k in reversed(list(snap.items)):
        new.items[k] = snap.items[k]
    return new


def paraphrase_test(snap: Snapshot) -> list[dict]:
    """S6 for the typed human inputs: a view's rationale is text; rewording it must leave both tracks unchanged.
    The LLM arms' paraphrase test (reworded prompts) is not built yet and is reported separately when it is."""
    from fedcast import forecast

    an = _analyses(snap)
    a = forecast.compute(snap, [_view("hawkish", 2, "Statement language shifted toward inflation risk.", snap.as_of)], an)
    b = forecast.compute(snap, [_view("hawkish", 2, "The wording of the statement now leans towards the risk that inflation stays high.", snap.as_of)], an)
    shift = max(abs(a["human_adjusted"][o] - b["human_adjusted"][o]) for o in OUTCOMES_BP) * 100
    return [{"perturbation": "view rationale reworded (same direction and strength)", "shift_pp": round(shift, 4), "ok": shift <= 1e-9}]


def coherence(entries: list[dict]) -> list[dict]:
    """S7 over the ledger: both tracks sum to 1, and the adjusted track is exactly the machine track tilted by the
    recorded views' net budget, so every difference between the tracks is attributable to a recorded view."""
    from fedcast.human.views import View, apply_tilt

    details = []
    for e in entries:
        f = json.loads(json.dumps(e["forecast"]))  # as the ledger stores it: string keys
        m = {o: f["machine_only"][str(o)] for o in OUTCOMES_BP}
        h = {o: f["human_adjusted"][str(o)] for o in OUTCOMES_BP}
        sums_ok = abs(sum(m.values()) - 1) < 1e-9 and abs(sum(h.values()) - 1) < 1e-9
        views = [View(**v) for v in f["human"]["views_applied"]]
        budget = max(-TILT_CAP, min(TILT_CAP, sum(v.signed_budget() for v in views)))
        budget_ok = abs(budget - f["human"]["net_budget"]) < 1e-9
        tilted = dict(zip(OUTCOMES_BP, apply_tilt([m[o] for o in OUTCOMES_BP], f["human"]["net_budget"])))
        tilt_ok = max(abs(tilted[o] - h[o]) for o in OUTCOMES_BP) < 1e-9
        details.append({"entry": e["seq"], "sums_to_one": sums_ok, "budget_matches_views": budget_ok,
                        "adjusted_is_tilted_machine": tilt_ok, "ok": sums_ok and budget_ok and tilt_ok})
    return details


def replay(entries: list[dict], find_snapshot: Callable[[str], Snapshot | None], current_spec: str) -> list[dict]:
    """S9: an entry recorded under the current spec must give back exactly the probabilities it published when its
    snapshot is recomputed with the current code. Entries recorded under an earlier spec (pool weights, floor or a
    model rule changed since, by logged amendment) are labelled and left out of the share; whether their numbers
    still match is shown for information. Fields added to the record since (new weight-0 models, annotations) do
    not count against an entry; the published numbers do."""
    from fedcast import forecast
    from fedcast.human.views import View

    details = []
    for e in entries:
        f = json.loads(json.dumps(e["forecast"]))  # as the ledger stores it: string keys
        spec = e.get("spec_hash", "")
        snap = find_snapshot(f["snapshot_hash"])
        if snap is None:
            details.append({"entry": e["seq"], "spec": spec[:8], "ok": None if spec != current_spec else False, "note": "snapshot not found"})
            continue
        got = json.loads(json.dumps(forecast.compute(snap, [View(**v) for v in f["human"]["views_applied"]])))
        nums = got["machine_only"] == f["machine_only"] and got["human_adjusted"] == f["human_adjusted"]
        full = got == f
        if spec != current_spec:
            details.append({"entry": e["seq"], "spec": spec[:8], "ok": None,
                            "note": "recorded under an earlier spec" + ("; numbers still match" if nums else "; numbers differ (a weight, floor or rule changed since)")})
            continue
        details.append({"entry": e["seq"], "spec": spec[:8], "ok": nums,
                        "note": "" if full else "numbers match; record has fields added since" if nums
                        else "published numbers differ under the current code: a rule changed after this entry without a new spec hash (amendment log)"})
    return details


_CACHE: dict = {}


def deterministic(snap: Snapshot, entries: list[dict], find_snapshot: Callable[[str], Snapshot | None],
                  current_spec: str) -> list[dict]:
    """Rows for S4, S5, S6, S7 and S9 from the code part of the chain. Cached per (snapshot, ledger, spec)."""
    key = (snap.hash, tuple(e["entry_hash"] for e in entries), current_spec)
    if key in _CACHE:
        return _CACHE[key]
    rows = []
    sh = shock_tests(snap)
    scored = [d for d in sh if d["ok"] is not None]
    rows.append(_row("S4", "models + pool (code)", round(100 * sum(d["ok"] for d in scored) / len(scored), 1) if scored else None, "pct",
                     f"{len(scored)} shock tests: one input moved in a known direction, the pool's expected change must follow", details=sh))
    nz = noise_tests(snap)
    scored = [d for d in nz if d["ok"] is not None]
    rows.append(_row("S5", "models + pool (code)", round(max(d["shift_pp"] for d in scored), 4) if scored else None, "pp",
                     f"largest move of any outcome probability under {len(scored)} irrelevant changes to the snapshot", details=nz))
    pp = paraphrase_test(snap)
    rows.append(_row("S6", "human views (code)", pp[0]["shift_pp"], "pp",
                     "a view's rationale reworded: typed inputs only; the LLM arms' reworded-prompt test is not built yet", details=pp))
    co = coherence(entries)
    rows.append(_row("S7", "ledger (code)", round(100 * sum(d["ok"] for d in co) / len(co), 1) if co else None, "pct",
                     f"all {len(co)} ledger entries: tracks sum to 1 and the adjusted track is the machine track tilted by the recorded views",
                     runs=len(co) or None, details=co))
    rp = replay(entries, find_snapshot, current_spec)
    cur = [d for d in rp if d["ok"] is not None]
    older = len(rp) - len(cur)
    rows.append(_row("S9", "ledger (code)", round(100 * sum(d["ok"] for d in cur) / len(cur), 1) if cur else None, "pct",
                     (f"{len(cur)} entries recorded under the current spec give back their published probabilities when recomputed"
                      if cur else "no entry recorded under the current spec yet: run a forecast")
                     + (f"; {older} earlier entries were recorded under an earlier spec (amendment log) and are labelled, not scored" if older else ""),
                     runs=len(cur) or None, details=rp))
    _CACHE[key] = rows
    return rows
