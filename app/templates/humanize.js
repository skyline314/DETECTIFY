const inputEl = document.getElementById("inputText");
const outputEl = document.getElementById("outputText");
const humanizeBtn = document.getElementById("humanizeBtn");

humanizeBtn.addEventListener("click", async () => {
  const text = inputEl.value.trim();
  if (!text) return;

  // contoh payload
  const payload = { text, mode: currentMode };

  // contoh: panggil API
  const res = await fetch("/api/humanize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  outputEl.value = data.humanizedText || "";
});

const copyBtn = document.getElementById("copyBtn");
copyBtn?.addEventListener("click", async () => {
  const text = outputEl.value || "";
  if (!text) return;
  await navigator.clipboard.writeText(text);
});
