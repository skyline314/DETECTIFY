/* theme.js
   Handles theme toggle + mobile menu behavior.

   Notes:
   - Initial theme is set in theme-init.js (runs before CSS paints).
   - This file only *toggles* theme and persists user choice.
*/
(() => {
  "use strict";

  const THEME_KEY = "detectify_theme";
  const root = document.documentElement;

  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  const ICONS = {
    dark: `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M21 14.8A8.5 8.5 0 0 1 9.2 3a7 7 0 1 0 9.8 11.8Z"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      </svg>`,
    light: `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z"
          fill="none" stroke="currentColor" stroke-width="2"/>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41
                 M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>`
  };

  const safeStorage = {
    get(key) {
      try { return localStorage.getItem(key); } catch { return null; }
    },
    set(key, val) {
      try { localStorage.setItem(key, val); } catch { /* ignore */ }
    },
    has(key) {
      try { return localStorage.getItem(key) != null; } catch { return false; }
    }
  };

  function renderThemeIcon(theme) {
    if (!themeIcon || !themeToggle) return;

    const isDark = theme === "dark";
    themeIcon.innerHTML = isDark ? ICONS.dark : ICONS.light;

    themeToggle.setAttribute("aria-pressed", isDark ? "true" : "false");
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  }

  function setTheme(theme, { persist = true } = {}) {
    root.setAttribute("data-theme", theme);
    if (persist) safeStorage.set(THEME_KEY, theme);
    renderThemeIcon(theme);
  }

  // Sync icon to current theme on load
  const currentTheme = root.getAttribute("data-theme") || "light";
  renderThemeIcon(currentTheme);

  // If user never explicitly set a theme, keep following OS changes.
  const mql = window.matchMedia?.("(prefers-color-scheme: dark)");
  if (mql && !safeStorage.has(THEME_KEY)) {
    mql.addEventListener?.("change", (e) => {
      setTheme(e.matches ? "dark" : "light", { persist: false });
    });
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const now = root.getAttribute("data-theme") || "light";
      setTheme(now === "dark" ? "light" : "dark", { persist: true });
    });
  }

  // -------------------------
  // Mobile menu
  // -------------------------
  const menuToggle = document.getElementById("menuToggle");
  const mobileMenu = document.getElementById("mobileMenu");
  let hideTimer = 0;

  function openMenu() {
    if (!menuToggle || !mobileMenu) return;
    clearTimeout(hideTimer);
    mobileMenu.hidden = false;
    mobileMenu.classList.add("is-open");
    menuToggle.setAttribute("aria-expanded", "true");
    menuToggle.setAttribute("aria-label", "Close menu");
  }

  function closeMenu() {
    if (!menuToggle || !mobileMenu) return;
    mobileMenu.classList.remove("is-open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open menu");

    clearTimeout(hideTimer);
    hideTimer = window.setTimeout(() => {
      mobileMenu.hidden = true;
    }, 160);
  }

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      const expanded = menuToggle.getAttribute("aria-expanded") === "true";
      expanded ? closeMenu() : openMenu();
    });

    document.addEventListener("click", (e) => {
      const expanded = menuToggle.getAttribute("aria-expanded") === "true";
      if (!expanded) return;

      const t = e.target;
      const inside = mobileMenu.contains(t) || menuToggle.contains(t);
      if (!inside) closeMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
        closeMenu();
        menuToggle.focus();
      }
    });
  }
})();
