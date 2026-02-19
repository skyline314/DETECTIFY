function copyText(text){
  if(!text) return;
  navigator.clipboard?.writeText(text).catch(() => {});
}

// ambil elemen input
const usernameInput = document.getElementById("usernameInput");
const emailInput = document.getElementById("emailInput");

// copy selalu ambil value TERBARU dari input
document.getElementById("copyUsernameBtn")?.addEventListener("click", () => {
  copyText(usernameInput?.value?.trim());
});

document.getElementById("copyEmailBtn")?.addEventListener("click", () => {
  copyText(emailInput?.value?.trim());
});

// helper: biar sec-item bisa diklik juga via Enter/Space
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

// === FUNGSI "SESUUNGGUHNYA" (kamu tinggal ganti endpoint/route sesuai backend kamu) ===
// Change Password: biasanya redirect ke halaman form change password
function goToChangePassword(){
  // contoh route:
  window.location.href = "/change-password";
  // atau kalau pakai modal, bisa panggil modal di sini
}

// Logout: biasanya panggil API logout lalu redirect ke login
async function doLogout(){
  try{
    // contoh API logout (sesuaikan)
    // await fetch("/api/logout", { method: "POST", credentials: "include" });

    // minimal: bersihin token kalau kamu simpan di localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");

    // redirect ke login
    window.location.href = "/login";
  }catch(err){
    console.error(err);
  }
}

bindClickAndKeyboard(document.getElementById("changePasswordBtn"), goToChangePassword);
bindClickAndKeyboard(document.getElementById("logoutBtn"), doLogout);

// Upgrade (opsional): arahkan ke halaman pricing/upgrade
document.getElementById("upgradeBtn")?.addEventListener("click", () => {
  window.location.href = "/pricing";
});
