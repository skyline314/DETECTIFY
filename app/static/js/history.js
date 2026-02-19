/**
 * history.js
 * Fetches history data from /history API and populates the sidebar + result card.
 */
(function () {
    const TOKEN_KEY = "detectify_token";

    // ---- DOM refs ----
    const fileList = document.getElementById("historyFileList");
    const resultCard = document.getElementById("historyResultCard");
    const noSelection = document.getElementById("historyNoSelection");
    const searchInput = document.getElementById("historySearch");

    const elFilename = document.getElementById("historyFilename");
    const elRisk = document.getElementById("historyRisk");
    const elHumanProb = document.getElementById("historyHumanProb");
    const elAiProb = document.getElementById("historyAiProb");
    const elBarFill = document.getElementById("historyBarFill");
    const elShield = document.getElementById("historyShieldPath");
    const elShieldCheck = document.getElementById("historyShieldCheck");
    const elType = document.getElementById("historyType");
    const elDetails = document.getElementById("historyDetails");
    const elStats = document.getElementById("historyStats");
    const sortDateSelect = document.getElementById("historySortDate");
    const filterTypeSelect = document.getElementById("historyFilterType");

    let historyItems = [];
    let activeId = null;

    // ---- helpers ----
    function clamp(n, min, max) {
        return Math.max(min, Math.min(max, n));
    }

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    /**
     * Truncate filename to maxLen characters, preserving the extension.
     * e.g. "very_long_filename_here.mp3" → "very_long_filen....mp3"
     */
    function truncateFilename(name, maxLen) {
        if (!name || name.length <= maxLen) return name || "Untitled";
        const dotIndex = name.lastIndexOf(".");
        if (dotIndex === -1 || dotIndex === 0) {
            // no extension or hidden file
            return name.substring(0, maxLen - 3) + "...";
        }
        const ext = name.substring(dotIndex); // e.g. ".mp3"
        const baseTrunc = maxLen - ext.length - 3; // space for "..."
        if (baseTrunc <= 3) return name.substring(0, maxLen - 3) + "...";
        return name.substring(0, baseTrunc) + "..." + ext;
    }

    // ---- parse result_summary ----
    /**
     * Parse result_summary from DB into { human, ai } percentages (0-100).
     *
     * Formats from backend:
     * TEXT:  { prediction, confidence_score, probability_ai, probability_human }  (0.0-1.0)
     * IMAGE: { prediction, confidence (0-100), status, raw_score (0-1) }
     * AUDIO: { prediction, confidence_score (0-100), details: { segments_total, segments_fake, segments_real } }
     * VIDEO: { prediction, confidence_score (0-100), details: { total_frames_analyzed, vote_distribution } }
     * HUMANIZE: no probability — just pass-through text
     */
    function parseResult(item) {
        const s = item.result_summary;
        let human = 50, ai = 50;

        if (!s || typeof s !== "object") return { human, ai };

        const prediction = (s.prediction || "").toUpperCase();

        // --- TEXT: has probability_human / probability_ai (0.0–1.0) ---
        if (s.probability_human !== undefined && s.probability_ai !== undefined) {
            human = parseFloat(s.probability_human) * 100;
            ai = parseFloat(s.probability_ai) * 100;
        }
        // --- IMAGE: has confidence (already 0-100) and raw_score ---
        else if (s.confidence !== undefined && s.raw_score !== undefined) {
            const conf = parseFloat(s.confidence);
            if (prediction === "FAKE") {
                ai = conf;
                human = 100 - conf;
            } else if (prediction === "REAL") {
                human = conf;
                ai = 100 - conf;
            } else {
                // SUSPICIOUS
                ai = 50;
                human = 50;
            }
        }
        // --- AUDIO / VIDEO: has confidence_score (0-100) and prediction ---
        else if (s.confidence_score !== undefined) {
            const conf = parseFloat(s.confidence_score);
            if (prediction === "FAKE") {
                ai = conf;
                human = 100 - conf;
            } else {
                human = conf;
                ai = 100 - conf;
            }
        }

        human = clamp(human, 0, 100);
        ai = clamp(ai, 0, 100);
        return { human, ai };
    }

    // ---- get detail text for segmented types ----
    function getDetailText(item) {
        const s = item.result_summary;
        if (!s || typeof s !== "object") return "";

        const type = (item.analysis_type || "").toUpperCase();

        // Audio details
        if (type === "AUDIO" && s.details) {
            const d = s.details;
            return `Segments: ${d.segments_total || "-"} (Real: ${d.segments_real || 0}, Fake: ${d.segments_fake || 0})`;
        }

        // Video details
        if (type === "VIDEO" && s.details) {
            const d = s.details;
            const dist = d.vote_distribution || {};
            return `Frames analyzed: ${d.total_frames_analyzed || "-"} | Votes: FAKE=${dist.FAKE || 0}, REAL=${dist.REAL || 0}`;
        }

        // Text details
        if (type === "TEXT") {
            const parts = [];
            if (s.language) parts.push(`Language: ${s.language}`);
            if (s.model_used) parts.push(`Model: ${s.model_used}`);
            return parts.join(" | ");
        }

        // Image details
        if (type === "IMAGE") {
            const parts = [];
            if (s.status) parts.push(`Status: ${s.status}`);
            if (s.raw_score !== undefined) parts.push(`Raw score: ${s.raw_score}`);
            return parts.join(" | ");
        }

        return "";
    }

    // ---- render file list ----
    function renderFileList(items) {
        if (!fileList) return;
        fileList.innerHTML = "";

        if (items.length === 0) {
            fileList.innerHTML = '<div class="history-empty">No history yet</div>';
            return;
        }

        items.forEach((item) => {
            const el = document.createElement("div");
            el.className = "history-file" + (item.analysis_id === activeId ? " active" : "");
            el.dataset.id = item.analysis_id;

            const typeLabel = (item.analysis_type || "").replace("_", " ");
            const displayName = truncateFilename(item.file_name, 28);
            el.innerHTML = `
        <div class="history-file__name" title="${item.file_name || ''}">${displayName}</div>
        <div class="history-file__type">${typeLabel}</div>
      `;

            el.addEventListener("click", () => selectItem(item));
            fileList.appendChild(el);
        });
    }

    // ---- select item ----
    function selectItem(item) {
        activeId = item.analysis_id;

        // highlight in sidebar
        document.querySelectorAll(".history-file").forEach((el) => {
            el.classList.toggle("active", el.dataset.id === activeId);
        });

        // show result card
        if (resultCard) resultCard.hidden = false;
        if (noSelection) noSelection.hidden = true;

        // populate
        const { human, ai } = parseResult(item);

        const isHumanize = (item.analysis_type || "").toUpperCase() === "HUMANIZE";

        // Hide stats container if Humanize
        if (elStats) elStats.hidden = isHumanize;

        if (elFilename) elFilename.textContent = item.file_name || "Untitled";
        if (elType) elType.textContent = (item.analysis_type || "").replace("_", " ");

        // risk
        if (elRisk) {
            elRisk.textContent = ai > 50 ? "HIGH RISK" : "LOW RISK";
            elRisk.className = "history-risk " + (ai > 50 ? "high" : "low");
        }

        // shield
        if (elShield) {
            const green = "#16a34a", red = "#ef4444";
            const colors = ai > 50
                ? { stop1: red, stop2: "#dc2626" }
                : { stop1: green, stop2: "#15803d" };

            // Fix: gradient stops are in <defs>, not inside the path
            const stops = document.querySelectorAll("#historyShieldGrad stop");
            if (stops[0]) stops[0].setAttribute("stop-color", colors.stop1);
            if (stops[1]) stops[1].setAttribute("stop-color", colors.stop2);

            // Dynamic glow color
            elShield.style.filter = ai > 50
                ? "drop-shadow(0 8px 14px rgba(239, 68, 68, .25))"
                : "drop-shadow(0 8px 14px rgba(22, 163, 74, .16))";
        }
        if (elShieldCheck) {
            elShieldCheck.setAttribute("d", ai > 50
                ? "M55 50 L73 50 M64 41 L64 59"  // plus/cross for high risk
                : "M45 65l12 12 28-32"              // checkmark for low risk
            );
        }

        // probs
        if (elHumanProb) elHumanProb.textContent = Math.round(human) + "%";
        if (elAiProb) elAiProb.textContent = Math.round(ai) + "%";

        // bar
        if (elBarFill) {
            elBarFill.style.width = human + "%";
            elBarFill.classList.toggle("is-full", human >= 100);
        }

        // details
        if (elDetails) {
            const detail = getDetailText(item);
            elDetails.textContent = detail;
            elDetails.style.display = detail ? "block" : "none";
        }
    }

    // ---- sort & filter logic ----
    function applyFilterAndSort() {
        const q = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const sortDateMode = sortDateSelect ? sortDateSelect.value : "newest";
        const filterType = filterTypeSelect ? filterTypeSelect.value : "all";

        // 1. Filter (Search + Type)
        let result = historyItems;

        // Search filter
        if (q) {
            result = result.filter((i) =>
                (i.file_name || "").toLowerCase().includes(q) ||
                (i.analysis_type || "").toLowerCase().includes(q)
            );
        }

        // Type filter
        if (filterType !== "all") {
            // Backend types: TEXT, IMAGE, VIDEO, AUDIO, HUMANIZE
            // Our select values: text, image, video, audio, humanize
            result = result.filter((i) =>
                (i.analysis_type || "").toLowerCase() === filterType
            );
        }

        // 2. Sort (Date)
        result.sort((a, b) => {
            const dateA = new Date(a.created_at);
            const dateB = new Date(b.created_at);

            if (sortDateMode === "newest") return dateB - dateA;
            if (sortDateMode === "oldest") return dateA - dateB;
            return 0;
        });

        renderFileList(result);
    }

    // Event listeners
    if (searchInput) searchInput.addEventListener("input", applyFilterAndSort);
    if (sortDateSelect) sortDateSelect.addEventListener("change", applyFilterAndSort);
    if (filterTypeSelect) filterTypeSelect.addEventListener("change", applyFilterAndSort);

    // ---- fetch history ----
    async function loadHistory() {
        const token = getToken();
        if (!token) {
            if (fileList) fileList.innerHTML = '<div class="history-empty">Please log in to see history</div>';
            return;
        }

        try {
            const res = await fetch("/history", {
                headers: { Authorization: "Bearer " + token },
            });
            if (!res.ok) {
                throw new Error("Failed to fetch");
            }
            historyItems = await res.json();
            renderFileList(historyItems);

            // auto-select first completed item
            const firstCompleted = historyItems.find((i) => i.status === "COMPLETED");
            if (firstCompleted) selectItem(firstCompleted);
        } catch (err) {
            console.error("History fetch error:", err);
            if (fileList) fileList.innerHTML = '<div class="history-empty">Failed to load history</div>';
        }
    }

    // init
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", loadHistory);
    } else {
        loadHistory();
    }
})();
