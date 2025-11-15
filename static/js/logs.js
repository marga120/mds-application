/**
 * LOGS MANAGER
 * 
 * This file manages the system activity logs interface for Admin users.
 * It handles loading, filtering, pagination, and display of system activity logs
 * including user actions, status changes, and audit trail information.
 */

class LogsManager {
  constructor() {
    this.logs = [];
    this.allUsers = new Map(); // Cache all users here
    this.currentPage = 1;
    this.limit = 10; // Show logs per page
    this.maxLogs = 50; // Maximum logs total (also might need to change in logs.py)
    this.totalPages = 1;
    this.currentFilters = {};

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

    // Add search on Enter key
    document.getElementById("userSearch").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.applyFilters();
      }
    });
  }

  async loadInitialData() {
    // First load all logs without filters to get all users
    await this.loadAllUsers();
    // Then load the actual logs for display
    await this.loadLogs();
  }

  async loadAllUsers() {
    try {
      // Load logs without any filters to get all users
      const response = await fetch(`/api/logs?limit=1000`); // Get a large number to capture all users
      const result = await response.json();

      if (result.success) {
        // Cache all unique users
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
      const offset = (this.currentPage - 1) * this.limit;
      const params = new URLSearchParams({
        limit: this.maxLogs, // Get all logs first
        offset: 0,
        ...this.currentFilters,
      });

      const response = await fetch(`/api/logs?${params}`);
      const result = await response.json();

      if (result.success) {
        // Calculate pagination based on all logs
        const allLogs = result.logs;
        this.totalPages = Math.ceil(allLogs.length / this.limit);

        // Get logs for current page
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

    const logsHtml = this.logs.map((log) => this.createLogCard(log)).join("");
    container.innerHTML = logsHtml;
  }

  createLogCard(log) {
    const timestamp = new Date(log.created_at).toLocaleString();

    // Special handling for clear_all_data action
    if (log.action_type === "clear_all_data") {
      const metadata = log.additional_metadata || {};
      const recordsDeleted = metadata.records_deleted || {};
      
      // Total records deleted = just the number of applicants
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
                <span class="font-medium">${log.user_name || 'Unknown User'}</span>
                <span class="text-gray-600">(${log.user_role || 'Unknown'})</span>
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
              performed <span class="font-medium">${this.formatActionType(
                log.action_type
              )}</span>
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

    this.currentPage = 1; // Reset to first page when applying filters
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
    // Refresh both users and logs
    this.allUsers.clear();
    this.loadInitialData();
  }

  loadMoreLogs() {
    this.offset += this.limit;
    this.loadLogs(false);
  }

  showError(message) {
    const container = document.getElementById("logsContainer");
    container.innerHTML = `
      <div class="text-center py-8">
        <p class="text-red-600">Error: ${message}</p>
      </div>
    `;
  }
}
