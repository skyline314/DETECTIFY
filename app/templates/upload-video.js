(() => {
  const MAX_MB = 100;
  const MAX_BYTES = MAX_MB * 1024 * 1024;

  const ALLOWED_MIME = ["video/mp4", "video/quicktime", "video/mpeg"];
  const ALLOWED_EXT = [".mp4", ".mov", ".mpeg"];

  // Isi kalau sudah ada backend (contoh: https://api.domain.com/upload-video)
  const UPLOAD_ENDPOINT = ""; // kosong = simulasi

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");

  const fileInfo = document.getElementById("fileInfo");
  const fileName = document.getElementById("fileName");
  const fileMeta = document.getElementById("fileMeta");

  const btnRemove = document.getElementById("btnRemove");
  const btnUpload = document.getElementById("btnUpload");

  const statusEl = document.getElementById("status");
  const progressWrap = document.getElementById("progressWrap");
  const progressBar = document.getElementById("progressBar");

  let selectedFile = null;
  let uploading = false;

  function setStatus(msg = "", type = "info") {
    statusEl.textContent = msg;
    statusEl.dataset.type = type;
  }

  function prettySize(bytes) {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(mb >= 10 ? 0 : 1)} MB`;
  }

  function isAllowed(file) {
    const name = (file?.name || "").toLowerCase();
    const okExt = ALLOWED_EXT.some(ext => name.endsWith(ext));
    const okType = ALLOWED_MIME.includes(file.type) || okExt;
    return okType;
  }

  function resetUI() {
    selectedFile = null;
    fileInput.value = "";
    fileInfo.hidden = true;

    btnRemove.disabled = true;
    btnUpload.disabled = true;

    progressWrap.hidden = true;
    progressBar.style.width = "0%";

    setStatus("");
  }

  function applyFile(file) {
    if (!file) return;

    if (!isAllowed(file)) {
      setStatus("Format tidak didukung. Gunakan MP4, MOV, atau MPEG.", "err");
      resetUI();
      return;
    }

    if (file.size > MAX_BYTES) {
      setStatus(`Ukuran file terlalu besar. Maksimal ${MAX_MB} MB.`, "err");
      resetUI();
      return;
    }

    selectedFile = file;

    fileInfo.hidden = false;
    fileName.textContent = file.name;
    fileMeta.textContent = `${prettySize(file.size)} • ${file.type || "video"}`;

    btnRemove.disabled = false;
    btnUpload.disabled = false;

    setStatus("File siap diunggah.", "ok");
  }

  function openPicker() {
    if (uploading) return;
    fileInput.click();
  }

  // Browse files link/button
  browseBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    openPicker();
  });

  // Click dropzone also opens picker
  dropzone.addEventListener("click", (e) => {
    // biar klik tombol "browse files" tidak double-trigger
    if (e.target === browseBtn) return;
    openPicker();
  });

  dropzone.addEventListener("keydown", (e) => {
    if (uploading) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  });

  fileInput.addEventListener("change", () => {
    if (uploading) return;
    applyFile(fileInput.files?.[0]);
  });

  // Drag & drop
  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!uploading) dropzone.classList.add("is-drag");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("is-drag");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (uploading) return;
    applyFile(e.dataTransfer?.files?.[0]);
  });

  btnRemove.addEventListener("click", () => {
    if (uploading) return;
    resetUI();
  });

  btnUpload.addEventListener("click", async () => {
    if (!selectedFile || uploading) return;

    uploading = true;
    btnUpload.disabled = true;
    btnRemove.disabled = true;

    progressWrap.hidden = false;
    progressBar.style.width = "0%";
    setStatus("Uploading…", "info");

    try {
      if (!UPLOAD_ENDPOINT) {
        await simulateUpload((p) => (progressBar.style.width = `${p}%`));
        setStatus("Upload selesai (simulasi). Isi UPLOAD_ENDPOINT untuk upload real.", "ok");
      } else {
        await realUpload(selectedFile, UPLOAD_ENDPOINT, (p) => {
          progressBar.style.width = `${p}%`;
        });
        setStatus("Upload berhasil.", "ok");
      }
    } catch (err) {
      setStatus(err?.message || "Upload gagal. Coba lagi.", "err");
      progressBar.style.width = "0%";
    } finally {
      uploading = false;
      btnRemove.disabled = !selectedFile;
      btnUpload.disabled = !selectedFile;
    }
  });

  function simulateUpload(onProgress) {
    return new Promise((resolve) => {
      let p = 0;
      const t = setInterval(() => {
        p += Math.random() * 12 + 6;
        if (p >= 100) {
          p = 100;
          onProgress(p);
          clearInterval(t);
          setTimeout(resolve, 250);
        } else {
          onProgress(Math.floor(p));
        }
      }, 140);
    });
  }

  function realUpload(file, endpoint, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append("file", file);

      xhr.open("POST", endpoint, true);

      xhr.upload.addEventListener("progress", (e) => {
        if (!e.lengthComputable) return;
        const pct = Math.round((e.loaded / e.total) * 100);
        onProgress(pct);
      });

      xhr.onreadystatechange = () => {
        if (xhr.readyState !== 4) return;
        if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.responseText);
        else reject(new Error(`Server error (${xhr.status}).`));
      };

      xhr.onerror = () => reject(new Error("Network error."));
      xhr.send(form);
    });
  }

  resetUI();
})();
