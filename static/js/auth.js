class AuthManager {
  constructor() {
    this.checkAuthentication();
    this.initializeLogout();
  }

  async checkAuthentication() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      if (!result.authenticated) {
        window.location.href = "/login";
        return;
      }

      // Update UI with user info
      this.updateUserInfo(result.user);
    } catch (error) {
      console.error("Auth check failed:", error);
      window.location.href = "/login";
    }
  }

  updateUserInfo(user) {
    // Add user info to the left (where purple arrow points)
    const userInfoArea = document.getElementById("userInfo");
    if (userInfoArea) {
      userInfoArea.innerHTML = `
                <div class="text-left">
                    <div class="text-white text-base font-medium">Welcome, ${user.full_name}</div>
                    <div class="text-ubc-gray-light text-sm">${user.role}</div>
                </div>
            `;
    }

    // Add logout button to the far right (where red arrow points)
    const logoutArea = document.getElementById("logoutArea");
    if (logoutArea) {
      logoutArea.innerHTML = `
                <button id="logoutBtn" class="bg-white text-ubc-blue hover:bg-gray-100 px-6 py-2 rounded text-sm font-medium transition-colors shadow-sm">
                    Logout
                </button>
            `;
    }
  }

  initializeLogout() {
    document.addEventListener("click", (e) => {
      if (e.target.id === "logoutBtn") {
        this.handleLogout();
      }
    });
  }

  async handleLogout() {
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });

      const result = await response.json();

      if (result.success) {
        window.location.href = "/login";
      }
    } catch (error) {
      console.error("Logout error:", error);
      // Force redirect anyway
      window.location.href = "/login";
    }
  }
}
