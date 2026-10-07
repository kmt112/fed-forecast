# FedCast — Plan (v0.1, 2026-09-19)

## 1. Thesis

> Claude inside an engineered harness produces forecasts that are measurably more
> **repeatable** and **faithful to evidence** than Claude prompted naively — and this
> can be demonstrated by judging the *process*, not the outcome.

The project is therefore two things at once:
1. **An application** — forecasts the next FOMC decision.
2. **An experiment** — an ablation ladder showing what each AI-engineering technique adds.

### Why process, not outcome
- 8 FOMC meetings/year → outcome-based tuning is overfitting to noise.
- Claude's training data contains past outcomes → LLM backtests before mid-2026 are contaminated.
- Futures-implied odds are a very strong benchmark; "beating" them over a few meetings proves nothing.
- Outcomes (Brier / log score vs market) are **logged, never tuned on**.

## 2. Decisions locked

| Decision | Choice |
|---|---|
| Target | Next-meeting decision: P(−50), P(−25), P(hold), P(+25), P(+50) |
| LLM runtime | Claude Code headless (`claude -p`, v2.1.175 installed) behind a backend interface; Anthropic API backend is a drop-in later |
| App form | Python 3.11 CLI + static HTML dashboard |
| Audience | Personal — deliverable is the working tool + scorecard dashboard + ablation results |

## 3. Process scorecard (primary KPI — pre-registered before any forecasting code)

| # | Dimension | Metric | Pass threshold (initial) |
|---|---|---|---|
| S1 | Repeatability | N=10 runs on one frozen snapshot: max std-dev of any outcome probability | ≤ 2 pp |
| S2 | Groundedness | % of factual claims the verifier traces to a snapshot item | ≥ 95% |
| S3 | Leakage control | # of numbers/facts in a trace not present in the snapshot | 0 |
| S4 | Directional sanity | Metamorphic tests: hawkish shock → P(hike/hold)↑; dovish shock → P(cut)↑ | 100% correct sign |
| S5 | Noise invariance | Irrelevant perturbations (reordered docs, unrelated news) shift forecast by | ≤ 1 pp |
| S6 | Paraphrase stability | Reworded prompts shift forecast by | ≤ 2 pp |
| S7 | Coherence | Probabilities sum to 1; run-to-run deltas attributable to input diffs | 100% |
| S8 | Reasoning quality | Rubric-graded trace (base rate first, both sides, key uncertainties, pre-mortem) | ≥ 4/5 |
| S9 | Auditability | Any ledger entry replays bit-for-bit on deterministic parts, within S1 on LLM parts | 100% |

Thresholds may only be changed via a logged amendment with rationale (no silent goalpost moves).

## 4. Architecture

```
fedcast/
  data/        fetchers: FRED/ALFRED (vintage), Fed statements/minutes/speeches, fed funds futures
  snapshot/    immutable, content-hashed input bundle per run (the ONLY thing models may see)
  models/      deterministic: futures-implied probs, Taylor rules, ordered probit, base rates
  llm/
    backend.py     LLMBackend protocol: complete(prompt, schema, seed_tag) -> validated JSON
    claude_code.py ClaudeCodeBackend: shells out to `claude -p --output-format json`
    api.py         AnthropicAPIBackend (stub now; same interface)
    replay.py      ReplayBackend: serves cached responses → deterministic tests, zero cost
  agents/      comms analyst, specialists, hawk/dove debaters, verifier, synthesizer
  prompts/     versioned prompt files (hash recorded in every trace)
  aggregate/   deterministic pooling; LLM adjustment bounded (±X pp) and must cite evidence
  ledger/      append-only JSONL forecasts + full provenance
  evals/       scorecard S1–S9, metamorphic test generator, rubric judge, ablation runner
  dashboard/   static HTML: forecast vs market, scorecard, traces, ablation ladder
  cli.py       fedcast snapshot | forecast | eval | ablate | dashboard
```

**Hard harness rules**
- LLM never sees the internet or its own memory for numbers — snapshot only.
- LLM never emits the final probability freehand — code aggregates.
- Every LLM output is schema-validated; invalid → bounded retry → fail loudly.
- Every run records: snapshot hash, prompt hashes, backend + model id, code git SHA.

## 5. Ablation ladder (the experiment)

| Arm | Adds | Expected to improve |
|---|---|---|
| A | Naive single prompt, no data supplied | (control) |
| B | Snapshot supplied + structured output | S3, S7 |
| C | Quant models + deterministic aggregation, LLM bounded | S1, S4 |
| D | Evidence-citation requirement + verifier agent | S2, S3 |
| E | Self-consistency sampling (k runs → median) | S1, S6 |
| F | Specialists + hawk/dove debate + superforecasting scaffold | S8, S4 |

All arms scored on the same frozen snapshots with the same scorecard. Result = a table
and chart of scorecard dimension × arm. That table *is* the proof.

## 6. Phases & exit criteria

| Phase | Build | Exit criterion |
|---|---|---|
| 0 | Repo, this plan, scorecard spec as code-level constants, amendment log | Spec committed before any model code |
| 1 | Data fetchers + snapshot + futures-implied baseline | Baseline within ~2 pp of CME FedWatch on a live check |
| 2 | Quant models + aggregation + ledger | Vintage-data backtest runs; ledger replay passes (S9 deterministic) |
| 3 | LLM backend interface + ClaudeCode/Replay backends + comms analyst + verifier | S2, S3 measurable on one snapshot |
| 4 | Specialists, debate, self-consistency | Full Arm F forecast end-to-end |
| 5 | Eval suite S1–S9, metamorphic generator, ablation runner, dashboard | `fedcast ablate` produces the ladder table |
| 6 | Live forward tracking from next FOMC meeting; eval-gated prompt changes | Forecast pre-registered in ledger before each meeting |

## 7. Human input (first-class, typed, logged — never a backdoor)

Principle: a human can influence *anything*, but only through a channel the harness can see,
bound, replay and score. Free-text that silently moves the number is the one thing not allowed.

| Channel | Example | What it becomes | How it takes effect |
|---|---|---|---|
| H1 Standing directive | "Watch out for XYZ in future" | Entry in versioned `watchlist.yaml` | Agents must address each item explicitly in the trace ("XYZ: checked — found / not found, evidence …"). Adding one goes through the eval gate. |
| H2 View | "The Chair is more hawkish than the market thinks — lean that way" | Structured view in the snapshot: direction, strength (1–3), rationale, author, timestamp, expiry (default: next meeting) | Treated as citable evidence with a bounded tilt (cap ±10 pp total probability mass moved). Aggregator applies it in code, not the LLM. |
| H3 Correction | "This trace misread the minutes" | Permanent regression case in `evals/golden/` | Every human catch becomes a test that all future versions must pass. |
| H5 Document | "Here is my write-up on bank lending standards" | Markdown file in `human/documents/`, frozen into the next snapshot as a `human_document` item | Evidence for the LLM analysts only, tagged human-sourced; must be quoted like any item; never read by quant models; never moves the number directly. |
| H6 Prediction-market odds | "Polymarket shows hold 68 / hike 31" | Entry in `human/prediction_markets.yaml` with venue, time, URL, raw prices, volume; frozen into the next snapshot | Read by the prediction_market model at pool weight 0.1; evidence, not a view. |
| H4 Governance | "S1 threshold is too loose" | Logged amendment with rationale | Changes scorecard constants; never retroactive. |

**Two-track forecasts.** Every run publishes both `machine_only` and `human_adjusted`
distributions. The delta must be 100% attributable to named H2 views. Over time the ledger
shows whether the human overlay adds or subtracts value (logged, never tuned on).

**Expiry is not forgetting.** An expired view stops tilting new forecasts but stays in the
ledger forever. The model's weights never change, so all "learning" lives in versioned files:

1. *Post-meeting review (process learning).* For each expired view ask: "what did the human
   see that the snapshot did not capture?" The answer becomes a candidate H1 directive, a new
   data source, or an H3 golden case — and enters through the eval gate. This is the main
   learning route and it is outcome-independent.
2. *View track record (reported, not auto-tuned).* The dashboard shows `machine_only` vs
   `human_adjusted` scores per author and view type. With ~8 meetings/year this is noise for
   a long time, so it never changes weights automatically.
3. *Cap amendments (human decision).* Once there are ≥ 20 scored views, the track record may
   justify an H4 amendment raising or lowering the tilt cap. Logged, with rationale.

How human input touches each scorecard dimension:

| # | Human input allowed | Kept honest by |
|---|---|---|
| S1 Repeatability | Views/directives are frozen into the snapshot | Same snapshot incl. human input → same output; S1 measured on both tracks |
| S2 Groundedness | A view is a citable snapshot item (`H2-014`) | Claims resting on it must cite it; verifier labels them "human-sourced", not "data-sourced" |
| S3 Leakage | H2 is the *only* sanctioned route for outside-snapshot information | Audit distinguishes tagged human input from untagged model memory (still 0 tolerated) |
| S4 Directional sanity | Human can add scenario tests ("if XYZ happens, forecast must move hawkish") | A hawkish view must move the forecast hawkish, and never beyond the cap |
| S5 Noise invariance | Human declares what counts as irrelevant | Expired or zero-strength views must move nothing |
| S6 Paraphrase stability | — | Views are structured fields, so rewording the rationale cannot change the tilt |
| S7 Coherence | — | `human_adjusted − machine_only` fully explained by listed views |
| S8 Reasoning quality | Human hand-grades sample traces to calibrate the rubric judge; H1 items become rubric checks | Judge–human agreement tracked |
| S9 Auditability | — | Every human input ledgered; any forecast replays with and without it |
| **S10 Human-input discipline (new)** | — | 100% of human influence arrives via H1–H4; 0 untyped overrides; all views entered before the pre-registration cutoff |

## 8. LLM layer (built 2026-10-02)

`fedcast/llm/backend.py` — `ClaudeCodeBackend` (claude -p, --json-schema, --tools "" so no tool can be used),
`ReplayBackend` (hash-keyed recordings), `FakeBackend` (tests). `fedcast/llm/analyst.py` — the communications
analyst (arm D: snapshot + schema + citations + code verifier + watch-outs + bounded tilt) and the naive control
(arm A). `fedcast analyse --arm comms|naive --runs N`. Analyses are saved under `analyses/<snapshot>/` and shown in
the graph as *computed*; the analyst enters the pool only after passing S1–S3/S10 and an amendment sets its weight.

## 9. Known risks / honest caveats
- **`claude -p` has no temperature/seed control** → repeatability must come from harness design
  (that is the point), and S1 is measured, not assumed. API backend later allows temperature=0 comparison.
- **Subscription rate limits** make N=10 × 6 arms slow → ReplayBackend caching + run ablations in batches.
- **Futures data source**: standalone app cannot use the in-chat IBKR connector; plan is free
  delayed ZQ quotes first, IBKR API optional later.
- **FRED needs a free API key** — you create it; it lives in a local `.env`, never in the repo.
- **LLM-as-judge (S8) is itself an LLM** → calibrate the rubric judge on hand-graded traces first.
- This is a research tool, not investment advice.
