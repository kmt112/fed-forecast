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
const OUT = path.join(__dirname, "FedCast_Fullerton_short.pptx");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "FedCast";
pres.title = "FedCast: short brief";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.6;

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
const light = (title, notes) => { const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Brief" }); s.addText(title, { placeholder: "title" }); if (notes) s.addNotes(notes); return s; };
const text = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top", ...o });
const card = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || THEME.colors.lt2 }, line: { color: fill || THEME.colors.lt2 }, rectRadius: 0.12, shadow: { type: "outer", blur: 4, offset: 1, angle: 90, color: "000000", opacity: 0.08 } });
const bullets = (items, o = {}) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6, ...o } }));
const numCircle = (s, x, y, n) => { s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 } }); text(s, String(n), { x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle" }); };

pres.addSection({ title: "Brief" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Brief" });
  s.addText("FedCast", { placeholder: "title" });
  s.addText("A forecaster for the next Federal Reserve rate decision, built to be judged by its process rather than its luck", { placeholder: "body" });
  text(s, "Tan Kah Ming · Fullerton · October 2026", { x: M, y: 6.4, w: 8, h: 0.4, fontSize: 14, color: THEME.colors.accent5 });
  s.addNotes("One line: a language model inside an engineered harness gives forecasts that are measurably more repeatable and more faithful to evidence than the same model asked naively, and we prove it by measuring the process, not by waiting for eight decisions a year to come true.");
}
{
  const s = light("About me", "One minute. The thread: every system on the right put a model's output in front of people making live decisions, and the hard part was never the model, it was earning trust in what it said. FedCast is that problem made explicit and measurable.");
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
  const s = light("What FedCast is, and why we built it", "Left: what it is, in one line, the diagram, and four things it does. Right: the three reasons we built it. Spend the time on the right-hand side; the diagram is there so the room can see the four families and that code, not a model, combines them.");
  text(s, "A forecast of the next FOMC decision as probabilities over five outcomes, from one frozen snapshot of evidence. Today, for 28 October 2026: no change 71%, +25 bps 23%.", { x: M, y: 1.35, w: W - 2 * M, h: 0.6, fontSize: 13.5, color: C.text1 });
  // the diagram: four families -> pool -> forecast
  const fam = [
    ["Economic predictors", "Fed funds futures, the Fed's own Taylor rules, prediction-market odds", THEME.colors.dk2],
    ["Empirical data", "What followed each kind of decision over 32 years of FOMC history", THEME.colors.dk2],
    ["Classic ML", "An ordered probit fitted on data as first published; shown, not yet in the number", THEME.colors.accent4],
    ["LLM-derived", "Five specialist analysts reading the Fed's own words; every claim quoted and verified by code", THEME.colors.accent2],
  ];
  const bx = M, by = 2.05, bw = 2.75, bh = 0.74, gapY = 0.08;
  fam.forEach(([h, b, col], i) => {
    const y = by + i * (bh + gapY);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y, w: bw, h: bh, fill: { color: col }, line: { color: col }, rectRadius: 0.08 });
    text(s, h, { x: bx + 0.14, y: y + 0.06, w: bw - 0.28, h: 0.3, fontSize: 12, bold: true, color: C.background1 });
    text(s, b, { x: bx + 0.14, y: y + 0.33, w: bw - 0.28, h: 0.4, fontSize: 8.5, color: C.background1 });
    s.addShape(pres.shapes.LINE, { x: bx + bw + 0.08, y: y + bh / 2, w: 0.4, h: 0, line: { color: THEME.colors.accent4, width: 1.5, endArrowType: "triangle" } });
  });
  const totalH = 4 * bh + 3 * gapY;
  const px = bx + bw + 0.55;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: by, w: 1.35, h: totalH, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent5 }, rectRadius: 0.1 });
  text(s, "Pool", { x: px, y: by + 0.25, w: 1.35, h: 0.4, fontSize: 14, bold: true, color: C.text2, align: "center" });
  text(s, "Combined by code with fixed, published weights. No model writes the number.", { x: px + 0.1, y: by + 0.75, w: 1.15, h: 2.8, fontSize: 9, color: C.text1, align: "center" });
  s.addShape(pres.shapes.LINE, { x: px + 1.42, y: by + totalH / 2, w: 0.4, h: 0, line: { color: THEME.colors.accent4, width: 1.5, endArrowType: "triangle" } });
  const fx = px + 1.9;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: by + totalH / 2 - 0.7, w: 1.4, h: 1.4, fill: { color: THEME.colors.dk2 }, line: { color: THEME.colors.dk2 }, rectRadius: 0.1 });
  text(s, "Forecast", { x: fx, y: by + totalH / 2 - 0.6, w: 1.4, h: 0.4, fontSize: 13, bold: true, color: C.background1, align: "center" });
  text(s, "no change 71%\n+25 bps 23%", { x: fx, y: by + totalH / 2 - 0.15, w: 1.4, h: 0.8, fontSize: 10.5, color: C.background1, align: "center" });
  // what it does
  text(s, "What it does", { x: M, y: 5.45, w: 7.0, h: 0.3, fontSize: 12, bold: true, color: C.text2 });
  s.addText(bullets([
    "Freezes one fingerprinted snapshot of evidence per forecast; nothing outside it may be read.",
    "Enforces repeatability: five identical runs per analyst, tools off, every quote checked by code, a pre-registered scorecard on every snapshot.",
    "Offers typed channels for human judgement (views, watch-outs, documents, odds): bounded, recorded, scored afterwards. None active today.",
    "Keeps every snapshot and forecast in a hash-chained ledger, so the number's path can be read back as information arrived.",
  ], { fontSize: 9.5, color: C.text1, paraSpaceAfter: 2 }), { x: M, y: 5.75, w: 7.1, h: 1.2, isTextBox: true, margin: 0, valign: "top" });
  // why we built it
  const rx = 8.0, rw = W - M - rx;
  text(s, "Why we built it", { x: rx, y: 2.0, w: rw, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
  const why = [
    ["Fed prediction tools are judged on outcomes, which cannot be repeated", "There are many of them. Eight decisions a year make a hit rate neither predictable nor repeatable as a measure of a tool. We judge ours on a pre-registered process: is the same answer produced from the same evidence, can every claim be traced, does a shock move the number the right way."],
    ["Most lean too far one way", "Either empirical formulas and market prices alone, or everything thrown at a language model. Ours harmonises the three: empirical data, classic ML and a harnessed LLM, each with a stated role and a stated weight, combined by code."],
    ["What that buys", "Auditability: every input visible, every forecast replayable. Evidence-based: every claim quoted and verified, nothing from memory. A harnessed LLM that cannot give random or spurious answers, and a naive LLM kept as the control that shows what the harness adds. Users can study how one piece of evidence moves the decision. The model can be scrutinised and improved, rather than hoping the LLM works."],
  ];
  why.forEach(([h, b], i) => {
    const y = 2.5 + i * 1.5;
    numCircle(s, rx, y + 0.02, i + 1);
    text(s, h, { x: rx + 0.55, y: y - 0.02, w: rw - 0.55, h: 0.4, fontSize: 12, bold: true, color: C.text2, valign: "top" });
    text(s, b, { x: rx + 0.55, y: y + 0.42, w: rw - 0.55, h: 1.05, fontSize: 9.5, color: C.text1 });
  });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
