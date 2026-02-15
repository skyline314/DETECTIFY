// auth.js
(() => {
  const authSlider = document.getElementById("authSlider");
  if (!authSlider) return;

  function setMode(mode) {
    // mode: "login" | "signup"
    authSlider.classList.toggle("is-signup", mode === "signup");
  }

  // default
  setMode("login");

  // Handle toggle buttons/links with data-auth-toggle="login|signup"
  document.querySelectorAll("[data-auth-toggle]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const target = el.getAttribute("data-auth-toggle");
      if (target === "login" || target === "signup") setMode(target);
    });
  });

  // Optional: prevent form submit reload (kalau belum ada backend)
  document.getElementById("loginForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    // TODO: integrate real auth here later
  });

  document.getElementById("signupForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    // TODO: integrate real auth here later
  });
})();
