# FedCast, Fullerton session: speaking script

Matches `FedCast_Fullerton.pptx` at 23 slides. Times add to about 30 minutes with the five demos; the first cut if short is demo 6 (slide 17), then the second half of slide 18.

Before: app at localhost:8765 with evidence pulled today, Forecast view open on the December number. Tabs ready: Evidence graph, Analyst prompts, Analyst results, Ledger. PowerPoint in Presenter View.

## 1 Title (30 s)

On Wednesday the Fed held rates. Nine hours earlier, a program on my laptop had written down: no change, 67.6 percent. No, I'm not retiring on it; the market said the same, with more confidence. So if you came for a hot tip, sorry. If you came out of curiosity, stay: this doesn't beat the market yet, but it is a foundation you can trust, and that is what greater things get built on.

Here's the problem it solves. Ask an AI about the Fed and you get a confident answer. Ask again, a different confident answer. FedCast shows every step from the evidence to the number, and proves the AI gives the same answer on Tuesday as on Monday. Judged by process, not luck.

## 2 About me (1 min)

Quickly, me. AI and data consultant, seconded to a sovereign wealth fund, building analytics for investment teams: attribution, valuation of illiquid assets, trade workflow. Before that, data scientist in the Air Force; before that, engineer. One line from the right: during COVID we built, in weeks, the system that contacted every home-recovery patient in Singapore, ten thousand a day.

The thread through all of it: every system put a model's output in front of people making live decisions, and the hard part was never the model. It was earning trust in what it said. FedCast is that problem made measurable.

## 3 Contents (30 s)

Six stops. What happened on Wednesday and how we called it. Why we built it this way. How the number is put together, with the app. The language-model analysts: their limits, how we work around them, and what they are asked. How we prove the harness works. And what comes next. Appendix slides if anyone wants the mechanics.

## 4 The question, the answer, and what happened (2 min)

The question is narrow on purpose: what will the committee decide at its next meeting, as probabilities over five outcomes. Top row: the date; our number, 67.6 percent no change, recorded nine hours before; what the Fed did, held at three and three-quarters to four; and the vote, ten to two, both dissents for the hike our analysts leaned toward.

Left, how the number was made: 23 pieces of evidence frozen that morning; four classic models pooled by code at fixed weights, which gave 70.9 percent no change; and five language-model analysts on top, every claim quoted and checked, whose mean opinion moved four points toward a hike, giving 67.6.

Right, what the outcome says. We hit it, but so did the futures market at ninety-ten and the betting odds at ninety-five; at five weeks out we do not claim to beat them. What we add is the reasons. Read the table: communications, minutes, inflation and financial conditions all leaned hawkish, labour the lone dove, mean plus four. And the vote had two dissents for a hike. That lean was in the vote. Every reason is a quote found in the frozen evidence. One decision proves little; it is scored formally when the Fed's rate row lands. The rest of the talk is how that number was made and why you can trust the process.

## 5 Demo 1, the forecast (1 min)

This is the app. Forecast view, the December number now. Two tracks: machine only, and with human views. This line: ledger entry, snapshot hash, the analysts' opinion. This number was made at this time from evidence frozen at this time. Everything next is how it got there.

## 6 Four kinds of signal (2 min)

Four kinds of signal already exist. Market prices: futures and prediction markets; the futures market is right about 88 percent of the time thirty days out, and it is our anchor. Economic signals: economist surveys and the data itself; broad, but slow. And the new LLM papers: 90 percent accuracy on sixteen meetings, with nothing verified and nothing replayable.

Put them on a line from pure data to pure model. Futures and rules on the left, surveys in the middle, the LLM agents on the right. FedCast sits between: one input from each area, combined by code at fixed weights, with a language model that must quote what it reads. Neither a formula nor an oracle.

## 7 Why this approach (2 min)

Three whys. One, why an ensemble and not one model: each signal is good at one thing and fails in a known way. Futures are the best single predictor, but they are a price that moves with the market on the day. The Fed's rules are transparent, but built on a natural rate nobody observes. Base rates know what the Fed usually does next and nothing about today. Prediction markets are fast but thin. Pool them at fixed weights and no single failure owns the number.

Two, why a language model on top, harnessed: the pool cannot read. The dissent sentence, a changed word, "the accumulation of more information": that lives in the Fed's text and in no price or rule. But the model remembers, varies and invents, so it never writes the number. It returns claims that each quote a line code finds, and an opinion that moves the pool by at most ten points. Five identical runs, the spread measured.

Three, why judge the process, not the luck: we are early, and eight decisions a year cannot separate skill from luck. So the questions were fixed before any code: same evidence, same answer? every claim quoted? any number from memory? does a shock move the number the right way? Outcomes are logged and never used to tune. A wrong call is a traceable wrong call, and because it goes wrong the same way every time, a fix can be tested and the drift table shows it stayed fixed. Audit, fix, re-measure.

## 8 Model architecture (2 min)

Four families of input. Economic predictors: futures, the Fed's four rules with the New York Fed natural rate, betting odds. Empirical data: what the Fed did next after each kind of decision since 1994; after a hike it hiked again two times in three and never cut, so history alone says hike today. Classic ML: an ordered probit, computed and shown, weight zero until it has a live record. And the language-model analysts, who give a bounded opinion, not a weight. Code pools the first three at 0.6, 0.2, 0.1, 0.1 with a 1.5 percent floor; then the analysts' opinion skews it. No model writes the number.

Right side, the chain in order: evidence, frozen and fingerprinted; signals computed by code; the pool; the analysts, where only four to eight enter and one to three are controls; you, with views capped at ten points; and the ledger, append-only and hash-chained. Every line here is a view in the app.

## 9 The arithmetic (2 min)

Here is the arithmetic for the October call. Each row: what the model reads, its probabilities, its weight. The market reads the November futures price: ninety-ten. The rules read inflation, unemployment and the natural rate: a lean to hike. The odds read Polymarket. The base rates read the 49 meetings since 1994 that followed a hike. The probit at weight zero.

Pool them, then a 1.5 percent floor on every outcome, so nothing is ever called impossible. The tinted row is the analysts: a modifier on the pooled number, not a model in the pool. Mean opinion plus four, hawkish, so four points of probability move toward a hike, capped at ten. Final: 67.6, 22.4, 7.7.

The red box: these weights are judgement, logged as amendments, never fitted. Ideally we would backtest them; with eight decisions a year there is no record to fit on, so live scores from October onward decide them.

## 10 Demo 2, the evidence graph and the pool (3 min)

Evidence graph. Click Market-implied: the futures price, one hundred minus the price, the expected change, the ninety-ten split. Arithmetic, not a black box. Click Pool: the four weights, the pooled line, the analysts' opinion line, the machine track. Click any evidence item: the frozen text and the link to the original.

Blue is in the number, grey is computed but not in it. Click a model and you see only what it read. The language model's opinion is one line between pooled and machine. It can tilt; it cannot write.

## 11 Working around the model's limits (2 min)

Two things a language model cannot be made to stop doing. Left: it answers from memory, and it answers differently each time. One design fixes both. Instead of one big question, "what will the Fed do", each analyst gets small fixed questions with a fixed answer shape, like a multiple-choice and short-answer paper. Less room to wander, so less variation between runs. The instruction says evidence only, and every claim must carry a verbatim quote from a named item, so a remembered fact has nowhere to stand. Every number is checked against the snapshot, and five identical runs must stay within two points.

Right: it can invent its own support, a fluent quote that was never in the document. Code checks every quote character for character; a quote stitched from two places fails. The opinion is bounded to plus or minus ten. And a failed answer goes back once with the verifier's report; both answers are kept. Neither limit is removed; each is designed around and measured on every snapshot. The proof is three slides on.

## 12 The group of analysts (2 min)

One model, the same frozen evidence, eight set-ups. Three points.

One: the three on the left are controls and never touch the number. Analyst one is the model on its own, from memory. Two adds all the evidence, 128,000 characters, free-form answer. Three adds the answer shape and the verifier.

Two: the five on the right enter the number. Same shape and verifier as three, with one change: each gets one slice of evidence and one question about it. Communications reads the statements, minutes, transcript and speeches. Minutes reads the minutes alone. Inflation and labour read the projections with their pre-reads. Financial conditions reads the market pre-reads. Never "give me a probability"; each returns quoted claims and an opinion from minus ten to plus ten, and code averages the five.

Three: every analyst runs five times on the same snapshot, and for one to three those runs are the benchmark four to eight are measured against.

## 13 Demo 3, what each analyst is asked and given (2 min)

Analyst prompts, the 29 October snapshot. Analyst one: 195 characters, no evidence, asked for probabilities. That is the whole input. Analyst four, communications: 45,000 characters. The answer schema, with the opinion bounded. Then the pre-read: the vote parsed, ten to two, Cook and Hammack; the two statements diffed word by word, "raise" removed, "maintain" added; seven hawkish terms, no dovish ones. Code computed this before any model ran. The model is handed the result and must quote it. The rest of the prompt is the Fed's own text.

The hash on the card: five repeats share it. If it is not on this page, the analyst does not get it. Same model; the only difference between analyst one and analyst four is this page. Next: what it answered.

## 14 How good is the harness (2 min)

First, the word. Harnessing is the data and code wrapped around a language model that turn it into a tool with one job: here, a fixed answer shape with a quote per claim, checked by code.

This is the proof, four snapshots, five runs each. Left: how far the answer moves between identical runs, in percentage points. Naive, 4.2. Add the evidence, 3.5. Add the answer shape and the verifier, 0.6. The specialists, 0.8. Middle: numbers from memory, 37 to zero the moment evidence is shown. Right: claims with a verbatim quote, zero to 99.7 percent.

The step that matters is two to three. Evidence alone does not make the model repeatable; the answer shape plus code verification does. The specialists keep both and add attribution.

## 15 LLM analysts: outcome (2 min)

The October run in one band: 25 runs, 25 prompts, 263 claims, all 263 verified, zero numbers from memory, five opinions. Four said hike, labour said hold; mean plus four. Four points moved toward a hike: the table shows each bucket before and after, plus-25 from 20.2 to 22.4. On the right, one real claim as recorded: the September statement stressed elevated inflation, and the statement's own line found by code, character for character. Two dissents for a hike is that opinion, in the vote.

## 16 Demo 4, what the analysts concluded (2 min)

Analyst results, same snapshot. Analyst one's card: cut 25 at 52 percent, 64 numbers from memory across five runs, nothing quoted. It still thinks the Fed is cutting. Same model, no evidence. Analyst four, run one: eight claims, eight quotes found, zero from memory; five runs mean plus five, spread 0.6. Open claim one: the dissenters wanted to tighten, quoting the dissent sentence in the October statement. Open claim six, dovish: the committee chose to hold. It read the diff the pre-read flagged, quoted it, and argued the other side too. The number it gives is an opinion, bounded, and code decides what it is worth.

## 17 Demo 6, the ledger and replay (1 min)

Ledger. Verify. Chain intact; entries under the current spec recompute exactly. Nothing here can be edited or deleted without the chain breaking, any entry recomputes from its snapshot, and eight numbered amendments carry every change with its reason. That is what auditable means here.

## 18 What comes next (2 min)

December is on file: entry 23, a hike at 73.6 percent, specialists plus four again. Six follow-ups in order of value. One, alternative weightings written down now and scored on every live decision; the backtest can guide the Taylor and base-rate split, not the market share, since we hold no history of futures odds. Two, reasoning quality graded by people in the app, twenty hand grades as the reference, a model grader trusted only once it agrees with them. Three, an events agent for the regime shifts the models cannot read: 1987, 1998, 2008, 2020. Four, a second model family on the same harness; if the ladder reads the same, the harness is doing the work. Five, other central banks, same chain, only the evidence sources change. Six, a classical model built for class imbalance, because the probit scored poorly. Which would you do first?

## 19 Three things to take away (1 min)

Design around the model's limits: it remembers, so it reads only frozen evidence; it varies, so it answers in a fixed shape five times and the spread is measured; it invents, so every claim carries a quote code finds. The engineering is in the harness: swap the model and the chain stands; remove the chain and the same model wobbles and leaks. And judge the process: the model lifts, the architecture decides whether the result can be trusted, repeated and replayed. The ask: open the December entry, challenge a quote, and tell me which follow-up deserves to be first. Thank you.

## 20 to 23, on request

- 20 Backup ladder: the numbers behind slide 14, four snapshots.
- 21 How an opinion of plus four becomes four points: the opinion is already in points of probability, capped at ten like a human view; averaged one vote each; spread across buckets by a re-weighting whose steepness is searched so exactly four points cross.
- 22 The probit: version one failed its gate and was reported, not tuned; version two is caveated; weight zero until live decisions judge it; the base rate beat it.
- 23 Historical base rates: group the 266 decisions since 1994 by the previous decision and count what came next. After a hike: hiked again 64 percent, held 36, never cut. No parameters; the prior the other models update.
