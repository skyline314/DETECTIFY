/* theme.js
   - Single source of truth untuk theme
   - Render icon sun/moon ke #themeIcon
   - Toggle data-theme di <html>
   - Simpan pilihan ke localStorage
   - Mobile menu handler
*/
(() => {
  "use strict";

  const THEME_KEY = "detectify_theme";
  const root = document.documentElement;

  // Elemen Toggle
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  // Ikon SVG (Fixed)
  const ICONS = {
    // Bulan (untuk mode Gelap)
    dark: `
      <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>`,
    // Matahari (untuk mode Terang)
    light: `
      <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>`
  };

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    updateIcon(theme);
  }

  function updateIcon(theme) {
    if (!themeIcon) return;
    // Jika tema 'dark', tampilkan ikon 'light' (Matahari) agar user bisa switch ke terang
    // Jika tema 'light', tampilkan ikon 'dark' (Bulan)
    themeIcon.innerHTML = theme === "dark" ? ICONS.dark : ICONS.light;
  }

  function toggleTheme() {
    const current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    const next = current === "dark" ? "light" : "dark";
    setTheme(next);
  }

  // Init
  const initialTheme = root.getAttribute("data-theme") || "light";
  updateIcon(initialTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }

  // -------------------------
  // Mobile menu Handler
  // -------------------------
  const menuToggle = document.getElementById("menuToggle");
  const mobileMenu = document.getElementById("mobileMenu");

  function toggleMenu() {
    if (!menuToggle || !mobileMenu) return;

    const isExpanded = menuToggle.getAttribute("aria-expanded") === "true";

    if (isExpanded) {
      // Tutup Menu
      mobileMenu.hidden = true;
      mobileMenu.classList.remove("is-open");
      menuToggle.setAttribute("aria-expanded", "false");
    } else {
      // Buka Menu
      mobileMenu.hidden = false;
      mobileMenu.classList.add("is-open");
      menuToggle.setAttribute("aria-expanded", "true");
    }
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", toggleMenu);

    // Tutup menu saat klik di luar
    document.addEventListener("click", (e) => {
      const isExpanded = menuToggle.getAttribute("aria-expanded") === "true";
      if (!isExpanded) return;
      if (!mobileMenu.contains(e.target) && !menuToggle.contains(e.target)) {
        toggleMenu(); // Tutup
      }
    });
  }
})();