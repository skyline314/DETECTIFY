// auth.js (ESM module)
// Firebase Auth for static hosting (client-side)

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
 * Fill this from Firebase Console → Project settings → Web app.
 * Firebase config keys are not "secrets" (they identify your project).
 */
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  appId: "YOUR_APP_ID",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// -------------------------
// Safe redirect target
// -------------------------
const params = new URLSearchParams(location.search);
const nextParam = params.get("next");

/**
 * Prevent open-redirect:
 * - allow only same-origin relative paths (no protocol / //)
 * - fallback to get-started.html
 */
function safeNextPath(path) {
  if (!path) return "get-started.html";
  if (/^(https?:)?\/\//i.test(path)) return "get-started.html";
  if (path.includes("\\") || path.includes("\0")) return "get-started.html";
  // allow relative or absolute path in same site (e.g., /dashboard.html)
  return path;
}

const redirectTo = safeNextPath(nextParam);

// -------------------------
// UI helpers
// -------------------------
const $ = (q) => document.querySelector(q);
const statusEl = $("#authStatus");

function setStatus(msg = "", type = "info") {
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.dataset.type = type; // used by CSS
}

function requireValue(el, label) {
  const v = (el?.value || "").trim();
  if (!v) throw new Error(`${label} wajib diisi.`);
  return v;
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

// Persistence: "Remember me" → local, else session
async function applyPersistence(remember) {
  await setPersistence(auth, remember ? browserLocalPersistence : browserSessionPersistence);
}

function isLikelyIOS() {
  const ua = navigator.userAgent || "";
  return /iPhone|iPad|iPod/i.test(ua);
}

async function providerSignIn(provider) {
  setStatus("Memproses login…");
  // iOS Safari is often more reliable with redirect
  if (isLikelyIOS()) {
    await signInWithRedirect(auth, provider);
    return;
  }
  await signInWithPopup(auth, provider);
}

function afterAuthSuccess() {
  setStatus("Login berhasil. Mengarahkan…", "ok");
  location.href = redirectTo;
}

// Handle redirect result (for iOS / fallback)
getRedirectResult(auth).catch(() => {
  // silent; normal when there's no redirect in progress
});

// -------------------------
// LOGIN
// -------------------------
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
      afterAuthSuccess();
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  document.getElementById("forgotPassword")?.addEventListener("click", async () => {
    setStatus("");
    try {
      const email = requireValue($("#loginEmail"), "Email");
      await sendPasswordResetEmail(auth, email);
      setStatus("Link reset password sudah dikirim ke email kamu.", "ok");
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  // Social login buttons
  $("#btnGoogle")?.addEventListener("click", async () => {
    try {
      await providerSignIn(new GoogleAuthProvider());
      afterAuthSuccess();
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  $("#btnFacebook")?.addEventListener("click", async () => {
    try {
      await providerSignIn(new FacebookAuthProvider());
      afterAuthSuccess();
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });

  $("#btnApple")?.addEventListener("click", async () => {
    try {
      const provider = new OAuthProvider("apple.com");
      provider.addScope("email");
      provider.addScope("name");
      await providerSignIn(provider);
      afterAuthSuccess();
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });
}

// -------------------------
// SIGNUP
// -------------------------
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

      await applyPersistence(true); // signup usually wants persistence
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(cred.user, { displayName: name });

      setStatus("Akun berhasil dibuat. Mengarahkan…", "ok");
      location.href = redirectTo;
    } catch (err) {
      setStatus(readableAuthError(err), "err");
    }
  });
}

// Optional: auto-redirect if already logged in (disabled by default)
onAuthStateChanged(auth, (user) => {
  if (user && (location.pathname.endsWith("login.html") || location.pathname.endsWith("signup.html"))) {
    // location.href = redirectTo;
  }
});

// -------------------------
// Firebase Auth errors → human text
// -------------------------
function readableAuthError(err) {
  const msg = (err && err.message) ? err.message : "Terjadi kesalahan.";
  const code = (err && err.code) ? err.code : "";

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
