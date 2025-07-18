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
    // Add Create Session button to the left
    const createSessionArea = document.getElementById("createSessionArea");
    if (createSessionArea) {
      // Only show Create Session for Admin/Faculty
      if (user.role === "Admin" || user.role === "Faculty") {
        createSessionArea.innerHTML = `
          <button id="createSessionHeaderBtn" class="bg-white text-ubc-blue hover:bg-gray-100 px-6 py-2 rounded text-sm font-medium transition-colors shadow-sm">
            🎓 Create New Session
          </button>
        `;
      } else {
        createSessionArea.innerHTML = "";
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

    // Initialize dropdown functionality
    this.initializeDropdown();
  }

  initializeDropdown() {
    const userDropdownBtn = document.getElementById("userDropdownBtn");
    const userDropdownMenu = document.getElementById("userDropdownMenu");

    if (userDropdownBtn && userDropdownMenu) {
      // Toggle dropdown on button click
      userDropdownBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        userDropdownMenu.classList.toggle("hidden");
      });

      // Close dropdown when clicking outside
      document.addEventListener("click", (e) => {
        if (
          !userDropdownBtn.contains(e.target) &&
          !userDropdownMenu.contains(e.target)
        ) {
          userDropdownMenu.classList.add("hidden");
        }
      });
    }
  }

  initializeLogout() {
    document.addEventListener("click", (e) => {
      if (e.target.id === "logoutBtn") {
        this.handleLogout();
      }
      if (e.target.id === "createSessionHeaderBtn") {
        window.location.href = "/create-new-session";
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
