document.addEventListener("DOMContentLoaded", () => {
  const API_HUMANIZE = "/humanize";

  const btn = document.getElementById("btn-humanize");
  const input = document.getElementById("textInput");
  const output = document.getElementById("humanizedOutput");


  let lang = null;

  // --- Language selector ---
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.addEventListener("click", (e) => {
      document.querySelectorAll(".lang-btn").forEach(x => x.classList.remove("active"));
      e.target.classList.add("active");
      lang = e.target.dataset.lang;
    });
  });

  // --- Word count ---
  function updateWordCount() {
    const words = input.value.trim().split(/\s+/).filter(Boolean).length;
    document.getElementById("wordCount").textContent = words;
  }
  input.addEventListener("input", updateWordCount);



  // --- Copy result ---
  const btnCopy = document.getElementById("btn-copy");
  if (btnCopy) btnCopy.addEventListener("click", () => {
    if (output.value) {
      navigator.clipboard.writeText(output.value);
      btnCopy.title = "Copied!";
      setTimeout(() => { btnCopy.title = ""; }, 2000);
    }
  });

  // --- Show/update result panel ---
  function showResultPanel(status) {
    document.getElementById("emptyState").hidden = true;
    document.getElementById("resultBody").hidden = false;
    const resultLang = document.getElementById("resultLang");
    if (resultLang) resultLang.textContent = lang === "id" ? "Indonesia" : "English";
    setStatus(status || "Processing...");
  }

  function setStatus(text, color) {
    const el = document.getElementById("resultStatus");
    if (el) {
      el.textContent = text;
      el.style.color = color || "";
    }
  }

  // --- Humanize ---
  if (btn) {
    btn.addEventListener("click", async () => {
      const text = input.value.trim();

      if (!lang) return alert("Please choose language first (English / Indonesia).");
      if (!text) return alert("Please enter text.");

      // Login guard
      if (!window.requireLogin || !window.requireLogin()) return;
      const token = localStorage.getItem("detectify_token");

      btn.disabled = true;
      btn.textContent = "Processing...";

      try {
        const res = await fetch(API_HUMANIZE, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({ text, language: lang })
        });

        const data = await res.json();

        // Handle auth/limit errors
        if (window.handleApiError && window.handleApiError(res, data)) {
          resetBtn();
          return;
        }
        if (!res.ok) throw new Error(data.error || "Failed");

        if (data.analysis_id) {
          showResultPanel("Processing...");
          output.value = "";
          poll(data.analysis_id, token);
        } else if (data.result) {
          showResultPanel("Success");
          setStatus("Success", "var(--success, #22c55e)");
          output.value = data.result;
          resetBtn();
        } else {
          throw new Error("Respons tidak valid");
        }

      } catch (err) {
        alert("Error: " + err.message);
        resetBtn();
      }
    });
  }

  function poll(id, token) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/status/${id}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.status === "COMPLETED") {
          clearInterval(interval);
          const result = data.result;

          // Backend returns { humanized_text: "..." }
          let text = "";
          if (typeof result === "string") {
            text = result;
          } else if (result && result.humanized_text) {
            text = result.humanized_text;
          } else {
            text = JSON.stringify(result);
          }

          output.value = text;
          setStatus("Success", "var(--success, #22c55e)");
          resetBtn();
        } else if (data.status === "FAILED") {
          clearInterval(interval);
          output.value = "Gagal memproses teks.";
          setStatus("Failed", "#ef4444");
          resetBtn();
        }
        // else: still PENDING/PROCESSING, keep polling
      } catch (e) {
        clearInterval(interval);
        output.value = "Error saat memproses.";
        setStatus("Error", "#ef4444");
        resetBtn();
      }
    }, 2500);
  }

  function resetBtn() {
    btn.disabled = false;
    btn.textContent = "Humanize Text";
  }
});