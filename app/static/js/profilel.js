function copyText(text){
  if(!text) return;
  navigator.clipboard?.writeText(text).catch(() => {});
}

const usernameInput = document.getElementById("usernameInput");
const emailInput = document.getElementById("emailInput");

document.getElementById("copyUsernameBtn")?.addEventListener("click", () => {
  copyText(usernameInput?.value.trim());
});

document.getElementById("copyEmailBtn")?.addEventListener("click", () => {
  copyText(emailInput?.value.trim());
});

// Change Password click
document.getElementById("changePasswordBtn")?.addEventListener("click", () => {
  window.location.href = "/change-password";
});

// Logout click
document.getElementById("logoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "/login";
});
