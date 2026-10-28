# Model improvement backlog

Not pressing. Each item is a candidate change; anything that touches the number goes through an amendment
and, where it is a fitted model, a pre-registered spec and the expanding-window evaluation before it earns weight.

## Model deep-dive (owner's request, 2026-10-16)
- [ ] A detailed, model-by-model review of inputs and mathematics, one session per model, written up in docs/:
      for each input, where it comes from, how it is transformed, what it is assumed to mean, and how sensitive the
      output is to it; for the maths, the formula, its derivation or source, and worked numbers from a real snapshot.
      Order: ordered probit (feature construction, standardisation, cutpoints, shrinkage, bucket split, the
      likelihood and its optimiser, the expanding-window scoring), then Taylor family, market-implied, base rates,
      prediction market, then the signals that feed them.
- [ ] From each review, a list of candidate changes, each tagged "pre-register before testing" where it would be
      judged on outcomes.

## Gate decisions pending live evidence
- [ ] Score every outside-the-pool model (probit v2, base rates, LLM analysts) on the 28 Oct 2026 decision and the
      following meetings from the ledger; decide pool weights only on that record.
- [x] Automate post-decision scoring: `fedcast score` (and the Ledger view's button) appends log and Brier scores per track,
      per model and for two naive baselines to ledger/scores.jsonl once the overnight-rate row is dated after the meeting
      (built 2026-10-28). First use: the 28 Oct 2026 decision, the morning after.

## Ordered probit
- [ ] v3 candidates (pre-register before fitting; judge on live decisions): months since last move; SEP median path
      as a feature on quarterly meetings; a hiking-cycle vs cutting-cycle regime flag; calibration curve check.
- [ ] Report reliability (calibration) alongside log score in the expanding-window table.
- [ ] Try a lower shrinkage (0.25) only as a pre-registered v3 variant, never by looking at results first.

## Pool weights (not tuned; judgement logged as amendments #1, #2, #6)
- [ ] Pre-register three or four candidate weight sets (and candidate tilt caps) now; score each on every live decision
      from 28 Oct 2026; change the live set only by amendment and only on that record, never on the backtest alone.
- [ ] Decide whether the 1.5% floor should be derived from the base-rate tail once the record exists.

## Historical base rates
- [ ] Decide whether base rates take a pool weight (proposed 0.1 from the market's 0.7) and whether the 1.5% surprise
      floor is then derived from the base-rate tail instead of fixed.
- [ ] Condition on the previous *two* decisions and on cycle position; check sample sizes stay meaningful.

## Taylor-rule family (the rules are the Fed's; the inputs and the conversion are ours)
- [ ] Inflation measure: show the 3-month-momentum variant beside the 12-month anchor (today they differ in sign:
      +11 bp vs -11 bp); decide by amendment whether the anchor stays 12-month only.
- [x] r*: read from the New York Fed DSGE model's natural rate for the meeting's quarter (amendment #7, 2026-10-28;
      snapshot item nyfed.dsge). The fixed grid 0.5-1.5% remains the fallback when a snapshot has no DSGE item.
- [ ] u*: read from the SEP longer-run median already in the snapshot (4.2%) instead of the fixed grid 4.0-4.4%.
- [ ] Partial adjustment (rho = 0.85 per meeting) and the quarter-to-meeting scaling of the first-difference rule
      (0.5): document a source or estimate them on the decision history (pre-register first).
- [ ] Rule rate -> probability: the normal with sigma = sqrt(spread^2 + 15 bp^2) is our construction; test
      alternatives on the expanding window (pre-register), and show the per-variant distributions, not just the mean.

## Market-implied
- [ ] Second futures price source with an agreement check (broker API; CME blocks scripts).
- [ ] Calibrate expected change -> outcome distribution on history (needs historical futures prices: paid feed, or
      our own daily snapshots from now on).
- [ ] Detect EFFR technical adjustments inside the range (spread-to-bottom jumps without a decision).

## Prediction market
- [x] Odds age shown and flagged (amendment #4). Decide a hard cut-off once there is a record of how stale entries behave.
- [ ] The entry H6-001 (2 Oct 2026) must be refreshed or withdrawn by hand before the 28 Oct decision.
- [ ] Automated fetch if the venue's API terms allow it; otherwise keep manual entry.

## Signals
- [ ] Pending-releases node (BEA schedule page parses; BLS blocks scripts: use the release dates inside the data?).
- [ ] Inflation nowcast from CPI components rather than a single monthly change.
- [ ] Labour: u* and breakeven payrolls from the SEP longer-run medians / CBO instead of fixed 4.2% and 75k.
- [ ] Financial conditions: a term-premium estimate so the 2-year gap is not read as pure expectations.
- [ ] Communications: speaker weighting (Chair, Vice Chair, voters this year); lexicon review against statements
      since 2020; press-conference Q&A split from prepared remarks.

## LLM analysts
- [x] N=5 runs per specialist on each snapshot for S1 (repeatability); UI runs selector (done 2026-10-16/24).
- [ ] Hawk-versus-dove debate and a synthesiser (arm F); verifier extended to numbers in summaries.
- [x] Arms B and C of the ablation ladder (evidence shown free-form; one generalist with schema and verifier) (done 2026-10-19).
- [x] S1-S3, S10 per arm from the analyses; S4, S5, S6 (typed inputs), S7, S9 from the code chain (evals.deterministic, 2026-10-25).
- [ ] S6 for the LLM arms: the same evidence under reworded prompts (three paraphrases of each specialist's question),
      scored as the max shift in tilt; pre-register the paraphrases.
- [ ] S8: a rubric grader for the traces (base rate first, both sides, uncertainties, pre-mortem), run by a second model
      family, graded against hand-marked examples before it counts.
- [ ] S9 for entries under earlier specs: replay each under its own recorded code version in a git worktree, so the
      whole ledger is checked, not only entries under the current spec.
- [ ] Make `pytest` fail when a scorecard measurement on the latest snapshot regresses (merge gate on prompt changes).

## App
- [ ] Post-meeting review screen: score expired views, ask what the snapshot missed, turn answers into watch-outs.
- [ ] Model comparison table (one row per model per ledger entry) and a scorecard-over-time view.
- [ ] Scheduled daily evidence pull.
