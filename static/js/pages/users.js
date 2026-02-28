/**
 * pages/users.js
 * User management page controller. Admin only.
 * Uses: AuthService, Notification, formatters, validators
 */
import { authService } from "../services/auth-service.js";
import { Notification } from "../components/notification.js";
import {
  getRoleName,
  getRoleBadgeClass,
  formatDate,
} from "../utils/formatters.js";
import { validateEmail, validatePassword } from "../utils/validators.js";

class UsersManager {
  constructor() {
    this._loggedInUserId = null;
    this._currentUserId = null;
    this._currentUserData = null;
    this._usersCache = [];
    this._selectedUsers = new Set();
    this._searchTimeout = null;
    this._sortField = null;
    this._sortDir = "asc";

    this._init();
  }

  async _init() {
    await this._loadCurrentUser();
    this._bindEvents();
    await this._loadUsers();
  }

  async _loadCurrentUser() {
    try {
      const result = await authService.getCurrentUser();
      if (result.success && result.user) this._loggedInUserId = result.user.id;
    } catch (err) {
      console.error("Error loading current user:", err);
    }
  }

  _bindEvents() {
    document
      .getElementById("createUserBtn")
      ?.addEventListener("click", () => this._showUserModal());
    document
      .getElementById("closeModal")
      ?.addEventListener("click", () => this._hideUserModal());
    document
      .getElementById("cancelBtn")
      ?.addEventListener("click", () => this._hideUserModal());
    document.getElementById("userForm")?.addEventListener("submit", (e) => {
      e.preventDefault();
      this._handleSaveUser();
    });

    document
      .getElementById("cancelDeleteBtn")
      ?.addEventListener("click", () => this._hideDeleteModal());
    document
      .getElementById("confirmDeleteBtn")
      ?.addEventListener("click", () => this._handleDeleteUser());
    document
      .getElementById("deleteSelectedBtn")
      ?.addEventListener("click", () => this._showBulkDeleteModal());
    document
      .getElementById("selectAllUsers")
      ?.addEventListener("change", (e) =>
        this._handleSelectAll(e.target.checked),
      );

    const searchInput = document.getElementById("userSearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        clearTimeout(this._searchTimeout);
        this._searchTimeout = setTimeout(
          () => this._filterUsers(e.target.value),
          300,
        );
      });
    }
  }

  async _loadUsers() {
    try {
      const result = await authService.getUsers();
      if (result.success) {
        this._usersCache = result.users || [];
        this._displayUsers(this._usersCache);
      } else {
        Notification.error(result.message || "Failed to load users.");
      }
    } catch (err) {
      Notification.error("Failed to load users.");
    }
  }

  _filterUsers(query) {
    if (!query?.trim()) {
      this._displayUsers(this._usersCache);
      return;
    }
    const lq = query.toLowerCase();
    this._displayUsers(
      this._usersCache.filter(
        (u) =>
          u.full_name.toLowerCase().includes(lq) ||
          u.email.toLowerCase().includes(lq) ||
          getRoleName(u.role_id).toLowerCase().includes(lq),
      ),
    );
  }

  toggleSort(field) {
    this._sortDir =
      this._sortField === field && this._sortDir === "asc" ? "desc" : "asc";
    this._sortField = field;
    this._updateSortIndicators();
    const query = document.getElementById("userSearchInput")?.value ?? "";
    this._filterUsers(query);
  }

  _updateSortIndicators() {
    ["name", "email", "role"].forEach((f) => {
      const icon = document.getElementById(
        `sort${f.charAt(0).toUpperCase() + f.slice(1)}Icon`,
      );
      if (!icon) return;
      if (this._sortField === f) {
        icon.textContent = this._sortDir === "asc" ? "↑" : "↓";
        icon.classList.add("text-blue-600");
      } else {
        icon.textContent = "⇅";
        icon.classList.remove("text-blue-600");
      }
    });
  }

  _displayUsers(users) {
    const tbody = document.getElementById("usersTableBody");
    if (!users?.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No users found</td></tr>`;
      return;
    }

    let sorted = [...users];
    if (this._sortField) {
      sorted.sort((a, b) => {
        let av, bv;
        if (this._sortField === "name") {
          av = a.full_name.toLowerCase();
          bv = b.full_name.toLowerCase();
        } else if (this._sortField === "email") {
          av = a.email.toLowerCase();
          bv = b.email.toLowerCase();
        } else if (this._sortField === "role") {
          av = getRoleName(a.role_id);
          bv = getRoleName(b.role_id);
        } else return 0;
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return this._sortDir === "asc" ? cmp : -cmp;
      });
    }

    tbody.innerHTML = sorted
      .map((u) => {
        const isSelf = u.id === this._loggedInUserId;
        const initials = this._initials(u.full_name);
        const badgeClass = getRoleBadgeClass(u.role_id);
        const roleName = getRoleName(u.role_id);
        const selfClass = isSelf ? "opacity-50 cursor-not-allowed" : "";
        return `
        <tr class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <input type="checkbox"
              class="user-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 ${isSelf ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}"
              data-user-id="${u.id}"
              ${isSelf ? "disabled" : ""}
              ${this._selectedUsers.has(u.id) ? "checked" : ""}
              onchange="window.usersManager.handleUserSelection(${u.id}, this.checked)">
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span class="text-blue-600 font-semibold">${initials}</span>
              </div>
              <div class="ml-4">
                <div class="text-sm font-medium text-gray-900">${u.full_name}</div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${u.email}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${badgeClass}">
              ${roleName}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${u.created_at ? new Date(u.created_at).toLocaleDateString() : ""}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <button onclick="window.usersManager.editUser(${u.id})"
              class="text-blue-600 hover:text-blue-900 mr-3 ${selfClass}"
              ${isSelf ? "disabled" : ""}>Edit</button>
            <button onclick="window.usersManager.showDeleteModal(${u.id})"
              class="text-red-600 hover:text-red-900 ${selfClass}"
              ${isSelf ? "disabled" : ""}>Delete</button>
          </td>
        </tr>`;
      })
      .join("");

    this._updateSelectAllCheckbox();
  }

  _initials(fullName) {
    const parts = fullName.split(" ");
    return parts.length >= 2
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : (fullName[0]?.toUpperCase() ?? "?");
  }

  _showUserModal(userId = null) {
    this._currentUserId = userId;
    const modal = document.getElementById("userModal");
    const title = document.getElementById("modalTitle");
    const passwordLabel = document
      .getElementById("passwordFields")
      ?.querySelector("label");
    const userInfoDisplay = document.getElementById("userInfoDisplay");
    const editableUserFields = document.getElementById("editableUserFields");

    if (userId) {
      title.textContent = "Edit User";
      if (passwordLabel)
        passwordLabel.textContent = "Password (leave empty to keep current)";
      document.getElementById("userPassword")?.removeAttribute("required");
      ["firstName", "lastName", "userEmail"].forEach((id) =>
        document.getElementById(id)?.removeAttribute("required"),
      );
      userInfoDisplay?.classList.remove("hidden");
      editableUserFields?.classList.add("hidden");
      this._loadUserData(userId);
    } else {
      title.textContent = "Create User";
      if (passwordLabel) passwordLabel.textContent = "Password";
      document
        .getElementById("userPassword")
        ?.setAttribute("required", "required");
      ["firstName", "lastName", "userEmail"].forEach((id) =>
        document.getElementById(id)?.setAttribute("required", "required"),
      );
      userInfoDisplay?.classList.add("hidden");
      editableUserFields?.classList.remove("hidden");
      document.getElementById("userForm")?.reset();
    }

    document.getElementById("modalMessage")?.classList.add("hidden");
    modal?.classList.remove("hidden");
  }

  _hideUserModal() {
    document.getElementById("userModal")?.classList.add("hidden");
    document.getElementById("userForm")?.reset();
    this._currentUserId = null;
    const saveBtn = document.getElementById("saveUserBtn");
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save User";
    }
  }

  async _loadUserData(userId) {
    try {
      const result = await authService.getUserById(userId);
      if (result.success) {
        this._currentUserData = result.user;
        const fullName =
          result.user.full_name ||
          `${result.user.first_name} ${result.user.last_name}`;
        const el = (id) => document.getElementById(id);
        if (el("displayFullName")) el("displayFullName").textContent = fullName;
        if (el("displayEmail"))
          el("displayEmail").textContent = result.user.email;
        if (el("userRole")) el("userRole").value = result.user.role_user_id;
      }
    } catch {
      this._showModalMessage("Failed to load user data.", "error");
    }
  }

  async _handleSaveUser() {
    const password = document.getElementById("userPassword")?.value || "";
    const roleId = parseInt(document.getElementById("userRole")?.value);
    const saveBtn = document.getElementById("saveUserBtn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      let result;
      if (this._currentUserId) {
        // Edit mode
        const emailCheck = validateEmail(this._currentUserData.email);
        const body = {
          first_name: this._currentUserData.first_name,
          last_name: this._currentUserData.last_name,
          email: this._currentUserData.email,
          role_user_id: roleId,
          ...(password ? { password } : {}),
        };
        result = await authService.updateUser(this._currentUserId, body);
      } else {
        // Create mode
        const firstName =
          document.getElementById("firstName")?.value.trim() || "";
        const lastName =
          document.getElementById("lastName")?.value.trim() || "";
        const email = document.getElementById("userEmail")?.value.trim() || "";

        const emailCheck = validateEmail(email);
        if (!emailCheck.valid) {
          this._showModalMessage(emailCheck.message, "error");
          saveBtn.disabled = false;
          saveBtn.textContent = "Save User";
          return;
        }
        const pwCheck = validatePassword(password);
        if (!pwCheck.valid) {
          this._showModalMessage(pwCheck.message, "error");
          saveBtn.disabled = false;
          saveBtn.textContent = "Save User";
          return;
        }

        result = await authService.createUser({
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          role_user_id: roleId,
        });
      }

      if (result.success) {
        this._showModalMessage(
          this._currentUserId
            ? "User updated successfully."
            : "User created successfully.",
          "success",
        );
        setTimeout(() => {
          this._hideUserModal();
          this._loadUsers();
        }, 1500);
      } else {
        this._showModalMessage(result.message, "error");
        saveBtn.disabled = false;
        saveBtn.textContent = "Save User";
      }
    } catch (err) {
      this._showModalMessage(err.message || "An error occurred.", "error");
      saveBtn.disabled = false;
      saveBtn.textContent = "Save User";
    }
  }

  editUser(userId) {
    this._showUserModal(userId);
  }

  showDeleteModal(userId) {
    this._currentUserId = userId;
    const confirmText = document.getElementById("deleteConfirmText");
    if (confirmText)
      confirmText.textContent =
        "Are you sure you want to delete this user? This action cannot be undone.";
    document.getElementById("deleteMessage")?.classList.add("hidden");
    document.getElementById("deleteModal")?.classList.remove("hidden");
  }

  _hideDeleteModal() {
    document.getElementById("deleteModal")?.classList.add("hidden");
    this._currentUserId = null;
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Yes, Delete";
    }
    document.getElementById("deleteMessage")?.classList.add("hidden");
    this._updateSelectionUI();
  }

  _showBulkDeleteModal() {
    if (this._selectedUsers.size === 0) return;
    const count = this._selectedUsers.size;
    const confirmText = document.getElementById("deleteConfirmText");
    if (confirmText)
      confirmText.textContent = `Are you sure you want to delete ${count} user${count > 1 ? "s" : ""}? This action cannot be undone.`;
    this._currentUserId = null;
    document.getElementById("deleteMessage")?.classList.add("hidden");
    document.getElementById("deleteModal")?.classList.remove("hidden");
  }

  async _handleDeleteUser() {
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";

    try {
      let result;
      if (this._currentUserId === null && this._selectedUsers.size > 0) {
        // Bulk delete
        const ids = Array.from(this._selectedUsers);
        result = await authService.deleteUsers(ids);
        if (result.success) {
          this._showDeleteMessage(
            `Deleted ${ids.length} user${ids.length > 1 ? "s" : ""}.`,
            "success",
          );
          this._selectedUsers.clear();
        }
      } else {
        // Single delete
        result = await authService.deleteUser(this._currentUserId);
        if (result.success)
          this._showDeleteMessage("User deleted successfully.", "success");
      }

      if (result.success) {
        setTimeout(() => {
          this._hideDeleteModal();
          this._loadUsers();
        }, 1500);
      } else {
        this._showDeleteMessage(result.message, "error");
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Yes, Delete";
      }
    } catch (err) {
      this._showDeleteMessage(err.message || "An error occurred.", "error");
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Yes, Delete";
    }
  }

  // ---- Selection management ----

  handleUserSelection(userId, isChecked) {
    if (isChecked) this._selectedUsers.add(userId);
    else this._selectedUsers.delete(userId);
    this._updateSelectionUI();
  }

  _handleSelectAll(isChecked) {
    if (isChecked) {
      this._usersCache.forEach((u) => {
        if (u.id !== this._loggedInUserId) this._selectedUsers.add(u.id);
      });
    } else {
      this._selectedUsers.clear();
    }
    this._updateSelectionUI();
    const query = document.getElementById("userSearchInput")?.value ?? "";
    this._filterUsers(query);
  }

  _updateSelectAllCheckbox() {
    const cb = document.getElementById("selectAllUsers");
    if (!cb) return;
    const selectable = this._usersCache.filter(
      (u) => u.id !== this._loggedInUserId,
    );
    const allSelected =
      selectable.length > 0 &&
      selectable.every((u) => this._selectedUsers.has(u.id));
    cb.checked = allSelected;
    cb.indeterminate = !allSelected && this._selectedUsers.size > 0;
  }

  _updateSelectionUI() {
    const deleteBtn = document.getElementById("deleteSelectedBtn");
    const countSpan = document.getElementById("selectedCount");
    if (this._selectedUsers.size > 0) {
      deleteBtn?.classList.remove("hidden");
      if (countSpan) countSpan.textContent = this._selectedUsers.size;
    } else {
      deleteBtn?.classList.add("hidden");
    }
    this._updateSelectAllCheckbox();
  }

  // ---- Message helpers ----

  _showModalMessage(message, type) {
    const el = document.getElementById("modalMessage");
    if (!el) return;
    el.textContent = message;
    el.className = `p-3 rounded-md ${type === "success" ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"}`;
    el.classList.remove("hidden");
  }

  _showDeleteMessage(message, type) {
    const el = document.getElementById("deleteMessage");
    if (!el) return;
    el.textContent = message;
    el.className = `p-3 rounded-md mb-4 ${type === "success" ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"}`;
    el.classList.remove("hidden");
  }
}

let usersManager;
document.addEventListener("DOMContentLoaded", () => {
  if (typeof AuthManager !== "undefined") new AuthManager();
  usersManager = new UsersManager();
  window.usersManager = usersManager;
});
