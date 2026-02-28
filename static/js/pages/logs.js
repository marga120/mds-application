import { api } from "../api/client.js";
import { Notification } from "../components/notification.js";
import { getRoleName, getRoleBadgeClass } from "../utils/formatters.js";

class LogsManager {
  constructor() {
    this.logs = [];
    this.allUsers = new Map();
    this.currentPage = 1;
    this.limit = 10;
    this.maxLogs = 50;
    this.totalPages = 1;
    this.currentFilters = {};
    this.selectedExportUserIds = new Set();
    this.exportUsers = [];
    this.currentDisplayedUserIds = [];
    this.exportSortField = "name";
    this.exportSortDir = "asc";

    this.initializeEventListeners();
    this.loadInitialData();
  }

  initializeEventListeners() {
    document.getElementById("applyFilters").addEventListener("click", () => {
      this.applyFilters();
    });

    document.getElementById("clearFilters").addEventListener("click", () => {
      this.clearFilters();
    });

    document.getElementById("refreshLogs").addEventListener("click", () => {
      this.refreshLogs();
    });

    document.getElementById("prevPageBtn").addEventListener("click", () => {
      this.goToPreviousPage();
    });

    document.getElementById("nextPageBtn").addEventListener("click", () => {
      this.goToNextPage();
    });

    document.getElementById("userSearch").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.applyFilters();
      }
    });

    document
      .getElementById("exportStatusChangesBtn")
      .addEventListener("click", () => {
        this.showExportModal();
      });

    document
      .getElementById("closeExportModal")
      .addEventListener("click", () => {
        this.closeExportModal();
      });

    document.getElementById("cancelExportBtn").addEventListener("click", () => {
      this.closeExportModal();
    });

    document.getElementById("exportAllBtn").addEventListener("click", () => {
      this.exportStatusChanges(null);
    });

    document
      .getElementById("exportForAdminBtn")
      .addEventListener("click", () => {
        if (this.selectedExportUserIds.size > 0) {
          this.exportStatusChanges([...this.selectedExportUserIds]);
        }
      });

    document
      .getElementById("exportSelectAllCheckbox")
      .addEventListener("change", (e) => {
        this.toggleSelectAllExportUsers(e.target.checked);
      });

    document
      .getElementById("exportAdminSearch")
      .addEventListener("input", (e) => {
        this.filterExportUsers(e.target.value.trim());
      });

    document
      .getElementById("exportSortNameTh")
      .addEventListener("click", () => {
        this.sortExportUsers("name");
      });

    document
      .getElementById("exportSortEmailTh")
      .addEventListener("click", () => {
        this.sortExportUsers("email");
      });

    document
      .getElementById("exportSortRoleTh")
      .addEventListener("click", () => {
        this.sortExportUsers("role");
      });

    document
      .getElementById("exportStatusChangesModal")
      .addEventListener("click", (e) => {
        if (e.target === document.getElementById("exportStatusChangesModal")) {
          this.closeExportModal();
        }
      });
  }

  async loadInitialData() {
    await this.loadAllUsers();
    await this.loadLogs();
  }

  async loadAllUsers() {
    try {
      const result = await api.get("/api/logs", { limit: 1000 });
      if (result.success) {
        result.logs.forEach((log) => {
          if (log.user_id && !this.allUsers.has(log.user_id)) {
            this.allUsers.set(log.user_id, {
              id: log.user_id,
              name: log.user_name,
              email: log.user_email,
            });
          }
        });
      }
    } catch (error) {
      console.error("Error loading users:", error);
    }
  }

  async loadLogs() {
    try {
      const params = {
        limit: this.maxLogs,
        offset: 0,
        ...this.currentFilters,
      };

      const result = await api.get("/api/logs", params);

      if (result.success) {
        const allLogs = result.logs;
        this.totalPages = Math.ceil(allLogs.length / this.limit);

        const startIndex = (this.currentPage - 1) * this.limit;
        const endIndex = startIndex + this.limit;
        this.logs = allLogs.slice(startIndex, endIndex);

        this.renderLogs();
        this.updateLogsCount();
        this.updatePaginationControls();
      } else {
        this.showError(result.message);
      }
    } catch (error) {
      console.error("Error loading logs:", error);
      this.showError("Failed to load activity logs");
    }
  }

  updatePaginationControls() {
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");
    const pageInfo = document.getElementById("pageInfo");

    prevBtn.disabled = this.currentPage <= 1;
    nextBtn.disabled = this.currentPage >= this.totalPages;

    pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
  }

  goToPreviousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadLogs();
    }
  }

  goToNextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadLogs();
    }
  }

  renderLogs() {
    const container = document.getElementById("logsContainer");

    if (this.logs.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8">
          <p class="text-gray-500">No activity logs found</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.logs
      .map((log) => this.createLogCard(log))
      .join("");
  }

  createLogCard(log) {
    const timestamp = new Date(log.created_at).toLocaleString();

    if (log.action_type === "clear_all_data") {
      const totalRecords = parseInt(log.old_value) || 0;

      return `
        <div class="border border-gray-200 rounded-lg p-4 mb-3 hover:bg-gray-50 transition-colors">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <div>
                  <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    ${this.formatActionType(log.action_type)}
                  </span>
                </div>
              </div>

              <div class="text-sm text-gray-900 mb-1">
                <span class="font-medium">${log.user_name || "Unknown User"}</span>
                <span class="text-gray-600">(${log.user_role || "Unknown"})</span>
                performed <span class="font-medium">${this.formatActionType(log.action_type)}</span>
              </div>

              <div class="mt-2 text-sm text-gray-600">
                <span class="font-medium">Total records deleted:</span>
                <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-semibold">${totalRecords}</span>
              </div>
            </div>

            <div class="text-right text-xs text-gray-500">
              <div>${timestamp}</div>
            </div>
          </div>
        </div>
      `;
    }

    let changeDetails = "";
    if (log.old_value && log.new_value && log.old_value !== log.new_value) {
      changeDetails = `
        <div class="mt-2 text-sm text-gray-600">
          <span class="font-medium">Changed from:</span>
          <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">${log.old_value}</span>
          <span class="mx-2">→</span>
          <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">${log.new_value}</span>
        </div>
      `;
    }

    let targetInfo = "";
    if (log.target_entity && log.target_id) {
      targetInfo = `
        <div class="text-sm text-gray-600">
          <span class="font-medium">Target:</span> ${log.target_entity} (${log.target_id})
        </div>
      `;
    }

    return `
      <div class="border border-gray-200 rounded-lg p-4 mb-3 hover:bg-gray-50 transition-colors">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <div>
                <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  ${this.formatActionType(log.action_type)}
                </span>
              </div>
            </div>

            <div class="text-sm text-gray-900 mb-1">
              <span class="font-medium">${log.user_name}</span>
              <span class="text-gray-600">(${log.user_role})</span>
              performed <span class="font-medium">${this.formatActionType(log.action_type)}</span>
            </div>

            ${targetInfo}
            ${changeDetails}

            ${
              log.additional_metadata
                ? `
              <details class="mt-2">
                <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                  Additional Details
                </summary>
                <pre class="text-xs text-gray-600 mt-1 bg-gray-100 p-2 rounded overflow-auto">
                  ${JSON.stringify(log.additional_metadata, null, 2)}
                </pre>
              </details>
              `
                : ""
            }
          </div>

          <div class="text-right text-xs text-gray-500">
            <div>${timestamp}</div>
          </div>
        </div>
      </div>
    `;
  }

  formatActionType(actionType) {
    return actionType
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
  }

  updateLogsCount() {
    const countElement = document.getElementById("logsCount");
    countElement.textContent = `Showing ${this.logs.length} logs`;
  }

  applyFilters() {
    const actionFilter = document.getElementById("actionFilter").value;
    const userSearch = document.getElementById("userSearch").value.trim();

    this.currentFilters = {};
    if (actionFilter) this.currentFilters.action_type = actionFilter;
    if (userSearch) this.currentFilters.user_search = userSearch;

    this.currentPage = 1;
    this.loadLogs();
  }

  clearFilters() {
    document.getElementById("actionFilter").value = "";
    document.getElementById("userSearch").value = "";
    this.currentFilters = {};
    this.currentPage = 1;
    this.loadLogs();
  }

  refreshLogs() {
    this.allUsers.clear();
    this.loadInitialData();
  }

  showError(message) {
    const container = document.getElementById("logsContainer");
    container.innerHTML = `
      <div class="text-center py-8">
        <p class="text-red-600">Error: ${message}</p>
      </div>
    `;
  }

  showExportModal() {
    this.selectedExportUserIds = new Set();
    this.exportSortField = "name";
    this.exportSortDir = "asc";
    document.getElementById("exportAdminSearch").value = "";
    document.getElementById("selectedAdminText").classList.add("hidden");
    document.getElementById("exportForAdminBtn").disabled = true;
    document.getElementById("exportForAdminBtn").textContent =
      "Export for Selected";
    document.getElementById("exportSelectAllCheckbox").checked = false;
    document.getElementById("exportSelectAllCheckbox").indeterminate = false;
    this.resetExportSortIcons();

    const modal = document.getElementById("exportStatusChangesModal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");

    this.loadExportUsers();
  }

  closeExportModal() {
    const modal = document.getElementById("exportStatusChangesModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
  }

  async loadExportUsers() {
    document.getElementById("exportUsersTableBody").innerHTML = `
      <tr><td colspan="5" class="px-4 py-6 text-center text-sm text-gray-500">Loading users...</td></tr>
    `;

    try {
      const result = await api.get("/api/auth/users");
      if (result.success) {
        this.exportUsers = result.users;
        this.renderExportUsersTable(this.exportUsers);
      } else {
        document.getElementById("exportUsersTableBody").innerHTML = `
          <tr><td colspan="5" class="px-4 py-6 text-center text-sm text-red-500">Failed to load users</td></tr>
        `;
      }
    } catch (error) {
      console.error("Error loading users:", error);
      document.getElementById("exportUsersTableBody").innerHTML = `
        <tr><td colspan="5" class="px-4 py-6 text-center text-sm text-red-500">Failed to load users</td></tr>
      `;
    }
  }

  filterExportUsers(query) {
    if (!query) {
      this.renderExportUsersTable(this.exportUsers);
      return;
    }

    const q = query.toLowerCase();
    const filtered = this.exportUsers.filter(
      (u) =>
        u.full_name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        getRoleName(u.role_id).toLowerCase().includes(q),
    );
    this.renderExportUsersTable(filtered);
  }

  sortExportUsers(field) {
    if (this.exportSortField === field) {
      this.exportSortDir = this.exportSortDir === "asc" ? "desc" : "asc";
    } else {
      this.exportSortField = field;
      this.exportSortDir = "asc";
    }

    this.resetExportSortIcons();
    const icon = document.getElementById(
      `exportSort${field.charAt(0).toUpperCase() + field.slice(1)}Icon`,
    );
    if (icon) {
      icon.textContent = this.exportSortDir === "asc" ? "↑" : "↓";
      icon.classList.replace("text-gray-400", "text-blue-600");
    }

    const query = document.getElementById("exportAdminSearch").value.trim();
    const q = query.toLowerCase();
    const source = q
      ? this.exportUsers.filter(
          (u) =>
            u.full_name.toLowerCase().includes(q) ||
            u.email.toLowerCase().includes(q) ||
            getRoleName(u.role_id).toLowerCase().includes(q),
        )
      : [...this.exportUsers];

    source.sort((a, b) => {
      let aVal, bVal;
      if (field === "name") {
        aVal = a.full_name;
        bVal = b.full_name;
      } else if (field === "email") {
        aVal = a.email;
        bVal = b.email;
      } else {
        aVal = getRoleName(a.role_id);
        bVal = getRoleName(b.role_id);
      }

      return this.exportSortDir === "asc"
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    });

    this.renderExportUsersTable(source);
  }

  resetExportSortIcons() {
    ["Name", "Email", "Role"].forEach((f) => {
      const icon = document.getElementById(`exportSort${f}Icon`);
      if (icon) {
        icon.textContent = "⇅";
        icon.classList.replace("text-blue-600", "text-gray-400");
      }
    });
  }

  renderExportUsersTable(users) {
    const tbody = document.getElementById("exportUsersTableBody");
    this.currentDisplayedUserIds = users ? users.map((u) => u.id) : [];

    if (!users || users.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5" class="px-4 py-6 text-center text-sm text-gray-500">No users found</td></tr>
      `;
      this.updateSelectAllCheckbox();
      return;
    }

    tbody.innerHTML = users
      .map((user) => {
        const initials = user.full_name
          .split(" ")
          .map((n) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2);
        const isSelected = this.selectedExportUserIds.has(user.id);

        return `
          <tr
            class="hover:bg-blue-50 cursor-pointer transition-colors ${isSelected ? "bg-blue-50" : ""}"
            data-user-id="${user.id}"
          >
            <td class="px-4 py-3 w-8">
              <input type="checkbox" class="export-user-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded cursor-pointer"
                data-user-id="${user.id}" ${isSelected ? "checked" : ""}>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex items-center">
                <div class="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span class="text-blue-600 text-xs font-semibold">${initials}</span>
                </div>
                <div class="ml-3 text-sm font-medium text-gray-900">${user.full_name}</div>
              </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">${user.email}</td>
            <td class="px-4 py-3 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeClass(user.role_id)}">
                ${getRoleName(user.role_id)}
              </span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
              ${new Date(user.created_at).toLocaleDateString()}
            </td>
          </tr>
        `;
      })
      .join("");

    tbody.querySelectorAll("tr[data-user-id]").forEach((row) => {
      row.addEventListener("click", (e) => {
        if (e.target.type === "checkbox") return;
        const cb = row.querySelector(".export-user-checkbox");
        cb.checked = !cb.checked;
        this.toggleExportAdmin(parseInt(row.dataset.userId), cb.checked);
      });
    });

    tbody.querySelectorAll(".export-user-checkbox").forEach((cb) => {
      cb.addEventListener("change", (e) => {
        e.stopPropagation();
        this.toggleExportAdmin(parseInt(cb.dataset.userId), cb.checked);
      });
    });

    this.updateSelectAllCheckbox();
  }

  toggleExportAdmin(userId, checked) {
    if (checked) {
      this.selectedExportUserIds.add(userId);
    } else {
      this.selectedExportUserIds.delete(userId);
    }

    const row = document.querySelector(`tr[data-user-id="${userId}"]`);
    if (row) {
      row.classList.toggle("bg-blue-50", checked);
    }

    this.updateSelectAllCheckbox();
    this.updateExportSelectionUI();
  }

  toggleSelectAllExportUsers(checked) {
    this.currentDisplayedUserIds.forEach((id) => {
      if (checked) {
        this.selectedExportUserIds.add(id);
      } else {
        this.selectedExportUserIds.delete(id);
      }
      const row = document.querySelector(`tr[data-user-id="${id}"]`);
      if (row) {
        row.classList.toggle("bg-blue-50", checked);
        const cb = row.querySelector(".export-user-checkbox");
        if (cb) cb.checked = checked;
      }
    });
    this.updateExportSelectionUI();
  }

  updateSelectAllCheckbox() {
    const selectAll = document.getElementById("exportSelectAllCheckbox");
    if (!selectAll || this.currentDisplayedUserIds.length === 0) return;

    const selectedCount = this.currentDisplayedUserIds.filter((id) =>
      this.selectedExportUserIds.has(id),
    ).length;

    selectAll.checked = selectedCount === this.currentDisplayedUserIds.length;
    selectAll.indeterminate =
      selectedCount > 0 && selectedCount < this.currentDisplayedUserIds.length;
  }

  updateExportSelectionUI() {
    const count = this.selectedExportUserIds.size;
    const btn = document.getElementById("exportForAdminBtn");
    const text = document.getElementById("selectedAdminText");

    if (count === 0) {
      btn.disabled = true;
      btn.textContent = "Export for Selected";
      text.classList.add("hidden");
    } else {
      btn.disabled = false;
      btn.textContent = `Export for Selected (${count})`;
      text.textContent = `${count} admin${count !== 1 ? "s" : ""} selected`;
      text.classList.remove("hidden");
    }
  }

  exportStatusChanges(userIds) {
    const url =
      userIds && userIds.length > 0
        ? `/api/logs/export/status-changes?user_ids=${userIds.join(",")}`
        : "/api/logs/export/status-changes";

    const link = document.createElement("a");
    link.href = url;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    this.closeExportModal();
  }
}

new LogsManager();
