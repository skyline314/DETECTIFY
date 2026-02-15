/**
 * text-detect.js
 * Backend: POST /analysis/text (FormData)
 */

document.addEventListener("DOMContentLoaded", () => {
  const API_TEXT = "/analysis/text";
  
  const textInput = document.getElementById("textInput");
  const fileInput = document.getElementById("fileInput");
  const btnDetect = document.getElementById("btn-detect");
  const btnPaste = document.getElementById("btn-paste");

  // --- CORE LOGIC ---
  const handleAnalyze = async () => {
    const text = textInput.value.trim();
    const token = localStorage.getItem("detectify_token");

    if (!text && (!fileInput.files || fileInput.files.length === 0)) {
        alert("Input text or upload file.");
        return;
    }
    if (!token) return (window.location.href = "/auth/get-started");

    setLoading(true);

    try {
      const formData = new FormData();
      
      // LOGIKA UTAMA: Backend butuh FILE
      if (fileInput.files.length > 0 && text === "") {
         // Case 1: Upload File Asli
         formData.append("file", fileInput.files[0]);
      } else {
         // Case 2: Paste Text -> Ubah jadi File Blob
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

      // Polling karena backend Async (Celery)
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
        const res = await fetch(`/analysis/${id}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.status === "COMPLETED") {
          clearInterval(interval);
          showResult(data.result);
          setLoading(false);
        } else if (data.status === "FAILED") {
          clearInterval(interval);
          throw new Error("Analysis failed");
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
    const ai = (result.ai_score * 100).toFixed(1);
    const human = (result.human_score * 100).toFixed(1);
    const hybrid = (result.hybrid_score || 0 * 100).toFixed(1);
    
    document.getElementById("emptyState").hidden = true;
    document.getElementById("resultBody").hidden = false;
    
    updateBar("barAi", "pctAi", ai);
    updateBar("barHuman", "pctHuman", human);
    updateBar("barHybrid", "pctHybrid", hybrid);
    
    document.getElementById("confidence").textContent = Math.max(ai, human) + "%";
    document.getElementById("signals").textContent = result.label || "Unknown";
  }

  function updateBar(barId, textId, val) {
    const el = document.getElementById(barId);
    const txt = document.getElementById(textId);
    if(el) el.style.width = val + "%";
    if(txt) txt.textContent = val + "%";
  }

  if(btnDetect) btnDetect.addEventListener("click", handleAnalyze);
  
  if(btnPaste) btnPaste.addEventListener("click", async () => {
    textInput.value = await navigator.clipboard.readText();
  });
  
  if(fileInput) fileInput.addEventListener("change", (e) => {
     // Preview text
     const file = e.target.files[0];
     if(file){
        const reader = new FileReader();
        reader.onload = (ev) => textInput.value = ev.target.result;
        reader.readAsText(file);
     }
  });
});