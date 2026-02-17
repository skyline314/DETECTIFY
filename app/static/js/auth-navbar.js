/**
 * auth-navbar.js
 * Loaded on EVERY page. Checks login state and swaps "Get Started" with
 * a profile avatar + username, plus a Chrome-style profile popup.
 */
(function () {
  const TOKEN_KEY = "detectify_token";
  const AUTH_URL = "/auth/get-started";
  const PRICING_URL = "/api/payment/pricing";

  // ---- helpers ----
  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function doLogout() {
    if (!confirm("Are you sure you want to logout?")) return;
    removeToken();
    window.location.href = AUTH_URL;
  }

  // ---- fetch user info ----
  async function fetchMe(token) {
    try {
      const res = await fetch("/auth/me", {
        headers: { Authorization: "Bearer " + token },
      });
      if (!res.ok) {
        if (res.status === 401 || res.status === 422) removeToken();
        return null;
      }
      return await res.json();
    } catch {
      return null;
    }
  }

  // ---- build profile avatar button ----
  function createAvatarBtn(username) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "nav-avatar-btn";
    btn.setAttribute("aria-label", "Open profile");
    btn.setAttribute("aria-expanded", "false");
    btn.id = "navAvatarBtn";

    const initial = (username || "U").charAt(0).toUpperCase();
    btn.innerHTML = `
      <span class="nav-avatar-circle">${initial}</span>
      <span class="nav-avatar-name">${username || "User"}</span>
      <svg class="nav-avatar-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    return btn;
  }

  // ---- build profile popup ----
  function createProfilePopup(user) {
    const popup = document.createElement("div");
    popup.className = "profile-popup";
    popup.id = "profilePopup";
    popup.hidden = true;

    const initial = (user.username || "U").charAt(0).toUpperCase();
    const planLabel =
      user.plan === "premium" ? "Premium Plan" : "Free Plan";
    const planClass =
      user.plan === "premium" ? "profile-popup__plan--premium" : "";

    popup.innerHTML = `
      <div class="profile-popup__header">
        <div class="profile-popup__avatar">${initial}</div>
        <div class="profile-popup__info">
          <div class="profile-popup__name">${user.username}</div>
          <div class="profile-popup__email">${user.email}</div>
        </div>
      </div>

      <div class="profile-popup__divider"></div>

      <div class="profile-popup__plan ${planClass}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M3 7l4.5 4L12 5l4.5 6L21 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"
                fill="currentColor" opacity=".25"/>
          <path d="M3 7l4.5 4L12 5l4.5 6L21 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"
                stroke="currentColor" stroke-width="1.5" fill="none"/>
        </svg>
        <span>${planLabel}</span>
      </div>

      ${user.plan !== "premium" ? `
      <a class="profile-popup__upgrade" href="${PRICING_URL}">
        ⚡ Upgrade to Premium
      </a>
      ` : ""}

      <div class="profile-popup__divider"></div>

      <button class="profile-popup__item" data-action="history" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
          <path d="M12 7v5l3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>History</span>
      </button>

      <button class="profile-popup__item" data-action="pricing" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="4" width="20" height="16" rx="3" stroke="currentColor" stroke-width="2"/>
          <path d="M2 10h20" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span>Pricing</span>
      </button>

      <button class="profile-popup__item" data-action="reset-password" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <rect x="5" y="11" width="14" height="10" rx="3" stroke="currentColor" stroke-width="2"/>
          <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="12" cy="16" r="1.5" fill="currentColor"/>
        </svg>
        <span>Reset Password</span>
      </button>

      <div class="profile-popup__divider"></div>

      <button class="profile-popup__item profile-popup__item--danger" data-action="logout" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M10 17l-1 0a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4h1" stroke="currentColor" stroke-width="2"/>
          <path d="M16 7l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>Log out</span>
      </button>
    `;

    // actions
    popup.addEventListener("click", (e) => {
      const item = e.target.closest("[data-action]");
      if (!item) return;
      const action = item.dataset.action;
      if (action === "history") window.location.href = "/history-page";
      if (action === "pricing") window.location.href = PRICING_URL;
      if (action === "reset-password") showResetPasswordModal(user.email);
      if (action === "logout") doLogout();
    });

    return popup;
  }

  // ---- Reset Password Modal ----
  function showResetPasswordModal(email) {
    // Remove existing modal if any
    document.querySelector(".reset-pw-overlay")?.remove();

    const overlay = document.createElement("div");
    overlay.className = "reset-pw-overlay";
    Object.assign(overlay.style, {
      position: "fixed", inset: "0", zIndex: "9999",
      background: "rgba(0,0,0,.55)", backdropFilter: "blur(6px)",
      display: "flex", alignItems: "center", justifyContent: "center"
    });

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const modalBg = isDark
      ? "linear-gradient(150deg, #111827, #0f172a)"
      : "#fff";
    const modalBorder = isDark
      ? "1px solid rgba(255,255,255,.1)"
      : "1px solid rgba(0,0,0,.08)";
    const textColor = isDark ? "#eaf2ff" : "#1e293b";

    overlay.innerHTML = `
      <div style="width:min(420px,90%);border-radius:20px;padding:32px 28px;text-align:center;
                  background:${modalBg};border:${modalBorder};color:${textColor};
                  box-shadow:0 20px 60px rgba(0,0,0,.3)">
        <div style="width:64px;height:64px;margin:0 auto 16px;border-radius:50%;display:grid;place-items:center;
                    background:linear-gradient(135deg,#0ea5c7,#7c3aed)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <rect x="5" y="11" width="14" height="10" rx="3" stroke="#fff" stroke-width="2"/>
            <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 style="font-size:20px;font-weight:700;margin:0 0 8px">Reset Password</h3>
        <p style="font-size:14px;line-height:1.6;margin:0 0 20px;opacity:.75">
          We'll send a password reset token to your email:<br>
          <strong>${email}</strong>
        </p>
        <div id="resetPwMsg" style="display:none;margin-bottom:12px;padding:10px;border-radius:10px;font-size:13px"></div>
        <button id="resetPwSendBtn" type="button"
          style="display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 28px;
                 border-radius:999px;font-size:14px;font-weight:700;border:none;cursor:pointer;
                 background:linear-gradient(135deg,#0ea5c7,#7c3aed);color:#fff;
                 box-shadow:0 8px 24px rgba(14,165,199,.25)">
          Send Reset Token
        </button>
        <br>
        <button id="resetPwCancelBtn" type="button"
          style="display:inline-block;margin-top:8px;padding:10px 24px;border-radius:999px;
                 font-size:14px;font-weight:500;border:none;cursor:pointer;
                 background:transparent;color:${textColor};opacity:.6">
          Cancel
        </button>
      </div>
    `;
    document.body.appendChild(overlay);

    // Cancel
    document.getElementById("resetPwCancelBtn").addEventListener("click", () => overlay.remove());
    overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });

    // Send
    document.getElementById("resetPwSendBtn").addEventListener("click", async () => {
      const btn = document.getElementById("resetPwSendBtn");
      const msg = document.getElementById("resetPwMsg");
      btn.disabled = true;
      btn.textContent = "Sending...";

      try {
        const res = await fetch("/auth/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await res.json();

        msg.style.display = "block";
        if (res.ok) {
          msg.style.background = "rgba(34,197,94,.12)";
          msg.style.color = "#16a34a";
          msg.textContent = "Link reset password telah dikirim ke email Anda!";
          btn.textContent = "← Back to Menu";
          btn.disabled = false;
          btn.style.background = "transparent";
          btn.style.color = "#0ea5c7";
          btn.style.boxShadow = "none";
          btn.style.border = "1px solid #0ea5c7";
          btn.replaceWith(btn.cloneNode(true));
          document.getElementById("resetPwSendBtn").addEventListener("click", () => overlay.remove());
        } else {
          msg.style.background = "rgba(239,68,68,.12)";
          msg.style.color = "#ef4444";
          msg.textContent = data.error || "Failed to send reset token.";
          btn.disabled = false;
          btn.textContent = "Send Reset Token";
        }
      } catch {
        msg.style.display = "block";
        msg.style.background = "rgba(239,68,68,.12)";
        msg.style.color = "#ef4444";
        msg.textContent = "Network error. Please try again.";
        btn.disabled = false;
        btn.textContent = "Send Reset Token";
      }
    });
  }

  // ---- init ----
  async function init() {
    const token = getToken();
    if (!token) return; // not logged in, keep "Get Started"

    const user = await fetchMe(token);
    if (!user) return; // token invalid

    // Cache daily limit for login-guard.js
    if (user.daily_limit) {
      window._detectifyDailyLimit = user.daily_limit;
    }

    // --- Desktop: replace "Get Started" button ---
    const getStartedBtn = document.querySelector(
      '.nav__right > a.btn.btn--primary'
    );
    if (getStartedBtn) {
      const wrapper = document.createElement("div");
      wrapper.className = "nav-profile-wrapper";

      const avatarBtn = createAvatarBtn(user.username);
      const popup = createProfilePopup(user);

      wrapper.appendChild(avatarBtn);
      wrapper.appendChild(popup);
      getStartedBtn.replaceWith(wrapper);

      // toggle popup
      avatarBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = !popup.hidden;
        popup.hidden = isOpen;
        avatarBtn.setAttribute("aria-expanded", isOpen ? "false" : "true");
      });

      // close on click outside
      document.addEventListener("click", (e) => {
        if (!wrapper.contains(e.target)) {
          popup.hidden = true;
          avatarBtn.setAttribute("aria-expanded", "false");
        }
      });
    }

    // --- Mobile: replace "Get Started" link ---
    const mobileCta = document.querySelector(
      '.mobile-menu a.btn.btn--primary.btn--block'
    );
    if (mobileCta) {
      const mobileWrapper = document.createElement("div");
      mobileWrapper.className = "mobile-profile-section";
      mobileWrapper.innerHTML = `
        <div class="mobile-profile-header">
          <span class="mobile-profile-avatar">${(user.username || "U").charAt(0).toUpperCase()}</span>
          <div class="mobile-profile-info">
            <div class="mobile-profile-name">${user.username}</div>
            <div class="mobile-profile-email">${user.email}</div>
          </div>
        </div>
        <a class="mobile-link" href="/history-page">📜 History</a>
        <a class="mobile-link" href="${PRICING_URL}">💳 Pricing</a>
        <button class="btn btn--primary btn--block" type="button" id="mobileLogoutBtn">Log out</button>
      `;
      mobileCta.replaceWith(mobileWrapper);

      document
        .getElementById("mobileLogoutBtn")
        ?.addEventListener("click", () => doLogout());
    }

    // --- Home Page: hide "Try it for Free" pill ---
    const heroPill = document.querySelector('.hero__pill');
    if (heroPill) {
      heroPill.remove();
    }
  }

  // run after DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
