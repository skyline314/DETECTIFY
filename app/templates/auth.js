// auth.js (ESM module)

// Firebase CDN (ringan & cepat untuk static hosting)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import {
  getAuth,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  FacebookAuthProvider,
  OAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

/**
 * 1) Isi config ini dari Firebase Console → Project settings → Web app
 * Keys Firebase ini bukan “secret”, aman ditaruh di frontend (aturan Firebase memang begitu).
 */
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  appId: "YOUR_APP_ID",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Redirect target setelah login
const redirectTo = new URLSearchParams(location.search).get("next") || "get-started.html";

// Helpers UI
const $ = (q) => document.querySelector(q);
const statusEl = $("#authStatus");

function setStatus(msg = "", type = "info") {
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.dataset.type = type; // dipakai CSS untuk warna
}

function togglePw(inputId, btnId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(btnId);
  if (!input || !btn) return;

  btn.addEventListener("click", () => {
    const isPw = input.type === "password";
    input.type = isPw ? "text" : "password";
    btn.setAttribute("aria-label", isPw ? "Hide password" : "Show password");
  });
}

togglePw("loginPassword", "toggleLoginPw");
togglePw("signupPassword", "toggleSignupPw");

// Persistence: "Remember me" → local, kalau tidak → session
async function applyPersistence(remember) {
  await setPersistence(auth, remember ? browserLocalPersistence : browserSessionPersistence);
}

// Basic validation ringan
function requireValue(el, label) {
  const v = (el?.value || "").trim();
  if (!v) throw new Error(`${label} wajib diisi.`);
  return v;
}

function isLikelyIOS() {
  const ua = navigator.userAgent || "";
  return /iPhone|iPad|iPod/i.test(ua);
}

async function providerSignIn(provider) {
  setStatus("Memproses login…");
  // iOS Safari sering lebih aman pakai redirect
  if (isLikelyIOS()) {
    await signInWithRedirect(auth, provider);
    return;
  }
  await signInWithPopup(auth, provider);
}

// Handle redirect result (untuk iOS / fallback)
getRedirectResult(auth).catch(() => {
  // silent; kalau user belum login redirect, ini normal
});

// ========== LOGIN FORM ==========
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    setStatus("");

    try {
      const email = requireValue($("#loginEmail"), "Email");
      const password = requireValue($("#loginPassword"), "Password");
      const remember = !!$("#rememberMe")?.checked;

      await applyPersistence(remember);
      await signInWithEmailAndPassword(auth, email, password);

      setStatus("Login berhasil. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  const forgotBtn = document.getElementById("forgotPassword");
  if (forgotBtn) {
    forgotBtn.addEventListener("click", async () => {
      setStatus("");
      try {
        const email = requireValue($("#loginEmail"), "Email");
        await sendPasswordResetEmail(auth, email);
        setStatus("Link reset password sudah dikirim ke email kamu.", "ok");
      } catch (err) {
        setStatus(readableAuthError(err), "err");
      }
    });
  }

  // Social login buttons
  $("#btnGoogle")?.addEventListener("click", async () => {
    try {
      const provider = new GoogleAuthProvider();
      await providerSignIn(provider);
      setStatus("Login berhasil. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  $("#btnFacebook")?.addEventListener("click", async () => {
    try {
      const provider = new FacebookAuthProvider();
      await providerSignIn(provider);
      setStatus("Login berhasil. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  $("#btnApple")?.addEventListener("click", async () => {
    try {
      // Firebase Apple provider
      const provider = new OAuthProvider("apple.com");
      provider.addScope("email");
      provider.addScope("name");
      await providerSignIn(provider);
      setStatus("Login berhasil. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });
}

// ========== SIGNUP FORM ==========
const signupForm = document.getElementById("signupForm");
if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    setStatus("");

    try {
      const name = requireValue($("#signupName"), "Nama");
      const email = requireValue($("#signupEmail"), "Email");
      const password = requireValue($("#signupPassword"), "Password");

      if (password.length < 6) throw new Error("Password minimal 6 karakter.");

      await applyPersistence(true); // biasanya daftar → persistent
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(cred.user, { displayName: name });

      setStatus("Akun berhasil dibuat. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });
}

// Optional: kalau kamu mau auto-redirect user yang sudah login
onAuthStateChanged(auth, (user) => {
  // contoh: jika user sudah login dan sedang di login.html / signup.html, boleh langsung redirect
  // (biar user gak lihat halaman auth lagi)
  if (user && (location.pathname.endsWith("login.html") || location.pathname.endsWith("signup.html"))) {
    // jangan override kalau user memang ingin tetap di sini (misal debug), bisa kamu matikan baris ini
    // location.href = redirectTo;
  }
});

function readableAuthError(err) {
  const msg = (err && err.message) ? err.message : "Terjadi kesalahan.";
  const code = (err && err.code) ? err.code : "";

  // Mapping error umum Firebase Auth
  const map = {
    "auth/invalid-email": "Format email tidak valid.",
    "auth/user-not-found": "Akun tidak ditemukan.",
    "auth/wrong-password": "Password salah.",
    "auth/invalid-credential": "Email / password salah atau kredensial tidak valid.",
    "auth/email-already-in-use": "Email sudah digunakan.",
    "auth/weak-password": "Password terlalu lemah (minimal 6 karakter).",
    "auth/popup-closed-by-user": "Popup login ditutup sebelum selesai.",
    "auth/account-exists-with-different-credential": "Email ini sudah terdaftar dengan metode login lain.",
    "auth/operation-not-allowed": "Provider belum diaktifkan di Firebase Console.",
    "auth/unauthorized-domain": "Domain belum di-allow di Firebase Authentication settings.",
  };

  return map[code] || msg;
}
