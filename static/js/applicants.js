class ApplicantsManager {
  constructor() {
    this.allApplicants = [];
    this.sessionName = ""; // Add property to store session name
    this.initializeEventListeners();
    this.loadSessionName(); // Load session name first
    this.loadApplicants();
    this.initializeActionButtons();
  }

  initializeEventListeners() {
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadBtn");
    const searchInput = document.getElementById("searchInput");
    const searchFilter = document.getElementById("searchFilter");

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
  }

  // Debug version of loadSessionName method
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
      console.error("💥 Failed to load session name:", error);
      // Fallback to default
      this.sessionName = "Default Session";
      this.updateSectionTitle();
    }
  }

  // Debug version of updateSectionTitle method
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

  displayApplicants(applicants) {
    const container = document.getElementById("applicantsContainer");

    if (applicants.length === 0) {
      const searchInput = document.getElementById("searchInput");
      const isSearching = searchInput.value.trim() !== "";

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
    const isSearching = searchInput.value.trim() !== "";
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
              <th style="width: 28%;">Applicant</th>
              <th style="width: 14%;">Student Number</th>
              <th style="width: 16%;">Application Status</th>
              <th style="width: 16%;">Submit Date</th>
              <th style="width: 13%;">Overall Rating</th>
              <th style="width: 13%;">Last Updated</th>
              <th style="width: 10%;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${applicants
              .map(
                (applicant) => `
                <tr>
                  <td>
                    <div class="applicant-card">
                      <div class="applicant-avatar">
                        ${this.getInitials(
                          applicant.given_name,
                          applicant.family_name
                        )}
                      </div>
                      <div class="applicant-info">
                        <h3>${applicant.given_name} ${
                  applicant.family_name
                }</h3>
                        <p>User Code: ${Math.floor(
                          parseFloat(applicant.user_code)
                        )}</p>
                      </div>
                    </div>
                  </td>
                  <td class="text-center">
                    ${
                      applicant.student_number &&
                      applicant.student_number !== "NaN"
                        ? `<span class="text-sm font-mono text-gray-800">${Math.floor(
                            parseFloat(applicant.student_number)
                          )}</span>`
                        : '<span class="text-xs text-gray-400">N/A</span>'
                    }
                  </td>
                  <td>
                    ${this.getStatusBadge(applicant.status)}
                  </td>
                  <td>
                    ${
                      applicant.submit_date
                        ? `<div class="date-display">${new Date(
                            applicant.submit_date
                          ).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}</div>`
                        : '<div class="text-gray-400 text-sm">Not submitted</div>'
                    }
                  </td>
                  <td class="text-center">
                    ${this.getOverallRatingDisplay(applicant.overall_rating)}
                  </td>
                  <td>
                    <span class="${
                      this.isRecentUpdate(applicant.seconds_since_update)
                        ? "last-updated-recent"
                        : "last-updated"
                    }">
                      ${this.formatLastChanged(applicant.seconds_since_update)}
                    </span>
                  </td>
                  <td>
                    <button class="btn-actions" data-user-code="${
                      applicant.user_code
                    }" data-user-name="${applicant.given_name} ${
                  applicant.family_name
                }">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zM12 13a1 1 0 110-2 1 1 0 010 2zM12 20a1 1 0 110-2 1 1 0 010 2z"></path>
                      </svg>
                    </button>
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
    const searchTerm = document
      .getElementById("searchInput")
      .value.toLowerCase()
      .trim();
    const filterBy = document.getElementById("searchFilter").value;

    if (searchTerm === "") {
      this.displayApplicants(this.allApplicants);
      return;
    }

    const filteredApplicants = this.allApplicants.filter((applicant) => {
      if (filterBy === "all") {
        return (
          (applicant.given_name &&
            applicant.given_name.toLowerCase().includes(searchTerm)) ||
          (applicant.family_name &&
            applicant.family_name.toLowerCase().includes(searchTerm)) ||
          applicant.user_code.toLowerCase().includes(searchTerm) ||
          (applicant.student_number &&
            applicant.student_number
              .toString()
              .toLowerCase()
              .includes(searchTerm)) ||
          (applicant.status && this.matchesStatus(applicant.status, searchTerm))
        );
      } else if (filterBy === "status") {
        return (
          applicant.status && this.matchesStatus(applicant.status, searchTerm)
        );
      } else {
        const fieldValue = applicant[filterBy];
        return (
          fieldValue && fieldValue.toString().toLowerCase().includes(searchTerm)
        );
      }
    });

    this.displayApplicants(filteredApplicants);
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

    // Show Comments & Ratings tab by default
    this.showTab("comments-ratings");

    this.loadRatings(userCode);

    this.loadMyRating(userCode);

    // Update rating form for viewers
    this.updateRatingFormForViewer();

    this.loadTestScores(userCode);

    this.loadInstitutionInfo(userCode);

    this.loadApplicationStatus(userCode);

    this.loadPrerequisites(userCode);
  }

  createApplicantModal() {
    const modal = document.createElement("div");
    modal.id = "applicantModal";
    modal.className =
      "fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50";

    modal.innerHTML = `
    <div class="relative top-5 mx-auto p-6 border w-11/12 max-w-4xl shadow-lg rounded-lg bg-white mb-10">
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
            Prerequisite Courses
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
      <div class="mt-6 max-h-96 overflow-y-auto">
        <!-- Applicant Info Tab -->
        <div id="applicant-info" class="tab-content hidden">
          <div id="applicantInfoContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading applicant information...
            </div>
          </div>
        </div>

        <!-- Institution Info Tab -->
        <div id="institution-info" class="tab-content hidden">
          <div id="institutionInfoContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading institution information...
            </div>
          </div>
        </div>

        <!-- Test Scores Tab -->
        <div id="test-scores" class="tab-content hidden">
          <div id="testScoresContainer" class="space-y-6 min-h-0">
            <div class="text-center py-8 text-gray-500">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
              Loading test scores...
            </div>
          </div>
        </div>

        <!-- Prerequisite Courses Tab -->
        <div id="prerequisite-courses" class="tab-content hidden">
          <div class="max-h-96 overflow-y-auto pr-2">
            <div class="mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">Prerequisite Courses</h4>
              <div id="prerequisitesContainer" class="bg-blue-50 p-6 rounded-lg border border-blue-200">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Computer Science:</label>
                    <input type="text" id="csInput" class="input-ubc w-full" placeholder="Enter review of Computer Science prerequisite courses">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Statistics:</label>
                    <input type="text" id="statInput" class="input-ubc w-full" placeholder="Enter review of Statistics prerequisite courses">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Math:</label>
                    <input type="text" id="mathInput" class="input-ubc w-full" placeholder="Enter review of Math prerequisite courses">
                  </div>
                  <div id="prerequisiteButtons" class="flex gap-3 mt-4">
                    <button id="savePrerequisitesBtn" class="btn-ubc">Save Prerequisites Review</button>
                    <button id="clearPrerequisitesBtn" class="btn-ubc-outline">Clear</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments & Ratings Tab -->
        <div id="comments-ratings" class="tab-content">
          <div class="max-h-96 overflow-y-auto pr-2">

            <!-- Add/Edit Rating Section -->
            <div id="ratingFormSection" class="bg-blue-50 p-6 rounded-lg mb-6">
              <h4 class="text-lg font-semibold text-gray-900 mb-4">Your Rating & Comment</h4>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Rating (0.0 - 10.0)</label>
                  <input type="number" id="ratingInput" min="0.0" max="10.0" step="0.1" class="input-ubc w-full" placeholder="Enter rating (e.g., 8.5)">
                  <p class="text-xs text-gray-500 mt-1">Enter a rating between 0.0 and 10.0</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Comment</label>
                  <textarea id="commentTextarea" rows="3" class="input-ubc w-full resize-none" placeholder="Add your comments about this applicant..."></textarea>
                </div>
                <div class="flex gap-3">
                  <button id="saveRatingBtn" class="btn-ubc">Save Rating</button>
                  <button id="clearRatingBtn" class="btn-ubc-outline">Clear</button>
                </div>
              </div>
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
        <div id="status-tab" class="tab-content hidden">
          <div class="max-h-96 overflow-y-auto pr-2">
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
                          <option value="Waitlist">Waitlist</option>
                          <option value="Offer">Offer</option>
                          <option value="CoGS">CoGS</option>
                          <option value="Offer Sent">Offer Sent</option>
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
    modal.querySelector("#saveRatingBtn").addEventListener("click", () => {
      this.saveRating();
    });

    modal.querySelector("#clearRatingBtn").addEventListener("click", () => {
      this.clearRatingForm();
    });

    modal.querySelector("#updateStatusBtn").addEventListener("click", () => {
      this.updateStatus();
    });

    modal.querySelector("#cancelStatusBtn").addEventListener("click", () => {
      this.loadAppStatus(modal.dataset.currentUserCode);
    });

    // Close modal when clicking outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
      }
    });

    const savePrereqBtn = modal.querySelector("#savePrerequisitesBtn");
    const clearPrereqBtn = modal.querySelector("#clearPrerequisitesBtn");

    if (savePrereqBtn) {
      savePrereqBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.savePrerequisites();
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

  async saveRating() {
    const modal = document.getElementById("applicantModal");
    const userCode = modal.dataset.currentUserCode;
    const rating = document.getElementById("ratingInput").value;
    const comment = document.getElementById("commentTextarea").value;

    if (!rating || rating === "") {
      this.showMessage("Please enter a rating", "error");
      return;
    }

    // Validate rating
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

    const saveBtn = document.getElementById("saveRatingBtn");
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const response = await fetch(`/api/ratings/${userCode}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rating: rating,
          comment: comment,
        }),
      });

      const result = await response.json();

      if (result.success) {
        this.showMessage(result.message, "success");
        this.loadRatings(userCode); // Reload all ratings
      } else {
        this.showMessage(result.message, "error");
      }
    } catch (error) {
      this.showMessage(`Error saving rating: ${error.message}`, "error");
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
          <div class="max-h-96 overflow-y-auto pr-2">
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
                    applicant.date_birth
                      ? new Date(applicant.date_birth).toLocaleDateString(
                          "en-CA"
                        )
                      : null
                  )}
                  ${this.renderInfoField("Gender", applicant.gender)}
                  ${this.renderInfoField(
                    "Age",
                    applicant.age ? `${applicant.age} years old` : null
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

        container.innerHTML = `
          <div class="max-h-96 overflow-y-auto pr-2">
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
      <div class="flex justify-between items-center">
        <span class="text-xs font-medium opacity-70">${label}:</span>
        <span class="${highlightClass} font-semibold">${value}</span>
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

  formatDate(dateString) {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
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
        container.innerHTML = `
          <div class="max-h-96 overflow-y-auto pr-2">
            <h4 class="text-xl font-semibold text-ubc-blue mb-6 flex items-center">
              <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
              </svg>
              Educational Background
            </h4>

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
                          ? `<p><span class="font-medium text-gray-700">Start Date:</span> ${new Date(
                              institution.start_date
                            ).toLocaleDateString()}</p>`
                          : ""
                      }
                      ${
                        institution.end_date
                          ? `<p><span class="font-medium text-gray-700">End Date:</span> ${new Date(
                              institution.end_date
                            ).toLocaleDateString()}</p>`
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
                          ? `<p><span class="font-medium text-gray-700">Date Conferred:</span> ${new Date(
                              institution.date_confer
                            ).toLocaleDateString()}</p>`
                          : ""
                      }
                      ${
                        institution.expected_confer_date
                          ? `<p><span class="font-medium text-gray-700">Expected Graduation:</span> ${new Date(
                              institution.expected_confer_date
                            ).toLocaleDateString()}</p>`
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
        container.innerHTML = `
          <div class="text-center py-12 text-gray-500">
            <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 3v18M13 3v18"></path>
            </svg>
            <h3 class="text-lg font-medium text-gray-400 mb-2">No Institution Information</h3>
            <p class="text-gray-400">No educational background information is available for this applicant.</p>
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

        // Update select dropdown
        document.getElementById("statusSelect").value = currentStatus;

        // Hide preview initially
        document.getElementById("statusPreview").classList.add("hidden");

        // Update status change buttons visibility based on user role
        this.updateStatusFormForViewer();

        // Add change listener for preview
        this.setupStatusPreview(currentStatus);
      }
    } catch (error) {
      console.error("Error loading applicant status:", error);
    }
  }

  updateStatusFormForViewer() {
    const statusButtons = document.getElementById("statusUpdateButtons");
    const statusSelect = document.getElementById("statusSelect");
    const statusChangeSection = document.getElementById("statusChangeSection");

    // Check user role from auth
    fetch("/api/auth/check-session")
      .then((response) => response.json())
      .then((result) => {
        if (
          result.authenticated &&
          (result.user?.role === "Admin" || result.user?.role === "Faculty")
        ) {
          // Admin and Faculty can update status - show everything
          if (statusChangeSection) {
            statusChangeSection.style.display = "block";
          }
          if (statusButtons) {
            statusButtons.style.display = "flex";
          }
          statusSelect.disabled = false;

          // Set title for Admin/Faculty
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
          // Viewers can see current status but not change it - hide the change section
          if (statusChangeSection) {
            statusChangeSection.style.display = "none";
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

        // Reload the entire status display
        this.loadApplicationStatus(userCode);
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
      case "Offer":
        badge.classList.add("bg-green-100", "text-green-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-green-400";
        break;
      case "CoGS":
        badge.classList.add("bg-blue-100", "text-blue-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-blue-400";
        break;
      case "Offer Sent":
        badge.classList.add("bg-purple-100", "text-purple-800");
        dot.className = "w-2 h-2 rounded-full mr-2 bg-purple-400";
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
        const applicationInfo = result.application_info;

        // Populate the input fields
        document.getElementById("csInput").value = applicationInfo.cs || "";
        document.getElementById("statInput").value = applicationInfo.stat || "";
        document.getElementById("mathInput").value = applicationInfo.math || "";
      }

      // Update prerequisites form for viewers
      this.updatePrerequisitesFormForViewer();
    } catch (error) {
      console.error("Error loading prerequisites:", error);
    }
  }

  async updatePrerequisitesFormForViewer() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      const prerequisiteButtons = document.getElementById(
        "prerequisiteButtons"
      );
      const csInput = document.getElementById("csInput");
      const statInput = document.getElementById("statInput");
      const mathInput = document.getElementById("mathInput");

      if (
        result.authenticated &&
        (result.user?.role === "Admin" || result.user?.role === "Faculty")
      ) {
        // Admin and Faculty can edit prerequisites
        prerequisiteButtons.style.display = "flex";
        csInput.disabled = false;
        statInput.disabled = false;
        mathInput.disabled = false;
      } else {
        // Viewers can only see the values
        prerequisiteButtons.style.display = "none";
        csInput.disabled = true;
        statInput.disabled = true;
        mathInput.disabled = true;

        // Update placeholder text for empty fields
        if (!csInput.value || csInput.value.trim() === "") {
          csInput.placeholder = "Not Provided";
        }
        if (!statInput.value || statInput.value.trim() === "") {
          statInput.placeholder = "Not Provided";
        }
        if (!mathInput.value || mathInput.value.trim() === "") {
          mathInput.placeholder = "Not Provided";
        }
      }
    } catch (error) {
      console.error("Error checking user permissions:", error);
    }
  }

  async savePrerequisites() {
    const userCode =
      document.getElementById("applicantModal").dataset.currentUserCode;
    const saveBtn = document.getElementById("savePrerequisitesBtn");

    if (!userCode) return;

    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const response = await fetch(
        `/api/applicant-application-info/${userCode}/prerequisites`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            cs: document.getElementById("csInput").value,
            stat: document.getElementById("statInput").value,
            math: document.getElementById("mathInput").value,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        this.showMessage(result.message, "success");
      } else {
        this.showMessage(result.message, "error");
      }
    } catch (error) {
      this.showMessage(`Error saving prerequisites: ${error.message}`, "error");
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    }
  }

  clearPrerequisites() {
    document.getElementById("csInput").value = "";
    document.getElementById("statInput").value = "";
    document.getElementById("mathInput").value = "";
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
}
