class AccountManager {
  constructor() {
    this.currentUser = null;
    this.loadUserInfo();
    this.initializeEventListeners();
  }

  async loadUserInfo() {
    try {
      const response = await fetch("/api/auth/user");
      const result = await response.json();

      if (result.success && result.user) {
        this.currentUser = result.user;

        document.getElementById("displayName").textContent = this.currentUser.full_name;
        document.getElementById("displayEmail").textContent = this.currentUser.email;
        document.getElementById("displayRole").textContent = this.currentUser.role;
      }
    } catch (error) {
      console.error("Error loading user info:", error);
    }
  }

  initializeEventListeners() {
    // Personal Settings
    document.getElementById("updateEmailForm").addEventListener("submit", (e) => { e.preventDefault(); this.handleUpdateEmail(); });
    document.getElementById("changePasswordForm").addEventListener("submit", (e) => { e.preventDefault(); this.handleChangePassword(); });
  }
  //Personal Settings
  async handleUpdateEmail() {
    const newEmail = document.getElementById("newEmail").value;
    const password = document.getElementById("emailPassword").value;
    const messageDiv = document.getElementById("emailMessage");

    try {
        const response = await fetch("/api/auth/update-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ new_email: newEmail, password: password })
        });
        const result = await response.json();
        this.showMessage(messageDiv, result.message, result.success ? "success" : "error");
        if(result.success) this.loadUserInfo();
    } catch (e) { console.error(e); }
  }

  async handleChangePassword() {
    const current = document.getElementById("currentPasswordAccount").value;
    const newPass = document.getElementById("newPasswordAccount").value;
    const confirm = document.getElementById("confirmPasswordAccount").value;
    const messageDiv = document.getElementById("passwordMessage");

    if (newPass !== confirm) return this.showMessage(messageDiv, "Passwords do not match", "error");

    try {
        const response = await fetch("/api/auth/reset-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ current_password: current, new_password: newPass })
        });
        const result = await response.json();
        this.showMessage(messageDiv, result.message, result.success ? "success" : "error");
        if(result.success) document.getElementById("changePasswordForm").reset();
    } catch (e) { console.error(e); }
  }

  showMessage(element, text, type) {
    element.textContent = text;
    element.className = `p-3 rounded-md mb-4 text-sm ${
      type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
    }`;
    element.classList.remove("hidden");
    setTimeout(() => element.classList.add("hidden"), 5000);
  }
}

let accountManager;
document.addEventListener("DOMContentLoaded", () => {
  // Initialize AuthManager for header dropdowns
  new AuthManager();

  // Initialize AccountManager for account settings functionality
  accountManager = new AccountManager();
});
