/**
 * billing.js
 * Handles the Upgrade to Pro flow via Midtrans Snap popup (no redirect).
 */

document.addEventListener("DOMContentLoaded", () => {
  const API_TRANSACTION = "/api/payment/create-transaction";
  const AUTH_URL = "/auth/get-started";

  const upgradeBtn = document.getElementById("upgradeToProBtn");
  const modal = document.getElementById("upgradeModal");
  const confirmBtn = document.getElementById("confirmUpgradeBtn");
  const closeBtns = document.querySelectorAll("[data-modal-close]");

  // 1. Check user status & update UI if already premium
  async function checkStatus() {
    const token = localStorage.getItem("detectify_token");
    if (!token) return;

    try {
      const res = await fetch("/auth/me", {
        headers: { Authorization: "Bearer " + token },
      });
      if (!res.ok) return;
      const user = await res.json();

      if (user.plan === "premium") {
        updateUI("pro", user.plan_expires_at);
      }
    } catch {
      // ignore
    }
  }

  function updateUI(plan, expiresAt) {
    if (plan === "pro") {
      const proCta = document.getElementById("upgradeToProBtn");
      if (proCta) {
        if (expiresAt) {
          const d = new Date(expiresAt).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
          proCta.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 4px 0;">
              <div>Current Plan</div>
              <div style="font-size: 13px; opacity: 0.8; font-weight: 500; text-transform: none;">Valid until: ${d}</div>
            </div>
          `;
        } else {
          proCta.textContent = "Current Plan";
        }
        proCta.classList.add("plan__cta--current");
        proCta.style.pointerEvents = "none";
        proCta.removeAttribute("href");
      }

      const freeCta = document.getElementById("freeTierBtn");
      if (freeCta) {
        freeCta.textContent = "Free Plan";
        freeCta.classList.remove("plan__cta--current");
      }
    }
  }

  // Show success message inline
  function showPaymentResult(type, message) {
    toggleModal(false);

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const overlay = document.createElement("div");
    overlay.className = "payment-result-overlay";
    Object.assign(overlay.style, {
      position: "fixed", inset: "0", zIndex: "9999",
      background: "rgba(0,0,0,.55)", backdropFilter: "blur(6px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    });

    const isSuccess = type === "success";
    const iconBg = isSuccess
      ? "linear-gradient(135deg,#10b981,#059669)"
      : "linear-gradient(135deg,#f59e0b,#d97706)";
    const iconSvg = isSuccess
      ? `<svg width="32" height="32" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4L19 7" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
      : `<svg width="32" height="32" viewBox="0 0 24 24" fill="none"><path d="M12 9v4m0 4h.01M12 3l9.66 16.59A1 1 0 0120.66 21H3.34a1 1 0 01-.86-1.41L12 3z" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    const title = isSuccess ? "Payment Successful!" : "Payment Pending";
    const desc = isSuccess
      ? "Your premium plan is now active. Enjoy unlimited access!"
      : message || "Your payment is being processed. Please wait for confirmation.";

    const modalBg = isDark ? "linear-gradient(150deg, #111827, #0f172a)" : "#fff";
    const modalBorder = isDark ? "1px solid rgba(255,255,255,.1)" : "1px solid rgba(0,0,0,.08)";
    const textColor = isDark ? "#eaf2ff" : "#1e293b";

    overlay.innerHTML = `
      <div style="width:min(420px,90%);border-radius:20px;padding:32px 28px;text-align:center;
                  background:${modalBg};border:${modalBorder};color:${textColor};
                  box-shadow:0 20px 60px rgba(0,0,0,.3)">
        <div style="width:72px;height:72px;margin:0 auto 16px;border-radius:50%;display:grid;place-items:center;
                    background:${iconBg}">
          ${iconSvg}
        </div>
        <h3 style="font-size:22px;font-weight:700;margin:0 0 8px">${title}</h3>
        <p style="font-size:14px;line-height:1.6;margin:0 0 24px;opacity:.75">${desc}</p>
        <button id="paymentResultOk" type="button"
          style="padding:12px 32px;border-radius:999px;font-size:14px;font-weight:700;border:none;cursor:pointer;
                 background:linear-gradient(135deg,#0ea5c7,#7c3aed);color:#fff;
                 box-shadow:0 8px 24px rgba(14,165,199,.25)">
          ${isSuccess ? "Let's Go!" : "OK"}
        </button>
      </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById("paymentResultOk").addEventListener("click", () => {
      overlay.remove();
      if (isSuccess) {
        window.location.reload();
      }
    });
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.remove();
        if (isSuccess) window.location.reload();
      }
    });
  }

  // 2. Handle Upgrade via Midtrans Snap (popup, no redirect)
  if (confirmBtn) {
    confirmBtn.addEventListener("click", async () => {
      const token = localStorage.getItem("detectify_token");
      if (!token) return (window.location.href = AUTH_URL);

      confirmBtn.disabled = true;
      confirmBtn.textContent = "Processing...";

      try {
        const res = await fetch(API_TRANSACTION, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        const data = await res.json();

        if (res.ok && data.token) {
          // Close the upgrade modal first
          toggleModal(false);

          // Open Midtrans Snap popup
          window.snap.pay(data.token, {
            onSuccess: function (result) {
              console.log("Payment success:", result);
              showPaymentResult("success", "Premium activated!");
            },
            onPending: function (result) {
              console.log("Payment pending:", result);
              showPaymentResult("pending", "Your payment is being processed. You'll be notified once it's confirmed.");
            },
            onError: function (result) {
              console.log("Payment error:", result);
              showPaymentResult("error", "Payment failed. Please try again.");
            },
            onClose: function () {
              // User closed the popup without completing payment
              console.log("Snap popup closed");
            },
          });
        } else {
          alert("Failed: " + (data.error || "Unknown error"));
        }
      } catch (e) {
        console.error("Payment error:", e);
        alert("Connection error. Please try again.");
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Continue";
      }
    });
  }

  // Modal Handlers
  const toggleModal = (show) => {
    if (modal) {
      modal.hidden = !show;
      modal.classList.toggle("is-open", show);
    }
  };

  if (upgradeBtn) {
    upgradeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const token = localStorage.getItem("detectify_token");
      if (!token) window.location.href = AUTH_URL;
      else toggleModal(true);
    });
  }

  closeBtns.forEach((b) =>
    b.addEventListener("click", () => toggleModal(false))
  );

  checkStatus();
});