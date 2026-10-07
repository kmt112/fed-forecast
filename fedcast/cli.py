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

    snap = build(date.today())
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
    n = ledger.verify(LEDGER)
    current = forecast._code_version()
    failures = 0
    for e in ledger.read(LEDGER):
        want = e["forecast"]
        dirs = list(config.SNAPSHOT_DIR.glob(f"*_{want['snapshot_hash'][:12]}"))
        if not dirs:
            print(f"  #{e['seq']} FAIL snapshot {want['snapshot_hash'][:12]} not found")
            failures += 1
            continue
        views = [View(**v) for v in want["human"]["views_applied"]]
        got = json.loads(json.dumps(forecast.compute(snapshot.load(dirs[0]), views)))
        ok = got == want
        failures += not ok
        note = "" if ok or e["code_version"] == current else f"  (recorded under code {e['code_version']}, now {current})"
        print(f"  #{e['seq']} {'ok  ' if ok else 'FAIL'} {want['meeting']} snapshot {want['snapshot_hash'][:12]}{note}")
    print(f"hash chain intact over {n} entries; {n - failures}/{n} replay bit-for-bit")
    if failures:
        raise SystemExit(1)


def _cmd_analyse(args: argparse.Namespace) -> None:
    import yaml

    from fedcast.llm import analyst
    from fedcast.llm.backend import ClaudeCodeBackend, ReplayBackend

    path = Path(args.snapshot) if args.snapshot else snapshot.latest(config.SNAPSHOT_DIR)
    snap = snapshot.load(path)
    watchlist = (yaml.safe_load((config.ROOT / "human" / "watchlist.yaml").read_text(encoding="utf-8")) or {}).get("items") or []
    live = ClaudeCodeBackend(model=args.model)
    backend = ReplayBackend(config.ROOT / "analyses" / "replay", live) if args.replay else live
    names = list(analyst.SPECIALISTS) if args.arm == "all" else ["communications" if args.arm == "comms" else args.arm]
    recs = []
    for name in names:
        if name == "naive":
            recs.append(analyst.run_naive(snap, backend, runs=args.runs))
        else:
            recs.append(analyst.run_specialist(analyst.SPECIALISTS[name], snap, backend, watchlist, runs=args.runs))
        analyst.save(recs[-1])
    rec = recs[-1]
    out = analyst.ANALYSES_DIR / snap.hash[:12]
    print(f"{rec['analyst']} (arm {rec['arm']}) on snapshot {snap.hash[:12]} via {rec['backend']}: {args.runs} run(s)")
    for k, v in rec["summary"].items():
        print(f"  {k}: {v}")
    if rec["analyst"] != "naive":
        v = rec["runs"][-1]["verification"]
        print("  last run claims:")
        for c in v["claims"]:
            flag = "ok " if c["verified"] else "UNVERIFIED"
            print(f"    [{flag}] ({c['lean']}) {c['text'][:90]}  <- {c['item']}"
                  + (f"  leaked {c['leaked_numbers']}" if c["leaked_numbers"] else ""))
        print(f"  summary: {rec['runs'][-1]['completion']['output'].get('summary', '')[:300]}")
    print(f"saved {out.relative_to(config.ROOT)}")


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
    a.add_argument("--arm", choices=["all", "comms", "communications", "minutes_digest", "inflation", "labour", "financial", "naive"],
                   default="all", help="a specialist (arm D), all of them, or the naive control (arm A)")
    a.add_argument("--runs", type=int, default=1, help="repeat N times to measure repeatability (S1)")
    a.add_argument("--snapshot", help="snapshot directory (default: latest)")
    a.add_argument("--model", help="claude model id (default: the CLI's default)")
    a.add_argument("--replay", action="store_true", help="serve recorded completions when available, record new ones")
    a.set_defaults(fn=_cmd_analyse)
    u = sub.add_parser("ui", help="open the local front end in your browser")
    u.add_argument("--port", type=int, default=8765)
    u.add_argument("--no-browser", action="store_true")
    u.set_defaults(fn=_cmd_ui)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
