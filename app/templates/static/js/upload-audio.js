document.addEventListener("DOMContentLoaded", () => {
    const CONFIG = {
        API_URL: "/audio",
        VALID_EXTS: /\.(mp3|wav|flac)$/i,
        MAX_SIZE: 50 * 1024 * 1024
    };

    const fileInput = document.getElementById("fileInput");
    const btnUpload = document.getElementById("btnUpload");
    const browseBtn = document.getElementById("browseBtn");
    const dropzone = document.getElementById("dropzone");
    const fileName = document.getElementById("fileName");
    const fileInfo = document.getElementById("fileInfo");
    const btnRemove = document.getElementById("btnRemove");
    const progressBar = document.getElementById("progressBar");
    const progressWrap = document.getElementById("progressWrap");
    const audioPreview = document.getElementById("audioPreview");
    const dropzoneIcon = document.getElementById("dropzoneIcon");

    let selectedFile = null;
    let fakeProgressTimer = null;

    // --- FILE HANDLING ---
    function handleFile(file) {
        if (!CONFIG.VALID_EXTS.test(file.name)) return alert("Format file tidak didukung. Gunakan MP3, WAV, atau FLAC.");
        if (file.size > CONFIG.MAX_SIZE) return alert("File terlalu besar (maks 50MB).");
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.hidden = false;
        btnUpload.disabled = false;
        btnRemove.disabled = false;
        const url = URL.createObjectURL(file);
        audioPreview.src = url;
        audioPreview.style.display = "block";
        if (dropzoneIcon) dropzoneIcon.style.display = "none";
    }

    function resetFile() {
        selectedFile = null;
        fileInfo.hidden = true;
        btnUpload.disabled = true;
        btnRemove.disabled = true;
        fileInput.value = "";
        audioPreview.pause();
        audioPreview.src = "";
        audioPreview.style.display = "none";
        if (dropzoneIcon) dropzoneIcon.style.display = "";
        document.getElementById("resultCard").style.display = "none";
    }

    // --- EVENTS ---
    if (browseBtn) browseBtn.addEventListener("click", () => fileInput.click());
    if (fileInput) fileInput.addEventListener("change", (e) => { if (e.target.files.length) handleFile(e.target.files[0]); });
    if (btnRemove) btnRemove.addEventListener("click", (e) => { e.stopPropagation(); resetFile(); });

    if (dropzone) {
        ["dragover", "dragleave"].forEach(evt => {
            dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.toggle("dropzone--active", evt === "dragover"); });
        });
        dropzone.addEventListener("drop", (e) => {
            e.preventDefault(); dropzone.classList.remove("dropzone--active");
            if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
        });
    }

    // --- FAKE PROGRESS (realistic animation during analysis) ---
    function startFakeProgress() {
        let pct = 0;
        progressWrap.hidden = false;
        progressBar.style.width = "0%";
        progressBar.style.transition = "width 0.5s ease";

        fakeProgressTimer = setInterval(() => {
            if (pct < 30) pct += Math.random() * 8;
            else if (pct < 60) pct += Math.random() * 4;
            else if (pct < 85) pct += Math.random() * 2;
            else if (pct < 92) pct += Math.random() * 0.5;
            // Never exceed 92% until result arrives
            pct = Math.min(pct, 92);
            progressBar.style.width = pct + "%";
        }, 600);
    }

    function finishProgress() {
        clearInterval(fakeProgressTimer);
        progressBar.style.width = "100%";
        setTimeout(() => { progressWrap.hidden = true; progressBar.style.width = "0%"; }, 500);
    }

    // --- UPLOAD ---
    if (btnUpload) btnUpload.addEventListener("click", () => {
        if (!selectedFile) return;
        const token = localStorage.getItem("detectify_token");
        if (!token) return (window.location.href = "/auth/get-started");

        btnUpload.disabled = true;
        btnUpload.textContent = "Uploading...";
        document.getElementById("resultCard").style.display = "none";

        // Real progress for upload phase
        progressWrap.hidden = false;
        progressBar.style.transition = "width 0.3s ease";

        const fd = new FormData();
        fd.append("file", selectedFile);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", CONFIG.API_URL);
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                // Upload phase: 0-30% of total bar
                const uploadPct = (e.loaded / e.total) * 30;
                progressBar.style.width = uploadPct + "%";
            }
        };

        xhr.onload = () => {
            try {
                const data = JSON.parse(xhr.responseText);
                if (data.analysis_id) {
                    btnUpload.textContent = "Analyzing...";
                    // Switch to fake progress for analysis phase (30-92%)
                    progressBar.style.width = "30%";
                    startFakeProgress();
                    pollStatus(data.analysis_id, token);
                } else {
                    finishProgress();
                    showResult(data);
                    resetUI();
                }
            } catch (e) {
                alert("Error parsing response");
                finishProgress();
                resetUI();
            }
        };

        xhr.onerror = () => { alert("Network error"); finishProgress(); resetUI(); };
        xhr.send(fd);
    });

    // --- POLLING ---
    function pollStatus(id, token) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/status/${id}`, { headers: { "Authorization": `Bearer ${token}` } });
                const data = await res.json();
                if (data.status === "COMPLETED") {
                    clearInterval(interval);
                    finishProgress();
                    showResult(data.result);
                    resetUI();
                } else if (data.status === "FAILED") {
                    clearInterval(interval);
                    finishProgress();
                    alert("Analisis gagal: " + (data.error || "Unknown error"));
                    resetUI();
                }
            } catch (e) {
                clearInterval(interval);
                finishProgress();
                resetUI();
            }
        }, 2000);
    }

    // --- RESULT with probability bar ---
    function showResult(res) {
        const card = document.getElementById("resultCard");
        card.style.display = "block";

        // Determine label and scores
        // Audio returns: { prediction: "FAKE"/"REAL", confidence_score: 0-100, details: {...} }
        const prediction = res.prediction || res.label || "Unknown";
        const confidenceRaw = res.confidence_score || res.confidence || 0;
        // confidence_score is already 0-100 from backend
        const confidence = confidenceRaw > 1 ? confidenceRaw : confidenceRaw * 100;

        // Calculate AI vs Human percentages (total = 100%)
        let aiPct, humanPct;
        if (prediction === "FAKE") {
            aiPct = confidence;
            humanPct = 100 - confidence;
        } else {
            humanPct = confidence;
            aiPct = 100 - confidence;
        }

        // Update label with color
        const labelEl = document.getElementById("resultLabel");
        labelEl.textContent = prediction === "FAKE" ? "AI Generated" : "Human / Real";
        labelEl.className = "result-card__label";
        labelEl.classList.add(prediction === "FAKE" ? "result-card__label--fake" : "result-card__label--real");

        // Animate bars (delayed for visual effect)
        setTimeout(() => {
            document.getElementById("barAi").style.width = aiPct.toFixed(1) + "%";
            document.getElementById("barHuman").style.width = humanPct.toFixed(1) + "%";
        }, 100);

        // Update percentage labels
        document.getElementById("pctAi").textContent = aiPct.toFixed(1) + "%";
        document.getElementById("pctHuman").textContent = humanPct.toFixed(1) + "%";

        // Confidence
        document.getElementById("resultConfidence").textContent = confidence.toFixed(1) + "%";

        // Details
        const detailsEl = document.getElementById("resultDetails");
        if (res.details) {
            detailsEl.textContent = `Segments: ${res.details.segments_total || '-'} (Real: ${res.details.segments_real || 0}, Fake: ${res.details.segments_fake || 0})`;
        } else {
            detailsEl.textContent = "";
        }
    }

    function resetUI() {
        btnUpload.disabled = false;
        btnUpload.textContent = "Analyze";
    }
});