document.addEventListener("DOMContentLoaded", () => {
  const API_HUMANIZE = "/analysis/humanize";
  
  const btn = document.getElementById("btn-humanize");
  const input = document.getElementById("textInput");
  const output = document.getElementById("humanizedOutput");
  
  let lang = "id"; 

  // Language selector logic
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.addEventListener("click", (e) => {
        document.querySelectorAll(".lang-btn").forEach(x => x.classList.remove("active"));
        e.target.classList.add("active");
        lang = e.target.dataset.lang;
    });
  });

  if(btn) {
      btn.addEventListener("click", async () => {
        const text = input.value.trim();
        const token = localStorage.getItem("detectify_token");

        if (!text) return alert("Please enter text.");
        if (!token) return (window.location.href = "/auth/get-started");

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
          if (!res.ok) throw new Error(data.error || "Failed");

          if (data.analysis_id) {
            output.value = "Sedang memproses...";
            poll(data.analysis_id, token);
          } else {
            output.value = data.result || "Error";
            resetBtn();
          }

        } catch (err) {
          alert(err.message);
          resetBtn();
        }
      });
  }

  function poll(id, token) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/analysis/${id}`, { 
            headers: {"Authorization": `Bearer ${token}`} 
        });
        const data = await res.json();
        
        if (data.status === "COMPLETED") {
            clearInterval(interval);
            // Sesuaikan key dengan return dari core.py
            output.value = data.result.humanized_text || data.result; 
            resetBtn();
        } else if (data.status === "FAILED") {
            clearInterval(interval);
            output.value = "Gagal memproses.";
            resetBtn();
        }
      } catch (e) {
        clearInterval(interval);
        resetBtn();
      }
    }, 2000);
  }

  function resetBtn(){
      btn.disabled = false;
      btn.textContent = "Humanize Text";
  }
});