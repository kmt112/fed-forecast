# FedCast, Fullerton session: speaking script

Matches `FedCast_Fullerton.pptx` at 24 slides. Times add to about 34 minutes with all six demos; the first cuts if short are demo 5's dropdown and demo 6.

Before: app at localhost:8765 with evidence pulled today, Forecast view open. PowerPoint in Presenter View.

## 1 Title (30 s)

On Wednesday the Fed held rates. Nine hours earlier, a program on my laptop had written down: no change, 67.6 percent. No, I'm not retiring on it; the market said the same, with more confidence. So if you came for a hot tip, sorry. If you came out of curiosity, stay: this doesn't beat the market yet, but it is a foundation you can trust, and that is what greater things get built on.

Here's the problem it solves. Ask an AI about the Fed and you get a confident answer. Ask again, a different confident answer. FedCast shows every step from the evidence to the number, and proves the AI gives the same answer on Tuesday as on Monday. Judged by process, not luck.

## 2 About me (1 min)

Quickly, me. AI and data consultant, seconded to a sovereign wealth fund, building analytics for investment teams: attribution, valuation of illiquid assets, trade workflow. Before that, data scientist in the Air Force; before that, engineer. One line from the right: during COVID we built, in weeks, the system that contacted every home-recovery patient in Singapore, ten thousand a day.

The thread through all of it: every system put a model's output in front of people making live decisions, and the hard part was never the model. It was earning trust in what it said. FedCast is that problem made measurable.

## 3 Contents (30 s)

Six stops. What happened on Wednesday and how we called it. Why we built it this way. How the number is put together. The language-model analysts: what they may do and may not. How we prove the harness works. And what comes next. Between stops I'll open the app itself, so you see the live thing.

## 4 The question, the answer, and what happened (2 min)

The question is narrow on purpose: what will the committee decide at its next meeting, as probabilities over five outcomes. Top row: the date; our number, 67.6 percent no change, recorded nine hours before; what the Fed did, held at three and three-quarters to four; and the vote, ten to two.

Left, how the number was made: 23 pieces of evidence frozen that morning; four classic models pooled by code at fixed weights, which gave 70.9 percent no change; and five language-model analysts on top, every claim quoted and checked, whose combined opinion moved four points toward a hike, giving 67.6.

Right, what the outcome says. We hit it, but so did the futures market at ninety-ten and the betting odds at ninety-five; at five weeks out we do not claim to beat them. What we add is the reasons. Four of five analysts leaned hawkish, labour the lone dove, and the vote had two dissents for a hike. That lean was in the vote. And every reason is a quote found in the evidence, so the call can be taken apart claim by claim. One decision proves little; it is scored formally when the Fed's rate row lands. The rest of the talk is the process.

## 5 Demo 1, the forecast (1 min)

This is the app. Forecast view, the December number now. Two tracks: machine only, and with human views. This line: ledger entry, snapshot hash, the analysts' opinion. This number was made at this time from evidence frozen at this time. Everything next is how it got there.

## 6 Four kinds of signal (2 min)

Four kinds of signal already exist. Market prices: the futures market is right about 88 percent of the time thirty days out; it is our anchor. Policy rules: transparent, the Fed's own, but they depend on things nobody can observe. Economist surveys: broad, slow. And the new LLM papers: 90 percent accuracy on sixteen meetings, with nothing verified.

Put them on a line from pure data to pure model. FedCast sits in the middle: one input from each, combined by code at fixed weights, with a language model that must quote what it reads. Neither a formula nor an oracle.

## 7 Why this approach (2 min)

Three reasons, and the first matters most. Eight decisions a year cannot separate skill from luck, so we judge the process, with questions written before any code existed: same evidence, same answer? every claim quoted? any number from memory? does a shock move the number the right way? Outcomes are logged and never used to tune.

Second, auditable means something concrete: an analyst that says inflation is elevated must quote the statement line, and code checks the quote is there, character for character.

Third, because everything is quotable and the process is repeatable, a wrong call is a traceable wrong call, and when it goes wrong it goes wrong the same way, so a fix can be tested and the drift table shows it stayed fixed. Audit, fix, re-measure.

## 8 Model architecture (2 min)

Four families of input. Economic predictors: futures, the Fed's four rules, betting odds. Empirical data: what the Fed did next after each kind of decision since 1994; after a hike it hiked again two times in three and never cut. Classic ML: an ordered probit, computed but at weight zero. And the language-model analysts, who give a bounded opinion, not a weight. Code pools the first three families; no model writes the number.

Right side, the chain in order: evidence, signals, pool, analysts, human channels, ledger. Only analysts four to eight enter the number. Every line here is a view in the app.

## 9 The arithmetic (2 min)

Here is the arithmetic for the October call. Each row: what the model reads, its probabilities, its weight. The market reads the futures price: ninety-ten. The rules read inflation, unemployment and the natural rate: a lean to hike. The odds, the base rates, and the probit at zero.

Pool them, then a 1.5 percent floor on every outcome, so nothing is ever called impossible. The tinted row is the analysts: an opinion of plus four moves four points of probability toward a hike, after pooling, capped at ten. Final: 67.6, 22.4, 7.7.

The red box: these weights are judgement, logged as amendments, never fitted. With eight decisions a year there is no record to fit on; live scores will decide them.

## 10 Demo 2, the evidence graph and the pool (3 min)

Evidence graph. Click Market-implied: the futures price, one hundred minus the price, the expected change, the split. Arithmetic, not a black box. Click Pool: the four weights, the pooled line, the analysts' opinion line, the machine track. Click any evidence item: the frozen text and the link to the original.

Blue is in the number, grey is computed but not in it. The language model's opinion is one line between pooled and machine. It can tilt; it cannot write.

## 11 Working around the model's limits (2 min)

Two things a language model cannot be made to stop doing. It answers from memory, and it answers differently each time. One design fixes both: instead of one big question, "what will the Fed do", each analyst gets small fixed questions with a fixed answer shape, like a multiple-choice and short-answer paper. Less room to wander, so less variation between runs. The instruction says evidence only, and every claim must carry a verbatim quote, so a remembered fact has nowhere to stand. Every number is checked, and five identical runs must stay within two points.

The second thing: it can invent support, a fluent quote that was never in the document. Code checks every quote character for character; the opinion is bounded; and a failed answer goes back once with the verifier's report. Neither limit is removed; each is designed around and measured.

## 12 The group of analysts (2 min)

One model, the same frozen evidence, eight set-ups. Three points.

One: the three on the left are controls and never touch the number. Analyst one is the model on its own; two adds the evidence; three adds the answer shape and the verifier.

Two: the five on the right enter the number. Each gets one slice of evidence and one question about it, never "give me a probability"; it returns quoted claims and an opinion from minus ten to plus ten.

Three: every analyst runs five times on the same snapshot, and for one to three those runs are the benchmark four to eight are measured against.

## 13 Demo 3, what each analyst is asked and given (2 min)

Analyst prompts. Analyst one: 195 characters, no evidence. Analyst six: the system prompt, the answer schema with the opinion bounded, the inflation pre-read computed by code, the item ids. If it is not on this page, the analyst does not get it. Same model; the only difference is this page.

## 14 How good is the harness (2 min)

This is the proof, four snapshots, five runs each. Left: how far the answer moves between identical runs, in percentage points. Naive, 4.2. Add the evidence, 3.5. Add the answer shape and the verifier, 0.6. Middle: numbers from memory, 37 to zero the moment evidence is shown. Right: claims with a verbatim quote, zero to 99.7 percent.

The step that matters is two to three: evidence alone does not make the model repeatable; the answer shape plus code verification does. Specialists keep both and add attribution.

## 15 LLM analysts: outcome (2 min)

The October run in one band: 25 runs, 25 prompts, 263 claims, all 263 verified, zero numbers from memory, five opinions. Four said hike, labour said hold back; mean plus four; four points moved toward a hike, plus-25 from 20.2 to 22.4. On the right, one real claim, with the statement's own line found by code.

## 16 Demo 4, what the analysts concluded (2 min)

Analyst results. Analyst one's card: it thinks the Fed is cutting, with its numbers from memory flagged; same model, no evidence. Analyst four: the opinion, grounded, leaked and watch-out badges, and one claim with its quote marked verified.

## 17 Demo 5, the scorecard and the drift table (2 min)

Scorecard. Pick a snapshot. Red in the control columns is expected; red on the right would be a defect. Expand shock direction: seven shocks, each with its delta. The over-time table: one row per snapshot, the marks never move. Two red cells have already pointed at defects, both fixed.

## 18 Demo 6, the ledger and replay (1 min)

Ledger. Verify. Chain intact; entries under the current spec recompute exactly. Nothing here can be edited without the chain breaking, and eight numbered amendments carry every change with its reason.

## 19 What comes next (2 min)

December is on file: a hike at 73.6 percent. Six follow-ups in order of value. Pre-registered weight sets scored on every live decision, so the weights stop being judgement. Reasoning quality graded by people in the app, with a model grader trusted only once it agrees with them. An events agent for the regime shifts the models cannot read. A second model family, to show the harness does the work. Other central banks, same chain. And a classical model built for class imbalance, because the probit scored poorly. Which would you do first?

## 20 Three things to take away (1 min)

The harness is the product: same model, same evidence, same day; naive it wobbles and invents, harnessed it is stable, quoted and checked. Judge the process: eight decisions a year cannot prove skill, a scorecard measured on every snapshot can show discipline. And the ask: scrutinise the scorecard, challenge a quote, and tell me which other decision deserves the same chain. Thank you.

## 21 to 24, on request

- 21 Backup ladder: the numbers behind slide 14, four snapshots.
- 22 How an opinion of plus four becomes four points: the opinion is already in points of probability, capped at ten like a human view; averaged one vote each; spread across buckets by a re-weighting whose steepness is searched so exactly four points cross.
- 23 The probit: version one failed its gate and was reported, not tuned; version two is caveated; weight zero until live decisions judge it; the base rate beat it.
- 24 Historical base rates: group the 266 decisions since 1994 by the previous decision and count what came next. After a hike: hiked again 64 percent, held 36, never cut. No parameters; the prior the other models update.
