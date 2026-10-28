# FedCast

Process-judged forecaster for the next FOMC decision. Every number is traceable to a frozen snapshot of
evidence; every change to the method is a logged amendment; LLM output is verified by code before it can
earn a weight. See [PLAN.md](PLAN.md) for the design and [docs/FACTORS.md](docs/FACTORS.md) for the
factor-by-factor spec.

## Run it on any machine

```bash
git clone https://github.com/kmt112/fed-forecast.git
cd fed-forecast
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,api]"      # macOS/Linux: .venv/bin/python
```

Create `.env` in the project folder (it is git-ignored; never commit it):

```
FRED_API_KEY=<your FRED key>
```

Then:

```bash
.venv\Scripts\fedcast ui          # local front end at http://localhost:8765
.venv\Scripts\fedcast snapshot    # fetch live evidence into a frozen, hashed bundle
.venv\Scripts\fedcast forecast    # run the models + your views, append to the ledger
.venv\Scripts\fedcast replay      # verify the ledger chain; entries under the current spec must recompute exactly
.venv\Scripts\fedcast score       # once the decision is in the evidence: log and Brier scores for every forecast of that meeting
.venv\Scripts\fedcast analyse     # run the analysts: --analyst 1..8, a name, specialists or all; --runs 5; --replay to reuse recorded calls
.venv\Scripts\python -m pytest -q
```

## What the app shows

Forecast (both tracks), Evidence graph (click a model to see only what it uses), Your input (views, watch-outs,
documents, prediction-market odds), Methodology, Ledger, Scorecard (the yardstick and the measurements against it:
S1-S3 and S10 per analyst from the recorded runs; S4, S5, S6, S7 and S9 from shock, noise, paraphrase, coherence and
replay checks run by code, on any measured snapshot, with every recorded run and an over-time drift table),
Analyst results (every claim with its quote and its verification) and Analyst prompts (the exact question,
evidence items, pre-reads, schema and full prompt each analyst receives, built live from the latest snapshot).

## LLM runtime

`fedcast analyse` and the UI's **Run analysts** button use whichever runtime is available:

| Runtime | How it is chosen | Setup |
|---|---|---|
| Claude Code CLI (subscription) | default when `claude` is on PATH | `claude auth login` once |
| Anthropic API | `ANTHROPIC_API_KEY` set, or `FEDCAST_LLM_BACKEND=api` | `pip install -e ".[api]"`, set the key |

Both enforce the same rules: no tools, JSON-schema output, every quote verified by code. Completions are
recorded under `analyses/replay/`, so reruns on the same snapshot are free and identical.

## Working from a cloud session (Claude Code on the web)

1. Make sure the Claude GitHub app covers `kmt112/fed-forecast`.
2. In the cloud environment's secrets set `FRED_API_KEY` and, for the analysts, `ANTHROPIC_API_KEY`.
3. Snapshots, the ledger and the analyses are committed, so pull before you forecast and push after.
   The ledger is append-only and hash-chained: two machines appending without pulling first will conflict,
   so forecast from one place at a time.

## Layout

```
fedcast/      data fetchers, snapshot, signals, models, aggregate, forecast, ledger, llm, ui
human/        your typed inputs: views, watch-outs, documents, prediction-market odds
snapshots/    frozen evidence bundles (immutable)
ledger/       append-only forecasts
analyses/     LLM analyst runs and replay recordings
governance/   amendment log for every change to the pre-registered spec
tests/        pytest suite
```
