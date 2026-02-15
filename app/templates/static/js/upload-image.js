document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const browseBtn = document.getElementById("browseBtn");
    const btnUpload = document.getElementById("btnUpload");
    const imagePreview = document.getElementById("imagePreview");
    const dropzoneIcon = document.getElementById("dropzoneIcon");
    const progressBar = document.getElementById("progressBar");
    const progressWrap = document.getElementById("progressWrap");

    let fakeProgressTimer = null;

    // --- 1. INTERAKSI (KLIK & SERET) ---
    dropzone.addEventListener("click", (e) => {
        if (e.target !== browseBtn) fileInput.click();
    });

    browseBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    ["dragover", "dragleave"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.toggle("dropzone--active", eventName === "dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dropzone--active");
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handlePreview(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) handlePreview(fileInput.files[0]);
    });

    // --- 2. PREVIEW GAMBAR ---
    function handlePreview(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['jpg', 'jpeg', 'png'].includes(ext)) return alert("Format file tidak didukung. Gunakan JPG, JPEG, atau PNG.");
        document.getElementById("fileName").textContent = file.name;
        document.getElementById("fileInfo").hidden = false;
        btnUpload.disabled = false;
        document.getElementById("btnRemove").disabled = false;
        document.getElementById("btnRemove").disabled = false;

        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = "block";
            dropzoneIcon.style.display = "none";
        };
        reader.readAsDataURL(file);
    }

    // Remove button
    document.getElementById("btnRemove").addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.value = "";
        document.getElementById("fileInfo").hidden = true;
        btnUpload.disabled = true;
        imagePreview.src = "";
        imagePreview.style.display = "none";
        dropzoneIcon.style.display = "";
        document.getElementById("resultCard").style.display = "none";
    });

    // --- FAKE PROGRESS ---
    function startFakeProgress() {
        let pct = 30;
        progressBar.style.transition = "width 0.5s ease";

        fakeProgressTimer = setInterval(() => {
            if (pct < 50) pct += Math.random() * 8;
            else if (pct < 70) pct += Math.random() * 4;
            else if (pct < 85) pct += Math.random() * 2;
            else if (pct < 92) pct += Math.random() * 0.5;
            pct = Math.min(pct, 92);
            progressBar.style.width = pct + "%";
        }, 600);
    }

    function finishProgress() {
        clearInterval(fakeProgressTimer);
        progressBar.style.width = "100%";
        setTimeout(() => { progressWrap.hidden = true; progressBar.style.width = "0%"; }, 500);
    }

    // --- 3. UPLOAD & POLLING ---
    btnUpload.addEventListener("click", async () => {
        const fileObj = fileInput.files[0];
        const token = localStorage.getItem('detectify_token');
        if (!fileObj || !token) return alert("Pilih file atau login kembali!");

        btnUpload.disabled = true;
        btnUpload.textContent = "Uploading...";
        document.getElementById("resultCard").style.display = "none";
        progressWrap.hidden = false;
        progressBar.style.transition = "width 0.3s ease";

        const fd = new FormData();
        fd.append('file', fileObj);

        try {
            // Use XHR for upload progress
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/image');
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const uploadPct = (e.loaded / e.total) * 30;
                    progressBar.style.width = uploadPct + "%";
                }
            };

            xhr.onload = () => {
                try {
                    const d = JSON.parse(xhr.responseText);
                    if (d.analysis_id) {
                        btnUpload.textContent = "Analyzing...";
                        progressBar.style.width = "30%";
                        startFakeProgress();
                        startPolling(d.analysis_id, token);
                    } else {
                        finishProgress();
                        showResult(d);
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
        } catch (e) {
            alert("Error: " + e);
            finishProgress();
            resetUI();
        }
    });

    function startPolling(id, token) {
        let iv = setInterval(async () => {
            try {
                const res = await fetch(`/status/${id}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const d = await res.json();
                if (d.status === 'COMPLETED') {
                    clearInterval(iv);
                    finishProgress();
                    showResult(d.result);
                    resetUI();
                } else if (d.status === 'FAILED') {
                    clearInterval(iv);
                    finishProgress();
                    alert("Analisis gagal: " + (d.error || "Unknown error"));
                    resetUI();
                }
            } catch (e) {
                clearInterval(iv);
                finishProgress();
                resetUI();
            }
        }, 2000);
    }

    // --- RESULT with probability bar ---
    function showResult(result) {
        const card = document.getElementById("resultCard");
        card.style.display = "block";

        // Image returns: { prediction: "FAKE"/"REAL"/"SUSPICIOUS", confidence: 0-100, raw_score: 0-1 }
        const prediction = result.prediction || result.label || "UNKNOWN";
        const confidenceRaw = result.confidence || result.confidence_score || 0;
        const confidence = confidenceRaw > 1 ? confidenceRaw : confidenceRaw * 100;
        const rawScore = result.raw_score || 0;

        // Calculate AI vs Human from raw_score (0=REAL, 1=FAKE)
        let aiPct, humanPct;
        if (rawScore > 0) {
            // Use raw sigmoid score for more accurate split
            aiPct = rawScore * 100;
            humanPct = (1 - rawScore) * 100;
        } else if (prediction === "FAKE") {
            aiPct = confidence;
            humanPct = 100 - confidence;
        } else if (prediction === "SUSPICIOUS") {
            aiPct = 50;
            humanPct = 50;
        } else {
            humanPct = confidence;
            aiPct = 100 - confidence;
        }

        const labelEl = document.getElementById("resultLabel");
        labelEl.className = "result-card__label";
        if (prediction === "FAKE") {
            labelEl.textContent = "AI Generated";
            labelEl.classList.add("result-card__label--fake");
        } else if (prediction === "SUSPICIOUS") {
            labelEl.textContent = "Suspicious";
            labelEl.classList.add("result-card__label--suspicious");
        } else {
            labelEl.textContent = "Human / Real";
            labelEl.classList.add("result-card__label--real");
        }

        setTimeout(() => {
            document.getElementById("barAi").style.width = aiPct.toFixed(1) + "%";
            document.getElementById("barHuman").style.width = humanPct.toFixed(1) + "%";
        }, 100);

        document.getElementById("pctAi").textContent = aiPct.toFixed(1) + "%";
        document.getElementById("pctHuman").textContent = humanPct.toFixed(1) + "%";
        document.getElementById("resultConfidence").textContent = confidence.toFixed(1) + "%";

        const detailsEl = document.getElementById("resultDetails");
        detailsEl.textContent = result.status ? `Status: ${result.status}` : "";
    }

    function resetUI() {
        btnUpload.disabled = false;
        btnUpload.textContent = "Analyze";
    }
});