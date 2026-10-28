const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(String.raw`C:\Users\tan_k\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\local-agent-mode-sessions\skills-plugin\ca9dbd77-06d9-4224-b79b-84131dcbdd53\1cf79891-da1f-46df-a0de-7e44b570a773\skills\pptx\scripts\apply_theme.js`);

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

// =========================================================================================================
pres.addSection({ title: "Objective" });
{
  const s = light("Objective", "The question, and today's answer", "The question is narrow on purpose: what will the FOMC decide at its next scheduled meeting, as probabilities over five outcomes. Today's answer is on the left. On the right is the point: the market alone says 90/10; the system says 71/23 and can show every step from evidence to that number.");
  stat(s, M, 1.7, 3.6, "28 Oct 2026", "the decision being forecast");
  stat(s, 4.5, 1.7, 3.2, "71%", "no change", C.text2);
  stat(s, 7.6, 1.7, 3.2, "23%", "+25 bps hike", THEME.colors.accent2);
  stat(s, 10.6, 1.7, 2.3, "6%", "the other three outcomes together");
  card(s, M, 3.7, W - 2 * M, 2.9);
  text(s, "Where the number comes from", { x: M + 0.4, y: 3.9, w: 6, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  s.addText(bullets([
    "One frozen snapshot of 22 evidence items, pulled 26 October: futures, eight FRED series, both statements, minutes, transcript, projections, speeches, 32 years of decisions, prediction-market odds",
    "Four models pooled by code with fixed weights: market-implied 0.6, the Fed's own Taylor rules 0.2, prediction-market odds 0.1, historical base rates 0.1; then a 1.5% floor on every outcome",
    "Five specialist analysts (a language model, tools off, every claim quoted and verified) lean the pooled number by a bounded 4.4 points toward a hike",
    "Ledger entry #16, hash-chained, replays exactly from its snapshot",
  ], { fontSize: 13.5, color: C.text1 }), { x: M + 0.4, y: 4.35, w: W - 2 * M - 0.8, h: 2.2, isTextBox: true, margin: 0, valign: "top" });
}
demo("Objective", 1, "the forecast", 1,
  ["The app at localhost:8765, Forecast view", "Top bar: when the evidence was pulled, what is new at the sources"],
  ["The two tracks side by side: machine only, and with views", "The meta line: ledger entry, snapshot hash, the specialists' tilt", "The five bars"],
  ["This number was made at <time> from evidence frozen at <time>. Everything I show next is how it got there."],
  "Keep this to one minute. The point is only that the number exists, is dated, and is traceable. Do not explain the models yet.");
{
  const s = light("Objective", "Why build this", "Three reasons. First, accuracy is the wrong yardstick at this horizon: eight decisions a year, and the market already gets most of them right, so a good year proves nothing. Second, what a desk can use is a number whose every input it can see and challenge. Third, the harness is the asset: the same machine can target the December meeting, the year-end rate, or a different central bank, and the controls tell you whether it is still working.");
  const cards = [
    ["1", "Judge the process, not the luck", "Eight decisions a year is far too few to tell skill from chance. So the yardstick is a ten-dimension scorecard fixed before any code existed: repeatability, groundedness, leakage, directional sanity, noise invariance, coherence, auditability and more. Outcomes are logged and never used to tune."],
    ["2", "A number you can audit", "Every forecast runs on one fingerprinted snapshot. Every model lists the items it read. Every analyst claim carries a verbatim quote that code has matched. Every entry in the ledger recomputes exactly from its snapshot. Nothing moves the number silently."],
    ["3", "A harness that transfers", "The decision is the first target, not the only one. The same chain can forecast the December meeting, the year-end rate, or another central bank, and the control analysts measure whether the language model is still earning its place."],
  ];
  cards.forEach(([n, h, b], i) => {
    const x = M + i * 4.1; card(s, x, 1.7, 3.85, 4.0);
    numCircle(s, x + 0.3, 1.95, n);
    text(s, h, { x: x + 0.3, y: 2.5, w: 3.3, h: 0.7, fontSize: 17, bold: true, color: C.text2 });
    text(s, b, { x: x + 0.3, y: 3.25, w: 3.3, h: 2.35, fontSize: 14, color: C.text1 });
  });
}
{
  const s = light("Objective", "What others do, and what each lacks", "The honest comparison. At thirty days the futures market, read through CME FedWatch, calls about 88% of decisions right over thirty years, and nothing here claims to beat that. The academic LLM papers report higher accuracy but on sixteen meetings, with no replay and no verification of what the model read. The gap we fill is the right-hand column: not a better guess, a checkable one.");
  const rows = [
    [{ text: "Predictor", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it is", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Strength", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it lacks", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }],
    ["Fed funds futures (CME FedWatch)", "Price of the contract that settles on the month's average rate", "About 88% right at 30 days over 1994 to 2024 (Bonini, Huang, Simaan). The anchor of our pool", "No reasons. One number with no evidence trail; fails silently when the Fed surprises"],
    ["Prediction markets (Polymarket, Kalshi)", "Crowd odds on each outcome", "Independent crowd; fast to move", "Thin and fee-distorted; a $22 entry can sit next to a $67m one"],
    ["Economist surveys", "Median of polled forecasters", "Human judgement, broad", "Slow, unauditable, consensus-seeking"],
    ["Policy rules (Taylor family)", "Rate a formula says is appropriate", "Transparent, the Fed's own benchmarks", "Depends on unobservable r* and u*; says where rates should be, not what the committee will do"],
    ["LLM 'FOMC agent' papers (2025)", "Models that read Fed text and vote", "Reported 90%+ accuracy on 2023 to 2024", "16 meetings; no frozen evidence, no quote verification, no replay, no control"],
    [{ text: "FedCast", options: { bold: true, color: C.text2 } }, "All of the above pooled by code, plus verified analysts", "Every number traceable; repeatable; a scorecard that catches drift", "No live record yet; no accuracy claim at five weeks"],
  ];
  s.addTable(rows, { x: M, y: 1.55, w: W - 2 * M, colW: [2.6, 2.9, 3.2, 3.43], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.62 });
  text(s, "Sources: Bonini, Huang and Simaan, 'Watching the FedWatch' (232 meetings, May 1994 to March 2024); FedSight AI preprint, December 2025; Takano, Hirano and Nakagawa, arXiv 2511.02469.", { x: M, y: 6.45, w: W - 2 * M, h: 0.4, fontSize: 9.5, color: C.accent4 });
}
{
  const s = light("Objective", "Our edge: not a better guess, a checkable one", "Four properties, each enforced by code, each measured. Say them slowly; they are the whole design.");
  const items = [
    ["Frozen evidence", "One fingerprinted snapshot per forecast, dated in US time, data as first published. No internet, no memory. If it is not in the snapshot, nothing may read it."],
    ["Code computes, models read, code checks", "Arithmetic is done by code. The language model is used only for reading text, and every claim it makes must quote a snapshot item; code string-matches the quote and flags any number not in the evidence."],
    ["Human judgement through typed channels", "Views tilt the number by a capped amount and expire. Watch-outs must be answered by id. Documents and odds enter as evidence. Nothing nudges the number quietly."],
    ["Pre-registered, amended in the open, replayable", "The scorecard, weights, floor and every model rule are hashed and pinned in the tests. Seven logged amendments. Every ledger entry recomputes from its snapshot."],
  ];
  items.forEach(([h, b], i) => {
    const x = M + (i % 2) * 6.2, y = 1.65 + Math.floor(i / 2) * 2.55;
    card(s, x, y, 5.95, 2.3);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.3, w: 0.5, h: 0.5, fill: { color: THEME.colors.accent6 }, line: { color: THEME.colors.accent6 } });
    text(s, h, { x: x + 1.0, y: y + 0.28, w: 4.7, h: 0.55, fontSize: 16, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: x + 0.3, y: y + 0.95, w: 5.4, h: 1.3, fontSize: 12.5, color: C.text1 });
  });
}

// =========================================================================================================
pres.addSection({ title: "How it works" });
{
  const s = light("How it works", "One chain, left to right", "Blue boxes are code and deterministic. The orange box is the language model, which may lean the number but never writes it. The green box is the human. Walk it left to right; every box is a view in the app.");
  const boxes = [
    ["Evidence", "22 frozen items", THEME.colors.dk2], ["Signals", "inflation, labour, financial, tone, base rates, projections", THEME.colors.dk2],
    ["Models", "market, Taylor rules, odds, base rates, probit", THEME.colors.dk2], ["Pool", "fixed weights, 1.5% floor", THEME.colors.dk2],
    ["Analysts", "5 specialists, bounded tilt", THEME.colors.accent2], ["You", "views, watch-outs, documents, odds", THEME.colors.accent3],
    ["Ledger", "hash-chained, replays exactly", THEME.colors.dk2],
  ];
  const bw = 1.62, gap = 0.17, y = 2.4;
  boxes.forEach(([h, b, col], i) => {
    const x = M + i * (bw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 2.0, fill: { color: col }, line: { color: col }, rectRadius: 0.1 });
    text(s, h, { x: x + 0.12, y: y + 0.15, w: bw - 0.24, h: 0.5, fontSize: 15, bold: true, color: C.background1, align: "center" });
    text(s, b, { x: x + 0.12, y: y + 0.7, w: bw - 0.24, h: 1.2, fontSize: 11, color: C.background1, align: "center" });
    if (i < boxes.length - 1) s.addShape(pres.shapes.RIGHT_TRIANGLE, { x: x + bw + 0.03, y: y + 0.93, w: 0.11, h: 0.14, fill: { color: THEME.colors.accent4 }, line: { color: THEME.colors.accent4 }, rotate: 0 });
  });
  const legend = [["Code, deterministic", THEME.colors.dk2], ["Language model, bounded", THEME.colors.accent2], ["Human, typed channels", THEME.colors.accent3]];
  legend.forEach(([t, col], i) => { s.addShape(pres.shapes.RECTANGLE, { x: M + i * 3.6, y: 4.9, w: 0.3, h: 0.3, fill: { color: col }, line: { color: col } }); text(s, t, { x: M + i * 3.6 + 0.4, y: 4.9, w: 3, h: 0.3, fontSize: 12, color: C.text1, valign: "middle" }); });
  text(s, "Signals are computed, not asked: the analysts are handed the numbers code has already worked out. Everything a model could compute, code computes. The language model reads the words.", { x: M, y: 5.6, w: W - 2 * M, h: 0.9, fontSize: 13, color: C.accent4, italic: true });
}
{
  const s = light("How it works", "Today's readings: from five models to one number", "This is the arithmetic for entry 16. The pool is a weighted average, then the floor. The specialists' mean lean of +4.4 basis points becomes 4.4 points of probability moved toward a hike, through the same capped mechanism a human view uses.");
  const hdr = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const r = (a, b, c, d, e, f, g, bold) => [{ text: a, options: { bold: !!bold } }, { text: b, options: { fontSize: 10.5 } }, ...[c, d, e, f, g].map(v => ({ text: v, options: { align: "center", bold: !!bold } }))];
  const rows = [
    [{ text: "Model", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, hdr("−25"), hdr("no change"), hdr("+25"), hdr("+50"), hdr("weight")],
    r("Market-implied", "November fed-funds future against the overnight rate: +2.5 bp expected", "0", "90", "10", "0", "0.6"),
    r("Taylor family", "12-month core PCE 3.0%, unemployment 4.2%, four rules × nine r*/u* pairs", "9", "44", "40", "7", "0.2"),
    r("Prediction market", "Polymarket, 26 Oct, $67m traded", "0", "95", "4.5", "0", "0.1"),
    r("Historical base rates", "What followed a hike at the 49 meetings since 1994 that came after one", "0", "35", "52", "13", "0.1"),
    r("Pooled", "Weighted average, then the 1.5% floor", "1.8", "74.7", "19.4", "2.6", "", true),
    r("Specialists' tilt", "+4.4 bp hawkish, mean of five: 4.4 points moved toward the hike outcomes", "", "", "", "", ""),
    r("Machine forecast", "Ledger entry #16", "1.4", "71.3", "22.6", "3.8", "", true),
  ];
  s.addTable(rows, { x: M, y: 1.55, w: W - 2 * M, colW: [2.1, 4.63, 0.9, 1.3, 0.9, 0.9, 1.4], fontSize: 12, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.52 });
  text(s, "Percentages, rounded. The ordered probit is computed and shown but carries weight 0 until it has a live record.", { x: M, y: 6.1, w: W - 2 * M, h: 0.4, fontSize: 11, color: C.accent4 });
}

demo("How it works", 2, "the evidence graph and the pool", 3,
  ["Evidence graph", "Click the Market-implied box", "Click the Pool box", "Methodology, scroll to the worked example"],
  ["Market-implied: the futures price, 100 minus price, the expected change, the 90/10 split", "Pool: the four weights, the pooled line, the specialists' tilt line, machine_only", "Any evidence item: the frozen text and the link to the original"],
  ["Blue is in the number, grey is computed but not in it. Click a model and you see only what it read.", "The language model's lean is the one line between pooled and machine_only. It can tilt, it cannot write."],
  "This is the longest demo. Start at the raw futures price so the audience sees arithmetic, not a black box. Then the pool box, then one click into an evidence item to show the frozen text.");

// =========================================================================================================
pres.addSection({ title: "The harness" });
{
  const s = light("The harness", "Eight analysts, one model, one ladder", "This is the slide that explains what harnessing means. The same model is run eight ways on the same snapshot. Analyst 1 gets nothing but the question: that is what the model does on its own, the control. Each step up adds exactly one thing, so the score difference between neighbouring steps is the value of that thing. Analysts 1 and 2 are meant to fail; the tool is judged on 3 and 4 to 8.");
  const steps = [
    ["1", "Analyst 1: naive", "The question and the date. Nothing else.", "What the model does on its own. The control every later step is measured against.", THEME.colors.accent4],
    ["2", "Analyst 2: evidence shown, nothing verified", "Every document and every pre-computed number, 128,000 characters. Free-form answer.", "Adds the evidence. Shows what evidence alone fixes, and what it does not.", THEME.colors.accent4],
    ["3", "Analyst 3: generalist with verifier", "Same evidence, but a fixed answer shape: a verbatim quote per claim, a watch-out report, a tilt capped at ±10 bp. Code checks every quote and number.", "Adds structure and verification. This is where the output becomes stable and checkable.", THEME.colors.dk2],
    ["4-8", "Analysts 4 to 8: specialists", "One slice each: communications, minutes, inflation, labour, financial conditions. Same schema, same verifier.", "Adds specialisation. Each judgement is attributable to its evidence; a dissent survives instead of being averaged away.", THEME.colors.accent2],
  ];
  steps.forEach(([a, h, gets, adds, col], i) => {
    const y = 1.55 + i * 1.27;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y, w: 0.9, h: 1.1, fill: { color: col }, line: { color: col }, rectRadius: 0.1 });
    text(s, a, { x: M, y, w: 0.9, h: 1.1, fontSize: a.length > 1 ? 22 : 30, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: THEME.headFontFace });
    text(s, h, { x: M + 1.1, y: y + 0.02, w: 4.0, h: 0.5, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
    text(s, gets, { x: M + 1.1, y: y + 0.5, w: 4.0, h: 0.65, fontSize: 10.5, color: C.text1 });
    text(s, adds, { x: 6.0, y: y + 0.1, w: 6.7, h: 0.95, fontSize: 12.5, color: C.text1, valign: "middle" });
  });
  text(s, "Each step adds one thing. The value of that thing is the difference in score between neighbouring steps.", { x: M, y: 6.65, w: W - 2 * M, h: 0.35, fontSize: 12, italic: true, color: C.accent4 });
}
{
  const s = light("The harness", "What the harness enforces around every analyst", "Five mechanisms. None of them is clever; together they are what makes a language model's output usable in a forecast.");
  const items = [
    ["Tools off, slice only", "The model sees its slice of the frozen snapshot and nothing else: no browsing, no memory of the Fed, no other analyst's output."],
    ["Pre-reads", "Numbers are computed by code and handed over: inflation gap, labour slack, financial conditions, tone, base rates. The model never does arithmetic."],
    ["Fixed answer shape", "Claims, each with a verbatim quote and the item it came from; a report on every watch-out by id; a tilt bounded to ±10 basis points. Enforced by the runtime."],
    ["Code verifies", "Every quote is string-matched to its item. Every number is matched to the snapshot. Every watch-out must be answered. Failures are counted, never hidden."],
    ["Recorded and repeated", "Five identical runs per analyst per snapshot, each stored with its prompt hash. Repeatability is measured, and a recorded run replays for free."],
  ];
  items.forEach(([h, b], i) => {
    const y = 1.55 + i * 1.02;
    numCircle(s, M, y + 0.1, i + 1);
    text(s, h, { x: M + 0.65, y, w: 3.4, h: 0.6, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: 4.4, y: y + 0.02, w: 8.3, h: 0.9, fontSize: 12.5, color: C.text1, valign: "middle" });
  });
}

demo("The harness", 3, "what each analyst is asked and given", 2,
  ["Analyst prompts view", "Analyst 1: open the full prompt", "Analyst 6: open the full prompt"],
  ["Analyst 1: 195 characters, no evidence", "Analyst 6: the system prompt, the enforced answer schema, the inflation pre-read, the item ids", "The prompt hash: five repeats share it"],
  ["If it is not on this page, the analyst does not get it.", "Same model. The only difference between analyst 1 and analyst 6 is this page."],
  "Open analyst 1 first so the contrast with analyst 6 lands. Scroll the full prompt slowly past the schema and the pre-read; do not read it out.");

// =========================================================================================================
pres.addSection({ title: "Evidence" });
{
  const s = light("Evidence", "The ladder, four snapshots, five runs each", "Read left to right as an evolution. Analyst 1 wobbles by three to five points between identical runs, cites nothing, and leaks three dozen numbers from memory; it still thinks the Fed is cutting. Adding the evidence (analyst 2) removes the leaks but not the wobble, and nothing can be checked. Adding the answer shape and the verifier (analyst 3) is the step that makes the output stable and fully verifiable. Specialists (4 to 8) keep that and add attribution. Same model, same day; the difference at each step is the one thing added.");
  const H_ = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const ok = t => ({ text: t, options: { color: THEME.colors.accent3, bold: true, align: "center" } });
  const bad = t => ({ text: t, options: { color: THEME.colors.accent2, bold: true, align: "center" } });
  const na = t => ({ text: t, options: { color: THEME.colors.accent4, align: "center" } });
  const rows = [
    [{ text: "Dimension (pass mark)", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, H_("Analyst 1: the question only"), H_("Analyst 2: + the evidence"), H_("Analyst 3: + answer shape + verifier"), H_("Analysts 4-8: + one slice each")],
    ["S1 Repeatability (≤ 2 pp)\nmax move of any probability across 5 identical runs", bad("3.4 / 4.5 / 4.9 / 4.1 pp, fail"), bad("3.3 / 2.3 / 4.8 / 3.4 pp, fail"), ok("0.6 / 0.5 / 0.5 / 0.8 bp of tilt, pass"), ok("0.5 / 0.8 / 1.2 / 0.8 bp of tilt, pass")],
    ["S2 Groundedness (≥ 95%)\nshare of claims whose quote code found in the evidence", bad("0%, fail"), na("not measurable: no quotes"), ok("100 / 100 / 100 / 99%, pass"), ok("100 / 97 / 100 / 100%, pass")],
    ["S3 Leakage (exactly 0)\nnumbers in the answer that are not in the snapshot", bad("36 / 36 / 39 / 38, fail"), ok("0, pass"), ok("0, pass"), ok("0, pass")],
    ["What it concluded", na("Cut 25 bps at 57 to 67%: its memory of the Fed is stale"), na("+25 bps at 50 to 57%: reads the evidence, overshoots the market"), na("+7.0 / +6.6 / +6.4 / +5.8 bp hawkish"), na("+4.4 / +4.1 / +4.4 / +4.0 bp hawkish; labour the lone non-hawk")],
  ];
  s.addTable(rows, { x: M, y: 1.55, w: W - 2 * M, colW: [3.3, 2.2, 2.2, 2.2, 2.23], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.85 });
  text(s, "Snapshots of 15, 24, 26 and 28 October 2026. Analysts 3 to 8 report S1 in basis points of tilt because they output a lean, not a distribution.", { x: M, y: 6.35, w: W - 2 * M, h: 0.5, fontSize: 10.5, color: C.accent4 });
}
{
  const s = light("Evidence", "What each step bought", "Three charts, one per dimension, averaged over the four snapshots. Left: how much the answer moves between identical runs. The step that matters is analyst 2 to analyst 3: the answer shape and the verifier take the wobble from three and a half points to under one. Middle: numbers from memory, gone as soon as the evidence is shown. Right: share of claims whose quote code found verbatim; analyst 2 cannot be measured because it quotes nothing. The specialists keep what analyst 3 achieved. For analysts 3 to 8 the wobble is in their lean, which maps one basis point to one percentage point of probability, so the four bars are comparable.");
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
  chart("S1: wobble between identical runs (pp)", cats, [4.2, 3.5, 0.6, 0.8], M, 5,
        "Largest standard deviation across five runs, mean of four snapshots. Pass mark 2 pp. Analysts 3 to 8: standard deviation of the lean, 1 bp = 1 pp.");
  chart("S3: numbers from memory (count)", cats, [37, 0, 0, 0], M + cw + 0.25, 40,
        "Numbers in the answer that exist nowhere in the frozen evidence, summed over five runs. Pass mark: exactly 0.", "0");
  chart("S2: claims with a verbatim quote (%)", ["1: question only", "3: + shape, verifier", "4-8: + one slice each"], [0, 99.7, 99.2], M + 2 * (cw + 0.25), 100,
        "Share of claims whose quote code found character for character in the item named. Pass mark 95%. Analyst 2 is not shown: it quotes nothing, so it cannot be measured.");
  text(s, "The step from analyst 2 to analyst 3 is the harness: a fixed answer shape with a quote per claim, checked by code. It is the step that makes the model repeatable and checkable. Specialists keep both and add attribution.", { x: M, y: 6.55, w: W - 2 * M, h: 0.45, fontSize: 11.5, italic: true, color: C.accent2 });
}
{
  const s = light("Evidence", "What the specialists said on 26 October", "Make it concrete. Each specialist's lean, and one real claim with the quote code matched. The labour analyst is the one that does not lean hawkish, and because it is a separate reader that dissent is visible rather than averaged away.");
  const rows = [
    [{ text: "Analyst", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Lean (5 runs)", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }, { text: "Verified", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }],
    ["4 Communications", "Both statements, minutes, transcript, speeches, tone pre-read", { text: "+6.0 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["5 Minutes digest", "The minutes only", { text: "+6.6 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["6 Inflation", "Inflation pre-read, projections, both statements", { text: "+6.4 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["7 Labour market", "Labour pre-read, projections, both statements", { text: "−0.4 bp, neutral", options: { align: "center", color: THEME.colors.accent3, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
    ["8 Financial conditions", "Financial pre-read, base rates, both statements", { text: "+3.4 bp hawkish", options: { align: "center", color: THEME.colors.accent2, bold: true } }, { text: "100%, 0 leaked", options: { align: "center" } }],
  ];
  s.addTable(rows, { x: M, y: 1.55, w: 7.4, colW: [1.9, 3.0, 1.4, 1.1], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.06, rowH: 0.55 });
  card(s, 8.4, 1.55, 4.33, 3.75);
  text(s, "One claim, as recorded", { x: 8.7, y: 1.75, w: 3.8, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  text(s, "Communications analyst: the deterministic tone read scores the most recent policy communication as fully hawkish, with a unanimous hike vote and no dovish lexicon hits.", { x: 8.7, y: 2.2, w: 3.8, h: 1.1, fontSize: 12, color: C.text1 });
  text(s, "Quote: \"score\": 1.0   Item: signal.tone   Verified by code", { x: 8.7, y: 3.3, w: 3.8, h: 0.55, fontSize: 11, color: C.accent4, fontFace: "Courier New" });
  text(s, "The pre-read is our arithmetic over the two statements: 12 votes for, none against, eight hawkish words, no dovish ones. The analyst quoted it and code found the quote.", { x: 8.7, y: 3.9, w: 3.8, h: 1.3, fontSize: 11, color: C.text1 });
}
demo("Evidence", 4, "what the analysts concluded", 2,
  ["Analyst results view", "Analyst 1 (naive) card", "Analyst 4 (communications) card"],
  ["Analyst 1: cut 25 at 57%, numbers from memory flagged", "Analyst 4: the lean, grounded, leaked, watch-outs badges; one claim with its quote and the 'quote verified' mark", "Hover a badge for its definition"],
  ["Every claim you see has a quote that code found character for character in the item named.", "The naive analyst still thinks the Fed is cutting. Same model, no evidence."],
  "Pick the signal.tone claim on analyst 4 if asked where a quote comes from: it is the pre-read, our arithmetic over the two statements.");
{
  const s = light("Evidence", "The scorecard: eight of ten dimensions measured by code", "Ten dimensions fixed before any forecasting code existed. Eight are now measured automatically on each new snapshot. The over-time table is the drift check: the marks never move, so a cell that turns red is a change in the system. It has already caught two things, bottom right.");
  const dims = [
    ["S1", "Repeatability", true], ["S2", "Groundedness", true], ["S3", "Leakage", true], ["S4", "Directional sanity", true], ["S5", "Noise invariance", true],
    ["S6", "Paraphrase stability", "part"], ["S7", "Coherence", true], ["S8", "Reasoning quality", false], ["S9", "Auditability", true], ["S10", "Human-input discipline", true],
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
  text(s, "Measured by code on the 26 October snapshot", { x: M + 0.3, y: 4.45, w: 5.4, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["S4: 7 shocks, one input each, the pool must move the right way: 7 of 7", "S5: 5 irrelevant changes to the snapshot: 0.0 points moved", "S7: all 17 ledger entries coherent and attributable", "S9: entries under the current spec recompute exactly: 3 of 3"], { fontSize: 12, color: C.text1 }), { x: M + 0.3, y: 4.9, w: 5.4, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
  card(s, 6.9, 4.3, 5.83, 2.4);
  text(s, "What it has already caught", { x: 7.2, y: 4.45, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["Four ledger entries stopped replaying after a model rule changed outside the hashed spec. Amendment #5 put every rule inside the hash; earlier entries are now labelled, not failed.", "A shock test was perturbing the wrong odds entry once two were on file. A red cell on the drift table pointed straight at it; fixed with a unit test the same hour."], { fontSize: 12, color: C.text1 }), { x: 7.2, y: 4.9, w: 5.3, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
}
demo("Evidence", 5, "the scorecard and the drift table", 2,
  ["Scorecard view", "The snapshot dropdown: pick 24 October, then 26 October", "Expand 'what was checked' under S4", "Scroll to the over-time table"],
  ["The grid: red in the control columns, green in the judged columns", "S4's seven shocks with their deltas", "The over-time table: one row per snapshot, the marks never move"],
  ["Analysts 1 and 2 are meant to fail. A red cell on the right would be a defect.", "This is the drift check. Two red cells have already pointed at defects and both are fixed."],
  "If time is short, skip the dropdown and go straight to the over-time table.");
{
  const s = light("Evidence", "Governance: pre-register, amend in the open, replay", "Seven amendments in five weeks, each logged with its reason, each changing the spec hash pinned in the tests. The point of the timeline is that every change to the method is visible and dated, and that the number can be recomputed under the spec it was made with.");
  const steps = [
    ["#0", "21 Sep", "Scorecard S1 to S10, tilt cap 10 pp"], ["#1", "2 Oct", "Taylor rules join; 1.5% floor"], ["#2", "2 Oct", "Prediction-market odds join at 0.1"],
    ["#3, #4", "16 Oct", "Stale odds flagged, used, never skipped"], ["#5", "25 Oct", "Every model rule inside the spec hash"], ["#6", "25 Oct", "Base rates at 0.1; specialists' tilt applied, capped"],
  ];
  s.addShape(pres.shapes.LINE, { x: M + 0.5, y: 2.75, w: W - 2 * M - 1.0, h: 0, line: { color: THEME.colors.accent5, width: 3 } });
  steps.forEach(([n, d, t], i) => {
    const x = M + 0.5 + i * ((W - 2 * M - 1.0) / 5);
    s.addShape(pres.shapes.OVAL, { x: x - 0.22, y: 2.53, w: 0.44, h: 0.44, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.lt1, width: 2 } });
    text(s, n, { x: x - 1.0, y: 1.85, w: 2.0, h: 0.4, fontSize: 14, bold: true, color: C.text2, align: "center" });
    text(s, d, { x: x - 1.0, y: 3.1, w: 2.0, h: 0.35, fontSize: 11, color: C.accent4, align: "center" });
    text(s, t, { x: x - 1.0, y: 3.45, w: 2.0, h: 1.1, fontSize: 11, color: C.text1, align: "center" });
  });
  const facts = [["17", "ledger entries, hash-chained"], ["7", "amendments, each with its reason"], ["108", "tests, spec hash pinned"], ["0", "numbers tuned on outcomes"]];
  facts.forEach(([n, l], i) => stat(s, M + i * 3.1, 5.0, 2.9, n, l));
}

demo("Evidence", 6, "the ledger and replay", 1,
  ["Ledger view", "Press Verify ledger"],
  ["17 entries, each with its snapshot hash and code version", "The replay result: chain intact, entries under the current spec recompute exactly"],
  ["Nothing in this ledger can be edited or deleted without the chain breaking.", "Any entry can be recomputed from its snapshot. That is what auditable means here."],
  "One minute. Press the button, read the result line, move on.");

// =========================================================================================================
pres.addSection({ title: "Limits and next" });
{
  const s = light("Limits and next", "What this does not claim", "Say the limits before anyone asks. There is no live record: the first scored decision is 28 October. The weights are judgement, logged, not fitted. The probit is kept out. The sample behind every quant model is small and unbalanced. And at five weeks the market is the anchor, not the competitor.");
  const items = [
    ["No live record yet", "The first decision this system is scored on is 28 October 2026. Everything so far is process evidence, which is the point, but calibration needs a record."],
    ["Weights are judgement", "Market 0.6, Taylor 0.2, odds 0.1, base rates 0.1, the floor and the tilt mapping were set by reasoning and logged, never fitted. Candidate sets will be pre-registered and scored live."],
    ["The fitted model is outside", "A first ordered probit failed its out-of-sample gate and was reported, not tuned. Version 2 beats the base rate but carries a contamination caveat, so it stays at weight 0."],
    ["Small, unbalanced history", "About 130 decisions with full features, roughly 250 in all; 68% are holds and cuts cluster in three episodes. That is why there is no gradient-boosted anything."],
    ["Not every dimension yet", "Reasoning quality (S8) needs a rubric grader checked against hand grades; the reworded-prompt test for the analysts is not built."],
    ["The market is the anchor", "At thirty days futures call most decisions. The claim is auditability and discipline, not a better hit rate at this horizon."],
  ];
  items.forEach(([h, b], i) => {
    const x = M + (i % 3) * 4.1, y = 1.6 + Math.floor(i / 3) * 2.5;
    card(s, x, y, 3.85, 2.25);
    text(s, h, { x: x + 0.3, y: y + 0.2, w: 3.3, h: 0.5, fontSize: 15, bold: true, color: C.text2 });
    text(s, b, { x: x + 0.3, y: y + 0.75, w: 3.3, h: 1.4, fontSize: 11.5, color: C.text1 });
  });
}
{
  const s = light("Limits and next", "Follow-ups, in order of value", "Three follow-ups worth discussing with the room. Live scoring is built and the first record lands the morning after the decision. Longer windows are where reading evidence should matter more: for the December meeting the market already prices a hike at three in four, and the year-end rate is open. And an events agent for regime shifts: the cuts of 1987, 1998, 2008 and 2020 were driven by financial stress, not by the data the models read; the base-rates pre-read already lists the intermeeting moves, and a watch-out agent could flag when conditions look like those episodes.");
  const items = [
    ["Score live decisions: built this week", "Once the overnight-rate row is dated after the meeting, one click scores every forecast of that meeting, each track, each model and two naive baselines, with log score and Brier, into an append-only file. The first record lands the morning after 28 October. Every weight decision waits on this record."],
    ["Longer windows, same chain", "The December meeting and the year-end rate. The market is less certain there (Polymarket prices a December hike at 76%), so evidence reading has more to add. The chain needs only a different target."],
    ["An events agent for regime shifts", "1987, 1998, 2008, 2020: the Fed cut because of financial stress, not the data. A watch-out agent that scans the last three months for bank failures, funding stress and market dislocations, and raises a typed watch-out every analyst must answer."],
    ["Pre-registered weight sets", "Three or four candidate weight sets written down now, all scored on each live decision; the live set changes only by amendment on that record."],
    ["Reasoning quality, S8", "Twenty traces hand-graded on four questions; a model grader trusted only once it agrees with those grades."],
    ["One more step and a second model family", "A hawk, a dove and a synthesiser on the ladder; a second model family as a cross-check that the harness, not the model, is doing the work."],
  ];
  items.forEach(([h, b], i) => {
    const x = M + (i % 2) * 6.2, y = 1.55 + Math.floor(i / 2) * 1.7;
    numCircle(s, x, y + 0.1, i + 1);
    text(s, h, { x: x + 0.6, y, w: 5.4, h: 0.5, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: x + 0.6, y: y + 0.5, w: 5.4, h: 1.15, fontSize: 11.5, color: C.text1 });
  });
}
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Limits and next" });
  s.addText("Three things to take away", { placeholder: "title" });
  s.addText([
    { text: "The harness is the product. Same model, same evidence, same day: naive it wobbles and leaks; harnessed it is stable, quoted and checked.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Judge the process. Eight decisions a year cannot prove skill; a pre-registered scorecard measured on every snapshot can show discipline and catch drift.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "The ask: scrutinise the scorecard, suggest the next window, and tell us which other decisions deserve the same chain.", options: { bullet: true } },
  ], { placeholder: "body" });
  s.addNotes("Close on the ask. The forecast for 28 October is on file; the scoring is automatic from here; what the room can add is scrutiny and the next target.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
