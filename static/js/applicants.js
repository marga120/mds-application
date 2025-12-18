/**
 * APPLICANTS MANAGER - Main Application Controller
 * 
 * This file manages the core functionality of the MDS Application Management System.
 * It handles applicant data display, CSV file uploads, search/filtering, modal interactions,
 * test scores management, ratings system, status updates, and all user interactions 
 * with the applicant database. This is the primary controller for the main dashboard.
 */

class ApplicantsManager {
  constructor() {
    this.allApplicants = [];
    this.sessionName = "";
    this.sortColumn = null;
    this.sortDirection = 'asc'; 
    this.initializeEventListeners();
    this.loadSessionName();
    this.loadApplicants();
    this.initializeActionButtons();
    this.selectedApplicants = new Set();
    this.initializeExportButton();
    window.applicantsManager = this;
    this.initializeClearDataButton();
  }

  initializeEventListeners() {
  const fileInput = document.getElementById("fileInput");
  const uploadBtn = document.getElementById("uploadBtn");
  const searchInput = document.getElementById("searchInput");
  const searchFilter = document.getElementById("searchFilter");
  const exportBtn = document.getElementById("exportBtn");
  const bulkExportBtn = document.getElementById("bulkExportBtn");
  
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      this.exportApplicants();
    });
  }

  if (bulkExportBtn) {
    bulkExportBtn.addEventListener("click", () => {
      this.exportSelectedApplicants();
    });
  }

  fileInput.addEventListener("change", (e) => {
    this.handleFileSelect(e.target.files[0]);
  });

  uploadBtn.addEventListener("click", () => {
    this.uploadFile();
  });

  searchInput.addEventListener("input", () => {
    this.filterApplicants();
  });

  searchFilter.addEventListener("change", () => {
    this.filterApplicants();
  });

  // Modal close buttons
  const closeUploadModal = document.getElementById("closeUploadModal");
  if (closeUploadModal) {
    closeUploadModal.addEventListener("click", () => {
      this.closeUploadModal();
    });
  }

  const cancelUploadBtn = document.getElementById("cancelUploadBtn");
  if (cancelUploadBtn) {
    cancelUploadBtn.addEventListener("click", () => {
      this.closeUploadModal();
    });
  }
}
  // Add checkbox selection tracking
  toggleApplicantSelection(userCode, checked) {
    if (checked) {
      this.selectedApplicants.add(userCode);
    } else {
      this.selectedApplicants.delete(userCode);
    }
    this.updateBulkExportButton();
  }

  getTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    const minutes = Math.floor(diffInSeconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (diffInSeconds < 60) {
      return `${diffInSeconds} second${diffInSeconds !== 1 ? "s" : ""} ago`;
    } else if (minutes < 60) {
      return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
    } else if (hours < 24) {
      return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
    } else {
      return `${days} day${days !== 1 ? "s" : ""} ago`;
    }
  }

  async loadSessionName() {
    try {
      const response = await fetch("/api/sessions");
      const result = await response.json();

      if (result.success && result.session_name) {
        this.sessionName = result.session_name;
        this.updateSectionTitle();
      } else {
        // Fallback to default if no session name found
        this.sessionName = "Default Session";
        this.updateSectionTitle();
      }
    } catch (error) {
      console.error("Failed to load session name:", error);
      // Fallback to default
      this.sessionName = "Default Session";
      this.updateSectionTitle();
    }
  }

  updateSectionTitle() {
    const titleElement = document.getElementById("applicantsSectionTitle");

    if (titleElement) {
      const newTitle = `${this.sessionName} Applicants Database`;
      titleElement.textContent = newTitle;
    } else {
      console.error("Could not find element with ID 'applicantsSectionTitle'");
    }
  }

  handleFileSelect(file) {
    if (file && file.name.endsWith(".csv")) {
      this.selectedFile = file;
      document.getElementById("uploadBtn").disabled = false;
      document.getElementById("fileStatus").textContent = file.name;

      // Add timestamp to file selection
      const timestamp = new Date().toLocaleString();
      this.showMessage(`Selected: ${file.name} at ${timestamp}`, "success");
    } else {
      this.showMessage("Please select a CSV file", "error");
      document.getElementById("uploadBtn").disabled = true;
      document.getElementById("fileStatus").textContent = "No file chosen";
    }
  }

  async uploadFile() {
    if (!this.selectedFile) return;

    const uploadStartTime = new Date();
    const formData = new FormData();
    formData.append("file", this.selectedFile);

    // Add timestamp to the upload payload
    formData.append("upload_timestamp", uploadStartTime.toISOString());

    const uploadBtn = document.getElementById("uploadBtn");
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      const uploadEndTime = new Date();
      const uploadDuration = ((uploadEndTime - uploadStartTime) / 1000).toFixed(
        2
      );

      if (result.success) {
        const successMessage = `${result.records_processed} records uploaded in ${uploadDuration}s`;
        this.showMessage(successMessage, "success");

        // Show upload timestamp
        const timestampElement = document.getElementById("uploadTimestamp");
        timestampElement.innerHTML = `
                    <strong>Last Upload:</strong> ${uploadEndTime.toLocaleString()}<br>
                    <strong>Records:</strong> ${result.records_processed}
                `;
        timestampElement.style.display = "block";

        setTimeout(() => {
          this.closeUploadModal();
        }, 2000);

        this.loadSessionName();
        this.loadApplicants();
        document.getElementById("fileInput").value = "";
        this.selectedFile = null;
      } else {
        this.showMessage(result.message, "error");
      }
    } catch (error) {
      const uploadEndTime = new Date();
      const uploadDuration = ((uploadEndTime - uploadStartTime) / 1000).toFixed(
        2
      );
      this.showMessage(
        `Upload failed after ${uploadDuration}s: ${error.message}`,
        "error"
      );
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.textContent = "Upload CSV";
    }
  }

  async loadApplicants() {
    const container = document.getElementById("applicantsContainer");
    container.innerHTML = `
      <div class="loading-state">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mb-4"></div>
        <p class="text-lg font-medium">Loading applicants...</p>
      </div>`;

    try {
      const response = await fetch("/api/applicants");
      const result = await response.json();

      if (result.success) {
        this.allApplicants = result.applicants;
        this.displayApplicants(this.allApplicants);
      } else {
        container.innerHTML = `<div class="no-data">Error: ${result.message}</div>`;
      }
    } catch (error) {
      container.innerHTML = `<div class="no-data">Failed to load: ${error.message}</div>`;
    }
  }

  sortApplicants(column) {
    // Toggle sort direction if clicking the same column
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }

    // Sort the filtered applicants (or all if no filter)
    const applicantsToDisplay = this.getFilteredApplicants();
    const sorted = [...applicantsToDisplay].sort((a, b) => {
      let aValue, bValue;

      switch (column) {
        case 'applicant':
          aValue = `${a.family_name} ${a.given_name}`.toLowerCase();
          bValue = `${b.family_name} ${b.given_name}`.toLowerCase();
          break;
        case 'status':
          aValue = (a.status || '').toLowerCase();
          bValue = (b.status || '').toLowerCase();
          break;
        case 'submit_date':
          aValue = a.submit_date ? new Date(a.submit_date).getTime() : 0;
          bValue = b.submit_date ? new Date(b.submit_date).getTime() : 0;
          break;
         case 'review_status':
          aValue = (a.review_status || '').toLowerCase();
          bValue = (b.review_status || '').toLowerCase();
          break;
        case 'overall_rating':
          aValue = parseFloat(a.overall_rating) || 0;
          bValue = parseFloat(b.overall_rating) || 0;
          break;
        case 'last_updated':
          aValue = a.seconds_since_update || 0;
          bValue = b.seconds_since_update || 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return this.sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return this.sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    this.displayApplicants(sorted);
  }


  formatLastChanged(secondsAgo) {
    const seconds = Math.floor(secondsAgo);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(seconds / 3600);
    const days = Math.floor(seconds / 86400);

    if (seconds < 10) {
      return "Just changed";
    } else if (seconds < 60) {
      return `${seconds} second${seconds > 1 ? "s" : ""} ago`;
    } else if (minutes < 60) {
      return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    } else if (hours < 24) {
      return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    } else {
      return `${days} day${days > 1 ? "s" : ""} ago`;
    }
  }

  getInitials(firstName, lastName) {
    const first = firstName ? firstName.charAt(0).toUpperCase() : "";
    const last = lastName ? lastName.charAt(0).toUpperCase() : "";
    return first + last || "?";
  }

  getStatusBadge(status) {
    if (
      !status ||
      status === "N/A" ||
      status.toLowerCase().includes("unsubmitted")
    ) {
      return '<span class="status-badge status-unsubmitted">Unsubmitted</span>';
    }

    const statusLower = status.toLowerCase();
    if (statusLower.includes("submitted")) {
      return '<span class="status-badge status-submitted">✓ Submitted</span>';
    } else if (statusLower.includes("progress")) {
      return '<span class="status-badge status-progress"> In Progress</span>';
    } else {
      return `<span class="status-badge status-unsubmitted">${status}</span>`;
    }
  }

  getReviewStatusBadge(status) {
    const badge = document.createElement('span');
    const dot = document.createElement('span');
    
    badge.className = "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium";
    
    // Add status-specific styling matching updateStatusBadge colors
    switch (status) {
      case "Not Reviewed":
        badge.classList.add("bg-gray-100", "text-gray-800");
        break;
      case "Waitlist":
        badge.classList.add("bg-yellow-100", "text-yellow-800");
        break;
      case "Send Offer to CoGS":
        badge.classList.add("bg-green-100", "text-green-800");
        break;
      case "Offer Sent to CoGS":
        badge.classList.add("bg-blue-100", "text-blue-800");
        break;
      case "Offer Sent to Student":
        badge.classList.add("bg-purple-100", "text-purple-800");
        break;
      case "Reviewed by PPA":
        badge.classList.add("bg-indigo-100", "text-indigo-800");
        break;
      case "Need Jeff's Review":
        badge.classList.add("bg-purple-100", "text-purple-800");
        break;
      case "Need Khalad's Review":
        badge.classList.add("bg-pink-100", "text-pink-800");
        break;
      case "Declined":
        badge.classList.add("bg-red-100", "text-red-800");
        break;
      case "Offer Accepted":
        badge.classList.add("bg-green-100", "text-green-800");
        break;
      case "Offer Declined":
        badge.classList.add("bg-orange-100", "text-orange-800");
        break;
      default:
        badge.classList.add("bg-gray-100", "text-gray-800");
    }
    
    badge.appendChild(document.createTextNode(status));
    
    return badge.outerHTML;
  }

  getOverallRatingDisplay(rating) {
    if (!rating || rating === null) {
      return '<div class="text-gray-400 text-sm">No rating</div>';
    }

    const ratingValue = parseFloat(rating);
    let colorClass = "text-gray-600";

    // Color coding based on rating
    if (ratingValue >= 8.0) {
      colorClass = "text-green-600";
    } else if (ratingValue >= 6.0) {
      colorClass = "text-blue-600";
    } else if (ratingValue >= 4.0) {
      colorClass = "text-yellow-600";
    } else {
      colorClass = "text-red-600";
    }

    return `
      <div class="text-center">
        <div class="text-lg font-semibold ${colorClass}">${ratingValue.toFixed(
      1
    )}</div>
        <div class="text-xs text-gray-500">/10.0</div>
      </div>
    `;
  }

  isRecentUpdate(secondsAgo) {
    return secondsAgo < 60; // Less than 1 minute is considered recent
  }

  matchesStatus(status, searchTerm) {
    if (!status) return false;

    const statusLower = status.toLowerCase();
    const searchLower = searchTerm.toLowerCase();

    // Handle specific status searches more precisely
    if (searchLower === "submitted") {
      return (
        statusLower.includes("submitted") &&
        !statusLower.includes("unsubmitted")
      );
    } else if (searchLower === "unsubmitted") {
      return statusLower.includes("unsubmitted");
    } else if (searchLower === "progress") {
      return statusLower.includes("progress");
    } else {
      // For other searches, use regular contains logic
      return statusLower.includes(searchLower);
    }
  }

  filterApplicants() {
    const filtered = this.getFilteredApplicants();
    
    // If there's an active sort, apply it
    if (this.sortColumn) {
      const sorted = [...filtered].sort((a, b) => {
        let aValue, bValue;

        switch (this.sortColumn) {
          case 'applicant':
            aValue = `${a.family_name} ${a.given_name}`.toLowerCase();
            bValue = `${b.family_name} ${b.given_name}`.toLowerCase();
            break;
          case 'student_number':
            aValue = parseFloat(a.student_number) || 0;
            bValue = parseFloat(b.student_number) || 0;
            break;
          case 'status':
            aValue = (a.status || '').toLowerCase();
            bValue = (b.status || '').toLowerCase();
            break;
          case 'submit_date':
            aValue = a.submit_date ? new Date(a.submit_date).getTime() : 0;
            bValue = b.submit_date ? new Date(b.submit_date).getTime() : 0;
            break;
          case 'review_status':
            aValue = (a.review_status || '').toLowerCase();
            bValue = (b.review_status || '').toLowerCase();
          break;
          case 'overall_rating':
            aValue = parseFloat(a.overall_rating) || 0;
            bValue = parseFloat(b.overall_rating) || 0;
            break;
          case 'last_updated':
            aValue = a.seconds_since_update || 0;
            bValue = b.seconds_since_update || 0;
            break;
          default:
            return 0;
        }

        if (aValue < bValue) return this.sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return this.sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
      this.displayApplicants(sorted);
    } else {
      this.displayApplicants(filtered);
    }
  }
  getFilteredApplicants() {
    const searchTerm = document.getElementById("searchInput").value.toLowerCase();
    const filter = document.getElementById("searchFilter").value;

    if (!searchTerm) return this.allApplicants;

    return this.allApplicants.filter((applicant) => {
      if (filter === "all") {
        return (
          applicant.given_name?.toLowerCase().includes(searchTerm) ||
          applicant.family_name?.toLowerCase().includes(searchTerm) ||
          applicant.user_code?.toString().includes(searchTerm) ||
          applicant.student_number?.toString().includes(searchTerm) ||
          applicant.status?.toLowerCase().includes(searchTerm) ||
          applicant.review_status?.toLowerCase().includes(searchTerm)
        );
      } else {
        return applicant[filter]?.toLowerCase().includes(searchTerm);
      }
    });
  }

  getSortIcon(column) {
    if (this.sortColumn !== column) {
      // Inactive column - light gray/white
      return `<svg class="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/>
              </svg>`;
    }
    if (this.sortDirection === 'asc') {
      // Active ascending - white
      return `<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
              </svg>`;
    }
    // Active descending - white
    return `<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>`;
  }

  showMessage(text, type) {
    const message = document.getElementById("message");
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = "block";

    setTimeout(() => {
      message.style.display = "none";
    }, 5000); // Extended to 5 seconds for timestamp messages
  }

  initializeActionButtons() {
    // Add event delegation for action buttons
    document.addEventListener("click", (e) => {
      if (e.target.closest(".btn-actions")) {
        const button = e.target.closest(".btn-actions");
        const userCode = button.dataset.userCode;
        const userName = button.dataset.userName;
        this.showApplicantModal(userCode, userName);
      }
    });
  }

  async updateRatingFormForViewer() {
    try {
      const response = await fetch("/api/auth/user");
      const result = await response.json();

      if (result.success && result.user.role === "Viewer") {
        const ratingFormSection = document.getElementById("ratingFormSection");
        if (ratingFormSection) {
          ratingFormSection.style.display = "none";
        }
      }
    } catch (error) {
      console.error("Error checking user role:", error);
    }
  }

  showApplicantModal(userCode, userName) {
    // Create modal if it doesn't exist
    let modal = document.getElementById("applicantModal");
    if (!modal) {
      modal = this.createApplicantModal();
      document.body.appendChild(modal);
    }
    //Close the existing dropdown menu if open
    const existingMenu = document.querySelector('.actions-dropdown');
    if (existingMenu) {
      if (existingMenu._closeListener) {
        document.removeEventListener('click', existingMenu._closeListener);
      }
      existingMenu.remove();
    }

    // Update modal content
    document.getElementById("modalApplicantName").textContent = userName;
    document.getElementById("modalUserCode").textContent = Math.floor(
      parseFloat(userCode)
    );

    // Find the student number from the applicant data
    const applicant = this.allApplicants.find(
      (app) => app.user_code === userCode
    );
    const studentNumber =
      applicant &&
      applicant.student_number &&
      applicant.student_number !== "NaN"
        ? Math.floor(parseFloat(applicant.student_number))
        : "N/A";
    document.getElementById("modalStudentNumber").textContent = studentNumber;

    // Set current user code for the modal
    modal.dataset.currentUserCode = userCode;

    // Show modal
    modal.classList.remove("hidden");
    modal.classList.add("flex");

    // Load applicant info and ratings
    this.loadApplicantInfo(userCode);

    // Show Applicant Info tab by default
    this.showTab("applicant-info");

    this.loadRatings(userCode);

    this.loadPrerequisitesSummary(userCode);

    this.loadMyRating(userCode);

    // Update rating form for viewers
    this.updateRatingFormForViewer();

    this.loadTestScores(userCode);

    this.loadInstitutionInfo(userCode);

    this.loadApplicationStatus(userCode);

    this.loadPrerequisites(userCode);

    this.loadScholarship(userCode);

    this.loadStatusHistory(userCode);
  }
  

  createApplicantModal() {
    const modal = document.createElement("div");
    modal.id = "applicantModal";
    modal.className =
      "fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50";

    modal.innerHTML = `
    <div class="relative top-2 mx-auto p-6 border w-11/12 max-w-6xl max-h-[96vh] shadow-lg rounded-lg bg-white mb-2 flex flex-col">
     <!-- Modal Header -->
      <div class="flex items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <h3 class="text-xl font-semibold text-gray-900" id="modalApplicantName">Applicant Details</h3>
          <div class="text-sm text-gray-500 space-y-1">
            <p>User Code: <span id="modalUserCode"></span></p>
            <p>Student Number: <span id="modalStudentNumber"></span></p>
          </div>
        </div>
        <button class="modal-close text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Tabs Navigation -->
      <div class="border-b border-gray-200 mt-4">
        <nav class="flex space-x-4 overflow-x-auto scrollbar-hide">
          <button class="tab-button py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0 active" data-tab="applicant-info">
            Applicant Info
          </button>
          <button class="tab-button py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap flex-shrink-0" data-tab="institution-info">
            Institution Info
          </button>
          <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="test-scores">
            Test Scores
          </button>
          <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="prerequisite-courses">
            Prerequisites
          </button>
          <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="comments-ratings">
            Comments & Ratings
          </button>
          <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="status-tab">
            Status: <span id="statusTabLabel">Not Reviewed</span>
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="mt-6 flex-1 flex flex-col overflow-hidden">
        <!-- Applicant Info Tab -->
        <div id="applicant-info" class="tab-content hidden h-full overflow-y-auto">
          <div id="applicantInfoContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading applicant information...
            </div>
          </div>
        </div>

        <!-- Institution Info Tab -->
        <div id="institution-info" class="tab-content hidden h-full overflow-y-auto">
          <div id="institutionInfoContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading institution information...
            </div>
          </div>
        </div>

        <!-- Test Scores Tab -->
        <div id="test-scores" class="tab-content hidden h-full overflow-y-auto">
          <div id="testScoresContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading test scores...
            </div>
          </div>
        </div>

        <!-- Prerequisites Tab -->
        <div id="prerequisite-courses" class="tab-content hidden h-full overflow-y-auto">
          <div class="pr-2">
            <div class="mb-6">
              <!-- Feedback Message Area -->
              <div id="prerequisitesFeedback" class="hidden mb-4 p-3 rounded-lg flex items-center">
                <svg class="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <span id="prerequisitesFeedbackText" class="text-sm font-medium"></span>
              </div>
              
              <!-- Overall GPA Section -->
              <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path>
                </svg>
                Overall GPA
              </h4>

              <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 mb-6">
                <div class="flex items-center gap-3">
                  <label class="text-sm font-medium text-gray-700">Overall GPA:</label>
                    <input
                      type="text"
                      id="overallGpa"
                      class="w-128 px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue"
                      placeholder="Enter GPA"
                    />
                </div>
              </div>
              <!-- Prerequisite Courses Section -->
              <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
                </svg>
                Prerequisite Courses
              </h4>
              
              <div id="prerequisiteCoursesContainer" class="space-y-4">
                <!-- Computer Science -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Computer Science:</label>
                  <textarea
                    id="prerequisiteCs"
                    class="single-line-scrollable flex-1 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none"
                    placeholder="Enter review of Computer Science prerequisite courses"
                  ></textarea>
                </div>

                <!-- Statistics -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Statistics:</label>
                  <textarea
                    id="prerequisiteStat"
                    class="single-line-scrollable flex-1 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none"
                    placeholder="Enter review of Statistics prerequisite courses"
                  ></textarea>
                </div>

                <!-- Math -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Math:</label>
                  <textarea
                    id="prerequisiteMath"
                    class="single-line-scrollable flex-1 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none"
                    placeholder="Enter review of Math prerequisite courses"
                  ></textarea>
                </div>

                <!-- Additional Comments -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Additional Comments (e.g., Reference Letter):</label>
                  <textarea
                    id="additionalComments"
                    class="single-line-scrollable flex-1 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none"
                    placeholder="Enter Additional Comments"
                  ></textarea>
                </div>

               <!-- Applied to Section -->
              <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                <label class="block text-sm font-medium text-gray-700 mb-3">Applied to</label>
                <div class="flex gap-12">
                  <!-- UBC-V -->
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-medium text-gray-700 min-w-[60px]">UBC-V</span>
                    <div class="flex gap-4">
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsV" value="Yes" class="mr-1.5" />
                        <span class="text-sm">Yes</span>
                      </label>
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsV" value="No" class="mr-1.5" checked />
                        <span class="text-sm">No</span>
                      </label>
                    </div>
                  </div>
                  
                  <!-- UBC-O -->
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-medium text-gray-700 min-w-[60px]">UBC-O</span>
                    <div class="flex gap-4">
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsO" value="Yes" class="mr-1.5" checked />
                        <span class="text-sm">Yes</span>
                      </label>
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsO" value="No" class="mr-1.5" />
                        <span class="text-sm">No</span>
                      </label>
                    </div>
                  </div>
                  
                  <!-- UBC-CL -->
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-medium text-gray-700 min-w-[60px]">UBC-CL</span>
                    <div class="flex gap-4">
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsCL" value="Yes" class="mr-1.5" />
                        <span class="text-sm">Yes</span>
                      </label>
                      <label class="flex items-center cursor-pointer">
                        <input type="radio" name="mdsCL" value="No" class="mr-1.5" checked />
                        <span class="text-sm">No</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>

                <!-- Status Selection -->
                <div class="mt-6">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Application Status</label>
                  <select id="prereqStatusSelect" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                    <option value="Not Reviewed">Not Reviewed</option>
                    <option value="Reviewed by PPA">Reviewed by PPA</option>
                    <option value="Need Jeff's Review">Need Jeff's Review</option>
                    <option value="Need Khalad's Review">Need Khalad's Review</option>
                    <option value="Waitlist">Waitlist</option>
                    <option value="Declined">Declined</option>
                    <option value="Send Offer to CoGS">Send Offer to CoGS</option>
                    <option value="Offer Sent to CoGS">Offer Sent to CoGS</option>
                    <option value="Offer Sent to Student">Offer Sent to Student</option>
                    <option value="Offer Accepted">Offer Accepted</option>
                    <option value="Offer Declined">Offer Declined</option>
                  </select>
                </div>

                <!-- Save Button -->
                <div class="flex gap-3 mt-6">
                  <button
                    id="saveAllPrerequisitesBtn"
                    class="px-4 py-2 bg-ubc-blue text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    Save All Prerequisites
                  </button>
                  <button
                    id="clearPrerequisitesBtn"
                    class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments & Ratings Tab -->
        <div id="comments-ratings" class="tab-content h-full overflow-y-auto">
          <div class="pr-2">

            <!-- Summary of Prerequisites Section -->
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200 mb-6">
              <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                Summary of Prerequisites
              </h4>
              <div class="space-y-3 text-sm">
                <div>
                  <span class="font-semibold text-gray-700">Overall CGPA:</span>
                  <span class="text-gray-900 ml-2" id="summaryGpa">-</span>
                </div>
                <div>
                  <span class="font-semibold text-gray-700">CS Prerequisite:</span>
                  <span class="text-gray-900 ml-2" id="summaryCs">-</span>
                </div>
                <div>
                  <span class="font-semibold text-gray-700">Stat Prerequisite:</span>
                  <span class="text-gray-900 ml-2" id="summaryStat">-</span>
                </div>
                <div>
                  <span class="font-semibold text-gray-700">Math Prerequisite:</span>
                  <span class="text-gray-900 ml-2" id="summaryMath">-</span>
                </div>
                <div>
                  <span class="font-semibold text-gray-700">Additional Comments:</span>
                  <span class="text-gray-900 ml-2" id="summaryAdditionalComments">-</span>
                </div>
              </div>
            </div>

            <!-- Add/Edit Rating Section -->
            <div id="ratingFormSection" class="bg-blue-50 p-6 rounded-lg border border-blue-200 mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">Your Rating & Comment</h4>
              <div class="space-y-4">
                <div class="flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Rating (0.0 - 10.0):</label>
                  <input type="number" id="ratingInput" min="0.0" max="10.0" step="0.1" class="input-ubc flex-1" placeholder="Enter a rating between 0.0 and 10.0">
                </div>
                <div class="flex items-center gap-4">
                  <label class="text-sm font-medium text-gray-700 whitespace-nowrap">Comment:</label>
                  <textarea id="commentTextarea" class="single-line-scrollable flex-1 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none" placeholder="Add your comments about this applicant..."></textarea>
                </div>
              </div>
            </div>

           <!-- Scholarship Section -->
          <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 mb-6">
            <div class="flex items-center gap-4 mb-3">
              <h4 class="text-base font-semibold text-ubc-blue whitespace-nowrap">Offer Scholarship:</h4>
              <div class="flex items-center gap-4">
                <label class="flex items-center cursor-pointer">
                  <input type="radio" name="scholarship" value="Yes" class="w-4 h-4 text-ubc-blue focus:ring-ubc-blue">
                  <span class="ml-2 text-gray-700">Yes</span>
                </label>
                <label class="flex items-center cursor-pointer">
                  <input type="radio" name="scholarship" value="No" class="w-4 h-4 text-ubc-blue focus:ring-ubc-blue">
                  <span class="ml-2 text-gray-700">No</span>
                </label>
                <label class="flex items-center cursor-pointer">
                  <input type="radio" name="scholarship" value="Undecided" class="w-4 h-4 text-ubc-blue focus:ring-ubc-blue" checked>
                  <span class="ml-2 text-gray-700">Undecided</span>
                </label>
              </div>
            </div>
          </div>

            <!-- Application Status Section -->
            <div class="mt-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">Application Status</label>
              <select id="ratingsStatusSelect" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                <option value="Not Reviewed">Not Reviewed</option>
                <option value="Reviewed by PPA">Reviewed by PPA</option>
                <option value="Need Jeff's Review">Need Jeff's Review</option>
                <option value="Need Khalad's Review">Need Khalad's Review</option>
                <option value="Waitlist">Waitlist</option>
                <option value="Declined">Declined</option>
                <option value="Send Offer to CoGS">Send Offer to CoGS</option>
                <option value="Offer Sent to CoGS">Offer Sent to CoGS</option>
                <option value="Offer Sent to Student">Offer Sent to Student</option>
                <option value="Offer Accepted">Offer Accepted</option>
                <option value="Offer Declined">Offer Declined</option>
              </select>
            </div>

            <!-- Save All Button -->
            <div class="flex gap-3 mt-6">
              <button
                id="saveAllRatingsBtn"
                class="px-4 py-2 bg-ubc-blue text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Save All
              </button>
              <button
                id="clearRatingBtn"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
              >
                Clear
              </button>
            </div>

            <!-- All Ratings Section -->
            <div class="mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">All Ratings & Comments</h4>
              <div id="ratingsContainer" class="space-y-3">
                <div class="text-center py-8 text-gray-500">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
                  Loading ratings...
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Status Tab -->
        <div id="status-tab" class="tab-content hidden h-full overflow-y-auto">
          <div class="pr-2">
            <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
              <h4 class="text-lg font-semibold text-ubc-blue mb-6 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Application Status Management
              </h4>
              
              <!-- Current Status Display -->
              <div class="mb-6">
                <div class="bg-white rounded-lg p-4 border border-blue-200 shadow-sm">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-gray-600 mb-1">Current Status</p>
                      <p class="text-lg font-bold text-gray-900" id="currentStatusDisplay">Not Reviewed</p>
                    </div>
                    <div class="flex items-center">
                      <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium" id="currentStatusBadge">
                        <div class="w-2 h-2 rounded-full mr-2" id="currentStatusDot"></div>
                        <span id="currentStatusText">Not Reviewed</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Status Change Section -->
              <div id="statusChangeSection">
                <div class="border-t border-blue-200 pt-6">
                  <h5 class="text-md font-semibold text-gray-800 mb-4 flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                    </svg>
                    Change Status
                  </h5>
                  
                  <div class="space-y-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-2">Select New Status</label>
                      <div id="statusDropdownContainer">
                        <select id="statusSelect" class="input-ubc w-full text-base">
                          <option value="Not Reviewed">Not Reviewed</option>
                          <option value="Reviewed by PPA">Reviewed by PPA</option>
                          <option value="Need Jeff's Review">Need Jeff's Review</option>
                          <option value="Need Khalad's Review">Need Khalad's Review</option>
                          <option value="Waitlist">Waitlist</option>
                          <option value="Declined">Declined</option>
                          <option value="Send Offer to CoGS">Send Offer to CoGS</option>
                          <option value="Offer Sent to CoGS">Offer Sent to CoGS</option>
                          <option value="Offer Sent to Student">Offer Sent to Student</option>
                          <option value="Offer Accepted">Offer Accepted</option>
                          <option value="Offer Declined">Offer Declined</option>
                        </select>
                      </div>
                    </div>

                    <!-- Preview Section -->
                    <div id="statusPreview" class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 hidden">
                      <div class="flex items-center">
                        <svg class="w-4 h-4 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span class="text-sm text-yellow-800">
                          <span class="font-medium">Preview:</span> 
                          <span id="currentStatusPreview">Not Reviewed</span> 
                          <span class="mx-2">→</span> 
                          <span class="font-semibold" id="newStatusPreview">Not Reviewed</span>
                        </span>
                      </div>
                    </div>

                    <div id="statusUpdateButtons" class="flex gap-3 pt-2">
                      <button id="updateStatusBtn" class="btn-ubc flex items-center">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        Update Status
                      </button>
                      <button id="cancelStatusBtn" class="btn-ubc-outline">Cancel</button>
                    </div>

                    <div class="border-t border-blue-200 pt-6 mt-6">
                      <div class="flex items-center justify-between mb-4">
                        <h5 class="text-md font-semibold text-gray-800 flex items-center">
                          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                          </svg>
                          Status History
                        </h5>
                        <span id="statusHistoryCount" class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          Showing recent 5 changes
                        </span>
                      </div>
                
                      <div id="statusHistoryContainer" class="space-y-3">
                        <div class="text-center py-4 text-gray-500">
                          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-ubc-blue mx-auto mb-2"></div>
                            Loading status history...
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  `;

    // Add event listeners
    modal.querySelector(".modal-close").addEventListener("click", () => {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    });

    // Tab switching - handle clicks on both button and nested elements
    modal.addEventListener("click", (e) => {
      // Check if the clicked element is a tab button or inside a tab button
      const tabButton = e.target.closest(".tab-button");
      if (tabButton) {
        const tabName = tabButton.dataset.tab;
        this.showTab(tabName);
      }
    });

    // Rating form handlers
    modal.querySelector("#saveAllRatingsBtn")?.addEventListener("click", () => {
      this.saveAllRatings();
    });

    modal.querySelector("#clearRatingBtn").addEventListener("click", () => {
      this.clearRatingForm();
    });

    modal.querySelector("#updateStatusBtn").addEventListener("click", () => {
      this.updateStatus();
    });

    modal.querySelector("#cancelStatusBtn").addEventListener("click", () => {
      this.loadApplicationStatus(modal.dataset.currentUserCode);
    });

    // Close modal when clicking outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
      }
    });
    
    const savePrereqBtn = modal.querySelector("#saveAllPrerequisitesBtn");
    const clearPrereqBtn = modal.querySelector("#clearPrerequisitesBtn");

    if (savePrereqBtn) {
      savePrereqBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.savePrerequisiteCourses();
      });
    }

    if (clearPrereqBtn) {
      clearPrereqBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.clearPrerequisites();
      });
    }

    return modal;
  }

  showTab(tabName) {
    const modal = document.getElementById("applicantModal");

    // Update tab buttons
    modal.querySelectorAll(".tab-button").forEach((btn) => {
      if (btn.dataset.tab === tabName) {
        btn.classList.add("active", "border-ubc-blue", "text-ubc-blue");
        btn.classList.remove("border-transparent", "text-gray-500");
      } else {
        btn.classList.remove("active", "border-ubc-blue", "text-ubc-blue");
        btn.classList.add("border-transparent", "text-gray-500");
      }
    });

    // Update tab content
    modal.querySelectorAll(".tab-content").forEach((content) => {
      if (content.id === tabName) {
        content.classList.remove("hidden");
      } else {
        content.classList.add("hidden");
      }
    });

    // If showing prerequisites tab, update permissions
    if (tabName === "prerequisite-courses") {
      this.updatePrerequisitesFormPermissions();
    }
  }

  async loadRatings(userCode) {
    try {
      const response = await fetch(`/api/ratings/${userCode}`);
      const result = await response.json();

      const container = document.getElementById("ratingsContainer");

      if (result.success && result.ratings.length > 0) {
        container.innerHTML = result.ratings
          .map(
            (rating) => `
          <div class="rating-card-container">
            <div class="rating-card-header">
              <div class="rating-user-avatar">
                <span class="text-white font-semibold text-xs">${
                  rating.first_name[0]
                }${rating.last_name[0]}</span>
              </div>
              <div class="rating-user-details">
                <p class="font-medium text-gray-900">${rating.first_name} ${
              rating.last_name
            }</p>
                <p class="text-sm text-gray-500">${rating.email}</p>
              </div>
              <div class="rating-score">
                <span class="text-lg font-bold text-ubc-blue">${parseFloat(
                  rating.rating
                ).toFixed(1)}</span>
                <span class="text-sm text-gray-500">/10.0</span>
              </div>
            </div>
            ${
              rating.user_comment
                ? `
              <div class="rating-comment-container">
                <div class="rating-comment-content">
                  ${rating.user_comment}
                </div>
              </div>
            `
                : ""
            }
          </div>
        `
          )
          .join("");
      } else {
        container.innerHTML = `
          <div class="text-center py-8 text-gray-500">
            <p>No ratings yet.</p>
          </div>
        `;
      }
    } catch (error) {
      document.getElementById("ratingsContainer").innerHTML = `
        <div class="text-center py-8 text-red-500">
          <p>Error loading ratings: ${error.message}</p>
        </div>
      `;
    }
  }

  async loadPrerequisitesSummary(userCode) {
    try {
      const response = await fetch(`/api/applicant-application-info/${userCode}`);
      const result = await response.json();

      if (result.success && result.application_info) {
        const appInfo = result.application_info;
        document.getElementById("summaryGpa").textContent = appInfo.gpa || "Not Provided";
        document.getElementById("summaryCs").textContent = appInfo.cs || "Not Provided";
        document.getElementById("summaryStat").textContent = appInfo.stat || "Not Provided";
        document.getElementById("summaryMath").textContent = appInfo.math || "Not Provided";
        document.getElementById("summaryAdditionalComments").textContent = appInfo.additional_comments || "Not Provided";
      } else {
        // Set all to "Not Provided" if no data
        document.getElementById("summaryGpa").textContent = "Not Provided";
        document.getElementById("summaryCs").textContent = "Not Provided";
        document.getElementById("summaryStat").textContent = "Not Provided";
        document.getElementById("summaryMath").textContent = "Not Provided";
        document.getElementById("summaryAdditionalComments").textContent = "Not Provided";
      }
    } catch (error) {
      console.error("Error loading prerequisites summary:", error);
    }
  }

  async loadMyRating(userCode) {
    try {
      const response = await fetch(`/api/ratings/${userCode}/my-rating`);
      const result = await response.json();

      if (result.success && result.rating) {
        document.getElementById("ratingInput").value =
          result.rating.rating || "";
        document.getElementById("commentTextarea").value =
          result.rating.user_comment || "";
      } else {
        // Clear inputs if no rating exists
        document.getElementById("ratingInput").value = "";
        document.getElementById("commentTextarea").value = "";
      }
    } catch (error) {
      console.error("Error loading user rating:", error);
      // Clear inputs on error as well
      document.getElementById("ratingInput").value = "";
      document.getElementById("commentTextarea").value = "";
    }
  }

  async saveAllRatings() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;
    if (!userCode) return;

    const rating = document.getElementById("ratingInput").value.trim();
    const comment = document.getElementById("commentTextarea").value.trim();
    const scholarship = document.querySelector('input[name="scholarship"]:checked').value;
    const status = document.getElementById("ratingsStatusSelect").value;

    // Validate rating if provided
    if (rating) {
      const ratingFloat = parseFloat(rating);
      if (isNaN(ratingFloat) || ratingFloat < 0.0 || ratingFloat > 10.0) {
        this.showMessage("Rating must be between 0.0 and 10.0", "error");
        return;
      }

      // Check decimal places
      if (Math.round(ratingFloat * 10) / 10 !== ratingFloat) {
        this.showMessage("Rating can only have one decimal place", "error");
        return;
      }
    }

    const saveBtn = document.getElementById("saveAllRatingsBtn");
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      // Save rating and comment if provided
      if (rating) {
        const ratingResponse = await fetch(`/api/ratings/${userCode}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            rating: rating,
            comment: comment,
          }),
        });

        const ratingResult = await ratingResponse.json();
        if (!ratingResult.success) {
          this.showMessage(ratingResult.message || "Failed to save rating", "error");
          return;
        }
      }

      // Save scholarship
      const scholarshipResponse = await fetch(`/api/applicant-application-info/${userCode}/scholarship`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ scholarship }),
      });

      const scholarshipResult = await scholarshipResponse.json();
      if (!scholarshipResult.success) {
        this.showMessage(scholarshipResult.message || "Failed to save scholarship", "error");
        return;
      }

      // Update status
      const statusResponse = await fetch(`/api/applicant-application-info/${userCode}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });

      const statusResult = await statusResponse.json();

      if (statusResult.success) {
        this.showMessage("All information saved successfully", "success");

        // Update the status tab label
        const statusTabLabel = document.getElementById("statusTabLabel");
        if (statusTabLabel) {
          statusTabLabel.textContent = status;
        }

        // Sync all status selects across all tabs
        this.syncAllStatusSelects(status);

        // Reload displays
        this.loadApplicationStatus(userCode);
        this.loadRatings(userCode);
        await this.loadStatusHistory(userCode);
        await this.loadApplicants();
      } else {
        this.showMessage("Rating and scholarship saved but failed to update status: " + (statusResult.message || "Unknown error"), "error");
      }
    } catch (error) {
      console.error("Error saving ratings information:", error);
      this.showMessage(`Error saving: ${error.message}`, "error");
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  }


  clearRatingForm() {
    document.getElementById("ratingInput").value = "";
    document.getElementById("commentTextarea").value = "";
  }

  async loadApplicantInfo(userCode) {
    try {
      const response = await fetch(`/api/applicant-info/${userCode}`);
      const result = await response.json();

      const container = document.getElementById("applicantInfoContainer");

      if (result.success && result.applicant) {
        const applicant = result.applicant;

        // NEW CODE - Load application_info data
        const applicationInfoResponse = await fetch(
          `/api/applicant-application-info/${userCode}`
        );
        const applicationInfoResult = await applicationInfoResponse.json();
        const applicationInfo = applicationInfoResult.success
          ? applicationInfoResult.application_info
          : null;

        container.innerHTML = `
          <div class="pr-2">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Personal Information -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  Personal Information
                </h4>
                <div class="space-y-3">
                  ${this.renderInfoField("Title", applicant.title)}
                  ${this.renderInfoField("Family Name", applicant.family_name)}
                  ${this.renderInfoField("Given Name", applicant.given_name)}
                  ${this.renderInfoField("Middle Name", applicant.middle_name)}
                  ${this.renderInfoField(
                    "Preferred Name",
                    applicant.preferred_name
                  )}
                  ${this.renderInfoField(
                    "Former Family Name",
                    applicant.former_family_name
                  )}
                  ${this.renderInfoField(
                    "Date of Birth",
                    applicant.date_birth ? this.formatDate(applicant.date_birth) : null
                  )}
                  ${this.renderInfoField("Gender", applicant.gender)}
                  ${this.renderInfoField(
                    "Age",
                    applicant.age ? `${applicant.age} years old` : null
                  )}
                  ${this.renderInfoField(
                    "Racialized",
                    this.formatYesNo(applicant.racialized)
                  )}
                  ${this.renderInfoField("Email", applicant.email, "email")}
                </div>
              </div>

              <!-- Contact & Address -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  Contact & Address
                </h4>
                <div class="space-y-3">
                  ${this.renderInfoField(
                    "Address Line 1",
                    applicant.address_line1
                  )}
                  ${this.renderInfoField(
                    "Address Line 2",
                    applicant.address_line2
                  )}
                  ${this.renderInfoField("City", applicant.city)}
                  ${this.renderInfoField(
                    "Province/State/Region",
                    applicant.province_state_region
                  )}
                  ${this.renderInfoField("Postal Code", applicant.postal_code)}
                  ${this.renderInfoField("Country", applicant.country)}
                  ${this.renderInfoField(
                    "Primary Telephone",
                    applicant.primary_telephone,
                    "phone"
                  )}
                  ${this.renderInfoField(
                    "Secondary Telephone",
                    applicant.secondary_telephone,
                    "phone"
                  )}
                </div>
              </div>

              <!-- Citizenship & Languages -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"></path>
                  </svg>
                  Citizenship & Languages
                </h4>
                <div class="space-y-3">
                  ${this.renderInfoField(
                    "Country of Birth",
                    applicant.country_birth
                  )}
                  ${this.renderInfoField(
                    "Country of Citizenship",
                    applicant.country_citizenship
                  )}
                  ${this.renderInfoField(
                    "Dual Citizenship",
                    applicant.dual_citizenship
                  )}
                  ${this.renderInfoField(
                    "Canadian Citizen/Resident",
                    applicationInfo && applicationInfo.canadian !== null
                      ? applicationInfo.canadian
                        ? "Yes"
                        : "No"
                      : "Not determined"
                  )}
                  ${this.renderInfoField(
                    "Primary Spoken Language",
                    applicant.primary_spoken_lang
                  )}
                  ${this.renderInfoField(
                    "Other Spoken Language",
                    applicant.other_spoken_lang
                  )}
                  ${this.renderInfoField("Visa Type", applicant.visa_type)}
                </div>
              </div>

              <!-- Academic & Background -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                  </svg>
                  Academic & Background
                </h4>
                <div class="space-y-3">
                  ${this.renderInfoField("Interest", applicant.interest)}
                  ${this.renderInfoField(
                    "Academic History",
                    applicant.academic_history
                  )}
                  ${this.renderInfoField(
                    "UBC Academic History",
                    applicant.ubc_academic_history
                  )}
                </div>
              </div>

              <!-- Aboriginal Information -->
              ${
                this.hasAboriginalInfo(applicant)
                  ? `
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 lg:col-span-2">
                <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                  </svg>
                  Aboriginal Information
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  ${this.renderInfoField(
                    "Aboriginal",
                    this.formatYesNo(applicant.aboriginal)
                  )}
                  ${this.renderInfoField(
                    "First Nation",
                    this.formatYesNo(applicant.first_nation)
                  )}
                  ${this.renderInfoField(
                    "Inuit",
                    this.formatYesNo(applicant.inuit)
                  )}
                  ${this.renderInfoField(
                    "Métis",
                    this.formatYesNo(applicant.metis)
                  )}
                  ${this.renderInfoField(
                    "Aboriginal Not Specified",
                    this.formatYesNo(applicant.aboriginal_not_specified)
                  )}
                  ${
                    applicant.aboriginal_info
                      ? `
                  <div class="md:col-span-2">
                    ${this.renderInfoField(
                      "Aboriginal Info",
                      applicant.aboriginal_info
                    )}
                  </div>
                  `
                      : ""
                  }
                </div>
              </div>
              `
                  : ""
              }

            </div>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="text-center py-8 text-gray-500">
            <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4-4-4m-6 8l4-4 4 4"></path>
            </svg>
            <p class="text-lg font-medium text-gray-600">No applicant information available</p>
          </div>
        `;
      }
    } catch (error) {
      document.getElementById("applicantInfoContainer").innerHTML = `
        <div class="text-center py-8 text-red-500">
          <svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p class="text-lg font-medium">Error loading applicant information</p>
          <p class="text-sm text-gray-600">${error.message}</p>
        </div>
      `;
    }
  }

  async loadTestScores(userCode) {
    try {
      const response = await fetch(`/api/applicant-test-scores/${userCode}`);
      const result = await response.json();

      const container = document.getElementById("testScoresContainer");

      if (result.success && result.test_scores) {
        const scores = result.test_scores;

        const englishStatusResponse = await fetch(
          `/api/applicant-application-info/${userCode}`
        );
        const englishStatusResult = await englishStatusResponse.json();
        const applicationInfo = englishStatusResult.success
          ? englishStatusResult.application_info
          : null;

        container.innerHTML = `
          <div class="pr-2">

          <!-- English Status Management Section -->
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 mb-6">
            <h4 class="text-lg font-semibold text-ubc-blue mb-6 flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              English Language Proficiency Status
            </h4>
            
            <!-- Current Status Display -->
            <div class="mb-6">
              <div class="bg-white rounded-lg p-4 border border-blue-200 shadow-sm">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-600 mb-1">Current English Status</p>
                    <p class="text-lg font-bold text-gray-900" id="currentEnglishStatusDisplay">${
                      applicationInfo?.english_status || "Not Set"
                    }</p>
                  </div>
                  <div class="flex items-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium" id="currentEnglishStatusBadge">
                      <div class="w-2 h-2 rounded-full mr-2" id="currentEnglishStatusDot"></div>
                      <span id="currentEnglishStatusText">${
                        applicationInfo?.english_status || "Not Set"
                      }</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- English Description Display -->
            ${
              applicationInfo?.english_description
                ? `
            <div class="mb-6">
              <div class="bg-white rounded-lg p-4 border border-blue-200 shadow-sm">
                <h5 class="text-sm font-semibold text-ubc-blue mb-2">English Status Description</h5>
                <p class="text-sm text-gray-900" id="englishDescriptionDisplay">${applicationInfo.english_description}</p>
              </div>
            </div>
            `
                : ""
            }

            <!-- English Comment Section -->
            <div class="mb-6">
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h5 class="text-sm font-semibold text-ubc-blue mb-3">English Comment</h5>
                <textarea
                  id="englishCommentTextarea"
                  rows="3"
                  class="w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue resize-none text-sm"
                  placeholder="Add comments about English proficiency status..."
                >${applicationInfo?.english_comment || ""}</textarea>
                <div class="mt-3 flex gap-2">
                  <button
                    id="saveEnglishCommentBtn"
                    class="px-3 py-1.5 bg-ubc-blue text-white text-sm rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    Save Comment
                  </button>
                  <button
                    id="clearEnglishCommentBtn"
                    class="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 transition-colors font-medium"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>

            <!-- Status Change Section -->
            <div id="englishStatusChangeSection">
              <div class="border-t border-blue-200 pt-6">
                <h5 class="text-md font-semibold text-gray-800 mb-4 flex items-center">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                  </svg>
                  Change English Status
                </h5>
                
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Select New English Status</label>
                    <div id="englishStatusDropdownContainer">
                      <select id="englishStatusSelect" class="input-ubc w-full text-base">
                        <option value="Not Met">Not Met</option>
                        <option value="Not Required">Not Required</option>
                        <option value="Passed">Passed</option>
                      </select>
                    </div>
                  </div>

                  <!-- Preview Section -->
                  <div id="englishStatusPreview" class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 hidden">
                    <div class="flex items-center">
                      <svg class="w-4 h-4 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      <span class="text-sm text-yellow-800">
                        <span class="font-medium">Preview:</span> 
                        <span id="currentEnglishStatusPreview">${
                          applicationInfo?.english_status || "Not Set"
                        }</span> 
                        <span class="mx-2">→</span> 
                        <span class="font-semibold" id="newEnglishStatusPreview">${
                          applicationInfo?.english_status || "Not Set"
                        }</span>
                      </span>
                    </div>
                  </div>

                  <div id="englishStatusUpdateButtons" class="flex gap-3 pt-2">
                    <button id="updateEnglishStatusBtn" class="btn-ubc flex items-center" disabled>
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                      </svg>
                      Update English Status
                    </button>
                    <button id="cancelEnglishStatusBtn" class="btn-ubc-outline">Cancel</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- END of English Status Management Section --> 

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              <!-- English Language Tests -->
              <div class="lg:col-span-2">
                <h4 class="text-xl font-semibold text-ubc-blue mb-6 flex items-center">
                  <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path>
                  </svg>
                  English Language Proficiency Tests
                </h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  ${this.renderTOEFLScores(scores.toefl)}
                  ${this.renderIELTSScores(scores.ielts)}
                  ${this.renderSingleTestScore("MELAB", scores.melab, [
                    "ref_num",
                    "date_written",
                    "total",
                  ])}
                  ${this.renderSingleTestScore("PTE", scores.pte, [
                    "ref_num",
                    "date_written",
                    "total",
                  ])}
                  ${this.renderCAELScore(scores.cael)}
                  ${this.renderCELPIPScore(scores.celpip)}
                  ${this.renderAltELPPScore(scores.alt_elpp)}
                  ${this.renderDuolingoScore(scores.duolingo)}
                </div>
              </div>

              <!-- Graduate Tests -->
              <div class="lg:col-span-2">
                <h4 class="text-xl font-semibold text-ubc-blue mb-6 flex items-center mt-8">
                  <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
                  </svg>
                  Graduate Admission Tests
                </h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  ${this.renderGREScore(scores.gre)}
                  ${this.renderGMATScore(scores.gmat)}
                </div>
              </div>
            </div>
          </div>
        `;

        // Update Duolingo permissions after rendering
        setTimeout(() => {
          this.updateDuolingoPermissions();
        }, 100);
        //Set current English status in dropdown and setup handlers
        if (applicationInfo?.english_status) {
          document.getElementById("englishStatusSelect").value =
            applicationInfo.english_status;
          this.updateEnglishStatusBadge(applicationInfo.english_status);
        }

        //Setup English status preview and event handlers
        this.setupEnglishStatusPreview(
          applicationInfo?.english_status || "Not Set"
        );
        this.updateEnglishStatusFormPermissions();
        this.setupEnglishCommentHandlers();
      } else {
        container.innerHTML = `
          <div class="text-center py-12 text-gray-500">
            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <h3 class="text-lg font-medium text-gray-600 mb-2">No Test Scores Available</h3>
            <p class="text-sm">This applicant has not submitted any test scores yet.</p>
          </div>
        `;
      }
    } catch (error) {
      document.getElementById("testScoresContainer").innerHTML = `
        <div class="text-center py-12 text-red-500">
          <svg class="w-16 h-16 text-red-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <h3 class="text-lg font-medium">Error Loading Test Scores</h3>
          <p class="text-sm text-gray-600 mt-2">${error.message}</p>
        </div>
      `;
    }
  }

  renderTOEFLScores(toeflScores) {
    if (!toeflScores || toeflScores.length === 0) {
      return this.renderEmptyTestCard("TOEFL");
    }

    return toeflScores
      .map(
        (score, index) => `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3 flex items-center">
          <span class="bg-blue-600 text-white text-xs px-2 py-1 rounded-full mr-2">${
            index + 1
          }</span>
          TOEFL ${toeflScores.length > 1 ? `Test ${index + 1}` : ""}
        </h5>
        <div class="space-y-2">
          ${this.renderScoreField("Registration #", score.registration_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          ${this.renderScoreField("Total Score", score.total_score, true)}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Listening", score.listening)}
            ${this.renderScoreField("Reading", score.reading)}
            ${this.renderScoreField("Writing", score.structure_written)}
            ${this.renderScoreField("Speaking", score.speaking)}
          </div>
          ${
            score.mybest_total
              ? `
            <div class="pt-2 border-t border-blue-200">
              <p class="text-xs font-medium text-blue-800 mb-2">MyBest Scores</p>
              ${this.renderScoreField("MyBest Total", score.mybest_total, true)}
              ${this.renderScoreField(
                "MyBest Date",
                this.formatDate(score.mybest_date)
              )}
            </div>
          `
              : ""
          }
        </div>
      </div>
    `
      )
      .join("");
  }

  renderIELTSScores(ieltsScores) {
    if (!ieltsScores || ieltsScores.length === 0) {
      return this.renderEmptyTestCard("IELTS");
    }

    return ieltsScores
      .map(
        (score, index) => `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3 flex items-center">
          <span class="bg-blue-600 text-white text-xs px-2 py-1 rounded-full mr-2">${
            index + 1
          }</span>
          IELTS ${ieltsScores.length > 1 ? `Test ${index + 1}` : ""}
        </h5>
        <div class="space-y-2">
          ${this.renderScoreField("Candidate #", score.candidate_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          ${this.renderScoreField(
            "Total Band Score",
            score.total_band_score,
            true
          )}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Listening", score.listening)}
            ${this.renderScoreField("Reading", score.reading)}
            ${this.renderScoreField("Writing", score.writing)}
            ${this.renderScoreField("Speaking", score.speaking)}
          </div>
        </div>
      </div>
    `
      )
      .join("");
  }

  renderSingleTestScore(testName, score, fields) {
    if (!score) {
      return this.renderEmptyTestCard(testName);
    }

    // CHANGE THIS: Use the same blue design for all tests
    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">${testName}</h5>
        <div class="space-y-2">
          ${fields
            .map((field) => {
              const value =
                field === "date_written"
                  ? this.formatDate(score[field])
                  : score[field];
              const isMainScore = field === "total";
              const label = field
                .replace(/_/g, " ")
                .replace(/\b\w/g, (l) => l.toUpperCase());
              return this.renderScoreField(label, value, isMainScore);
            })
            .join("")}
        </div>
      </div>
    `;
  }

  renderCAELScore(score) {
    if (!score) {
      return this.renderEmptyTestCard("CAEL");
    }

    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">CAEL</h5>
        <div class="space-y-2">
          ${this.renderScoreField("Reference #", score.ref_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Reading", score.reading)}
            ${this.renderScoreField("Listening", score.listening)}
            ${this.renderScoreField("Writing", score.writing)}
            ${this.renderScoreField("Speaking", score.speaking)}
          </div>
        </div>
      </div>
    `;
  }

  renderCELPIPScore(score) {
    if (!score) {
      return this.renderEmptyTestCard("CELPIP");
    }

    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">CELPIP</h5>
        <div class="space-y-2">
          ${this.renderScoreField("Reference #", score.ref_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Listening", score.listening)}
            ${this.renderScoreField("Speaking", score.speaking)}
            ${this.renderScoreField("Reading & Writing", score.reading_writing)}
          </div>
        </div>
      </div>
    `;
  }

  renderAltELPPScore(score) {
    if (!score) {
      return this.renderEmptyTestCard("ALT ELPP");
    }

    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">ALT ELPP</h5>
        <div class="space-y-2">
          ${this.renderScoreField("Reference #", score.ref_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          ${this.renderScoreField("Total Score", score.total, true)}
          ${this.renderScoreField("Test Type", score.test_type)}
        </div>
      </div>
    `;
  }

  renderDuolingoScore(score) {
    // Count date_written too so the input pre-fills even when only a date exists
    const hasScore =
      score && (score.score || score.description || score.date_written);

    // current values & validity for initial render
    const scoreValue = score && score.score != null ? String(score.score) : "";
    const dateValue =
      score && score.date_written
        ? this.formatDateForInput(score.date_written)
        : "";

    const scoreInvalid = scoreValue
      ? !this.isValidDuolingoScore(scoreValue)
      : false;
    const dateInvalid = dateValue ? this.isFutureYMD(dateValue) : false;

    return `
    <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">

      <h5 class="font-semibold text-blue-900 mb-3 flex items-center justify-between">
        Duolingo
        ${
          hasScore
            ? ""
            : '<span class="text-xs text-blue-600 italic">No information entered</span>'
        }
      </h5>
      <div class="space-y-3">
        ${
          hasScore
            ? `
          <div class="space-y-2">
            ${
              score.score
                ? this.renderScoreField("Score", score.score, true)
                : ""
            }
            ${
              score.date_written
                ? this.renderScoreField(
                    "Date Written",
                    this.formatDate(score.date_written)
                  )
                : ""
            }
            ${
              score.description
                ? `
              <div class="bg-white rounded p-2 border border-blue-200">
                <span class="text-xs font-medium text-gray-700 block mb-1">Description:</span>
                <span class="text-sm text-gray-700">${score.description}</span>
              </div>
            `
                : ""
            }
          </div>
        `
            : ""
        }

        <!-- Input Section (will be hidden/disabled based on permissions) -->
        <div id="duolingoInputSection" class="bg-white rounded-lg p-3 border border-blue-200">
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Score (0-160):</label>
              <input
                type="number"
                id="duolingoScoreInput"
                class="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-500
                       ${
                         scoreInvalid
                           ? "border-red-500 ring-1 ring-red-500 focus:ring-red-500"
                           : "border-gray-300"
                       }"
                placeholder="Enter Duolingo score"
                min="0"
                max="160"
                value="${hasScore && score.score != null ? score.score : ""}"
                oninput="window.applicantsManager.updateDuolingoValidity()"
              />
              <p id="duo-score-error" class="mt-1 text-xs text-red-600 ${
                scoreInvalid ? "" : "hidden"
              }">
                Score must be between 0 and 160.
              </p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Description:</label>
              <textarea
                id="duolingoDescriptionInput"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                rows="2"
                placeholder="Enter description or notes"
              >${
                hasScore && score.description ? score.description : ""
              }</textarea>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Date Written:</label>
              <input
                type="date"
                id="duolingoDateInput"
                class="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-500
                       ${
                         dateInvalid
                           ? "border-red-500 ring-1 ring-red-500 focus:ring-red-500"
                           : "border-gray-300"
                       }"
                value="${
                  hasScore && score.date_written
                    ? this.formatDateForInput(score.date_written)
                    : ""
                }"
                oninput="window.applicantsManager.updateDuolingoValidity()"
              />
              <p id="duo-date-error" class="mt-1 text-xs text-red-600 ${
                dateInvalid ? "" : "hidden"
              }">
                Date cannot be in the future.
              </p>
            </div>

            <button
              id="saveDuolingoBtn"
              class="w-full px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors font-medium
                     disabled:opacity-50 disabled:cursor-not-allowed"
              ${scoreInvalid || dateInvalid ? "disabled" : ""}
              onclick="window.applicantsManager.saveDuolingoScore()"
            >
              Save Duolingo Score
            </button>
          </div>
        </div>
      </div>
    </div>
    `;
  }

  async updateDuolingoPermissions() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      const inputSection = document.getElementById("duolingoInputSection");
      const scoreInput = document.getElementById("duolingoScoreInput");
      const descriptionInput = document.getElementById(
        "duolingoDescriptionInput"
      );
      const dateInput = document.getElementById("duolingoDateInput");
      const saveBtn = document.getElementById("saveDuolingoBtn");

      if (result.authenticated && result.user?.role === "Admin") {
        // Admin can edit everything
        if (inputSection) inputSection.style.display = "block";
        if (scoreInput) scoreInput.disabled = false;
        if (descriptionInput) descriptionInput.disabled = false;
        if (dateInput) dateInput.disabled = false;
        if (saveBtn) saveBtn.style.display = "block";
      } else {
        // Faculty and Viewers can only view
        if (inputSection) inputSection.style.display = "none";
        if (scoreInput) scoreInput.disabled = true;
        if (descriptionInput) descriptionInput.disabled = true;
        if (dateInput) dateInput.disabled = true;
        if (saveBtn) saveBtn.style.display = "none";
      }
    } catch (error) {
      console.error("Error checking user permissions:", error);
      // Hide inputs on error to be safe
      const inputSection = document.getElementById("duolingoInputSection");
      if (inputSection) inputSection.style.display = "none";
    }
  }

  async saveDuolingoScore() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;

    if (!userCode) {
      this.showMessage("No user selected", "error");
      return;
    }

    const scoreInput = document.getElementById("duolingoScoreInput");
    const descriptionInput = document.getElementById(
      "duolingoDescriptionInput"
    );
    const dateInput = document.getElementById("duolingoDateInput");
    const saveBtn = document.getElementById("saveDuolingoBtn");

    const score = scoreInput.value.trim();
    const description = descriptionInput.value.trim();
    const dateWritten = dateInput.value.trim();

    // Validate score if provided
    if (score) {
      const scoreNum = parseInt(score);
      if (isNaN(scoreNum) || scoreNum < 0 || scoreNum > 160) {
        this.showMessage("Duolingo score must be between 0 and 160", "error");
        return;
      }
    }

    // Validate date if provided
    if (dateWritten) {
      // Parse date as local date to avoid timezone issues
      const dateParts = dateWritten.split("-");
      if (dateParts.length !== 3) {
        this.showMessage("Please enter a valid date", "error");
        return;
      }

      const year = parseInt(dateParts[0]);
      const month = parseInt(dateParts[1]) - 1; // Month is 0-indexed
      const day = parseInt(dateParts[2]);
      const selectedDate = new Date(year, month, day);

      if (isNaN(selectedDate.getTime())) {
        this.showMessage("Please enter a valid date", "error");
        return;
      }

      const today = new Date();
      today.setHours(23, 59, 59, 999); // Set to end of today

      if (selectedDate > today) {
        this.showMessage("Date cannot be in the future", "error");
        return;
      }
    }

    // Save button loading state
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const response = await fetch(`/api/duolingo-score/${userCode}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          score: score || null,
          description: description || null,
          date_written: dateWritten || null,
        }),
      });

      const result = await response.json();

      if (result.success) {
        this.showMessage("Duolingo score saved successfully", "success");
        // Reload test scores to show updated data
        this.loadTestScores(userCode);
      } else {
        this.showMessage(
          result.message || "Failed to save Duolingo score",
          "error"
        );
      }
    } catch (error) {
      this.showMessage(
        `Error saving Duolingo score: ${error.message}`,
        "error"
      );
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  }

  renderGREScore(score) {
    if (!score) {
      return this.renderEmptyTestCard("GRE");
    }

    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">GRE</h5>
        <div class="space-y-2">
          ${this.renderScoreField("Registration #", score.reg_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Verbal Reasoning", score.verbal)}
            ${this.renderScoreField(
              "Quantitative Reasoning",
              score.quantitative
            )}
            ${this.renderScoreField("Analytical Writing", score.writing)}
          </div>
          ${
            score.verbal_below ||
            score.quantitative_below ||
            score.writing_below
              ? `
            <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
              ${
                score.verbal_below
                  ? this.renderScoreField(
                      "Verbal Reasoning % Below",
                      score.verbal_below
                    )
                  : ""
              }
              ${
                score.quantitative_below
                  ? this.renderScoreField(
                      "Quantitative Reasoning % Below",
                      score.quantitative_below
                    )
                  : ""
              }
              ${
                score.writing_below
                  ? this.renderScoreField(
                      "Analytical Writing % Below",
                      score.writing_below
                    )
                  : ""
              }
            </div>
          `
              : ""
          }
          ${
            score.subject_tests
              ? `
            <div class="pt-2 border-t border-blue-200">
              <p class="text-xs font-medium text-blue-800 mb-2">Subject Test</p>
              ${this.renderScoreField("Subject Tests", score.subject_tests)}
              ${
                score.subject_scaled_score
                  ? this.renderScoreField(
                      "Subject Scaled Score",
                      score.subject_scaled_score
                    )
                  : ""
              }
              ${
                score.subject_below
                  ? this.renderScoreField(
                      "Subject % Below",
                      score.subject_below
                    )
                  : ""
              }
            </div>
          `
              : ""
          }
        </div>
      </div>
    `;
  }

  renderGMATScore(score) {
    if (!score) {
      return this.renderEmptyTestCard("GMAT");
    }

    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
        <h5 class="font-semibold text-blue-900 mb-3">GMAT</h5>
        <div class="space-y-2">
          ${this.renderScoreField("Reference #", score.ref_num)}
          ${this.renderScoreField(
            "Date Written",
            this.formatDate(score.date_written)
          )}
          ${this.renderScoreField("Total Score", score.total, true)}
          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-blue-200">
            ${this.renderScoreField("Quantitative", score.quantitative)}
            ${this.renderScoreField("Verbal", score.verbal)}
            ${this.renderScoreField(
              "Integrated Reasoning",
              score.integrated_reasoning
            )}
            ${this.renderScoreField("Writing", score.writing)}
          </div>
        </div>
      </div>
    `;
  }

  renderScoreField(label, value, isHighlight = false) {
    if (!value || value === "null" || value === "undefined") {
      return `
        <div class="flex justify-between items-center">
          <span class="text-xs font-medium opacity-70">${label}:</span>
          <span class="text-xs opacity-50 italic">N/A</span>
        </div>
      `;
    }

    const highlightClass = isHighlight ? "font-bold text-lg" : "text-sm";

    return `
      <div class="flex justify-between items-start gap-2">
        <span class="text-xs font-medium opacity-70 flex-shrink-0">${label}:</span>
        <span class="${highlightClass} font-semibold break-all text-right max-w-[60%]">${value}</span>
      </div>
    `;
  }

  renderEmptyTestCard(testName) {
    return `
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200 opacity-60">
        <h5 class="font-semibold text-blue-900 mb-3">${testName}</h5>
        <div class="text-center py-4">
          <p class="text-xs text-blue-500 italic">No ${testName} scores submitted</p>
        </div>
      </div>
    `;
  }

  // Format "display" dates without timezone drift
  formatDate(dateString) {
    if (!dateString) return null;
    try {
      // 1) yyyy-MM-dd (treat as a date-only in UTC)
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateString.trim())) {
        const [y, m, d] = dateString.trim().split("-").map(Number);
        const utc = new Date(Date.UTC(y, m - 1, d));
        return utc.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          timeZone: "UTC",
        });
      }

      // 2) RFC/GMT strings — format using UTC components
      if (dateString.includes("GMT") || dateString.includes("UTC")) {
        const dt = new Date(dateString);
        if (!isNaN(dt.getTime())) {
          return dt.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            timeZone: "UTC",
          });
        }
      }

      // 3) Fallback: best effort
      const dt = new Date(dateString);
      return isNaN(dt.getTime())
        ? dateString
        : dt.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
          });
    } catch {
      return dateString;
    }
  }

  // Format specifically for <input type="date"> → "yyyy-MM-dd" (UTC-safe)
  formatDateForInput(dateString) {
    if (!dateString) return "";

    const s = String(dateString).trim();

    // Already correct for <input type="date">
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;

    // Parse any RFC/ISO/GMT string, then take the UTC y-m-d so midnight UTC
    // doesn't shift a day in local time.
    const dt = new Date(s);
    if (!isNaN(dt.getTime())) {
      const y = dt.getUTCFullYear();
      const m = String(dt.getUTCMonth() + 1).padStart(2, "0");
      const d = String(dt.getUTCDate()).padStart(2, "0");
      return `${y}-${m}-${d}`;
    }

    // Fallback: don't crash the UI
    return "";
  }

  isValidDuolingoScore(value) {
    if (value === null || value === undefined || value === "") return true; // empty is allowed
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 && number <= 160;
  }

  isFutureYMD(ymd) {
    if (!ymd) return false;
    // ymd is "yyyy-MM-dd"
    const today = new Date();
    const todayYMD = new Date(
      Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate())
    )
      .toISOString()
      .slice(0, 10);
    return ymd > todayYMD;
  }

  updateDuolingoValidity() {
    const scoreEl = document.getElementById("duolingoScoreInput");
    const dateEl = document.getElementById("duolingoDateInput");
    const btn = document.getElementById("saveDuolingoBtn");

    if (!scoreEl || !dateEl || !btn) return;

    const scoreValue = scoreEl.value.trim();
    const dateValue = dateEl.value.trim();

    const scoreInvalid =
      scoreValue !== "" && !this.isValidDuolingoScore(scoreValue);
    const dateInvalid = dateValue !== "" && this.isFutureYMD(dateValue);

    // Score styles + message
    scoreEl.classList.toggle("border-red-500", scoreInvalid);
    scoreEl.classList.toggle("ring-1", scoreInvalid);
    scoreEl.classList.toggle("ring-red-500", scoreInvalid);
    scoreEl.classList.toggle("focus:ring-red-500", scoreInvalid);
    scoreEl.classList.toggle("border-gray-300", !scoreInvalid);

    const scoreMsg = document.getElementById("duo-score-error");
    if (scoreMsg) scoreMsg.classList.toggle("hidden", !scoreInvalid);

    // Date styles + message
    dateEl.classList.toggle("border-red-500", dateInvalid);
    dateEl.classList.toggle("ring-1", dateInvalid);
    dateEl.classList.toggle("ring-red-500", dateInvalid);
    dateEl.classList.toggle("focus:ring-red-500", dateInvalid);
    dateEl.classList.toggle("border-gray-300", !dateInvalid);

    const dateMsg = document.getElementById("duo-date-error");
    if (dateMsg) dateMsg.classList.toggle("hidden", !dateInvalid);

    // Button enable/disable
    btn.disabled = scoreInvalid || dateInvalid;
  }

  renderInfoField(label, value, type = "text") {
    if (
      !value ||
      value === "null" ||
      value === "undefined" ||
      value === "NaN"
    ) {
      return `
        <div class="flex justify-between items-center py-2 border-b border-white/30">
          <span class="text-sm font-medium text-gray-600">${label}:</span>
          <span class="text-sm text-gray-400 italic">Not provided</span>
        </div>
      `;
    }

    let displayValue = value;
    if (type === "email") {
      displayValue = `<a href="mailto:${value}" class="text-blue-600 hover:text-blue-800 hover:underline">${value}</a>`;
    } else if (type === "phone") {
      displayValue = `<a href="tel:${value}" class="text-blue-600 hover:text-blue-800 hover:underline">${value}</a>`;
    }

    // Check if this is a long text field that should wrap instead of truncate
    const longTextFields = [
      "Academic History",
      "UBC Academic History",
      "Aboriginal Info",
      "Visa Type",
    ];
    const isLongTextField = longTextFields.includes(label);

    if (isLongTextField) {
      return `
        <div class="py-2 border-b border-white/30">
          <span class="text-sm font-medium text-gray-700 block mb-1">${label}:</span>
          <span class="text-sm text-gray-900 leading-relaxed">${displayValue}</span>
        </div>
      `;
    }

    return `
      <div class="flex justify-between items-center py-2 border-b border-white/30">
        <span class="text-sm font-medium text-gray-700">${label}:</span>
        <span class="text-sm text-gray-900 text-right max-w-xs truncate" title="${value}">${displayValue}</span>
      </div>
    `;
  }

  hasAboriginalInfo(applicant) {
    return (
      applicant.aboriginal === "Y" ||
      applicant.first_nation === "Y" ||
      applicant.inuit === "Y" ||
      applicant.metis === "Y" ||
      applicant.aboriginal_not_specified === "Y" ||
      applicant.aboriginal_info
    );
  }

  formatYesNo(value) {
    if (value === "Y") return "Yes";
    if (value === "N") return "No";
    return null;
  }

  hasInstitutionData(institution) {
  // Helper to check if a value is meaningful (not null, undefined, empty string, or placeholder)
  const hasValue = (val) => {
    if (val === null || val === undefined || val === '') return false;
    // Treat "UNKNOWN" and similar placeholders as empty
    if (typeof val === 'string' && val.toUpperCase() === 'UNKNOWN') return false;
    return true;
  };
  
  // Check if institution has any meaningful data besides institution_number
  return (
    hasValue(institution.full_name) ||
    hasValue(institution.country) ||
    hasValue(institution.start_date) ||
    hasValue(institution.end_date) ||
    hasValue(institution.program_study) ||
    hasValue(institution.degree_confer) ||
    hasValue(institution.credential_receive) ||
    hasValue(institution.date_confer) ||
    hasValue(institution.expected_confer_date) ||
    hasValue(institution.honours) ||
    hasValue(institution.gpa) ||
    hasValue(institution.fail_withdraw) ||
    hasValue(institution.reason)
  );
}

  async loadInstitutionInfo(userCode) {
    try {
      const response = await fetch(`/api/applicant-institutions/${userCode}`);
      const result = await response.json();

      const container = document.getElementById("institutionInfoContainer");

      if (
        result.success &&
        result.institutions &&
        result.institutions.length > 0
      ) {
        // First, get applicant info to check UBC attendance
        const applicantResponse = await fetch(
          `/api/applicant-info/${userCode}`
        );
        const applicantResult = await applicantResponse.json();

        let ubcSection = "";
        if (applicantResult.success && applicantResult.applicant) {
          const applicant = applicantResult.applicant;
          const academicHistoryCode = applicant.academic_history_code;
          const ubcAcademicHistory = applicant.ubc_academic_history;

          // Check if they attended UBC (Y or U codes)
          const attendedUBC =
            academicHistoryCode === "Y" || academicHistoryCode === "U";

          // Parse UBC academic history
          const ubcRecords = this.parseUbcAcademicHistory(ubcAcademicHistory);

          ubcSection = `
            <!-- UBC Educational Background Section -->
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6 border border-blue-200">
              <h5 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
                </svg>
                UBC Educational Background
              </h5>
              ${
                attendedUBC
                  ? `
                  <div class="mb-4">
                    <div class="flex items-center mb-4">
                      <div class="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                      <span class="text-sm font-medium text-blue-800">Previous UBC Student</span>
                      ${
                        ubcRecords.length > 0
                          ? `
                        <span class="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                          ${ubcRecords.length} record${
                              ubcRecords.length !== 1 ? "s" : ""
                            }
                        </span>
                      `
                          : ""
                      }
                    </div>
                    <div class="space-y-3">
                      ${this.renderUbcAcademicHistoryRecords(ubcRecords)}
                    </div>
                  </div>
              `
                  : `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                  <div class="flex items-center mb-2">
                    <div class="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                    <span class="text-sm font-medium text-gray-600">No Previous UBC Attendance</span>
                  </div>
                  <p class="text-sm text-gray-500">This applicant has not previously attended UBC.</p>
                </div>
              `
              }
            </div>
          `;
        }

        container.innerHTML = `
          <div class="pr-2">
            <h4 class="text-xl font-semibold text-ubc-blue mb-6 flex items-center">
              <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
              </svg>
              Educational Background
            </h4>

            ${ubcSection}

             <!-- Academic Summary Section -->
            <div class="bg-gradient-to-r from-ubc-blue to-blue-600 text-white rounded-lg p-6 mb-6">
              <h5 class="text-lg font-semibold mb-4">Academic Summary</h5>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="text-center">
                  <p class="text-blue-100 text-sm">Highest Degree</p>
                  <p class="text-xl font-bold" id="highestDegreeDisplay">-</p>
                </div>
                <div class="text-center">
                  <p class="text-blue-100 text-sm">Field of Study</p>
                  <p class="text-xl font-bold" id="degreeAreaDisplay">-</p>
                </div>
                <div class="text-center">
                  <p class="text-blue-100 text-sm">GPA</p>
                  <p class="text-xl font-bold" id="gpaDisplay">-</p>
                </div>
              </div>
            </div>
            
            <div class="space-y-6">
              ${result.institutions
                .filter(institution => this.hasInstitutionData(institution))
                .map(
                  (institution, index) => `
                <div class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center">
                      <div class="bg-ubc-blue text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold mr-3">
                        ${institution.institution_number}
                      </div>
                      <div>
                        <h5 class="text-lg font-semibold text-gray-900">${
                          institution.full_name ||
                          "Institution Name Not Provided"
                        }</h5>
                        <p class="text-sm text-gray-600">${
                          institution.country || "Country Not Specified"
                        }</p>
                      </div>
                    </div>
                    ${
                      institution.gpa
                        ? `
                      <div class="bg-blue-50 px-3 py-1 rounded-full">
                        <span class="text-sm font-medium text-ubc-blue">GPA: ${institution.gpa}</span>
                      </div>
                    `
                        : ""
                    }
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div class="space-y-2">
                      ${
                        institution.program_study
                          ? `<p><span class="font-medium text-gray-700">Program:</span> ${institution.program_study}</p>`
                          : ""
                      }
                      ${
                        institution.start_date
                          ? `<p><span class="font-medium text-gray-700">Start Date:</span> ${this.formatDate(institution.start_date)}</p>`
                          : ""
                      }
                      ${
                        institution.end_date
                          ? `<p><span class="font-medium text-gray-700">End Date:</span> ${this.formatDate(institution.end_date)}</p>`
                          : ""
                      }
                      ${
                        institution.degree_confer
                          ? `<p><span class="font-medium text-gray-700">Degree Conferred:</span> ${institution.degree_confer}</p>`
                          : ""
                      }
                    </div>
                    
                    <div class="space-y-2">
                      ${
                        institution.credential_receive
                          ? `<p><span class="font-medium text-gray-700">Credential:</span> ${institution.credential_receive}</p>`
                          : ""
                      }
                      ${
                        institution.date_confer
                          ? `<p><span class="font-medium text-gray-700">Date Conferred:</span> ${this.formatDate(institution.date_confer)}</p>`
                          : ""
                      }
                      ${
                        institution.expected_confer_date
                          ? `<p><span class="font-medium text-gray-700">Expected Graduation:</span> ${this.formatDate(institution.expected_confer_date)}</p>`
                          : ""
                      }
                      ${
                        institution.honours
                          ? `<p><span class="font-medium text-gray-700">Honours:</span> ${institution.honours}</p>`
                          : ""
                      }
                    </div>
                  </div>
                  
                  ${
                    institution.fail_withdraw && institution.reason
                      ? `
                    <div class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                      <p class="text-sm text-red-800"><span class="font-medium">Withdrawal/Academic Issue:</span> ${institution.reason}</p>
                    </div>
                  `
                      : ""
                  }
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `;
        this.loadAcademicSummary(userCode);
      } else {
        // Even if no institution info, still show UBC section
        const applicantResponse = await fetch(
          `/api/applicant-info/${userCode}`
        );
        const applicantResult = await applicantResponse.json();

        let ubcSection = "";
        if (applicantResult.success && applicantResult.applicant) {
          const applicant = applicantResult.applicant;
          const academicHistoryCode = applicant.academic_history_code;
          const ubcAcademicHistory = applicant.ubc_academic_history;

          // Parse UBC academic history
          const ubcRecords = this.parseUbcAcademicHistory(ubcAcademicHistory);

          // Check if they attended UBC (Y or U codes)
          const attendedUBC =
            academicHistoryCode === "Y" || academicHistoryCode === "U";

          ubcSection = `
            <div class="mb-6">
              <h4 class="text-xl font-semibold text-ubc-blue mb-4 flex items-center">
                <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
                </svg>
                Educational Background
              </h4>
              
              <!-- UBC Educational Background Section -->
              <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6 border border-blue-200">
                <h5 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
                  </svg>
                  UBC Educational Background
                </h5>
                ${
                  attendedUBC
                    ? `
                  <div class="bg-white rounded-lg p-4 border border-green-200">
                    <div class="flex items-center mb-3">
                      <div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                      <span class="text-sm font-medium text-green-800">Previous UBC Student</span>
                    </div>
                    <div class="text-sm text-gray-700 leading-relaxed">
                      ${
                        ubcAcademicHistory && ubcAcademicHistory.trim() !== ""
                          ? `<p class="whitespace-pre-line">${ubcAcademicHistory}</p>`
                          : `<p class="text-gray-500 italic">UBC academic history details not available</p>`
                      }
                    </div>
                  </div>
                `
                    : `
                  <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex items-center mb-2">
                      <div class="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                      <span class="text-sm font-medium text-gray-600">No Previous UBC Attendance</span>
                    </div>
                    <p class="text-sm text-gray-500">This applicant has not previously attended UBC.</p>
                  </div>
                `
                }
              </div>
            </div>
          `;
        }

        container.innerHTML = `
          <div class="pr-2">
            ${ubcSection}
            
            <div class="text-center py-12 text-gray-500">
              <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
              </svg>
              <h3 class="text-lg font-medium text-gray-400 mb-2">No Institution Information</h3>
              <p class="text-gray-400">No external educational background information is available for this applicant.</p>
            </div>
          </div>
        `;
      }
    } catch (error) {
      const container = document.getElementById("institutionInfoContainer");
      container.innerHTML = `
        <div class="text-center py-8 text-red-500">
          <p>Error loading institution information: ${error.message}</p>
        </div>
      `;
    }
  }

  calculateHighestDegreeFromInstitutions(institutions) {
    if (!institutions || institutions.length === 0) {
      return { highest_degree: null, degree_area: null, gpa: null };
    }

    const degreeHierarchy = {
      phd: 4,
      doctorate: 4,
      doctoral: 4,
      "ph.d": 4,
      "ph.d.": 4,
      master: 3,
      "master's": 3,
      masters: 3,
      msc: 3,
      ma: 3,
      mba: 3,
      med: 3,
      bachelor: 2,
      "bachelor's": 2,
      bachelors: 2,
      bsc: 2,
      ba: 2,
      beng: 2,
      associate: 1,
      diploma: 1,
      certificate: 1,
    };

    let highestDegreeLevel = 0;
    let selectedInstitution = null;

    for (const institution of institutions) {
      if (!institution.credential_receive) continue;

      const credential = institution.credential_receive.toLowerCase().trim();

      // Find matching degree level
      let currentDegreeLevel = 0;
      for (const [degreeKey, level] of Object.entries(degreeHierarchy)) {
        if (credential.includes(degreeKey)) {
          currentDegreeLevel = Math.max(currentDegreeLevel, level);
        }
      }

      // If this is a higher degree, or same degree with later date
      if (currentDegreeLevel > highestDegreeLevel) {
        highestDegreeLevel = currentDegreeLevel;
        selectedInstitution = institution;
      } else if (
        currentDegreeLevel === highestDegreeLevel &&
        selectedInstitution
      ) {
        // Same degree level - choose the one with latest date_confer
        const currentDate = institution.date_confer
          ? new Date(institution.date_confer)
          : null;
        const selectedDate = selectedInstitution.date_confer
          ? new Date(selectedInstitution.date_confer)
          : null;

        if (currentDate && selectedDate) {
          if (currentDate > selectedDate) {
            selectedInstitution = institution;
          }
        } else if (currentDate && !selectedDate) {
          selectedInstitution = institution;
        }
      }
    }

    if (selectedInstitution) {
      return {
        highest_degree: selectedInstitution.credential_receive,
        degree_area: selectedInstitution.program_study,
        gpa: selectedInstitution.gpa,
      };
    }

    return { highest_degree: null, degree_area: null, gpa: null };
  }

  async loadAcademicSummary(userCode) {
    try {
      // Fetch institution data to calculate highest degree locally
      const response = await fetch(`/api/applicant-institutions/${userCode}`);
      const result = await response.json();

      if (result.success && result.institutions) {
        // Calculate highest degree from institutions data
        const academicSummary = this.calculateHighestDegreeFromInstitutions(
          result.institutions
        );

        // Update academic summary displays
        document.getElementById("highestDegreeDisplay").textContent =
          academicSummary.highest_degree || "-";
        document.getElementById("degreeAreaDisplay").textContent =
          academicSummary.degree_area || "-";
        document.getElementById("gpaDisplay").textContent =
          academicSummary.gpa || "-";
      } else {
        // Set default values if no institutions found
        document.getElementById("highestDegreeDisplay").textContent = "-";
        document.getElementById("degreeAreaDisplay").textContent = "-";
        document.getElementById("gpaDisplay").textContent = "-";
      }
    } catch (error) {
      console.error("Error loading academic summary:", error);
      // Set default values if there's an error
      document.getElementById("highestDegreeDisplay").textContent = "-";
      document.getElementById("degreeAreaDisplay").textContent = "-";
      document.getElementById("gpaDisplay").textContent = "-";
    }
  }

  async loadApplicationStatus(userCode) {
    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}`
      );
      const result = await response.json();

      if (result.success && result.application_info) {
        const currentStatus = result.application_info.sent || "Not Reviewed";

        // Update tab label
        document.getElementById("statusTabLabel").textContent = currentStatus;

        // Update current status display
        document.getElementById("currentStatusDisplay").textContent =
          currentStatus;
        document.getElementById("currentStatusText").textContent =
          currentStatus;

        // Update status badge styling
        this.updateStatusBadge(currentStatus);

        // Update ALL status select dropdowns (sync all three)
        document.getElementById("statusSelect").value = currentStatus;
        document.getElementById("prereqStatusSelect").value = currentStatus;
        document.getElementById("ratingsStatusSelect").value = currentStatus;

        // Hide preview initially
        document.getElementById("statusPreview").classList.add("hidden");

        // Update status change buttons visibility based on user role
        this.updateStatusFormPermissions();

        // Add change listener for preview
        this.setupStatusPreview(currentStatus);
      }
            // Also update the prerequisites tab status dropdown
      const prereqStatusSelect = document.getElementById("prereqStatusSelect");
      if (prereqStatusSelect && result.status) {
        prereqStatusSelect.value = result.status;
      }
    } catch (error) {
      console.error("Error loading applicant status:", error);
    }
  }

  updateStatusFormPermissions() {
    const statusButtons = document.getElementById("statusUpdateButtons");
    const statusSelect = document.getElementById("statusSelect");
    const statusChangeSection = document.getElementById("statusChangeSection");
    
    // Also get the new status sections in prereq and ratings tabs
    const prereqStatusSection = document.getElementById("prereqStatusChangeSection");
    const ratingsStatusSection = document.getElementById("ratingsStatusChangeSection");

    // Check user role from auth
    fetch("/api/auth/check-session")
      .then((response) => response.json())
      .then((result) => {
        if (result.authenticated && result.user?.role === "Admin") {
          // Only Admin can update status - show everything
          if (statusChangeSection) {
            statusChangeSection.style.display = "block";
          }
          if (prereqStatusSection) {
            prereqStatusSection.style.display = "block";
          }
          if (ratingsStatusSection) {
            ratingsStatusSection.style.display = "block";
          }
          if (statusButtons) {
            statusButtons.style.display = "flex";
          }
          statusSelect.disabled = false;

          // Set title for Admin
          const statusTitle = document.querySelector("#status-tab h4");
          if (statusTitle) {
            statusTitle.innerHTML = `
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Application Status Management
          `;
          }
        } else {
          // Faculty and Viewers can see current status but not change it
          if (statusChangeSection) {
            statusChangeSection.style.display = "none";
          }
          if (prereqStatusSection) {
            prereqStatusSection.style.display = "none";
          }
          if (ratingsStatusSection) {
            ratingsStatusSection.style.display = "none";
          }

          // Set title for Viewers
          const statusTitle = document.querySelector("#status-tab h4");
          if (statusTitle) {
            statusTitle.innerHTML = `
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Application Status
          `;
          }
        }
      })
      .catch((error) => {
        console.error("Error checking user permissions:", error);
      });
  }

  async updateStatus() {
    const userCode =
      document.getElementById("applicantModal").dataset.currentUserCode;
    const newStatus = document.getElementById("statusSelect").value;
    const updateBtn = document.getElementById("updateStatusBtn");

    if (!userCode || !newStatus) return;

    const originalHTML = updateBtn.innerHTML;
    updateBtn.disabled = true;
    updateBtn.innerHTML = `
    <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
    </svg>
    Updating...
  `;

    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}/status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            status: newStatus,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        this.showMessage(result.message, "success");

        // Update tab label
        document.getElementById("statusTabLabel").textContent = newStatus;

        // Sync all status selects
        this.syncAllStatusSelects(newStatus);

        // Reload the entire status display
        this.loadApplicationStatus(userCode);

        // Reload status history immediately
        await this.loadStatusHistory(userCode);
        await this.loadApplicants();
      } else {
        this.showMessage(result.message, "error");
      }
    } catch (error) {
      this.showMessage(`Error updating status: ${error.message}`, "error");
    } finally {
      updateBtn.disabled = false;
      updateBtn.innerHTML = originalHTML;
    }
  }

  syncAllStatusSelects(status) {
    // Sync all three status selects
    const statusSelect = document.getElementById("statusSelect");
    const prereqStatusSelect = document.getElementById("prereqStatusSelect");
    const ratingsStatusSelect = document.getElementById("ratingsStatusSelect");
    
    if (statusSelect) statusSelect.value = status;
    if (prereqStatusSelect) prereqStatusSelect.value = status;
    if (ratingsStatusSelect) ratingsStatusSelect.value = status;
  }

  async loadStatusHistory(userCode) {
    const container = document.getElementById("statusHistoryContainer");
    const countElement = document.getElementById("statusHistoryCount");

    try {
      // Only Admins can view logs; check role first to avoid 403s and console noise
      const auth = await fetch("/api/auth/check-session")
        .then((r) => r.json())
        .catch(() => ({}));
      const isAdmin = !!(
        auth &&
        auth.authenticated &&
        auth.user &&
        auth.user.role === "Admin"
      );

      if (!isAdmin) {
        // For Viewer/Faculty, don't call the logs API; show a quiet placeholder instead
        if (container) {
          container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
              <p class="text-sm">Status history is available to admins.</p>
            </div>
          `;
        }
        if (countElement) countElement.textContent = "";
        return;
      }

      // Admins: fetch status change logs for this specific applicant - limit to 5
      const response = await fetch(
        `/api/logs?action_type=status_change&target_id=${userCode}&limit=5`
      );
      const result = await response.json();

      if (result.success) {
        if (result.logs.length === 0) {
          container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
              <p class="text-sm">No status changes recorded yet</p>
            </div>
          `;
          countElement.textContent = "No changes yet";
          return;
        }

        // Update the counter based on actual results
        const displayCount = Math.min(result.logs.length, 5);
        countElement.textContent = `Showing recent ${displayCount} change${
          displayCount !== 1 ? "s" : ""
        }`;

        const historyHtml = result.logs
          .map((log) => this.createStatusHistoryItem(log))
          .join("");
        container.innerHTML = historyHtml;
      } else {
        container.innerHTML = `
          <div class="text-center py-4 text-red-500">
            <p class="text-sm">Error loading status history</p>
          </div>
        `;
        countElement.textContent = "Error loading";
      }
    } catch (error) {
      console.error("Error loading status history:", error);
      container.innerHTML = `
        <div class="text-center py-4 text-red-500">
          <p class="text-sm">Failed to load status history</p>
        </div>
      `;
      countElement.textContent = "Error loading";
    }
  }

  createStatusHistoryItem(log) {
    const timestamp = new Date(log.created_at);
    const timeString = timestamp.toLocaleString();
    const timeAgo = this.getTimeAgo(timestamp);

    return `
      <div class="bg-white rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-sm text-gray-900">
              <span class="font-medium">${log.user_name}</span> 
              changed status from 
              <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">${
                log.old_value || "Unknown"
              }</span>
              to 
              <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">${
                log.new_value || "Unknown"
              }</span>
            </p>
            <div class="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>${timeString}</span>
              <span>•</span>
              <span>${timeAgo}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  updateStatusBadge(status) {
    const badge = document.getElementById("currentStatusBadge");
    const dot = document.getElementById("currentStatusDot");

    // Remove existing classes
    badge.className =
      "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium";

    // Add status-specific styling
    switch (status) {
      case "Not Reviewed":
        badge.classList.add("bg-gray-100", "text-gray-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-gray-400";
        break;
      case "Waitlist":
        badge.classList.add("bg-yellow-100", "text-yellow-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-yellow-400";
        break;
      case "Send Offer to CoGS":
        badge.classList.add("bg-green-100", "text-green-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-green-400";
        break;
      case "Offer Sent to CoGS":
        badge.classList.add("bg-blue-100", "text-blue-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-blue-400";
        break;
      case "Offer Sent to Student":
        badge.classList.add("bg-purple-100", "text-purple-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-purple-400";
        break;
      case "Reviewed by PPA":
        badge.classList.add("bg-indigo-100", "text-indigo-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-indigo-400";
        break;
      case "Need Jeff's Review":
        badge.classList.add("bg-purple-100", "text-purple-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-purple-400";
        break;
      case "Need Khalad's Review":
        badge.classList.add("bg-pink-100", "text-pink-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-pink-400";
        break;
      case "Declined":
        badge.classList.add("bg-red-100", "text-red-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-red-400";
        break;
      case "Offer Accepted":
        badge.classList.add("bg-green-100", "text-green-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-green-400";
        break;
      case "Offer Declined":
        badge.classList.add("bg-orange-100", "text-orange-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-orange-400";
        break;
      default:
        badge.classList.add("bg-gray-100", "text-gray-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-gray-400";
    }
  }

  async loadPrerequisites(userCode) {
    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}`
      );
      const result = await response.json();

      if (result.success && result.application_info) {
        const appInfo = result.application_info;
        document.getElementById("prerequisiteCs").value = appInfo.cs || "";
        document.getElementById("prerequisiteStat").value = appInfo.stat || "";
        document.getElementById("prerequisiteMath").value = appInfo.math || "";
        document.getElementById("additionalComments").value = appInfo.additional_comments || "";
        document.getElementById("overallGpa").value = appInfo.gpa || "";

        // Load MDS radio button values
        const mdsV = appInfo.mds_v || "No";
        const mdsO = appInfo.mds_o || "Yes";
        const mdsCL = appInfo.mds_cl || "No";

        // Set UBC-V radio buttons
        const mdsVRadios = document.querySelectorAll('input[name="mdsV"]');
        mdsVRadios.forEach(radio => {
          radio.checked = radio.value === mdsV;
        });

        // Set UBC-O radio buttons
        const mdsORadios = document.querySelectorAll('input[name="mdsO"]');
        mdsORadios.forEach(radio => {
          radio.checked = radio.value === mdsO;
        });

        // Set UBC-CL radio buttons
        const mdsCLRadios = document.querySelectorAll('input[name="mdsCL"]');
        mdsCLRadios.forEach(radio => {
          radio.checked = radio.value === mdsCL;
        });
      }

      await this.updatePrerequisitesFormPermissions();
    } catch (error) {
      console.error("Error loading prerequisites:", error);
    }
  }

  async loadScholarship(userCode) {
    try {
      const response = await fetch(`/api/applicant-application-info/${userCode}`);
      const result = await response.json();

      if (result.success && result.application_info) {
        const scholarship = result.application_info.scholarship || "Undecided";
        const radioButton = document.querySelector(`input[name="scholarship"][value="${scholarship}"]`);
        if (radioButton) {
          radioButton.checked = true;
        }
      } else {
        // Default to Undecided
        const undecidedRadio = document.querySelector('input[name="scholarship"][value="Undecided"]');
        if (undecidedRadio) {
          undecidedRadio.checked = true;
        }
      }

      // Update permissions after loading
      await this.updateScholarshipFormPermissions();
    } catch (error) {
      console.error("Error loading scholarship:", error);
    }
  }

  async updateScholarshipFormPermissions() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      const scholarshipRadios = document.querySelectorAll('input[name="scholarship"]');
      const saveScholarshipBtn = document.getElementById("saveScholarshipBtn");

      if (result.authenticated && result.user) {
        if (result.user.role === "Admin") {
          // Admin can edit - enable all controls
          scholarshipRadios.forEach(radio => radio.disabled = false);
          if (saveScholarshipBtn) saveScholarshipBtn.style.display = "inline-block";
        } else {
          // Faculty and Viewer can only view - disable all controls
          scholarshipRadios.forEach(radio => radio.disabled = true);
          if (saveScholarshipBtn) saveScholarshipBtn.style.display = "none";
        }
      }
    } catch (error) {
      console.error("Error checking user permissions:", error);
    }
  }

  async updatePrerequisitesFormPermissions() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      // Get all the elements we need to control
      const savePrerequisitesBtn = document.getElementById(
        "savePrerequisitesBtn"
      );
      const clearPrerequisitesBtn = document.getElementById(
        "clearPrerequisitesBtn"
      );
      const saveGpaBtn = document.getElementById("saveGpaBtn");
      const csInput = document.getElementById("prerequisiteCs");
      const statInput = document.getElementById("prerequisiteStat");
      const mathInput = document.getElementById("prerequisiteMath");
      const additionalCommentsInput = document.getElementById("additionalComments");
      const gpaInput = document.getElementById("overallGpa");

      if (result.authenticated && result.user?.role === "Admin") {
        // Only Admin can edit everything including GPA
        if (savePrerequisitesBtn)
          savePrerequisitesBtn.style.display = "inline-block";
        if (clearPrerequisitesBtn)
          clearPrerequisitesBtn.style.display = "inline-block";
        if (csInput) csInput.disabled = false;
        if (statInput) statInput.disabled = false;
        if (mathInput) mathInput.disabled = false;
        if (gpaInput) gpaInput.disabled = false;
      } else if (result.authenticated && result.user?.role === "Faculty") {
        // Faculty can edit prerequisites but not GPA
        if (savePrerequisitesBtn)
          savePrerequisitesBtn.style.display = "inline-block";
        if (clearPrerequisitesBtn)
          clearPrerequisitesBtn.style.display = "inline-block";
        if (csInput) csInput.disabled = false;
        if (statInput) statInput.disabled = false;
        if (mathInput) mathInput.disabled = false;
        if (gpaInput) gpaInput.disabled = true; // Disable GPA editing for Faculty
      } else {
        // Viewers can only see the values - hide all buttons and disable inputs
        if (savePrerequisitesBtn) savePrerequisitesBtn.style.display = "none";
        if (clearPrerequisitesBtn) clearPrerequisitesBtn.style.display = "none";
        if (csInput) {
          csInput.disabled = true;
          if (!csInput.value || csInput.value.trim() === "") {
            csInput.placeholder = "Not Provided";
          }
        }
        if (statInput) {
          statInput.disabled = true;
          if (!statInput.value || statInput.value.trim() === "") {
            statInput.placeholder = "Not Provided";
          }
        }
        if (mathInput) {
          mathInput.disabled = true;
          if (!mathInput.value || mathInput.value.trim() === "") {
            mathInput.placeholder = "Not Provided";
          }
        }
        if (additionalCommentsInput) {
          additionalCommentsInput.disabled = true;
          if (!additionalCommentsInput.value || additionalCommentsInput.value.trim() === "") {
            additionalCommentsInput.placeholder = "Not Provided";
          }
        }
        if (gpaInput) {
          gpaInput.disabled = true;
          if (!gpaInput.value || gpaInput.value.trim() === "") {
            gpaInput.placeholder = "N/A";
          }
        }
      }
    } catch (error) {
      console.error("Error checking user permissions:", error);
    }
  }

  showPrerequisitesFeedback(message, isSuccess) {
    const feedbackDiv = document.getElementById("prerequisitesFeedback");
    const feedbackText = document.getElementById("prerequisitesFeedbackText");

    if (feedbackDiv && feedbackText) {
      feedbackText.textContent = message;

      // Remove existing classes
      feedbackDiv.classList.remove(
        "hidden",
        "bg-green-100",
        "text-green-800",
        "bg-red-100",
        "text-red-800"
      );

      // Add appropriate classes based on success/error
      if (isSuccess) {
        feedbackDiv.classList.add("bg-green-100", "text-green-800");
      } else {
        feedbackDiv.classList.add("bg-red-100", "text-red-800");
      }

      // Auto-hide after 5 seconds
      setTimeout(() => {
        feedbackDiv.classList.add("hidden");
      }, 5000);
    }
  }

  async savePrerequisiteCourses() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;
    if (!userCode) return;

    const cs = document.getElementById("prerequisiteCs").value;
    const stat = document.getElementById("prerequisiteStat").value;
    const math = document.getElementById("prerequisiteMath").value;
    const additionalComments = document.getElementById("additionalComments").value;
    const gpa = document.getElementById("overallGpa").value;
    const status = document.getElementById("prereqStatusSelect").value;

    // Get MDS radio button values
    const mdsV = document.querySelector('input[name="mdsV"]:checked')?.value || "No";
    const mdsO = document.querySelector('input[name="mdsO"]:checked')?.value || "Yes";
    const mdsCL = document.querySelector('input[name="mdsCL"]:checked')?.value || "No";

    const saveBtn = document.getElementById("saveAllPrerequisitesBtn");
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      // Save prerequisites (GPA, CS, Stat, Math, Additional Comments)
      const prereqResponse = await fetch(
        `/api/applicant-application-info/${userCode}/prerequisites`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ cs, stat, math, gpa, additional_comments: additionalComments, mds_v: mdsV, mds_cl: mdsCL, mds_o: mdsO }),
        }
      );

      const prereqResult = await prereqResponse.json();

      if (!prereqResult.success) {
        this.showPrerequisitesFeedback(
          prereqResult.message || "Failed to save prerequisites",
          false
        );
        return;
      }

      // Update status
      const statusResponse = await fetch(`/api/applicant-application-info/${userCode}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });

      const statusResult = await statusResponse.json();

      if (statusResult.success) {
        this.showPrerequisitesFeedback(
          "All prerequisites and status saved successfully",
          true
        );
        
        // Update the status tab label
        const statusTabLabel = document.getElementById("statusTabLabel");
        if (statusTabLabel) {
          statusTabLabel.textContent = status;
        }

        // Sync all status selects across all tabs
        this.syncAllStatusSelects(status);

        // Reload the entire status display
        this.loadApplicationStatus(userCode);

        // Reload status history
        await this.loadStatusHistory(userCode);

        // Refresh the applicants list to show updated status
        await this.loadApplicants();
      } else {
        this.showPrerequisitesFeedback(
          "Prerequisites saved but failed to update status: " + (statusResult.message || "Unknown error"),
          false
        );
      }
    } catch (error) {
      console.error("Error saving prerequisites:", error);
      this.showPrerequisitesFeedback(
        "Error saving prerequisites",
        false
      );
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
      this.loadPrerequisitesSummary(modal.dataset.currentUserCode);
    }
  }

  async clearPrerequisites() {
    // Clear prerequisite courses for all roles
    document.getElementById("prerequisiteCs").value = "";
    document.getElementById("prerequisiteStat").value = "";
    document.getElementById("prerequisiteMath").value = "";
    document.getElementById("additionalComments").value = "";

    // Only clear GPA if user is Admin
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      if (result.authenticated && result.user?.role === "Admin") {
        // Admin can clear GPA
        document.getElementById("overallGpa").value = "";
      }
      // Faculty and Viewers: don't clear GPA field
      
      // Don't touch the status dropdown - it should remain as selected
      
    } catch (error) {
      console.error("Error checking user permissions:", error);
      // If error checking permissions, don't clear GPA to be safe
    }
  }

  setupStatusPreview(currentStatus) {
    const statusSelect = document.getElementById("statusSelect");
    const statusPreview = document.getElementById("statusPreview");
    const currentStatusPreview = document.getElementById(
      "currentStatusPreview"
    );
    const newStatusPreview = document.getElementById("newStatusPreview");
    const updateBtn = document.getElementById("updateStatusBtn");

    // Clear any existing event listeners without cloning
    statusSelect.removeEventListener(
      "change",
      statusSelect._statusChangeHandler
    );

    // Create new handler and store reference
    const changeHandler = () => {
      const newStatus = statusSelect.value;

      if (newStatus !== currentStatus) {
        // Show preview
        statusPreview.classList.remove("hidden");
        currentStatusPreview.textContent = currentStatus;
        newStatusPreview.textContent = newStatus;
        updateBtn.disabled = false;
      } else {
        // Hide preview if same as current
        statusPreview.classList.add("hidden");
        updateBtn.disabled = true;
      }
    };

    // Store handler reference and add listener
    statusSelect._statusChangeHandler = changeHandler;
    statusSelect.addEventListener("change", changeHandler);

    // Make sure the update button starts disabled
    updateBtn.disabled = true;
  }

  parseUbcAcademicHistory(ubcHistoryString) {
    if (!ubcHistoryString || ubcHistoryString.trim() === "") {
      return [];
    }

    try {
      // Split by '} {' to separate records, then clean up
      const recordStrings = ubcHistoryString
        .split("} {")
        .map((record, index, array) => {
          // Clean up the record string
          let cleaned = record.trim();

          // Add missing braces
          if (index === 0 && !cleaned.startsWith("{")) {
            cleaned = "{" + cleaned;
          }
          if (index === array.length - 1 && !cleaned.endsWith("}")) {
            cleaned = cleaned + "}";
          }
          if (index > 0 && index < array.length - 1) {
            if (!cleaned.startsWith("{")) cleaned = "{" + cleaned;
            if (!cleaned.endsWith("}")) cleaned = cleaned + "}";
          }

          return cleaned;
        });

      const records = [];

      recordStrings.forEach((recordString) => {
        if (!recordString.trim()) return;

        // Remove outer braces and split by semicolons
        const content = recordString.replace(/^{|}$/g, "").trim();
        const parts = content.split(";");

        const record = {};

        parts.forEach((part) => {
          const trimmedPart = part.trim();
          if (!trimmedPart) return;

          const colonIndex = trimmedPart.indexOf(":");
          if (colonIndex === -1) return;

          const key = trimmedPart.substring(0, colonIndex).trim();
          const value = trimmedPart.substring(colonIndex + 1).trim();

          // Clean up key names and store values
          switch (key) {
            case "eVision Record #":
              record.recordNumber = parseInt(value) || 0;
              break;
            case "Degree Conferred?":
              record.degreeConferred = value;
              break;
            case "Start Date":
              record.startDate = value;
              break;
            case "End Date or Expected End Date":
              record.endDate = value;
              break;
            case "Expected Conferred Date":
              record.expectedConferredDate = value;
              break;
            case "Expected Credential":
              record.expectedCredential = value;
              break;
            case "Category":
              record.category = value;
              break;
            case "Program of Study":
              record.programOfStudy = value;
              break;
            case "Required to Withdraw?":
              record.requiredToWithdraw = value;
              break;
            case "Honours":
              record.honours = value;
              break;
            case "SPEC1":
              record.specialization = value;
              break;
            default:
              // Handle any other fields
              record[key.toLowerCase().replace(/[^a-z0-9]/g, "")] = value;
          }
        });

        if (Object.keys(record).length > 0) {
          records.push(record);
        }
      });

      // Sort by record number
      return records.sort(
        (a, b) => (a.recordNumber || 0) - (b.recordNumber || 0)
      );
    } catch (error) {
      console.error("Error parsing UBC academic history:", error);
      return [];
    }
  }

  renderUbcAcademicHistoryRecords(records) {
    if (!records || records.length === 0) {
      return `<p class="text-gray-500 italic">No UBC academic history records available</p>`;
    }

    return records
      .map(
        (record) => `
      <div class="bg-white rounded-lg p-4 border border-gray-200 mb-3">
        <div class="mb-3">
          <h6 class="text-sm font-semibold text-ubc-blue">
            eVision Record #${record.recordNumber || "Unknown"}
          </h6>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          ${
            record.degreeConferred
              ? `
            <div>
              <span class="font-medium text-gray-700">Degree Conferred:</span>
              <span class="text-gray-600 ml-1">${record.degreeConferred}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.startDate
              ? `
            <div>
              <span class="font-medium text-gray-700">Start Date:</span>
              <span class="text-gray-600 ml-1">${record.startDate}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.endDate
              ? `
            <div>
              <span class="font-medium text-gray-700">End Date:</span>
              <span class="text-gray-600 ml-1">${record.endDate}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.expectedCredential && record.expectedCredential.trim()
              ? `
            <div class="md:col-span-2">
              <span class="font-medium text-gray-700">Expected Credential:</span>
              <span class="text-gray-600 ml-1">${record.expectedCredential}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.category && record.category.trim()
              ? `
            <div>
              <span class="font-medium text-gray-700">Category:</span>
              <span class="text-gray-600 ml-1">${record.category}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.programOfStudy && record.programOfStudy.trim()
              ? `
            <div>
              <span class="font-medium text-gray-700">Program of Study:</span>
              <span class="text-gray-600 ml-1">${record.programOfStudy}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.specialization && record.specialization.trim()
              ? `
            <div class="md:col-span-2">
              <span class="font-medium text-gray-700">Specialization:</span>
              <span class="text-gray-600 ml-1">${record.specialization}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.expectedConferredDate && record.expectedConferredDate.trim()
              ? `
            <div>
              <span class="font-medium text-gray-700">Expected Graduation:</span>
              <span class="text-gray-600 ml-1">${record.expectedConferredDate}</span>
            </div>
          `
              : ""
          }
          
          ${
            record.requiredToWithdraw
              ? `
            <div>
              <span class="font-medium text-gray-700">Required to Withdraw:</span>
              <span class="text-gray-600 ml-1">${record.requiredToWithdraw}</span>
            </div>
          `
              : ""
          }
        </div>
        
        ${
          record.honours &&
          record.honours.trim() &&
          record.honours !==
            "Please see Workday for Awards or Honours awarded to this applicant."
            ? `
          <div class="mt-3 pt-3 border-t border-gray-100">
            <span class="font-medium text-gray-700 block mb-1">Honours:</span>
            <span class="text-gray-600 text-sm">${record.honours}</span>
          </div>
        `
            : ""
        }
      </div>
    `
      )
      .join("");
  }

  //updateEnglishStatusBadge method
  updateEnglishStatusBadge(status) {
    const badge = document.getElementById("currentEnglishStatusBadge");
    const dot = document.getElementById("currentEnglishStatusDot");
    const text = document.getElementById("currentEnglishStatusText");

    if (!badge || !dot || !text) return;

    // Remove existing classes
    badge.className =
      "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium";

    // Update text
    text.textContent = status;

    // Add status-specific styling
    switch (status) {
      case "Not Met":
        badge.classList.add("bg-red-100", "text-red-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-red-400";
        break;
      case "Not Required":
        badge.classList.add("bg-gray-100", "text-gray-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-gray-400";
        break;
      case "Passed":
        badge.classList.add("bg-green-100", "text-green-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-green-400";
        break;
      default:
        badge.classList.add("bg-gray-100", "text-gray-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-gray-400";
    }
  }

  //setupEnglishStatusPreview method
  setupEnglishStatusPreview(currentStatus) {
    const statusSelect = document.getElementById("englishStatusSelect");
    const statusPreview = document.getElementById("englishStatusPreview");
    const currentStatusPreview = document.getElementById(
      "currentEnglishStatusPreview"
    );
    const newStatusPreview = document.getElementById("newEnglishStatusPreview");
    const updateBtn = document.getElementById("updateEnglishStatusBtn");

    if (
      !statusSelect ||
      !statusPreview ||
      !currentStatusPreview ||
      !newStatusPreview ||
      !updateBtn
    ) {
      return;
    }

    // Clear any existing event listeners
    statusSelect.removeEventListener(
      "change",
      statusSelect._englishStatusChangeHandler
    );

    // Create new handler and store reference
    const changeHandler = () => {
      const newStatus = statusSelect.value;

      if (newStatus !== currentStatus) {
        // Show preview
        statusPreview.classList.remove("hidden");
        currentStatusPreview.textContent = currentStatus;
        newStatusPreview.textContent = newStatus;
        updateBtn.disabled = false;
      } else {
        // Hide preview if same as current
        statusPreview.classList.add("hidden");
        updateBtn.disabled = true;
      }
    };

    // Store handler reference and add listener
    statusSelect._englishStatusChangeHandler = changeHandler;
    statusSelect.addEventListener("change", changeHandler);

    // Make sure the update button starts disabled
    updateBtn.disabled = true;
  }

  async updateEnglishStatusFormPermissions() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      const updateBtn = document.getElementById("updateEnglishStatusBtn");
      const cancelBtn = document.getElementById("cancelEnglishStatusBtn");
      const statusSelect = document.getElementById("englishStatusSelect");
      const englishStatusChangeSection = document.getElementById(
        "englishStatusChangeSection"
      );

      if (result.authenticated && result.user?.role === "Admin") {
        // Only Admin can update English status
        if (englishStatusChangeSection) {
          englishStatusChangeSection.style.display = "block";
        }
        if (updateBtn) updateBtn.style.display = "inline-flex";
        if (cancelBtn) cancelBtn.style.display = "inline-block";
        if (statusSelect) statusSelect.disabled = false;
      } else {
        // Faculty and Viewers can only see current status
        if (englishStatusChangeSection) {
          englishStatusChangeSection.style.display = "none";
        }
      }

      // Update English comment permissions
      this.updateEnglishCommentPermissions();
    } catch (error) {
      console.error(
        "Error checking user permissions for English status:",
        error
      );
    }
  }

  async updateEnglishCommentPermissions() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      const textarea = document.getElementById("englishCommentTextarea");
      const saveBtn = document.getElementById("saveEnglishCommentBtn");
      const clearBtn = document.getElementById("clearEnglishCommentBtn");

      if (result.authenticated && result.user?.role === "Admin") {
        // Only Admin can edit English comments
        if (textarea) {
          textarea.disabled = false;
          textarea.placeholder =
            "Add comments about English proficiency status...";
        }
        if (saveBtn) saveBtn.style.display = "inline-block";
        if (clearBtn) clearBtn.style.display = "inline-block";
      } else {
        // Faculty and Viewers can only view English comments
        if (textarea) {
          textarea.disabled = true;
          textarea.placeholder =
            "N/A";
        }
        if (saveBtn) saveBtn.style.display = "none";
        if (clearBtn) clearBtn.style.display = "none";
      }
    } catch (error) {
      console.error(
        "Error checking user permissions for English comments:",
        error
      );
    }
  }

  setupEnglishCommentHandlers() {
    const saveBtn = document.getElementById("saveEnglishCommentBtn");
    const clearBtn = document.getElementById("clearEnglishCommentBtn");
    const updateEnglishBtn = document.getElementById("updateEnglishStatusBtn");
    const cancelEnglishBtn = document.getElementById("cancelEnglishStatusBtn");

    if (saveBtn) {
      saveBtn.addEventListener("click", async () => {
        // Check permissions before saving
        const response = await fetch("/api/auth/check-session");
        const result = await response.json();

        if (!result.authenticated || result.user?.role !== "Admin") {
          alert("You don't have permission to edit English comments.");
          return;
        }

        this.saveEnglishComment();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", async () => {
        // Check permissions before clearing
        const response = await fetch("/api/auth/check-session");
        const result = await response.json();

        if (!result.authenticated || result.user?.role !== "Admin") {
          alert("You don't have permission to edit English comments.");
          return;
        }

        document.getElementById("englishCommentTextarea").value = "";
      });
    }

    if (updateEnglishBtn) {
      updateEnglishBtn.addEventListener("click", () => {
        this.updateEnglishStatus();
      });
    }

    if (cancelEnglishBtn) {
      cancelEnglishBtn.addEventListener("click", () => {
        const userCode =
          document.getElementById("applicantModal").dataset.currentUserCode;
        this.loadTestScores(userCode); // Reload to reset form
      });
    }
  }

  //saveEnglishComment method
  async saveEnglishComment() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;
    const comment = document.getElementById("englishCommentTextarea").value;

    if (!userCode) return;

    const saveBtn = document.getElementById("saveEnglishCommentBtn");
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}/english-comment`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            english_comment: comment,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        this.showMessage("English comment saved successfully", "success");
      } else {
        this.showMessage(
          result.message || "Failed to save English comment",
          "error"
        );
      }
    } catch (error) {
      this.showMessage(
        `Error saving English comment: ${error.message}`,
        "error"
      );
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  }

  //updateEnglishStatus method
  async updateEnglishStatus() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;
    const newStatus = document.getElementById("englishStatusSelect").value;

    if (!userCode || !newStatus) return;

    const updateBtn = document.getElementById("updateEnglishStatusBtn");
    const originalHTML = updateBtn.innerHTML;
    updateBtn.disabled = true;
    updateBtn.innerHTML = `
      <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
      </svg>
      Updating...
    `;

    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}/english-status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            english_status: newStatus,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        this.showMessage("English status updated successfully", "success");

        // Update the current status displays
        document.getElementById("currentEnglishStatusDisplay").textContent =
          newStatus;
        document.getElementById("currentEnglishStatusText").textContent =
          newStatus;

        // Update badge styling
        this.updateEnglishStatusBadge(newStatus);

        // Hide preview and disable update button
        document.getElementById("englishStatusPreview").classList.add("hidden");
        updateBtn.disabled = true;

        // Reset the preview functionality with new current status
        this.setupEnglishStatusPreview(newStatus);
      } else {
        this.showMessage(
          result.message || "Failed to update English status",
          "error"
        );
      }
    } catch (error) {
      this.showMessage(
        `Error updating English status: ${error.message}`,
        "error"
      );
    } finally {
      updateBtn.disabled = false;
      updateBtn.innerHTML = originalHTML;
    }
  }

//    ###CHANGED------------------------------------------------------------------------------------------------  
async initializeExportButton() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      if (result.authenticated && result.user) {
        this.currentUser = result.user;
        
        // "Export All" button logic is removed as requested.
        // We rely on the bulk selection export button which appears when items are selected.
      }
    } catch (error) {
      console.error("Error checking user permissions:", error);
    }
  }

  toggleAllApplicants(checked) {
    const checkboxes = document.querySelectorAll('.applicant-checkbox');
    checkboxes.forEach(cb => {
      cb.checked = checked;
      this.toggleApplicantSelection(cb.dataset.userCode, checked);
    });
  }

  updateBulkExportButton() {
    const bulkExportBtn = document.getElementById('bulkExportBtn');
    const count = this.selectedApplicants.size;

    if (bulkExportBtn) {
      if (count > 0) {
        bulkExportBtn.classList.remove('hidden');
        bulkExportBtn.classList.add('flex');
        bulkExportBtn.innerHTML = `
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Export Selected (${count})
        `;
      } else {
        bulkExportBtn.classList.add('hidden');
        bulkExportBtn.classList.remove('flex');
      }
    }
  }

  async exportSelectedApplicants() {
    if (this.selectedApplicants.size === 0) {
      this.showMessage('No applicants selected', 'error');
      return;
    }

    // Show export options modal for bulk export
    this.showBulkExportOptionsModal();
  }

  showBulkExportOptionsModal() {
    let modal = document.getElementById('sharedExportOptionsModal');
    if (!modal) {
      modal = this.createSharedExportOptionsModal();
      document.body.appendChild(modal);
    }

    // Update modal text
    document.getElementById('exportModalTitle').textContent = 'Export Selected Applicants';
    document.getElementById('exportModalDescription').textContent = 
      `Exporting ${this.selectedApplicants.size} applicants. Select data columns to include:`;

    // Remove old click handler and add new one
    const confirmBtn = modal.querySelector('#confirmExportBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', () => {
      this.executeBulkExport();
    });

    // Show modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  createSharedExportOptionsModal() {
    const modal = document.createElement('div');
    modal.id = 'sharedExportOptionsModal';
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center hidden z-50';

    modal.innerHTML = `
      <div class="mx-auto p-6 border w-11/12 max-w-md shadow-lg rounded-lg bg-white">
        <div class="flex items-center justify-between pb-4 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900" id="exportModalTitle">Export Options</h3>
          <button class="export-modal-close text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="mt-4">
          <p class="text-sm text-gray-600 mb-4" id="exportModalDescription">
            Select data columns to include
          </p>

          <div class="space-y-3" id="exportSectionsContainer">
            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="checkbox" class="export-section-checkbox w-4 h-4" value="personal" checked>
              <span class="text-sm font-medium text-gray-700">Personal Info (Age, Gender, Citizenship...)</span>
            </label>

            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="checkbox" class="export-section-checkbox w-4 h-4" value="application" checked>
              <span class="text-sm font-medium text-gray-700">Application Data (Status, Dates, Offer...)</span>
            </label>

            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="checkbox" class="export-section-checkbox w-4 h-4" value="education" checked>
              <span class="text-sm font-medium text-gray-700">Education History (Degree, Year, Subject...)</span>
            </label>
          </div>

          <div class="mt-6 flex gap-3">
            <button id="confirmExportBtn" class="btn-ubc flex-1">
              Export Selected
            </button>
            <button class="export-modal-close btn-ubc-outline">
              Cancel
            </button>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    modal.querySelectorAll('.export-modal-close').forEach(btn => {
      btn.addEventListener('click', () => this.closeExportModal());
    });

    return modal;
  }

  showExportOptionsModal(userCode, userName) {
    // Close the actions dropdown first
    const existingActionsMenu = document.querySelector('.actions-dropdown');
    if (existingActionsMenu) {
      existingActionsMenu.remove();
    }

    // Rest of your existing code...
    let modal = document.getElementById('sharedExportOptionsModal');
    if (!modal) {
      modal = this.createSharedExportOptionsModal();
      document.body.appendChild(modal);
    }

    modal.dataset.userCode = userCode;
    document.getElementById('exportModalTitle').textContent = 'Export Options';
    document.getElementById('exportModalDescription').textContent = `Exporting data for: ${userName}`;

    const confirmBtn = modal.querySelector('#confirmExportBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', () => {
      this.exportSingleApplicant();
    });

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  closeExportModal() {
    const modal = document.getElementById('sharedExportOptionsModal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }

  getSelectedExportSections() {
    const checkboxes = document.querySelectorAll('.export-section-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
  }

  async executeBulkExport() {
    const sections = this.getSelectedExportSections();

    if (sections.length === 0) {
      this.showMessage('Please select at least one section to export', 'error');
      return;
    }

    const confirmBtn = document.querySelector('#confirmExportBtn');
    const originalHTML = confirmBtn.innerHTML;
    
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `
      <svg class="w-5 h-5 animate-spin mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
      </svg>
    `;

    try {
      const response = await fetch('/api/export/selected', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          user_codes: Array.from(this.selectedApplicants),
          sections: sections
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const dateStr = new Date().toISOString().slice(0, 10);
      a.download = `selected_applicants_${this.selectedApplicants.size}_${dateStr}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showMessage(`Successfully exported ${this.selectedApplicants.size} applicants`, 'success');
      
      this.closeExportModal();
      this.selectedApplicants.clear();
      document.querySelectorAll('.applicant-checkbox').forEach(cb => cb.checked = false);
      const selectAllCb = document.getElementById('selectAllCheckbox');
      if(selectAllCb) selectAllCb.checked = false;
      this.updateBulkExportButton();

    } catch (error) {
      console.error('Export error:', error);
      this.showMessage(`Failed to export: ${error.message}`, 'error');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = originalHTML;
    }
  }
  async exportSingleApplicant() {
    const modal = document.getElementById('sharedExportOptionsModal');
    const userCode = modal.dataset.userCode;
    const sections = this.getSelectedExportSections();

    if (sections.length === 0) {
      this.showMessage('Please select at least one section to export', 'error');
      return;
    }

    const confirmBtn = modal.querySelector('#confirmExportBtn');
    const originalHTML = confirmBtn.innerHTML;

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `
    <svg class="w-5 h-5 animate-spin mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
    </svg>
  `;

    try {
      const response = await fetch(`/api/export/single/${userCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ sections })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const dateStr = new Date().toISOString().slice(0, 10);
      a.download = `applicant_${userCode}_${sections.join('_')}_${dateStr}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      this.showMessage('Successfully exported applicant data', 'success');
      this.closeExportModal();

    } catch (error) {
      console.error('Export error:', error);
      this.showMessage(`Failed to export: ${error.message}`, 'error');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = originalHTML;
    }
  }

  // NOTE: Ensure you are calling this method, not 'showApplicants'
  displayApplicants(applicants) {
    const container = document.getElementById("applicantsContainer");

    if (applicants.length === 0) {
      const searchInput = document.getElementById("searchInput");
      const isSearching = searchInput && searchInput.value.trim() !== "";

      if (isSearching) {
        container.innerHTML = `
        <div class="no-data-state">
          <h3 class="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p>No applicants match your search criteria. Try adjusting your search terms.</p>
        </div>`;
      } else {
        container.innerHTML = `
        <div class="no-data-state">
          <h3 class="text-lg font-medium text-gray-900 mb-2">No applicants yet</h3>
          <p>Upload a CSV file to see applicant data here.</p>
        </div>`;
      }
      return;
    }

    const searchInput = document.getElementById("searchInput");
    const isSearching = searchInput && searchInput.value.trim() !== "";
    const resultText = isSearching
      ? `<div class="mb-4 text-sm text-gray-600 bg-blue-50 px-4 py-2 rounded-lg">
         Showing <span class="font-semibold">${applicants.length}</span> of <span class="font-semibold">${this.allApplicants.length}</span> applicants
       </div>`
      : "";

    const table = `
    ${resultText}
    <div class="overflow-x-auto">
      <table class="modern-table">
        <thead>
          <tr>
            <th style="width: 3%;">
              <input type="checkbox" id="selectAllCheckbox" class="w-4 h-4" onchange="window.applicantsManager.toggleAllApplicants(this.checked)">
            </th>
            <th style="width: 25%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('applicant')">
              <div class="flex items-center justify-between">
                <span>Applicant</span>
                ${this.getSortIcon('applicant')}
              </div>
            </th>
            <th style="width: 14%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('status')">
              <div class="flex items-center justify-center gap-2">
                <span>Application Status</span>
                ${this.getSortIcon('status')}
              </div>
            </th>
            <th style="width: 14%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('submit_date')">
              <div class="flex items-center justify-center gap-2">
                <span>Submit Date</span>
                ${this.getSortIcon('submit_date')}
              </div>
            </th>
            <th style="width: 12%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('review_status')">
              <div class="flex items-center justify-center gap-2">
                <span>Review Status</span>
                ${this.getSortIcon('review_status')}
              </div>
            </th>
            <th style="width: 11%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('overall_rating')">
              <div class="flex items-center justify-center gap-2">
                <span>Overall Rating</span>
                ${this.getSortIcon('overall_rating')}
              </div>
            </th>
            <th style="width: 11%; cursor: pointer;" onclick="window.applicantsManager.sortApplicants('last_updated')">
              <div class="flex items-center justify-center gap-2">
                <span>Last Updated</span>
                ${this.getSortIcon('last_updated')}
              </div>
            </th>
            <th style="width: 10%;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${applicants
            .map(
              (applicant) => `
              <tr>
                <td class="text-center">
                  <input type="checkbox" class="applicant-checkbox w-4 h-4" 
                           data-user-code="${applicant.user_code}"
                           onchange="window.applicantsManager.toggleApplicantSelection('${applicant.user_code}', this.checked)">
                </td>
                <td>
                  <div class="applicant-card">
                    <div class="applicant-avatar">
                      ${this.getInitials(applicant.given_name, applicant.family_name)}
                    </div>
                    <div class="applicant-info">
                      <h3>${applicant.given_name} ${applicant.family_name}</h3>
                      <p>User Code: ${Math.floor(parseFloat(applicant.user_code))}</p>
                      <p>Student #: ${
                        applicant.student_number && applicant.student_number !== "NaN"
                          ? Math.floor(parseFloat(applicant.student_number))
                          : "N/A"
                      }</p>
                    </div>
                  </div>
                </td>
                <td>
                  ${this.getStatusBadge(applicant.status)}
                </td>
                <td>
                  ${
                    applicant.submit_date
                      ? `<div class="date-display">${new Date(applicant.submit_date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}</div>`
                      : '<div class="text-gray-400 text-sm">Not submitted</div>'
                  }
                </td>
                <td class="text-center">
                  <div style="display: flex; flex-direction: column; gap: 4px; align-items: center;">
                    ${this.getReviewStatusBadge(applicant.review_status || "Not Reviewed")}
                    ${
                      applicant.review_status_updated_at
                        ? `<span class="text-xs text-gray-500">Updated: ${new Date(
                            applicant.review_status_updated_at
                          ).toLocaleDateString()}</span>`
                        : ""
                    }
                  </div>
                </td>
                <td class="text-center">
                  ${this.getOverallRatingDisplay(applicant.overall_rating)}
                </td>
                <td>
                  <span class="${this.isRecentUpdate(applicant.seconds_since_update) ? "last-updated-recent" : "last-updated"}">
                    ${this.formatLastChanged(applicant.seconds_since_update)}
                  </span>
                </td>
                <td>
                  <div class="relative">
                    <button class="btn-actions" data-user-code="${applicant.user_code}" 
                            data-user-name="${applicant.given_name} ${applicant.family_name}"
                            onclick="window.applicantsManager.showActionsMenu(event, '${applicant.user_code}', '${applicant.given_name} ${applicant.family_name}')">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zM12 13a1 1 0 110-2 1 1 0 010 2zM12 20a1 1 0 110-2 1 1 0 010 2z"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;

    container.innerHTML = table;
    // If you have logic that re-checks checkboxes based on selectedApplicants set, call it here
  }

  showActionsMenu(event, userCode, userName) {
    event.stopPropagation();

    // Remove any existing menu
    const existingMenu = document.querySelector('.actions-dropdown');
    if (existingMenu) {
      existingMenu.remove();
    }
  
    // Create dropdown menu
    const menu = document.createElement('div');
    menu.className = 'actions-dropdown absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50';
    menu.innerHTML = `
    <button class="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 transition-colors duration-150 flex items-center gap-2 rounded-t-lg"
            onclick="window.applicantsManager.showApplicantModal('${userCode}', '${userName}')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
      </svg>
      View Details
    </button>
    <button class="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 transition-colors duration-150 flex items-center gap-2 rounded-b-lg"
            onclick="window.applicantsManager.showExportOptionsModal('${userCode}', '${userName}')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
      </svg>
      Export Applicant
    </button>
  `;

    // Position menu relative to button
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    menu.style.position = 'fixed';
    menu.style.top = `${rect.bottom + 5}px`;
    menu.style.left = `${rect.left - 150}px`; // Offset to the left

    document.body.appendChild(menu);

    // Close menu when clicking outside
    const closeMenu = (e) => {
      if (!menu.contains(e.target) && e.target !== button) {
        menu.remove();
        document.removeEventListener('click', closeMenu);
      }
    };
    //document.getElementById('applicantsContainer').classList.toggle("showing-dropdown");
    setTimeout(() => document.addEventListener('click', closeMenu), 10);
  }
  
  initializeClearDataButton() {
  const clearBtn = document.getElementById('clearAllDataBtn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => this.confirmClearAllData());
  }

  const cancelBtn = document.getElementById('cancelClearBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => this.closeConfirmModal());
  }

  const confirmBtn = document.getElementById('confirmClearBtn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => this.executeClearAllData());
  }
}

confirmClearAllData() {
  document.getElementById('confirmModal').classList.remove('hidden');
}

closeConfirmModal() {
  document.getElementById('confirmModal').classList.add('hidden');
}

async executeClearAllData() {
  const confirmBtn = document.getElementById('confirmClearBtn');
  const originalText = confirmBtn.textContent;
  
  confirmBtn.disabled = true;
  confirmBtn.textContent = 'Deleting...';
  
  try {
    const response = await fetch('/api/clear-all-data', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const result = await response.json();
    
    if (result.success) {
      this.closeConfirmModal();
      this.showClearDataMessage(result.message, 'success');
      
      // Reload the applicants list to show empty state
      setTimeout(() => {
        this.loadApplicants();
      }, 1000);
    } else {
      this.closeConfirmModal();
      this.showClearDataMessage(result.message, 'error');
    }
  } catch (error) {
    this.closeConfirmModal();
    this.showClearDataMessage(`Error: ${error.message}`, 'error');
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.textContent = originalText;
  }
}

showClearDataMessage(text, type) {
  const messageDiv = document.getElementById('clearDataMessage');
  if (!messageDiv) return;
  
  messageDiv.textContent = text;
  messageDiv.className = `mt-4 p-4 rounded-md ${
    type === 'success' 
      ? 'bg-green-100 text-green-700' 
      : 'bg-red-100 text-red-700'
  }`;
  messageDiv.classList.remove('hidden');
  
  setTimeout(() => {
    messageDiv.classList.add('hidden');
  }, 5000);
}

openUploadModal() {
  document.getElementById('uploadModal').classList.remove('hidden');
}

closeUploadModal() {
  document.getElementById('uploadModal').classList.add('hidden');
  // Reset file input
  const fileInput = document.getElementById('fileInput');
  const fileStatus = document.getElementById('fileStatus');
  const uploadBtn = document.getElementById('uploadBtn');
  const message = document.getElementById('message');
  
  if (fileInput) fileInput.value = '';
  if (fileStatus) fileStatus.textContent = 'No file chosen';
  if (uploadBtn) uploadBtn.disabled = true;
  if (message) message.classList.add('hidden');
}
}
