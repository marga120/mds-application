class AccountManager {
  constructor() {
    this.currentUser = null;
    this.searchTimeout = null;
    this.userToDelete = null; // Store ID for modal
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

        if (this.currentUser.role_id === 1) { // 1 = Admin
            this.enableAdminMode();
        }
      }
    } catch (error) {
      console.error("Error loading user info:", error);
    }
  }

  enableAdminMode() {
    const mainContainer = document.getElementById("mainContainer");
    mainContainer.classList.remove("max-w-2xl");
    mainContainer.classList.add("max-w-7xl");

    const contentGrid = document.getElementById("contentGrid");
    contentGrid.classList.remove("grid-cols-1");
    contentGrid.classList.add("lg:grid-cols-3");

    const adminSection = document.getElementById("adminSection");
    adminSection.classList.remove("hidden");
    adminSection.classList.add("lg:col-span-2");

    this.loadSystemUsers();
  }

  initializeEventListeners() {
    // Personal Settings
    document.getElementById("updateEmailForm").addEventListener("submit", (e) => { e.preventDefault(); this.handleUpdateEmail(); });
    document.getElementById("changePasswordForm").addEventListener("submit", (e) => { e.preventDefault(); this.handleChangePassword(); });

    // Admin: Create User
    document.getElementById("createUserForm").addEventListener("submit", (e) => { e.preventDefault(); this.handleCreateUser(e); });

    // Admin: Search (Debounced)
    const searchInput = document.getElementById("userSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.loadSystemUsers(e.target.value);
            }, 400);
        });
    }

    // Admin: Delete Modal Buttons
    document.getElementById("cancelDeleteBtn").addEventListener("click", () => {
        document.getElementById("deleteConfirmModal").classList.add("hidden");
        this.userToDelete = null;
    });

    document.getElementById("confirmDeleteBtn").addEventListener("click", () => {
        if (this.userToDelete) {
            this.performDelete(this.userToDelete);
        }
    });
  }

  async loadSystemUsers(query = "") {
    try {
        // encodeURIComponent handles spaces correctly (%20)
        const url = query 
            ? `/api/auth/users?q=${encodeURIComponent(query)}` 
            : "/api/auth/users";

        const response = await fetch(url);
        const result = await response.json();
        if (result.success) {
            this.renderUserTable(result.users);
        }
    } catch (error) {
        console.error("Error loading users:", error);
    }
  }

  renderUserTable(users) {
    const tbody = document.getElementById("userTableBody");
    
    if (users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="px-4 py-4 text-center text-sm text-gray-500">No users found.</td></tr>`;
        return;
    }

    tbody.innerHTML = users.map(user => {
        const isSelf = user.id === this.currentUser.id;
        
        // Pass name to the delete handler for the modal text
        const deleteBtn = isSelf 
            ? `<span class="text-gray-400 text-xs italic">Current User</span>`
            : `<button onclick="accountManager.openDeleteModal(${user.id}, '${user.full_name}')" class="text-red-600 hover:text-red-900 text-sm font-medium bg-red-50 px-3 py-1 rounded border border-red-200 hover:bg-red-100 transition-colors">Delete</button>`;

        const roleColor = user.role_id === 1 ? 'bg-purple-100 text-purple-800' : 
                          (user.role_id === 2 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800');
        const roleName = user.role_id === 1 ? 'Admin' : (user.role_id === 2 ? 'Editor' : 'Viewer');

        return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${user.full_name}</div>
                    <div class="text-xs text-gray-500">${user.email}</div>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${roleColor}">
                        ${roleName}
                    </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right">
                    ${deleteBtn}
                </td>
            </tr>
        `;
    }).join('');
  }

  // --- DELETE MODAL LOGIC ---
  openDeleteModal(userId, userName) {
      this.userToDelete = userId;
      document.getElementById("deleteUserName").textContent = userName;
      document.getElementById("deleteConfirmModal").classList.remove("hidden");
  }

  async performDelete(userId) {
    const btn = document.getElementById("confirmDeleteBtn");
    btn.textContent = "Deleting...";
    btn.disabled = true;

    try {
        const response = await fetch(`/api/auth/delete-user/${userId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            // Refresh with current search term to keep table state
            const currentSearch = document.getElementById("userSearchInput").value;
            this.loadSystemUsers(currentSearch);
            document.getElementById("deleteConfirmModal").classList.add("hidden");
        } else {
            alert(result.message || "Failed to delete");
        }
    } catch (error) {
        alert("An error occurred");
    } finally {
        btn.textContent = "Delete";
        btn.disabled = false;
    }
  }

  // --- CREATE USER LOGIC ---
  async handleCreateUser(e) {
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const msgDiv = document.getElementById('createMessage');

    try {
        const response = await fetch('/api/auth/create-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            document.getElementById('createUserModal').classList.add('hidden');
            form.reset();
            const currentSearch = document.getElementById("userSearchInput").value;
            this.loadSystemUsers(currentSearch);
            // Optional: Show success toast
        } else {
            this.showMessage(msgDiv, result.message, "error");
        }
    } catch (error) {
        console.error('Error:', error);
    }
  }

  // --- PERSONAL SETTINGS LOGIC ---
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
  accountManager = new AccountManager();
});