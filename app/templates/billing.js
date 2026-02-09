/* billing.js
   Minimal plan + upgrade flow (demo) aligned with your current project:
   - Uses auth.js pattern: login.html?next=...
   - Stores plan in localStorage
   - Updates pricing UI when plan changes
*/
(() => {
  "use strict";

  const PLAN_KEY = "detectify_plan"; // "free" | "pro"
  const DEFAULT_PLAN = "free";

  const safeStorage = {
    get(key) {
      try { return localStorage.getItem(key); } catch { return null; }
    },
    set(key, val) {
      try { localStorage.setItem(key, val); } catch { /* ignore */ }
    },
    del(key) {
      try { localStorage.removeItem(key); } catch { /* ignore */ }
    }
  };

  function getPlan() {
    const p = (safeStorage.get(PLAN_KEY) || "").toLowerCase();
    return (p === "pro" || p === "free") ? p : DEFAULT_PLAN;
  }

  function setPlan(plan) {
    const p = (plan || "").toLowerCase();
    safeStorage.set(PLAN_KEY, (p === "pro") ? "pro" : "free");
  }

  // ---------------------------------
  // Upgrade redirect using auth.js
  // ---------------------------------
  function goLoginThenReturnToUpgrade() {
    // after login, user returns here and we activate pro in demo
    const next = "pricing.html?plan=pro&upgraded=1";
    location.href = `login.html?next=${encodeURIComponent(next)}`;
  }

  // ---------------------------------
  // Modal
  // ---------------------------------
  const modal = document.getElementById("upgradeModal");
  const openBtn = document.getElementById("upgradeToProBtn");
  const confirmBtn = document.getElementById("confirmUpgradeBtn");

  let lastFocused = null;

  function openModal() {
    if (!modal) return;
    lastFocused = document.activeElement;

    modal.hidden = false;
    document.body.classList.add("modal-open");
    document.addEventListener("keydown", onKeydown);

    // focus primary action
    confirmBtn?.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    document.removeEventListener("keydown", onKeydown);

    // restore focus
    if (lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  function onKeydown(e) {
    if (e.key === "Escape") closeModal();
  }

  // click-to-close overlay / close buttons
  modal?.addEventListener("click", (e) => {
    const t = e.target;
    if (t?.matches?.("[data-modal-close]")) closeModal();
  });

  openBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    if (getPlan() === "pro") return; // already pro
    openModal();
  });

  confirmBtn?.addEventListener("click", () => {
    // In a real app: call backend checkout -> return_url to pricing.html?...
    // For this build: use login redirect and then "activate" Pro
    goLoginThenReturnToUpgrade();
  });

  // ---------------------------------
  // Apply upgrade if returned from login
  // ---------------------------------
  function applyUpgradeFromQuery() {
    const url = new URL(location.href);
    const plan = (url.searchParams.get("plan") || "").toLowerCase();
    const upgraded = url.searchParams.get("upgraded");

    if (upgraded === "1" && plan === "pro") {
      setPlan("pro");

      // clean the URL so it looks nice
      url.searchParams.delete("plan");
      url.searchParams.delete("upgraded");
      history.replaceState({}, "", url.pathname + (url.search ? url.search : "") + url.hash);
    }
  }

  // ---------------------------------
  // Update Pricing UI (Free vs Pro)
  // ---------------------------------
  function updatePricingUI() {
    const plan = getPlan();

    const proCta = document.getElementById("upgradeToProBtn");
    const freeCard = document.querySelector(".plan--free");
    const proCard = document.querySelector(".plan--pro");

    // If your Free CTA has a class, we can grab it safely:
    const freeCta = freeCard?.querySelector(".plan__cta");

    if (plan === "pro") {
      // Pro becomes current
      if (proCta) {
        proCta.textContent = "Your current plan";
        proCta.setAttribute("aria-disabled", "true");
        proCta.style.pointerEvents = "none";
        proCta.style.filter = "grayscale(0.1)";
        proCta.style.opacity = "0.92";
      }

      // Free offers downgrade (optional)
      if (freeCta) {
        freeCta.textContent = "Downgrade to Free";
        freeCta.classList.remove("plan__cta--current");
        freeCta.href = "#";
        freeCta.addEventListener("click", (e) => {
          e.preventDefault();
          setPlan("free");
          // quick refresh of UI only
          updatePricingUI();
        }, { once: true });
      }
    } else {
      // Free is current (default)
      if (proCta) {
        proCta.textContent = "Upgrade to Pro";
        proCta.removeAttribute("aria-disabled");
        proCta.style.pointerEvents = "";
        proCta.style.filter = "";
        proCta.style.opacity = "";
      }

      if (freeCta) {
        freeCta.textContent = "Your current plan";
        freeCta.classList.add("plan__cta--current");
      }
    }
  }

  // init
  applyUpgradeFromQuery();
  updatePricingUI();
})();
