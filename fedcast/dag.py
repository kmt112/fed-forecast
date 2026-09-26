"""Factor graph behind one ledger entry: what feeds what, with the values actually used.

Built from the ledger entry and its snapshot only. Evidence that is frozen but not yet read
by any model is marked `frozen`; components not yet built are `planned`. The graph therefore
never implies an influence that is not in the number.
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP, config
from fedcast.journey import _dist, _label
from fedcast.snapshot import Snapshot

COLUMNS = ("Frozen evidence", "Signals", "Models", "Pool", "Your input", "Forecast")

FRED_GROUPS = {
    "Inflation data": ["PCEPILFE", "CPILFESL"],
    "Labour data": ["UNRATE", "PAYEMS", "ICSA"],
    "Market data": ["T5YIE", "DGS2", "NFCI"],
}


def _p(probs: dict, outcome: int) -> float:
    return float(probs.get(str(outcome), probs.get(outcome, 0.0)))


def _top(probs: dict) -> str:
    best = max(OUTCOMES_BP, key=lambda o: _p(probs, o))
    return f"{_label(best)} {_p(probs, best) * 100:.0f}%"


def _node(id: str, col: int, label: str, summary: str, kind: str, status: str, body: str,
          rows: list | None = None, evidence: list | None = None) -> dict:
    return {"id": id, "col": col, "label": label, "summary": summary, "kind": kind, "status": status,
            "detail": {"body": body, "rows": rows or [], "evidence": evidence or []}}


def build(entry: dict, snap: Snapshot, watchlist: list[dict] | None = None) -> dict:
    fc = entry["forecast"]
    m = fc["models"]["market_implied"]
    nodes: list[dict] = []
    edges: list[dict] = []

    def link(a: str, b: str, status: str = "live") -> None:
        edges.append({"from": a, "to": b, "status": status})

    # --- column 0: frozen evidence ------------------------------------------------------
    cal = snap.get("calendar")
    effr = snap.get("effr")["latest"]
    nodes.append(_node("calendar", 0, "FOMC calendar", f"next {cal['next_meeting']}", "source", "live",
                       "Scheduled meeting dates from federalreserve.gov. Fixes which meeting is being forecast "
                       "and whether the month after it is meeting-free, which decides how the futures price is read.",
                       [["Next decision", cal["next_meeting"]], ["Meetings in window", ", ".join(cal["meetings"])]],
                       ["calendar"]))
    nodes.append(_node("effr", 0, "Overnight rate (EFFR)", f"{effr['effr']:.2f}% on {effr['date']}", "source", "live",
                       "The effective federal funds rate: what banks actually paid to borrow overnight, published "
                       "by the New York Fed. This is the starting point every change is measured from.",
                       [["EFFR", f"{effr['effr']:.2f}%"], ["Date", effr["date"]],
                        ["Target range", f"{effr['target_low']:.2f}% to {effr['target_high']:.2f}%"]], ["effr"]))

    contract_id = next(e for e in m["evidence"] if e.startswith("futures."))
    contract = snap.get(contract_id)
    nodes.append(_node(contract_id, 0, f"Futures {contract['symbol'].split('.')[0]}", f"price {contract['price']}",
                       "source", "live",
                       f"30-day fed funds futures for {contract['contract_month']}. The contract settles at 100 minus "
                       "that month's average overnight rate, so its price is the market's bet on the rate.",
                       [["Symbol", contract["symbol"]], ["Price", str(contract["price"])],
                        ["Implied average rate", f"100 − {contract['price']} = {100 - contract['price']:.3f}%"],
                        ["Volume", str(contract.get("volume"))]], [contract_id]))
    others = sorted(i for i in snap.items if i.startswith("futures.") and i != contract_id)
    if others:
        nodes.append(_node("futures.other", 0, "Other futures", f"{len(others)} contracts, unused", "source", "frozen",
                           "Adjacent contract months, frozen for the record. Not read by any model yet; a later "
                           "version can use them to cross-check the chosen contract.",
                           [[i.split(".")[1], f"price {snap.get(i)['price']}"] for i in others], others))

    for label, series in FRED_GROUPS.items():
        rows, ids = [], []
        for sid in series:
            iid = f"fred.{sid}"
            if iid not in snap.items:
                continue
            obs = next((o for o in snap.get(iid)["observations"] if o["value"] is not None), None)
            rows.append([f"{sid}: {config.FRED_SERIES[sid]}", f"{obs['value']:g} ({obs['date']})" if obs else "no data"])
            ids.append(iid)
        if ids:
            nodes.append(_node(f"fred.{label}", 0, label, f"{len(ids)} series, frozen", "source", "frozen",
                               "Frozen as it stood on the snapshot date (FRED real-time vintage), so a later "
                               "revision cannot leak in. No model reads it yet.", rows, ids))

    for d in sorted(i for i in snap.items if i.startswith("fed.")):
        text = snap.get(d)["text"]
        kind = "statement" if ".statement." in d else "minutes"
        nodes.append(_node(d, 0, f"Fed {kind} {d[-10:]}", f"{len(text.split())} words, frozen", "source", "frozen",
                           f"The full text of the {kind}, frozen. It will be read by the communications analyst, "
                           "which must quote it for every claim. No model reads it yet.",
                           [["Opens with", text[:320].strip() + "…"]], [d]))

    n_watch = len([w for w in (watchlist or []) if w.get("status") == "active"])
    nodes.append(_node("watchouts", 0, "Your watch-outs", f"{n_watch} active", "human", "planned",
                       "Standing directives ('watch for XYZ'). Each one must be addressed explicitly in every "
                       "analyst trace. The analysts are not built yet, so nothing acts on them today.",
                       [[w["id"], w["directive"]] for w in (watchlist or [])]))

    # --- column 1: signals ---------------------------------------------------------------
    nodes.append(_node("sig.rate_before", 1, "Rate before meeting", f"{m['rate_before']:.2f}%", "signal", "live",
                       "The latest EFFR is taken as the rate that holds until the decision.",
                       [["Rate before", f"{m['rate_before']:.2f}%"]], ["effr"]))
    link("effr", "sig.rate_before")

    implied = 100.0 - contract["price"]
    if m["method"] == "next_month_contract":
        body = ("The month after the meeting has no meeting of its own, so its contract trades entirely at the "
                "post-meeting rate and reads the market's expected new rate directly.")
        rows = [["Implied rate after meeting", f"100 − {contract['price']} = {implied:.3f}%"],
                ["Expected change", f"{implied:.3f}% − {m['rate_before']:.2f}% = {m['expected_change_bp']:+.1f} bp"]]
    else:
        body = ("The meeting-month contract settles at the month's average rate, a day-weighted blend of the rate "
                "before and after the decision; the after-meeting rate is backed out of that average.")
        rows = [["Implied month-average rate", f"100 − {contract['price']} = {implied:.3f}%"],
                ["Expected change (day-weighted)", f"{m['expected_change_bp']:+.1f} bp"]]
    nodes.append(_node("sig.change", 1, "Market-expected change", f"{m['expected_change_bp']:+.1f} bp", "signal", "live",
                       body, rows, [contract_id, "effr", "calendar"]))
    for src in (contract_id, "effr", "calendar"):
        link(src, "sig.change")

    planned_signals = [
        ("sig.inflation", "Inflation gap", "Core PCE and CPI inflation against the 2% goal.", ["fred.Inflation data"]),
        ("sig.labour", "Labour slack", "Unemployment, payroll growth and claims against trend.", ["fred.Labour data"]),
        ("sig.financial", "Financial conditions", "Breakevens, the 2-year yield and the Chicago Fed index.",
         ["fred.Market data"]),
        ("sig.tone", "Communication tone", "Hawkish/dovish reading of the statement and minutes, every claim quoted.",
         [d for d in snap.items if d.startswith("fed.")]),
        ("sig.history", "Base rates", "How often the Fed has moved, held, or surprised in comparable set-ups.",
         ["calendar"]),
    ]
    for sid, label, what, srcs in planned_signals:
        nodes.append(_node(sid, 1, label, "planned", "signal", "planned",
                           what + " Not computed yet, so it has no effect on today's number."))
        for s in srcs:
            link(s, sid, "planned")

    # --- column 2: models ----------------------------------------------------------------
    nodes.append(_node("model.market", 2, "Market-implied", _top(m["probabilities"]), "model", "live",
                       f"The Fed moves in 25 bp steps, so an expected change of {m['expected_change_bp']:+.1f} bp "
                       f"({m['expected_change_bp'] / 25:+.2f} of a step) is shared between the two nearest outcomes.",
                       [["Distribution", _dist(m["probabilities"])], ["Method", m["method"]]], m["evidence"]))
    link("sig.change", "model.market")

    planned_models = [
        ("model.taylor", "Taylor rule", "A policy-rule rate from inflation and slack, compared with the current rate.",
         ["sig.inflation", "sig.labour", "sig.rate_before"]),
        ("model.probit", "Ordered probit", "A statistical model fitted on past meetings using data as first published.",
         ["sig.inflation", "sig.labour", "sig.financial"]),
        ("model.base", "Historical base rates", "Frequencies of cut/hold/hike in comparable situations.",
         ["sig.history"]),
        ("model.llm", "LLM analysts", "Specialist analysts, a hawk-vs-dove debate and a verifier; output is a "
         "bounded, cited signal, never the final number.", ["sig.tone", "sig.inflation", "sig.labour", "watchouts"]),
    ]
    for mid, label, what, srcs in planned_models:
        nodes.append(_node(mid, 2, label, "planned", "model", "planned",
                           what + " Not built yet; weight 0 in the pool until it passes the eval gate."))
        for s in srcs:
            link(s, mid, "planned")

    # --- columns 3-5: pool, human input, forecast ------------------------------------------
    weights = fc["pool_weights"]
    nodes.append(_node("pool", 3, "Pool (machine only)", _top(fc["machine_only"]), "pool", "live",
                       "Weighted average of every live model, done in code. No language model writes the number. "
                       + ("Only one model is live, so the pool equals it." if len(weights) == 1 else ""),
                       [[name, f"weight {w:g}"] for name, w in weights.items()]
                       + [["machine_only", _dist(fc["machine_only"])]]))
    link("model.market", "pool")
    for mid, *_ in planned_models:
        link(mid, "pool", "planned")

    views = fc["human"]["views_applied"]
    budget = fc["human"]["net_budget"]
    nodes.append(_node("views", 4, "Your views", f"{len(views)} active, tilt {budget * 100:+.0f} pp", "human", "live",
                       "Each active view adds a signed tilt (3/6/10 pp by strength), netted and capped at 10 pp. Code "
                       "shifts exactly that much probability, keeps the machine forecast's shape, and never adds "
                       "weight to an outcome the machine gave 0%. Rewording a rationale cannot change the number.",
                       [[v["id"], f"{v['direction']}, strength {v['strength']}: {v['rationale']}"] for v in views]
                       + [["Net tilt", f"{budget * 100:+.0f} pp"]]))
    link("pool", "views")

    nodes.append(_node("out", 5, "Forecast", _top(fc["human_adjusted"]), "output", "live",
                       f"The recorded forecast for the {fc['meeting']} decision, ledger entry #{entry['seq']}.",
                       [["machine_only", _dist(fc["machine_only"])], ["human_adjusted", _dist(fc["human_adjusted"])],
                        ["Snapshot", fc["snapshot_hash"][:12]], ["Code version", entry["code_version"]],
                        ["Entry fingerprint", entry["entry_hash"]]]))
    link("views", "out")

    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["from"] in ids and e["to"] in ids]
    return {"columns": list(COLUMNS), "nodes": nodes, "edges": edges}
