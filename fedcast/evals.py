"""Scorecard measurements from the analyses on one snapshot (S1, S2, S3, S10 for the LLM arms).

Each measurement names the arm it applies to, the value, the pre-registered threshold and pass/fail.
S1 for an arm that outputs probabilities (the naive control) is in pp, as pre-registered. The specialists
output a bounded tilt in bp rather than a distribution, so their S1 is reported in bp of tilt as a proxy,
labelled as such; it becomes a pp measurement once a tilt-to-probability mapping is adopted by amendment.
"""

from __future__ import annotations

from fedcast.scorecard import SCORECARD

_DIM = {d.id: d for d in SCORECARD}


def _row(dim_id: str, arm: str, value, unit: str, note: str = "", runs: int | None = None) -> dict:
    d = _DIM[dim_id]
    ok = None if value is None else d.passes(value)
    return {"id": dim_id, "name": d.name, "arm": arm, "value": value, "unit": unit, "threshold": d.threshold,
            "direction": d.direction, "pass": ok, "runs": runs, "note": note}


def measure(analyses: dict[str, dict | None]) -> list[dict]:
    rows: list[dict] = []
    naive = analyses.get("naive")
    if naive:
        s = naive["summary"]
        rows.append(_row("S1", "A naive", s.get("max_std_pp"), "pp", "max std of any outcome probability across runs", s["runs"]))
        rows.append(_row("S2", "A naive", 0.0, "pct", "nothing to cite: groundedness is 0 by construction", s["runs"]))
        rows.append(_row("S3", "A naive", s["leakage_total"], "count", "numbers in the reasoning, all from memory", s["runs"]))
    specialists = {k: v for k, v in analyses.items() if v and k != "naive"}
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
