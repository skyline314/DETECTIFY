/**
 * billing.js
 * Prinsip: KISS - Cek localStorage, Request Transaksi, Redirect.
 */

document.addEventListener("DOMContentLoaded", () => {
  const API_TRANSACTION = "/api/payment/create-transaction"; // Perhatikan /api
  
  const upgradeBtn = document.getElementById("upgradeToProBtn"); // Tombol di card Pro
  const modal = document.getElementById("upgradeModal");
  const confirmBtn = document.getElementById("confirmUpgradeBtn"); // Tombol di Modal
  const closeBtns = document.querySelectorAll("[data-modal-close]");

  // 1. Cek Status User (UI Logic)
  function checkStatus() {
    const userStr = localStorage.getItem("detectify_user");
    if (userStr) {
      const user = JSON.parse(userStr);
      // Asumsi backend kirim 'plan_type' di object user saat login
      if (user.plan_type === 'premium') { 
        updateUI('pro');
      }
    }
  }

  function updateUI(plan) {
    const proCta = document.querySelector(".plan--pro .plan__cta");
    if (plan === 'pro' && proCta) {
      proCta.textContent = "Current Plan";
      proCta.classList.add("plan__cta--current");
      proCta.href = "javascript:void(0)";
      proCta.style.pointerEvents = "none";
    }
  }

  // 2. Handle Upgrade (Midtrans)
  if (confirmBtn) {
    confirmBtn.addEventListener("click", async () => {
      const token = localStorage.getItem("detectify_token");
      if (!token) return (window.location.href = "/auth/login-page");

      confirmBtn.disabled = true;
      confirmBtn.textContent = "Processing...";

      try {
        const res = await fetch(API_TRANSACTION, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        });

        const data = await res.json();

        if (res.ok && data.redirect_url) {
          window.location.href = data.redirect_url; // Redirect ke Midtrans
        } else {
          alert("Gagal: " + (data.error || "Unknown error"));
        }
      } catch (e) {
        alert("Connection error");
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
        if (!token) window.location.href = "/auth/login-page";
        else toggleModal(true);
      });
  }
  
  closeBtns.forEach(b => b.addEventListener("click", () => toggleModal(false)));

  checkStatus();
});