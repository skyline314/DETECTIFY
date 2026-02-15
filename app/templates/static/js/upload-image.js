document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const browseBtn = document.getElementById("browseBtn");
    const btnUpload = document.getElementById("btnUpload");
    const imagePreview = document.getElementById("imagePreview");
    const dropzoneIcon = document.getElementById("dropzoneIcon");

    // --- 1. LOGIKA INTERAKSI (KLIK & SERET) ---

    // A. Klik Kotak Langsung Membuka File Explorer
    dropzone.addEventListener("click", (e) => {
        // Jangan trigger jika yang diklik adalah tombol browse (karena sudah punya listener sendiri)
        if (e.target !== browseBtn) fileInput.click();
    });

    browseBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // Cegah double trigger
        fileInput.click();
    });

    // B. Logika Drag & Drop
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
            fileInput.files = e.dataTransfer.files; // Masukkan file ke input
            handlePreview(e.dataTransfer.files[0]); // Jalankan preview
        }
    });

    // C. Change Listener untuk Input Tradisional
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) handlePreview(fileInput.files[0]);
    });

    // --- 2. LOGIKA PREVIEW GAMBAR ---
    function handlePreview(file) {
        if (!file.type.startsWith("image/")) return alert("Hanya file gambar!");

        // Update Info UI
        document.getElementById("fileName").textContent = file.name;
        document.getElementById("fileInfo").hidden = false;
        btnUpload.disabled = false;
        document.getElementById("btnRemove").disabled = false;

        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = "block";
            dropzoneIcon.style.display = "none";
        };
        reader.readAsDataURL(file);
    }

    // --- 3. LOGIKA UPLOAD & POLLING (Identik Console.html) ---
    btnUpload.addEventListener("click", async () => {
        const fileObj = fileInput.files[0];
        const token = localStorage.getItem('detectify_token');

        if (!fileObj || !token) return alert("Pilih file atau login kembali!");

        btnUpload.disabled = true;
        btnUpload.textContent = "⏳ Processing...";
        document.getElementById("progressWrap").hidden = false;

        const fd = new FormData();
        fd.append('file', fileObj);

        try {
            const res = await fetch('/image', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: fd
            });
            const d = await res.json();
            if (d.analysis_id) startPolling(d.analysis_id, token);
        } catch (e) {
            alert("Error: " + e);
            resetUI();
        }
    });

    function startPolling(id, token) {
        let iv = setInterval(async () => {
            const res = await fetch(`/status/${id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const d = await res.json();
            if (d.status === 'COMPLETED') {
                clearInterval(iv);
                showResult(d.result);
            }
        }, 2000);
    }

    function showResult(result) {
        document.getElementById("progressWrap").hidden = true;
        const card = document.getElementById("resultCard");
        card.style.display = "block";
        
        const label = result.label || "UNKNOWN";
        const score = (result.confidence || 0) * 100;

        document.getElementById("resultLabel").textContent = label;
        document.getElementById("resultScore").textContent = score.toFixed(1) + "%";
        resetUI();
    }

    function resetUI() {
        btnUpload.disabled = false;
        btnUpload.textContent = "Analyze";
    }
});