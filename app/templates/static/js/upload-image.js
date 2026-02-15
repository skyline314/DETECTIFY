(() => {
  "use strict";

  const MAX_MB = 10;
  const MAX_BYTES = MAX_MB * 1024 * 1024;

  const ALLOWED_MIME = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
  const ALLOWED_EXT = [".png", ".jpg", ".jpeg", ".webp"];

  // Set this when you have a backend endpoint (example: https://api.domain.com/upload-image)
  const UPLOAD_ENDPOINT = ""; // empty = simulated upload

  const el = {
    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("fileInput"),
    browseBtn: document.getElementById("browseBtn"),

    fileInfo: document.getElementById("fileInfo"),
    fileName: document.getElementById("fileName"),
    fileMeta: document.getElementById("fileMeta"),

    btnRemove: document.getElementById("btnRemove"),
    btnUpload: document.getElementById("btnUpload"),

    status: document.getElementById("status"),
    progressWrap: document.getElementById("progressWrap"),
    progressBar: document.getElementById("progressBar"),
  };

  if (!el.dropzone || !el.fileInput) return;

  let selectedFile = null;
  let uploading = false;

  const setStatus = (msg = "", type = "info") => {
    if (!el.status) return;
    el.status.textContent = msg;
    el.status.dataset.type = type;
  };

  const prettySize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(mb >= 10 ? 0 : 1)} MB`;
  };

  const isAllowed = (file) => {
    const name = (file?.name || "").toLowerCase();
    const okExt = ALLOWED_EXT.some((ext) => name.endsWith(ext));
    const okType = ALLOWED_MIME.includes(file.type) || okExt;
    return okType;
  };

  const resetUI = () => {
    selectedFile = null;
    el.fileInput.value = "";
    el.fileInfo && (el.fileInfo.hidden = true);

    el.btnRemove && (el.btnRemove.disabled = true);
    el.btnUpload && (el.btnUpload.disabled = true);

    if (el.progressWrap) el.progressWrap.hidden = true;
    if (el.progressBar) el.progressBar.style.width = "0%";

    setStatus("");
  };

  const applyFile = (file) => {
    if (!file) return;

    if (!isAllowed(file)) {
      setStatus("Format tidak didukung. Gunakan PNG / JPG / JPEG / WEBP.", "err");
      resetUI();
      return;
    }

    if (file.size > MAX_BYTES) {
      setStatus(`Ukuran file terlalu besar. Maksimal ${MAX_MB} MB.`, "err");
      resetUI();
      return;
    }

    selectedFile = file;

    if (el.fileInfo) el.fileInfo.hidden = false;
    if (el.fileName) el.fileName.textContent = file.name;
    if (el.fileMeta) el.fileMeta.textContent = `${prettySize(file.size)} • ${file.type || "image"}`;

    if (el.btnRemove) el.btnRemove.disabled = false;
    if (el.btnUpload) el.btnUpload.disabled = false;

    setStatus("File siap diunggah.", "ok");
  };

  const openPicker = () => {
    if (uploading) return;
    el.fileInput.click();
  };

  el.browseBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    openPicker();
  });

  el.dropzone.addEventListener("click", (e) => {
    if (e.target === el.browseBtn) return;
    openPicker();
  });

  el.dropzone.addEventListener("keydown", (e) => {
    if (uploading) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  });

  el.fileInput.addEventListener("change", () => {
    if (uploading) return;
    applyFile(el.fileInput.files?.[0]);
  });

  // Drag & drop
  ["dragenter", "dragover"].forEach((evt) => {
    el.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!uploading) el.dropzone.classList.add("is-drag");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    el.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      el.dropzone.classList.remove("is-drag");
    });
  });

  el.dropzone.addEventListener("drop", (e) => {
    if (uploading) return;
    applyFile(e.dataTransfer?.files?.[0]);
  });

  el.btnRemove?.addEventListener("click", () => {
    if (uploading) return;
    resetUI();
  });

  el.btnUpload?.addEventListener("click", async () => {
    if (!selectedFile || uploading) return;

    uploading = true;
    el.btnUpload.disabled = true;
    el.btnRemove && (el.btnRemove.disabled = true);

    if (el.progressWrap) el.progressWrap.hidden = false;
    if (el.progressBar) el.progressBar.style.width = "0%";
    setStatus("Uploading…", "info");

    try {
      if (!UPLOAD_ENDPOINT) {
        await simulateUpload((p) => (el.progressBar.style.width = `${p}%`));
        setStatus("Upload selesai (simulasi). Isi UPLOAD_ENDPOINT untuk upload real.", "ok");
      } else {
        await realUpload(selectedFile, UPLOAD_ENDPOINT, (p) => {
          el.progressBar.style.width = `${p}%`;
        });
        setStatus("Upload berhasil.", "ok");
      }
    } catch (err) {
      setStatus(err?.message || "Upload gagal. Coba lagi.", "err");
      if (el.progressBar) el.progressBar.style.width = "0%";
    } finally {
      uploading = false;
      el.btnRemove && (el.btnRemove.disabled = !selectedFile);
      el.btnUpload && (el.btnUpload.disabled = !selectedFile);
    }
  });

  function simulateUpload(onProgress) {
    return new Promise((resolve) => {
      let p = 0;
      const t = setInterval(() => {
        p += Math.random() * 15 + 8;
        if (p >= 100) {
          p = 100;
          onProgress(p);
          clearInterval(t);
          setTimeout(resolve, 200);
        } else {
          onProgress(Math.floor(p));
        }
      }, 120);
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
