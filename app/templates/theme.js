(function () {
  const THEME_KEY = "detectify_theme";
  const root = document.documentElement;

  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  function renderThemeIcon(theme) {
    if (!themeIcon || !themeToggle) return;

    if (theme === "dark") {
      themeIcon.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 14.8A8.5 8.5 0 019.2 3a7 7 0 109.8 11.8Z"
            fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`;
      themeToggle.setAttribute("aria-pressed", "true");
      themeToggle.setAttribute("aria-label", "Switch to light mode");
    } else {
      themeIcon.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 18a6 6 0 100-12 6 6 0 000 12Z"
            fill="none" stroke="currentColor" stroke-width="2"/>
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41
                   M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      themeToggle.setAttribute("aria-pressed", "false");
      themeToggle.setAttribute("aria-label", "Switch to dark mode");
    }
  }

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    renderThemeIcon(theme);
  }

  renderThemeIcon(root.getAttribute("data-theme") || "light");

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = root.getAttribute("data-theme") || "light";
      setTheme(current === "dark" ? "light" : "dark");
    });
  }

  // Mobile menu
  const menuToggle = document.getElementById("menuToggle");
  const mobileMenu = document.getElementById("mobileMenu");

  function openMenu() {
    mobileMenu.hidden = false;
    mobileMenu.classList.add("is-open");
    menuToggle.setAttribute("aria-expanded", "true");
    menuToggle.setAttribute("aria-label", "Close menu");
  }

  function closeMenu() {
    mobileMenu.classList.remove("is-open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open menu");
    setTimeout(() => { mobileMenu.hidden = true; }, 160);
  }

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      const expanded = menuToggle.getAttribute("aria-expanded") === "true";
      expanded ? closeMenu() : openMenu();
    });

    document.addEventListener("click", (e) => {
      const expanded = menuToggle.getAttribute("aria-expanded") === "true";
      const inside = mobileMenu.contains(e.target) || menuToggle.contains(e.target);
      if (expanded && !inside) closeMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") closeMenu();
    });
  }
})();
