document.addEventListener("DOMContentLoaded", () => {
  // CONFIG: Sesuai backend services.py
  const CONFIG = {
    API_URL: "/api/analysis/audio", 
    VALID_EXTS: /\.(mp3|wav|flac)$/i, // Sesuai services.py
    MAX_SIZE: 50 * 1024 * 1024 // 50MB
  };
  
  setupUploader(CONFIG);
});

// --- GENERIC UPLOADER LOGIC (DRY) ---
function setupUploader(conf) {
  const fileInput = document.getElementById("fileInput");
  const btnUpload = document.getElementById("btnUpload");
  const browseBtn = document.getElementById("browseBtn");
  const dropzone = document.getElementById("dropzone");
  const fileName = document.getElementById("fileName");
  const fileInfo = document.getElementById("fileInfo");
  const btnRemove = document.getElementById("btnRemove");
  const progressBar = document.getElementById("progressBar");
  
  let selectedFile = null;

  function handleFile(file) {
      if(!conf.VALID_EXTS.test(file.name)) return alert("Format file tidak didukung.");
      if(file.size > conf.MAX_SIZE) return alert("File terlalu besar.");
      selectedFile = file;
      fileName.textContent = file.name;
      fileInfo.hidden = false;
      btnUpload.disabled = false;
      btnRemove.disabled = false;
  }

  if(browseBtn) browseBtn.addEventListener("click", () => fileInput.click());
  if(fileInput) fileInput.addEventListener("change", (e) => {
      if(e.target.files.length) handleFile(e.target.files[0]);
  });
  if(btnRemove) btnRemove.addEventListener("click", (e) => {
      e.stopPropagation();
      selectedFile = null;
      fileInfo.hidden = true;
      btnUpload.disabled = true;
      fileInput.value = "";
  });

  if(btnUpload) btnUpload.addEventListener("click", () => {
      if(!selectedFile) return;
      const token = localStorage.getItem("detectify_token");
      if(!token) return window.location.href = "/auth/get-started";

      btnUpload.disabled = true;
      btnUpload.textContent = "Uploading...";
      document.getElementById("progressWrap").hidden = false;

      const fd = new FormData();
      fd.append("file", selectedFile);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", conf.API_URL);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      
      xhr.upload.onprogress = (e) => {
          if(e.lengthComputable) {
              const pct = (e.loaded / e.total) * 100;
              progressBar.style.width = pct + "%";
              if(pct >= 100) btnUpload.textContent = "Analyzing...";
          }
      };

      xhr.onload = () => {
          try {
             const data = JSON.parse(xhr.responseText);
             if(data.analysis_id) pollStatus(data.analysis_id, token);
             else showResult(data);
          } catch(e) { alert("Error parsing response"); btnUpload.disabled = false; }
      };
      
      xhr.send(fd);
  });

  function pollStatus(id, token) {
      const interval = setInterval(async () => {
          const res = await fetch(`/analysis/${id}`, { headers: {"Authorization": `Bearer ${token}`} });
          const data = await res.json();
          if(data.status === "COMPLETED") {
              clearInterval(interval);
              showResult(data.result);
              btnUpload.textContent = "Analyze";
              btnUpload.disabled = false;
          } else if (data.status === "FAILED") {
              clearInterval(interval);
              alert("Gagal.");
              btnUpload.disabled = false;
          }
      }, 2000);
  }

  function showResult(res) {
      const label = res.label || "Unknown";
      const conf = ((res.confidence || res.ai_score || 0) * 100).toFixed(1);
      alert(`Result: ${label} (${conf}%)`);
  }
}