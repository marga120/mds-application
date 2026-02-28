/**
 * pages/account.js
 * Account settings page controller.
 * Uses: AuthService, Notification, validators
 */
import { authService } from "../services/auth-service.js";
import { Notification } from "../components/notification.js";
import {
  validatePassword,
  validateConfirmPassword,
} from "../utils/validators.js";

class AccountManager {
  constructor() {
    this._loadUserInfo();
    this._bindForms();
  }

  async _loadUserInfo() {
    try {
      const result = await authService.getCurrentUser();
      if (result.success && result.user) {
        const u = result.user;
        const el = (id) => document.getElementById(id);
        if (el("displayName")) el("displayName").textContent = u.full_name;
        if (el("displayEmail")) el("displayEmail").textContent = u.email;
        if (el("displayRole")) el("displayRole").textContent = u.role;
      }
    } catch (err) {
      console.error("Error loading user info:", err);
    }
  }

  _bindForms() {
    const pwForm = document.getElementById("changePasswordForm");
    if (pwForm) {
      pwForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this._handleChangePassword();
      });
    }
  }

  async _handleChangePassword() {
    const current = document.getElementById("currentPasswordAccount").value;
    const newPass = document.getElementById("newPasswordAccount").value;
    const confirm = document.getElementById("confirmPasswordAccount").value;

    const pwCheck = validatePassword(newPass);
    if (!pwCheck.valid) return Notification.error(pwCheck.message);

    const confirmCheck = validateConfirmPassword(newPass, confirm);
    if (!confirmCheck.valid) return Notification.error(confirmCheck.message);

    try {
      const result = await authService.resetPassword(current, newPass);
      if (result.success) {
        Notification.success("Password changed successfully.");
        document.getElementById("changePasswordForm").reset();
      } else {
        Notification.error(result.message || "Failed to change password.");
      }
    } catch (err) {
      Notification.error(err.message || "An error occurred.");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // AuthManager is loaded globally via auth.js in the template
  if (typeof AuthManager !== "undefined") new AuthManager();
  new AccountManager();
});
