# How the LLM analysts work

A plain-language account for someone who has not seen the architecture. The code is in `fedcast/llm/`.

## The one-paragraph version

FedCast forecasts the next Federal Reserve rate decision. Most of the forecast comes from arithmetic on
observed data (futures prices, policy rules, history). The LLM analysts are the part that reads text: the
Fed's statements, minutes, press conference and speeches, and your own notes. Each analyst is a large
language model (Claude) wrapped in code that controls what it sees, what shape its answer must take, and
whether its answer is true to the evidence. The model never writes the forecast; it produces a small,
bounded lean with cited reasons, and code checks every citation before the lean counts for anything.

## Why not just ask the model?

We measured that. Asked the bare question with no evidence, five times, the same model said a rate *cut*
was most likely, moved its probabilities by over three points between runs, cited nothing, and used 36
numbers that exist nowhere in the evidence. Its memory of the economy is stale and it cannot tell. That
unassisted run is kept as the control (analyst 1) so the harness is always measured against it.

## The harness: five mechanisms around every analyst

1. **Evidence by construction.** Code builds the prompt from a frozen, fingerprinted snapshot of evidence
   taken at a known time. The model's runtime is started with every tool disabled, so it cannot fetch,
   browse, or read files. It sees the evidence we chose and nothing else.
2. **Shape by schema.** The answer must match a fixed JSON schema: a list of claims, each with the verbatim
   quote it rests on and the id of the evidence item; a report on every standing watch-out; a tilt between
   −10 and +10 basis points; a confidence; a one-paragraph summary. Anything else is rejected before we
   see it.
3. **Verification by code.** Each quote is string-matched against the named item. Each number in a claim
   is checked against the whole evidence set. Each active watch-out must be answered by id. The tilt is
   clipped to its bounds. The scores that matter come from these checks, not from the model's confidence.
4. **Recording.** Every call is stored under a hash of its prompt and run index, with the model's full
   output and usage. Any result can be replayed exactly and nothing can be edited without a visible commit.
5. **Scoring.** Repeated runs measure repeatability; the verifier measures groundedness and leakage; the
   watch-out check measures discipline. These are dimensions S1, S2, S3 and S10 of the pre-registered
   process scorecard. An analyst earns a place in the forecast only by passing them, and only by amendment.

## The six analysts

| Analyst | Evidence slice it receives | Pre-read (computed by code, handed over) |
|---|---|---|
| Communications | both statements, the press-conference transcript, policy speeches, the minutes, your documents | vote, statement word-diff, lexicon score |
| Minutes digest | the minutes only | none |
| Inflation | the statement, the SEP projections table, your documents | inflation-gap signal |
| Labour | the statement, the SEP projections table, your documents | labour-slack signal |
| Financial | the statement, your documents | financial-conditions and base-rate signals |
| Naive (control) | nothing | none |

Each specialist is defined by three things only: a question written for its domain, a rule saying which
items it receives, and which pre-read it gets. There is no fine-tuning and no "skills" text: anything the
model would need to be taught is computed in code and handed over as evidence instead, because an
instruction cannot be verified and a number can.

## What one run looks like

1. Pull evidence (or use the latest snapshot). 2. For each specialist, build its prompt from the snapshot.
3. Call the model with tools off and the schema enforced; about 30 to 70 seconds per call.
4. Verify: quotes, numbers, watch-outs, tilt bound. 5. Save the record. 6. Repeat N times for S1.
7. Show the results in the Analysts view (claims with verified/unverified marks) and the Audit view
(every record, every run, every score, over time).

## What the analysts do not do

- They do not see the market price, the other models' outputs, or each other's answers.
- They do not produce probabilities. They produce a tilt in basis points with reasons.
- They are not in the forecast yet. Their tilt is computed and displayed; whether and how it enters the
  pool is a logged amendment decision, taken on their measured record.

## The ladder

The harness is evaluated as a ladder of analysts, each one step up from the last. Analyst 1 is the bare model
with the question only. Analyst 2 adds the evidence. Analyst 3 adds the fixed answer shape with a quote per
claim and the code verifier. Analysts 4 to 8 add specialisation, one slice of evidence each. Every analyst sees
the same snapshot and is scored on the same scorecard, five runs each, so the change in score at each step is
the measured value of the one thing that was added. A planned further step is a hawk-versus-dove debate with a
synthesiser.

## Runtime

Claude through the Claude Code command line (subscription) on this machine, or the Anthropic API with a key
elsewhere; both enforce the same rules. Model and prompt version are recorded on every run.
