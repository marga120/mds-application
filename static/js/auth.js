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
            <button id="sessionsDropdownBtn" class="bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 border border-white/20">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Sessions
              <svg class="w-3 h-3 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          <button id="userDropdownBtn" class="bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-3 border border-white/20">
            <!-- User Avatar -->
            <div class="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <span class="text-white font-semibold text-sm">${user.full_name
                .split(" ")
                .map((n) => n[0])
                .join("")}</span>
            </div>
            <div class="text-left hidden md:block">
              <div class="font-medium text-white">${user.full_name}</div>
              <div class="text-xs text-white/70">${user.role}</div>
            </div>
            <svg class="w-3 h-3 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        const isHidden = userDropdownMenu.classList.contains("hidden");

        // Close sessions dropdown if open
        const sessionsDropdownMenu = document.getElementById(
          "sessionsDropdownMenu"
        );
        if (sessionsDropdownMenu) {
          sessionsDropdownMenu.classList.add("hidden");
          sessionsDropdownMenu.classList.remove("show");
        }

        // Toggle user dropdown with animation
        if (isHidden) {
          userDropdownMenu.classList.remove("hidden");
          setTimeout(() => userDropdownMenu.classList.add("show"), 10);
        } else {
          userDropdownMenu.classList.remove("show");
          setTimeout(() => userDropdownMenu.classList.add("hidden"), 200);
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
