from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from fedcast import config, forecast, ledger, snapshot
from fedcast.human.store import load_views
from fedcast.human.views import View
from fedcast.models.baseline import market_implied

LEDGER = config.ROOT / "ledger" / "forecasts.jsonl"
VIEWS = config.ROOT / "human" / "views.yaml"


def _bars(probs: dict) -> None:
    for outcome, p in probs.items():
        outcome = int(outcome)
        label = "hold" if outcome == 0 else f"{outcome:+d} bp"
        print(f"  {label:>7}  {p * 100:5.1f}%  {'#' * round(p * 40)}")


def _cmd_snapshot(args: argparse.Namespace) -> None:
    from fedcast.collect import build  # network only when asked for

    snap = build(config.today())
    path = snap.write(config.SNAPSHOT_DIR)
    print(f"snapshot {path.name}: {len(snap.items)} items, complete={snap.complete}")
    for item_id, reason in snap.missing.items():
        print(f"  MISSING {item_id}: {reason}")


def _cmd_baseline(args: argparse.Namespace) -> None:
    path = Path(args.snapshot) if args.snapshot else snapshot.latest(config.SNAPSHOT_DIR)
    result = market_implied(snapshot.load(path))
    if args.json:
        print(json.dumps(result, indent=1))
        return
    print(f"Next FOMC decision {result['meeting']}  (snapshot {path.name})")
    print(f"Rate before: {result['rate_before']:.2f}%   expected change: {result['expected_change_bp']:+.1f} bp"
          f"   [{result['method']}]")
    _bars(result["probabilities"])


def _cmd_forecast(args: argparse.Namespace) -> None:
    path = Path(args.snapshot) if args.snapshot else snapshot.latest(config.SNAPSHOT_DIR)
    snap = snapshot.load(path)
    if not snap.complete and not args.allow_incomplete:
        raise SystemExit(f"snapshot {path.name} is incomplete ({len(snap.missing)} sources missing); "
                         "re-run `fedcast snapshot` or pass --allow-incomplete")
    entry = ledger.append(LEDGER, forecast.run(snap, load_views(VIEWS)))
    fc = entry["forecast"]
    print(f"Ledger entry #{entry['seq']} [{entry['entry_hash']}]  meeting {fc['meeting']}  "
          f"snapshot {fc['snapshot_hash'][:12]}  code {entry['code_version']}")
    print("machine_only:")
    _bars(fc["machine_only"])
    n = len(fc["human"]["views_applied"])
    print(f"human_adjusted ({n} active view{'s' if n != 1 else ''}, net tilt {fc['human']['net_budget'] * 100:+.0f} pp):")
    _bars(fc["human_adjusted"])


def _cmd_replay(args: argparse.Namespace) -> None:
    from fedcast import evals
    from fedcast.scorecard import spec_hash

    n = ledger.verify(LEDGER)
    entries = ledger.read(LEDGER)
    by_seq = {e["seq"]: e for e in entries}
    find = lambda h: next((snapshot.load(d) for d in config.SNAPSHOT_DIR.glob(f"*_{h[:12]}")), None)  # noqa: E731
    details = evals.replay(entries, find, spec_hash())
    scored = [d for d in details if d["ok"] is not None]
    for d in details:
        e = by_seq[d["entry"]]
        mark = "ok  " if d["ok"] else "FAIL" if d["ok"] is False else "    "
        print(f"  #{d['entry']} {mark} {e['forecast']['meeting']} snapshot {e['forecast']['snapshot_hash'][:12]}"
              f"  spec {d['spec']}  {d['note']}")
    print(f"hash chain intact over {n} entries; {sum(d['ok'] for d in scored)}/{len(scored)} entries under the current spec "
          f"{spec_hash()} give back their published probabilities; {n - len(scored)} recorded under earlier specs")
    if any(d["ok"] is False for d in scored):
        raise SystemExit(1)


def _cmd_analyse(args: argparse.Namespace) -> None:
    import yaml

    from fedcast.llm import analyst
    from fedcast.llm.api_backend import make_backend
    from fedcast.llm.backend import ReplayBackend

    path = Path(args.snapshot) if args.snapshot else snapshot.latest(config.SNAPSHOT_DIR)
    snap = snapshot.load(path)
    watchlist = (yaml.safe_load((config.ROOT / "human" / "watchlist.yaml").read_text(encoding="utf-8")) or {}).get("items") or []
    if args.reverify:
        for name, rec in analyst.latest_all(snap.hash).items():
            if rec and name != "naive":
                rec = analyst.reverify(rec, snap, watchlist)
                folder = analyst.ANALYSES_DIR / snap.hash[:12]
                latest_file = sorted(folder.glob(f"*_{name}.json"))[-1]
                latest_file.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
                s = rec["summary"]
                print(f"  {name:15s} tilt {s['tilt_mean_bp']:+.1f} bp, grounded {s['groundedness_pct_mean']}%, leaked {s['leakage_total']}, watch-outs missing {s['watchouts_missing_total']}")
        return
    live = make_backend(args.model)
    backend = ReplayBackend(config.ROOT / "analyses" / "replay", live) if args.replay else live
    arm_map = {"A": ["naive"], "B": ["evidence_only"], "C": ["generalist"], "D": list(analyst.SPECIALISTS)}
    names = (analyst.ALL_ANALYSTS if args.arm == "all" else arm_map.get(args.arm)
             or ["communications" if args.arm == "comms" else args.arm])
    recs = []
    for name in names:
        if name == "naive":
            recs.append(analyst.run_naive(snap, backend, runs=args.runs))
        elif name == "evidence_only":
            recs.append(analyst.run_evidence_only(snap, backend, runs=args.runs))
        elif name == "generalist":
            recs.append(analyst.run_specialist(analyst.GENERALIST, snap, backend, watchlist, runs=args.runs))
        else:
            recs.append(analyst.run_specialist(analyst.SPECIALISTS[name], snap, backend, watchlist, runs=args.runs))
        analyst.save(recs[-1])
    rec = recs[-1]
    out = analyst.ANALYSES_DIR / snap.hash[:12]
    print(f"{rec['analyst']} (arm {rec['arm']}) on snapshot {snap.hash[:12]} via {rec['backend']}: {args.runs} run(s)")
    for k, v in rec["summary"].items():
        print(f"  {k}: {v}")
    if rec["analyst"] not in ("naive", "evidence_only"):
        v = rec["runs"][-1]["verification"]
        print("  last run claims:")
        for c in v["claims"]:
            flag = "ok " if c["verified"] else "UNVERIFIED"
            print(f"    [{flag}] ({c['lean']}) {c['text'][:90]}  <- {c['item']}"
                  + (f"  leaked {c['leaked_numbers']}" if c["leaked_numbers"] else ""))
        print(f"  summary: {rec['runs'][-1]['completion']['output'].get('summary', '')[:300]}")
    print(f"saved {out.relative_to(config.ROOT)}")


def _cmd_probit(args: argparse.Namespace) -> None:
    """Fetch the real-time panels once, build the dataset, run the pre-registered evaluation, fit on all rows."""
    from fedcast.data import alfred, sources
    from fedcast.models import probit

    key = config.secret("FRED_API_KEY")
    if not key:
        raise SystemExit("FRED_API_KEY not set in .env")
    snap = snapshot.load(snapshot.latest(config.SNAPSHOT_DIR))
    meetings = snap.get("history.meetings")["meetings"]
    path = snap.get("history.target_rate")["changes"]
    if probit.PANELS_PATH.exists() and not args.refetch:
        panels = json.loads(probit.PANELS_PATH.read_text(encoding="utf-8"))
        print(f"using cached panels from {probit.PANELS_PATH.relative_to(config.ROOT)} (--refetch to update)")
    else:
        panels = {}
        for sid in ("PCEPILFE", "UNRATE", "PAYEMS"):
            panels[sid] = alfred.fetch_realtime(sid, key, "1990-01-01")
            print(f"  {sid}: {len(panels[sid])} vintage rows, first vintage {alfred.first_vintage(panels[sid])}")
        d = sources.fetch_fred("DGS2", key, config.today(), n_obs=100000, observation_start="1990-01-01")
        panels["DGS2"] = [{"date": o["date"], "value": o["value"]} for o in d["observations"] if o["value"] is not None]
        print(f"  DGS2: {len(panels['DGS2'])} daily observations")
        probit.PANELS_PATH.parent.mkdir(parents=True, exist_ok=True)
        probit.PANELS_PATH.write_text(json.dumps(panels), encoding="utf-8")
    rec = probit.fit_and_save(panels, meetings, path, snap.as_of)
    ev, ew, m1, m2 = rec["evaluation_v1_split"], rec["evaluation_expanding"], rec["model_v1"], rec["model_v2"]
    print(f"dataset: {rec['rows']} scheduled decisions, {rec['first_date']} to {rec['last_date']}")
    print(f"v1 single split (record): train {ev['train_n']} (< {ev['train_end']}), test {ev['test_n']}; classes cut/hold/hike {ev['test_class_counts']}")
    for name in ("probit", "base_given_previous", "base_unconditional"):
        print(f"  {name:22s} log score {ev[name]['log_score']:+.3f}   accuracy {ev[name]['accuracy']:.0%}")
    print(f"expanding window from {ew['start']} (each decision predicted from strictly earlier ones):")
    print(f"  {'model':22s} {'all':>18s} {'2010-2017':>18s} {'2018 on':>18s}")
    for name in ("base_unconditional", "base_given_previous", "probit_v1", "probit_v2"):
        cells = [f"{ew[name][k]['log_score']:+.3f} / {ew[name][k]['accuracy']:.0%}" for k in ("all", "before_split", "from_split")]
        print(f"  {name:22s} {cells[0]:>18s} {cells[1]:>18s} {cells[2]:>18s}")
    print("v2 coefficients (standardised), fitted on all rows:")
    for f, b in m2["beta"].items():
        print(f"  {f:9s} {b:+.3f}")
    print(f"v2 cutpoints {m2['cuts'][0]:+.3f} / {m2['cuts'][1]:+.3f}; shrinkage {m2['shrink']}; converged {m2['converged']}; large-move shares {rec['size_shares']}")
    print(f"saved {probit.MODEL_PATH.relative_to(config.ROOT)}")


def _cmd_ui(args: argparse.Namespace) -> None:
    from fedcast.ui.server import serve

    serve(args.port, open_browser=not args.no_browser)


def main() -> None:
    parser = argparse.ArgumentParser(prog="fedcast")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot", help="fetch live data into a new frozen snapshot").set_defaults(fn=_cmd_snapshot)
    b = sub.add_parser("baseline", help="market-implied probabilities from a snapshot")
    b.add_argument("--snapshot", help="snapshot directory (default: latest)")
    b.add_argument("--json", action="store_true")
    b.set_defaults(fn=_cmd_baseline)
    f = sub.add_parser("forecast", help="run models + human views on a snapshot and append to the ledger")
    f.add_argument("--snapshot", help="snapshot directory (default: latest)")
    f.add_argument("--allow-incomplete", action="store_true")
    f.set_defaults(fn=_cmd_forecast)
    sub.add_parser("replay", help="verify the ledger chain and recompute every entry").set_defaults(fn=_cmd_replay)
    a = sub.add_parser("analyse", help="run an LLM analyst on a snapshot and verify its claims")
    a.add_argument("--arm", choices=["all", "A", "B", "C", "D", "comms", "communications", "minutes_digest", "inflation", "labour",
                                     "financial", "generalist", "evidence_only", "naive"],
                   default="all", help="an arm letter (A naive, B evidence only, C generalist with verifier, D specialists), an analyst name, or all")
    a.add_argument("--runs", type=int, default=1, help="repeat N times to measure repeatability (S1)")
    a.add_argument("--snapshot", help="snapshot directory (default: latest)")
    a.add_argument("--model", help="claude model id (default: the CLI's default)")
    a.add_argument("--replay", action="store_true", help="serve recorded completions when available, record new ones")
    a.add_argument("--reverify", action="store_true", help="re-run the code verifier over the latest recorded analyses, no model calls")
    a.set_defaults(fn=_cmd_analyse)
    pr = sub.add_parser("probit", help="fit and evaluate the ordered probit on history as first published")
    pr.add_argument("--refetch", action="store_true", help="re-download the ALFRED panels")
    pr.set_defaults(fn=_cmd_probit)
    u = sub.add_parser("ui", help="open the local front end in your browser")
    u.add_argument("--port", type=int, default=8765)
    u.add_argument("--no-browser", action="store_true")
    u.set_defaults(fn=_cmd_ui)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
