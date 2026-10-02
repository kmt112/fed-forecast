"""Factor graph behind one ledger entry: what feeds what, with the values actually used.

Built from the ledger entry and its snapshot only. Evidence that is frozen but not yet read
by anything is `idle`; one computed from the snapshot but not yet in the number is `computed`;
components not yet built are `planned`. The graph therefore
never implies an influence that is not in the number.

Each node carries three explanations: `what` it is, `why` it bears on the decision, and
`how` it is (or will be) computed, so the page can teach as well as show.
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP, config
from fedcast.journey import _dist, _label
from fedcast.signals import inflation
from fedcast.snapshot import Snapshot

COLUMNS = ("Frozen evidence", "Signals", "Models", "Pool", "Your input", "Forecast")

FRED_GROUPS = {
    "Inflation data": ["PCEPILFE", "CPILFESL"],
    "Labour data": ["UNRATE", "PAYEMS", "ICSA"],
    "Market data": ["T5YIE", "DGS2", "NFCI"],
}

_GROUP_TEXT = {
    "Inflation data": (
        "Two price indexes: core PCE (the Fed's official gauge, published by the BEA about four weeks after "
        "the month ends) and core CPI (published by the BLS about two weeks after, so one month fresher). "
        "'Core' strips out food and energy, whose swings the Fed looks through.",
        "The Fed's mandate is price stability, defined as 2% PCE inflation. Where inflation sits against that "
        "goal, and which way it is heading, is the first thing every committee member looks at.",
        "Index levels are turned into annualised rates over 1, 3, 6 and 12 months, so the level tells you where "
        "inflation is and the short windows tell you where it is going. Frozen as the vintage known on the "
        "snapshot date; later revisions cannot leak in."),
    "Labour data": (
        "The unemployment rate and nonfarm payrolls (monthly, from the BLS jobs report, first Friday of the "
        "month) and initial jobless claims (weekly, the earliest read on layoffs).",
        "Maximum employment is the other half of the mandate. Rising slack pushes the Fed toward cuts even when "
        "inflation is still above target, as in 2024; a tight labour market removes that pressure.",
        "Each series is read against its own trend: unemployment against its sustainable level, payrolls "
        "against the pace that keeps unemployment steady, claims against their recent average."),
    "Market data": (
        "The 2-year Treasury yield, the 5-year breakeven inflation rate (nominal minus inflation-protected "
        "yield) and the Chicago Fed's National Financial Conditions Index.",
        "The 2-year yield is roughly the average policy rate investors expect over the next two years, so its "
        "gap to today's rate shows how much tightening or easing is priced. Breakevens are market-expected "
        "inflation, which the Fed watches for signs that expectations are coming unanchored. The NFCI shows "
        "whether financial conditions are tight or loose, i.e. whether policy is biting.",
        "Daily and weekly series, read as levels and as gaps to the policy rate."),
}


def _p(probs: dict, outcome: int) -> float:
    return float(probs.get(str(outcome), probs.get(outcome, 0.0)))


def _top(probs: dict) -> str:
    best = max(OUTCOMES_BP, key=lambda o: _p(probs, o))
    return f"{_label(best)} {_p(probs, best) * 100:.0f}%"


def _node(id: str, col: int, label: str, summary: str, kind: str, status: str, what: str,
          why: str = "", how: str = "", rows: list | None = None, evidence: list | None = None,
          today: str = "") -> dict:
    return {"id": id, "col": col, "label": label, "summary": summary, "kind": kind, "status": status,
            "detail": {"body": what, "why": why, "how": how, "today": today,
                       "rows": rows or [], "evidence": evidence or []}}


def _ann(obs: list[dict], k: int) -> float | None:
    vals = [o["value"] for o in obs if o["value"] is not None]
    if len(vals) <= k:
        return None
    return ((vals[0] / vals[k]) ** (12 / k) - 1) * 100


def build(entry: dict, snap: Snapshot, watchlist: list[dict] | None = None) -> dict:
    fc = entry["forecast"]
    m = fc["models"]["market_implied"]
    nodes: list[dict] = []
    edges: list[dict] = []

    def link(a: str, b: str, status: str = "live") -> None:
        edges.append({"from": a, "to": b, "status": status})

    def has(item_id: str) -> bool:
        return item_id in snap.items

    infl = None
    if has("fred.PCEPILFE") and has("fred.CPILFESL"):
        try:
            infl = inflation.compute(snap)
        except ValueError:
            infl = None

    # --- column 0: frozen evidence ------------------------------------------------------
    cal = snap.get("calendar")
    effr = snap.get("effr")["latest"]
    nodes.append(_node(
        "calendar", 0, "FOMC calendar", f"next {cal['next_meeting']}", "source", "live",
        what="The Federal Open Market Committee's scheduled meeting dates, from federalreserve.gov. The committee "
             "sets the policy rate eight times a year; the decision is announced at 2 pm on the second day.",
        why="It fixes which decision is being forecast, and whether the month after it is meeting-free, which "
            "decides how the futures price can be read. It also says which data releases will land before the "
            "meeting and which the committee will not yet have seen.",
        how="Parsed from the calendar page; the next scheduled decision on or after the snapshot date is the target.",
        rows=[["Next decision", cal["next_meeting"]], ["Meetings in window", ", ".join(cal["meetings"])]],
        evidence=["calendar"]))
    nodes.append(_node(
        "effr", 0, "Overnight rate (EFFR)", f"{effr['effr']:.2f}% on {effr['date']}", "source", "live",
        what="The effective federal funds rate: the volume-weighted median rate at which banks actually lent "
             "to each other overnight, published every morning by the New York Fed for the previous day.",
        why="The Fed sets a target range; this is where the rate really trades inside it, and it is the rate the "
            "futures contracts settle on. A policy change shows up here the next business day.",
        how="The latest print is used as the rate in force until the decision. Planned checks: flag a print more "
            "than 3 bp from its 5-day median (month- and quarter-end distortions), and record the spread to the "
            "bottom of the range so drift inside the range is not mistaken for policy.",
        rows=[["EFFR", f"{effr['effr']:.2f}%"], ["Date", effr["date"]],
              ["Target range", f"{effr['target_low']:.2f}% to {effr['target_high']:.2f}%"],
              ["Spread to range bottom", f"{(effr['effr'] - effr['target_low']) * 100:.0f} bp"]],
        evidence=["effr"]))

    contract_id = next(e for e in m["evidence"] if e.startswith("futures."))
    contract = snap.get(contract_id)
    nodes.append(_node(
        contract_id, 0, f"Futures {contract['symbol'].split('.')[0]}", f"price {contract['price']}", "source", "live",
        what=f"The 30-day fed funds futures contract for {contract['contract_month']}, traded on the CME. It settles "
             "at 100 minus that month's average effective rate, so a price of 96 means traders expect an average "
             "rate of 4% that month.",
        why="It is the most direct measure of what investors expect the Fed to do, with real money behind it. The "
            "Fed very rarely surprises a market that has priced a move with conviction, and it signals ahead of "
            "time precisely to avoid doing so. CME's FedWatch tool is a published rendering of this same price "
            "with the same arithmetic.",
        how="Contract choice: if the month after the meeting has no meeting, that contract trades entirely at the "
            "post-meeting rate and reads it directly; otherwise the meeting-month contract is unpicked by day "
            "count. Quote is delayed; its timestamp is recorded. Planned: staleness check and a second price source.",
        rows=[["Symbol", contract["symbol"]], ["Price", str(contract["price"])],
              ["Implied average rate", f"100 − {contract['price']} = {100 - contract['price']:.3f}%"],
              ["Volume", str(contract.get("volume"))]],
        evidence=[contract_id]))
    others = sorted(i for i in snap.items if i.startswith("futures.") and i != contract_id)
    if others:
        nodes.append(_node(
            "futures.other", 0, "Adjacent contracts", f"{len(others)} months, unused", "source", "idle",
            what="The adjacent fed-funds futures contract months (the same CME instrument, not prediction markets), "
                 "kept for the record.",
            why="They let the chosen contract be cross-checked: the meeting-month contract implies the same move "
                "by a noisier route, and the contract two months out shows what is priced for the meeting after.",
            how="Not read by any model yet.",
            rows=[[i.split(".")[1], f"price {snap.get(i)['price']} (implies {100 - snap.get(i)['price']:.3f}%)"]
                  for i in others],
            evidence=others))

    for label, series in FRED_GROUPS.items():
        rows, ids = [], []
        for sid in series:
            iid = f"fred.{sid}"
            if not has(iid):
                continue
            obs = snap.get(iid)["observations"]
            latest = next((o for o in obs if o["value"] is not None), None)
            rows.append([f"{sid}: {config.FRED_SERIES[sid]}",
                         f"{latest['value']:g} ({latest['date']})" if latest else "no data"])
            ids.append(iid)
        if ids:
            what, why, how = _GROUP_TEXT[label]
            used = label == "Inflation data" and infl is not None
            nodes.append(_node(f"fred.{label}", 0, label,
                               f"{len(ids)} series, {'read by inflation gap' if used else 'not yet used'}", "source",
                               "computed" if used else "idle", what=what, why=why,
                               how=how + (" Read by the inflation-gap signal." if used else " Nothing reads this yet."),
                               rows=rows, evidence=ids))

    for d in sorted(i for i in snap.items if i.startswith("fed.")):
        text = snap.get(d)["text"]
        kind = "statement" if ".statement." in d else "minutes"
        if kind == "statement":
            why = ("The statement is drafted word by word and changes are deliberate: a phrase added or dropped "
                   "('additional firming', 'the extent and timing of') is how the committee signals its next move. "
                   "The vote and any dissents show how united it is.")
            how = ("Planned: fetch the previous statement and compute a word-level diff, parse the vote "
                   "mechanically, then have the communications analyst read the diff and quote every claim.")
        else:
            why = ("The minutes, released three weeks after the meeting, show the range of views: how 'many', "
                   "'several' or 'a few' participants leaned, and what would change their minds. That reveals "
                   "the direction of travel before it reaches the statement.")
            how = "Planned: count the participant-weighting phrases and let the analyst quote the key passages."
        nodes.append(_node(
            d, 0, f"Fed {kind} {d[-10:]}", f"{len(text.split())} words, not yet used", "source", "idle",
            what=f"The full text of the FOMC {kind}, frozen as published.", why=why, how=how + " No model reads it yet.",
            rows=[["Opens with", text[:320].strip() + "…"]], evidence=[d]))

    n_watch = len([w for w in (watchlist or []) if w.get("status") == "active"])
    nodes.append(_node(
        "watchouts", 0, "Your watch-outs", f"{n_watch} active", "human", "planned",
        what="Standing directives you have entered: things every future run must check for.",
        why="They encode what you have learned that the data feeds do not capture, and force the analysts to "
            "look rather than drift past it.",
        how="Each one must be addressed explicitly in every analyst trace ('H1-001: checked, found / not found, "
            "evidence …'). The analysts are not built yet, so nothing acts on them today.",
        rows=[[w["id"], w["directive"]] for w in (watchlist or [])]))

    docs = sorted(i for i in snap.items if i.startswith("human.doc."))
    nodes.append(_node(
        "documents", 0, "Your documents", f"{len(docs)} in snapshot" if docs else "none yet", "human",
        "idle" if docs else "planned",
        what="Your own write-ups, notes, uploaded reports and analyses, frozen into the snapshot as evidence "
             "tagged human-sourced. The verbatim text is what is stored; no summary stands in for it.",
        why="Analysts you trust, or your own reading, may know things the data feeds cannot show. Entering that "
            "as evidence keeps it visible and quotable rather than letting it move the number silently.",
        how="Only the LLM analysts will read these, quoting them like any other item; the quant models never see "
            "them and they never move the number directly. Enter a view if you want the number to move.",
        rows=[[snap.get(d)["id"], f"{snap.get(d)['title']} ({snap.get(d)['relevance']})"] for d in docs],
        evidence=docs))

    # --- column 1: signals ---------------------------------------------------------------
    nodes.append(_node(
        "sig.rate_before", 1, "Rate before meeting", f"{m['rate_before']:.2f}%", "signal", "live",
        what="The policy rate in force going into the meeting, taken as the latest EFFR.",
        why="The decision is a change, not a level: cut, hold or hike are all measured from here, and so is the "
            "distance to where a policy rule says the rate should be.",
        how="Latest EFFR print. The target-range midpoint would be the alternative; EFFR is used because the "
            "futures settle on it.",
        rows=[["Rate before", f"{m['rate_before']:.2f}%"]], evidence=["effr"]))
    link("effr", "sig.rate_before")

    implied = 100.0 - contract["price"]
    if m["method"] == "next_month_contract":
        how = ("The month after the meeting has no meeting of its own, so its contract trades entirely at the "
               "post-meeting rate: 100 minus the price is the expected new rate, and subtracting the rate before "
               "gives the expected change.")
        rows = [["Implied rate after meeting", f"100 − {contract['price']} = {implied:.3f}%"],
                ["Expected change", f"{implied:.3f}% − {m['rate_before']:.2f}% = {m['expected_change_bp']:+.1f} bp"]]
    else:
        how = ("The meeting-month contract settles at the month's average rate, a day-weighted blend of the rate "
               "before and after the decision; the after-meeting rate is backed out of that average.")
        rows = [["Implied month-average rate", f"100 − {contract['price']} = {implied:.3f}%"],
                ["Expected change (day-weighted)", f"{m['expected_change_bp']:+.1f} bp"]]
    nodes.append(_node(
        "sig.change", 1, "Market-expected change", f"{m['expected_change_bp']:+.1f} bp", "signal", "live",
        what="The change in the policy rate that the futures market is pricing for this meeting, in basis points.",
        why="At a five-week horizon this is the single strongest predictor there is: it already aggregates the "
            "data, the Fed's own guidance and every speech. The other signals exist to explain it, to catch the "
            "rare occasions it is wrong, and to show the reasoning.",
        how=how, rows=rows, evidence=[contract_id, "effr", "calendar"]))
    for src in (contract_id, "effr", "calendar"):
        link(src, "sig.change")

    unrate = snap.get("fred.UNRATE")["observations"] if has("fred.UNRATE") else []
    dgs2 = snap.get("fred.DGS2")["observations"] if has("fred.DGS2") else []
    lab_rows, fin_rows = [], []
    if unrate:
        u = [o["value"] for o in unrate if o["value"] is not None]
        lab_rows = [["Unemployment", f"{u[0]:.1f}% (a year ago {u[12]:.1f}%)" if len(u) > 12 else f"{u[0]:.1f}%"]]
    if dgs2:
        y = next(o["value"] for o in dgs2 if o["value"] is not None)
        fin_rows = [["2-year yield minus policy rate", f"{y:.2f}% − {m['rate_before']:.2f}% = {(y - m['rate_before']) * 100:+.0f} bp"]]

    planned_signals = [
        ("sig.labour", "Labour slack",
         "How much spare capacity the labour market has: unemployment against its sustainable level, payroll "
         "growth against the pace needed to absorb new workers, claims against their trend.",
         "Rising slack is the second mandate calling for easier policy, and it can override inflation that is "
         "still above target, as in 2024. A tight market removes that pressure and lets inflation dominate. The "
         "Sahm rule (3-month average unemployment half a point above its 12-month low) is the classic "
         "recession trigger.",
         "Unemployment gap to a ~4.2% sustainable level; 3-month payroll average against a breakeven pace; 4-week "
         "claims against the 26-week average. Not computed yet, so it has no effect on today's number.",
         lab_rows, ["fred.Labour data"]),
        ("sig.financial", "Financial conditions",
         "What the bond market expects and how tight financial conditions are.",
         "The 2-year yield is close to the average policy rate expected over two years, so a wide positive gap to "
         "today's rate means the market expects more hikes, which corroborates or contradicts the futures. "
         "Breakevens show whether inflation expectations stay anchored near 2%, which the Fed treats as a "
         "precondition for easing. A loose NFCI despite high rates tells the Fed its tightening is not biting.",
         "Gaps and levels from the three series. Not computed yet.",
         fin_rows, ["fred.Market data"]),
        ("sig.tone", "Communication tone",
         "A hawkish-to-dovish reading of what the committee has said, concentrating on what changed.",
         "The Fed telegraphs. Wording changes in the statement, the balance of views in the minutes and the Chair's "
         "press-conference answers move markets precisely because they precede decisions.",
         "Planned: deterministic word diff of statement against the previous one, a lexicon score as a baseline, and "
         "an LLM analyst reading that must quote every claim. Not computed yet.",
         [], [d for d in snap.items if d.startswith("fed.")]),
        ("sig.history", "Base rates",
         "How often, historically, the Fed has moved, held or surprised in situations like this one.",
         "It is the antidote to overconfidence. If the market prices a move at 50% five weeks out, the question "
         "is how often such pricing was followed by a move. It also measures how often the Fed did something the "
         "market priced at 0%, which is why no outcome should ever be given exactly 0%.",
         "Planned: tables from past meetings; a surprise floor derived from them. Not computed yet.",
         [], ["calendar"]),
    ]
    infl_what = ("How far realised core PCE inflation is above or below the Fed's 2% goal, with 3- and 6-month "
                 "windows showing which way it is heading.")
    infl_why = ("It is realised inflation against the mandate, not a forecast against another forecast. The Fed's "
                "reaction function (the Taylor principle) says the policy rate should rise more than one-for-one "
                "when inflation is above target, so a positive gap argues for restrictive policy: hold or hike. A "
                "closing gap is what permits cuts. On its own the gap says nothing about this meeting; it has to be "
                "read against where the rate already is. If the current rate is already above what the rule implies "
                "for this gap, the gap argues for holding, not hiking. That reading is the Taylor rule's job. "
                "Market-expected inflation (breakevens) is a different thing and lives under market data.")
    if infl:
        rows = [["Core PCE, 12-month (anchor)", f"{infl['anchor_12m']:.2f}% → gap to 2% goal {infl['gap_pp']:+.2f} pp"],
                ["Momentum: 3-month annualised", f"{infl['momentum']['3m']:.2f}%"],
                ["Momentum: 6-month annualised", f"{infl['momentum']['6m']:.2f}%"],
                ["Core PCE data through", infl["pce_through"]],
                ["Core CPI, 12-month / 3-month",
                 f"{infl['cpi']['12m']:.2f}% / {infl['cpi']['3m']:.2f}% (through {infl['cpi']['through']})"]]
        if infl["nowcast"]:
            nc = infl["nowcast"]
            rows.append([f"Nowcast to {nc['month']}", f"{nc['anchor_12m']:.2f}% → gap {nc['gap_pp']:+.2f} pp "
                                                       f"({nc['method']})"])
        rows.append(["Reading", inflation.direction(infl)])
        nodes.append(_node(
            "sig.inflation", 1, "Inflation gap", f"gap {infl['gap_pp']:+.2f} pp", "signal", "computed",
            what=infl_what, why=infl_why,
            how="Computed from the snapshot by fedcast/signals/inflation.py: 12-month core PCE is the anchor, 3- and "
                "6-month annualised rates are momentum, and because PCE lags CPI by a month the latest core-CPI "
                "monthly change carries PCE forward as a labelled nowcast. It does not feed a live model yet: the "
                "Taylor rule, next to be built, will read it. So it is not in today's number.",
            rows=rows, evidence=infl["evidence"]))
        link("fred.Inflation data", "sig.inflation", "computed")
    else:
        nodes.append(_node("sig.inflation", 1, "Inflation gap", "planned", "signal", "planned", what=infl_what,
                           why=infl_why, how="Needs core PCE and core CPI in the snapshot."))
        link("fred.Inflation data", "sig.inflation", "planned")

    for sid, label, what, why, how, rows, srcs in planned_signals:
        nodes.append(_node(sid, 1, label, "planned", "signal", "planned", what=what, why=why, how=how,
                           rows=rows, today=""))
        for s in srcs:
            link(s, sid, "planned")

    # --- column 2: models ----------------------------------------------------------------
    nodes.append(_node(
        "model.market", 2, "Market-implied", _top(m["probabilities"]), "model", "live",
        what="The futures-implied probability of each outcome.",
        why="The market's expectation is the anchor every other model is read against.",
        how=f"The Fed moves in 25 bp steps, so an expected change of {m['expected_change_bp']:+.1f} bp "
            f"({m['expected_change_bp'] / 25:+.2f} of a step) is shared between the two nearest outcomes. This is "
            "an interpolation, not a calibrated probability: it leaves the other outcomes at exactly 0%, which "
            "the planned surprise floor will correct.",
        rows=[["Distribution", _dist(m["probabilities"])], ["Method", m["method"]]], evidence=m["evidence"]))
    link("sig.change", "model.market")

    planned_models = [
        ("model.taylor", "Taylor rule",
         "A formula for where the policy rate 'should' be given the inflation gap and labour slack.",
         "The Fed does not follow it mechanically, but its decisions have tracked it for thirty years, and the "
         "distance between the rule rate and the actual rate is the pressure to move. Worked today: neutral real "
         "rate 1.0 + inflation 3.34 + 0.5 × gap 1.34 + 0.5 × output gap ≈ 5.1%; with the usual policy inertia "
         "(85% of today's rate, 15% of the rule) ≈ 4.06%, i.e. about +18 bp, leaning hike. Using 3-month "
         "inflation instead gives about +12 bp.",
         "Inertial rule with ranges for the unknowable inputs (neutral rate, sustainable unemployment), turned into "
         "outcome probabilities through a spread rather than a point. Not built yet; weight 0 in the pool.",
         ["sig.inflation", "sig.labour", "sig.rate_before"]),
        ("model.probit", "Ordered probit",
         "A statistical model of past decisions as a function of the signals.",
         "It lets the data say how the Fed actually weighted inflation, slack and market pricing, rather than "
         "assuming the weights.",
         "Fitted on roughly 250 meetings since 1994 using data as first published; features and procedure "
         "pre-registered before fitting; evaluated by log score on a held-out window. Not built yet.",
         ["sig.inflation", "sig.labour", "sig.financial"]),
        ("model.base", "Historical base rates",
         "Outcome frequencies in comparable situations.",
         "Keeps every model honest about surprises.",
         "Tables from past meetings. Not built yet.",
         ["sig.history"]),
        ("model.llm", "LLM analysts",
         "Specialist analysts (inflation, labour, financial conditions, communications), a hawk-versus-dove "
         "debate and an independent verifier, run on Claude.",
         "Reading text and weighing arguments is what the quant models cannot do; the harness keeps that reading "
         "honest.",
         "Every claim must quote a snapshot item and the verifier string-matches the quote; every watch-out must "
         "be addressed; the output is a bounded, cited tilt, never the final number. Not built yet.",
         ["sig.tone", "sig.inflation", "sig.labour", "watchouts", "documents"]),
    ]
    for mid, label, what, why, how, srcs in planned_models:
        nodes.append(_node(mid, 2, label, "planned", "model", "planned", what=what, why=why, how=how))
        for s in srcs:
            link(s, mid, "planned")

    # --- columns 3-5: pool, human input, forecast ------------------------------------------
    weights = fc["pool_weights"]
    nodes.append(_node(
        "pool", 3, "Pool (machine only)", _top(fc["machine_only"]), "pool", "live",
        what="The combined machine forecast.",
        why="One number has to come out, and it must be produced by code so it can be replayed and audited.",
        how="Weighted average of every live model with fixed, recorded weights. "
            + ("Only one model is live, so the pool equals it." if len(weights) == 1 else "")
            + " Planned: the market-implied model as anchor, the others as bounded adjustments.",
        rows=[[name, f"weight {w:g}"] for name, w in weights.items()] + [["machine_only", _dist(fc["machine_only"])]]))
    link("model.market", "pool")
    for mid, *_ in planned_models:
        link(mid, "pool", "planned")

    views = fc["human"]["views_applied"]
    budget = fc["human"]["net_budget"]
    nodes.append(_node(
        "views", 4, "Your views", f"{len(views)} active, tilt {budget * 100:+.0f} pp", "human", "live",
        what="Your directional opinions, each with a strength, a reason and an expiry.",
        why="Judgement belongs in the system, but through a channel that can be bounded, replayed and scored.",
        how="Each active view adds a signed tilt (3, 6 or 10 pp by strength), netted and capped at 10 pp. Code "
            "shifts exactly that much probability, keeps the machine forecast's shape, and never adds weight to an "
            "outcome the machine gave 0%. Rewording a rationale cannot change the number.",
        rows=[[v["id"], f"{v['direction']}, strength {v['strength']}: {v['rationale']}"] for v in views]
             + [["Net tilt", f"{budget * 100:+.0f} pp"]]))
    link("pool", "views")

    nodes.append(_node(
        "out", 5, "Forecast", _top(fc["human_adjusted"]), "output", "live",
        what=f"The recorded forecast for the {fc['meeting']} decision, ledger entry #{entry['seq']}.",
        why="Both tracks are published so the value of human input can be seen, never hidden.",
        how="Appended to the hash-chained ledger with the snapshot, code and scorecard versions it was made under.",
        rows=[["machine_only", _dist(fc["machine_only"])], ["human_adjusted", _dist(fc["human_adjusted"])],
              ["Snapshot", fc["snapshot_hash"][:12]], ["Code version", entry["code_version"]],
              ["Entry fingerprint", entry["entry_hash"]]]))
    link("views", "out")

    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["from"] in ids and e["to"] in ids]
    return {"columns": list(COLUMNS), "nodes": nodes, "edges": edges}
