/* text-detect.js
   - Paste text (clipboard)
   - Upload doc (txt/md)
   - Word limit 500
   - Detect AI (demo heuristics) + update bars UI
   - Theme toggle via data-theme attr (dark/light)
*/

(function () {
  const $ = (sel) => document.querySelector(sel);

  const textInput = $("#textInput");
  const btnPaste = $("#btn-paste");
  const fileInput = $("#fileInput");
  const btnDetect = $("#btn-detect");

  const wordCountEl = $("#wordCount");
  const wordLimitEl = $("#wordLimit");

  const emptyState = $("#emptyState");
  const resultBody = $("#resultBody");

  const pctAi = $("#pctAi");
  const pctHybrid = $("#pctHybrid");
  const pctHuman = $("#pctHuman");

  const barAi = $("#barAi");
  const barHybrid = $("#barHybrid");
  const barHuman = $("#barHuman");

  const resultNote = $("#resultNote");
  const confidenceEl = $("#confidence");
  const signalsEl = $("#signals");

  const LIMIT = 500;
  wordLimitEl.textContent = String(LIMIT);

  // ===== Helpers
  function words(text) {
    return (text || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);
  }

  function clamp(n, a, b) {
    return Math.max(a, Math.min(b, n));
  }

  function setPercent(elText, elBar, value) {
    const v = clamp(Math.round(value), 0, 100);
    elText.textContent = `${v}%`;
    elBar.style.width = `${v}%`;
  }

  function showResult() {
  emptyState.hidden = true;
  resultBody.hidden = false;

  // safety: kalau ada CSS yang ngebypass hidden
  emptyState.style.display = "none";
  resultBody.style.display = "block";
  }

  function showEmpty() {
    emptyState.hidden = false;
    resultBody.hidden = true;

    emptyState.style.display = "grid"; // sesuai layout kamu yang center
    resultBody.style.display = "none";
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("df_theme", theme);
  }

  function initTheme() {
    const saved = localStorage.getItem("df_theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
  }

  // ===== Word limit enforcement
  function enforceLimit() {
    const w = words(textInput.value);
    if (w.length > LIMIT) {
      textInput.value = w.slice(0, LIMIT).join(" ");
    }
    wordCountEl.textContent = String(words(textInput.value).length);
  }

  // ===== Demo analyzer (heuristic)
  // Ini placeholder supaya UI "hidup".
  // Nanti gampang diganti fetch() ke backend beneran.
  function analyze(text) {
    const w = words(text);
    const len = w.length;

    // Signals (heuristic): repetisi, panjang kalimat, punctuation ratio
    const raw = text.trim();
    const sentences = raw ? raw.split(/[.!?]+/).filter(Boolean) : [];
    const avgSentLen = sentences.length ? (len / sentences.length) : len;

    const unique = new Set(w.map((x) => x.toLowerCase()));
    const uniqRatio = len ? unique.size / len : 1;

    const punct = (raw.match(/[,;:]/g) || []).length;
    const punctRatio = len ? punct / len : 0;

    // Heuristic scoring -> convert to percentages
    let ai = 0;

    // very long, very even sentences => a bit more "AI-like"
    ai += clamp((avgSentLen - 16) * 2.2, 0, 35);

    // low uniqueness (repetitive) => more "AI-like"
    ai += clamp((0.72 - uniqRatio) * 120, 0, 35);

    // punctuation sparse on longer text => could be AI-ish
    if (len > 120) ai += clamp((0.03 - punctRatio) * 500, 0, 20);

    // normalize by length (very short text is unreliable)
    if (len < 40) ai *= 0.55;
    if (len < 15) ai *= 0.25;

    ai = clamp(ai, 3, 92);

    // Hybrid gets some share if AI not too high/low
    let hybrid = clamp(100 - Math.abs(50 - ai) * 1.25, 5, 55);
    // Human is the remainder with some bias when ai is low
    let human = clamp(100 - ai - hybrid, 3, 92);

    // Re-balance to sum 100
    const sum = ai + hybrid + human;
    ai = (ai / sum) * 100;
    hybrid = (hybrid / sum) * 100;
    human = 100 - ai - hybrid;

    // Confidence proxy
    let conf = 0.35 + clamp(len / 600, 0, 0.45);
    if (len < 40) conf -= 0.15;
    conf = clamp(conf, 0.15, 0.85);

    const sig = [
      `avg sentence length ~ ${avgSentLen.toFixed(1)} words`,
      `uniqueness ${(uniqRatio * 100).toFixed(0)}%`,
      `punct ratio ${(punctRatio * 100).toFixed(1)}%`,
    ].join(" • ");

    return {
      ai,
      hybrid,
      human,
      confidence: `${Math.round(conf * 100)}%`,
      signals: sig,
    };
  }

  // ===== Actions
  btnPaste?.addEventListener("click", async () => {
    try {
      const t = await navigator.clipboard.readText();
      if (t) {
        textInput.value = t.trim();
        enforceLimit();
      }
    } catch {
      // fallback: focus textarea (user can paste manually)
      textInput.focus();
    }
  });

  fileInput?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Basic type check
    const ok =
      file.type.startsWith("text/") ||
      /\.(txt|md|text)$/i.test(file.name);

    if (!ok) {
      alert("Please upload a .txt or .md file.");
      e.target.value = "";
      return;
    }

    const content = await file.text();
    textInput.value = (content || "").trim();
    enforceLimit();
    e.target.value = "";
  });

  textInput?.addEventListener("input", enforceLimit);

  btnDetect?.addEventListener("click", () => {
    const t = (textInput.value || "").trim();
    const wc = words(t).length;

    if (!t || wc === 0) {
      showEmpty();
      return;
    }

    const res = analyze(t);
    showResult();

    setPercent(pctAi, barAi, res.ai);
    setPercent(pctHybrid, barHybrid, res.hybrid);
    setPercent(pctHuman, barHuman, res.human);

    resultNote.textContent = `Analyzed ${wc} words`;
    confidenceEl.textContent = res.confidence;
    signalsEl.textContent = res.signals;
  });

  // ===== Theme toggles
  $("#btn-light")?.addEventListener("click", () => setTheme("light"));
  $("#btn-dark")?.addEventListener("click", () => setTheme("dark"));

  // ===== Init
  initTheme();
  enforceLimit();
  showEmpty();
})();
