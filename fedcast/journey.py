"""Start-to-end account of how one ledger entry got its numbers.

Built only from the ledger entry and the snapshot it points to, so the explanation is
derived from the same evidence as the forecast and cannot drift from it.
"""

from __future__ import annotations

from collections import Counter

from fedcast import OUTCOMES_BP
from fedcast.snapshot import Snapshot

_KIND_LABEL = {"calendar": "FOMC calendar", "effr": "Effective fed funds rate", "futures": "Fed funds futures",
               "fred": "FRED macro series", "document": "Fed documents", "human_view": "Human views",
               "human_document": "Your documents", "history": "Decision history"}


def _label(outcome: int) -> str:
    return "hold" if outcome == 0 else f"{outcome:+d} bp"


def _dist(probs: dict) -> str:
    parts = [f"{_label(o)} {float(probs[str(o)] if str(o) in probs else probs[o]) * 100:.1f}%" for o in OUTCOMES_BP]
    return " · ".join(p for p in parts if not p.endswith(" 0.0%")) or "—"


def build(entry: dict, snap: Snapshot) -> list[dict]:
    fc = entry["forecast"]
    steps: list[dict] = []

    kinds = Counter(i.kind for i in snap.items.values())
    steps.append({
        "title": "Collect and freeze the evidence",
        "body": (f"On {snap.as_of.isoformat()} the app fetched {len(snap.items)} items and froze them as snapshot "
                 f"{snap.hash[:12]}. From here on nothing else may be read: no internet, no memory. "
                 "Every item carries its own fingerprint, so a later edit is detected on load."),
        "rows": [[_KIND_LABEL.get(k, k), f"{n} item{'s' if n != 1 else ''}"] for k, n in sorted(kinds.items())],
        "note": "Snapshot is complete." if snap.complete else f"Snapshot is missing {len(snap.missing)} sources.",
    })

    m = fc["models"]["market_implied"]
    effr = snap.get("effr")["latest"]
    contract_id = next(e for e in m["evidence"] if e.startswith("futures."))
    contract = snap.get(contract_id)
    implied = 100.0 - contract["price"]
    steps.append({
        "title": "Read where policy stands today",
        "body": f"The next decision is on {fc['meeting']}. The rate banks actually paid overnight is the starting point.",
        "rows": [["Effective fed funds rate", f"{effr['effr']:.2f}% (on {effr['date']})"],
                 ["Target range", f"{effr['target_low']:.2f}% to {effr['target_high']:.2f}%"]],
        "evidence": ["calendar", "effr"],
    })

    if m["method"] == "next_month_contract":
        why = ("The month after the meeting has no meeting of its own, so that month's futures contract trades "
               "entirely at the post-meeting rate. It reads the market's expected new rate directly.")
        maths = [["Contract", f"{contract['symbol']} ({contract['contract_month']})"],
                 ["Price", f"{contract['price']}"],
                 ["Implied rate after the meeting", f"100 − {contract['price']} = {implied:.3f}%"],
                 ["Expected change", f"{implied:.3f}% − {m['rate_before']:.2f}% = {m['expected_change_bp']:+.1f} bp"]]
    else:
        why = ("The meeting-month contract settles at the month's average rate, which blends the rate before and "
               "after the decision by day count. The app backs out the after-meeting rate from that average.")
        maths = [["Contract", f"{contract['symbol']} ({contract['contract_month']})"],
                 ["Price", f"{contract['price']}"],
                 ["Implied month-average rate", f"100 − {contract['price']} = {implied:.3f}%"],
                 ["Expected change (day-weighted)", f"{m['expected_change_bp']:+.1f} bp"]]
    steps.append({"title": "Turn a futures price into an expected rate change", "body": why, "rows": maths,
                  "evidence": [contract_id]})

    share = m["expected_change_bp"] / 25.0
    steps.append({
        "title": "Split the expected change into outcomes",
        "body": ("The Fed moves in 25 bp steps. An expected change that falls between two steps is shared between "
                 f"them: {m['expected_change_bp']:+.1f} bp is {share:+.2f} of a step."),
        "rows": [["Market-implied distribution", _dist(m["probabilities"])]],
    })

    weights = fc["pool_weights"]
    live = [name for name in weights if name in fc["models"]]
    floor = fc.get("surprise_floor", 0.0)
    tr = fc["models"].get("taylor_rule")
    if tr:
        steps.append({
            "title": "Read the rate against the Taylor-rule family",
            "body": (f"With 12-month core PCE at {tr['inputs']['inflation_12m']:.2f}% and unemployment at "
                     f"{tr['inputs']['unemployment']:.1f}%, the four Monetary Policy Report rules, over a grid of "
                     f"neutral-rate and sustainable-unemployment assumptions, prescribe an average move of "
                     f"{tr['expected_change_bp']:+.1f} bp from {tr['rate_before']:.2f}% (spread {tr['spread_bp']:.0f} bp). "
                     f"That spread plus a 15 bp floor sets the width of the distribution."),
            "rows": [[f"{v} rule", f"{bp:+.1f} bp"] for v, bp in tr["by_variant_bp"].items()]
                    + [["Taylor-rule distribution", _dist(tr["probabilities"])]],
            "evidence": tr["evidence"],
        })
    steps.append({
        "title": "Pool the models",
        "body": ("Each live model's distribution is averaged using fixed, recorded weights, then no outcome is allowed "
                 f"below the {floor * 100:.1f}% surprise floor. Code does this; no language model writes the number."
                 + (" Models that could not run on this snapshot are listed and dropped: "
                    + "; ".join(f"{k} ({v})" for k, v in fc.get("models_skipped", {}).items())
                    if fc.get("models_skipped") else "")),
        "rows": [[name, f"weight {w:g}" + ("" if name in live else " (not run)")] for name, w in weights.items()]
                + [["machine_only", _dist(fc["machine_only"])]],
    })

    views = fc["human"]["views_applied"]
    budget = fc["human"]["net_budget"]
    if views:
        body = (f"{len(views)} active view{'s' if len(views) != 1 else ''} gave a net tilt of {budget * 100:+.0f} pp "
                "(capped at 10). Code shifts exactly that much probability, keeps the shape of the machine forecast, "
                "and never puts weight on an outcome the machine gave 0%.")
        rows = [[v["id"], f"{v['direction']}, strength {v['strength']}: {v['rationale']}"] for v in views]
    else:
        body = "No active views, so the human-adjusted forecast equals the machine forecast."
        rows = []
    steps.append({"title": "Apply your views", "body": body,
                  "rows": rows + [["human_adjusted", _dist(fc["human_adjusted"])]]})

    steps.append({
        "title": "Record it so it can be checked",
        "body": ("The forecast is appended to a ledger where each entry includes the fingerprint of the one before, "
                 "so an edit or deletion breaks the chain. 'Verify ledger' recomputes every entry from its stored "
                 "snapshot and demands an exact match."),
        "rows": [["Ledger entry", f"#{entry['seq']} [{entry['entry_hash']}]"],
                 ["Previous entry", entry["prev_hash"]],
                 ["Code version", entry["code_version"]],
                 ["Scorecard version", entry["spec_hash"]],
                 ["Recorded at (UTC)", entry["created_at"]]],
    })

    used = {e for mo in fc["models"].values() for e in mo["evidence"]}
    unused = sorted(i for i in snap.items if i not in used)
    steps.append({
        "title": "What is in the snapshot but not yet in the number",
        "body": ("These items are frozen and ready, but no model reads them yet. They feed the remaining quant "
                 "models and the LLM analysts in the next phases."),
        "rows": [[i, snap.items[i].source] for i in unused],
        "muted": True,
    })
    for n, s in enumerate(steps, start=1):
        s["n"] = n
    return steps
