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
    // Add Sessions dropdown to the left
    const sessionsDropdownArea = document.getElementById(
      "sessionsDropdownArea"
    );
    if (sessionsDropdownArea) {
      // Only show Sessions dropdown for Admin/Faculty
      if (user.role === "Admin" || user.role === "Faculty") {
        sessionsDropdownArea.innerHTML = `
          <div class="relative">
            <button id="sessionsDropdownBtn" class="bg-white text-ubc-blue hover:bg-gray-100 px-6 py-2 rounded text-sm font-medium transition-colors shadow-sm flex items-center gap-2">
              📋 Sessions
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            <div id="sessionsDropdownMenu" class="hidden absolute left-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
              <a href="/create-new-session" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
                🎓 Create New Session
              </a>
              <button class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md border-t border-gray-100">
                📊 View All Sessions
              </button>
            </div>
          </div>
        `;
      } else {
        sessionsDropdownArea.innerHTML = "";
      }
    }

    // Add user dropdown to the right
    const userDropdownArea = document.getElementById("userDropdownArea");
    if (userDropdownArea) {
      userDropdownArea.innerHTML = `
        <div class="relative">
          <button id="userDropdownBtn" class="bg-white text-ubc-blue hover:bg-gray-100 px-6 py-2 rounded text-sm font-medium transition-colors shadow-sm flex items-center gap-2">
            <div class="text-left">
              <div class="font-medium">Welcome, ${user.full_name}</div>
              <div class="text-xs text-gray-600">${user.role}</div>
            </div>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
            <button id="logoutBtn" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
              Logout
            </button>
          </div>
        </div>
      `;
    }

    // Initialize both dropdowns
    this.initializeDropdowns();
  }

  initializeDropdowns() {
    // User dropdown functionality
    const userDropdownBtn = document.getElementById("userDropdownBtn");
    const userDropdownMenu = document.getElementById("userDropdownMenu");

    if (userDropdownBtn && userDropdownMenu) {
      userDropdownBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        userDropdownMenu.classList.toggle("hidden");
        // Close sessions dropdown if open
        const sessionsDropdownMenu = document.getElementById(
          "sessionsDropdownMenu"
        );
        if (sessionsDropdownMenu) {
          sessionsDropdownMenu.classList.add("hidden");
        }
      });
    }

    // Sessions dropdown functionality
    const sessionsDropdownBtn = document.getElementById("sessionsDropdownBtn");
    const sessionsDropdownMenu = document.getElementById(
      "sessionsDropdownMenu"
    );

    if (sessionsDropdownBtn && sessionsDropdownMenu) {
      sessionsDropdownBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        sessionsDropdownMenu.classList.toggle("hidden");
        // Close user dropdown if open
        if (userDropdownMenu) {
          userDropdownMenu.classList.add("hidden");
        }
      });
    }

    // Close dropdowns when clicking outside
    document.addEventListener("click", (e) => {
      const isUserDropdown =
        userDropdownBtn &&
        (userDropdownBtn.contains(e.target) ||
          (userDropdownMenu && userDropdownMenu.contains(e.target)));
      const isSessionsDropdown =
        sessionsDropdownBtn &&
        (sessionsDropdownBtn.contains(e.target) ||
          (sessionsDropdownMenu && sessionsDropdownMenu.contains(e.target)));

      if (!isUserDropdown && userDropdownMenu) {
        userDropdownMenu.classList.add("hidden");
      }
      if (!isSessionsDropdown && sessionsDropdownMenu) {
        sessionsDropdownMenu.classList.add("hidden");
      }
    });
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
