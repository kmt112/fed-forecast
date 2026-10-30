const pptxgen = require("pptxgenjs");
const path = require("path");
// apply_theme.js ships with the pptx skill; set PPTX_APPLY_THEME to its path on another machine
const APPLY_THEME_CANDIDATES = [process.env.PPTX_APPLY_THEME,
  String.raw`C:\Users\tan_k\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\local-agent-mode-sessions\skills-plugin\ca9dbd77-06d9-4224-b79b-84131dcbdd53\1cf79891-da1f-46df-a0de-7e44b570a773\skills\pptx\scripts\apply_theme.js`,
  "/Users/tankahming/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/ca9dbd77-06d9-4224-b79b-84131dcbdd53/1cf79891-da1f-46df-a0de-7e44b570a773/skills/pptx/scripts/apply_theme.js"].filter(Boolean);
const { applyTheme } = require(APPLY_THEME_CANDIDATES.find(f => require("fs").existsSync(f)));

const THEME = {
  name: "FedCast",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: { dk1: "1B1F2A", lt1: "FFFFFF", dk2: "1E2761", lt2: "EEF2F7", accent1: "1E2761", accent2: "C8553D",
            accent3: "2C6E49", accent4: "6B7280", accent5: "CADCFC", accent6: "E9B44C", hlink: "1E2761", folHlink: "6B7280" },
};
const OUT = path.join(__dirname, "FedCast_Fullerton.pptx");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "FedCast";
pres.title = "FedCast: a process-judged forecaster for the next Fed decision";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.6;

// --- layouts ----------------------------------------------------------------------------------------------
pres.defineSlideMaster({
  title: "DARK", background: { color: THEME.colors.dk2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 2.3, w: W - 2 * M, h: 1.4, fontSize: 40, bold: true, color: C.background1, align: "left", valign: "bottom", margin: 0 } } },
            { placeholder: { options: { name: "body", type: "body", x: M, y: 3.85, w: W - 2 * M, h: 1.6, fontSize: 20, color: THEME.colors.accent5, align: "left", valign: "top", margin: 0 } } }],
});
pres.defineSlideMaster({
  title: "LIGHT", background: { color: THEME.colors.lt1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: W - 2 * M, h: 0.9, fontSize: 32, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 } } },
            { text: { text: "FedCast · Fullerton session · October 2026", options: { x: M, y: H - 0.5, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0, isTextBox: true } } }],
  slideNumber: { x: W - M - 0.6, y: H - 0.5, w: 0.6, h: 0.3, fontSize: 10, color: THEME.colors.accent4, align: "right" },
});

pres.defineSlideMaster({
  title: "DEMO", background: { color: THEME.colors.dk1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: M, y: 0.6, w: W - 2 * M, h: 0.9, fontSize: 30, bold: true, color: C.background1, align: "left", valign: "middle", margin: 0 } } },
            { text: { text: "LIVE DEMO", options: { x: M, y: H - 0.55, w: 4, h: 0.3, fontSize: 10, color: THEME.colors.accent6, bold: true, margin: 0, isTextBox: true } } }],
});
function demo(section, n, view, minutes, open, point, say, notes) {
  const s = pres.addSlide({ masterName: "DEMO", sectionTitle: section });
  s.addText(`Live demo ${n}: ${view}`, { placeholder: "title" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: W - M - 1.6, y: 0.75, w: 1.6, h: 0.6, fill: { color: THEME.colors.accent6 }, line: { color: THEME.colors.accent6 }, rectRadius: 0.1 });
  s.addText(`${minutes} min`, { x: W - M - 1.6, y: 0.75, w: 1.6, h: 0.6, fontSize: 16, bold: true, color: THEME.colors.dk1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  const cols = [["Open", open], ["Point at", point], ["Say", say]];
  cols.forEach(([h, items], i) => {
    const x = M + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 3.85, h: 3.5, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.12 });
    s.addText(h, { x: x + 0.3, y: 2.1, w: 3.2, h: 0.5, fontSize: 18, bold: true, color: THEME.colors.accent6, isTextBox: true, margin: 0 });
    s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1, paraSpaceAfter: 8 } })), { x: x + 0.3, y: 2.7, w: 3.25, h: 2.6, fontSize: 13, color: THEME.colors.lt1, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes(notes);
  return s;
}

const light = (section, title, notes) => { const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: section }); s.addText(title, { placeholder: "title" }); if (notes) s.addNotes(notes); return s; };
const text = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top", ...o });
const card = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || THEME.colors.lt2 }, line: { color: fill || THEME.colors.lt2 }, rectRadius: 0.12, shadow: { type: "outer", blur: 4, offset: 1, angle: 90, color: "000000", opacity: 0.08 } });
const bullets = (items, o = {}) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6, ...o } }));
const stat = (s, x, y, w, big, label, color) => {
  text(s, big, { x, y, w, h: 0.9, fontSize: 40, bold: true, color: color || C.text2, fontFace: THEME.headFontFace });
  text(s, label, { x, y: y + 0.92, w, h: 0.6, fontSize: 12, color: C.accent4 });
};
const numCircle = (s, x, y, n) => { s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 } }); text(s, String(n), { x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle" }); };

// =========================================================================================================
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
  s.addText("FedCast", { placeholder: "title" });
  s.addText("A forecaster for the next Federal Reserve rate decision, built to be judged by its process rather than its luck", { placeholder: "body" });
  text(s, "Tan Kah Ming · Fullerton · October 2026", { x: M, y: 6.4, w: 8, h: 0.4, fontSize: 14, color: THEME.colors.accent5 });
  s.addNotes("Before the session: start the app (fedcast ui), press Pull evidence then Run forecast so the top bar reads 'under an hour ago', open the Forecast view, and have the Evidence graph, Analyst prompts, Analyst results and Scorecard tabs one click away. Open with the one-line thesis: a language model inside an engineered harness gives forecasts that are measurably more repeatable and more faithful to evidence than the same model asked naively, and the way to prove it is to measure the process, not to wait for eight decisions a year to come true.");
}
{
  const s = light("Opening", "About me", "One minute. The thread to pull: every system on the right had to put a model's output in front of people making live decisions, and the hard part was never the model, it was earning trust in what it said. FedCast is that problem made explicit and measurable.");
  card(s, M, 1.55, 4.9, 5.1);
  text(s, "Tan Kah Ming", { x: M + 0.35, y: 1.8, w: 4.2, h: 0.55, fontSize: 24, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  text(s, "Senior AI, Data and Technology Consultant, seconded to Temasek Holdings, Digital Innovation (2023 to now)", { x: M + 0.35, y: 2.4, w: 4.2, h: 0.8, fontSize: 12.5, color: C.text1 });
  text(s, "Before that", { x: M + 0.35, y: 3.3, w: 4.2, h: 0.35, fontSize: 12, bold: true, color: C.text2 });
  s.addText(bullets(["Data scientist, RSAF Data Office: authored the Air Force's AI strategy, set up its first digital unit", "Air engineering and weapons logistics officer, where the data-driven habit started (Weibull analysis, predictive maintenance)"], { fontSize: 11.5, color: C.text1 }), { x: M + 0.35, y: 3.65, w: 4.2, h: 1.4, isTextBox: true, margin: 0, valign: "top" });
  text(s, "Training", { x: M + 0.35, y: 5.1, w: 4.2, h: 0.35, fontSize: 12, bold: true, color: C.text2 });
  text(s, "M.Eng Aeronautical Engineering, Imperial College London · Graduate Certificate in Predictive Analytics, NUS · CFA Level 3 candidate (February 2027)", { x: M + 0.35, y: 5.45, w: 4.2, h: 1.1, fontSize: 11.5, color: C.text1 });
  text(s, "Things I have built that models had to earn trust in", { x: 5.9, y: 1.6, w: 6.85, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
  const built = [
    ["Investment analytics at Temasek", "An AI-assisted analyst performance and attribution platform for 50+ investment professionals, with an LLM signal tracker for high-conviction ideas; signal cadence moved from monthly to daily, every recommendation logged in real time."],
    ["Valuation and execution", "A machine-learning mark-to-market for private holdings, systematic and reproducible; and an AI-driven order management system on AWS processing about S$30m a day, replacing an email-based workflow."],
    ["Forecasting under a scoreboard", "4th of 160+ teams (MIT, DoD, USAF) in the 2023 USAF AI Accelerator, predicting pilot flying difficulty from physiology; an ammunition recommender (quantile LightGBM) that cut wastage with no shortfall, Defence Manpower Committee Innovation Award 2022."],
    ["COVID-19, 2021", "Built, in weeks, the system that engaged every home-recovery patient in Singapore, 10,000 people a day, on form.sg, Azure and Zendesk. The lesson that carries over: a system people rely on must say what it knows and what it does not."],
  ];
  built.forEach(([h, b], i) => {
    const y = 2.15 + i * 1.12;
    numCircle(s, 5.9, y + 0.05, i + 1);
    text(s, h, { x: 6.45, y, w: 6.3, h: 0.35, fontSize: 13, bold: true, color: C.text2 });
    text(s, b, { x: 6.45, y: y + 0.35, w: 6.3, h: 0.78, fontSize: 10.5, color: C.text1 });
  });
}

{
  const s = light("Opening", "What we will cover", "One minute. The thread: a decision was made, here is how we called it, why we built the tool this way, how the number is put together, what the language model is allowed to do and how we prove it behaves, and what comes next. Six stops, with the app opened between them.");
  const stops = [
    ["The question, and what happened", "The 28 October decision, our final number before it, and what the outcome says. The app: the forecast as it stands today."],
    ["Why this approach", "Four kinds of signal already exist and where FedCast sits among them. Why an ensemble, why a harnessed language model on top, why the process is what we judge."],
    ["How the number is built", "Four families of input pooled by code at fixed weights, and the arithmetic from five models to one number. The app: the evidence graph and the pool."],
    ["The LLM analysts", "What a language model cannot stop doing and how the harness works around it; the eight analysts; what each is asked and what it returned. The app: the prompts and the results."],
    ["How good is the harness", "What each step of the harness bought, measured on four snapshots. The app: the scorecard, the drift table, the ledger and replay."],
    ["What comes next", "Six follow-ups in order of value. Appendix: how the analysts' opinion moves the number; the probit."],
  ];
  const lx = M + 0.3;
  s.addShape(pres.shapes.LINE, { x: lx + 0.21, y: 1.75, w: 0, h: 4.75, line: { color: THEME.colors.accent5, width: 3 } });
  stops.forEach(([h, b], i) => {
    const y = 1.55 + i * 0.95;
    numCircle(s, lx, y + 0.08, i + 1);
    text(s, h, { x: lx + 0.7, y, w: 4.2, h: 0.55, fontSize: 16, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: 5.6, y: y + 0.02, w: W - M - 5.6, h: 0.85, fontSize: 11.5, color: C.text1, valign: "middle" });
  });
}

// =========================================================================================================
pres.addSection({ title: "Objective" });
{
  const s = light("Objective", "The question, the answer, and what happened", "Left, three points: where the numbers come from, the pool of classic models, the LLM analysts on top. Right, three points: we hit the target but so did the market and the odds, and we do not claim to beat them at five weeks; the LLM analysts got the direction right, and the table shows each one's opinion against the vote; every reason is a quote found in the evidence, and one decision proves little, so the scoring is formal and the rest of the talk is about process.");
  stat(s, M, 1.5, 3.0, "28 Oct", "the decision being forecast, 2026");
  stat(s, 3.7, 1.5, 3.0, "67.6%", "FedCast, no change: ledger entry #18, nine hours before", C.text2);
  stat(s, 6.9, 1.5, 3.0, "Hold", "what the Fed did: 3.75 to 4.00%, unchanged", THEME.colors.accent3);
  stat(s, 10.1, 1.5, 2.6, "10 to 2", "two dissents, both for the +25 bps the specialists leaned toward", THEME.colors.accent2);
  // left: how the number was made, three points
  card(s, M, 3.2, 5.9, 3.55);
  text(s, "How the number was made", { x: M + 0.25, y: 3.32, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  const made = [
    ["Evidence", "23 items frozen on 28 October: futures, eight FRED series as first published, both statements, minutes, transcript, projections, speeches, 32 years of decisions, the NY Fed natural rate, prediction-market odds."],
    ["Classic models, pooled by code", "Futures-implied 0.6, the Fed's Taylor rules 0.2, prediction-market odds 0.1, historical base rates 0.1; a 1.5% floor on every outcome. Pooled: no change 70.9%, hike 26.2%."],
    ["LLM analysts on top", "Five specialists read the Fed's words; every claim quoted and verified by code. Their mean opinion, +4.0, moves 4 points toward a hike: no change 67.6%, +25 bps 22.4%, +50 bps 7.7%."],
  ];
  made.forEach(([h, b], i) => {
    const y = 3.72 + i * 1.0;
    text(s, h, { x: M + 0.25, y, w: 5.4, h: 0.28, fontSize: 11.5, bold: true, color: C.text2 });
    text(s, b, { x: M + 0.25, y: y + 0.28, w: 5.4, h: 0.72, fontSize: 10, color: C.text1 });
  });
  // right: what the outcome says, three points, with the analysts' table
  const rx = 6.75, rw = W - M - rx;
  card(s, rx, 3.2, rw, 3.55);
  text(s, "What the outcome says", { x: rx + 0.25, y: 3.32, w: rw - 0.5, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  text(s, "1. We hit the target. So did the market (90/10) and the odds (95/5); at five weeks we do not claim to beat them.", { x: rx + 0.25, y: 3.72, w: rw - 0.5, h: 0.5, fontSize: 10, color: C.text1 });
  text(s, "2. The LLM analysts got the direction right, and the vote agreed:", { x: rx + 0.25, y: 4.2, w: rw - 0.5, h: 0.28, fontSize: 10, color: C.text1 });
  const hdr = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const c = (t, col, bold) => ({ text: t, options: { align: "center", color: col || THEME.colors.dk1, bold: !!bold } });
  const rows = [
    [{ text: "Analyst", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, hdr("Opinion"), hdr("Reads")],
    ["4 Communications", c("+6.0 hike", THEME.colors.accent2, true), c("statements, minutes, transcript, speeches")],
    ["5 Minutes", c("+6.2 hike", THEME.colors.accent2, true), c("the minutes only")],
    ["6 Inflation", c("+5.8 hike", THEME.colors.accent2, true), c("inflation pre-read, projections")],
    ["8 Financial conditions", c("+3.4 hike", THEME.colors.accent2, true), c("2-year gap, breakevens, NFCI")],
    ["7 Labour market", c("−1.4 hold", THEME.colors.accent3, true), c("labour pre-read, projections")],
    [{ text: "Mean, one vote each", options: { bold: true } }, c("+4.0 hike", THEME.colors.dk2, true), c("two dissents for a hike in a 10 to 2 vote", THEME.colors.dk2)],
  ];
  s.addTable(rows, { x: rx + 0.25, y: 4.5, w: rw - 0.5, colW: [1.7, 1.0, 2.83], fontSize: 9, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.03, rowH: 0.24 });
  text(s, "3. Every reason is a quote code found in the frozen evidence. One decision proves little: it is scored formally (log score, Brier, against the market and two naive baselines) when the post-meeting rate row lands.", { x: rx + 0.25, y: 6.2, w: rw - 0.5, h: 0.5, fontSize: 10, color: C.text1 });
}
demo("Objective", 1, "the forecast", 1,
  ["The app at localhost:8765, Forecast view", "Top bar: when the evidence was pulled, what is new at the sources"],
  ["The two tracks side by side: machine only, and with views", "The meta line: ledger entry, snapshot hash, the specialists' tilt", "The five bars"],
  ["This number was made at <time> from evidence frozen at <time>. Everything I show next is how it got there."],
  "Keep this to one minute. The point is only that the number exists, is dated, and is traceable. Do not explain the models yet.");
{
  const s = light("Objective", "Why this approach ?", "2 MIN. Three whys. One, why an ensemble: each signal is good at one thing and fails in a known way, futures the best single predictor but a price, rules transparent but built on an unobservable r*, base rates blind to today, odds fast but thin; pooled at fixed published weights no single failure owns the number, the floor keeps every outcome alive, and nothing is fitted because eight decisions a year would fit noise; the backtest only decides who enters, and the probit failed it. Two, why a language model on top: the pool cannot read, and the dissent sentence or a changed word lives only in the text; the model reads it in a minute but remembers, varies and invents, so it never writes the number, it returns quoted claims code verifies and an opinion capped at 10 points. Three, why judge the process: a good year proves nothing; the scorecard was fixed before any code; outcomes are logged, never used to tune; a wrong call is traceable and a fix stays fixed.");
  const cards = [
    ["1", "Why an ensemble, not one model", [
      "Each signal is good at one thing and fails in a known way. Futures: the best single predictor at 30 days, about 88% right, but a price that moves with the market on the day. The Fed's rules: transparent, but built on an r* nobody observes. Base rates: what the Fed usually does next, nothing about today. Prediction markets: fast, but thin.",
      "Pooled at fixed, published weights (0.6 / 0.2 / 0.1 / 0.1), no single input's failure owns the number. A 1.5% floor keeps every outcome alive, so a surprise is never scored at zero.",
      "Nothing is fitted: eight decisions a year would fit noise. The backtest decides only which models enter; the probit failed it and sits at weight 0.",
    ]],
    ["2", "Why a language model on top, harnessed", [
      "The pool cannot read. The dissent sentence, a changed word, 'the accumulation of more information': that is in the Fed's text and in no price or rule.",
      "A model reads it in a minute. But it remembers, varies and invents, so it never writes the number. It returns claims that each quote a line code finds, and an opinion that moves the pool by at most 10 points.",
      "Five identical runs, the spread measured. Boxed and checked this way, a cheaper model can do the job.",
    ]],
    ["3", "Why judge the process, not the luck", [
      "We are early, and eight decisions a year: a good year proves nothing. The yardstick is a ten-point scorecard fixed before any code: same evidence, same answer? every claim quoted? any number from memory? does a shock move the number the right way?",
      "Outcomes are logged after each decision and never used to tune.",
      "A wrong call is a traceable wrong call: we see which input or quote led where. Repeatable means it goes wrong the same way every time, so a fix can be tested and the drift table shows it stayed fixed. Audit, fix, re-measure.",
    ]],
  ];
  cards.forEach(([n, h, items], i) => {
    const x = M + i * 4.1; card(s, x, 1.5, 3.85, 5.1);
    numCircle(s, x + 0.3, 1.7, n);
    text(s, h, { x: x + 0.85, y: 1.65, w: 2.8, h: 0.55, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    s.addText(bullets(items, { fontSize: 12, color: C.text1, paraSpaceAfter: 8 }), { x: x + 0.3, y: 2.4, w: 3.3, h: 4.05, isTextBox: true, margin: 0, valign: "top" });
  });
}

// =========================================================================================================
pres.addSection({ title: "How it works" });
{
  const s = light("How it works", "Model architecture", "Left: the diagram from the brief. Four families of input, combined by code with fixed, published weights; no model writes the number. The language-model family enters only as a bounded opinion. Right: the chain in order, each line a view in the app. Walk the diagram first, then the chain.");
  const fam = [
    ["Economic predictors", "Fed funds futures (the anchor), the Fed's own four Taylor rules with r* from the NY Fed DSGE model, prediction-market odds", THEME.colors.dk2],
    ["Empirical data", "What the Fed did next after each kind of decision, 266 scheduled meetings since 1994. After a hike: hiked again 64%, held 36%, never cut", THEME.colors.dk2],
    ["Classic ML", "An ordered probit fitted on data as first published; computed and shown, weight 0 until it has a live record", THEME.colors.accent4],
    ["LLM-derived", "Five specialist analysts reading the Fed's own words; every claim quoted and verified by code; a bounded opinion, not a weight", THEME.colors.accent2],
  ];
  const bx = M, by = 1.6, bw = 3.0, bh = 1.05, gapY = 0.12;
  fam.forEach(([h, b, col], i) => {
    const y = by + i * (bh + gapY);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y, w: bw, h: bh, fill: { color: col }, line: { color: col }, rectRadius: 0.08 });
    text(s, h, { x: bx + 0.15, y: y + 0.07, w: bw - 0.3, h: 0.32, fontSize: 13, bold: true, color: C.background1 });
    text(s, b, { x: bx + 0.15, y: y + 0.4, w: bw - 0.3, h: 0.62, fontSize: 9.5, color: C.background1 });
    s.addShape(pres.shapes.LINE, { x: bx + bw + 0.08, y: y + bh / 2, w: 0.42, h: 0, line: { color: THEME.colors.accent4, width: 1.5, endArrowType: "triangle" } });
  });
  const totalH = 4 * bh + 3 * gapY;
  const px = bx + bw + 0.58;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: by, w: 1.5, h: totalH, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent5 }, rectRadius: 0.1 });
  text(s, "Pool", { x: px, y: by + 0.3, w: 1.5, h: 0.4, fontSize: 15, bold: true, color: C.text2, align: "center" });
  text(s, "Weights 0.6 / 0.2 / 0.1 / 0.1, fixed and published. A 1.5% floor on every outcome. Then the analysts' opinion, capped at 10 points. Code does this; no model writes the number.", { x: px + 0.12, y: by + 0.8, w: 1.26, h: 3.6, fontSize: 9.5, color: C.text1, align: "center" });
  s.addShape(pres.shapes.LINE, { x: px + 1.58, y: by + totalH / 2, w: 0.42, h: 0, line: { color: THEME.colors.accent4, width: 1.5, endArrowType: "triangle" } });
  const fx = px + 2.08;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: by + totalH / 2 - 0.85, w: 1.55, h: 1.7, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.1 });
  text(s, "Forecast", { x: fx, y: by + totalH / 2 - 0.75, w: 1.55, h: 0.4, fontSize: 14, bold: true, color: C.background1, align: "center" });
  text(s, "28 Oct, entry #18\nno change 67.6%\n+25 bps 22.4%", { x: fx, y: by + totalH / 2 - 0.3, w: 1.55, h: 1.1, fontSize: 10.5, color: C.background1, align: "center" });
  const rx = fx + 1.85, rw = W - M - rx;
  text(s, "The chain, in order", { x: rx, y: 1.55, w: rw, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  const chain = [
    ["Evidence", "23 items, frozen and fingerprinted, dated in US time, data as first published.", THEME.colors.dk2],
    ["Signals", "Numbers computed by code: inflation gap, labour slack, financial conditions, statement tone, base rates, projections.", THEME.colors.dk2],
    ["Pool", "Four families at fixed weights; a 1.5% floor; then the specialists' opinion.", THEME.colors.dk2],
    ["Analysts", "Analysts 4 to 8 enter the number. Analysts 1 to 3 are controls.", THEME.colors.accent2],
    ["You", "Views move the number by at most 10 points and expire; watch-outs are answered by id; documents and odds become evidence.", THEME.colors.accent3],
    ["Ledger", "Append-only, hash-chained; every entry recomputes from its snapshot.", THEME.colors.dk2],
  ];
  chain.forEach(([h, b, col], i) => {
    const y = 2.0 + i * 0.78;
    s.addShape(pres.shapes.RECTANGLE, { x: rx, y: y + 0.05, w: 0.12, h: 0.6, fill: { color: col }, line: { color: col } });
    text(s, h, { x: rx + 0.25, y, w: 1.3, h: 0.7, fontSize: 12.5, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: rx + 1.5, y, w: rw - 1.5, h: 0.72, fontSize: 10, color: C.text1, valign: "middle" });
  });
}
{
  const s = light("How it works", "The arithmetic: from five models to one number", "Entry 18, the final one before the meeting. The pool is a weighted average, then the floor. The specialists' mean score of +4.0 is 4.0 points of probability moved toward a hike, through the same capped mechanism a human view uses. The opinion row is tinted and labelled 'after pooling': it is a modifier on the pooled number, not a model in the pool. Then the footer: the weights are judgement, logged; ideally they would be backtested, but there is no live record yet, so live scores from 28 October onward decide them by amendment.");
  const hdr = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const r = (a, b, c, d, e, f, g, bold) => [{ text: a, options: { bold: !!bold } }, { text: b, options: { fontSize: 10.5 } }, ...[c, d, e, f, g].map(v => ({ text: v, options: { align: "center", bold: !!bold } }))];
  const rows = [
    [{ text: "Model", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, hdr("−25"), hdr("no change"), hdr("+25"), hdr("+50"), hdr("weight")],
    r("Market-implied", "The November fed-funds futures price", "0", "90", "10", "0", "0.6"),
    r("Taylor family", "Core PCE inflation, unemployment, the NY Fed natural rate, through the Fed's own four policy rules", "4.5", "26.9", "44.6", "23.8", "0.2"),
    r("Prediction market", "Polymarket odds on each outcome, 26 October", "0.2", "94.9", "4.5", "0.4", "0.1"),
    r("Historical base rates", "What the Fed did at the 49 meetings since 1994 that followed a hike", "0", "34.7", "52.2", "13.1", "0.1"),
    r("Ordered probit v2", "Nine macro features, as first published; fitted on decisions since 2000", "0", "24.2", "63.8", "12.0", "0"),
    r("Pooled", "Weighted average, then the 1.5% floor", "1.5", "70.9", "20.2", "6.0", "", true),
    [{ text: "After pooling", options: { bold: true, color: THEME.colors.accent2, fill: { color: "FBEFEA" } } },
     { text: [{ text: "Specialists' opinion: a modifier on the pooled number, not a model in the pool. ", options: { bold: true } }, { text: "Mean of analysts 4 to 8, +4.0, hawkish: 4.0 points of probability moved toward a hike, capped at 10." }], options: { fontSize: 10, fill: { color: "FBEFEA" } } },
     ...["−0.3", "−3.3", "+2.2", "+1.7", "—"].map(v => ({ text: v, options: { align: "center", color: THEME.colors.accent4, fill: { color: "FBEFEA" } } }))],
    r("Machine forecast", "Ledger entry #18, 28 October", "1.2", "67.6", "22.4", "7.7", "", true),
  ];
  s.addTable(rows, { x: M, y: 1.45, w: W - 2 * M, colW: [2.0, 4.73, 0.9, 1.3, 0.9, 0.9, 1.4], fontSize: 11, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.04, rowH: 0.44 });
  card(s, M, 6.28, W - 2 * M, 0.62);
  text(s, "Weights are based on judgement", { x: M + 0.25, y: 6.3, w: 3.0, h: 0.58, fontSize: 13, bold: true, color: THEME.colors.accent2, valign: "middle" });
  text(s, "Logged as amendments, never fitted. Ideally we would backtest the appropriate weights; with eight decisions a year there is no record to fit on yet, so live scores from 28 October onward decide them, by amendment.", { x: M + 3.35, y: 6.3, w: W - 2 * M - 3.6, h: 0.58, fontSize: 10.5, color: C.text1, valign: "middle" });
}

demo("How it works", 2, "the evidence graph and the pool", 3,
  ["Evidence graph", "Click the Market-implied box", "Click the Pool box", "Methodology, scroll to the worked example"],
  ["Market-implied: the futures price, 100 minus price, the expected change, the 90/10 split", "Pool: the four weights, the pooled line, the specialists' tilt line, Machine track", "Any evidence item: the frozen text and the link to the original"],
  ["Blue is in the number, grey is computed but not in it. Click a model and you see only what it read.", "The language model's opinion is the one line between Pooled and Machine track. It can tilt, it cannot write."],
  "This is the longest demo. Start at the raw futures price so the audience sees arithmetic, not a black box. Then the pool box, then one click into an evidence item to show the frozen text.");

// =========================================================================================================
pres.addSection({ title: "The harness" });
{
  const s = light("The harness", "Working around the model's limits", "Two things a language model cannot be made to stop doing: it answers from memory and it answers differently each time; and it can invent support. Left column, the first two together, because the same design fixes both: break the one big question into small fixed ones, like a multiple-choice and short-answer paper, and make every answer quote its source. Right column: verification by code. The proof is on the harness slide later.");
  text(s, "Two things a language model cannot be made to stop doing. Neither is removed; each is designed around, and the design is measured on every snapshot.", { x: M, y: 1.38, w: W - 2 * M, h: 0.3, fontSize: 12, color: C.accent4 });
  const cols = [
    { limit: "It answers from memory, and differently each time", sub: "It knows the Fed from its training and will use that unless stopped; ask the same question twice and the number moves.",
      items: [["Break the question down: ", "instead of one big 'what will the Fed do', each analyst gets small fixed questions with a fixed answer shape, like a multiple-choice and short-answer paper. Less room to wander, so less variation between runs."],
              ["Evidence only: ", "the instruction says use only the evidence; every claim must carry a verbatim quote from a named item, so a remembered fact has nowhere to stand."],
              ["Measured: ", "every number in the answer is matched to the snapshot by code; five identical runs per analyst, and the spread between them must stay within 2 points."]] },
    { limit: "It can invent its own support", sub: "A fluent quote or figure that was never in the document.",
      items: [["Check by code, not by a model: ", "every quote is matched to its item character for character; a quote stitched from two places fails."],
              ["Bounds: ", "every watch-out answered by id; the opinion clipped to −10 to +10."],
              ["One repair round: ", "the verifier's report goes back once; both answers are kept; what still fails stays unverified, never hidden."]] },
  ];
  const cw = (W - 2 * M - 0.25) / 2;
  cols.forEach((c, i) => {
    const x = M + i * (cw + 0.25);
    let y = 1.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: 1.2, fill: { color: THEME.colors.accent2 }, line: { color: THEME.colors.accent2 }, rectRadius: 0.1 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + 1.0, w: cw, h: 0.2, fill: { color: THEME.colors.accent2 }, line: { color: THEME.colors.accent2 } });
    text(s, "LIMIT", { x: x + 0.25, y: y + 0.12, w: cw - 0.5, h: 0.2, fontSize: 9, bold: true, color: "F8D7CE", charSpacing: 1 });
    text(s, c.limit, { x: x + 0.25, y: y + 0.34, w: cw - 0.5, h: 0.36, fontSize: 16, bold: true, color: C.background1 });
    text(s, c.sub, { x: x + 0.25, y: y + 0.72, w: cw - 0.5, h: 0.45, fontSize: 11, color: "F8D7CE" });
    y += 1.2;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: 3.4, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.lt2 } });
    text(s, "WHAT WE DO", { x: x + 0.25, y: y + 0.15, w: cw - 0.5, h: 0.2, fontSize: 9, bold: true, color: C.accent4, charSpacing: 1 });
    const runs = [];
    c.items.forEach(([k, v], j) => { runs.push({ text: k, options: { bullet: true, bold: true, color: THEME.colors.dk1 } }); runs.push({ text: v, options: { breakLine: j < c.items.length - 1, paraSpaceAfter: 10 } }); });
    s.addText(runs, { x: x + 0.25, y: y + 0.45, w: cw - 0.5, h: 2.85, fontSize: 13, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  });
}
{
  const s = light("The harness", "LLM breakdown: the group of analysts", "One model, the same frozen evidence, eight configurations. Left: analysts 1 to 3 are controls, drawn grey and dashed; they never enter the number. Right: the five specialists that do. Every analyst runs five times on the same snapshot; for 1 to 3 those runs build the benchmark 4 to 8 are measured against. Analyst 1 sets the baseline (variance, numbers from memory, nothing quoted); 2 tests what immutable evidence fixes; 3 tests the answer shape and code verification. Each rung adds one thing, so the change in the measurements is the value of that thing.");
  const tag = (x, y, t, fill, col) => { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.5, h: 0.22, fill: { color: fill }, line: { color: fill }, rectRadius: 0.11 }); text(s, t, { x, y, w: 1.5, h: 0.22, fontSize: 8, bold: true, color: col, align: "center", valign: "middle", charSpacing: 1 }); };
  text(s, "CONTROLS", { x: M, y: 1.46, w: 1.0, h: 0.24, fontSize: 9.5, bold: true, color: C.accent4, charSpacing: 1, valign: "middle" });
  tag(M + 0.95, 1.47, "BUILD THE LADDER", "E5E7EB", "4B5563");
  const controls = [
    ["1", "Naive", "The question and the date. Nothing else.", "what the model does on its own, from memory. Its output also forms the baseline for every other step."],
    ["2", "Evidence shown, nothing verified", "Every document and pre-read, 128,000 characters. Free-form answer.", "to observe what evidence alone fixes (memory), and what it does not (variance; nothing checkable)."],
    ["3", "Generalist with verifier", "Same evidence; a fixed answer shape, a quote per claim, code checks every quote and number.", "isolate the value of the structure and verification."],
  ];
  controls.forEach(([n, h, gets, intent], i) => {
    const y = 1.75 + i * 1.36;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y, w: 4.17, h: 1.24, fill: { color: "F3F4F6" }, line: { color: "9CA3AF", width: 1.2, dashType: "dash" }, rectRadius: 0.12 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M + 0.17, y: y + 0.16, w: 0.42, h: 0.42, fill: { color: THEME.colors.accent4 }, line: { color: THEME.colors.accent4 }, rectRadius: 0.1 });
    text(s, n, { x: M + 0.17, y: y + 0.16, w: 0.42, h: 0.42, fontSize: 15, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: THEME.headFontFace });
    text(s, h, { x: M + 0.72, y: y + 0.12, w: 3.3, h: 0.3, fontSize: 13, bold: true, color: C.text1 });
    text(s, gets, { x: M + 0.72, y: y + 0.4, w: 3.3, h: 0.42, fontSize: 10.5, color: C.text1 });
    s.addText([{ text: "Intent: ", options: { bold: true } }, { text: intent }], { x: M + 0.72, y: y + 0.84, w: 3.3, h: 0.38, fontSize: 10.5, color: THEME.colors.accent4, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addShape(pres.shapes.LINE, { x: 4.95, y: 3.45, w: 0.5, h: 0, line: { color: THEME.colors.dk2, width: 2.5, endArrowType: "triangle" } });
  text(s, "SPECIALISTS · THE FIVE THAT ENTER THE NUMBER", { x: 5.65, y: 1.46, w: 3.6, h: 0.24, fontSize: 9.5, bold: true, color: C.accent4, charSpacing: 1, valign: "middle" });
  tag(9.3, 1.47, "IN THE FORECAST", THEME.colors.dk2, THEME.colors.lt1);
  const bx = 5.65, bw = W - M - bx;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: 1.75, w: bw, h: 4.2, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.12 });
  s.addText([{ text: "Analyst 3's shape and verifier, with one change: each reader gets " }, { text: "one slice of evidence", options: { bold: true, color: THEME.colors.lt1 } }, { text: ". A judgement is attributable to its slice, and a dissent survives instead of being averaged away." }],
            { x: bx + 0.2, y: 1.9, w: bw - 0.4, h: 0.5, fontSize: 11.5, color: THEME.colors.accent5, isTextBox: true, margin: 0, valign: "top" });
  const specs = [
    ["4", "Communications", "Both statements, the minutes, the transcript, the speeches, the tone pre-read.", "what the committee is signalling."],
    ["5", "Minutes digest", "The minutes only.", "the committee's own account of its debate, read in isolation."],
    ["6", "Inflation", "Projections table, both statements, the inflation pre-read.", "is inflation pulling toward a hike."],
    ["7", "Labour market", "Projections table, both statements, the labour pre-read.", "is labour pulling the other way."],
    ["8", "Financial conditions", "Both statements, the financial-conditions and base-rate pre-reads.", "is the market or stress already doing the committee's work."],
  ];
  const cellW = (bw - 0.4 - 0.12) / 2;
  specs.forEach(([n, h, gets, intent], i) => {
    const full = i === 4;
    const x = bx + 0.2 + (i % 2) * (cellW + 0.12), y = 2.48 + Math.floor(i / 2) * 0.86, w = full ? bw - 0.4 : cellW;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.76, fill: { color: THEME.colors.lt1, transparency: 90 }, line: { color: THEME.colors.lt1, transparency: 90 }, rectRadius: 0.1 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.12, y: y + 0.12, w: 0.34, h: 0.34, fill: { color: THEME.colors.accent2 }, line: { color: THEME.colors.accent2 }, rectRadius: 0.08 });
    text(s, n, { x: x + 0.12, y: y + 0.12, w: 0.34, h: 0.34, fontSize: 12, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: THEME.headFontFace });
    text(s, h, { x: x + 0.56, y: y + 0.06, w: w - 0.66, h: 0.26, fontSize: 12, bold: true, color: C.background1 });
    s.addText([{ text: gets, options: { breakLine: true } }, { text: "Intent: ", options: { bold: true, color: THEME.colors.lt1 } }, { text: intent }], { x: x + 0.56, y: y + 0.3, w: w - 0.66, h: 0.44, fontSize: 9.5, color: THEME.colors.accent5, isTextBox: true, margin: 0, valign: "top" });
  });
  text(s, "Each specialist is asked one question about its own slice (above), not how likely each outcome is. It returns claims, each with a verbatim quote and item id, and an opinion from −10 (strongly dovish) to +10 (strongly hawkish). Code averages the five opinions and moves that many points of probability from hold toward a hike (positive) or a cut (negative), capped at 10.", { x: bx + 0.2, y: 5.12, w: bw - 0.4, h: 0.7, fontSize: 11.5, color: THEME.colors.accent5 });
  card(s, M, 6.06, W - 2 * M, 0.85, "F3F4F6");
  s.addText([{ text: "Every analyst runs five times on the same snapshot. ", options: { bold: true } }, { text: "For analysts 1 to 3 those runs are not forecasts: they build the benchmark that 4 to 8 are measured against." }], { x: M + 0.17, y: 6.12, w: W - 2 * M - 0.34, h: 0.26, fontSize: 11.5, color: C.text1, isTextBox: true, margin: 0 });
  const bench = [["1 sets the baseline: ", "variance of the probabilities across runs; numbers from memory (all of them); nothing quoted."], ["2 tests immutable evidence: ", "numbers from memory fall to zero; the variance does not; nothing can be checked."], ["3 tests the answer shape and code verification: ", "variance falls under 1 point; every claim quoted and checked."]];
  const bwid = (W - 2 * M - 0.34 - 0.3) / 3;
  bench.forEach(([k, v], i) => s.addText([{ text: k, options: { bold: true } }, { text: v }], { x: M + 0.17 + i * (bwid + 0.15), y: 6.42, w: bwid, h: 0.45, fontSize: 10, color: C.text1, isTextBox: true, margin: 0, valign: "top" }));
}
{
  const s = light("The harness", "LLM analysts: outcome", "One line of method, then the outcome. Each specialist runs five times on the same frozen snapshot; the five answers must sit within the variance pass mark, every claim must carry a quote code finds, and no number may come from memory. Only then does the opinion count. The band is the 28 October run; bottom left is what the five said and what it did to the number; bottom right is one claim as recorded, with the quote code found.");
  card(s, M, 1.42, W - 2 * M, 0.78);
  s.addText([{ text: "Each specialist runs five times on the same frozen snapshot. ", options: { bold: true, color: THEME.colors.dk2 } },
             { text: "The five answers must sit within the variance pass mark (2 points), every claim must carry a quote that code finds in the evidence, character for character, and no number may come from memory. Only then does the opinion count toward the number." }],
            { x: M + 0.22, y: 1.5, w: W - 2 * M - 0.44, h: 0.62, fontSize: 12.5, color: C.text1, isTextBox: true, margin: 0, valign: "middle" });
  // the flow band: analysts 4 to 8 only, stepping down toward the five opinions
  const sg = 0.146, sw = (W - 2 * M - 4 * sg) / 5;
  const band = [["25 runs", "5 specialists × 5 identical runs"], ["25 prompts", "one slice each, hashed"], ["263 claims", "every one with a verbatim quote"], ["263 verified", "100%; 0 numbers from memory"], ["5 scores, −10 to +10", "+6.0 · +6.2 · +5.8 · −1.4 · +3.4"]];
  const bh = [1.62, 1.5, 1.38, 1.26, 1.0], bfill = ["CADCFC", "B9CEF3", "A8C3EC", "97B7E5", THEME.colors.dk2], cy = 3.25;
  band.forEach(([big, small], i) => {
    const x = M + i * (sw + sg), w = i < 4 ? sw + sg : sw, h = bh[i], y = cy - h / 2;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: bfill[i] }, line: { color: bfill[i] } });
    const dark = i === 4;
    text(s, big, { x, y: cy - 0.42, w, h: 0.44, fontSize: 20, bold: true, color: dark ? C.background1 : C.text1, align: "center", valign: "middle" });
    text(s, small, { x, y: cy + 0.04, w, h: 0.32, fontSize: 10.5, color: dark ? THEME.colors.accent5 : C.text1, align: "center", valign: "middle" });
  });
  // bottom left: what the five said, and what it did to the number
  const ly = 4.3, lh = 2.6;
  card(s, M, ly, 4.85, lh + 0.1, "FBEFEA");
  text(s, "WHAT THE FIVE SAID, AND WHAT IT DID TO THE NUMBER", { x: M + 0.17, y: ly + 0.12, w: 4.5, h: 0.2, fontSize: 9, bold: true, color: THEME.colors.accent2, charSpacing: 1 });
  const said = [["Communications", "+6.0 hike"], ["Minutes", "+6.2 hike"], ["Inflation", "+5.8 hike"], ["Financial conditions", "+3.4 hike"], ["Labour market", "−1.4 hold"], ["Equal-weight mean", "+4.0"]];
  s.addTable(said.map(([a, b], i) => [{ text: a, options: { color: i === 4 ? THEME.colors.accent3 : THEME.colors.dk1, bold: i === 5 } }, { text: b, options: { align: "right", bold: true, color: i === 4 ? THEME.colors.accent3 : THEME.colors.dk1 } }]),
             { x: M + 0.17, y: ly + 0.42, w: 2.3, colW: [1.4, 0.9], fontSize: 11, border: { type: "none" }, margin: 0.02, rowH: 0.3 });
  s.addText([{ text: "Four say hike, one says hold: ", options: { bold: true } }, { text: "+4.0.", options: { breakLine: true } },
             { text: "+4.0 moves 4 points of probability to the hike side. ", options: { bold: true } }, { text: "Each bucket is scaled by a factor rising from the cut end to the hike end, so the hikes gain 4.0 and hold plus the cuts lose 4.0:" }],
            { x: M + 2.55, y: ly + 0.42, w: 2.2, h: 1.1, fontSize: 10, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  const sh = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const sc = (t, col) => ({ text: t, options: { align: "right", color: col || THEME.colors.dk1 } });
  const spread = [
    [{ text: "Outcome", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, sh("Before"), sh("After"), sh("Change")],
    ["−50 bps", sc("1.5"), sc("1.1"), sc("−0.45", THEME.colors.accent3)],
    ["−25 bps", sc("1.5"), sc("1.2"), sc("−0.27", THEME.colors.accent3)],
    ["no change", sc("70.9"), sc("67.6"), sc("−3.28", THEME.colors.accent3)],
    ["+25 bps", sc("20.2"), sc("22.4"), sc("+2.24", THEME.colors.accent2)],
    ["+50 bps", sc("6.0"), sc("7.7"), sc("+1.76", THEME.colors.accent2)],
  ];
  s.addTable(spread, { x: M + 2.55, y: ly + 1.6, w: 2.2, colW: [0.75, 0.45, 0.45, 0.55], fontSize: 8.5, color: THEME.colors.dk1, border: { type: "solid", color: "E7CFC5", pt: 0.5 }, valign: "middle", margin: 0.02, rowH: 0.17 });
  // bottom right: one verified claim as recorded
  const rx = M + 5.0, rw = W - M - rx;
  card(s, rx, ly, rw, lh);
  text(s, "ONE VERIFIED CLAIM, AS RECORDED · ANALYST 4, COMMUNICATIONS, RUN 1 OF 5", { x: rx + 0.17, y: ly + 0.1, w: rw - 0.34, h: 0.2, fontSize: 9, bold: true, color: C.accent4, charSpacing: 1 });
  s.addText([{ text: "Claim ", options: { bold: true } }, { text: "The September statement stressed elevated inflation and a resolve to return to target on a timelier basis." }], { x: rx + 0.17, y: ly + 0.38, w: rw - 0.34, h: 0.4, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  text(s, "\u201cInflation remains elevated. Today's policy action will support a timelier return to the Committee's 2 percent goal. The Committee will deliver price stability.\u201d", { x: rx + 0.17, y: ly + 0.82, w: rw - 0.34, h: 0.5, fontSize: 9.5, color: "374151", fontFace: "Courier New" });
  s.addText([{ text: "Item " }, { text: "fed.statement.2026-09-16", options: { bold: true, color: THEME.colors.dk1 } }, { text: " · quote found by code, character for character · opinion hawkish · 12 of 12 claims in this run verified" }], { x: rx + 0.17, y: ly + 1.4, w: rw - 0.34, h: 0.4, fontSize: 10, color: C.accent4, isTextBox: true, margin: 0, valign: "top" });
}

demo("The harness", 3, "what each analyst is asked and given", 2,
  ["Analyst prompts view, snapshot of 29 October: the December call", "Analyst 1: open the full prompt", "Analyst 4, Communications: open the full prompt"],
  ["Analyst 1: 195 characters, no evidence, asked for probabilities", "Analyst 4: 45,000 characters. The answer schema. The tone pre-read: vote 10 to 2, Cook and Hammack; the diff: 'raise by 1/4 percentage point' removed, 'maintain' added; seven hawkish terms counted, no dovish ones", "The prompt hash: five repeats share it"],
  ["The pre-read is code, not the model: it parsed the vote, diffed the two statements, counted the words. The model is handed the result and must quote.", "Its answer, next demo: 8 claims, 8 quotes found; the first quotes the dissent sentence; opinion +4.", "Same model. The only difference between analyst 1 and analyst 4 is this page."],
  "DEMO 3, 2 MIN. Before the talk: the app is open on the Analyst prompts view, snapshot 5f6a8d193890, evidence of 29 October; eight cards. STEP 1, 20 s: card 'Analyst 1: Naive control, 195 characters'. Read the Question row aloud. Say: 'that is the whole input, no evidence; it answers from memory, and next demo you will see its memory is stale.' Open the full prompt: one line of system prompt, the schema (five probabilities, a reasoning string), the question. Close. STEP 2, 70 s: card 'Analyst 4: Communications, 45,363 characters'. Point at the four rows: Question (which way does the next decision lean, and why: not a probability); Evidence items; Pre-computed numbers (signal.tone); Answer shape. Open the full prompt. The schema: 'every claim must carry text, a quote, the item and a lean; the opinion is a number between minus 10 and plus 10; the runtime rejects anything else.' Scroll to USER PROMPT, then DETERMINISTIC PRE-READ (signal.tone) and stop: vote 10 for, 2 against, Cook and Hammack; seven hawkish terms, none dovish, score 1.0; diff: removed 'raise', 'by 1/4 percentage point', '12', '0'; added '10', '2', 'maintain', 'strong' and the dissent sentence. Say: 'code computed this before any model ran; it parsed the vote and compared the two statements word by word; the model is handed the result and must quote it.' WATCH-OUTS: none. Scroll fast through the minutes, the transcript, both statements, the speeches: 'that is 95 percent of the prompt, the Fed's own text as published, nothing else.' STEP 3, 20 s: close. Point at the hash on the card: 'five repeats share it.' The line: 'if it is not on this page, the analyst does not get it; same model; the only difference between analyst 1 and analyst 4 is this page.' Bridge: 'next, what it answered.' FALLBACK: if the reader is slow, the four rows on the card carry the point.");


// =========================================================================================================
pres.addSection({ title: "Evidence" });
{
  const s = light("Evidence", "How good is the harness: what each step bought", "Three charts, one per dimension, averaged over the four snapshots. Left: how much the answer moves between identical runs. The step that matters is analyst 2 to analyst 3: the answer shape and the verifier take the wobble from three and a half points to under one. Middle: numbers from memory, gone as soon as the evidence is shown. Right: share of claims whose quote code found verbatim; analyst 2 cannot be measured because it quotes nothing. The specialists keep what analyst 3 achieved. For analysts 3 to 8 the wobble is in their opinion, which is already in points of probability, so the four bars are comparable.");
  const cats = ["1: question only", "2: + evidence", "3: + shape, verifier", "4-8: + one slice each"];
  const cw = (W - 2 * M - 0.5) / 3;
  const chart = (title, labels, vals, x, max, note, fmt = "0.0") => {
    text(s, title, { x, y: 1.45, w: cw, h: 0.4, fontSize: 13, bold: true, color: C.text2 });
    s.addChart(pres.charts.BAR, [{ name: title, labels, values: vals }], {
      x, y: 1.85, w: cw, h: 3.9, barDir: "col", barGapWidthPct: 60,
      chartColors: [THEME.colors.dk2], showValue: true, dataLabelFontSize: 11, dataLabelColor: THEME.colors.dk1, dataLabelFormatCode: fmt,
      catAxisLabelFontSize: 9, catAxisLabelColor: THEME.colors.dk1, valAxisLabelFontSize: 9, valAxisLabelColor: THEME.colors.accent4,
      valAxisMinVal: 0, valAxisMaxVal: max, showLegend: false, catAxisLineShow: false, valAxisLineShow: false,
      valGridLine: { color: "E5E7EB", style: "solid", size: 0.5 },
    });
    text(s, note, { x, y: 5.8, w: cw, h: 0.7, fontSize: 9.5, color: C.accent4 });
  };
  chart("Repeatability: variance between identical runs (pp)", cats, [4.2, 3.5, 0.6, 0.8], M, 5,
        "Largest standard deviation across five runs, mean of four snapshots. Pass mark 2 pp. Analysts 3 to 8: standard deviation of the score, in points of probability.");
  chart("Numbers from memory (count)", cats, [37, 0, 0, 0], M + cw + 0.25, 40,
        "Numbers in the answer that exist nowhere in the frozen evidence, summed over five runs. Pass mark: exactly 0.", "0");
  chart("Claims with a verbatim quote (%)", ["1: question only", "3: + shape, verifier", "4-8: + one slice each"], [0, 99.7, 99.2], M + 2 * (cw + 0.25), 100,
        "Share of claims whose quote code found character for character in the item named. Pass mark 95%. Analyst 2 is not shown: it quotes nothing, so it cannot be measured.");
  text(s, "The step from analyst 2 to analyst 3 is the harness: a fixed answer shape with a quote per claim, checked by code. Specialists keep both and add attribution. What they concluded, four snapshots: analyst 1 a cut at 57 to 67%; analyst 2 +25 bp at 50 to 57%; analyst 3 +5.8 to +7.0 hawkish; specialists +4.0 to +4.4, labour the lone non-hawk.", { x: M, y: 6.42, w: W - 2 * M, h: 0.55, fontSize: 10.5, italic: true, color: C.accent2, valign: "top" });
}
{
  const s = light("Evidence", "What the specialists said on 28 October", "Make it concrete: the five opinions behind entry #18, and one real claim with the quote code matched. The labour analyst is the one that is not hawkish, and because it is a separate reader that dissent is visible rather than averaged away.");
  const rows = [
    [{ text: "Analyst", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Opinion (5 runs)", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }, { text: "Verified", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }],
    ["4 Communications", "Both statements, minutes, transcript, speeches, tone pre-read", { text: "+6.0 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["5 Minutes digest", "The minutes only", { text: "+6.2 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["6 Inflation", "Inflation pre-read, projections, both statements", { text: "+5.8 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["7 Labour market", "Labour pre-read, projections, both statements", { text: "−1.4 bp, no hike", options: { align: "center", color: THEME.colors.accent3, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["8 Financial conditions", "Financial pre-read, base rates, both statements", { text: "+3.4 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
  ];
  s.addTable(rows, { x: M, y: 1.55, w: 7.4, colW: [1.9, 3.0, 1.4, 1.1], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.55 });
  card(s, 8.4, 1.55, 4.33, 3.75);
  text(s, "One claim, as recorded", { x: 8.7, y: 1.75, w: 3.8, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  text(s, "Communications analyst, run 1 of 5: the September statement stressed elevated inflation and a resolve to return to target on a timelier basis.", { x: 8.7, y: 2.2, w: 3.8, h: 0.9, fontSize: 12, color: C.text1 });
  text(s, "\u201cInflation remains elevated. Today's policy action will support a timelier return to the Committee's 2 percent goal. The Committee will deliver price stability.\u201d", { x: 8.7, y: 3.1, w: 3.8, h: 0.9, fontSize: 10, color: "374151", fontFace: "Courier New" });
  text(s, "Item fed.statement.2026-09-16 · quote found by code, character for character · 12 of 12 claims in this run verified, none from memory.", { x: 8.7, y: 4.05, w: 3.8, h: 1.1, fontSize: 11, color: C.text1 });
}
demo("Evidence", 4, "what the analysts concluded", 2,
  ["Analyst results view, same snapshot of 29 October", "Analyst 1 (naive) card", "Analyst 4 (communications) card, run 1"],
  ["Analyst 1: cut 25 at 52%, 64 numbers from memory across five runs, nothing quoted", "Analyst 4: 8 claims, 8 quotes found, 0 numbers from memory; five runs mean +5.0, spread 0.6", "Claim 1: the dissenters wanted to tighten, quoting the dissent sentence in the 28 October statement. Claim 6, dovish: the committee chose to hold"],
  ["Every claim you see has a quote that code found character for character in the item named.", "The analyst read the diff the pre-read flagged and quoted it. It also argued the other side: the hold itself, and the wait-for-data line.", "The naive analyst still thinks the Fed is cutting. Same model, no evidence."],
  "DEMO 4, 2 MIN. Analyst results view, 29 October snapshot. Analyst 1 first: cut 25 at 52%, 64 numbers from memory, nothing quoted; its memory of the Fed is stale. Then analyst 4, run 1: 8 claims, 8 verified, opinion +4; the mean of five runs +5.0 with a spread of 0.6. Open the first claim: the dissent sentence, found by code in the 28 October statement. Open the sixth: 'the committee actually chose to hold', its own dovish offset. Say: the analyst was handed the diff and quoted it, and it argued both sides; the number it gives is an opinion, bounded, and the code decides what it is worth.");
{
  const s = light("Evidence", "The scorecard: eight of ten dimensions measured by code", "Ten dimensions fixed before any forecasting code existed. Eight are now measured automatically on each new snapshot. The over-time table is the drift check: the marks never move, so a cell that turns red is a change in the system. It has already caught two things, bottom right.");
  const dims = [
    ["1", "Repeatability", true], ["2", "Quotes verified", true], ["3", "Numbers from memory", true], ["4", "Shock direction", true], ["5", "Noise invariance", true],
    ["6", "Rewording", "part"], ["7", "Coherence", true], ["8", "Reasoning quality", false], ["9", "Replay", true], ["10", "Human-input discipline", true],
  ];
  dims.forEach(([id, name, m], i) => {
    const x = M + (i % 5) * 2.45, y = 1.6 + Math.floor(i / 5) * 1.25;
    const col = m === true ? THEME.colors.accent3 : m === "part" ? THEME.colors.accent6 : THEME.colors.accent4;
    card(s, x, y, 2.3, 1.05, THEME.colors.lt2);
    s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: y + 0.3, w: 0.42, h: 0.42, fill: { color: col }, line: { color: col } });
    text(s, id, { x: x + 0.15, y: y + 0.3, w: 0.42, h: 0.42, fontSize: 10, bold: true, color: C.background1, align: "center", valign: "middle" });
    text(s, name, { x: x + 0.68, y: y + 0.12, w: 1.55, h: 0.45, fontSize: 12, bold: true, color: C.text2, valign: "middle" });
    text(s, m === true ? "measured by code" : m === "part" ? "typed inputs only" : "not built: rubric grader", { x: x + 0.68, y: y + 0.55, w: 1.55, h: 0.45, fontSize: 10, color: C.accent4 });
  });
  card(s, M, 4.3, 6.0, 2.4);
  text(s, "Measured by code on the 28 October snapshot", { x: M + 0.3, y: 4.45, w: 5.4, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["Shock direction: 7 shocks, one input each, the pool must move the right way: 7 of 7", "Noise: 5 irrelevant changes to the snapshot: 0.0 points moved", "Coherence: every ledger entry adds up and every difference is attributable", "Replay: entries under the current spec recompute exactly, from the analyst runs they name"], { fontSize: 12, color: C.text1 }), { x: M + 0.3, y: 4.9, w: 5.4, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
  card(s, 6.9, 4.3, 5.83, 2.4);
  text(s, "What it has already caught", { x: 7.2, y: 4.45, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["Four ledger entries stopped replaying after a model rule changed outside the hashed spec; amendment #5 put every rule inside the hash.", "A shock test was perturbing the wrong odds entry once two were on file; a red cell on the drift table pointed at it.", "Replay was reading the latest analyst runs instead of the runs the entry used; a rerun would have broken an honest entry. Fixed the same day, with a test.", "A verifier false positive (a zero written as 0 in the evidence); fixed, records re-scored without calling the model."], { fontSize: 11, color: C.text1 }), { x: 7.2, y: 4.9, w: 5.3, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
}
demo("Evidence", 5, "the scorecard and the drift table", 2,
  ["Scorecard view", "The snapshot dropdown: pick 24 October, then 26 October", "Expand 'what was checked' under Shock direction", "Scroll to the over-time table"],
  ["The grid: red in the control columns, green in the judged columns", "The seven shocks with their deltas", "The over-time table: one row per snapshot, the marks never move"],
  ["Analysts 1 and 2 are meant to fail. A red cell on the right would be a defect.", "This is the drift check. Two red cells have already pointed at defects and both are fixed."],
  "If time is short, skip the dropdown and go straight to the over-time table.");

demo("Evidence", 6, "the ledger and replay", 1,
  ["Ledger view", "Press Verify ledger"],
  ["Every entry with its snapshot hash, spec hash and code version", "The replay result: chain intact, entries under the current spec recompute exactly", "Eight numbered amendments, each with its reason, each a new spec hash pinned in the tests"],
  ["Nothing in this ledger can be edited or deleted without the chain breaking.", "Any entry can be recomputed from its snapshot. That is what auditable means here."],
  "One minute. Press the button, read the result line, move on.");

// =========================================================================================================
pres.addSection({ title: "Limits and next" });
{
  const s = light("Limits and next", "What comes next", "Six follow-ups, in order of value. One: alternative weightings written down now and scored on every live decision, so the weights stop being judgement. Two: reasoning quality graded by people in the app, which becomes the tenth measured dimension and a gate. Three: an events agent for the regime shifts the models cannot read. Four: a second model family to show the harness, not the model, does the work. Five: other central banks; the chain needs a calendar, a rate series, the statements and a curve, and the scorecard transfers unchanged. Six: better classical models, judged by the expanding window only.");
  text(s, "December is on file: entry #23 for the 9 December meeting, +25 bps 73.6%, no change 16.7%, specialists +4.0. The 28 October call is scored the moment the post-meeting rate row lands.", { x: M, y: 1.4, w: W - 2 * M, h: 0.4, fontSize: 11.5, color: C.accent4 });
  const next = [
    ["Alternative weightings, written down now, scored live", "Write down three or four alternative weightings now, for example market 0.6, 0.5 or 0.7 with the rest redistributed. The backtest can guide the split between Taylor and base rates; it cannot set the market share, since we hold no history of futures or prediction-market odds. Score every weighting on every live decision with the same log score and Brier. The live weighting changes only by amendment, on that record. Weights are never fitted to the past."],
    ["Reasoning quality, graded by people", "A grading form in the app: a user marks an analyst's answer from 1 to 5 on four questions (did it start from the base rate, argue both sides, say what it was unsure of, say what would prove it wrong). Twenty hand grades become the reference; a model grader is trusted only once it agrees with them. The grade becomes the tenth measured dimension and a gate on the opinion."],
    ["An events agent for regime shifts", "1987, 1998, 2008, 2020: the Fed cut on financial stress, not the data the models read. A watch-out agent that scans for bank failures, funding stress and market dislocations and raises a typed watch-out every analyst must answer."],
    ["A second model family", "The same harness, the same snapshots, a different language model. If the ladder reads the same, the harness is doing the work, not the model."],
    ["Other central banks and geographies", "ECB, Bank of England, MAS. The chain needs four things: a meeting calendar, a policy-rate series, the bank's own statements and minutes, and a futures or swap curve. The scorecard, the ledger and the analysts transfer unchanged; only the evidence sources change."],
    ["Better classical models", "Our probit scored poorly. The cause is the data: 68% of decisions are holds and the cuts bunch into a few episodes, so the model learns hold and misses the rest. Replace it with a model built for that imbalance (class weights, or an ordinal model that shrinks toward the base rate), tested only on decisions it has not seen. About 130 usable decisions, so small models."],
  ];
  next.forEach(([h, b], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.2, y = 1.95 + row * 1.6, w = 5.95;
    card(s, x, y, w, 1.45);
    numCircle(s, x + 0.2, y + 0.18, i + 1);
    text(s, h, { x: x + 0.75, y: y + 0.12, w: w - 0.95, h: 0.4, fontSize: 13, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: x + 0.2, y: y + 0.64, w: w - 0.4, h: 0.8, fontSize: 10, color: C.text1 });
  });
}
{
  const s = light("Limits and next", "Three things to take away", "1 MIN. Three lines, then the ask. One: the model's limits are designed around, not removed. Two: the engineering is in the chain around the model, not in the model. Three: the model lifts, the architecture decides whether the result can be trusted; judge the process. The ask: open the December entry, challenge a quote, grade an answer, pick the first follow-up. Questions.");
  const items = [
    ["Design around the model's limits", "It remembers: so it reads only the frozen evidence, and every number in its answer is matched to the snapshot. It varies: so it answers in a fixed shape, five times, and the spread is measured against a pass mark. It invents: so every claim carries a verbatim quote that code finds character for character, with one repair round. Nothing is removed. Everything is checked."],
    ["The engineering is in the harness", "The model is one component in a chain: frozen evidence, pre-reads computed by code, a fixed answer shape, a verifier, a bounded opinion, a pool at fixed weights, an append-only ledger. The chain decides what the model may read, what shape it must answer in, and what happens when it is wrong. Swap the model and the chain stands. Remove the chain and the same model wobbles and leaks."],
    ["Process is what you can judge", "The model does the heavy lifting: it reads the statements, the minutes and the transcript in a minute and comes back with quoted claims. The architecture decides whether that work can be trusted, repeated and replayed. Eight decisions a year cannot prove skill. A scorecard written before the first run and measured on every snapshot shows discipline and catches drift."],
  ];
  const cw = (W - 2 * M - 2 * 0.2) / 3;
  items.forEach(([h, b], i) => {
    const x = M + i * (cw + 0.2), y = 1.5;
    card(s, x, y, cw, 3.9);
    numCircle(s, x + 0.25, y + 0.25, i + 1);
    text(s, h, { x: x + 0.8, y: y + 0.22, w: cw - 1.0, h: 0.5, fontSize: 16, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: x + 0.25, y: y + 0.95, w: cw - 0.5, h: 2.85, fontSize: 14, color: C.text1 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.7, w: W - 2 * M, h: 0.75, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.1 });
  s.addText([{ text: "The ask. ", options: { bold: true, color: THEME.colors.accent6 } }, { text: "Open the app on the 9 December entry. Challenge a quote. Grade one analyst's answer. Tell us which of the six follow-ups to do first.", options: { color: THEME.colors.lt1 } }],
            { x: M + 0.3, y: 5.7, w: W - 2 * M - 0.6, h: 0.75, fontSize: 14, isTextBox: true, margin: 0, valign: "middle" });
}

// =========================================================================================================
pres.addSection({ title: "Backup" });
{
  const s = light("Backup", "Backup: the ladder, four snapshots, five runs each", "Read left to right as an evolution. Analyst 1 wobbles by three to five points between identical runs, cites nothing, and leaks three dozen numbers from memory; it still thinks the Fed is cutting. Adding the evidence (analyst 2) removes the leaks but not the wobble, and nothing can be checked. Adding the answer shape and the verifier (analyst 3) is the step that makes the output stable and fully verifiable. Specialists (4 to 8) keep that and add attribution. Same model, same day; the difference at each step is the one thing added.");
  const H_ = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const ok = t => ({ text: t, options: { color: THEME.colors.accent3, bold: true, align: "center" } });
  const bad = t => ({ text: t, options: { color: THEME.colors.accent2, bold: true, align: "center" } });
  const na = t => ({ text: t, options: { color: THEME.colors.accent4, align: "center" } });
  const rows = [
    [{ text: "Dimension (pass mark)", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, H_("Analyst 1: the question only"), H_("Analyst 2: + the evidence"), H_("Analyst 3: + answer shape + verifier"), H_("Analysts 4-8: + one slice each")],
    ["Repeatability (≤ 2 pp)\nlargest standard deviation of any outcome probability across 5 identical runs", bad("3.4 / 4.5 / 4.9 / 4.1 pp, fail"), bad("3.3 / 2.3 / 4.8 / 3.4 pp, fail"), ok("0.6 / 0.5 / 0.5 / 0.8 points, pass"), ok("0.5 / 0.8 / 1.2 / 0.8 points, pass")],
    ["Quotes verified (≥ 95%)\nshare of claims whose quote code found in the evidence", bad("0%, fail"), na("not measurable: no quotes"), ok("100 / 100 / 100 / 99%, pass"), ok("100 / 97 / 100 / 100%, pass")],
    ["Numbers from memory (exactly 0)\nnumbers in the answer that are not in the snapshot", bad("36 / 36 / 39 / 38, fail"), ok("0, pass"), ok("0, pass"), ok("0, pass")],
    ["What it concluded", na("Cut 25 bps at 57 to 67%: its memory of the Fed is stale"), na("+25 bps at 50 to 57%: reads the evidence, overshoots the market"), na("+7.0 / +6.6 / +6.4 / +5.8 hawkish"), na("+4.4 / +4.1 / +4.4 / +4.0 hawkish; labour the lone non-hawk")],
  ];
  s.addTable(rows, { x: M, y: 1.55, w: W - 2 * M, colW: [3.3, 2.2, 2.2, 2.2, 2.23], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.85 });
  text(s, "Snapshots of 15, 24, 26 and 28 October 2026. Analysts 3 to 8 report repeatability in points of their score because they output a score, not a distribution.", { x: M, y: 6.35, w: W - 2 * M, h: 0.5, fontSize: 10.5, color: C.accent4 });
}

{
  const s = light("Backup", "Appendix: how the analysts' score moves the number", "Three parts. The score: already in points of probability, capped at 10 like a human view. The average: one vote each. The spread: the points leave every bucket on the hold-or-cut side and land on both hike buckets, in proportion to size and distance from the middle, so the shape of the distribution is kept and nothing goes to zero.");
  // left: the score and the average
  card(s, M, 1.45, 5.9, 5.3);
  text(s, "1. The score", { x: M + 0.25, y: 1.55, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "Each specialist returns one number from −10 to +10: how many points of probability its evidence says should move toward a hike (positive) or a cut (negative). It is not a probability and not a rate forecast.",
    "Ten is the cap any single input has on the number, the same as a human view.",
  ], { fontSize: 10.5, color: C.text1, paraSpaceAfter: 4 }), { x: M + 0.25, y: 1.92, w: 5.4, h: 1.5, isTextBox: true, margin: 0, valign: "top" });
  text(s, "2. The average", { x: M + 0.25, y: 3.45, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "Five scores, one vote each, plain mean. 28 October: +6.0, +6.2, +5.8, +3.4, −1.4; mean +4.0.",
    "That mean is the number of points that must cross from the hold-or-cut side to the hike side. It is applied after the pool and the floor, by the same mechanism as a human view, and the pool before it is always recorded beside the result.",
  ], { fontSize: 10.5, color: C.text1, paraSpaceAfter: 4 }), { x: M + 0.25, y: 3.82, w: 5.4, h: 1.5, isTextBox: true, margin: 0, valign: "top" });
  text(s, "3. The spread, in words", { x: M + 0.25, y: 5.35, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  text(s, "Number the five outcomes −2, −1, 0, +1, +2 from most dovish to most hawkish. Multiply each bucket by e raised to (steepness × its number), then rescale so the five sum to one. Code searches for the one steepness at which exactly the mean score's points cross the line; on 28 October it was 0.153. Each bucket moves in proportion to its own size and its distance from the middle, so no bucket is zeroed and the shape is kept.", { x: M + 0.25, y: 5.72, w: 5.4, h: 1.0, fontSize: 10, color: C.text1 });
  // right: the worked example
  const rx = M + 6.15, rw = W - M - rx;
  text(s, "28 October, entry #18: mean score +4.0", { x: rx, y: 1.5, w: rw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  const H_ = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const c = (t, bold, col) => ({ text: t, options: { align: "center", bold: !!bold, color: col || THEME.colors.dk1 } });
  const rows = [
    [{ text: "Outcome", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, H_("Pooled, before"), H_("Multiplier"), H_("After"), H_("Change")],
    ["−50 bps", c("1.50"), c("× 0.70"), c("1.05"), c("−0.45", false, THEME.colors.accent2)],
    ["−25 bps", c("1.50"), c("× 0.82"), c("1.23"), c("−0.27", false, THEME.colors.accent2)],
    ["no change", c("70.86"), c("× 0.95"), c("67.58"), c("−3.28", false, THEME.colors.accent2)],
    ["+25 bps", c("20.17"), c("× 1.11"), c("22.41"), c("+2.24", false, THEME.colors.accent3)],
    ["+50 bps", c("5.97"), c("× 1.29"), c("7.73"), c("+1.76", false, THEME.colors.accent3)],
    [{ text: "Hold-or-cut side", options: { bold: true } }, c("73.86", true), c(""), c("69.86", true), c("−4.00", true, THEME.colors.accent2)],
    [{ text: "Hike side", options: { bold: true } }, c("26.14", true), c(""), c("30.14", true), c("+4.00", true, THEME.colors.accent3)],
  ];
  s.addTable(rows, { x: rx, y: 1.95, w: rw, colW: [1.7, 1.3, 1.1, 1.1, 1.08], fontSize: 11, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.05, rowH: 0.42 });
  text(s, "Multiplier = e^(0.153 × position) ÷ 1.0486, where position is −2, −1, 0, +1, +2 and 1.0486 is what the five re-weighted buckets add up to before rescaling. Exactly 4.00 points crossed; the after column is the machine forecast recorded as entry #18.", { x: rx, y: 5.45, w: rw, h: 1.2, fontSize: 10, color: C.accent4 });
}
{
  const s = light("Backup", "Appendix: the ordered probit, and why it sits at weight 0", "The quant side's own test. A first ordered probit, spec frozen before fitting, failed its out-of-sample gate and was reported, not tuned. A second version beats the base rate on the expanding window but was specified after seeing the first fail, so it carries a contamination caveat and waits for live decisions. The base rates, which need no fitting, beat the fitted model and are the yardstick. Below: why no gradient-boosted anything.");
  card(s, M, 1.45, 5.9, 5.3);
  text(s, "What it is", { x: M + 0.25, y: 1.55, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "An ordered probit: the decision (cut, hold, hike) as a function of signals, with two cutpoints. Fitted on every scheduled decision since August 2000, each read with the data as first published (ALFRED vintages), never today's revised figures.",
    "Version 1, seven features (inflation gap and momentum, unemployment and its 12-month change, payrolls, the 2-year yield gap, the previous decision). Spec frozen before fitting; single split at 2018. Result: log score −1.14 against −0.71 for a base rate. Failed, reported as such.",
    "Version 2 adds two features (at the zero bound; the streak of same-direction moves) and shrinks 50% toward the base rate. Written after seeing v1 fail, so its score on 2018 onward is optimistic: a declared contamination caveat.",
    "Weight 0 until live decisions judge it. Computed and shown on every snapshot, never hidden.",
  ], { fontSize: 10.5, color: C.text1, paraSpaceAfter: 5 }), { x: M + 0.25, y: 1.92, w: 5.4, h: 4.7, isTextBox: true, margin: 0, valign: "top" });
  const rx = M + 6.15, rw = W - M - rx;
  text(s, "The gate: expanding window, 129 decisions since 2010", { x: rx, y: 1.5, w: rw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  const H_ = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const c = (t, col) => ({ text: t, options: { align: "center", color: col || THEME.colors.dk1 } });
  const rows = [
    [{ text: "Candidate", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, H_("Log score, all"), H_("2010 to 2017"), H_("2018 on"), H_("Accuracy")],
    ["Base rate, unconditional", c("−0.744"), c("−0.550"), c("−0.918"), c("77%")],
    [{ text: "Base rate given the previous decision", options: { bold: true, color: THEME.colors.accent3 } }, c("−0.584", THEME.colors.accent3), c("−0.449", THEME.colors.accent3), c("−0.704", THEME.colors.accent3), c("81%", THEME.colors.accent3)],
    [{ text: "Probit v1", options: { color: THEME.colors.accent2 } }, c("−0.788", THEME.colors.accent2), c("−0.293", THEME.colors.accent2), c("−1.232", THEME.colors.accent2), c("78%", THEME.colors.accent2)],
    ["Probit v2 (caveated)", c("−0.469"), c("−0.353"), c("−0.572"), c("80%")],
  ];
  s.addTable(rows, { x: rx, y: 1.95, w: rw, colW: [2.4, 1.1, 1.1, 1.0, 0.68], fontSize: 10.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.05, rowH: 0.42 });
  text(s, "For each decision from 2010 on: fit on all decisions before it, predict it. Log score: ln of the probability given to what happened (0 is perfect). The base rate given the previous decision beat the fitted model and joined the pool at 0.1 (amendment #6).", { x: rx, y: 4.15, w: rw, h: 0.75, fontSize: 10, color: C.accent4 });
  text(s, "Why not a bigger model", { x: rx, y: 4.95, w: rw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  text(s, "About 130 scheduled decisions with full features, roughly 250 in all; 68% are holds and the cuts cluster in three short episodes. On a sample that small and that unbalanced a boosted tree or a random forest memorises the episodes and a calibration curve on a few dozen non-hold cases is noise. The route is a better-specified small model: features written down before fitting, heavy regularisation, a reliability check beside the log score, the expanding window as the only judge. A regularised boosted model can be one pre-registered candidate, judged the same way.", { x: rx, y: 5.3, w: rw, h: 1.45, fontSize: 10, color: C.text1 });
}

{
  const s = light("Backup", "Appendix: historical base rates", "The simplest model in the pool and the only one with no parameters. Take every scheduled decision since 1994, group them by what the Fed had done at the previous meeting, and count what it did next. That count is the forecast. After a hike the Fed hiked again at two meetings in three and never cut; after a hold it held 85% of the time; after a cut it cut again two times in three and never hiked. It beat the fitted probit on the expanding-window test, which is why it is in the pool at 0.1.");
  card(s, M, 1.45, 5.9, 5.3);
  text(s, "What it is", { x: M + 0.25, y: 1.55, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "The simplest model in the pool, and the only one with no parameters: nothing is fitted, nothing can be tuned.",
    "Take the 266 scheduled decisions since 1994. Group them by what the Fed had done at the previous meeting: a hike, a hold or a cut. Count what it did next. That count is the forecast.",
    "Today the last decision was a hike, so the model reads the 49 meetings that followed a hike: hold 35%, hike 65%. The hike share is split 80/20 between +25 and +50, the historical share of large moves.",
    "Why it is in the pool: on the expanding-window test it beat the fitted probit (log score −0.584 against −0.788), so it earned 0.1 (amendment #6). Why not more: it knows nothing about today; it is the prior the other models update.",
    "Intermeeting moves (28 since 1994) are counted separately and never as a scheduled decision.",
  ], { fontSize: 10.5, color: C.text1, paraSpaceAfter: 5 }), { x: M + 0.25, y: 1.92, w: 5.4, h: 4.7, isTextBox: true, margin: 0, valign: "top" });
  const rx = M + 6.15, rw = W - M - rx;
  text(s, "What the Fed did next, 266 scheduled meetings since 1994", { x: rx, y: 1.5, w: rw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  const H_ = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const c = (t, col, bold) => ({ text: t, options: { align: "center", color: col || THEME.colors.dk1, bold: !!bold } });
  const rows = [
    [{ text: "Previous decision", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, H_("Cases"), H_("Next: cut"), H_("Next: hold"), H_("Next: hike")],
    [{ text: "A hike (today's case)", options: { bold: true } }, c("50", null, true), c("0%", null, true), c("36%", null, true), c("64%", THEME.colors.accent2, true)],
    ["A hold", c("183"), c("6%"), c("85%", THEME.colors.accent3), c("9%")],
    ["A cut", c("32"), c("66%", THEME.colors.accent3), c("34%"), c("0%")],
    [{ text: "All decisions", options: { color: THEME.colors.accent4 } }, c("266", THEME.colors.accent4), c("12%", THEME.colors.accent4), c("69%", THEME.colors.accent4), c("19%", THEME.colors.accent4)],
  ];
  s.addTable(rows, { x: rx, y: 1.95, w: rw, colW: [2.1, 1.0, 1.05, 1.05, 1.08], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.05, rowH: 0.46 });
  text(s, "Read the first row: of the 50 meetings that came right after a hike, the Fed hiked again at 32 and held at 18; it never cut straight after a hike. The pool uses the 49 cases known at the time of the 28 October snapshot.", { x: rx, y: 4.4, w: rw, h: 0.9, fontSize: 10.5, color: C.accent4 });
  text(s, "Why a prior matters", { x: rx, y: 5.35, w: rw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  text(s, "The Fed moves in runs. A hike is usually followed by another hike, a cut by another cut, and a hold by a hold. Any forecast that ignores this starts from the wrong place; the base rate is the place to start, and the market, the rules and the analysts move it from there.", { x: rx, y: 5.7, w: rw, h: 1.0, fontSize: 10.5, color: C.text1 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
