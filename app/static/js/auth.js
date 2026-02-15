/**
 * auth.js - FINAL FIXED VERSION
 * Menggabungkan backend Flask dengan animasi CSS asli (.is-signup)
 */

document.addEventListener("DOMContentLoaded", () => {
  
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
        } else {
          setStatus(data.message || data.error || "Login Gagal", "error");
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
          setStatus("Akun dibuat! Cek email verifikasi.", "success");
          setTimeout(() => {
            setMode('login'); // Geser otomatis ke Login pakai fungsi helper tadi
            setStatus("", "");
          }, 2000);
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
});