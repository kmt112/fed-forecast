from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from fedcast import config, snapshot
from fedcast.models.baseline import market_implied


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
    for outcome, p in result["probabilities"].items():
        label = "hold" if outcome == 0 else f"{outcome:+d} bp"
        print(f"  {label:>7}  {p * 100:5.1f}%  {'#' * round(p * 40)}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="fedcast")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot", help="fetch live data into a new frozen snapshot").set_defaults(fn=_cmd_snapshot)
    b = sub.add_parser("baseline", help="market-implied probabilities from a snapshot")
    b.add_argument("--snapshot", help="snapshot directory (default: latest)")
    b.add_argument("--json", action="store_true")
    b.set_defaults(fn=_cmd_baseline)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
