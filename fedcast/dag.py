"""Factor graph behind one ledger entry: what feeds what, with the values actually used.

Built from the ledger entry and its snapshot only. Node status: `live` is in the number; `computed`
is calculated from the snapshot but not yet in the number; `idle` is in the snapshot but nothing reads
it; `planned` is not built. The graph therefore never implies an influence that is not in the number.

Each node carries three explanations: `what` it is, `why` it bears on the decision, and `how` it is
(or will be) computed, so the page can teach as well as show.
"""

from __future__ import annotations

from fedcast import OUTCOMES_BP, config
from fedcast.journey import _dist, _label
from fedcast.signals import base_rates, comms, financial, inflation, labour, sep
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

_INFL_WHAT = ("How far realised core PCE inflation is above or below the Fed's 2% goal, with 3- and 6-month "
              "windows showing which way it is heading.")
_INFL_WHY = ("It is realised inflation against the mandate, not a forecast against another forecast. The Fed's "
             "reaction function (the Taylor principle) says the policy rate should rise more than one-for-one "
             "when inflation is above target, so a positive gap argues for restrictive policy: hold or hike. A "
             "closing gap is what permits cuts. On its own the gap says nothing about this meeting; it has to be "
             "read against where the rate already is. If the current rate is already above what the rule implies "
             "for this gap, the gap argues for holding, not hiking. That reading is the Taylor rule's job. "
             "Market-expected inflation (breakevens) is a different thing and lives under market data.")
_LAB_WHAT = ("How much spare capacity the labour market has: unemployment against its sustainable level, payroll "
             "growth against the pace needed to absorb new workers, claims against their trend.")
_LAB_WHY = ("Rising slack is the second mandate calling for easier policy, and it can override inflation that is "
            "still above target, as in 2024. A tight market removes that pressure and lets inflation dominate. The "
            "Sahm rule (3-month average unemployment half a point above its 12-month low) is the classic recession "
            "trigger. In the Taylor rules the unemployment gap enters with a coefficient of 1 or 2, so a tenth of a "
            "point of slack is worth 10 to 20 bp of rule rate.")
_TAY_WHAT = ("A family of formulas for where the policy rate 'should' be given the inflation gap and labour slack: "
             "the four rules the Fed itself reports in its Monetary Policy Report (Taylor 1993, balanced approach, "
             "balanced approach with shortfalls, and the first-difference rule).")
_TAY_WHY = ("The Fed does not follow any rule mechanically, but its decisions have tracked this family for thirty "
            "years, and the distance between the rule rate and the actual rate is the pressure to move. Reporting "
            "several variants shows how much the answer depends on the rule chosen, which is itself information.")


def _p(probs: dict, outcome: int) -> float:
    return float(probs.get(str(outcome), probs.get(outcome, 0.0)))


def _top(probs: dict) -> str:
    best = max(OUTCOMES_BP, key=lambda o: _p(probs, o))
    return f"{_label(best)} {_p(probs, best) * 100:.0f}%"


def _node(id: str, col: int, label: str, summary: str, kind: str, status: str, what: str,
          why: str = "", how: str = "", rows: list | None = None, evidence: list | None = None) -> dict:
    return {"id": id, "col": col, "label": label, "summary": summary, "kind": kind, "status": status,
            "detail": {"body": what, "why": why, "how": how, "rows": rows or [], "evidence": evidence or []}}


def _try(fn, snap: Snapshot):
    try:
        return fn(snap)
    except (ValueError, KeyError):
        return None


def build(entry: dict, snap: Snapshot, watchlist: list[dict] | None = None,
          analyses: dict | None = None) -> dict:
    fc = entry["forecast"]
    m = fc["models"]["market_implied"]
    tr = fc["models"].get("taylor_rule")
    nodes: list[dict] = []
    edges: list[dict] = []

    def link(a: str, b: str, status: str = "live") -> None:
        edges.append({"from": a, "to": b, "status": status})

    def has(item_id: str) -> bool:
        return item_id in snap.items

    infl = _try(inflation.compute, snap) if has("fred.PCEPILFE") and has("fred.CPILFESL") else None
    lab = _try(labour.compute, snap) if all(has(e) for e in labour.EVIDENCE) else None
    fin = _try(financial.compute, snap) if all(has(e) for e in financial.EVIDENCE) else None
    tone = _try(comms.compute, snap)
    hist = _try(base_rates.compute, snap) if all(has(e) for e in base_rates.EVIDENCE) else None
    sepsig = _try(sep.compute, snap)
    sig_status = "live" if tr else "computed"  # the signals are in the number once the Taylor rule runs

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
        months = ", ".join(snap.get(i)["contract_month"] for i in others)
        nodes.append(_node(
            "futures.other", 0, "Adjacent contracts", f"{len(others)} months, unused", "source", "idle",
            what=f"The neighbouring months of the same CME fed-funds futures contract ({months}); the forecast reads "
                 f"{contract['contract_month']}. These are not prediction markets: Polymarket or Kalshi contracts on "
                 "the Fed decision are a genuinely different source, worth adding later as their own evidence item, "
                 "with the caveat that they are thin and fee-distorted compared with the futures.",
            why="They let the chosen contract be cross-checked: the meeting-month contract implies the same move by "
                "a noisier route, and the contract two months out shows what is priced for the meeting after.",
            how="Not read by any model yet.",
            rows=[[i.split(".")[1], f"price {snap.get(i)['price']} (implies {100 - snap.get(i)['price']:.3f}%)"]
                  for i in others],
            evidence=others))

    group_signal = {"Inflation data": infl, "Labour data": lab, "Market data": fin}
    for label, series in FRED_GROUPS.items():
        rows, ids = [], []
        for sid in series:
            iid = f"fred.{sid}"
            if not has(iid):
                continue
            latest = next((o for o in snap.get(iid)["observations"] if o["value"] is not None), None)
            rows.append([f"{sid}: {config.FRED_SERIES[sid]}",
                         f"{latest['value']:g} ({latest['date']})" if latest else "no data"])
            ids.append(iid)
        if ids:
            what, why, how = _GROUP_TEXT[label]
            used = group_signal.get(label) is not None
            status = ("computed" if label == "Market data" else sig_status) if used else "idle"
            reader = {"Inflation data": "inflation gap", "Labour data": "labour slack",
                      "Market data": "financial conditions"}.get(label, "")
            nodes.append(_node(
                f"fred.{label}", 0, label, f"{len(ids)} series, {'read by ' + reader if used else 'not yet used'}",
                "source", status, what=what, why=why,
                how=how + (f" Read by the {reader} signal." if used else " Nothing reads this yet."),
                rows=rows, evidence=ids))

    for d in sorted(i for i in snap.items if i.startswith("fed.")):
        text = snap.get(d)["text"]
        kind = "statement" if ".statement." in d else "minutes" if ".minutes." in d else "press conference"
        if kind == "press conference":
            why = ("The Chair's prepared remarks and answers to reporters are the most candid official guidance: how the "
                   "committee weighs the risks, what would make it move, and what it declines to pre-commit to.")
            how = "Planned: the communications analyst reads the transcript and must quote it."
        elif kind == "statement":
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
        read = kind == "statement" and tone is not None and d in tone["evidence"]
        rows = [["Opens with", text[:320].strip() + "…"]]
        if read:
            v = comms.vote(text)
            rows.insert(0, ["Vote", f"{v['for']} – {v['against']}" + (f", against: {v['dissenters']}" if v["dissenters"] else "")])
        nodes.append(_node(
            d, 0, f"Fed {kind} {d[-10:]}", f"{len(text.split())} words, {'read by tone' if read else 'not yet used'}",
            "source", "computed" if read else "idle",
            what=f"The full text of the FOMC {kind}, frozen as published.", why=why,
            how=how + (" Read by the communication-tone signal." if read else " No model reads it yet."),
            rows=rows, evidence=[d]))

    sp = snap.get("fed.speeches") if has("fed.speeches") else None
    if sp:
        nodes.append(_node(
            "fed.speeches", 0, "Fed speeches", f"{len(sp['speeches'])} since {sp['since']}", "source", "idle",
            what=f"Speeches by Board members since the last decision ({sp['since']}), from the Fed's own feed, as text.",
            why="Between meetings this is where the signal moves: officials use speeches to prepare markets for the next "
                "decision, and the balance of hawkish and dovish voices shifts before the statement does.",
            how="Each speech is frozen as text. Planned: the communications analyst reads the ones on the economy and "
                "policy and must quote them; regulatory speeches are listed but carry no policy signal. No model reads "
                "them yet.",
            rows=[[s_["date"], f"{s_['speaker']}: {s_['title']}"] for s_ in sp["speeches"]],
            evidence=["fed.speeches"]))

    sep_ids = sorted(i for i in snap.items if i.startswith("fed.sep."))
    if sep_ids:
        sd = snap.get(sep_ids[-1])
        ffr = sd["medians"].get("Federal funds rate", {})
        nodes.append(_node(
            sep_ids[-1], 0, f"Projections (SEP) {sep_ids[-1][-10:]}", "medians, read by projections", "source",
            "computed" if sepsig else "idle",
            what="The Summary of Economic Projections published with quarterly meetings: each participant's projection "
                 "for growth, unemployment, inflation and the appropriate federal funds rate at each year-end; the table "
                 "gives the median and the range, and the previous SEP's medians for comparison.",
            why="It is the committee saying, in numbers, where it expects to take the rate. The 'dot plot' median is the "
                "closest thing to official forward guidance, and its revision from the previous quarter shows which way "
                "the committee has moved.",
            how="Parsed from the Fed's projections table by code. Read by the committee-projections signal.",
            rows=[[f"Fed funds rate median, {y}", f"{v:.1f}%" + (f" (previous {sd['previous']['Federal funds rate'][y]:.1f}%)"
                   if y in sd["previous"].get("Federal funds rate", {}) else "")] for y, v in ffr.items()]
                 + [[f"{var} median, {sd['years'][0]}", f"{vals[sd['years'][0]]:.1f}"] for var, vals in sd["medians"].items()
                    if var != "Federal funds rate" and sd["years"][0] in vals],
            evidence=[sep_ids[-1]]))

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
             "tagged human-sourced. The verbatim text is what is stored as the source; a summary made from it "
             "may be stored too, typed as derived, naming the model and prompt that made it and pointing back here.",
        why="Analysts you trust, or your own reading, may know things the data feeds cannot show. Entering that "
            "as evidence keeps it visible and quotable rather than letting it move the number silently.",
        how="Only the LLM analysts will read these, quoting them like any other item; the quant models never see "
            "them and they never move the number directly. Enter a view if you want the number to move.",
        rows=[[snap.get(d)["id"], f"{snap.get(d)['title']} ({snap.get(d)['relevance']})"] for d in docs],
        evidence=docs))

    pm_items = sorted(i for i in snap.items if i.startswith("human.pm."))
    pmm = fc["models"].get("prediction_market")
    nodes.append(_node(
        "pm", 0, "Prediction-market odds", f"{len(pm_items)} entr{'y' if len(pm_items) == 1 else 'ies'}" if pm_items else "none entered",
        "human", "live" if pmm else ("idle" if pm_items else "planned"),
        what="Odds for this meeting as shown on Polymarket or Kalshi, typed in by you with the time you saw them, the "
             "URL and the volume. Recorded exactly as the site showed them; they rarely sum to 100 because of spreads.",
        why="A second crowd answering the same question with money at stake, independent of the futures market. Thin "
            "and fee-distorted by comparison, which is why it carries a small weight, but it can disagree with the "
            "futures in informative ways.",
        how="Frozen into the snapshot as a typed item. The prediction-market model normalises the most recent entry "
            "for the next meeting. Entered by hand because these venues block scripts and reword contracts each meeting.",
        rows=[[snap.get(i)["id"], f"{snap.get(i)['venue']} at {snap.get(i)['observed_at'].replace('T', ' ')}: "
                                   + ", ".join(f"{_label(int(k))} {v:g}%" for k, v in snap.get(i)["prices"].items())]
              for i in pm_items],
        evidence=pm_items))

    if has("history.meetings") and has("history.target_rate"):
        hm, ht = snap.get("history.meetings")["meetings"], snap.get("history.target_rate")["changes"]
        nodes.append(_node(
            "history", 0, "Decision history", f"{len(hm)} meetings, {len(ht)} rate changes", "source",
            "computed" if hist else "idle",
            what="Every FOMC meeting date since 1994 (from the Fed's per-year history pages) and every change in the "
                 "policy target since 1990 (FRED series DFEDTAR, then the upper bound DFEDTARU from December 2008).",
            why="It is the record of what the committee actually did, which is what base rates are measured from.",
            how="Meeting dates are parsed from the history pages; the daily target series is collapsed to the days it "
                "changed. Both are frozen in the snapshot like any other item.",
            rows=[["Meetings", f"{hm[0]['date']} to {hm[-1]['date']}"], ["Target changes", f"{ht[0]['date']} to {ht[-1]['date']}"],
                  ["Latest target (upper bound)", f"{ht[-1]['target']:.2f}% since {ht[-1]['date']}"]],
            evidence=["history.meetings", "history.target_rate"]))

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

    if infl:
        rows = [["Core PCE, 12-month (anchor)", f"{infl['anchor_12m']:.2f}% → gap to 2% goal {infl['gap_pp']:+.2f} pp"],
                ["Momentum: 3-month annualised", f"{infl['momentum']['3m']:.2f}%"],
                ["Momentum: 6-month annualised", f"{infl['momentum']['6m']:.2f}%"],
                ["Core PCE data through", infl["pce_through"]],
                ["Core CPI, 12-month / 3-month",
                 f"{infl['cpi']['12m']:.2f}% / {infl['cpi']['3m']:.2f}% (through {infl['cpi']['through']})"]]
        if infl["nowcast"]:
            nc = infl["nowcast"]
            rows.append([f"Nowcast to {nc['month']}", f"{nc['anchor_12m']:.2f}% → gap {nc['gap_pp']:+.2f} pp ({nc['method']})"])
        rows.append(["Reading", inflation.direction(infl)])
        nodes.append(_node(
            "sig.inflation", 1, "Inflation gap", f"gap {infl['gap_pp']:+.2f} pp", "signal", sig_status,
            what=_INFL_WHAT, why=_INFL_WHY,
            how="Computed from the snapshot by fedcast/signals/inflation.py: 12-month core PCE is the anchor, 3- and "
                "6-month annualised rates are momentum, and because PCE lags CPI by a month the latest core-CPI "
                "monthly change carries PCE forward as a labelled nowcast. "
                + ("The 12-month anchor feeds the Taylor rule, so it is in today's number."
                   if tr else "It does not feed a live model yet, so it is not in today's number."),
            rows=rows, evidence=infl["evidence"]))
        link("fred.Inflation data", "sig.inflation", sig_status)
    else:
        nodes.append(_node("sig.inflation", 1, "Inflation gap", "planned", "signal", "planned", what=_INFL_WHAT,
                           why=_INFL_WHY, how="Needs core PCE and core CPI in the snapshot."))
        link("fred.Inflation data", "sig.inflation", "planned")

    if lab:
        rows = [["Unemployment", f"{lab['unemployment']:.1f}% (a year ago {lab['unemployment_year_ago']:.1f}%)"],
                ["Gap to sustainable level", f"{lab['unemployment']:.1f} − {lab['u_star']:.1f} = {lab['gap_pp']:+.2f} pp"
                                             + (" (slack)" if lab["gap_pp"] > 0 else " (tight)" if lab["gap_pp"] < 0 else "")],
                ["Sahm indicator", f"{lab['sahm']:.2f} (trigger 0.50)"],
                ["Payrolls, 3-month average", f"{lab['payrolls_3m_avg_k']:+.0f}k/month vs {lab['breakeven_payrolls_k']:.0f}k breakeven"
                                              f" (12-month {lab['payrolls_12m_avg_k']:+.0f}k)"],
                ["Initial claims, 4-week average", f"{lab['claims_4wk_k']:.0f}k vs 26-week {lab['claims_26wk_k']:.0f}k"],
                ["Data through", f"unemployment {lab['through']['unemployment']}, claims {lab['through']['claims']}"],
                ["Reading", labour.direction(lab)]]
        nodes.append(_node(
            "sig.labour", 1, "Labour slack", f"gap {lab['gap_pp']:+.2f} pp", "signal", sig_status,
            what=_LAB_WHAT, why=_LAB_WHY,
            how="Computed from the snapshot by fedcast/signals/labour.py with a 4.2% sustainable unemployment "
                "assumption and a 75k/month breakeven payroll pace, both pre-registered. "
                + ("The unemployment level and its year-ago value feed the Taylor rules, so it is in today's number."
                   if tr else "It does not feed a live model yet."),
            rows=rows, evidence=lab["evidence"]))
        link("fred.Labour data", "sig.labour", sig_status)
    else:
        nodes.append(_node("sig.labour", 1, "Labour slack", "planned", "signal", "planned", what=_LAB_WHAT,
                           why=_LAB_WHY, how="Needs unemployment, payrolls and claims in the snapshot."))
        link("fred.Labour data", "sig.labour", "planned")

    fin_what = "What the bond market expects and how tight financial conditions are."
    fin_why = ("The 2-year yield is close to the average policy rate expected over two years, so a wide positive gap to "
               "today's rate means the market expects more hikes, which corroborates or contradicts the futures. "
               "Breakevens show whether inflation expectations stay anchored near 2%, which the Fed treats as a "
               "precondition for easing. A loose NFCI despite high rates tells the Fed its tightening is not biting.")
    if fin:
        t2, be, nf = fin["two_year"], fin["breakeven"], fin["nfci"]
        rows = [["2-year yield minus policy rate", f"{t2['yield']:.2f}% − {fin['policy_rate']:.2f}% = {t2['gap_bp']:+.0f} bp ({t2['date']})"],
                ["2-year yield, 4-week change", f"{t2['change_4wk_bp']:+.0f} bp since {t2['ago_date']}"],
                ["5-year breakeven inflation", f"{be['level']:.2f}% ({be['vs_goal_pp']:+.2f} pp vs 2% goal; 4-week change {be['change_4wk_pp']:+.2f})"],
                ["Chicago Fed NFCI", f"{nf['level']:+.2f} ({nf['date']}; 0 = average, negative = loose; 4-week change {nf['change_4wk']:+.2f})"],
                ["Reading", financial.direction(fin)]]
        nodes.append(_node("sig.financial", 1, "Financial conditions", f"2y gap {t2['gap_bp']:+.0f} bp", "signal", "computed",
                           what=fin_what, why=fin_why,
                           how="Computed from the snapshot by fedcast/signals/financial.py: the 2-year gap in bp, the "
                               "breakeven against the goal, the NFCI level, each with a 4-week change. It does not feed "
                               "a live model yet (the ordered probit and the analysts will read it), so it is not in "
                               "today's number.", rows=rows, evidence=fin["evidence"]))
        link("fred.Market data", "sig.financial", "computed")
        link("effr", "sig.financial", "computed")
    else:
        nodes.append(_node("sig.financial", 1, "Financial conditions", "planned", "signal", "planned", what=fin_what,
                           why=fin_why, how="Needs the 2-year yield, breakevens and NFCI in the snapshot."))
        link("fred.Market data", "sig.financial", "planned")

    tone_what = ("A hawkish-to-dovish reading of what the committee has said, concentrating on the vote and on what "
                 "changed since the previous statement.")
    tone_why = ("The Fed telegraphs. Wording changes in the statement, the balance of views in the minutes and the "
                "Chair's press-conference answers move markets precisely because they precede decisions. The vote "
                "shows how united the committee is, and dissents show which way the pressure runs.")
    if tone:
        v, lx = tone["vote"], tone["lexicon"]
        rows = [["Latest statement", tone["latest"]],
                ["Vote", f"{v['for']} – {v['against']}" + (f", against: {v['dissenters']}" if v["dissenters"] else "")],
                ["Lexicon score", f"{lx['score']:+.2f} (hawkish terms {sum(lx['hawkish'].values())}, dovish {sum(lx['dovish'].values())})"],
                ["Hawkish terms found", ", ".join(f"{k} ×{n}" for k, n in lx["hawkish"].items()) or "none"],
                ["Dovish terms found", ", ".join(f"{k} ×{n}" for k, n in lx["dovish"].items()) or "none"]]
        if tone["diff"]:
            d_ = tone["diff"]
            rows += [["Compared with", tone["previous"] + f" (similarity {d_['similarity']:.0%})"],
                     ["Phrases added", " | ".join(d_["added"][:8]) or "none"],
                     ["Phrases removed", " | ".join(d_["removed"][:8]) or "none"]]
        else:
            rows.append(["Compared with", "previous statement not in this snapshot yet: take a new snapshot to get the diff"])
        rows.append(["Reading", comms.direction(tone)])
        nodes.append(_node("sig.tone", 1, "Communication tone", comms.direction(tone).split(",")[0], "signal", "computed",
                           what=tone_what, why=tone_why,
                           how="Deterministic baseline from fedcast/signals/comms.py: the vote parsed from the statement, "
                               "a word-level diff against the previous statement (boilerplate stripped), and a lexicon "
                               "score from counts of hawkish and dovish terms. Crude by design: it is the floor the LLM "
                               "communications analyst must beat and the check it is held against. Not in today's number.",
                           rows=rows, evidence=tone["evidence"]))
        for e in tone["evidence"]:
            link(e, "sig.tone", "computed")
    else:
        nodes.append(_node("sig.tone", 1, "Communication tone", "planned", "signal", "planned", what=tone_what,
                           why=tone_why, how="Needs a statement in the snapshot."))

    planned_signals = [
    ]
    for sid, label, what, why, how, rows, srcs in planned_signals:
        nodes.append(_node(sid, 1, label, "planned", "signal", "planned", what=what, why=why, how=how, rows=rows))
        for s in srcs:
            link(s, sid, "planned")

    sep_what = ("What the committee's own median projection implies for the rest of the year: the number of 25 bp moves "
                "between today's target midpoint and the median year-end rate, spread over the meetings still to come.")
    sep_why = ("It is the committee telling you its plan. A median above the current rate means more hikes are pencilled "
               "in; the revision from the previous SEP shows whether the plan moved. It is a plan, not a promise: the "
               "committee revises it every quarter, and the data between SEPs decide which way.")
    if sepsig:
        g = sepsig
        rows = [["Median fed funds rate, end-" + g["year"], f"{g['median_end_year']:.1f}%" + (f" (previous SEP {g['previous_median']:.1f}%, revision {g['revision_pp']:+.1f} pp)" if g["previous_median"] is not None else "")],
                ["Current target midpoint", f"{g['current_midpoint']:.3f}%"],
                ["Implied change by year-end", f"{g['implied_change_bp']:+.1f} bp ≈ {g['implied_moves']:+.1f} moves of 25 bp"],
                ["Meetings left this year", ", ".join(g["remaining_meetings"]) or "none"],
                ["Average per remaining meeting", f"{g['per_meeting_bp']:+.1f} bp" if g["per_meeting_bp"] is not None else "n/a"],
                ["Median path", ", ".join(f"{y}: {v:.1f}%" for y, v in g["path"].items())],
                ["Reading", sep.direction(g)]]
        nodes.append(_node("sig.sep", 1, "Committee projections", f"{g['implied_moves']:+.1f} moves by year-end", "signal", "computed",
                           what=sep_what, why=sep_why,
                           how="Computed from the snapshot by fedcast/signals/sep.py. Not in today's number yet: the next "
                               "amendment can give it a pool weight, or the ordered probit can take it as a feature.",
                           rows=rows, evidence=g["evidence"]))
        link(g["sep_item"], "sig.sep", "computed")
        link("effr", "sig.sep", "computed")
    else:
        nodes.append(_node("sig.sep", 1, "Committee projections", "planned", "signal", "planned", what=sep_what,
                           why=sep_why, how="Needs a projections table in the snapshot (quarterly meetings)."))

    hist_what = "How often, since 1994, the Fed has cut, held or hiked at scheduled meetings, and what it did next."
    hist_why = ("It is the antidote to overconfidence. The conditional table (what followed a hike, a hold, a cut) is "
                "the Fed's revealed tendency to continue, pause or reverse, and the frequency of 50 bp moves and "
                "reversals is the evidence behind the surprise floor. What it cannot say is how often the market was "
                "surprised; that needs historical futures prices.")
    if hist:
        g, o, c = hist["given_last"], hist["overall"], hist["conditional"]
        rows = [["Scheduled decisions", f"{hist['scheduled_decisions']} from {hist['since']} to {hist['through']}"],
                ["Overall", f"cut {o['cut']:.0%}, hold {o['hold']:.0%}, hike {o['hike']:.0%}"],
                ["Last decision", f"{hist['last_decision']['decision']} of {hist['last_decision']['change_bp']:+.0f} bp on {hist['last_decision']['date']}"],
                [f"Next decision after a {hist['last_decision']['decision']} (n = {hist['given_last_n']})",
                 f"cut {g['cut']:.0%}, hold {g['hold']:.0%}, hike {g['hike']:.0%}"],
                ["After a hike", f"cut {c['hike']['cut']:.0%}, hold {c['hike']['hold']:.0%}, hike {c['hike']['hike']:.0%}"],
                ["After a hold", f"cut {c['hold']['cut']:.0%}, hold {c['hold']['hold']:.0%}, hike {c['hold']['hike']:.0%}"],
                ["After a cut", f"cut {c['cut']['cut']:.0%}, hold {c['cut']['hold']:.0%}, hike {c['cut']['hike']:.0%}"],
                ["Moves of 50 bp or more", f"{hist['moves_50bp_or_more']} of {hist['moves']} moves ({hist['share_of_moves_50bp_or_more']:.0%})"],
                ["Direct reversals (cut after hike or hike after cut)", str(hist["reversals"])],
                ["Intermeeting moves", f"{hist['intermeeting_moves']} since 1994; since 2000: "
                                        + (", ".join(f"{m['date']} ({m['change_bp']:+.0f})" for m in hist["intermeeting_recent"]) or "none")],
                ["Reading", base_rates.direction(hist)]]
        nodes.append(_node("sig.history", 1, "Base rates", base_rates.direction(hist).split(",")[0], "signal", "computed",
                           what=hist_what, why=hist_why,
                           how="Computed from the snapshot by fedcast/signals/base_rates.py: each scheduled meeting's "
                               "decision is the change in the target from the day before to the day after; the "
                               "conditional table pairs each decision with the next. Not in today's number yet: it "
                               "will become the historical base-rate model and replace the interim surprise floor.",
                           rows=rows, evidence=hist["evidence"]))
        link("history", "sig.history", "computed")
    else:
        nodes.append(_node("sig.history", 1, "Base rates", "planned", "signal", "planned", what=hist_what, why=hist_why,
                           how="Needs the decision history in the snapshot: take a new snapshot."))
        if has("history.meetings"):
            link("history", "sig.history", "planned")

    # --- column 2: models ----------------------------------------------------------------
    nodes.append(_node(
        "model.market", 2, "Market-implied", _top(m["probabilities"]), "model", "live",
        what="The futures-implied probability of each outcome.",
        why="The market's expectation is the anchor every other model is read against.",
        how=f"The Fed moves in 25 bp steps, so an expected change of {m['expected_change_bp']:+.1f} bp "
            f"({m['expected_change_bp'] / 25:+.2f} of a step) is shared between the two nearest outcomes. This is "
            "an interpolation, not a calibrated probability; the pool's surprise floor keeps the other outcomes "
            "above 0%.",
        rows=[["Distribution", _dist(m["probabilities"])], ["Method", m["method"]]], evidence=m["evidence"]))
    link("sig.change", "model.market")

    if tr:
        rows = [["Inputs", f"inflation {tr['inputs']['inflation_12m']:.2f}%, unemployment {tr['inputs']['unemployment']:.1f}% "
                           f"(year ago {tr['inputs']['unemployment_year_ago']:.1f}%), rate {tr['rate_before']:.2f}%"]]
        rows += [[f"{v} rule, prescribed change", f"{bp:+.1f} bp"] for v, bp in tr["by_variant_bp"].items()]
        rows += [["All variants × parameter grid", f"mean {tr['expected_change_bp']:+.1f} bp, spread {tr['spread_bp']:.0f} bp, "
                                                   f"σ {tr['sigma_bp']:.0f} bp"],
                 ["Distribution", _dist(tr["probabilities"])]]
        nodes.append(_node(
            "model.taylor", 2, "Taylor-rule family", _top(tr["probabilities"]), "model", "live",
            what=_TAY_WHAT, why=_TAY_WHY,
            how="Each level rule gives a rule rate; the prescribed change for one meeting is 15% of the distance to "
                "it (partial adjustment, ρ = 0.85). The first-difference rule gives a change directly, halved from a "
                "quarter to a meeting. All four run over a grid of neutral real rates (0.5, 1.0, 1.5%) and "
                "sustainable unemployment (4.0, 4.2, 4.4%). The mean prescription and its spread, plus a 15 bp floor, "
                "define a normal distribution whose mass in each 25 bp bucket is the model's probability.",
            rows=rows, evidence=tr["evidence"]))
        for s in ("sig.inflation", "sig.labour", "sig.rate_before"):
            link(s, "model.taylor")
    else:
        nodes.append(_node(
            "model.taylor", 2, "Taylor-rule family", "not run", "model", "planned", what=_TAY_WHAT, why=_TAY_WHY,
            how="Could not run on this snapshot: " + fc.get("models_skipped", {}).get("taylor_rule", "needs the inflation and labour signals.")))
        for s in ("sig.inflation", "sig.labour", "sig.rate_before"):
            link(s, "model.taylor", "planned")

    if pmm:
        nodes.append(_node(
            "model.pm", 2, "Prediction market", _top(pmm["probabilities"]), "model", "live",
            what="The hand-entered prediction-market odds, normalised to sum to 100%.",
            why="An independent read of the same question; small weight because the market is thin.",
            how=f"Latest entry ({pmm['venue']}, {pmm['observed_at'].replace('T', ' ')}) with raw prices summing to "
                f"{pmm['raw_total_pct']:g}%, divided through by that total.",
            rows=[["Raw prices", ", ".join(f"{_label(int(k))} {v:g}%" for k, v in pmm["raw_prices_pct"].items())],
                  ["Volume", f"${pmm['volume_usd']:,.0f}" if pmm.get("volume_usd") else "not recorded"],
                  ["Distribution", _dist(pmm["probabilities"])]],
            evidence=pmm["evidence"]))
        link("pm", "model.pm")
    else:
        nodes.append(_node("model.pm", 2, "Prediction market", "not run", "model", "planned",
                           what="The hand-entered prediction-market odds, normalised to sum to 100%.",
                           why="An independent read of the same question; small weight because the market is thin.",
                           how="Could not run: " + fc.get("models_skipped", {}).get("prediction_market", "no odds entered for this meeting.")))
        link("pm", "model.pm", "planned")

    planned_models = [
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
    ]
    for mid, label, what, why, how, srcs in planned_models:
        nodes.append(_node(mid, 2, label, "planned", "model", "planned", what=what, why=why, how=how))
        for s in srcs:
            link(s, mid, "planned")

    llm_what = ("Specialist analysts (communications first; inflation, labour and financial conditions to follow), "
                "a hawk-versus-dove debate and an independent verifier, run on Claude through the Claude Code CLI with "
                "all tools disabled, so the model can read nothing but the prompt.")
    llm_why = ("Reading text and weighing arguments is what the quant models cannot do; the harness keeps that reading "
               "honest: every claim must quote a snapshot item and the verifier string-matches the quote, numbers "
               "outside the quoted item count as leakage, every watch-out must be addressed by id, and the output is "
               "a bounded tilt in basis points, never the final number.")
    comm = (analyses or {}).get("communications")
    naive = (analyses or {}).get("naive")
    llm_srcs = ["sig.tone", "sig.inflation", "sig.labour", "sig.sep", "watchouts", "documents"]
    for d_ in sorted(i for i in snap.items if i.startswith("fed.presconf.")):
        link(d_, "sig.tone", "planned")
    if has("fed.speeches"):
        link("fed.speeches", "sig.tone", "planned")
    if comm:
        sm = comm["summary"]
        last = comm["runs"][-1]["verification"]
        rows = [["Runs on this snapshot", f"{sm['runs']} via {comm['backend']} ({comm['prompt_version']})"],
                ["Tilt (bounded ±10 bp)", f"mean {sm['tilt_mean_bp']:+.1f} bp" + (f", std {sm['tilt_std_bp']:.1f} bp (S1)" if sm["tilt_std_bp"] is not None else "")],
                ["Groundedness (S2)", f"{sm['groundedness_pct_mean']:.0f}% of claims quote-verified"],
                ["Leakage (S3)", f"{sm['leakage_total']} number(s) not in the quoted evidence"],
                ["Watch-outs (S10)", f"{sm['watchouts_missing_total']} missing"],
                ["Last run", f"{last['n_verified']}/{last['n_claims']} claims verified; "
                             + comm["runs"][-1]["completion"]["output"].get("summary", "")[:240]]]
        if naive:
            ns = naive["summary"]
            rows.append(["Naive control (arm A), same snapshot date",
                         f"{ns['runs']} run(s): " + ", ".join(f"{_label(int(k))} {v * 100:.0f}%" for k, v in ns["mean_probabilities"].items() if v >= 0.005)
                         + (f"; max std {ns['max_std_pp']:.1f} pp" if ns["max_std_pp"] is not None else "")
                         + f"; {ns['leakage_total']} numbers from memory, 0% groundedness"])
        nodes.append(_node("model.llm", 2, "LLM analysts", f"tilt {sm['tilt_mean_bp']:+.0f} bp, {sm['groundedness_pct_mean']:.0f}% grounded",
                           "model", "computed", what=llm_what, why=llm_why,
                           how="The communications analyst reads the statement diff, both statements, the minutes, your "
                               "documents and the watch-outs, and returns claims with verbatim quotes, a watch-out "
                               "report and a tilt. Code verifies every quote. Computed and scored; not in the number until "
                               "it passes the eval gate (S1-S3, S10 thresholds) and a weight is set by amendment.",
                           rows=rows))
        for s_ in llm_srcs:
            link(s_, "model.llm", "computed")
    else:
        nodes.append(_node("model.llm", 2, "LLM analysts", "not run yet", "model", "planned", what=llm_what, why=llm_why,
                           how="Run `fedcast analyse` (needs the claude CLI signed in). Not in today's number."))
        for s_ in llm_srcs:
            link(s_, "model.llm", "planned")
    link("model.llm", "pool", "planned")

    # --- columns 3-5: pool, human input, forecast ------------------------------------------
    weights = fc["pool_weights"]
    floor = fc.get("surprise_floor", 0.0)
    live_models = [n for n in weights if n in fc["models"]]
    nodes.append(_node(
        "pool", 3, "Pool (machine only)", _top(fc["machine_only"]), "pool", "live",
        what="The combined machine forecast.",
        why="One number has to come out, and it must be produced by code so it can be replayed and audited. The "
            "market is the anchor; the other models corroborate or dissent at smaller weights.",
        how=f"Weighted average of the live models with fixed, recorded weights, then no outcome is allowed below the "
            f"{floor * 100:.1f}% surprise floor and the result is renormalised. Models that could not run are dropped "
            "and the remaining weights rescaled.",
        rows=[[name, f"weight {w:g}" + ("" if name in live_models else " (not run)")] for name, w in weights.items()]
             + [["Surprise floor", f"{floor * 100:.1f}% per outcome"], ["machine_only", _dist(fc["machine_only"])]]))
    link("model.market", "pool")
    link("model.taylor", "pool", "live" if tr else "planned")
    link("model.pm", "pool", "live" if pmm else "planned")
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
