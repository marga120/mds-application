/**
 * pages/login.js
 * Login page controller.
 * Uses: AuthService, Notification
 */
import { authService } from "../services/auth-service.js";
import { Notification } from "../components/notification.js";

class LoginManager {
  constructor() {
    this._checkExistingSession();
    this._bindForm();
  }

  async _checkExistingSession() {
    try {
      const result = await authService.checkSession();
      if (result.authenticated) window.location.href = "/";
    } catch {
      // No session — stay on login page
    }
  }

  _bindForm() {
    const form = document.getElementById("loginForm");
    if (form)
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        this._handleLogin();
      });
  }

  async _handleLogin() {
    const loginBtn = document.getElementById("loginBtn");
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember")?.checked ?? false;

    if (!email || !password) {
      this._showInlineError("Please enter both email and password.");
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = "Signing in...";

    try {
      const result = await authService.login(email, password, remember);
      window.location.href = result.redirect || "/";
    } catch (err) {
      this._showInlineError(err.message || "Login failed. Please try again.");
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = "Sign in";
    }
  }

  // The login template has a dedicated #message div — use it when present.
  _showInlineError(message) {
    const messageDiv = document.getElementById("message");
    if (messageDiv) {
      messageDiv.textContent = message;
      messageDiv.className = "p-4 rounded-md bg-red-100 text-red-700";
      messageDiv.classList.remove("hidden");
      setTimeout(() => messageDiv.classList.add("hidden"), 5000);
    } else {
      Notification.error(message);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new LoginManager());
