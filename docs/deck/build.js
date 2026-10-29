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

// =========================================================================================================
pres.addSection({ title: "Objective" });
{
  const s = light("Objective", "The question, the answer, and what happened", "The question is narrow on purpose: what will the FOMC decide at its next scheduled meeting, as probabilities over five outcomes. The final entry before the meeting said no change at 67.6%, hike at 22.4%, with the specialists leaning hawkish by four points. The Fed held, ten votes to two, and both dissents wanted the quarter-point hike the specialists were leaning toward. Say plainly that the market alone was more confident (90/10) and we do not claim to beat it at five weeks; what the system adds is the reasons, and the vote bore the reasons out. Then: one decision proves little, which is why the rest of the talk is about process.");
  stat(s, M, 1.55, 3.0, "28 Oct", "the decision being forecast, 2026");
  stat(s, 3.7, 1.55, 3.0, "67.6%", "FedCast, no change: ledger entry #18, nine hours before", C.text2);
  stat(s, 6.9, 1.55, 3.0, "Hold", "what the Fed did: 3.75 to 4.00%, unchanged", THEME.colors.accent3);
  stat(s, 10.1, 1.55, 2.6, "10 to 2", "two dissents, both for the +25 bps the specialists leaned toward", THEME.colors.accent2);
  card(s, M, 3.35, 6.0, 3.35);
  text(s, "How the number was made", { x: M + 0.3, y: 3.5, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  s.addText(bullets([
    "One frozen snapshot of 23 evidence items, pulled 28 October: futures, eight FRED series, both statements, minutes, transcript, projections, speeches, 32 years of decisions, the NY Fed natural rate, prediction-market odds",
    "Four models pooled by code at fixed weights (market 0.6, Taylor rules 0.2, odds 0.1, base rates 0.1), then a 1.5% floor on every outcome: no change 70.9%, hike 26.2%",
    "Five specialist analysts, every claim quoted and verified by code, move the number 4.0 points toward a hike: no change 67.6%, +25 bps 22.4%, +50 bps 7.7%",
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
  const s = light("Objective", "Four kinds of signal, and where FedCast sits", "Four kinds of signal exist already; each is good at one thing. Market prices are the best single predictor at thirty days and are the anchor of the pool. Surveys carry judgement; FedCast takes the data the committee reads instead, as history and a fitted model. The rules are the Fed's own benchmarks. The LLM papers show a model can read the Fed, on sixteen meetings. FedCast's claim is not a better guess but the combination: one of each kind, pooled by code at fixed weights, every number traceable to frozen evidence.");
  // --- four signal groups ---------------------------------------------------------------------------------
  const groups = [
    { name: "Market signals", color: THEME.colors.accent1,
      who: "Fed funds futures (CME FedWatch); prediction markets (Polymarket, Kalshi)",
      what: "Prices and crowd odds on each outcome",
      strength: "Futures about 88% right at 30 days, 1994 to 2024; odds move fast" },
    { name: "Economic signals", color: THEME.colors.accent3,
      who: "Economist surveys; the macro data itself",
      what: "The median of polled forecasters; the data the committee reads",
      strength: "Broad human judgement; the data is the Fed's own input" },
    { name: "Policy rules", color: THEME.colors.accent6,
      who: "The Taylor family",
      what: "The rate a formula says is appropriate given inflation and unemployment",
      strength: "Transparent; the Fed's own published benchmarks" },
    { name: "ML / AI signals", color: THEME.colors.accent2,
      who: "LLM 'FOMC agent' papers (2025)",
      what: "Models that read the Fed's text and vote",
      strength: "Reported 90%+ accuracy on 2023 to 2024" },
  ];
  const gw = 2.86, gap = (W - 2 * M - 4 * gw) / 3, gy = 1.55, gh = 2.55;
  groups.forEach((g, i) => {
    const x = M + i * (gw + gap);
    card(s, x, gy, gw, gh);
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.25, y: gy + 0.3, w: 0.16, h: 0.16, fill: { color: g.color }, line: { color: g.color } });
    text(s, g.name, { x: x + 0.5, y: gy + 0.18, w: gw - 0.7, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
    text(s, g.who, { x: x + 0.25, y: gy + 0.68, w: gw - 0.5, h: 0.62, fontSize: 12, bold: true, color: C.text1 });
    text(s, [{ text: "What it is  ", options: { bold: true, color: THEME.colors.accent4 } }, { text: g.what }],
         { x: x + 0.25, y: gy + 1.32, w: gw - 0.5, h: 0.6, fontSize: 11.5, color: C.text1 });
    text(s, [{ text: "Strength  ", options: { bold: true, color: THEME.colors.accent4 } }, { text: g.strength }],
         { x: x + 0.25, y: gy + 1.94, w: gw - 0.5, h: 0.58, fontSize: 11.5, color: C.text1 });
  });

  // --- the spectrum: pure data at one end, pure model at the other, FedCast in the middle -----------------
  const ly = 4.98, lx0 = M + 0.2, lx1 = W - M - 0.2, L = lx1 - lx0;
  s.addShape(pres.shapes.LINE, { x: lx0, y: ly, w: L, h: 0, line: { color: THEME.colors.accent4, width: 1.75, beginArrowType: "triangle", endArrowType: "triangle" } });
  text(s, "Pure data", { x: M, y: ly + 0.12, w: 2.4, h: 0.3, fontSize: 12, bold: true, color: C.accent4 });
  text(s, "prices and formulas; no reading of the Fed's words", { x: M, y: ly + 0.4, w: 2.6, h: 0.5, fontSize: 10.5, color: C.accent4 });
  text(s, "Pure model", { x: W - M - 2.4, y: ly + 0.12, w: 2.4, h: 0.3, fontSize: 12, bold: true, color: C.accent4, align: "right" });
  text(s, "one model's judgement; nothing it reads is checked", { x: W - M - 2.6, y: ly + 0.4, w: 2.6, h: 0.5, fontSize: 10.5, color: C.accent4, align: "right" });
  // where each kind of signal sits (markers above the line)
  const marks = [
    [0.11, THEME.colors.accent1, "Futures, prediction markets"],
    [0.30, THEME.colors.accent6, "Policy rules"],
    [0.70, THEME.colors.accent3, "Economist surveys"],
    [0.90, THEME.colors.accent2, "LLM 'FOMC agents'"],
  ];
  marks.forEach(([f, col, label]) => {
    const x = lx0 + f * L;
    s.addShape(pres.shapes.OVAL, { x: x - 0.1, y: ly - 0.1, w: 0.2, h: 0.2, fill: { color: col }, line: { color: THEME.colors.lt1, width: 1 } });
    text(s, label, { x: x - 1.15, y: ly - 0.52, w: 2.3, h: 0.3, fontSize: 11.5, bold: true, color: C.text1, align: "center", valign: "bottom" });
  });
  // FedCast in the middle (below the line)
  const fx = lx0 + 0.5 * L;
  s.addShape(pres.shapes.LINE, { x: fx, y: ly, w: 0, h: 0.28, line: { color: THEME.colors.dk2, width: 1.75 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx - 0.7, y: ly + 0.28, w: 1.4, h: 0.4, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.2 });
  text(s, "FedCast", { x: fx - 0.7, y: ly + 0.28, w: 1.4, h: 0.4, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: THEME.headFontFace });
  text(s, "Takes one input from each area, prices, 32 years of decisions, the Fed's own rules and a language model that must quote what it reads, and combines them by code at fixed weights. Neither a formula nor an oracle.",
       { x: fx - 3.9, y: ly + 0.8, w: 7.8, h: 0.6, fontSize: 11.5, color: C.text1, align: "center" });

  text(s, "Sources: Bonini, Huang and Simaan, 'Watching the FedWatch' (232 meetings, May 1994 to March 2024); FedSight AI preprint, December 2025; Takano, Hirano and Nakagawa, arXiv 2511.02469.",
       { x: M, y: 6.62, w: W - 2 * M, h: 0.3, fontSize: 9.5, color: C.accent4 });
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
  const s = light("How it works", "The arithmetic: from five models to one number", "Entry 18, the final one before the meeting. The pool is a weighted average, then the floor. The specialists' mean score of +4.0 is 4.0 points of probability moved toward a hike, through the same capped mechanism a human view uses. The lean row is tinted and labelled 'after pooling': it is a modifier on the pooled number, not a model in the pool. Then the footer: the weights are judgement, logged; ideally they would be backtested, but there is no live record yet, so live scores from 28 October onward decide them by amendment.");
  const hdr = t => ({ text: t, options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } });
  const r = (a, b, c, d, e, f, g, bold) => [{ text: a, options: { bold: !!bold } }, { text: b, options: { fontSize: 10.5 } }, ...[c, d, e, f, g].map(v => ({ text: v, options: { align: "center", bold: !!bold } }))];
  const rows = [
    [{ text: "Model", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "What it reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, hdr("−25"), hdr("no change"), hdr("+25"), hdr("+50"), hdr("weight")],
    r("Market-implied", "November fed-funds future against the overnight rate: +2.5 bp expected, split between the two nearest outcomes", "0", "90", "10", "0", "0.6"),
    r("Taylor family", "12-month core PCE 3.0%, unemployment 4.2%, r* from the NY Fed DSGE model (0.65 / 1.86 / 3.06%); three level rules × nine r*/u* pairs plus the first-difference rule × three u*: 30 prescriptions, mean +22.5 bp", "4.5", "26.9", "44.6", "23.8", "0.2"),
    r("Prediction market", "Polymarket, 26 Oct, $67m traded: 94.5% no change at the mid price, 94.9% once the five prices are renormalised", "0.2", "94.9", "4.5", "0.4", "0.1"),
    r("Historical base rates", "What followed a hike at the 49 scheduled meetings since 1994 that came after one", "0", "34.7", "52.2", "13.1", "0.1"),
    r("Ordered probit v2", "Nine features on first-published data; failed v1, caveated v2", "0", "24.2", "63.8", "12.0", "0"),
    r("Pooled", "Weighted average, then the 1.5% floor", "1.5", "70.9", "20.2", "6.0", "", true),
    [{ text: "After pooling", options: { bold: true, color: THEME.colors.accent2, fill: { color: "FBEFEA" } } },
     { text: [{ text: "Specialists' lean: a modifier on the pooled number, not a model in the pool. ", options: { bold: true } }, { text: "Mean of analysts 4 to 8, +4.0, hawkish: 4.0 points of probability moved toward a hike, capped at 10." }], options: { fontSize: 10, fill: { color: "FBEFEA" } } },
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
  ["Blue is in the number, grey is computed but not in it. Click a model and you see only what it read.", "The language model's lean is the one line between Pooled and Machine track. It can tilt, it cannot write."],
  "This is the longest demo. Start at the raw futures price so the audience sees arithmetic, not a black box. Then the pool box, then one click into an evidence item to show the frozen text.");

// =========================================================================================================
pres.addSection({ title: "The harness" });
{
  const s = light("The harness", "Working around the model's limits", "Three things a language model cannot be made to stop doing: it remembers, it varies between runs, and it can invent support. None is removed. Each is designed around, and the design is measured on every snapshot. Walk the three columns top to bottom: the limit, what we do, the proof. The proof numbers are from the 28 October records and the four-snapshot means.");
  text(s, "Three things a language model cannot be made to stop doing. None is removed; each is designed around, and the design is measured on every snapshot.", { x: M, y: 1.38, w: W - 2 * M, h: 0.3, fontSize: 12, color: C.accent4 });
  const cols = [
    { limit: "Memory cannot be switched off", sub: "Everything it knows about the Fed is in its weights, and it will use it unless something stops it.",
      items: [["Prompt engineering: ", "use only the evidence; do not use anything you remember about the economy, the Fed or markets."],
              ["Answer shape: ", "every claim must carry a verbatim quote from a named item, so a remembered fact has nowhere to stand."],
              ["Harness: ", "every number in the answer is matched to the snapshot by code; one that is not found is flagged as from memory and sent back once to be removed."]],
      plabel: "PROOF, 28 OCTOBER", stat: "38 → 0", proof: "figures in the answer that appear nowhere in the evidence: analyst 1, which sees no evidence, against analysts 2 to 8, five runs each" },
    { limit: "The same question gets different answers", sub: "Ask twice and the number moves.",
      items: [["Answer shape: ", "a JSON schema fixes the form of the answer; the runtime rejects anything else before anyone reads it."],
              ["Five identical runs ", "per analyst per snapshot: the same evidence, the same question, the same schema, only the run number differs. Each is stored and hashed, so it can be audited later."],
              ["Repeatability is measured: ", "how far the answer moves between those five runs. Pass mark: 2 points."]],
      plabel: "PROOF, FOUR SNAPSHOTS", stat: "4.2 → 0.8", proof: "how far the answer moves between identical runs: naive 4.2 points, specialists 0.8 points, mean of four snapshots" },
    { limit: "It can invent its own support", sub: "A fluent quote or figure that was never in the document.",
      items: [["Harness: ", "every quote and every number in a claim is verified by code, not by a model. A quote must match its item character for character; a quote stitched from two places fails."],
              ["Bounds: ", "every watch-out must be answered by id; the score is clipped to −10 to +10."],
              ["One repair round ", "with the verifier's report; both answers are kept. What still fails is recorded as unverified, never hidden."]],
      plabel: "PROOF, 28 OCTOBER", stat: "326 / 327", proof: "claims whose quote code found verbatim, analysts 3 to 8, 30 runs; the one miss is on the record" },
  ];
  const cw = (W - 2 * M - 2 * 0.17) / 3;
  cols.forEach((c, i) => {
    const x = M + i * (cw + 0.17);
    let y = 1.78;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: 1.05, fill: { color: THEME.colors.accent2 }, line: { color: THEME.colors.accent2 }, rectRadius: 0.1 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.85, w: cw, h: 0.2, fill: { color: THEME.colors.accent2 }, line: { color: THEME.colors.accent2 } });
    text(s, "LIMIT", { x: x + 0.17, y: y + 0.1, w: cw - 0.3, h: 0.2, fontSize: 9, bold: true, color: "F8D7CE", charSpacing: 1 });
    text(s, c.limit, { x: x + 0.17, y: y + 0.3, w: cw - 0.3, h: 0.32, fontSize: 14, bold: true, color: C.background1 });
    text(s, c.sub, { x: x + 0.17, y: y + 0.62, w: cw - 0.3, h: 0.4, fontSize: 10.5, color: "F8D7CE" });
    y += 1.05;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: 2.2, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.lt2 } });
    text(s, "WHAT WE DO", { x: x + 0.17, y: y + 0.12, w: cw - 0.3, h: 0.2, fontSize: 9, bold: true, color: C.accent4, charSpacing: 1 });
    const runs = [];
    c.items.forEach(([k, v], j) => { runs.push({ text: k, options: { bullet: true, bold: true, color: THEME.colors.dk1 } }); runs.push({ text: v, options: { breakLine: j < c.items.length - 1, paraSpaceAfter: 5 } }); });
    s.addText(runs, { x: x + 0.17, y: y + 0.38, w: cw - 0.3, h: 1.78, fontSize: 10.5, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
    y += 2.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: 1.05, fill: { color: THEME.colors.lt1 }, line: { color: "D5DBE5" }, rectRadius: 0.1 });
    text(s, c.plabel, { x: x + 0.17, y: y + 0.1, w: cw - 0.3, h: 0.2, fontSize: 9, bold: true, color: C.accent4, charSpacing: 1 });
    text(s, c.stat, { x: x + 0.17, y: y + 0.35, w: 1.55, h: 0.6, fontSize: 22, bold: true, color: THEME.colors.accent3, fontFace: THEME.headFontFace, valign: "middle" });
    text(s, c.proof, { x: x + 1.75, y: y + 0.32, w: cw - 1.9, h: 0.68, fontSize: 10, color: C.text1, valign: "middle" });
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
  text(s, "Each specialist is asked one question about its own slice (above), never for a probability. It returns claims, each with a verbatim quote and item id, and a lean of at most ±10 bp: direction and strength, positive toward a hike. Code averages the five leans; 1 bp of mean lean moves 1 point of probability, capped at 10.", { x: bx + 0.2, y: 5.12, w: bw - 0.4, h: 0.7, fontSize: 11.5, color: THEME.colors.accent5 });
  card(s, M, 6.06, W - 2 * M, 0.85, "F3F4F6");
  s.addText([{ text: "Every analyst runs five times on the same snapshot. ", options: { bold: true } }, { text: "For analysts 1 to 3 those runs are not forecasts: they build the benchmark that 4 to 8 are measured against." }], { x: M + 0.17, y: 6.12, w: W - 2 * M - 0.34, h: 0.26, fontSize: 11.5, color: C.text1, isTextBox: true, margin: 0 });
  const bench = [["1 sets the baseline: ", "variance of the probabilities across runs; numbers from memory (all of them); nothing quoted."], ["2 tests immutable evidence: ", "numbers from memory fall to zero; the variance does not; nothing can be checked."], ["3 tests the answer shape and code verification: ", "variance falls under 1 point; every claim quoted and checked."]];
  const bwid = (W - 2 * M - 0.34 - 0.3) / 3;
  bench.forEach(([k, v], i) => s.addText([{ text: k, options: { bold: true } }, { text: v }], { x: M + 0.17 + i * (bwid + 0.15), y: 6.42, w: bwid, h: 0.45, fontSize: 10, color: C.text1, isTextBox: true, margin: 0, valign: "top" }));
}
{
  const s = light("The harness", "LLM analysts: outcome", "One line of method, then the outcome. Each specialist runs five times on the same frozen snapshot; the five answers must sit within the variance pass mark, every claim must carry a quote code finds, and no number may come from memory. Only then does the lean count. The band is the 28 October run; bottom left is what the five said and what it did to the number; bottom right is one claim as recorded, with the quote code found.");
  card(s, M, 1.42, W - 2 * M, 0.78);
  s.addText([{ text: "Each specialist runs five times on the same frozen snapshot. ", options: { bold: true, color: THEME.colors.dk2 } },
             { text: "The five answers must sit within the variance pass mark (2 points), every claim must carry a quote that code finds in the evidence, character for character, and no number may come from memory. Only then does the lean count toward the number." }],
            { x: M + 0.22, y: 1.5, w: W - 2 * M - 0.44, h: 0.62, fontSize: 12.5, color: C.text1, isTextBox: true, margin: 0, valign: "middle" });
  // the flow band: analysts 4 to 8 only, stepping down toward the five leans
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
  card(s, M, ly, 4.85, lh, "FBEFEA");
  text(s, "WHAT THE FIVE SAID, AND WHAT IT DID TO THE NUMBER", { x: M + 0.17, y: ly + 0.12, w: 4.5, h: 0.2, fontSize: 9, bold: true, color: THEME.colors.accent2, charSpacing: 1 });
  const said = [["Communications", "+6.0 hike"], ["Minutes", "+6.2 hike"], ["Inflation", "+5.8 hike"], ["Financial conditions", "+3.4 hike"], ["Labour market", "−1.4 hold"], ["Equal-weight mean", "+4.0"]];
  s.addTable(said.map(([a, b], i) => [{ text: a, options: { color: i === 4 ? THEME.colors.accent3 : THEME.colors.dk1, bold: i === 5 } }, { text: b, options: { align: "right", bold: true, color: i === 4 ? THEME.colors.accent3 : THEME.colors.dk1 } }]),
             { x: M + 0.17, y: ly + 0.42, w: 2.3, colW: [1.4, 0.9], fontSize: 11, border: { type: "none" }, margin: 0.02, rowH: 0.3 });
  s.addText([{ text: "Four say hike, one says hold back. ", options: { bold: true } }, { text: "Plain average, one vote each: +4.0.", options: { breakLine: true } },
             { text: "Each point of lean moves one point of probability ", options: { bold: true } }, { text: "from the hold side to the hike side, by rule, capped at 10. So +4.0 moves 4.0 points, after the pool:" }],
            { x: M + 2.55, y: ly + 0.42, w: 2.15, h: 1.3, fontSize: 10.5, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  text(s, "+25 bps: 20.2% → 22.4%", { x: M + 2.55, y: ly + 1.78, w: 2.2, h: 0.36, fontSize: 14, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  text(s, "+50 bps 6.0 → 7.7; no change 70.9 → 67.6; cuts 3.0 → 2.3", { x: M + 2.55, y: ly + 2.15, w: 2.2, h: 0.4, fontSize: 9.5, color: C.accent4 });
  // bottom right: one verified claim as recorded
  const rx = M + 5.0, rw = W - M - rx;
  card(s, rx, ly, rw, lh);
  text(s, "ONE VERIFIED CLAIM, AS RECORDED · ANALYST 4, COMMUNICATIONS, RUN 1 OF 5", { x: rx + 0.17, y: ly + 0.1, w: rw - 0.34, h: 0.2, fontSize: 9, bold: true, color: C.accent4, charSpacing: 1 });
  s.addText([{ text: "Claim ", options: { bold: true } }, { text: "The September statement stressed elevated inflation and a resolve to return to target on a timelier basis." }], { x: rx + 0.17, y: ly + 0.38, w: rw - 0.34, h: 0.4, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  text(s, "\u201cInflation remains elevated. Today's policy action will support a timelier return to the Committee's 2 percent goal. The Committee will deliver price stability.\u201d", { x: rx + 0.17, y: ly + 0.82, w: rw - 0.34, h: 0.5, fontSize: 9.5, color: "374151", fontFace: "Courier New" });
  s.addText([{ text: "Item " }, { text: "fed.statement.2026-09-16", options: { bold: true, color: THEME.colors.dk1 } }, { text: " · quote found by code, character for character · lean hawkish · 12 of 12 claims in this run verified" }], { x: rx + 0.17, y: ly + 1.4, w: rw - 0.34, h: 0.4, fontSize: 10, color: C.accent4, isTextBox: true, margin: 0, valign: "top" });
}

demo("The harness", 3, "what each analyst is asked and given", 2,
  ["Analyst prompts view", "Analyst 1: open the full prompt", "Analyst 6: open the full prompt"],
  ["Analyst 1: 195 characters, no evidence", "Analyst 6: the system prompt, the enforced answer schema, the inflation pre-read, the item ids", "The prompt hash: five repeats share it"],
  ["If it is not on this page, the analyst does not get it.", "Same model. The only difference between analyst 1 and analyst 6 is this page."],
  "Open analyst 1 first so the contrast with analyst 6 lands. Scroll the full prompt slowly past the schema and the pre-read; do not read it out.");

// =========================================================================================================
pres.addSection({ title: "Evidence" });
{
  const s = light("Evidence", "How good is the harness: what each step bought", "Three charts, one per dimension, averaged over the four snapshots. Left: how much the answer moves between identical runs. The step that matters is analyst 2 to analyst 3: the answer shape and the verifier take the wobble from three and a half points to under one. Middle: numbers from memory, gone as soon as the evidence is shown. Right: share of claims whose quote code found verbatim; analyst 2 cannot be measured because it quotes nothing. The specialists keep what analyst 3 achieved. For analysts 3 to 8 the wobble is in their lean, which is already in points of probability, so the four bars are comparable.");
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
  const s = light("Evidence", "What the specialists said on 28 October", "Make it concrete: the five leans behind entry #18, and one real claim with the quote code matched. The labour analyst is the one that does not lean hawkish, and because it is a separate reader that dissent is visible rather than averaged away.");
  const rows = [
    [{ text: "Analyst", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Reads", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 } } }, { text: "Lean (5 runs)", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }, { text: "Verified", options: { bold: true, color: THEME.colors.lt1, fill: { color: THEME.colors.dk2 }, align: "center" } }],
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
  ["Analyst results view", "Analyst 1 (naive) card", "Analyst 4 (communications) card"],
  ["Analyst 1: cut 25 at 57%, numbers from memory flagged", "Analyst 4: the lean, grounded, leaked, watch-outs badges; one claim with its quote and the 'quote verified' mark", "Hover a badge for its definition"],
  ["Every claim you see has a quote that code found character for character in the item named.", "The naive analyst still thinks the Fed is cutting. Same model, no evidence."],
  "If asked where a quote comes from, open the statement claim on analyst 4: the quote is the statement's own line, found by code in item fed.statement.2026-09-16.");
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
  const s = light("Limits and next", "What comes next", "Six follow-ups, in order of value. One: pre-registered weight sets scored on every live decision, so the weights stop being judgement. Two: reasoning quality graded by people in the app, which becomes the tenth measured dimension and a gate. Three: an events agent for the regime shifts the models cannot read. Four: a second model family to show the harness, not the model, does the work. Five: other central banks; the chain needs a calendar, a rate series, the statements and a curve, and the scorecard transfers unchanged. Six: better classical models, judged by the expanding window only.");
  text(s, "December is on file: entry #23 for the 9 December meeting, +25 bps 73.6%, no change 16.7%, specialists +4.0. The 28 October call is scored the moment the post-meeting rate row lands.", { x: M, y: 1.4, w: W - 2 * M, h: 0.4, fontSize: 11.5, color: C.accent4 });
  const next = [
    ["Pre-registered weight sets, scored live", "Write down three or four candidate weight sets now (for example market 0.6 / 0.5 / 0.7 with the rest redistributed). Score every set on every live decision with the same log score and Brier. The live set changes only by amendment, on that record. Weights stop being judgement without ever being fitted to the past."],
    ["Reasoning quality, graded by people", "A grading form in the app: a user marks an analyst's answer from 1 to 5 on four questions (did it start from the base rate, argue both sides, say what it was unsure of, say what would prove it wrong). Twenty hand grades become the reference; a model grader is trusted only once it agrees with them. The grade becomes the tenth measured dimension and a gate on the lean."],
    ["An events agent for regime shifts", "1987, 1998, 2008, 2020: the Fed cut on financial stress, not the data the models read. A watch-out agent that scans for bank failures, funding stress and market dislocations and raises a typed watch-out every analyst must answer."],
    ["A second model family", "The same harness, the same snapshots, a different language model. If the ladder reads the same, the harness is doing the work, not the model."],
    ["Other central banks and geographies", "ECB, Bank of England, MAS. The chain needs four things: a meeting calendar, a policy-rate series, the bank's own statements and minutes, and a futures or swap curve. The scorecard, the ledger and the analysts transfer unchanged; only the evidence sources change."],
    ["Better classical models", "The probit's successor: features written down before fitting, a regularised ordinal model, a reliability check beside the log score, and the expanding window as the only judge. A regularised boosted model as one pre-registered candidate. About 130 usable decisions, 68% holds: small models, honestly tested, not big ones."],
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
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Limits and next" });
  s.addText("Three things to take away", { placeholder: "title" });
  s.addText([
    { text: "The harness is the product. Same model, same evidence, same day: naive it wobbles and leaks; harnessed it is stable, quoted and checked.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Judge the process. Eight decisions a year cannot prove skill; a pre-registered scorecard measured on every snapshot can show discipline and catch drift.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "The ask: scrutinise the scorecard, challenge a quote, and tell us which other decisions deserve the same chain. The 28 October call is on file; the 9 December forecast is too.", options: { bullet: true } },
  ], { placeholder: "body" });
  s.addNotes("Close on the ask. The forecast for 28 October is on file; the scoring is automatic from here; what the room can add is scrutiny and the next target.");
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
  const s = light("Backup", "Appendix: how the analysts' score moves the number", "Three parts. The score and why it stops at 10: it is already in points of probability, and 10 is the most any single input may move the number, the same cap as a human view; a wider range would let the analysts write the number, which the design forbids. The average: one vote each. The spread: the points leave every bucket on the hold-or-cut side and land on both hike buckets, in proportion to size and distance from the middle, so the shape of the distribution is kept and nothing goes to zero.");
  // left: the score and the average
  card(s, M, 1.45, 5.9, 5.3);
  text(s, "1. The score", { x: M + 0.25, y: 1.55, w: 5.4, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
  s.addText(bullets([
    "Each specialist returns one number from −10 to +10: how many points of probability its evidence says should move toward a hike (positive) or a cut (negative). It is not a probability and not a rate forecast.",
    "Why it stops at 10: ten points is the most any single input may move the number, the same cap a human view has. A range of −100 to +100 would let the analysts write the number; the design lets them shift it, never write it.",
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
  text(s, "Multiplier = e^(0.153 × bucket number) ÷ 1.0486, the rescaling total. Exactly 4.00 points crossed; the after column is the machine forecast recorded as entry #18. The cruder alternative, taking all 4 points from no change and giving them to +25, is easier to say and would be amendment #9 if preferred.", { x: rx, y: 5.45, w: rw, h: 1.2, fontSize: 10, color: C.accent4 });
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

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
