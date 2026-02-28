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
}

new StatisticsManager();
