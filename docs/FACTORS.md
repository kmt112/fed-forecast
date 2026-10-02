# Factors: how each one is filled, and what is still weak

Working spec for Phases 2b–4. Worked numbers are from snapshot `2026-09-24` (November
contract 95.965 → +15.5 bp expected change). Companion to PLAN.md.

## A. Filling each factor robustly

### Frozen evidence

**Overnight rate (EFFR).** 3.88% in a 3.75–4.00 range. The right anchor because futures settle
on EFFR, not the target. Rules: use the last print; flag if more than 3 bp from its 5-day median
(month/quarter-end spikes); record the spread to the range bottom (13 bp) so drift inside the
range is not misread as policy.

**Futures contract.** Use the month after the meeting if meeting-free (Nov: 100 − 95.965 =
4.035% → +15.5 bp); otherwise back the post-meeting rate out of the meeting month by day
weighting. Add: (a) cross-check with the meeting-month contract (Oct 3.89% avg → ~3.98% after,
+10 bp: same sign, noisier); (b) staleness: quote within one trading day or the snapshot is
incomplete; (c) second source (CME settlement) with agreement within one tick.

**Inflation data.** Core PCE 12m 3.34%, 6m ann. 3.46%, 3m ann. 3.05%; core CPI 3m 1.97%, 12m
2.76%. Always compute the same four windows; record staleness (PCE through July, CPI through
August); CPI-based nowcast fills the PCE gap. All values are FRED real-time vintages.

**Labour data.** Unemployment 4.1% (4.3% a year ago); payrolls +71k/3m vs +50k/12m; claims
202k 4-wk vs 209k 26-wk. Express each as level vs its own slow trend; Sahm-style trigger
(3m avg − 12m low = 0.03, trigger 0.5).

**Market data.** 2y 4.87% vs funds 3.88% = 99 bp gap (bond market expects further tightening);
5y breakeven 2.34%; NFCI −0.555 (loose). The 2y–funds gap is the most informative.

**Fed documents.** The statement is ~1,000 characters; the information is the *change*. Fetch
the previous statement and compute a deterministic word diff; parse vote and dissents
mechanically. Missing: press-conference transcript, speeches, SEP dots.

**Pending releases (new node).** Before 28 Oct: September jobs and CPI typically land; September
PCE and Q3 GDP land after; blackout starts ~10 days before. Fetch BLS/BEA calendars; never take
dates from the model's memory.

### Models

**Taylor rule (worked).** r* 1.0 + π 3.34 + 0.5(3.34 − 2) + 0.5 × gap (u 4.1 vs u* 4.2 → Okun
+0.2) = 5.11%. Inertial 0.85 × 3.88 + 0.15 × 5.11 = 4.06% → +18 bp. With 3m inflation: 4.68
→ inertial 4.00 → +12 bp. r*, u* unknowable to ±0.5 → output a range; convert distance-to-rule
into probabilities through a spread, never a point.

**Ordered probit.** Features: four inflation windows, unemployment gap, payroll trend, 2y–funds
gap, previous decision. ~250 meetings since 1994, first-published data only. Evaluate by log
score (hold dominates).

**Base rates.** Measure, don't assume: (a) at five weeks out, when the market priced 40–60% of a
move, how often did the Fed move? (b) how often did the Fed do what the market priced at 0%?
Table (b) becomes a *surprise floor*: no bucket is ever 0%.

**LLM analysts.** Fixed schema: each claim carries a verbatim quote and snapshot item id; the
verifier string-matches the quote against that item, making S2/S3 mechanical. Each watch-out is
a required field. Output is a signed, bounded tilt with reasons; pool weight set by process
scores, never outcomes.

## B. Critique of the plan so far

1. **The 46/54 split is not a probability** — linear interpolation of an expected change. The
   0% buckets are overconfident and the view tilt cannot express "a cut is possible" because it
   never adds mass to a 0% bucket. Fix now: surprise floor (1.5% interim, amendment logged).
   Later: calibrate the expected-change → distribution mapping on history (needs historical
   futures: paid feed, or build our own history by snapshotting daily).
2. **Contamination through the developer.** The model knows outcomes through mid-2026. Pre-register
   probit features and fit procedure before the first backtest; evaluate once on a held-out
   window; no iteration after seeing results.
3. **Control arm scheduled last.** Build Arm A (naive prompt) with the LLM backend, early.
4. **Pool averages non-independent models.** Market-implied is the anchor; others are bounded,
   calibrated adjustments; deterministic weights fitted pre-2024; LLM weight from process scores.
5. **Communications evidence thin.** Previous statement + diff, press conference, speeches.
6. **No horizon awareness.** Pending-releases node.
7. **Views need a review loop.** "What would change my mind" field; post-meeting review screen
   that scores expired views and asks what the snapshot missed.
8. **Housekeeping.** Repo now in the GitHub clone; `.env` key stays local.

## C. Build order

1. Surprise floor + base-rate table.
2. Evidence robustness: previous statement + diff, release calendar, futures staleness + second source.
3. Taylor rule with ranges; pre-registered probit spec; then fit.
4. LLM backend + Arm A + first analyst with quote verification.
5. Post-meeting review screen.
