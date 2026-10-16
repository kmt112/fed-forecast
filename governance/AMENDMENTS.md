# Amendment log (H4)

Any change to `fedcast/scorecard.py` needs a new entry here, and the pinned hash in
`tests/test_scorecard.py` updated in the same commit. Amendments are never retroactive:
past ledger entries keep the spec hash they were scored under.

| # | Date | Spec hash | Change | Rationale | Author |
|---|---|---|---|---|---|
| 0 | 2026-09-21 | 74213ad4ceacab43 | Initial pre-registration: S1–S10, tilt cap 10 pp, strengths 3/6/10 pp | Baseline agreed in planning before any forecasting code | tankahming123 |
| 1 | 2026-10-02 | f081a3c6b0d3cd0e | Pool weights market 0.8 / Taylor-rule family 0.2; surprise floor 1.5% per outcome; S10 wording H1–H5 (documents channel) | Taylor rule is the first model to join the market anchor; a 0% bucket is overconfident and cannot be moved by a view; documents became a typed channel | tankahming123 |
| 2 | 2026-10-02 | c897c8e7a54bc3d1 | Pool weights market 0.7 / Taylor 0.2 / prediction market 0.1; S10 wording H1–H6 (hand-entered prediction-market odds) | A second, independent crowd on the same question; thin and fee-distorted, so a small weight taken from the futures anchor | tankahming123 |
| 3 | 2026-10-16 | n/a (model rule, spec hash unchanged) | Prediction-market odds older than 7 days at snapshot time are skipped (recorded in models_skipped); market-implied output records quote time, age and volume | Model audit: a 13-day-old $22 Polymarket entry was still tilting the pool; staleness must be visible and bounded | tankahming123 |
| 4 | 2026-10-16 | n/a (model rule, spec hash unchanged) | Prediction-market odds are used regardless of age; age is recorded and flagged as stale after 7 days (replaces the skip in #3) | Owner's decision: the entered odds stand until replaced, with staleness always visible rather than silently dropped | tankahming123 |
