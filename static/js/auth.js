/**
 * AUTHENTICATION MANAGER
 * 
 * This file handles user authentication, session management, and role-based access control.
 * It manages user login/logout, session validation, user information display, 
 * and updates the UI based on user permissions (Admin, Faculty, Viewer roles).
 */

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
      this.updateUploadSection(result.user);
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
      // Show Sessions dropdown for all users, but different content based on role
      const createSessionOption =
        user.role === "Admin"
          ? `<a href="/create-new-session" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
             Create New Session
           </a>
           <div class="border-t border-gray-100"></div>`
          : "";

      sessionsDropdownArea.innerHTML = `
        <div class="relative">
          <button id="sessionsDropdownBtn" class="bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 border border-white/20">
            Sessions
            <svg class="w-3 h-3 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
          <div id="sessionsDropdownMenu" class="hidden absolute left-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
            ${createSessionOption}
            <button class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
              View All Sessions
            </button>
          </div>
        </div>
      `;
    }

    // Add Data dropdown (only for Admin users)
    const dataDropdownArea = document.getElementById("logsDropdownArea");
    if (dataDropdownArea) {
      if (user.role === "Admin") {
        dataDropdownArea.innerHTML = `
          <div class="relative">
            <button id="dataDropdownBtn" class="bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 border border-white/20">
              Data
              <svg class="w-3 h-3 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            <div id="dataDropdownMenu" class="hidden absolute left-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
              <button id="uploadCsvMenuBtn" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
                Upload CSV
              </button>
              <button id="clearDataMenuBtn" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
                Clear All Data
              </button>
              <div class="border-t border-gray-100"></div>
              <a href="/logs" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md">
                View Logs
              </a>
            </div>
          </div>
        `;
      } else {
        // Clear data dropdown for non-admin users
        dataDropdownArea.innerHTML = "";
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

  updateUploadSection(user) {
  const uploadSection = document.getElementById("uploadSection");
  const clearDataSection = document.getElementById("clearDataSection");
  
  if (user.role === "Viewer" || user.role === "Faculty") {
    if (uploadSection) {
      uploadSection.style.display = "none";
    }
    if (clearDataSection) {
      clearDataSection.style.display = "none";
    }
  } else if (user.role === "Admin") {
    if (uploadSection) {
      uploadSection.style.display = "block";
    }
    if (clearDataSection) {
      clearDataSection.style.display = "block";
    }
  }
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

        // Close logs dropdown if open
        const logsDropdownMenu = document.getElementById("logsDropdownMenu");
        if (logsDropdownMenu) {
          logsDropdownMenu.classList.add("hidden");
          logsDropdownMenu.classList.remove("show");
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
        const isHidden = sessionsDropdownMenu.classList.contains("hidden");

        // Close user dropdown if open
        if (userDropdownMenu) {
          userDropdownMenu.classList.add("hidden");
          userDropdownMenu.classList.remove("show");
        }

        // Close data dropdown if open
        const dataDropdownMenu = document.getElementById("dataDropdownMenu");
        if (dataDropdownMenu) {
          dataDropdownMenu.classList.add("hidden");
          dataDropdownMenu.classList.remove("show");
        }

        // Toggle sessions dropdown with animation
        if (isHidden) {
          sessionsDropdownMenu.classList.remove("hidden");
          setTimeout(() => sessionsDropdownMenu.classList.add("show"), 10);
        } else {
          sessionsDropdownMenu.classList.remove("show");
          setTimeout(() => sessionsDropdownMenu.classList.add("hidden"), 200);
        }
      });
    }

    // Add data dropdown functionality
    const dataDropdownBtn = document.getElementById("dataDropdownBtn");
    const dataDropdownMenu = document.getElementById("dataDropdownMenu");

    if (dataDropdownBtn && dataDropdownMenu) {
      dataDropdownBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isHidden = dataDropdownMenu.classList.contains("hidden");

        // Close other dropdowns
        if (userDropdownMenu) {
          userDropdownMenu.classList.add("hidden");
          userDropdownMenu.classList.remove("show");
        }
        if (sessionsDropdownMenu) {
          sessionsDropdownMenu.classList.add("hidden");
          sessionsDropdownMenu.classList.remove("show");
        }

        // Toggle data dropdown with animation
        if (isHidden) {
          dataDropdownMenu.classList.remove("hidden");
          setTimeout(() => dataDropdownMenu.classList.add("show"), 10);
        } else {
          dataDropdownMenu.classList.remove("show");
          setTimeout(() => dataDropdownMenu.classList.add("hidden"), 200);
        }
      });
    }

    // Add event listeners for Upload CSV and Clear Data from dropdown
    const uploadCsvMenuBtn = document.getElementById('uploadCsvMenuBtn');
    if (uploadCsvMenuBtn) {
      uploadCsvMenuBtn.addEventListener('click', () => {
        // Close dropdown
        const dataDropdownMenu = document.getElementById("dataDropdownMenu");
        if (dataDropdownMenu) {
          dataDropdownMenu.classList.remove("show");
          setTimeout(() => dataDropdownMenu.classList.add("hidden"), 200);
        }
        // Open upload modal
        if (window.applicantsManager) {
          window.applicantsManager.openUploadModal();
        }
      });
    }

    const clearDataMenuBtn = document.getElementById('clearDataMenuBtn');
    if (clearDataMenuBtn) {
      clearDataMenuBtn.addEventListener('click', () => {
        // Close dropdown
        const dataDropdownMenu = document.getElementById("dataDropdownMenu");
        if (dataDropdownMenu) {
          dataDropdownMenu.classList.remove("show");
          setTimeout(() => dataDropdownMenu.classList.add("hidden"), 200);
        }
        // Open clear data modal
        if (window.applicantsManager) {
          window.applicantsManager.confirmClearAllData();
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
      // Add data dropdown check
      const isDataDropdown =
        dataDropdownBtn &&
        (dataDropdownBtn.contains(e.target) ||
          (dataDropdownMenu && dataDropdownMenu.contains(e.target)));

      if (!isUserDropdown && userDropdownMenu) {
        userDropdownMenu.classList.add("hidden");
        userDropdownMenu.classList.remove("show");
      }
      if (!isSessionsDropdown && sessionsDropdownMenu) {
        sessionsDropdownMenu.classList.add("hidden");
        sessionsDropdownMenu.classList.remove("show");
      }
      // Close data dropdown when clicking outside
      if (!isDataDropdown && dataDropdownMenu) {
        dataDropdownMenu.classList.add("hidden");
        dataDropdownMenu.classList.remove("show");
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
