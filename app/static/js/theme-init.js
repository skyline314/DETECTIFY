/* theme-init.js
   Sets the initial theme ASAP (pre-CSS paint) to avoid flash.
   - Uses saved preference if available
   - Falls back to prefers-color-scheme
*/
(() => {
  const KEY = "detectify_theme";
  const root = document.documentElement;

  try {
    const saved = localStorage.getItem(KEY);
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
    const theme =
      saved === "light" || saved === "dark"
        ? saved
        : (prefersDark ? "dark" : "light");

    root.setAttribute("data-theme", theme);
  } catch {
    // If storage is blocked, just rely on CSS defaults.
  }
})();
