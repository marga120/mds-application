class LogsManager {
  constructor() {
    this.logs = [];
    this.allUsers = new Map(); // Cache all users here
    this.offset = 0;
    this.limit = 50;
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

    document.getElementById("loadMoreBtn").addEventListener("click", () => {
      this.loadMoreLogs();
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

        // Populate the user filter dropdown once with all users
        this.populateUserFilter();
      }
    } catch (error) {
      console.error("Error loading users:", error);
    }
  }

  async loadLogs(reset = true) {
    if (reset) {
      this.offset = 0;
      this.logs = [];
    }

    try {
      const params = new URLSearchParams({
        limit: this.limit,
        offset: this.offset,
        ...this.currentFilters,
      });

      const response = await fetch(`/api/logs?${params}`);
      const result = await response.json();

      if (result.success) {
        if (reset) {
          this.logs = result.logs;
        } else {
          this.logs.push(...result.logs);
        }

        this.renderLogs();
        this.updateLogsCount();
        // Don't repopulate user filter here anymore

        // Show/hide load more button
        const loadMoreContainer = document.getElementById("loadMoreContainer");
        if (result.logs.length === this.limit) {
          loadMoreContainer.classList.remove("hidden");
        } else {
          loadMoreContainer.classList.add("hidden");
        }
      } else {
        this.showError(result.message);
      }
    } catch (error) {
      console.error("Error loading logs:", error);
      this.showError("Failed to load activity logs");
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
            <div class="mt-1">ID: ${log.id}</div>
          </div>
        </div>
      </div>
    `;
  }

  populateUserFilter() {
    const userFilter = document.getElementById("userFilter");

    // Clear existing options except "All Users"
    userFilter.innerHTML = '<option value="">All Users</option>';

    // Use cached users instead of current logs
    Array.from(this.allUsers.values()).forEach((user) => {
      const option = document.createElement("option");
      option.value = user.id;
      option.textContent = `${user.name} (${user.email})`;
      userFilter.appendChild(option);
    });
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
    const userFilter = document.getElementById("userFilter").value;

    this.currentFilters = {};
    if (actionFilter) this.currentFilters.action_type = actionFilter;
    if (userFilter) this.currentFilters.user_id = userFilter;

    this.loadLogs(true);
  }

  clearFilters() {
    document.getElementById("actionFilter").value = "";
    document.getElementById("userFilter").value = "";
    this.currentFilters = {};
    this.loadLogs(true);
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
