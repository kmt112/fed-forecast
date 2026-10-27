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
  const s = light("What FedCast is, and why we built it", "Left: what it is in five lines and today's number. Right: the four reasons, with the honest framing that at five weeks the market is the anchor and the claim is a checkable number, a reusable harness and a method for deciding when a language model may be trusted inside a process. Close on the last line: the first live decision is scored this week.");
  card(s, M, 1.5, 5.6, 5.3);
  text(s, "What it is", { x: M + 0.35, y: 1.7, w: 5, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  s.addText(bullets([
    "A forecast of the next FOMC decision as probabilities over five outcomes, from one frozen, fingerprinted snapshot of evidence: futures, FRED series as first published, statements, minutes, transcript, projections, speeches, 32 years of decisions, prediction-market odds.",
    "Code computes the signals and pools four models with fixed weights: market-implied 0.6, the Fed's own Taylor rules 0.2, prediction-market odds 0.1, historical base rates 0.1.",
    "A language model is used only to read text: five specialist analysts, tools off, every claim quoted and verified by code, whose combined lean can tilt the number by at most 10 points and never write it.",
    "Human judgement enters only through typed, bounded, recorded channels: views, watch-outs, documents, odds.",
    "Every forecast goes into a hash-chained ledger that recomputes exactly from its snapshot.",
  ], { fontSize: 12, color: C.text1 }), { x: M + 0.35, y: 2.2, w: 4.95, h: 3.6, isTextBox: true, margin: 0, valign: "top" });
  text(s, "Today, for 28 October 2026: no change 71%, +25 bps 23%", { x: M + 0.35, y: 5.95, w: 4.95, h: 0.7, fontSize: 13, bold: true, color: C.text2 });
  text(s, "Why we built it", { x: 6.7, y: 1.55, w: 6, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  const why = [
    ["Accuracy is the wrong yardstick at this horizon", "Eight decisions a year, and the futures market already calls about 88% of them a month out. A good year proves nothing. So the system is judged on a ten-dimension process scorecard fixed before any code existed, measured by code on every snapshot, and outcomes are logged but never used to tune."],
    ["A desk needs a number it can challenge", "Every input is visible, every analyst claim carries a quote code has matched, every ledger entry replays. When the number moves, you can see which input moved it and by how much."],
    ["Language models are entering this work unchecked", "Recent papers report 90%+ accuracy from models that read Fed text, on sixteen meetings, with no frozen evidence, no verification and no control. We built the control: the same model with no harness, with evidence only, with structure and verification, with specialisation, so the value of each technique is measured, not asserted."],
    ["The harness is the asset", "The same chain can target the December meeting, the year-end rate or another central bank. The first live decision is scored this week, and the record starts there."],
  ];
  why.forEach(([h, b], i) => {
    const y = 2.1 + i * 1.18;
    numCircle(s, 6.7, y + 0.03, i + 1);
    text(s, h, { x: 7.25, y, w: 5.5, h: 0.35, fontSize: 13, bold: true, color: C.text2 });
    text(s, b, { x: 7.25, y: y + 0.35, w: 5.5, h: 0.85, fontSize: 10.5, color: C.text1 });
  });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
