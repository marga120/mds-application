class AccountManager {
  constructor() {
    this.currentUser = null;
    this.searchTimeout = null;
    this.usersCache = [];
    this.sortField = null; // 'name' or 'role'
    this.sortDir = 'asc'; // 'asc' or 'desc'
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

    // Admin: Edit User
    const editUserForm = document.getElementById("editUserForm");
    if (editUserForm) {
        editUserForm.addEventListener("submit", (e) => { e.preventDefault(); this.handleEditUser(e); });
    }

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
            // cache users so we can sort client-side without re-fetching
            this.usersCache = result.users || [];
            this.renderUserTable();
        }
    } catch (error) {
        console.error("Error loading users:", error);
    }
  }

  renderUserTable(users) {
    const tbody = document.getElementById("userTableBody");
    // prefer explicit users param, otherwise use cached values
    let list = Array.isArray(users) ? users.slice() : this.usersCache.slice();

    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="px-4 py-4 text-center text-sm text-gray-500">No users found.</td></tr>`;
        return;
    }

    // client-side sorting
    if (this.sortField) {
        const dir = this.sortDir === 'asc' ? 1 : -1;
        if (this.sortField === 'name') {
            list.sort((a, b) => a.full_name.localeCompare(b.full_name) * dir);
        } else if (this.sortField === 'role') {
            // map role_id to readable order/name
            const roleName = (rid) => rid === 1 ? 'Admin' : (rid === 2 ? 'Editor' : 'Viewer');
            list.sort((a, b) => roleName(a.role_id).localeCompare(roleName(b.role_id)) * dir);
        }
    }

    tbody.innerHTML = list.map(user => {
        const isSelf = user.id === this.currentUser.id;
        
        // Pass name to the delete handler for the modal text
        const deleteBtn = isSelf 
            ? `<span class="text-gray-400 text-xs italic">Current User</span>`
            : `<button onclick="accountManager.openDeleteModal(${user.id}, '${user.full_name}')" class="text-red-600 hover:text-red-900 text-sm font-medium bg-red-50 px-3 py-1 rounded border border-red-200 hover:bg-red-100 transition-colors">Delete</button>`;
        const editBtn = isSelf
            ? `<span class="text-gray-400 text-xs italic">Current User</span>`
            : `<button onclick="accountManager.openEditModal(${user.id}, '${user.full_name}')" class="text-blue-600 hover:text-blue-900 text-sm font-medium bg-blue-50 px-3 py-1 rounded border border-blue-200 hover:bg-blue-100 transition-colors">Edit</a>`;
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
                <td class="px-4 py-3 whitespace-nowrap text-right">
                    ${editBtn}
                </td>
                
            </tr>
        `;
        }).join('');
  }

    toggleSort(field) {
        if (this.sortField === field) {
                // toggle direction
                this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
                this.sortField = field;
                this.sortDir = 'asc';
        }

        // update UI indicators
        const nameIcon = document.getElementById('sortNameIcon');
        const roleIcon = document.getElementById('sortRoleIcon');
        if (nameIcon) nameIcon.textContent = this.sortField === 'name' ? (this.sortDir === 'asc' ? '↑' : '↓') : '⇅';
        if (roleIcon) roleIcon.textContent = this.sortField === 'role' ? (this.sortDir === 'asc' ? '↑' : '↓') : '⇅';

        // re-render with new sort
        this.renderUserTable();
    }
  // --- EDIT MODAL LOGIC ---
  openEditModal(userId, userName) {
      this.userToEdit = userId;
      document.getElementById("editUserId").value = userId;
      document.getElementById("editEmail").value = "";
      document.getElementById("editPassword").value = "";
      document.getElementById("editMessage").classList.add("hidden");
      document.getElementById("editModal").classList.remove("hidden");
  }

  async handleEditUser(e) {
      const form = e.target;
      const userId = document.getElementById("editUserId").value;
      const email = document.getElementById("editEmail").value;
      const password = document.getElementById("editPassword").value;
      const msgDiv = document.getElementById("editMessage");

      if (!email && !password) {
          this.showMessage(msgDiv, "Please enter at least an email or new password", "error");
          return;
      }

      try {
          const body = { user_id: userId };
          if (email) body.email = email;
          if (password) body.password = password;

          const response = await fetch("/api/auth/edit-user", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body)
          });
          const result = await response.json();

          if (result.success) {
              document.getElementById("editModal").classList.add("hidden");
              const currentSearch = document.getElementById("userSearchInput").value;
              this.loadSystemUsers(currentSearch);
          } else {
              this.showMessage(msgDiv, result.message || "Failed to update user", "error");
          }
      } catch (error) {
          console.error("Error:", error);
          this.showMessage(msgDiv, "An error occurred", "error");
      }
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