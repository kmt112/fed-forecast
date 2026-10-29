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
  const s = light("Objective", "The question, the answer, and what happened", "The question is narrow on purpose: what will the FOMC decide at its next scheduled meeting, as probabilities over five outcomes. The final entry before the meeting said no change at 67.6%, hike at 22.4%, with the specialists leaning hawkish by four basis points. The Fed held, ten votes to two, and both dissents wanted the quarter-point hike the specialists were leaning toward. Say plainly that the market alone was more confident (90/10) and we do not claim to beat it at five weeks; what the system adds is the reasons, and the vote bore the reasons out. Then: one decision proves little, which is why the rest of the talk is about process.");
  stat(s, M, 1.55, 3.0, "28 Oct", "2026: the decision being forecast");
  stat(s, 3.7, 1.55, 3.0, "67.6%", "FedCast, no change: ledger entry #18, 27 hours before", C.text2);
  stat(s, 6.9, 1.55, 3.0, "Hold", "what the Fed did: 3.75 to 4.00%, unchanged", THEME.colors.accent3);
  stat(s, 10.1, 1.55, 2.6, "10 to 2", "two dissents, both for the +25 bps the specialists leaned toward", THEME.colors.accent2);
  card(s, M, 3.35, 6.0, 3.35);
  text(s, "How the number was made", { x: M + 0.3, y: 3.5, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  s.addText(bullets([
    "One frozen snapshot of 23 evidence items, pulled 28 October: futures, eight FRED series, both statements, minutes, transcript, projections, speeches, 32 years of decisions, the NY Fed natural rate, prediction-market odds",
    "Four models pooled by code at fixed weights (market 0.6, Taylor rules 0.2, odds 0.1, base rates 0.1), then a 1.5% floor on every outcome: no change 70.9%, hike 26.2%",
    "Five specialist analysts, every claim quoted and verified by code, lean the number +4.0 bp toward a hike: no change 67.6%, +25 bps 22.4%, +50 bps 7.7%",
    "Hash-chained ledger entry #18; recomputes exactly from its snapshot and the analyst runs it names",
  ], { fontSize: 12, color: C.text1, paraSpaceAfter: 4 }), { x: M + 0.3, y: 3.9, w: 5.5, h: 2.75, isTextBox: true, margin: 0, valign: "top" });
  card(s, 6.85, 3.35, W - M - 6.85, 3.35);
  text(s, "What the outcome says", { x: 7.15, y: 3.5, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  s.addText(bullets([
    "The most likely outcome was the outcome. The market alone was more confident (90/10); at five weeks we do not claim to beat it",
    "What the system added was the reasons: the hawkish lean came from the communications, minutes and inflation readers; the labour reader was the lone dove. Two dissents for a hike is that lean, in the vote",
    "Every reason is a quote code found in the frozen evidence, so the call can be taken apart claim by claim, which the rest of this talk does",
    "One decision proves little. It is scored formally (log score, Brier, against the market and two naive baselines) the moment the NY Fed's post-meeting rate row lands, and every weight decision waits on that record",
  ], { fontSize: 12, color: C.text1, paraSpaceAfter: 4 }), { x: 7.15, y: 3.9, w: W - M - 7.15, h: 2.75, isTextBox: true, margin: 0, valign: "top" });
}
demo("Objective", 1, "the forecast", 1,
  ["The app at localhost:8765, Forecast view", "Top bar: when the evidence was pulled, what is new at the sources"],
  ["The two tracks side by side: machine only, and with views", "The meta line: ledger entry, snapshot hash, the specialists' tilt", "The five bars"],
  ["This number was made at <time> from evidence frozen at <time>. Everything I show next is how it got there."],
  "Keep this to one minute. The point is only that the number exists, is dated, and is traceable. Do not explain the models yet.");
{
  const s = light("Objective", "Why build this", "Three reasons, the first is the one to land. Eight decisions a year cannot tell skill from luck, so we judge the process with a scorecard fixed before any code. Second, auditable means concrete: an analyst that says inflation is elevated must quote the line it read and code must find it. Third, because everything is quotable and the analysts can read only the evidence, a wrong call is a traceable wrong call, and because the harness is repeatable it goes wrong the same way every time, so a fix can be tested and stays fixed. Details later in the deck: the ladder, the scorecard, the drift table.");
  const cards = [
    ["1", "We judge the process, not the luck", [
      "Eight decisions a year: a good year proves nothing",
      "The yardstick is a ten-point scorecard, fixed before any code: same evidence, same answer? every claim quoted? any number from memory? a shock moves the number the right way?",
      "Outcomes are logged after each decision and never used to tune",
    ]],
    ["2", "Every step is auditable", [
      "An analyst that says 'inflation remains elevated' must quote the statement line it read, and code checks the quote is there, character for character",
      "Every number it uses must exist in the frozen evidence, or it is flagged as from memory",
      "Every model lists the items it read; every ledger entry recomputes from its snapshot. If it is not quoted, it does not count",
    ]],
    ["3", "A harness that compounds", [
      "Everything is quotable and the analysts can read only the evidence, so a wrong call is a traceable wrong call: we see which quote led where",
      "The harness is repeatable, so it goes wrong the same way every time; a fix can be tested, and the drift table shows it stayed fixed",
      "That is the virtuous cycle: audit, fix, re-measure. The ladder, the scorecard and the drift table later in the deck are that cycle",
    ]],
  ];
  cards.forEach(([n, h, items], i) => {
    const x = M + i * 4.1; card(s, x, 1.55, 3.85, 4.35);
    numCircle(s, x + 0.3, 1.75, n);
    text(s, h, { x: x + 0.85, y: 1.7, w: 2.8, h: 0.55, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    s.addText(bullets(items, { fontSize: 13, color: C.text1, paraSpaceAfter: 8 }), { x: x + 0.3, y: 2.45, w: 3.3, h: 3.35, isTextBox: true, margin: 0, valign: "top" });
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

// =========================================================================================================
pres.addSection({ title: "How it works" });
{
  const s = light("How it works", "Four families, one pool, one number", "Left: the diagram from the brief. Four families of input, combined by code with fixed, published weights; no model writes the number. The language-model family enters only as a bounded lean. Right: the chain in order, each line a view in the app. Walk the diagram first, then the chain.");
  const fam = [
    ["Economic predictors", "Fed funds futures (the anchor), the Fed's own four Taylor rules with r* from the NY Fed DSGE model, prediction-market odds", THEME.colors.dk2],
    ["Empirical data", "What followed each kind of decision over 32 years of FOMC history, conditioned on the last move", THEME.colors.dk2],
    ["Classic ML", "An ordered probit fitted on data as first published; computed and shown, weight 0 until it has a live record", THEME.colors.accent4],
    ["LLM-derived", "Five specialist analysts reading the Fed's own words; every claim quoted and verified by code; a bounded lean, not a weight", THEME.colors.accent2],
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
  text(s, "Weights 0.6 / 0.2 / 0.1 / 0.1, fixed and published. A 1.5% floor on every outcome. Then the analysts' lean, capped at 10 points. Code does this; no model writes the number.", { x: px + 0.12, y: by + 0.8, w: 1.26, h: 3.6, fontSize: 9.5, color: C.text1, align: "center" });
  s.addShape(pres.shapes.LINE, { x: px + 1.58, y: by + totalH / 2, w: 0.42, h: 0, line: { color: THEME.colors.accent4, width: 1.5, endArrowType: "triangle" } });
  const fx = px + 2.08;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: by + totalH / 2 - 0.85, w: 1.55, h: 1.7, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.1 });
  text(s, "Forecast", { x: fx, y: by + totalH / 2 - 0.75, w: 1.55, h: 0.4, fontSize: 14, bold: true, color: C.background1, align: "center" });
  text(s, "28 Oct, entry #18\nno change 67.6%\n+25 bps 22.4%", { x: fx, y: by + totalH / 2 - 0.3, w: 1.55, h: 1.1, fontSize: 10.5, color: C.background1, align: "center" });
  const rx = fx + 1.85, rw = W - M - rx;
  text(s, "The chain, in order", { x: rx, y: 1.55, w: rw, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  const chain = [
    ["Evidence", "23 items frozen and fingerprinted, dated in US time, data as first published. Nothing outside it may be read.", THEME.colors.dk2],
    ["Signals", "Computed by code and handed to the analysts as numbers: inflation gap, labour slack, financial conditions, statement tone, base rates, projections.", THEME.colors.dk2],
    ["Pool", "Four families at fixed weights, the floor, then the specialists' lean.", THEME.colors.dk2],
    ["Analysts", "Only analysts 4 to 8 enter the number. Analysts 1 to 3 are checks and balances on the ladder.", THEME.colors.accent2],
    ["You", "Views tilt by at most 10 points and expire; watch-outs must be answered by id; documents and odds become evidence.", THEME.colors.accent3],
    ["Ledger", "Append-only, hash-chained; every entry recomputes from its snapshot and the runs it names.", THEME.colors.dk2],
  ];
  chain.forEach(([h, b, col], i) => {
    const y = 2.0 + i * 0.78;
    s.addShape(pres.shapes.RECTANGLE, { x: rx, y: y + 0.05, w: 0.12, h: 0.6, fill: { color: col }, line: { color: col } });
    text(s, h, { x: rx + 0.25, y, w: 1.3, h: 0.7, fontSize: 12.5, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: rx + 1.5, y, w: rw - 1.5, h: 0.72, fontSize: 10, color: C.text1, valign: "middle" });
  });
}
{
  const s = light("How it works", "The arithmetic: from five models to one number", "Entry 18, the final one before the meeting. The pool is a weighted average, then the floor. The specialists' mean lean of +4.0 basis points becomes 4.0 points of probability moved toward a hike, through the same capped mechanism a human view uses. Then the sentence in red: the weights are judgement, logged, not backtested. The backtest decides who is in the pool, not the weight; the probit failed its gate and sits at zero. Live scores from 28 October onward will move the weights, by amendment, on the record.");
  const hdr = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const r = (a, b, c, d, e, f, g, bold) => [{ text: a, options: { bold: !!bold } }, { text: b, options: { fontSize: 10.5 } }, ...[c, d, e, f, g].map(v => ({ text: v, options: { align: "center", bold: !!bold } }))];
  const rows = [
    [{ text: "Model", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, hdr("−25"), hdr("no change"), hdr("+25"), hdr("+50"), hdr("weight")],
    r("Market-implied", "November fed-funds future against the overnight rate: +2.5 bp expected, split between the two nearest outcomes", "0", "90", "10", "0", "0.6"),
    r("Taylor family", "12-month core PCE 3.0%, unemployment 4.2%, r* from the NY Fed DSGE model (0.65 / 1.86 / 3.06%), four rules × nine r*/u* pairs: +22.5 bp mean", "4.5", "26.9", "44.6", "23.8", "0.2"),
    r("Prediction market", "Polymarket, 26 Oct, $67m traded: 94.5% no change", "0.2", "94.9", "4.5", "0.4", "0.1"),
    r("Historical base rates", "What followed a hike at the 49 scheduled meetings since 1994 that came after one", "0", "34.7", "52.2", "13.1", "0.1"),
    r("Ordered probit v2", "Nine features on first-published data; failed v1, caveated v2", "0", "24.2", "63.8", "12.0", "0"),
    r("Pooled", "Weighted average, then the 1.5% floor", "1.5", "70.9", "20.2", "6.0", "", true),
    r("Specialists' lean", "+4.0 bp hawkish, mean of analysts 4 to 8: 4.0 points moved toward the hike outcomes", "", "", "", "", ""),
    r("Machine forecast", "Ledger entry #18, 28 October", "1.2", "67.6", "22.4", "7.7", "", true),
  ];
  s.addTable(rows, { x: M, y: 1.5, w: W - 2 * M, colW: [2.0, 4.73, 0.9, 1.3, 0.9, 0.9, 1.4], fontSize: 11.5, color: THEME.colors.dk1, border: { type: "solid", color: "D5DBE5", pt: 0.5 }, valign: "middle", margin: 0.05, rowH: 0.5 });
  card(s, M, 6.05, W - 2 * M, 0.85);
  text(s, "The weights are judgement, logged, not backtested. The backtest (expanding window, 129 decisions since 2010) decides who is in the pool: the base rates beat the fitted probit and joined; the probit failed its gate and sits at weight 0. Live scores from 28 October onward decide the weights, by amendment, on the record. Fitting them on the same history the models came from would prove nothing.", { x: M + 0.25, y: 6.12, w: W - 2 * M - 0.5, h: 0.72, fontSize: 11, color: THEME.colors.accent2, valign: "middle" });
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
  text(s, "Each step adds one thing; the value of that thing is the difference in score between neighbouring steps. Only analysts 4 to 8 enter the number. Analysts 1 to 3 never touch it: they exist as checks and balances, to show what the harness adds and to catch drift.", { x: M, y: 6.6, w: W - 2 * M, h: 0.5, fontSize: 12, italic: true, color: THEME.colors.accent2 });
}
{
  const s = light("The harness", "What the harness enforces around every analyst", "Six mechanisms. None of them is clever; together they are what makes a language model's output usable in a forecast. This is the architecture slide: spend time here. The repair round is the newest: a bounded correction against frozen evidence, with both answers kept so it cannot turn into prompt tuning.");
  const items = [
    ["Tools off, slice only", "The model sees its slice of the frozen snapshot and nothing else: no browsing, no memory of the Fed, no other analyst's output."],
    ["Pre-reads", "Numbers are computed by code and handed over: inflation gap, labour slack, financial conditions, tone, base rates. The model never does arithmetic."],
    ["Fixed answer shape", "Claims, each with a verbatim quote and the item it came from; a report on every watch-out by id; a tilt bounded to ±10 basis points. Enforced by the runtime."],
    ["Code verifies", "Every quote is string-matched to its item. Every number is matched to the snapshot. Every watch-out must be answered. Failures are counted, never hidden."],
    ["Recorded and repeated", "Five identical runs per analyst per snapshot, each stored with its prompt hash. Repeatability is measured, and a recorded run replays for free."],
    ["One repair round", "If a quote is not found or a number is not in the evidence, the answer goes back once with the verifier's report: fix the quote verbatim, drop the number, or drop the claim. Both answers are kept; the repaired one counts. No second round."],
  ];
  items.forEach(([h, b], i) => {
    const y = 1.5 + i * 0.86;
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
  const s = light("Evidence", "How good is the harness: what each step bought", "Three charts, one per dimension, averaged over the four snapshots. Left: how much the answer moves between identical runs. The step that matters is analyst 2 to analyst 3: the answer shape and the verifier take the wobble from three and a half points to under one. Middle: numbers from memory, gone as soon as the evidence is shown. Right: share of claims whose quote code found verbatim; analyst 2 cannot be measured because it quotes nothing. The specialists keep what analyst 3 achieved. For analysts 3 to 8 the wobble is in their lean, which maps one basis point to one percentage point of probability, so the four bars are comparable.");
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
  text(s, "Measured by code on the 28 October snapshot", { x: M + 0.3, y: 4.45, w: 5.4, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["S4: 7 shocks, one input each, the pool must move the right way: 7 of 7", "S5: 5 irrelevant changes to the snapshot: 0.0 points moved", "S7: every ledger entry coherent and attributable", "S9: entries under the current spec recompute exactly, from the analyst runs they name"], { fontSize: 12, color: C.text1 }), { x: M + 0.3, y: 4.9, w: 5.4, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
  card(s, 6.9, 4.3, 5.83, 2.4);
  text(s, "What it has already caught", { x: 7.2, y: 4.45, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets(["Four ledger entries stopped replaying after a model rule changed outside the hashed spec; amendment #5 put every rule inside the hash.", "A shock test was perturbing the wrong odds entry once two were on file; a red cell on the drift table pointed at it.", "Replay was reading the latest analyst runs instead of the runs the entry used; a rerun would have broken an honest entry. Fixed the same day, with a test.", "A verifier false positive (a zero written as 0 in the evidence); fixed, records re-scored without calling the model."], { fontSize: 11, color: C.text1 }), { x: 7.2, y: 4.9, w: 5.3, h: 1.7, isTextBox: true, margin: 0, valign: "top" });
}
demo("Evidence", 5, "the scorecard and the drift table", 2,
  ["Scorecard view", "The snapshot dropdown: pick 24 October, then 26 October", "Expand 'what was checked' under S4", "Scroll to the over-time table"],
  ["The grid: red in the control columns, green in the judged columns", "S4's seven shocks with their deltas", "The over-time table: one row per snapshot, the marks never move"],
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
  const s = light("Limits and next", "What this does not claim, and what comes next", "Left, the limits, said before anyone asks: one scored decision; weights by judgement; the fitted model outside; the market is the anchor. Right, what is next, in order of value: the December window is already running on the same chain; pre-registered weight sets scored live; an events agent for the regime shifts the models cannot read (1987, 1998, 2008, 2020 were financial-stress cuts); the reasoning grader and a second model family.");
  text(s, "What this does not claim", { x: M, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  const limits = [
    ["One scored decision", "28 October is the first. Everything before it is process evidence, which is the point, but calibration needs a record."],
    ["Weights are judgement", "Market 0.6, Taylor 0.2, odds 0.1, base rates 0.1, the floor and the lean cap were set by reasoning and logged, never fitted."],
    ["The fitted model is outside", "Probit v1 failed its gate and was reported, not tuned; v2 beats the base rate but carries a contamination caveat, so weight 0. About 130 usable decisions, 68% holds: no gradient-boosted anything."],
    ["The market is the anchor", "At five weeks futures call most decisions. The claim is auditability and discipline, not a better hit rate."],
  ];
  limits.forEach(([h, b], i) => {
    const y = 2.0 + i * 1.15;
    card(s, M, y, 6.0, 1.05);
    text(s, h, { x: M + 0.25, y: y + 0.08, w: 5.5, h: 0.35, fontSize: 13, bold: true, color: C.text2 });
    text(s, b, { x: M + 0.25, y: y + 0.42, w: 5.5, h: 0.6, fontSize: 10.5, color: C.text1 });
  });
  text(s, "What comes next, in order of value", { x: 6.95, y: 1.5, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  const next = [
    ["The December window, same chain: running now", "The 9 December meeting is less certain (the market prices a hike at about three in four), so reading the evidence has more to add. The chain needed only a new target."],
    ["Pre-registered weight sets, scored live", "Three or four candidate sets written down now, all scored on every live decision; the live set changes only by amendment on that record."],
    ["An events agent for regime shifts", "1987, 1998, 2008, 2020: the Fed cut on financial stress, not the data the models read. A watch-out agent that scans for bank failures, funding stress and dislocations, and raises a watch-out every analyst must answer."],
    ["Reasoning quality and a second model family", "Twenty traces hand-graded, a model grader trusted only once it agrees; a second model family to show the harness, not the model, does the work."],
  ];
  next.forEach(([h, b], i) => {
    const y = 2.0 + i * 1.15;
    numCircle(s, 6.95, y + 0.1, i + 1);
    text(s, h, { x: 7.5, y, w: 5.25, h: 0.4, fontSize: 13, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: 7.5, y: y + 0.4, w: 5.25, h: 0.7, fontSize: 10.5, color: C.text1 });
  });
}
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Limits and next" });
  s.addText("Three things to take away", { placeholder: "title" });
  s.addText([
    { text: "The harness is the product. Same model, same evidence, same day: naive it wobbles and leaks; harnessed it is stable, quoted and checked.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Judge the process. Eight decisions a year cannot prove skill; a pre-registered scorecard measured on every snapshot can show discipline and catch drift.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "The ask: scrutinise the scorecard, challenge a quote, and tell us which other decisions deserve the same chain. The 28 October call is on file; December is already running.", options: { bullet: true } },
  ], { placeholder: "body" });
  s.addNotes("Close on the ask. The forecast for 28 October is on file; the scoring is automatic from here; what the room can add is scrutiny and the next target.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
