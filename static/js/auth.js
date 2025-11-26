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
    this.initializeResetPassword();
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
            <a href="/account" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-t-md">
              Account Settings
            </a>
            <button id="resetPasswordBtn" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
              Reset Password
            </button>
            <div class="border-t border-gray-100"></div>
            <button id="logoutBtn" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-b-md">
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
  
  initializeResetPassword() {
  // Open modal
  document.addEventListener("click", (e) => {
    if (e.target.id === "resetPasswordBtn") {
      const modal = document.getElementById("resetPasswordModal");
      modal.classList.remove("hidden");
      modal.classList.add("flex");
      
      // Close the user dropdown
      const userDropdownMenu = document.getElementById("userDropdownMenu");
      if (userDropdownMenu) {
        userDropdownMenu.classList.add("hidden");
      }
    }
  });

  //Close modal if x/cancel
  document.addEventListener("click", (e) => {
    const closeButton = e.target.closest("#closeResetPasswordModal");
    const cancelButton = e.target.closest("#cancelResetPassword");
    
    if (closeButton || cancelButton) {
      this.closeResetPasswordModal();
    }
  });

  // Handle form submission
  const form = document.getElementById("resetPasswordForm");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.handleResetPassword();
    });
  }
}
//close pass modal
closeResetPasswordModal() {
  const modal = document.getElementById("resetPasswordModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
  
  document.getElementById("resetPasswordForm").reset();
  document.getElementById("resetPasswordError").classList.add("hidden");
  document.getElementById("resetPasswordSuccess").classList.add("hidden");
}

  async handleResetPassword() {
    const currentPassword = document.getElementById("currentPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const errorDiv = document.getElementById("resetPasswordError");
    const successDiv = document.getElementById("resetPasswordSuccess");

    // Hide previous messages
    errorDiv.classList.add("hidden");
    successDiv.classList.add("hidden");

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      errorDiv.textContent = "New passwords do not match";
      errorDiv.classList.remove("hidden");
      return;
    }

    // Validate password length
    if (newPassword.length < 8) {
      errorDiv.textContent = "Password must be at least 8 characters";
      errorDiv.classList.remove("hidden");
      return;
    }

    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const result = await response.json();

      if (result.success) {
        successDiv.textContent = "Password reset successfully!";
        successDiv.classList.remove("hidden");
        
        // Close modal after 2 seconds
        setTimeout(() => {
          this.closeResetPasswordModal();
        }, 2000);
      } else {
        errorDiv.textContent = result.message || "Failed to reset password";
        errorDiv.classList.remove("hidden");
      }
    } catch (error) {
      console.error("Reset password error:", error);
      errorDiv.textContent = "An error occurred. Please try again.";
      errorDiv.classList.remove("hidden");
    }
  }

  createDataModals() {
  // Create Upload CSV Modal
  const uploadModalHTML = `
    <div id="uploadCsvModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
      <div class="relative top-20 mx-auto p-8 border w-11/12 max-w-2xl shadow-lg rounded-lg bg-white">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-semibold text-gray-900">Upload CSV File</h3>
          <button class="close-upload-modal text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="mb-6">
          <p class="text-gray-600 mb-4">Drag and drop your CSV file here or click to select</p>
          <div id="dropZoneModal" class="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-400 transition-colors cursor-pointer">
            <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <button type="button" class="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              Choose CSV File
            </button>
            <p class="mt-2 text-sm text-gray-500" id="fileNameModal">No file chosen</p>
          </div>
          <input type="file" id="csvFileInputModal" accept=".csv" class="hidden">
        </div>
        
        <div class="flex justify-end gap-3">
          <button class="close-upload-modal px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
            Cancel
          </button>
          <button id="uploadCsvBtnModal" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed" disabled>
            Upload CSV
          </button>
        </div>
        
        <div id="uploadStatusModal" class="mt-4 hidden"></div>
      </div>
    </div>
  `;
  
  // Create Clear Data Modal
  const clearModalHTML = `
    <div id="clearDataModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
      <div class="relative top-20 mx-auto p-8 border w-11/12 max-w-md shadow-lg rounded-lg bg-white">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-semibold text-red-600 flex items-center">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            Warning
          </h3>
          <button class="close-clear-modal text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="mb-6">
          <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p class="text-red-800 font-semibold mb-2">This action cannot be undone!</p>
            <p class="text-red-700 text-sm">This will permanently delete ALL applicant data from the database.</p>
          </div>
          
          <p class="text-gray-700 mb-4">Are you absolutely sure you want to clear all data?</p>
          
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p class="text-yellow-800 text-sm">This will delete data from all applicant-related tables.</p>
          </div>
        </div>
        
        <div class="flex justify-end gap-3">
          <button class="close-clear-modal px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
            Cancel
          </button>
          <button id="confirmClearDataBtn" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
            Yes, Delete All Data
          </button>
        </div>
        
        <div id="clearStatusModal" class="mt-4 hidden"></div>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', uploadModalHTML);
  document.body.insertAdjacentHTML('beforeend', clearModalHTML);
  
  this.setupUploadModal();
  this.setupClearModal();
}

setupUploadModal() {
  const uploadMenuItem = document.getElementById('uploadCsvMenuItem');
  const modal = document.getElementById('uploadCsvModal');
  const closeButtons = modal.querySelectorAll('.close-upload-modal');
  const dropZone = document.getElementById('dropZoneModal');
  const fileInput = document.getElementById('csvFileInputModal');
  const uploadBtn = document.getElementById('uploadCsvBtnModal');
  const fileName = document.getElementById('fileNameModal');
  const uploadStatus = document.getElementById('uploadStatusModal');
  
  let selectedFile = null;
  
  uploadMenuItem.addEventListener('click', (e) => {
    e.preventDefault();
    modal.classList.remove('hidden');
  });
  
  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modal.classList.add('hidden');
      selectedFile = null;
      fileName.textContent = 'No file chosen';
      fileInput.value = '';
      uploadBtn.disabled = true;
      uploadStatus.classList.add('hidden');
    });
  });
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.add('hidden');
    }
  });
  
  dropZone.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      selectedFile = file;
      fileName.textContent = file.name;
      uploadBtn.disabled = false;
    }
  });
  
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-400', 'bg-blue-50');
  });
  
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
  });
  
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-400', 'bg-blue-50');
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      selectedFile = file;
      fileName.textContent = file.name;
      uploadBtn.disabled = false;
    }
  });
  
  uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        uploadStatus.className = 'mt-4 p-4 rounded-lg bg-green-100 text-green-800';
        uploadStatus.textContent = 'CSV uploaded successfully! Reloading...';
        uploadStatus.classList.remove('hidden');
        setTimeout(() => window.location.reload(), 1500);
      } else {
        uploadStatus.className = 'mt-4 p-4 rounded-lg bg-red-100 text-red-800';
        uploadStatus.textContent = result.message || 'Upload failed';
        uploadStatus.classList.remove('hidden');
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload CSV';
      }
    } catch (error) {
      uploadStatus.className = 'mt-4 p-4 rounded-lg bg-red-100 text-red-800';
      uploadStatus.textContent = 'Error uploading file';
      uploadStatus.classList.remove('hidden');
      uploadBtn.disabled = false;
      uploadBtn.textContent = 'Upload CSV';
    }
  });
  }
  initializeResetPassword() {
    // Open modal
    document.addEventListener("click", (e) => {
      if (e.target.id === "resetPasswordBtn") {
        const modal = document.getElementById("resetPasswordModal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        
        // Close the user dropdown
        const userDropdownMenu = document.getElementById("userDropdownMenu");
        if (userDropdownMenu) {
          userDropdownMenu.classList.add("hidden");
        }
      }
    });

    // Close modal ONLY with X button or Cancel button
    document.addEventListener("click", (e) => {
      // Check if the clicked element or its parent is the close button or cancel button
      const closeButton = e.target.closest("#closeResetPasswordModal");
      const cancelButton = e.target.closest("#cancelResetPassword");
      
      if (closeButton || cancelButton) {
        this.closeResetPasswordModal();
      }
    });

    // Handle form submission
    const form = document.getElementById("resetPasswordForm");
    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleResetPassword();
      });
    }
  }
  closeResetPasswordModal() {
    const modal = document.getElementById("resetPasswordModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    
    document.getElementById("resetPasswordForm").reset();
    document.getElementById("resetPasswordError").classList.add("hidden");
    document.getElementById("resetPasswordSuccess").classList.add("hidden");
  }
  setupClearModal() {
    const clearMenuItem = document.getElementById('clearDataMenuItem');
    const modal = document.getElementById('clearDataModal');
    const closeButtons = modal.querySelectorAll('.close-clear-modal');
    const confirmBtn = document.getElementById('confirmClearDataBtn');
    const clearStatus = document.getElementById('clearStatusModal');
    
    clearMenuItem.addEventListener('click', (e) => {
      e.preventDefault();
      modal.classList.remove('hidden');
    });
    
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        modal.classList.add('hidden');
        clearStatus.classList.add('hidden');
      });
    });
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
    
    confirmBtn.addEventListener('click', async () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'Deleting...';
      
      try {
        const response = await fetch('/api/clear-all-data', {
          method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
          clearStatus.className = 'mt-4 p-4 rounded-lg bg-green-100 text-green-800';
          clearStatus.textContent = 'All data deleted successfully! Reloading...';
          clearStatus.classList.remove('hidden');
          setTimeout(() => window.location.reload(), 1500);
        } else {
          clearStatus.className = 'mt-4 p-4 rounded-lg bg-red-100 text-red-800';
          clearStatus.textContent = result.message || 'Failed to clear data';
          clearStatus.classList.remove('hidden');
          confirmBtn.disabled = false;
          confirmBtn.textContent = 'Yes, Delete All Data';
        }
      } catch (error) {
        clearStatus.className = 'mt-4 p-4 rounded-lg bg-red-100 text-red-800';
        clearStatus.textContent = 'Error clearing data';
        clearStatus.classList.remove('hidden');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Yes, Delete All Data';
      }
    });
  }
  async handleResetPassword() {
    const currentPassword = document.getElementById("currentPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const errorDiv = document.getElementById("resetPasswordError");
    const successDiv = document.getElementById("resetPasswordSuccess");

    // Hide previous messages
    errorDiv.classList.add("hidden");
    successDiv.classList.add("hidden");

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      errorDiv.textContent = "New passwords do not match";
      errorDiv.classList.remove("hidden");
      return;
    }

    // Validate password length
    if (newPassword.length < 8) {
      errorDiv.textContent = "Password must be at least 8 characters";
      errorDiv.classList.remove("hidden");
      return;
    }

    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const result = await response.json();

      if (result.success) {
        successDiv.textContent = "Password reset successfully!";
        successDiv.classList.remove("hidden");
        
        // Close modal after 2 seconds
        setTimeout(() => {
          this.closeResetPasswordModal();
        }, 2000);
      } else {
        errorDiv.textContent = result.message || "Failed to reset password";
        errorDiv.classList.remove("hidden");
      }
    } catch (error) {
      console.error("Reset password error:", error);
      errorDiv.textContent = "An error occurred. Please try again.";
      errorDiv.classList.remove("hidden");
    }
  }
}
