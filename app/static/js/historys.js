// =========================
// HELPERS
// =========================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

// =========================
// THEME TOGGLE + ICON
// =========================
const html = document.documentElement;
const themeBtn = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");

// SVG icons (inline)
const ICON_SUN = `
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z" fill="none" stroke="currentColor" stroke-width="2"/>
  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>`;

const ICON_MOON = `
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M21 13.2A7.5 7.5 0 0 1 10.8 3a6.5 6.5 0 1 0 10.2 10.2Z"
        fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
</svg>`;

function setTheme(theme) {
  html.setAttribute("data-theme", theme);
  localStorage.setItem("detectify_theme", theme);

  // update aria + icon
  if (themeBtn) themeBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  if (themeIcon) themeIcon.innerHTML = theme === "dark" ? ICON_MOON : ICON_SUN;
}

// init theme
const savedTheme = localStorage.getItem("detectify_theme");
if (savedTheme === "dark" || savedTheme === "light") {
  setTheme(savedTheme);
} else {
  // default: dark (biar konsisten dengan palette kamu)
  setTheme("dark");
}

if (themeBtn) {
  themeBtn.addEventListener("click", () => {
    const current = html.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

// =========================
// MOBILE MENU TOGGLE
// =========================
const menuToggle = document.getElementById("menuToggle");
const mobileMenu = document.getElementById("mobileMenu");

if (menuToggle && mobileMenu) {
  menuToggle.addEventListener("click", () => {
    const isHidden = mobileMenu.hasAttribute("hidden");
    if (isHidden) {
      mobileMenu.removeAttribute("hidden");
      mobileMenu.classList.add("is-open");
      menuToggle.setAttribute("aria-expanded", "true");
    } else {
      mobileMenu.setAttribute("hidden", "");
      mobileMenu.classList.remove("is-open");
      menuToggle.setAttribute("aria-expanded", "false");
    }
  });
}

// =========================
// HISTORY DATA (edit sesuai kebutuhan)
// =========================
const historyData = {
  "tralala_tralelo.jpg": { human: 88, ai: 12 },
  "Function-UseCase Point - week 6": { human: 35, ai: 65 },
  "WhatsApp Image 2025-10-30 a ...": { human: 55, ai: 45 },
  "temanfinancial (1).mp4": { human: 42, ai: 58 },
  "koruptor jadi kurban.mp4": { human: 25, ai: 75 },
  "theo_analysis.txt": { human: 70, ai: 30 },
  "ganash selfie.png": { human: 92, ai: 8 },
  "trump_speech.mp3": { human: 40, ai: 60 }
};

// =========================
// UI ELEMENTS
// =========================
const files = $$(".file");
const fileTitle = document.getElementById("fileTitle");
const shieldBg = document.getElementById("shieldBg");
const shieldIcon = document.getElementById("shieldIcon");
const humanProb = document.getElementById("humanProb");
const aiProb = document.getElementById("aiProb");
const probBar = document.getElementById("probBar"); // <- bar fill

function updateCard(fileName) {
  if (fileTitle) fileTitle.textContent = fileName;

  const data = historyData[fileName];

  // kalau data belum ada, fallback
  const human = data ? clamp(Number(data.human), 0, 100) : 50;
  const ai = data ? clamp(Number(data.ai), 0, 100) : (100 - human);

  if (humanProb) humanProb.textContent = `${human}%`;
  if (aiProb) aiProb.textContent = `${ai}%`;

  // risk text
if (riskText) {

  riskText.classList.remove("low", "high");

  if (ai > 50) {
    // TEXT
    riskText.textContent = "HIGH RISK";
    riskText.classList.add("high");

    // SHIELD
    if (shieldBg) shieldBg.setAttribute("fill", "#ef4444");
    if (shieldIcon) shieldIcon.textContent = "!";
  } else {
    // TEXT
    riskText.textContent = "LOW RISK";
    riskText.classList.add("low");

    // SHIELD
    if (shieldBg) shieldBg.setAttribute("fill", "#16a34a");
    if (shieldIcon) shieldIcon.textContent = "✓";
  }
}




  // progress bar (hijau = human)
  if (probBar) {
    probBar.style.width = `${human}%`;
  }
}

// init dari item aktif pertama
const activeItem = $(".file.active") || files[0];
if (activeItem) {
  updateCard(activeItem.textContent.trim());
}

// click handler
files.forEach((file) => {
  file.addEventListener("click", () => {
    files.forEach((f) => f.classList.remove("active"));
    file.classList.add("active");

    const fileName = file.textContent.trim();
    updateCard(fileName);
  });
});


// =========================
// PROFILE POPUP (OPEN/CLOSE)
// =========================
const openProfileBtn = document.getElementById("openProfilePopup");
const profileOverlay = document.getElementById("profilePopupOverlay");
const closeProfileBtn = document.getElementById("closeProfilePopup");

function openProfilePopup(){
  if(!profileOverlay) return;
  profileOverlay.hidden = false;
  profileOverlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden"; // lock scroll

  // optional: fokus ke username
  document.getElementById("usernameInput")?.focus();
}

function closeProfilePopup(){
  if(!profileOverlay) return;
  profileOverlay.hidden = true;
  profileOverlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = ""; // restore scroll
}

openProfileBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  openProfilePopup();
});

closeProfileBtn?.addEventListener("click", closeProfilePopup);

// klik di area luar dialog -> close
profileOverlay?.addEventListener("click", (e) => {
  if(e.target === profileOverlay) closeProfilePopup();
});

// ESC -> close
document.addEventListener("keydown", (e) => {
  if(e.key === "Escape" && profileOverlay && !profileOverlay.hidden){
    closeProfilePopup();
  }
});

// =========================
// PROFILE POPUP (COPY + ACTIONS)
// (ambil dari profiled/profilel.js, tapi tanpa pindah page profile)
// =========================
function copyText(text){
  if(!text) return;
  navigator.clipboard?.writeText(text).catch(() => {});
}

const usernameInput = document.getElementById("usernameInput");
const emailInput = document.getElementById("emailInput");

document.getElementById("copyUsernameBtn")?.addEventListener("click", () => {
  copyText(usernameInput?.value?.trim());
});

document.getElementById("copyEmailBtn")?.addEventListener("click", () => {
  copyText(emailInput?.value?.trim());
});

// helper: biar item bisa Enter/Space
function bindClickAndKeyboard(el, handler){
  if(!el) return;
  el.addEventListener("click", handler);
  el.addEventListener("keydown", (e) => {
    if(e.key === "Enter" || e.key === " "){
      e.preventDefault();
      handler();
    }
  });
}

// Ini aku biarin sama persis kayak profiled.js (tetep redirect ke route kamu),
// tapi TIDAK pindah ke profiled.html. Kalau mau ubah route, kamu tinggal ganti stringnya.
function goToChangePassword(){
  window.location.href = "/change-password";
}

async function doLogout(){
  try{
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  }catch(err){
    console.error(err);
  }
}

bindClickAndKeyboard(document.getElementById("changePasswordBtn"), goToChangePassword);
bindClickAndKeyboard(document.getElementById("logoutBtn"), doLogout);

document.getElementById("upgradeBtn")?.addEventListener("click", () => {
  window.location.href = "/pricing";
});


document.getElementById("upgradePlanBtn")?.addEventListener("click", () => {
  window.location.href = "pricing.html";
});
