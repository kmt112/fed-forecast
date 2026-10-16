"""Ordered probit: the Fed's decision at a scheduled meeting as a function of the signals, fitted on history
as it was first published.

PRE-REGISTERED SPEC v1 (2026-10-16, before any fitting). Frozen; its result stands as reported.

Outcome      y in {0 cut, 1 hold, 2 hike}: the change in the policy target from the day before to the day
             after a scheduled decision (see signals/base_rates.py). Intermeeting moves are excluded.
Features     each measured as the reader would have seen it the day before the decision (ALFRED vintages;
             DGS2 is never revised; the target rate is the one in force):
  infl_gap   12-month core PCE inflation − 2.0                     (the live inflation signal's anchor)
  infl_mom   3-month annualised core PCE − 12-month                (momentum against level)
  u_level    unemployment rate
  u_chg12    unemployment − its value 12 months earlier
  pay3       3-month average monthly payroll change, thousands
  y2_gap     2-year Treasury yield − policy target (upper bound of the range; the single target before
             Dec 2008), percentage points                           (the market's expected path)
  prev       previous scheduled decision: −1 cut, 0 hold, +1 hike
Sample       scheduled meetings from the first core-PCE vintage in ALFRED (August 2000) to the latest decision.
Model        P(y ≤ k | x) = Φ(c_k − x·β), two cutpoints, features standardised on the training sample.
             Maximum likelihood (L-BFGS); no regularisation, no feature selection, no re-specification.
Evaluation   single split fixed in advance: train = decisions before 2018-01-01, test = 2018-01-01 onward.
             RESULT (2026-10-16): test log score −1.14 vs −0.71 for the base rate given the previous decision.
             v1 fails the gate and earns no pool weight.

PRE-REGISTERED SPEC v2 (2026-10-16, after seeing v1's failures; written before v2 was fitted).
Contamination note: the two added features answer v1's observed failures (2020 at the lower bound, 2018's
every-other-meeting pattern), so v2's score on 2018 onward is optimistic. The 2010–2017 window is the cleaner
read, and the binding gate is live decisions from here on, tracked in the ledger.
  at_lb      1 if the policy target is at or below 0.25% the day before the decision (no room to cut), else 0
  streak     signed count of consecutive same-direction moves immediately before the decision, capped at ±4
             (+2 = the last two decisions were both hikes; a hold resets it to 0)
Shrinkage    final probabilities = 0.5 × probit + 0.5 × base rate given the previous decision (training sample).
             The 0.5 is fixed in advance, not fitted: a hedge against the overconfidence that sank v1.
Evaluation   expanding window, identical for every model: for each scheduled decision from 2010-01-01 on,
             fit on all decisions before it and predict it. Mean log score and accuracy, overall and split at
             2018-01-01. v1 and the two base rates are scored on the same windows for comparison.
Five buckets cut and hike are split into 25 bp and 50+ bp by the historical share of large moves among moves in
             that direction, in the fitting sample.
Pool entry   none until an amendment sets a weight.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

from fedcast import OUTCOMES_BP, config
from fedcast.data.alfred import as_known
from fedcast.signals import base_rates, inflation, labour
from fedcast.snapshot import Snapshot

FEATURES_V1 = ("infl_gap", "infl_mom", "u_level", "u_chg12", "pay3", "y2_gap", "prev")
FEATURES_V2 = FEATURES_V1 + ("at_lb", "streak")
FEATURES = FEATURES_V1  # kept for the v1 record
CLASSES = ("cut", "hold", "hike")
TRAIN_END = "2018-01-01"
WINDOW_START = "2010-01-01"
SHRINK = 0.5
LOWER_BOUND = 0.25
MODEL_PATH = config.ROOT / "data" / "probit" / "model.json"
PANELS_PATH = config.ROOT / "data" / "probit" / "panels.json"
GOAL = 2.0


# --- feature construction --------------------------------------------------------------------------------

def _ann(series: list[tuple[str, float]], k: int) -> float | None:
    if len(series) <= k:
        return None
    return ((series[0][1] / series[k][1]) ** (12 / k) - 1) * 100


def features_from_series(pce: list[tuple[str, float]], unrate: list[tuple[str, float]],
                         payems: list[tuple[str, float]], dgs2_latest: float, target: float,
                         prev: int, streak: int = 0) -> dict | None:
    """Features from 'as known' series (newest first). None if any input is too short."""
    a12, a3 = _ann(pce, 12), _ann(pce, 3)
    if a12 is None or a3 is None or len(unrate) < 13 or len(payems) < 4:
        return None
    return {"infl_gap": a12 - GOAL, "infl_mom": a3 - a12, "u_level": unrate[0][1],
            "u_chg12": unrate[0][1] - unrate[12][1], "pay3": (payems[0][1] - payems[3][1]) / 3,
            "y2_gap": dgs2_latest - target, "prev": float(prev),
            "at_lb": 1.0 if target <= LOWER_BOUND else 0.0, "streak": float(max(-4, min(4, streak)))}


def _next_streak(streak: int, decision: str) -> int:
    d = {"cut": -1, "hold": 0, "hike": 1}[decision]
    if d == 0:
        return 0
    return streak + d if (streak == 0 or (streak > 0) == (d > 0)) else d


def build_dataset(panels: dict, meetings: list[dict], path: list[dict], as_of: date) -> list[dict]:
    """One row per scheduled decision with exact vintages available: features as known the day before.
    Only decisions at least three days before `as_of` count: a meeting needs the next day's target published
    to be scored, and a future calendar date is not a hold."""
    cutoff = (as_of - timedelta(days=3)).isoformat()
    decided, _ = base_rates.decisions([m for m in meetings if m["date"] <= cutoff], path)
    sched = [d for d in decided if d["scheduled"]]
    dates = [date.fromisoformat(p["date"]) for p in path]
    targets = [p["target"] for p in path]
    dgs2 = sorted(((r["date"], r["value"]) for r in panels["DGS2"]), reverse=True)
    first_pce = min(r["realtime_start"] for r in panels["PCEPILFE"])
    rows, prev, streak = [], 0, 0
    for d in sched:
        when = date.fromisoformat(d["date"]) - timedelta(days=1)
        if when.isoformat() >= first_pce:
            i = max(k for k, t in enumerate(dates) if t <= when)
            y2 = next(v for dt, v in dgs2 if dt <= when.isoformat())
            x = features_from_series(as_known(panels["PCEPILFE"], when, 14), as_known(panels["UNRATE"], when, 14),
                                     as_known(panels["PAYEMS"], when, 5), y2, targets[i], prev, streak)
            if x:
                rows.append({"date": d["date"], "y": CLASSES.index(d["decision"]), "change_bp": d["change_bp"], **x})
        prev = {"cut": -1, "hold": 0, "hike": 1}[d["decision"]]
        streak = _next_streak(streak, d["decision"])
    return rows


# --- fitting ------------------------------------------------------------------------------------------------

def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def class_probs(z: float, cuts: tuple[float, float]) -> list[float]:
    p0 = _phi(cuts[0] - z)
    p1 = _phi(cuts[1] - z) - p0
    return [p0, p1, 1 - p0 - p1]


def fit(rows: list[dict], features: tuple[str, ...] = FEATURES_V1) -> dict:
    import numpy as np
    from scipy.optimize import minimize
    from scipy.stats import norm

    X = np.array([[r[f] for f in features] for r in rows], dtype=float)
    y = np.array([r["y"] for r in rows])
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd

    def nll(theta):
        beta, c1, gap = theta[:len(features)], theta[-2], theta[-1]
        c2 = c1 + math.exp(gap)
        z = Z @ beta
        p0 = norm.cdf(c1 - z)
        p1 = norm.cdf(c2 - z) - p0
        p2 = 1 - p0 - p1
        p = np.where(y == 0, p0, np.where(y == 1, p1, p2))
        return -np.sum(np.log(np.clip(p, 1e-12, None)))

    x0 = np.zeros(len(features) + 2)
    x0[-2], x0[-1] = -1.0, math.log(2.0)
    res = minimize(nll, x0, method="L-BFGS-B")
    beta, c1, gap = res.x[:len(features)], float(res.x[-2]), float(res.x[-1])
    return {"features": list(features), "beta": {f: float(b) for f, b in zip(features, beta)},
            "cuts": [c1, c1 + math.exp(gap)], "mean": {f: float(m) for f, m in zip(features, mu)},
            "sd": {f: float(s) for f, s in zip(features, sd)}, "n": int(len(rows)), "nll": float(res.fun),
            "converged": bool(res.success)}


def predict_probs(model: dict, x: dict) -> list[float]:
    z = sum(model["beta"][f] * (x[f] - model["mean"][f]) / model["sd"][f] for f in model["features"])
    return class_probs(z, tuple(model["cuts"]))


def base_tables(rows: list[dict]) -> dict:
    """Unconditional and given-previous-decision class frequencies from `rows`."""
    n = len(rows)
    uncond = [sum(1 for r in rows if r["y"] == k) / n for k in range(3)]
    cond = {}
    for pv in (-1, 0, 1):
        sub = [r for r in rows if int(r["prev"]) == pv]
        cond[str(pv)] = [sum(1 for r in sub if r["y"] == k) / len(sub) if sub else uncond[k] for k in range(3)]
    return {"unconditional": uncond, "given_previous": cond}  # string keys: they survive the JSON round trip


def fit_v2(rows: list[dict]) -> dict:
    m = fit(rows, FEATURES_V2)
    m["shrink"] = SHRINK
    m["base"] = base_tables(rows)
    return m


def predict_v2(model: dict, x: dict) -> list[float]:
    p = predict_probs(model, x)
    b = model["base"]["given_previous"][str(int(x["prev"]))]
    return [(1 - model["shrink"]) * pi + model["shrink"] * bi for pi, bi in zip(p, b)]


# --- evaluation ---------------------------------------------------------------------------------------------

def _score(pairs: list[tuple[list[float], int]]) -> dict:
    if not pairs:
        return {"log_score": None, "accuracy": None, "n": 0}
    ls = [math.log(max(p[y], 1e-12)) for p, y in pairs]
    acc = sum(1 for p, y in pairs if max(range(3), key=lambda k: p[k]) == y) / len(pairs)
    return {"log_score": round(sum(ls) / len(ls), 4), "accuracy": round(acc, 3), "n": len(pairs)}


def evaluate(rows: list[dict]) -> dict:
    """v1's single pre-registered split (kept as the v1 record)."""
    train = [r for r in rows if r["date"] < TRAIN_END]
    test = [r for r in rows if r["date"] >= TRAIN_END]
    model = fit(train)
    base = base_tables(train)
    return {
        "train_n": len(train), "test_n": len(test), "train_end": TRAIN_END,
        "probit": _score([(predict_probs(model, r), r["y"]) for r in test]),
        "base_unconditional": _score([(base["unconditional"], r["y"]) for r in test]),
        "base_given_previous": _score([(base["given_previous"][str(int(r["prev"]))], r["y"]) for r in test]),
        "test_class_counts": [sum(1 for r in test if r["y"] == k) for k in range(3)],
        "model_train_only": model,
    }


def expanding_window(rows: list[dict], start: str = WINDOW_START) -> dict:
    """Every decision from `start` predicted from strictly earlier decisions, for every model alike."""
    preds: dict[str, list[tuple[list[float], int, str]]] = {k: [] for k in ("probit_v1", "probit_v2", "base_given_previous", "base_unconditional")}
    for i, r in enumerate(rows):
        if r["date"] < start:
            continue
        train = rows[:i]
        base = base_tables(train)
        preds["base_unconditional"].append((base["unconditional"], r["y"], r["date"]))
        preds["base_given_previous"].append((base["given_previous"][str(int(r["prev"]))], r["y"], r["date"]))
        preds["probit_v1"].append((predict_probs(fit(train), r), r["y"], r["date"]))
        preds["probit_v2"].append((predict_v2(fit_v2(train), r), r["y"], r["date"]))
    out = {"start": start, "split": TRAIN_END}
    for name, pairs in preds.items():
        out[name] = {"all": _score([(p, y) for p, y, _ in pairs]),
                     "before_split": _score([(p, y) for p, y, d in pairs if d < TRAIN_END]),
                     "from_split": _score([(p, y) for p, y, d in pairs if d >= TRAIN_END])}
    return out


def size_shares(rows: list[dict]) -> dict:
    """Share of cuts / hikes that were 50 bp or more."""
    out = {}
    for name, sign in (("cut", -1), ("hike", 1)):
        moves = [r for r in rows if (r["change_bp"] > 0) == (sign > 0) and r["change_bp"] != 0]
        out[name] = round(sum(1 for r in moves if abs(r["change_bp"]) >= 50) / len(moves), 3) if moves else 0.25
    return out


def fit_and_save(panels: dict, meetings: list[dict], path: list[dict], as_of: date) -> dict:
    rows = build_dataset(panels, meetings, path, as_of)
    ev_v1 = evaluate(rows)
    ew = expanding_window(rows)
    record = {"spec": "ordered-probit v1 + v2 (see fedcast/models/probit.py docstring)", "fitted_on": date.today().isoformat(),
              "rows": len(rows), "first_date": rows[0]["date"], "last_date": rows[-1]["date"],
              "model_v1": fit(rows), "model_v2": fit_v2(rows),
              "evaluation_v1_split": {k: v for k, v in ev_v1.items() if k != "model_train_only"},
              "evaluation_expanding": ew, "size_shares": size_shares(rows), "dataset": rows}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


# --- live prediction from a snapshot ----------------------------------------------------------------------

def load_model(path: Path = MODEL_PATH) -> dict:
    if not path.exists():
        raise ValueError("ordered probit not fitted yet: run `fedcast probit`")
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_features(snap: Snapshot) -> dict:
    infl = inflation.compute(snap)
    lab = labour.compute(snap)
    hist = base_rates.compute(snap)
    effr = snap.get("effr")["latest"]
    dgs2 = next(o["value"] for o in snap.get("fred.DGS2")["observations"] if o["value"] is not None)
    decided, _ = base_rates.decisions(
        [m for m in snap.get("history.meetings")["meetings"] if m["date"] <= (snap.as_of - timedelta(days=3)).isoformat()],
        snap.get("history.target_rate")["changes"])
    streak = 0
    for d in decided:
        if d["scheduled"]:
            streak = _next_streak(streak, d["decision"])
    prev = {"cut": -1, "hold": 0, "hike": 1}[hist["last_decision"]["decision"]]
    return {"infl_gap": infl["gap_pp"], "infl_mom": infl["momentum"]["3m"] - infl["anchor_12m"],
            "u_level": lab["unemployment"], "u_chg12": lab["unemployment"] - lab["unemployment_year_ago"],
            "pay3": lab["payrolls_3m_avg_k"], "y2_gap": dgs2 - effr["target_high"], "prev": float(prev),
            "at_lb": 1.0 if effr["target_high"] <= LOWER_BOUND else 0.0, "streak": float(max(-4, min(4, streak)))}


def ordered_probit(snap: Snapshot, model_path: Path = MODEL_PATH) -> dict:
    rec = load_model(model_path)
    x = snapshot_features(snap)
    p1 = predict_probs(rec["model_v1"], x)
    p2 = predict_v2(rec["model_v2"], x)
    sh = rec["size_shares"]
    p_cut, p_hold, p_hike = p2
    probs = {-50: p_cut * sh["cut"], -25: p_cut * (1 - sh["cut"]), 0: p_hold,
             25: p_hike * (1 - sh["hike"]), 50: p_hike * sh["hike"]}
    m2 = rec["model_v2"]
    contributions = {f: round(m2["beta"][f] * (x[f] - m2["mean"][f]) / m2["sd"][f], 3) for f in m2["features"]}
    return {"model": "ordered_probit", "version": "v2 (v1 shown for the record)", "meeting": snap.get("calendar")["next_meeting"],
            "features": {k: round(v, 3) for k, v in x.items()}, "contributions": contributions,
            "class_probabilities": {"cut": round(p_cut, 4), "hold": round(p_hold, 4), "hike": round(p_hike, 4)},
            "class_probabilities_v1": {"cut": round(p1[0], 4), "hold": round(p1[1], 4), "hike": round(p1[2], 4)},
            "probabilities": {o: probs[o] for o in OUTCOMES_BP}, "fitted_on": rec["fitted_on"], "rows": rec["rows"],
            "evaluation": rec["evaluation_expanding"], "evaluation_v1_split": rec["evaluation_v1_split"],
            "evidence": sorted(set(inflation.EVIDENCE + labour.EVIDENCE + base_rates.EVIDENCE + ["fred.DGS2", "effr", "calendar"])),
            "snapshot_hash": snap.hash}
