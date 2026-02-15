(() => {
  const WORD_LIMIT_FREE = 500;

  // Kalau sudah ada backend:
  // const HUMANIZE_ENDPOINT = "https://api.domain.com/humanize";
  const HUMANIZE_ENDPOINT = ""; // kosong = demo lokal

  const input = document.getElementById("inputText");
  const counter = document.getElementById("counter");
  const statusEl = document.getElementById("status");

  const outText = document.getElementById("outputText");
  const outPlaceholder = document.getElementById("outPlaceholder");
  const btnCopy = document.getElementById("btnCopy");

  const btnCheck = document.getElementById("btnCheck");
  const btnHumanize = document.getElementById("btnHumanize");

  const tabs = Array.from(document.querySelectorAll(".mode__tab"));
  let mode = "casual";

  const txtInput = document.getElementById("txtInput");
  const btnUploadTxt = document.getElementById("btnUploadTxt");

  function setStatus(msg = "", type = "info") {
    statusEl.textContent = msg;
    statusEl.dataset.type = type;
  }

  function wordsCount(text) {
    const t = (text || "").trim();
    if (!t) return 0;
    return t.split(/\s+/).filter(Boolean).length;
  }

  function clampToLimit(text, limit) {
    const parts = (text || "").trim().split(/\s+/).filter(Boolean);
    if (parts.length <= limit) return text || "";
    return parts.slice(0, limit).join(" ");
  }

  function syncCounter() {
    const w = wordsCount(input.value);
    counter.textContent = `${w} / ${WORD_LIMIT_FREE} words`;

    if (w > WORD_LIMIT_FREE) {
      input.value = clampToLimit(input.value, WORD_LIMIT_FREE);
      setStatus(`Maksimal ${WORD_LIMIT_FREE} kata untuk plan Free. Teks dipotong otomatis.`, "err");
      counter.textContent = `${WORD_LIMIT_FREE} / ${WORD_LIMIT_FREE} words`;
    } else {
      setStatus("", "info");
    }
  }

  function setOutput(text) {
    const t = (text || "").trim();
    if (!t) {
      outText.hidden = true;
      outPlaceholder.hidden = false;
      btnCopy.disabled = true;
      return;
    }
    outText.textContent = t;
    outText.hidden = false;
    outPlaceholder.hidden = true;
    btnCopy.disabled = false;
  }

  // Mode switching
  tabs.forEach((b) => {
    b.addEventListener("click", () => {
      tabs.forEach(x => {
        x.classList.remove("is-active");
        x.setAttribute("aria-selected", "false");
      });
      b.classList.add("is-active");
      b.setAttribute("aria-selected", "true");
      mode = b.dataset.mode || "casual";
      setStatus(`Mode: ${mode}`, "info");
    });
  });

  // Upload .txt -> masuk ke textarea
  btnUploadTxt?.addEventListener("click", () => txtInput.click());
  txtInput?.addEventListener("change", async () => {
    const file = txtInput.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setStatus("File .txt terlalu besar (maks 2MB untuk demo).", "err");
      txtInput.value = "";
      return;
    }

    const text = await file.text();
    input.value = text;
    syncCounter();
    setStatus("Teks dari file berhasil dimuat.", "ok");
  });

  // Basic AI-check demo (placeholder, bukan detektor sungguhan)
  btnCheck.addEventListener("click", () => {
    const t = input.value.trim();
    if (!t) return setStatus("Masukkan teks dulu.", "err");

    const w = wordsCount(t);
    const avgLen = t.split(/[.!?]/).filter(Boolean).map(s => s.trim().split(/\s+/).length);
    const avg = avgLen.length ? (avgLen.reduce((a, b) => a + b, 0) / avgLen.length) : 0;

    // Heuristik sederhana: makin panjang & repetitif -> “lebih AI”
    const uniq = new Set(t.toLowerCase().split(/\s+/).filter(Boolean));
    const uniqRatio = uniq.size / Math.max(1, w);

    let risk = "Low";
    if (avg > 20 || uniqRatio < 0.45) risk = "Medium";
    if (avg > 28 || uniqRatio < 0.35) risk = "High";

    setStatus(`AI-likeness (demo): ${risk}`, "ok");
  });

  // Humanize
  btnHumanize.addEventListener("click", async () => {
    const t = input.value.trim();
    if (!t) return setStatus("Masukkan teks dulu.", "err");

    setStatus("Memproses…", "info");

    try {
      if (HUMANIZE_ENDPOINT) {
        // Real API
        const res = await fetch(HUMANIZE_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: t, mode })
        });
        if (!res.ok) throw new Error(`Server error (${res.status}).`);
        const data = await res.json();
        setOutput(data.output || "");
      } else {
        // Demo lokal: “humanize” ringan biar UI hidup
        const out = humanizeLocal(t, mode);
        setOutput(out);
      }

      setStatus("Selesai.", "ok");
    } catch (e) {
      setStatus(e?.message || "Gagal memproses.", "err");
    }
  });

  // Copy output
  btnCopy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(outText.textContent || "");
      setStatus("Output berhasil di-copy.", "ok");
    } catch {
      setStatus("Gagal copy (browser membatasi clipboard).", "err");
    }
  });

  // Keep counter updated
  input.addEventListener("input", syncCounter);

  // Demo local transformer
  function humanizeLocal(text, mode) {
    let s = text;

    // rapikan spasi
    s = s.replace(/\s+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/[ \t]{2,}/g, " ").trim();

    // “human” touches (ringan)
    if (mode === "casual") {
      s = s
        .replace(/\bdo not\b/gi, "don't")
        .replace(/\bcan not\b/gi, "can't")
        .replace(/\bI am\b/gi, "I'm")
        .replace(/\bIt is\b/gi, "It's");
      s = addSoftener(s, ["Honestly,", "Quick note:", "Just to be clear,"]);
    }

    if (mode === "academic") {
      s = s.replace(/\bI think\b/gi, "It appears that")
           .replace(/\bkind of\b/gi, "to some extent");
      s = addTransition(s, ["Moreover,", "In addition,", "Notably,"]);
    }

    if (mode === "professional") {
      s = s.replace(/\bASAP\b/gi, "as soon as possible")
           .replace(/\bgonna\b/gi, "going to");
      s = addTransition(s, ["To summarize,", "In practice,", "As a next step,"]);
    }

    return s;
  }

  function addSoftener(text, starters) {
    const lines = text.split("\n");
    if (lines.length && lines[0].length > 0 && !/^[A-Z].*[:,]$/.test(lines[0])) {
      lines[0] = `${starters[Math.floor(Math.random() * starters.length)]} ${lines[0]}`;
    }
    return lines.join("\n");
  }

  function addTransition(text, starters) {
    const sentences = text.split(/(\. |\? |! )/);
    if (sentences.length >= 3) {
      const idx = Math.min(2, sentences.length - 1);
      sentences[idx] = `${starters[Math.floor(Math.random() * starters.length)]} ${sentences[idx]}`;
    }
    return sentences.join("");
  }

  // init
  syncCounter();
  setOutput("");
})();
