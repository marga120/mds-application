/**
 * LOGIN MANAGER
 * 
 * This file handles the login page functionality including user authentication,
 * form validation, session checking, and login form submission. It manages
 * the login process and redirects users to the main application upon success.
 */

class LoginManager {
  constructor() {
    this.initializeEventListeners();
    this.checkExistingSession();
  }

  initializeEventListeners() {
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }
  }

  async checkExistingSession() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      if (result.authenticated) {
        // User is already logged in, redirect to dashboard
        window.location.href = "/";
      }
    } catch (error) {
      console.log("No existing session");
    }
  }

  async handleLogin() {
    const loginBtn = document.getElementById("loginBtn");
    const messageDiv = document.getElementById("message");

    // Get form data
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember").checked;

    if (!email || !password) {
      this.showMessage("Please enter both email and password", "error");
      return;
    }

    // Disable button and show loading
    loginBtn.disabled = true;
    loginBtn.textContent = "Signing in...";

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
          remember: remember,
        }),
        credentials: "include", // Important for cookies
      });

      const result = await response.json();

      if (result.success) {
        window.location.href = result.redirect || "/";
      } else {
        this.showMessage(result.message || "Login failed", "error");
      }
    } catch (error) {
      this.showMessage("Network error. Please try again.", "error");
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = "Sign in";
    }
  }

  showMessage(text, type) {
    const messageDiv = document.getElementById("message");
    messageDiv.textContent = text;
    messageDiv.className = `p-4 rounded-md ${
      type === "success"
        ? "bg-green-100 text-green-700"
        : "bg-red-100 text-red-700"
    }`;
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }
}

// Initialize login manager when page loads
document.addEventListener("DOMContentLoaded", function () {
  new LoginManager();
});
