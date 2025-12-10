/**
 * USERS MANAGER
 *
 * Handles user management including creating, editing, deleting users,
 * and changing user roles. Admin-only functionality.
 */

class UsersManager {
  constructor() {
    this.currentUserId = null;
    this.loggedInUserId = null;
    this.usersCache = [];
    this.selectedUsers = new Set(); // Track selected user IDs
    this.searchTimeout = null;
    this.sortField = null; // 'name', 'email', or 'role'
    this.sortDir = 'asc'; // 'asc' or 'desc'
    this.loadCurrentUser();
    this.loadUsers();
    this.initializeEventListeners();
  }

  async loadCurrentUser() {
    try {
      const response = await fetch('/api/auth/user');
      const result = await response.json();
      if (result.success && result.user) {
        this.loggedInUserId = result.user.id;
      }
    } catch (error) {
      console.error('Error loading current user:', error);
    }
  }

  initializeEventListeners() {
    // Create User Button
    document.getElementById("createUserBtn").addEventListener("click", () => {
      this.showUserModal();
    });

    // Modal Close Buttons
    document.getElementById("closeModal").addEventListener("click", () => {
      this.hideUserModal();
    });

    document.getElementById("cancelBtn").addEventListener("click", () => {
      this.hideUserModal();
    });

    // User Form Submit
    document.getElementById("userForm").addEventListener("submit", (e) => {
      e.preventDefault();
      this.handleSaveUser();
    });

    // Delete Modal Buttons
    document.getElementById("cancelDeleteBtn").addEventListener("click", () => {
      this.hideDeleteModal();
    });

    document.getElementById("confirmDeleteBtn").addEventListener("click", () => {
      this.handleDeleteUser();
    });

    // Delete Selected Button
    document.getElementById("deleteSelectedBtn").addEventListener("click", () => {
      this.showBulkDeleteModal();
    });

    // Select All Checkbox
    document.getElementById("selectAllUsers").addEventListener("change", (e) => {
      this.handleSelectAll(e.target.checked);
    });

    // Search Input (Debounced)
    const searchInput = document.getElementById("userSearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
          this.filterUsers(e.target.value);
        }, 300);
      });
    }
  }

  async loadUsers(query = "") {
    try {
      const url = query
        ? `/api/auth/users?q=${encodeURIComponent(query)}`
        : "/api/auth/users";

      const response = await fetch(url);
      const result = await response.json();

      if (result.success) {
        this.usersCache = result.users || [];
        this.displayUsers(this.usersCache);
      } else {
        this.showPageMessage(result.message, "error");
      }
    } catch (error) {
      this.showPageMessage("Failed to load users", "error");
    }
  }

  filterUsers(query) {
    if (!query.trim()) {
      this.displayUsers(this.usersCache);
      return;
    }

    const lowerQuery = query.toLowerCase();
    const filtered = this.usersCache.filter(user => {
      return (
        user.full_name.toLowerCase().includes(lowerQuery) ||
        user.email.toLowerCase().includes(lowerQuery) ||
        this.getRoleName(user.role_id).toLowerCase().includes(lowerQuery)
      );
    });

    this.displayUsers(filtered);
  }

  toggleSort(field) {
    if (this.sortField === field) {
      // Toggle direction
      this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortField = field;
      this.sortDir = 'asc';
    }

    // Update UI indicators
    this.updateSortIndicators();

    // Re-render with current search query
    const searchInput = document.getElementById("userSearchInput");
    const query = searchInput ? searchInput.value : "";
    this.filterUsers(query);
  }

  updateSortIndicators() {
    const indicators = {
      name: document.getElementById('sortNameIcon'),
      email: document.getElementById('sortEmailIcon'),
      role: document.getElementById('sortRoleIcon')
    };

    Object.keys(indicators).forEach(field => {
      const icon = indicators[field];
      if (icon) {
        if (this.sortField === field) {
          icon.textContent = this.sortDir === 'asc' ? '↑' : '↓';
          icon.classList.add('text-blue-600');
        } else {
          icon.textContent = '⇅';
          icon.classList.remove('text-blue-600');
        }
      }
    });
  }

  displayUsers(users) {
    const tbody = document.getElementById("usersTableBody");

    if (!users || users.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-4 text-center text-gray-500">
            No users found
          </td>
        </tr>
      `;
      return;
    }

    // Sort users if a sort field is selected
    let sortedUsers = [...users];
    if (this.sortField) {
      sortedUsers.sort((a, b) => {
        let aVal, bVal;

        switch (this.sortField) {
          case 'name':
            aVal = a.full_name.toLowerCase();
            bVal = b.full_name.toLowerCase();
            break;
          case 'email':
            aVal = a.email.toLowerCase();
            bVal = b.email.toLowerCase();
            break;
          case 'role':
            aVal = this.getRoleName(a.role_id);
            bVal = this.getRoleName(b.role_id);
            break;
          default:
            return 0;
        }

        const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        return this.sortDir === 'asc' ? comparison : -comparison;
      });
    }
    tbody.innerHTML = sortedUsers.map(user => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 whitespace-nowrap">
          <input type="checkbox"
            class="user-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 ${user.id === this.loggedInUserId ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
            data-user-id="${user.id}"
            ${user.id === this.loggedInUserId ? 'disabled' : ''}
            ${this.selectedUsers.has(user.id) ? 'checked' : ''}
            onchange="window.usersManager.handleUserSelection(${user.id}, this.checked)">
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center">
            <div class="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <span class="text-blue-600 font-semibold">${this.getInitialsFromFullName(user.full_name)}</span>
            </div>
            <div class="ml-4">
              <div class="text-sm font-medium text-gray-900">${user.full_name}</div>
            </div>
          </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${user.email}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${this.getRoleBadgeColor(user.role_id)}">
            ${this.getRoleName(user.role_id)}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${new Date(user.created_at).toLocaleDateString()}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
          <button onclick="window.usersManager.editUser(${user.id})"
            class="text-blue-600 hover:text-blue-900 mr-3 ${user.id === this.loggedInUserId ? 'opacity-50 cursor-not-allowed' : ''}"
            ${user.id === this.loggedInUserId ? 'disabled' : ''}>
            Edit
          </button>
          <button onclick="window.usersManager.showDeleteModal(${user.id})"
            class="text-red-600 hover:text-red-900 ${user.id === this.loggedInUserId ? 'opacity-50 cursor-not-allowed' : ''}"
            ${user.id === this.loggedInUserId ? 'disabled' : ''}>
            Delete
          </button>
        </td>
      </tr>
    `).join('');

    // Update the select all checkbox state
    this.updateSelectAllCheckbox();
  }

  getInitialsFromFullName(fullName) {
    const names = fullName.split(' ');
    if (names.length >= 2) {
      return `${names[0].charAt(0)}${names[names.length - 1].charAt(0)}`.toUpperCase();
    }
    return fullName.charAt(0).toUpperCase();
  }

  getRoleName(roleId) {
    switch (roleId) {
      case 1:
        return 'Admin';
      case 2:
        return 'Faculty';
      case 3:
        return 'Viewer';
      default:
        return 'Unknown';
    }
  }

  getRoleBadgeColor(roleId) {
    switch (roleId) {
      case 1: // Admin
        return 'bg-purple-100 text-purple-800';
      case 2: // Faculty
        return 'bg-blue-100 text-blue-800';
      case 3: // Viewer
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  showUserModal(userId = null) {
    const modal = document.getElementById("userModal");
    const title = document.getElementById("modalTitle");
    const passwordField = document.getElementById("passwordFields");
    const userInfoDisplay = document.getElementById("userInfoDisplay");
    const editableUserFields = document.getElementById("editableUserFields");

    this.currentUserId = userId;

    if (userId) {
      // Edit mode - show only role and password
      title.textContent = "Edit User";
      passwordField.querySelector('label').textContent = "Password (leave empty to keep current)";
      document.getElementById("userPassword").removeAttribute('required');

      // Remove required attributes from hidden fields
      document.getElementById("firstName").removeAttribute('required');
      document.getElementById("lastName").removeAttribute('required');
      document.getElementById("userEmail").removeAttribute('required');

      // Show user info display, hide editable name/email fields
      userInfoDisplay.classList.remove("hidden");
      editableUserFields.classList.add("hidden");

      this.loadUserData(userId);
    } else {
      // Create mode - show all fields
      title.textContent = "Create User";
      passwordField.querySelector('label').textContent = "Password";
      document.getElementById("userPassword").setAttribute('required', 'required');

      // Add required attributes back for create mode
      document.getElementById("firstName").setAttribute('required', 'required');
      document.getElementById("lastName").setAttribute('required', 'required');
      document.getElementById("userEmail").setAttribute('required', 'required');

      // Hide user info display, show editable name/email fields
      userInfoDisplay.classList.add("hidden");
      editableUserFields.classList.remove("hidden");

      document.getElementById("userForm").reset();
    }

    document.getElementById("modalMessage").classList.add("hidden");
    modal.classList.remove("hidden");
  }

  hideUserModal() {
    document.getElementById("userModal").classList.add("hidden");
    document.getElementById("userForm").reset();
    this.currentUserId = null;

    // Reset button state
    const saveBtn = document.getElementById("saveUserBtn");
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save User";
    }
  }

  async loadUserData(userId) {
    try {
      const response = await fetch(`/api/auth/user/${userId}`);
      const result = await response.json();

      if (result.success) {
        // Store the user data for later use
        this.currentUserData = result.user;

        // Create full name from first_name and last_name if full_name doesn't exist
        const fullName = result.user.full_name || `${result.user.first_name} ${result.user.last_name}`;

        // Display user info in read-only section
        document.getElementById("displayFullName").textContent = fullName;
        document.getElementById("displayEmail").textContent = result.user.email;

        // Set role (editable)
        document.getElementById("userRole").value = result.user.role_user_id;
      }
    } catch (error) {
      this.showModalMessage("Failed to load user data", "error");
    }
  }

  async handleSaveUser() {
    const password = document.getElementById("userPassword").value;
    const roleId = parseInt(document.getElementById("userRole").value);

    const saveBtn = document.getElementById("saveUserBtn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const url = this.currentUserId
        ? `/api/auth/user/${this.currentUserId}`
        : "/api/auth/register";

      const method = this.currentUserId ? "PUT" : "POST";

      let body;

      if (this.currentUserId) {
        // Edit mode - send all fields but use existing data for name/email
        body = {
          first_name: this.currentUserData.first_name,
          last_name: this.currentUserData.last_name,
          email: this.currentUserData.email,
          role_user_id: roleId
        };

        // Only include password if it's provided
        if (password) {
          body.password = password;
        }
      } else {
        // Create mode - send all fields from form
        const firstName = document.getElementById("firstName").value.trim();
        const lastName = document.getElementById("lastName").value.trim();
        const email = document.getElementById("userEmail").value.trim();

        body = {
          first_name: firstName,
          last_name: lastName,
          email: email,
          role_user_id: roleId
        };

        // Password is required for create
        if (password) {
          body.password = password;
        }
      }

      const response = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      });

      const result = await response.json();

      if (result.success) {
        this.showModalMessage(
          this.currentUserId ? "User updated successfully" : "User created successfully",
          "success"
        );
        setTimeout(() => {
          this.hideUserModal();
          this.loadUsers();
        }, 1500);
      } else {
        this.showModalMessage(result.message, "error");
        saveBtn.disabled = false;
        saveBtn.textContent = "Save User";
      }
    } catch (error) {
      this.showModalMessage("An error occurred while saving the user", "error");
      saveBtn.disabled = false;
      saveBtn.textContent = "Save User";
    }
  }

  editUser(userId) {
    this.showUserModal(userId);
  }

  showDeleteModal(userId) {
    this.currentUserId = userId;
    const confirmText = document.getElementById("deleteConfirmText");
    confirmText.textContent = "Are you sure you want to delete this user? This action cannot be undone.";
    document.getElementById("deleteMessage").classList.add("hidden");
    document.getElementById("deleteModal").classList.remove("hidden");
  }

  hideDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
    this.currentUserId = null;

    // Reset button state
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Yes, Delete";
    }

    // Hide any messages
    document.getElementById("deleteMessage").classList.add("hidden");

    // Update UI to hide delete button if no selections
    this.updateSelectionUI();
  }

  async handleDeleteUser() {
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";

    try {
      const response = await fetch(`/api/auth/delete-user/${this.currentUserId}`, {
        method: "DELETE"
      });

      const result = await response.json();

      if (result.success) {
        this.showDeleteMessage("User deleted successfully", "success");
        setTimeout(() => {
          this.hideDeleteModal();
          this.loadUsers();
        }, 1500);
      } else {
        this.showDeleteMessage(result.message, "error");
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Yes, Delete";
      }
    } catch (error) {
      this.showDeleteMessage("An error occurred while deleting the user", "error");
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Yes, Delete";
    }
  }

  showPageMessage(message, type) {
    const messageDiv = document.getElementById("message");
    messageDiv.textContent = message;
    messageDiv.className = `mb-4 p-4 rounded-md ${
      type === "success"
        ? "bg-green-50 text-green-800 border border-green-200"
        : "bg-red-50 text-red-800 border border-red-200"
    }`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  showModalMessage(message, type) {
    const messageDiv = document.getElementById("modalMessage");
    messageDiv.textContent = message;
    messageDiv.className = `p-3 rounded-md ${
      type === "success"
        ? "bg-green-50 text-green-800 border border-green-200"
        : "bg-red-50 text-red-800 border border-red-200"
    }`;
    messageDiv.classList.remove("hidden");
  }

  showDeleteMessage(message, type) {
    const messageDiv = document.getElementById("deleteMessage");
    messageDiv.textContent = message;
    messageDiv.className = `p-3 rounded-md mb-4 ${
      type === "success"
        ? "bg-green-50 text-green-800 border border-green-200"
        : "bg-red-50 text-red-800 border border-red-200"
    }`;
    messageDiv.classList.remove("hidden");
  }

  // Selection Management
  handleUserSelection(userId, isChecked) {
    if (isChecked) {
      this.selectedUsers.add(userId);
    } else {
      this.selectedUsers.delete(userId);
    }
    this.updateSelectionUI();
  }

  handleSelectAll(isChecked) {
    if (isChecked) {
      // Select all users except the logged-in user
      this.usersCache.forEach(user => {
        if (user.id !== this.loggedInUserId) {
          this.selectedUsers.add(user.id);
        }
      });
    } else {
      this.selectedUsers.clear();
    }

    // Update the delete button visibility and selection count
    this.updateSelectionUI();

    // Re-render to update checkboxes
    const searchInput = document.getElementById("userSearchInput");
    const query = searchInput ? searchInput.value : "";
    this.filterUsers(query);
  }

  updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById("selectAllUsers");
    const selectableUsers = this.usersCache.filter(u => u.id !== this.loggedInUserId);
    const allSelected = selectableUsers.length > 0 &&
                       selectableUsers.every(u => this.selectedUsers.has(u.id));

    if (selectAllCheckbox) {
      selectAllCheckbox.checked = allSelected;
      selectAllCheckbox.indeterminate = !allSelected && this.selectedUsers.size > 0;
    }
  }

  updateSelectionUI() {
    const deleteBtn = document.getElementById("deleteSelectedBtn");
    const countSpan = document.getElementById("selectedCount");

    if (this.selectedUsers.size > 0) {
      deleteBtn.classList.remove("hidden");
      countSpan.textContent = this.selectedUsers.size;
    } else {
      deleteBtn.classList.add("hidden");
    }

    this.updateSelectAllCheckbox();
  }

  showBulkDeleteModal() {
    if (this.selectedUsers.size === 0) return;

    const count = this.selectedUsers.size;
    const confirmText = document.getElementById("deleteConfirmText");
    confirmText.textContent = `Are you sure you want to delete ${count} user${count > 1 ? 's' : ''}? This action cannot be undone.`;

    this.currentUserId = null; // Signal bulk delete
    document.getElementById("deleteMessage").classList.add("hidden");
    document.getElementById("deleteModal").classList.remove("hidden");
  }

  async handleDeleteUser() {
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";

    try {
      // Check if this is a bulk delete or single delete
      if (this.currentUserId === null && this.selectedUsers.size > 0) {
        // Bulk delete
        const userIds = Array.from(this.selectedUsers);
        const response = await fetch('/api/auth/delete-users', {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ user_ids: userIds })
        });

        const result = await response.json();

        if (result.success) {
          this.showDeleteMessage(`Successfully deleted ${userIds.length} user${userIds.length > 1 ? 's' : ''}`, "success");
          this.selectedUsers.clear();
          setTimeout(() => {
            this.hideDeleteModal();
            this.loadUsers();
          }, 1500);
        } else {
          this.showDeleteMessage(result.message, "error");
          confirmBtn.disabled = false;
          confirmBtn.textContent = "Yes, Delete";
        }
      } else {
        // Single delete
        const response = await fetch(`/api/auth/delete-user/${this.currentUserId}`, {
          method: "DELETE"
        });

        const result = await response.json();

        if (result.success) {
          this.showDeleteMessage("User deleted successfully", "success");
          setTimeout(() => {
            this.hideDeleteModal();
            this.loadUsers();
          }, 1500);
        } else {
          this.showDeleteMessage(result.message, "error");
          confirmBtn.disabled = false;
          confirmBtn.textContent = "Yes, Delete";
        }
      }
    } catch (error) {
      this.showDeleteMessage("An error occurred while deleting", "error");
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Yes, Delete";
    }
  }
}

// Initialize the users manager when the page loads
let usersManager;
document.addEventListener("DOMContentLoaded", () => {
  // Initialize AuthManager for header dropdowns
  new AuthManager();

  // Initialize UsersManager for user management functionality
  usersManager = new UsersManager();
  window.usersManager = usersManager;
});