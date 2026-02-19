/**
 * login-guard.js
 * Shared utility for all detection/analysis pages.
 * - Shows a login-required modal if not logged in
 * - Shows a daily-limit-exceeded modal if backend returns 403
 * - Both modals have CTAs (Login / Upgrade)
 */
(function () {
  const TOKEN_KEY = "detectify_token";
  const LOGIN_URL = "/auth/get-started";
  const PRICING_URL = "/api/payment/pricing";

  // --- Inject modal CSS ---
  const style = document.createElement("style");
  style.textContent = `
    .guard-overlay {
      position: fixed; inset: 0; z-index: 9999;
      background: rgba(0,0,0,.55); backdrop-filter: blur(6px);
      display: flex; align-items: center; justify-content: center;
      animation: guardFadeIn .2s ease;
    }
    @keyframes guardFadeIn {
      from { opacity: 0; } to { opacity: 1; }
    }
    .guard-modal {
      width: min(420px, 90%); border-radius: 20px; padding: 32px 28px;
      text-align: center; position: relative;
      animation: guardSlideUp .25s ease;
    }
    @keyframes guardSlideUp {
      from { transform: translateY(16px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    html[data-theme="light"] .guard-modal {
      background: #fff; border: 1px solid rgba(0,0,0,.08);
      box-shadow: 0 20px 60px rgba(0,0,0,.15);
    }
    html[data-theme="dark"] .guard-modal {
      background: linear-gradient(150deg, #111827, #0f172a);
      border: 1px solid rgba(255,255,255,.1);
      box-shadow: 0 20px 60px rgba(0,0,0,.5);
      color: #eaf2ff;
    }
    .guard-modal__icon {
      width: 64px; height: 64px; margin: 0 auto 16px;
      border-radius: 50%; display: grid; place-items: center;
    }
    .guard-modal__icon--lock {
      background: linear-gradient(135deg, #0ea5c7, #7c3aed);
    }
    .guard-modal__icon--limit {
      background: linear-gradient(135deg, #f59e0b, #ef4444);
    }
    .guard-modal__icon svg { color: #fff; }
    .guard-modal__title {
      font-size: 20px; font-weight: 700; margin: 0 0 8px;
    }
    .guard-modal__desc {
      font-size: 14px; line-height: 1.6; margin: 0 0 20px; opacity: .75;
    }
    .guard-modal__btn {
      display: inline-flex; align-items: center; justify-content: center;
      gap: 8px; padding: 12px 28px; border-radius: 999px;
      font-size: 14px; font-weight: 700; border: none; cursor: pointer;
      transition: transform .15s, filter .15s; text-decoration: none;
    }
    .guard-modal__btn:hover { transform: translateY(-1px); filter: brightness(1.08); }
    .guard-modal__btn--primary {
      background: linear-gradient(135deg, #0ea5c7, #7c3aed);
      color: #fff; box-shadow: 0 8px 24px rgba(14,165,199,.25);
    }
    .guard-modal__btn--secondary {
      background: transparent; color: inherit; opacity: .6;
      margin-top: 8px; font-weight: 500;
    }
  `;
  document.head.appendChild(style);

  // --- Show modal helper ---
  function showModal(html, closeable) {
    const overlay = document.createElement("div");
    overlay.className = "guard-overlay";
    overlay.innerHTML = html;
    document.body.appendChild(overlay);

    if (closeable) {
      overlay.querySelectorAll("[data-dismiss]").forEach(btn => {
        btn.addEventListener("click", () => overlay.remove());
      });
      overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
    }

    return overlay;
  }

  // --- LOGIN REQUIRED modal ---
  window.showLoginRequired = function () {
    return showModal(`
      <div class="guard-modal">
        <div class="guard-modal__icon guard-modal__icon--lock">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <rect x="5" y="11" width="14" height="10" rx="3" stroke="currentColor" stroke-width="2"/>
            <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 class="guard-modal__title">Login Required</h3>
        <p class="guard-modal__desc">
          You need to log in first before using this feature.<br>
          Create a free account or sign in to continue.
        </p>
        <a class="guard-modal__btn guard-modal__btn--primary" href="${LOGIN_URL}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" stroke-width="2"/>
            <path d="M10 17l5-5-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Log In / Sign Up
        </a>
      </div>
    `, false);
  };

  // --- DAILY LIMIT EXCEEDED modal ---
  window.showLimitExceeded = function () {
    // Try to get daily limit from cached user data
    const dailyLimit = window._detectifyDailyLimit || 5;

    return showModal(`
      <div class="guard-modal">
        <div class="guard-modal__icon guard-modal__icon--limit">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 7v6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="12" cy="17" r="1.2" fill="currentColor"/>
          </svg>
        </div>
        <h3 class="guard-modal__title">Daily Limit Reached</h3>
        <p class="guard-modal__desc">
          You've used all <strong>${dailyLimit}</strong> free detections for today.<br>
          Upgrade to Premium for <strong>unlimited</strong> access, or come back tomorrow.
        </p>
        <a class="guard-modal__btn guard-modal__btn--primary" href="${PRICING_URL}">
          ⚡ Upgrade to Premium
        </a>
        <br>
        <button class="guard-modal__btn guard-modal__btn--secondary" data-dismiss type="button">
          Maybe later
        </button>
      </div>
    `, true);
  };

  /**
   * Helper: check if user is logged in.
   * If not, shows login modal and returns false.
   */
  window.requireLogin = function () {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      window.showLoginRequired();
      return false;
    }
    return true;
  };

  /**
   * Helper: handle API response errors.
   * Returns true if the error was handled (login/limit modal shown).
   */
  window.handleApiError = function (response, data) {
    if (response.status === 401 || response.status === 422) {
      localStorage.removeItem(TOKEN_KEY);
      window.showLoginRequired();
      return true;
    }
    if (response.status === 403 && data?.error?.includes("Kuota")) {
      window.showLimitExceeded();
      return true;
    }
    return false;
  };
})();
