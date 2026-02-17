/**
 * auth.js - FINAL FIXED VERSION
 * Menggabungkan backend Flask dengan animasi CSS asli (.is-signup)
 */

document.addEventListener("DOMContentLoaded", () => {

  // --- 0. HANDLE VERIFICATION REDIRECT ---
  const urlParams = new URLSearchParams(window.location.search);
  const verified = urlParams.get("verified");
  const verifyMsg = urlParams.get("msg");
  if (verified && verifyMsg) {
    const banner = document.createElement("div");
    const isSuccess = verified === "success" || verified === "already";
    banner.style.cssText = `
      position:fixed;top:0;left:0;right:0;z-index:10000;
      padding:14px 20px;text-align:center;font-size:14px;font-weight:600;
      font-family:Inter,sans-serif;animation:bannerSlide .3s ease;
      background:${isSuccess ? "linear-gradient(135deg,#10b981,#059669)" : "linear-gradient(135deg,#ef4444,#dc2626)"};
      color:#fff;
    `;
    banner.textContent = decodeURIComponent(verifyMsg.replace(/\+/g, " "));
    document.body.prepend(banner);
    // Auto-dismiss after 6s
    setTimeout(() => { banner.style.opacity = "0"; banner.style.transition = "opacity .3s"; }, 5500);
    setTimeout(() => banner.remove(), 6000);
    // Clean URL
    window.history.replaceState(null, null, window.location.pathname);
  }

  // --- 1. KONFIGURASI API ---
  const URLS = {
    apiLogin: "/auth/login",
    apiRegister: "/auth/register"
  };

  // --- 2. LOGIKA SLIDER (MENGGUNAKAN CLASS ASLI: .is-signup) ---
  const container = document.getElementById('authSlider'); // Pastikan ID ini ada di HTML
  const toggleBtns = document.querySelectorAll('[data-auth-toggle]');

  // Fungsi helper untuk ubah mode
  function setMode(mode) {
    if (!container) return;

    // KUNCI PERBAIKAN: Gunakan class 'is-signup' sesuai CSS asli Anda
    if (mode === 'signup') {
      container.classList.add('is-signup');
      window.history.replaceState(null, null, "?mode=signup");
    } else {
      container.classList.remove('is-signup');
      window.history.replaceState(null, null, "?mode=login");
    }
  }

  // A. Deteksi URL/Query Param saat Load
  // Jika URL ada '?mode=signup' atau path '/signup-page', otomatis geser
  const params = new URLSearchParams(window.location.search);
  if (params.get('mode') === 'signup' || window.location.pathname.includes('/signup-page')) {
    setMode('signup');
  } else {
    setMode('login');
  }

  // B. Event Listener untuk Klik Tombol
  toggleBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault(); // Mencegah reload
      const target = btn.getAttribute('data-auth-toggle');
      setMode(target); // target stringnya: 'login' atau 'signup'
    });
  });


  // --- 3. DOM ELEMENTS FORM ---
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const loginStatus = document.getElementById("loginStatus");
  const signupStatus = document.getElementById("signupStatus");

  function setStatus(msg, type, context = "login") {
    const el = context === "signup" ? signupStatus : loginStatus;
    const other = context === "signup" ? loginStatus : signupStatus;

    if (el) {
      el.textContent = msg;
      el.className = `auth__status ${type}`;
      el.style.display = msg ? "block" : "none";
    }
    if (other) {
      other.style.display = "none";
      other.textContent = "";
    }
  }

  // --- 4. HANDLER LOGIN ---
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector("button[type='submit']");
      const originalText = btn.textContent;
      btn.disabled = true; btn.textContent = "Processing...";
      setStatus("", "", "login");

      try {
        const res = await fetch(URLS.apiLogin, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: document.getElementById("loginEmail").value,
            password: document.getElementById("loginPassword").value
          })
        });
        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("detectify_token", data.access_token);
          setStatus("Login Successful! Redirecting...", "success", "login");
          setTimeout(() => window.location.href = "/", 1000);
        } else if (res.status === 403) {
          // Unverified account
          setStatus("Account not verified. Please check your email and click the verification link.", "error", "login");
        } else {
          setStatus(data.error || data.message || "Login Failed", "error", "login");
        }
      } catch (err) {
        setStatus("Failed to connect to server.", "error", "login");
      } finally {
        btn.disabled = false; btn.textContent = originalText;
      }
    });
  }

  // --- 5. HANDLER REGISTER ---
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = signupForm.querySelector("button[type='submit']");
      const originalText = btn.textContent;
      btn.disabled = true; btn.textContent = "Processing...";
      setStatus("", "", "signup");

      try {
        const res = await fetch(URLS.apiRegister, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: document.getElementById("signupName").value,
            email: document.getElementById("signupEmail").value,
            password: document.getElementById("signupPassword").value
          })
        });
        const data = await res.json();

        if (res.ok) {
          // Show Modal "Like Reset Password"
          const emailVal = document.getElementById("signupEmail").value;
          showVerificationModal(emailVal);

          // Switch to login background
          setMode('login');
        } else {
          setStatus(data.error || data.message || "Registration Failed", "error", "signup");
        }
      } catch (err) {
        setStatus("Failed to connect to server.", "error", "signup");
      } finally {
        btn.disabled = false; btn.textContent = originalText;
      }
    });
  }

  // --- 6. TOGGLE PASSWORD ---
  document.querySelectorAll(".field__icon").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      if (input) input.type = input.type === "password" ? "text" : "password";
    });
  });

  // --- 7. FORGOT PASSWORD ---
  const forgotLink = document.getElementById("forgotPasswordLink");
  const backToLogin = document.getElementById("backToLoginLink");
  const forgotPanel = document.getElementById("forgotPasswordPanel");
  const forgotForm = document.getElementById("forgotPasswordForm");

  if (forgotLink && forgotPanel && loginForm) {
    forgotLink.addEventListener("click", (e) => {
      e.preventDefault();
      loginForm.style.display = "none";
      // Also hide the login title/desc
      const card = loginForm.closest(".auth__panel--login");
      const h1 = card?.querySelector("h1.auth__title");
      const p = card?.querySelector("p.auth__desc");
      if (h1) h1.style.display = "none";
      if (p) p.style.display = "none";
      forgotPanel.style.display = "block";
    });
  }

  if (backToLogin && forgotPanel && loginForm) {
    backToLogin.addEventListener("click", (e) => {
      e.preventDefault();
      forgotPanel.style.display = "none";
      loginForm.style.display = "block";
      const card = loginForm.closest(".auth__panel--login");
      const h1 = card?.querySelector("h1.auth__title");
      const p = card?.querySelector("p.auth__desc");
      if (h1) h1.style.display = "";
      if (p) p.style.display = "";
    });
  }

  if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("forgotEmail").value;
      const btn = forgotForm.querySelector("button[type='submit']");
      const msg = document.getElementById("forgotMsg");
      const originalText = btn.textContent;
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
          msg.textContent = data.message || "Check your email for a reset token!";
          btn.textContent = "Sent!";
        } else {
          msg.style.background = "rgba(239,68,68,.12)";
          msg.style.color = "#ef4444";
          msg.textContent = data.error || "Failed to send.";
          btn.disabled = false;
          btn.textContent = originalText;
        }
      } catch {
        msg.style.display = "block";
        msg.style.background = "rgba(239,68,68,.12)";
        msg.style.color = "#ef4444";
        msg.textContent = "Network error. Please try again.";
        btn.disabled = false;
        btn.textContent = originalText;
      }
    });
  }

  // --- 8. VERIFICATION MODAL (REQUIRED FOR REGISTRATION) ---
  // DO NOT DELETE THIS FUNCTION - IT IS USED BY SIGNUP HANDLER
  function showVerificationModal(email) {
    // Inject Styles if needed
    if (!document.getElementById("authModalStyle")) {
      const css = `
        .auth-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 9999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); animation: fadeIn 0.3s; }
        .auth-modal { background: #1e1e2d; padding: 2.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); text-align: center; max-width: 420px; width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); animation: slideUp 0.3s; position: relative; }
        .auth-modal__icon { font-size: 4rem; margin-bottom: 1.5rem; background: rgba(255,255,255,0.05); width: 80px; height: 80px; line-height: 80px; border-radius: 50%; margin: 0 auto 1.5rem auto; }
        .auth-modal__title { font-size: 1.5rem; color: #fff; margin-bottom: 0.75rem; font-weight: 700; }
        .auth-modal__text { color: #ccc; margin-bottom: 1rem; line-height: 1.6; font-size: 0.95rem; }
        .auth-modal__subtext { font-size: 0.85rem; color: #888; margin-bottom: 2rem; }
        .auth-modal__btn { background: #6366f1; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; width: 100%; }
        .auth-modal__btn:hover { background: #4f46e5; transform: translateY(-1px); }
        @keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
        @keyframes slideUp { from { transform:translateY(20px); opacity:0; } to { transform:translateY(0); opacity:1; } }
        `;
      const style = document.createElement("style");
      style.id = "authModalStyle";
      style.textContent = css;
      document.head.appendChild(style);
    }

    const overlay = document.createElement("div");
    overlay.className = "auth-overlay";
    overlay.innerHTML = `
      <div class="auth-modal">
        <div class="auth-modal__icon">✉️</div>
        <h3 class="auth-modal__title">Verify Your Email</h3>
        <p class="auth-modal__text">
          We've sent a verification link to <br><strong style="color:#6366f1">${email}</strong>
        </p>
        <p class="auth-modal__subtext">
          Please check your inbox (and spam folder) to activate your account.
        </p>
        <button class="auth-modal__btn" id="closeModalBtn">OK, I Check it</button>
      </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById("closeModalBtn").onclick = () => {
      overlay.remove();
      setMode('login');
    };
  }
});