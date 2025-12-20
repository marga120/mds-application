/**
 * Statistics page for admin use, shows applicant information
 * 
 * 
 * 
 * 
 */


class statisticsManager {
    constructor(){
        this.currentUserId = null;
        this.loggedInUserId = null;
        this.loadCurrentUser();
        this.loadUsers();
        this.initializeEventListeners();
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
}