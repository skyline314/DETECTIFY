/**
 * text-detect.js
 * Backend: POST /text (FormData with file + language)
 * Result: { prediction: "FAKE"/"REAL", probability_ai: 0-1, probability_human: 0-1, confidence_score: 0-1 }
 */
document.addEventListener("DOMContentLoaded", () => {
  const API_TEXT = "/text";

  const textInput = document.getElementById("textInput");
  const fileInput = document.getElementById("fileInput");
  const btnDetect = document.getElementById("btn-detect");
  const btnPaste = document.getElementById("btn-paste");

  let selectedLang = null;

  // --- LANGUAGE SELECTOR ---
  const langBtns = document.querySelectorAll("#langSelector .lang-btn");
  langBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      langBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedLang = btn.dataset.lang;
    });
  });

  // --- PASTE (must choose lang first) ---
  if (btnPaste) btnPaste.addEventListener("click", async () => {
    if (!selectedLang) return alert("Pilih bahasa terlebih dahulu sebelum paste text.");
    try {
      textInput.value = await navigator.clipboard.readText();
      updateWordCount();
    } catch (e) {
      alert("Gagal paste dari clipboard.");
    }
  });

  // --- FILE UPLOAD (must choose lang first) ---
  if (fileInput) fileInput.addEventListener("change", (e) => {
    if (!selectedLang) {
      alert("Pilih bahasa terlebih dahulu sebelum upload file.");
      fileInput.value = "";
      return;
    }
    const file = e.target.files[0];
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (!['txt', 'pdf', 'docx'].includes(ext)) {
        alert("Format file tidak didukung. Gunakan TXT, PDF, atau DOCX.");
        fileInput.value = "";
        return;
      }
      if (ext === 'txt') {
        const reader = new FileReader();
        reader.onload = (ev) => { textInput.value = ev.target.result; updateWordCount(); };
        reader.readAsText(file);
      } else {
        textInput.value = `[File uploaded: ${file.name}]`;
      }
    }
  });

  // --- WORD COUNT ---
  function updateWordCount() {
    const words = textInput.value.trim().split(/\s+/).filter(Boolean).length;
    document.getElementById("wordCount").textContent = words;
  }
  if (textInput) textInput.addEventListener("input", updateWordCount);

  // --- ANALYZE ---
  const handleAnalyze = async () => {
    const text = textInput.value.trim();
    const token = localStorage.getItem("detectify_token");

    if (!selectedLang) return alert("Pilih bahasa terlebih dahulu (English / Indonesia).");
    if (!text && (!fileInput.files || fileInput.files.length === 0)) return alert("Input text atau upload file.");
    if (!token) return (window.location.href = "/auth/get-started");

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("language", selectedLang);

      if (fileInput.files.length > 0 && text === "") {
        formData.append("file", fileInput.files[0]);
      } else {
        const blob = new Blob([text], { type: "text/plain" });
        formData.append("file", blob, "manual_input.txt");
      }

      const res = await fetch(API_TEXT, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Analysis failed");

      if (data.analysis_id) {
        await pollStatus(data.analysis_id, token);
      } else {
        showResult(data);
      }
    } catch (err) {
      alert("Error: " + err.message);
      setLoading(false);
    }
  };

  async function pollStatus(id, token) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/status/${id}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.status === "COMPLETED") {
          clearInterval(interval);
          showResult(data.result);
          setLoading(false);
        } else if (data.status === "FAILED") {
          clearInterval(interval);
          alert("Analisis gagal.");
          setLoading(false);
        }
      } catch (err) {
        clearInterval(interval);
        alert(err.message);
        setLoading(false);
      }
    }, 2000);
  }

  function setLoading(loading) {
    btnDetect.disabled = loading;
    btnDetect.textContent = loading ? "Analyzing..." : "Detect AI";
  }

  function showResult(result) {
    // Backend returns: probability_ai (0-1), probability_human (0-1), prediction, confidence_score
    const probAi = result.probability_ai || 0;
    const probHuman = result.probability_human || 0;

    const aiPct = (probAi * 100).toFixed(1);
    const humanPct = (probHuman * 100).toFixed(1);
    const confidence = (result.confidence_score ? result.confidence_score * 100 : Math.max(probAi, probHuman) * 100).toFixed(1);

    document.getElementById("emptyState").hidden = true;
    document.getElementById("resultBody").hidden = false;

    // Update bars (AI + Human only, no hybrid)
    updateBar("barAi", "pctAi", aiPct);
    updateBar("barHuman", "pctHuman", humanPct);

    // Prediction label
    const prediction = result.prediction || "Unknown";
    const labelText = prediction === "FAKE" ? "AI-Generated" : "Human-Written";

    document.getElementById("confidence").textContent = confidence + "%";
    document.getElementById("signals").textContent = labelText;
    document.getElementById("resultNote").textContent =
      prediction === "FAKE" ? "This text appears AI-generated" :
        prediction === "REAL" ? "This text appears human-written" :
          "Analysis complete";
  }

  function updateBar(barId, textId, val) {
    const el = document.getElementById(barId);
    const txt = document.getElementById(textId);
    if (el) el.style.width = val + "%";
    if (txt) txt.textContent = val + "%";
  }

  if (btnDetect) btnDetect.addEventListener("click", handleAnalyze);
});