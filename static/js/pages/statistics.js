/**
 * pages/statistics.js
 * Statistics page controller — ES module.
 * Uses: api/client.js, services/status-service.js
 */

import { api } from "../api/client.js";
import { statusService } from "../services/status-service.js";

class StatisticsManager {
  constructor() {
    this.applicants = [];
    this.statusOptions = [];
    this.historyData = [];
    this.isAdmin = false;
    this.activeTab = "stats";
    // Compare mode state
    this.compareMode = false;
    this.rangeMode = false;
    this.timelineMode = false;
    this.sessionsList = [];
    this.init();
  }

  async init() {
    await this.loadStatuses();
    this.populateStatusFilter();
    await this.loadApplicants();
    this.setupEventListeners();
    this.displayOverallStatistics();
    this.displayStatusBreakdown();
    this.displayStatusStatistics("");

    const userResult = await api.get("/api/auth/user");
    if (userResult?.user?.is_admin) {
      this.isAdmin = true;
      this.initTabs();
      this.initStatusHistory();
    }
    this.initCompare();
  }

  initTabs() {
    const historyTab = document.getElementById("tabChangeHistory");
    const bothTab = document.getElementById("tabBoth");
    if (historyTab) historyTab.classList.remove("hidden");
    if (bothTab) bothTab.classList.remove("hidden");

    document.querySelectorAll(".stats-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        this.switchTab(btn.dataset.tab);
      });
    });

    const saved = localStorage.getItem("mds_stats_tab");
    this.switchTab(saved || "stats");
  }

  switchTab(tab) {
    this.activeTab = tab;
    localStorage.setItem("mds_stats_tab", tab);

    document.querySelectorAll(".stats-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tab);
    });

    const statsSection = document.getElementById("statusStatsSection");
    const historySection = document.getElementById("statusHistorySection");

    if (tab === "stats") {
      if (statsSection) statsSection.classList.remove("hidden");
      if (historySection) historySection.classList.add("hidden");
    } else if (tab === "history") {
      if (statsSection) statsSection.classList.add("hidden");
      if (historySection) historySection.classList.remove("hidden");
    } else if (tab === "both") {
      if (statsSection) statsSection.classList.remove("hidden");
      if (historySection) {
        historySection.classList.remove("hidden");
        historySection.classList.add("mt-8");
      }
    }
  }

  async loadStatuses() {
    try {
      this.statusOptions = await statusService.getActiveStatuses();
    } catch (error) {
      console.error("Statistics: Error loading statuses:", error);
      this.statusOptions = [];
    }
  }

  populateStatusFilter() {
    const statusFilter = document.getElementById("statusFilter");
    if (!statusFilter) return;

    const existingOptions = Array.from(statusFilter.options).map(
      (opt) => opt.value,
    );

    this.statusOptions.forEach((status) => {
      if (!existingOptions.includes(status.status_name)) {
        const option = document.createElement("option");
        option.value = status.status_name;
        option.textContent = status.status_name;
        statusFilter.appendChild(option);
      }
    });
  }

  isSubmittedStatus(status) {
    if (
      !status ||
      status === "N/A" ||
      status.toLowerCase().includes("unsubmitted")
    ) {
      return false;
    }
    return status.toLowerCase().includes("submitted");
  }

  isUnsubmittedStatus(status) {
    if (
      !status ||
      status === "N/A" ||
      status.toLowerCase().includes("unsubmitted")
    ) {
      return true;
    }
    const statusLower = status.toLowerCase();
    if (statusLower.includes("submitted")) {
      return false;
    }
    return true;
  }

  displayOverallStatistics() {
    const total = this.applicants.length;

    const submitted = this.applicants.filter((a) =>
      this.isSubmittedStatus(a.status),
    ).length;
    const unsubmitted = this.applicants.filter((a) =>
      this.isUnsubmittedStatus(a.status),
    ).length;

    const domestic = this.applicants.filter(
      (a) => a.canadian === "Yes" || a.visa === "PERM",
    ).length;
    const international = total - domestic;

    const male = this.applicants.filter((a) => a.gender === "Male").length;
    const female = this.applicants.filter((a) => a.gender === "Female").length;
    const genderNotSpecified = total - male - female;

    document.getElementById("submittedCount").textContent = submitted;
    document.getElementById("unsubmittedCount").textContent = unsubmitted;
    document.getElementById("domesticCount").textContent = domestic;
    document.getElementById("internationalCount").textContent = international;
    document.getElementById("maleCount").textContent = male;
    document.getElementById("femaleCount").textContent = female;
    document.getElementById("genderNotSpecifiedCount").textContent =
      genderNotSpecified;

    if (total > 0) {
      const malePercent = ((male / total) * 100).toFixed(1);
      const femalePercent = ((female / total) * 100).toFixed(1);
      const notSpecifiedPercent = ((genderNotSpecified / total) * 100).toFixed(
        1,
      );

      document.getElementById("malePercent").textContent = malePercent;
      document.getElementById("femalePercent").textContent = femalePercent;
      document.getElementById("genderNotSpecifiedPercent").textContent =
        notSpecifiedPercent;

      document.getElementById("maleBar").style.width = malePercent + "%";
      document.getElementById("femaleBar").style.width = femalePercent + "%";
      document.getElementById("genderNotSpecifiedBar").style.width =
        notSpecifiedPercent + "%";
    }

    this.displayCountryDistribution(this.applicants);
  }

  displayStatusBreakdown() {
    const container = document.getElementById("statusBreakdownList");
    if (!container) return;

    const canonicalStatusOrder = this.statusOptions.map((s) => s.status_name);

    const statusData = {};
    canonicalStatusOrder.forEach((status) => {
      statusData[status] = { count: 0, totalRating: 0, ratedCount: 0 };
    });

    let submittedCount = 0;
    let unsubmittedCount = 0;
    let submittedTotalRating = 0;
    let submittedRatedCount = 0;
    let unsubmittedTotalRating = 0;
    let unsubmittedRatedCount = 0;
    let totalWithStatus = 0;

    this.applicants.forEach((applicant) => {
      const status = applicant.review_status || "Not Reviewed";

      if (this.isSubmittedStatus(applicant.status)) {
        submittedCount++;
        if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
          submittedTotalRating += parseFloat(applicant.overall_rating);
          submittedRatedCount++;
        }
      } else if (this.isUnsubmittedStatus(applicant.status)) {
        unsubmittedCount++;
        if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
          unsubmittedTotalRating += parseFloat(applicant.overall_rating);
          unsubmittedRatedCount++;
        }
      }

      if (statusData[status]) {
        statusData[status].count++;
        totalWithStatus++;
        if (applicant.overall_rating && !isNaN(applicant.overall_rating)) {
          statusData[status].totalRating += parseFloat(
            applicant.overall_rating,
          );
          statusData[status].ratedCount++;
        }
      }
    });

    const totalApplicants = this.applicants.length;
    const submittedPercentage =
      totalApplicants > 0
        ? ((submittedCount / totalApplicants) * 100).toFixed(1)
        : "0.0";
    const unsubmittedPercentage =
      totalApplicants > 0
        ? ((unsubmittedCount / totalApplicants) * 100).toFixed(1)
        : "0.0";

    const submittedUnsubmittedHtml = `
      <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="Submitted Applications">
        <div class="flex justify-between items-center text-xs">
          <span class="text-gray-700 font-medium truncate" title="Submitted Applications">Submitted Applications</span>
          <span class="text-gray-600 ml-2 flex-shrink-0">${submittedCount} (${submittedPercentage}%)</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
          <div class="bg-green-500 h-1.5 rounded-full transition-all duration-500" style="width: ${submittedPercentage}%"></div>
        </div>
      </div>
      <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="Unsubmitted Applications">
        <div class="flex justify-between items-center text-xs">
          <span class="text-gray-700 font-medium truncate" title="Unsubmitted Applications">Unsubmitted Applications</span>
          <span class="text-gray-600 ml-2 flex-shrink-0">${unsubmittedCount} (${unsubmittedPercentage}%)</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
          <div class="bg-gray-400 h-1.5 rounded-full transition-all duration-500" style="width: ${unsubmittedPercentage}%"></div>
        </div>
      </div>
    `;

    const orderedStatuses = canonicalStatusOrder.map((status) => [
      status,
      statusData[status],
    ]);

    const reviewStatusHtml = orderedStatuses
      .map(([status, data]) => {
        const percentage =
          totalWithStatus > 0
            ? ((data.count / totalWithStatus) * 100).toFixed(1)
            : "0.0";
        const barColor = this.getBarColor(status);

        return `
          <div class="cursor-pointer hover:bg-blue-50 hover:shadow-sm px-2 py-1.5 rounded transition-all duration-200 status-item" data-status="${status}">
            <div class="flex justify-between items-center text-xs">
              <span class="text-gray-700 font-medium truncate" title="${status}">${status}</span>
              <span class="text-gray-600 ml-2 flex-shrink-0">${data.count} (${percentage}%)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
              <div class="h-1.5 rounded-full transition-all duration-500" style="width: ${percentage}%; background-color: ${barColor};"></div>
            </div>
          </div>
        `;
      })
      .join("");

    container.innerHTML = submittedUnsubmittedHtml + reviewStatusHtml;

    this.setupStatusRowClickHandlers();
  }

  setupStatusRowClickHandlers() {
    const statusItems = document.querySelectorAll(".status-item");
    statusItems.forEach((item) => {
      item.addEventListener("click", () => {
        const status = item.getAttribute("data-status");
        const statusFilter = document.getElementById("statusFilter");
        if (statusFilter) {
          statusFilter.value = status;
          this.displayStatusStatistics(status);
          const statusStatsSection = document.getElementById("statusStats");
          if (statusStatsSection) {
            statusStatsSection.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }
        }
      });
    });
  }

  getStatusColor(status) {
    const statusConfig = this.statusOptions.find(
      (s) => s.status_name === status,
    );
    const color = statusConfig ? statusConfig.badge_color : "gray";
    return `bg-${color}-100 text-${color}-800`;
  }

  getBarColor(status) {
    const statusConfig = this.statusOptions.find(
      (s) => s.status_name === status,
    );
    const color = statusConfig ? statusConfig.badge_color : "gray";

    const colorMap = {
      gray: "#6B7280",
      red: "#EF4444",
      yellow: "#F59E0B",
      green: "#10B981",
      blue: "#3B82F6",
      indigo: "#6366F1",
      purple: "#A855F7",
      pink: "#EC4899",
      orange: "#F97316",
      teal: "#14B8A6",
    };

    return colorMap[color] || colorMap["gray"];
  }

  async loadApplicants() {
    try {
      const sessionId = window.SessionStore
        ? SessionStore.getCurrentSessionId()
        : null;
      const params = sessionId ? { session_id: sessionId } : {};
      const result = await api.get("/api/applicants", params);
      this.applicants = result.applicants || [];
    } catch (error) {
      console.error("Error loading applicants:", error);
      this.applicants = [];
    }
  }

  setupEventListeners() {
    const statusFilter = document.getElementById("statusFilter");
    if (statusFilter) {
      statusFilter.addEventListener("change", (e) => {
        this.displayStatusStatistics(e.target.value);
      });
    }
  }

  displayStatusStatistics(status) {
    const statusStatsContainer = document.getElementById("statusStats");

    let filteredApplicants;
    if (status === "Submitted Applications") {
      filteredApplicants = this.applicants.filter((a) =>
        this.isSubmittedStatus(a.status),
      );
    } else if (status === "Unsubmitted Applications") {
      filteredApplicants = this.applicants.filter((a) =>
        this.isUnsubmittedStatus(a.status),
      );
    } else {
      filteredApplicants = !status
        ? this.applicants
        : this.applicants.filter((a) => a.review_status === status);
    }

    const total = filteredApplicants.length;
    const displayTitle = !status ? "All Statuses" : status;

    if (total === 0) {
      statusStatsContainer.innerHTML = `
        <div class="bg-white rounded-lg shadow p-6">
          <h3 class="text-xl font-semibold text-gray-800 mb-4">${displayTitle}</h3>
          <p class="text-gray-500 text-center">No applicants with this status</p>
        </div>
      `;
      return;
    }

    const domestic = filteredApplicants.filter(
      (a) => a.canadian === "Yes" || a.visa === "PERM",
    ).length;
    const international = total - domestic;
    const domesticPercent = ((domestic / total) * 100).toFixed(1);
    const internationalPercent = ((international / total) * 100).toFixed(1);

    const male = filteredApplicants.filter((a) => a.gender === "Male").length;
    const female = filteredApplicants.filter(
      (a) => a.gender === "Female",
    ).length;
    const genderNotSpecified = total - male - female;
    const malePercent = ((male / total) * 100).toFixed(1);
    const femalePercent = ((female / total) * 100).toFixed(1);
    const notSpecifiedPercent = ((genderNotSpecified / total) * 100).toFixed(1);

    const countryBarsHTML = this.generateCountryBars(filteredApplicants);

    statusStatsContainer.innerHTML = `
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-xl font-semibold text-gray-800 mb-6">
          ${displayTitle}
          <span class="text-gray-500 text-base font-normal">(${total} applicants)</span>
        </h3>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 class="text-md font-semibold text-gray-700 mb-4">Residency Status</h4>
            <div class="space-y-3">
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">Domestic</span>
                  <span class="font-medium text-gray-900">${domestic} (${domesticPercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div class="bg-blue-500 h-3 rounded-full transition-all duration-500" style="width: ${domesticPercent}%"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">International</span>
                  <span class="font-medium text-gray-900">${international} (${internationalPercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div class="bg-green-600 h-3 rounded-full transition-all duration-500" style="width: ${internationalPercent}%"></div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 class="text-md font-semibold text-gray-700 mb-4">Gender Distribution</h4>
            <div class="space-y-3">
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">Male</span>
                  <span class="font-medium text-gray-900">${male} (${malePercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div class="bg-blue-500 h-3 rounded-full transition-all duration-500" style="width: ${malePercent}%"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">Female</span>
                  <span class="font-medium text-gray-900">${female} (${femalePercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div class="bg-pink-500 h-3 rounded-full transition-all duration-500" style="width: ${femalePercent}%"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">Not Specified</span>
                  <span class="font-medium text-gray-900">${genderNotSpecified} (${notSpecifiedPercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div class="bg-gray-400 h-3 rounded-full transition-all duration-500" style="width: ${notSpecifiedPercent}%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <h4 class="text-md font-semibold text-gray-700 mb-4">Top Countries</h4>
          <div class="space-y-2 max-h-80 overflow-y-auto">
            ${countryBarsHTML}
          </div>
        </div>
      </div>
    `;
  }

  displayCountryDistribution(applicants) {
    const countriesChart = document.getElementById("countriesChart");
    if (!countriesChart) return;

    const countryCounts = {};
    applicants.forEach((applicant) => {
      const country = applicant.citizenship_country || "Not Specified";
      countryCounts[country] = (countryCounts[country] || 0) + 1;
    });

    const sortedCountries = Object.entries(countryCounts).sort(
      (a, b) => b[1] - a[1],
    );

    if (sortedCountries.length === 0) {
      countriesChart.innerHTML =
        '<div class="text-center text-gray-500 py-4">No data available</div>';
      return;
    }

    const total = applicants.length;
    const html = sortedCountries
      .map(([country, count]) => {
        const percent = ((count / total) * 100).toFixed(1);
        return `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-gray-700 font-medium truncate" title="${country}">${country}</span>
              <span class="text-gray-600 ml-2 flex-shrink-0">${count} (${percent}%)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-ubc-blue h-2 rounded-full transition-all duration-500" style="width: ${percent}%"></div>
            </div>
          </div>
        `;
      })
      .join("");

    countriesChart.innerHTML = html;
  }

  initStatusHistory() {
    ["historyStatusFromFilter", "historyStatusToFilter"].forEach((id) => {
      const select = document.getElementById(id);
      if (select) {
        this.statusOptions.forEach((status) => {
          const option = document.createElement("option");
          option.value = status.status_name;
          option.textContent = status.status_name;
          select.appendChild(option);
        });
      }
    });

    const statusFromFilter = document.getElementById("historyStatusFromFilter");
    const statusToFilter = document.getElementById("historyStatusToFilter");
    const acceptedFilter = document.getElementById("historyAcceptedFilter");
    if (statusFromFilter)
      statusFromFilter.addEventListener("change", () =>
        this.loadStatusHistory(),
      );
    if (statusToFilter)
      statusToFilter.addEventListener("change", () => this.loadStatusHistory());
    if (acceptedFilter)
      acceptedFilter.addEventListener("change", () => this.loadStatusHistory());
    const searchInput = document.getElementById("historySearch");
    if (searchInput)
      searchInput.addEventListener("input", () => this._applySearchAndRender());

    if (window.SessionStore) {
      SessionStore.onSessionChange(() => this.loadStatusHistory());
    }

    this.loadStatusHistory();
  }

  async loadStatusHistory() {
    const sessionId = window.SessionStore
      ? SessionStore.getCurrentSessionId()
      : null;
    if (!sessionId) {
      this._showHistoryState("empty");
      return;
    }

    const statusFrom =
      document.getElementById("historyStatusFromFilter")?.value || "";
    const statusTo =
      document.getElementById("historyStatusToFilter")?.value || "";
    const acceptedFilter =
      document.getElementById("historyAcceptedFilter")?.value || "";

    // Only show the loading spinner on the very first load to avoid page jumping
    if (this.historyData.length === 0) {
      this._showHistoryState("loading");
    }

    try {
      const params = { session_id: sessionId };
      if (statusFrom) params.status_from = statusFrom;
      if (statusTo) params.status_to = statusTo;
      if (acceptedFilter) params.accepted_filter = acceptedFilter;

      const result = await api.get("/api/logs/status-history", params);
      this.historyData = result.history || [];
      this._applySearchAndRender();
    } catch (error) {
      console.error("Error loading status history:", error);
      this._showHistoryState("empty");
    }
  }

  _applySearchAndRender() {
    const search =
      document.getElementById("historySearch")?.value.toLowerCase().trim() ||
      "";
    let filtered = this.historyData;

    if (search) {
      filtered = filtered.filter((row) => {
        const name =
          `${row.given_name || ""} ${row.family_name || ""}`.toLowerCase();
        const studentNum = (row.student_number || "").toLowerCase();
        const submitDate = row.submit_date
          ? new Date(row.submit_date).toLocaleDateString().toLowerCase()
          : "";
        const changedAt = row.status_changed_at
          ? new Date(row.status_changed_at).toLocaleString().toLowerCase()
          : "";
        return (
          name.includes(search) ||
          studentNum.includes(search) ||
          submitDate.includes(search) ||
          changedAt.includes(search)
        );
      });
    }

    // Keep the table wrapper always visible once shown — never toggle it to
    // avoid layout shifts that cause the page to jump on filter changes.
    // Instead, render an empty-state row directly inside the tbody.
    this._showHistoryState("table");
    this._renderHistoryTable(filtered);
  }

  _showHistoryState(state) {
    document
      .getElementById("statusHistoryLoading")
      ?.classList.toggle("hidden", state !== "loading");
    document
      .getElementById("statusHistoryEmpty")
      ?.classList.toggle("hidden", state !== "empty");
    document
      .getElementById("statusHistoryTableWrapper")
      ?.classList.toggle("hidden", state !== "table");
  }

  _renderHistoryTable(rows) {
    const tbody = document.getElementById("statusHistoryTableBody");
    if (!tbody) return;

    const countEl = document.getElementById("historyResultCount");
    const countWrapper = document.getElementById("historyResultCountWrapper");
    const statusFrom =
      document.getElementById("historyStatusFromFilter")?.value || "";
    const statusTo =
      document.getElementById("historyStatusToFilter")?.value || "";
    const searchVal =
      document.getElementById("historySearch")?.value.trim() || "";
    const isFiltering = !!statusFrom || !!statusTo || !!searchVal;

    if (countEl && countWrapper) {
      countWrapper.style.display = isFiltering ? "" : "none";
      if (isFiltering) {
        const parts = [];
        if (statusFrom) parts.push(`From: <strong>${statusFrom}</strong>`);
        if (statusTo) parts.push(`To: <strong>${statusTo}</strong>`);
        const filterLabel = parts.length ? ` (${parts.join(", ")})` : "";
        countEl.innerHTML = `Showing <span class="font-semibold">${rows.length}</span> of <span class="font-semibold">${this.historyData.length}</span> results${filterLabel}`;
      }
    }

    if (rows.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="px-4 py-8 text-center text-sm text-gray-500">
            No results found.
          </td>
        </tr>
      `;
      return;
    }
    tbody.innerHTML = rows.map((row) => this._renderHistoryRow(row)).join("");
  }

  _renderHistoryRow(row) {
    const name =
      `${row.given_name || ""} ${row.family_name || ""}`.trim() || "—";
    const studentNumber = row.student_number || "—";
    const submitDate = row.submit_date
      ? new Date(row.submit_date).toLocaleDateString()
      : "—";
    const changedAt = row.status_changed_at
      ? new Date(row.status_changed_at).toLocaleString()
      : "—";
    const previousStatus = row.previous_status || "—";
    const statusReached = row.status_reached || "—";
    const previousBadgeClass = this.getStatusColor(row.previous_status);
    const reachedBadgeClass = this.getStatusColor(row.status_reached);
    return `
      <tr class="hover:bg-gray-50">
        <td class="px-4 py-3 text-sm text-gray-900">${name}</td>
        <td class="px-4 py-3 text-sm text-gray-600">${studentNumber}</td>
        <td class="px-4 py-3 text-sm text-gray-600">${submitDate}</td>
        <td class="px-4 py-3 text-sm text-gray-600">${changedAt}</td>
        <td class="px-4 py-3 text-sm">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="px-2 py-1 rounded-full text-xs font-medium ${previousBadgeClass}">${previousStatus}</span>
            <span class="text-gray-400">→</span>
            <span class="px-2 py-1 rounded-full text-xs font-medium ${reachedBadgeClass}">${statusReached}</span>
          </div>
        </td>
      </tr>
    `;
  }

  generateCountryBars(applicants) {
    const countryCounts = {};
    applicants.forEach((applicant) => {
      const country = applicant.citizenship_country || "Not Specified";
      countryCounts[country] = (countryCounts[country] || 0) + 1;
    });

    const sortedCountries = Object.entries(countryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    if (sortedCountries.length === 0) {
      return '<div class="text-center text-gray-500 py-4">No data available</div>';
    }

    const total = applicants.length;
    return sortedCountries
      .map(([country, count]) => {
        const percent = ((count / total) * 100).toFixed(1);
        return `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-gray-700 font-medium truncate" title="${country}">${country}</span>
              <span class="text-gray-600 ml-2 flex-shrink-0">${count} (${percent}%)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-ubc-blue h-2 rounded-full transition-all duration-500" style="width: ${percent}%"></div>
            </div>
          </div>
        `;
      })
      .join("");
  }
  // ── Compare mode ─────────────────────────────────────────────────────────

  initCompare() {
    document
      .getElementById("compareToggleBtn")
      ?.addEventListener("click", () => this.toggleCompare());
    document
      .getElementById("compareResetBtn")
      ?.addEventListener("click", () => this.toggleCompare(false));
    document
      .getElementById("timelineModeToggle")
      ?.addEventListener("click", () => this.toggleTimelineMode());
    document
      .getElementById("rangeModeToggle")
      ?.addEventListener("click", () => this.toggleRangeMode());
    document
      .getElementById("compareSessionA")
      ?.addEventListener("change", () => this.loadCompareData());
    document
      .getElementById("compareSessionB")
      ?.addEventListener("change", () => this.loadCompareData());
    document
      .getElementById("compareMonthPicker")
      ?.addEventListener("change", () => this.loadCompareData());
    document
      .getElementById("compareSessionRange")
      ?.addEventListener("change", () => this.loadCompareData());
    document
      .getElementById("rangeYearFrom")
      ?.addEventListener("change", () => this.loadCompareData());
    document
      .getElementById("rangeYearTo")
      ?.addEventListener("change", () => this.loadCompareData());
  }

  async toggleCompare(on = !this.compareMode) {
    this.compareMode = on;
    const btn = document.getElementById("compareToggleBtn");
    const pickerBar = document.getElementById("comparePickerBar");
    const singleView = document.getElementById("compareStatsSingle");
    const compareView = document.getElementById("compareStatsView");

    btn?.classList.toggle("bg-ubc-blue", on);
    btn?.classList.toggle("text-white", on);
    pickerBar?.classList.toggle("hidden", !on);
    singleView?.classList.toggle("hidden", on);
    compareView?.classList.toggle("hidden", !on);

    if (on) {
      if (this.sessionsList.length === 0) await this.loadSessionsForCompare();
      this.loadCompareData();
    }
  }

  toggleRangeMode() {
    this.rangeMode = !this.rangeMode;
    const btn = document.getElementById("rangeModeToggle");
    document
      .getElementById("twoSessionPickers")
      ?.classList.toggle("hidden", this.rangeMode);
    document
      .getElementById("rangeModePickers")
      ?.classList.toggle("hidden", !this.rangeMode);
    btn?.classList.toggle("bg-ubc-blue", this.rangeMode);
    btn?.classList.toggle("text-white", this.rangeMode);
    btn?.classList.toggle("border-ubc-blue", this.rangeMode);
    if (!this.rangeMode) this.loadCompareData();
    else {
      const view = document.getElementById("compareStatsView");
      if (view)
        view.innerHTML = `<p class="text-gray-400 text-sm p-4 text-center">Enter a From and To year to compare.</p>`;
    }
  }

  toggleTimelineMode() {
    this.timelineMode = !this.timelineMode;
    const btn = document.getElementById("timelineModeToggle");
    btn?.classList.toggle("bg-ubc-blue", this.timelineMode);
    btn?.classList.toggle("text-white", this.timelineMode);
    btn?.classList.toggle("border-ubc-blue", this.timelineMode);
    const view = document.getElementById("compareTimelineView");
    if (!this.timelineMode) {
      view?.classList.add("hidden");
      return;
    }
    view?.classList.remove("hidden");
    this._loadTimelineData();
  }

  async _loadTimelineData() {
    const view = document.getElementById("compareTimelineView");
    if (!view) return;
    const a = document.getElementById("compareSessionA")?.value;
    const b = document.getElementById("compareSessionB")?.value;
    if (!a || !b) {
      view.innerHTML = `<p class="text-gray-400 text-sm p-4 text-center">Select two sessions to see the timeline.</p>`;
      return;
    }
    view.innerHTML = this._loadingHTML();
    try {
      const data = await api.get("/api/statistics/compare-timeline", {
        session_a: a,
        session_b: b,
      });
      if (!data?.success) throw new Error(data?.message || "Failed to load");
      this._renderTimelineView(view, data);
    } catch (e) {
      view.innerHTML = `<p class="text-red-500 text-sm p-4">${e.message}</p>`;
    }
  }

  async loadSessionsForCompare() {
    const result = await api.get("/api/sessions");
    const byCampus = result?.sessions || {};
    this.sessionsList = Object.values(byCampus).flat();
    ["compareSessionA", "compareSessionB", "compareSessionRange"].forEach(
      (id) => this._populateSessionSelect(id),
    );
    // Default B to the second session so we get a meaningful diff immediately
    const bSelect = document.getElementById("compareSessionB");
    if (bSelect && bSelect.options.length > 1) bSelect.selectedIndex = 1;
  }

  _populateSessionSelect(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    el.innerHTML = this.sessionsList
      .map((s) => `<option value="${s.id}">${s.name}</option>`)
      .join("");
    // Pre-select current session for A and Range selects
    const currentId = window.SessionStore?.getCurrentSessionId();
    if (currentId && selectId !== "compareSessionB") {
      const match = [...el.options].find(
        (o) => Number(o.value) === Number(currentId),
      );
      if (match) match.selected = true;
    }
  }

  async loadCompareData() {
    const view = document.getElementById("compareStatsView");
    if (!view) return;
    view.innerHTML = this._loadingHTML();

    try {
      const data = this.rangeMode
        ? await this._fetchRangeData()
        : await this._fetchTwoSessionData();

      // null means inputs are incomplete — show a soft prompt, not an error
      if (data === null) {
        view.innerHTML = `<p class="text-gray-400 text-sm p-4 text-center">
          ${this.rangeMode ? "Enter a From and To year to compare." : "Select two sessions to compare."}
        </p>`;
        return;
      }

      if (!data.success) throw new Error(data.message || "Failed to load");
      this._renderCompareView(view, data);
    } catch (e) {
      view.innerHTML = `<p class="text-red-500 text-sm p-4">${e.message}</p>`;
    }
    if (this.timelineMode) this._loadTimelineData();
  }

  async _fetchTwoSessionData() {
    const a = document.getElementById("compareSessionA")?.value;
    const b = document.getElementById("compareSessionB")?.value;
    if (!a || !b) return null;
    const month = document.getElementById("compareMonthPicker")?.value;
    const params = { session_a: a, session_b: b };
    if (month) params.cutoff_month = month;
    return api.get("/api/statistics/compare", params);
  }

  async _fetchRangeData() {
    const sessionId = document.getElementById("compareSessionRange")?.value;
    const yearFrom = document.getElementById("rangeYearFrom")?.value;
    const yearTo = document.getElementById("rangeYearTo")?.value;
    if (!sessionId || !yearFrom || !yearTo) return null;
    return api.get("/api/statistics/compare-range", {
      session_id: sessionId,
      year_from: yearFrom,
      year_to: yearTo,
    });
  }

  // ── Timeline rendering ────────────────────────────────────────────────────

  _renderTimelineView(container, data) {
    const { session_a, session_b, months } = data;
    if (!months?.length) {
      container.innerHTML =
        '<p class="text-gray-500 text-sm p-4">No submission data available for these sessions.</p>';
      return;
    }
    const MONTHS = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    const metrics = [
      { label: "Submitted", fn: (s) => s.submitted ?? 0 },
      { label: "Domestic", fn: (s) => s.domestic ?? 0 },
      { label: "International", fn: (s) => s.international ?? 0 },
      { label: "Male", fn: (s) => s.male ?? 0 },
      { label: "Female", fn: (s) => s.female ?? 0 },
      ...this.statusOptions.map((opt) => ({
        label: opt.status_name,
        fn: (s) => s.review_status_counts?.[opt.status_name] ?? 0,
      })),
    ];
    const monthHeaders = months
      .map(
        ({ month }) =>
          `<th colspan="2" class="px-3 py-2 text-center text-xs font-bold uppercase tracking-wider text-gray-500 border-l border-gray-100">${MONTHS[month - 1]}</th>`,
      )
      .join("");
    const subHeaders = months
      .map(
        () =>
          `<th class="px-2 py-1.5 text-center text-xs font-semibold text-blue-600 border-l border-gray-100">A</th>` +
          `<th class="px-2 py-1.5 text-center text-xs font-semibold text-amber-600">B</th>`,
      )
      .join("");
    const rows = metrics
      .map(({ label, fn }) => {
        const cells = months
          .map(({ a_stats, b_stats }) => {
            const a = fn(a_stats);
            const b = fn(b_stats);
            const cls =
              a > b
                ? "text-green-600"
                : a < b
                  ? "text-red-500"
                  : "text-gray-400";
            return (
              `<td class="px-2 py-2 text-center text-sm font-medium text-gray-900 border-l border-gray-100">${a}</td>` +
              `<td class="px-2 py-2 text-center text-sm font-medium ${cls}">${b}</td>`
            );
          })
          .join("");
        return `<tr class="hover:bg-gray-50"><td class="px-3 py-2 text-sm text-gray-600 font-medium whitespace-nowrap sticky left-0 bg-white">${label}</td>${cells}</tr>`;
      })
      .join("");
    container.innerHTML = `
      <div class="mb-3 flex items-center gap-2 flex-wrap">
        <span class="inline-block text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-200">A — ${session_a.name}</span>
        <span class="text-gray-300 font-bold">vs</span>
        <span class="inline-block text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-200">B — ${session_b.name}</span>
        <span class="text-xs text-gray-400 ml-1">submitted by 1st of month</span>
      </div>
      <div class="bg-white rounded-lg shadow overflow-x-auto">
        <table class="border-collapse text-sm">
          <thead>
            <tr class="bg-gray-50">
              <th class="px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-gray-500 sticky left-0 bg-gray-50">Metric</th>
              ${monthHeaders}
            </tr>
            <tr class="bg-gray-50 border-b border-gray-200">
              <th class="sticky left-0 bg-gray-50"></th>${subHeaders}
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">${rows}</tbody>
        </table>
      </div>`;
  }

  // ── Compare rendering ─────────────────────────────────────────────────────

  _renderCompareView(container, data) {
    const isRange = this.rangeMode;
    const left = isRange ? data.session : data.session_a;
    const right = isRange ? data.range : data.session_b;
    if (!left || !right?.stats) {
      container.innerHTML =
        '<p class="text-gray-500 text-sm p-4">No data available for one or both sessions.</p>';
      return;
    }
    container.innerHTML = [
      this._compareSection(
        "Quick Stats",
        this._quickStatsHTML(left.stats, left.name, "a") +
          this._quickStatsHTML(right.stats, right.name ?? right.label, "b"),
        "compare-cols",
      ),
      this._compareSection(
        "Applications by Status",
        this._statusTableHTML(left, right),
        "",
      ),
      this._compareSection(
        "Gender Distribution",
        this._genderHTML(left.stats, left.name, "a") +
          this._genderHTML(right.stats, right.name ?? right.label, "b"),
        "compare-cols",
      ),
      this._compareSection(
        "Top Countries",
        this._countriesHTML(left.stats, left.name, "a") +
          this._countriesHTML(right.stats, right.name ?? right.label, "b"),
        "compare-cols",
      ),
    ].join("");
  }

  _compareSection(title, innerHTML, gridClass) {
    return `
      <div class="mb-7">
        <div class="flex items-center gap-2 mb-3.5">
          <span class="text-xs font-bold uppercase tracking-widest text-gray-400">${title}</span>
          <div class="flex-1 h-px bg-gray-200"></div>
        </div>
        <div class="${gridClass === "compare-cols" ? "grid grid-cols-2 gap-5" : ""}">
          ${innerHTML}
        </div>
      </div>`;
  }

  _colHeader(label, side) {
    const cls =
      side === "a"
        ? "bg-blue-50 text-blue-700 border border-blue-200"
        : "bg-amber-50 text-amber-700 border border-amber-200";
    return `<span class="inline-block text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-md mb-3 ${cls}">${label}</span>`;
  }

  _quickStatsHTML(stats, label, side) {
    const cards = [
      {
        label: "Submitted",
        val: stats.submitted,
        color: "green",
        icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
      },
      {
        label: "Unsubmitted",
        val: stats.unsubmitted,
        color: "yellow",
        icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
      },
      {
        label: "Domestic",
        val: stats.domestic,
        color: "blue",
        icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
      },
      {
        label: "International",
        val: stats.international,
        color: "purple",
        icon: "M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
      },
    ];
    const cardRows = cards
      .map(
        ({ label: lbl, val, color, icon }) => `
        <div class="bg-white rounded-lg shadow p-4 border-l-4 border-${color}-500 flex items-center justify-between">
          <div>
            <p class="text-xs text-gray-600 font-medium">${lbl}</p>
            <p class="text-2xl font-bold text-gray-900">${val ?? "—"}</p>
          </div>
          <div class="bg-${color}-100 rounded-full p-2.5">
            <svg class="w-5 h-5 text-${color}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${icon}"/>
            </svg>
          </div>
        </div>`,
      )
      .join("");
    return `<div>${this._colHeader(label, side)}<div class="grid grid-cols-2 gap-3">${cardRows}</div></div>`;
  }

  _statusTableHTML(left, right) {
    const lStats = left.stats;
    const rStats = right.stats;
    const lTotal = lStats.total || 1;
    const rTotal = rStats.total || 1;
    const lLabel = left.name;
    const rLabel = right.name ?? right.label;

    const rows = [
      { label: "Submitted", lVal: lStats.submitted, rVal: rStats.submitted },
      {
        label: "Unsubmitted",
        lVal: lStats.unsubmitted,
        rVal: rStats.unsubmitted,
      },
      ...this.statusOptions.map((s) => ({
        label: s.status_name,
        lVal: lStats.review_status_counts?.[s.status_name] ?? 0,
        rVal: rStats.review_status_counts?.[s.status_name] ?? 0,
      })),
    ]
      .map(({ label, lVal, rVal }) => {
        const delta = (lVal ?? 0) - (rVal ?? 0);
        return `
          <tr class="hover:bg-gray-50">
            <td class="px-3 py-2 text-sm text-gray-700">${label}</td>
            <td class="px-3 py-2 text-sm font-medium text-gray-900">
              ${lVal ?? 0} <span class="text-gray-400 font-normal">(${((lVal / lTotal) * 100).toFixed(1)}%)</span>
            </td>
            <td class="px-3 py-2 text-center">${this._deltaTag(delta)}</td>
            <td class="px-3 py-2 text-sm font-medium text-gray-900">
              ${rVal ?? 0} <span class="text-gray-400 font-normal">(${((rVal / rTotal) * 100).toFixed(1)}%)</span>
            </td>
          </tr>`;
      })
      .join("");

    return `
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="bg-gray-50">
              <th class="px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Status</th>
              <th class="px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-blue-600">${lLabel}</th>
              <th class="px-3 py-2 text-center text-xs font-bold uppercase tracking-wider text-gray-400">Δ</th>
              <th class="px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-amber-600">${rLabel}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">${rows}</tbody>
        </table>
      </div>`;
  }

  _genderHTML(stats, label, side) {
    const total = stats.total || 1;
    const bars = [
      { lbl: "Male", val: stats.male, color: "#3b82f6" },
      { lbl: "Female", val: stats.female, color: "#ec4899" },
      {
        lbl: "Not Specified",
        val: stats.gender_not_specified,
        color: "#9ca3af",
      },
    ]
      .map(({ lbl, val, color }) => {
        const pct = ((val / total) * 100).toFixed(1);
        return `
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">${lbl}</span>
              <span class="font-medium text-gray-900">${val} (${pct}%)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
              <div class="h-3 rounded-full transition-all duration-500" style="width:${pct}%;background:${color}"></div>
            </div>
          </div>`;
      })
      .join("");
    return `<div class="bg-white rounded-lg shadow p-5">${this._colHeader(label, side)}<div class="space-y-3">${bars}</div></div>`;
  }

  _countriesHTML(stats, label, side) {
    const total = stats.total || 1;
    const bars = (stats.top_countries || [])
      .map(({ country, count }) => {
        const pct = ((count / total) * 100).toFixed(1);
        return `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-gray-700 font-medium truncate" title="${country}">${country}</span>
              <span class="text-gray-500 ml-2 flex-shrink-0">${count} (${pct}%)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-ubc-blue h-2 rounded-full" style="width:${pct}%"></div>
            </div>
          </div>`;
      })
      .join("");
    return `<div class="bg-white rounded-lg shadow p-5">${this._colHeader(label, side)}<div class="space-y-2.5 max-h-64 overflow-y-auto">${bars}</div></div>`;
  }

  _deltaTag(delta) {
    if (delta > 0)
      return `<span class="inline-flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded-full bg-green-50 text-green-700">▲ ${delta}</span>`;
    if (delta < 0)
      return `<span class="inline-flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded-full bg-red-50 text-red-600">▼ ${Math.abs(delta)}</span>`;
    return `<span class="inline-flex items-center text-xs font-semibold px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">— 0</span>`;
  }

  _loadingHTML() {
    return `<div class="flex items-center justify-center py-12 text-gray-400 text-sm gap-2">
      <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      Loading comparison…
    </div>`;
  }
}

new StatisticsManager();
