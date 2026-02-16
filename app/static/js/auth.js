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
  const authStatus = document.getElementById("authStatus");

  function setStatus(msg, type) {
    if (!authStatus) return;
    authStatus.textContent = msg;
    authStatus.className = `auth__status ${type}`;
    authStatus.style.display = "block";
  }

  // --- 4. HANDLER LOGIN ---
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector("button[type='submit']");
      const originalText = btn.textContent;
      btn.disabled = true; btn.textContent = "Processing...";
      setStatus("", "");

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
          setStatus("Login Berhasil! Mengalihkan...", "success");
          setTimeout(() => window.location.href = "/", 1000);
        } else if (res.status === 403) {
          // Unverified account
          setStatus("Akun belum diverifikasi. Silakan cek email Anda dan klik link verifikasi.", "error");
        } else {
          setStatus(data.error || "Login Gagal", "error");
        }
      } catch (err) {
        setStatus("Gagal terhubung ke server.", "error");
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
      setStatus("", "");

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
          setStatus("✅ Registrasi berhasil! Silakan cek email Anda untuk verifikasi akun.", "success");
          setTimeout(() => {
            setMode('login');
            setStatus("Cek email Anda untuk link verifikasi, lalu login di sini.", "success");
          }, 4000);
        } else {
          setStatus(data.error || "Registrasi Gagal", "error");
        }
      } catch (err) {
        setStatus("Gagal terhubung ke server.", "error");
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
});