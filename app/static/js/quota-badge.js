/**
 * quota-badge.js
 * Fetches /auth/quota and renders a quota pill badge into #quotaBadge.
 * Also disables the analyze button if quota is exceeded for free users.
 *
 * Usage: include this script on any feature page that has:
 *   <div id="quotaBadge"></div>
 *   and optionally an analyze button with id="btn-analyze" (or btn-detect, btnUpload, btnDetect)
 */
(function () {
    const ANALYZE_BTN_IDS = ['btn-detect', 'btn-analyze', 'btnUpload', 'btnDetect', 'btnAnalyze', 'btn-humanize'];

    function getToken() {
        return localStorage.getItem('detectify_token');
    }

    function getAnalyzeBtn() {
        for (const id of ANALYZE_BTN_IDS) {
            const el = document.getElementById(id);
            if (el) return el;
        }
        return null;
    }

    function renderBadge(data) {
        const container = document.getElementById('quotaBadge');
        if (!container) return;

        let html = '';

        if (data.is_premium) {
            // Pro: unlimited cyan pill
            html = `
        <div class="quota-badge quota-badge--pro" title="Premium plan — unlimited usage">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1l1.9 3.8 4.1.6-3 2.9.7 4.1L8 10.4l-3.7 1.9.7-4.1L2 5.4l4.1-.6L8 1z"/></svg>
          <span>Pro &mdash; Unlimited</span>
        </div>`;
        } else {
            const { usage, limit, remaining } = data;
            const exceeded = remaining === 0;
            const pct = Math.round((usage / limit) * 100);

            if (exceeded) {
                // Quota habis: merah + disable analyze button
                html = `
          <div class="quota-badge quota-badge--exceeded" title="Daily quota exhausted">
            <svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1a7 7 0 100 14A7 7 0 008 1zm.75 4.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5zm-.75 7a.875.875 0 110-1.75.875.875 0 010 1.75z"/></svg>
            <span>0 / ${limit} &mdash; <a href="/payment/pricing" style="color:inherit;text-decoration:underline;font-weight:700;">Upgrade to Pro</a></span>
          </div>`;

                const btn = getAnalyzeBtn();
                if (btn) {
                    btn.disabled = true;
                    btn.title = 'Daily quota exhausted — upgrade to Pro';
                }
            } else {
                // Free, still has quota
                const cls = pct >= 60 ? 'quota-badge--warn' : 'quota-badge--ok';
                html = `
          <div class="quota-badge ${cls}" title="${remaining} remaining today (resets at midnight UTC)">
            <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.4"/><text x="8" y="11.5" text-anchor="middle" font-size="7" font-weight="700" fill="currentColor">${remaining}</text></svg>
            <span>${usage} / ${limit} uses today</span>
          </div>`;
            }
        }

        container.innerHTML = html;
    }

    function renderGuest() {
        // Not logged in — don't show badge, just hide the container
        const container = document.getElementById('quotaBadge');
        if (container) container.style.display = 'none';
    }

    async function loadQuota() {
        const token = getToken();
        if (!token) { renderGuest(); return; }

        try {
            const res = await fetch('/auth/quota', {
                headers: { Authorization: 'Bearer ' + token }
            });
            if (!res.ok) { renderGuest(); return; }
            const data = await res.json();
            renderBadge(data);
        } catch {
            renderGuest();
        }
    }

    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadQuota);
    } else {
        loadQuota();
    }
})();
