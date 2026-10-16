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
- [ ] Automate post-decision scoring: `fedcast score` appends Brier / log score per model and per track to the ledger
      once the decision is in the target-rate series.

## Ordered probit
- [ ] v3 candidates (pre-register before fitting; judge on live decisions): months since last move; SEP median path
      as a feature on quarterly meetings; a hiking-cycle vs cutting-cycle regime flag; calibration curve check.
- [ ] Report reliability (calibration) alongside log score in the expanding-window table.
- [ ] Try a lower shrinkage (0.25) only as a pre-registered v3 variant, never by looking at results first.

## Historical base rates
- [ ] Decide whether base rates take a pool weight (proposed 0.1 from the market's 0.7) and whether the 1.5% surprise
      floor is then derived from the base-rate tail instead of fixed.
- [ ] Condition on the previous *two* decisions and on cycle position; check sample sizes stay meaningful.

## Taylor-rule family (the rules are the Fed's; the inputs and the conversion are ours)
- [ ] Inflation measure: show the 3-month-momentum variant beside the 12-month anchor (today they differ in sign:
      +11 bp vs -11 bp); decide by amendment whether the anchor stays 12-month only.
- [ ] r* and u*: read them from the SEP longer-run medians already in the snapshot (3.2% nominal funds rate,
      4.2% unemployment) instead of the fixed grids 0.5-1.5% and 4.0-4.4%.
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
- [ ] Odds age shown and flagged; decide a hard cut-off once there is a record of how stale entries behave.
- [ ] Automated fetch if the venue's API terms allow it; otherwise keep manual entry.

## Signals
- [ ] Pending-releases node (BEA schedule page parses; BLS blocks scripts: use the release dates inside the data?).
- [ ] Inflation nowcast from CPI components rather than a single monthly change.
- [ ] Labour: u* and breakeven payrolls from the SEP longer-run medians / CBO instead of fixed 4.2% and 75k.
- [ ] Financial conditions: a term-premium estimate so the 2-year gap is not read as pure expectations.
- [ ] Communications: speaker weighting (Chair, Vice Chair, voters this year); lexicon review against statements
      since 2020; press-conference Q&A split from prepared remarks.

## LLM analysts
- [ ] N=5 runs per specialist on each snapshot for S1 (repeatability); UI runs selector.
- [ ] Hawk-versus-dove debate and a synthesiser (arm F); verifier extended to numbers in summaries.
- [ ] Arms B and C of the ablation ladder (snapshot + naive prompt; quant models without the LLM).
- [ ] `fedcast eval`: compute S1-S10 from the analyses and the ledger; merge gate on prompt changes.

## App
- [ ] Post-meeting review screen: score expired views, ask what the snapshot missed, turn answers into watch-outs.
- [ ] Model comparison table (one row per model per ledger entry) and a scorecard-over-time view.
- [ ] Scheduled daily evidence pull.
