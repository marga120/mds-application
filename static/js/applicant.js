class ApplicantManager {
  constructor() {
    this.allApplicants = [];
    this.initializeEventListeners();
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

  handleFileSelect(file) {
    if (file && file.name.endsWith(".csv")) {
      this.selectedFile = file;
      document.getElementById("uploadBtn").disabled = false;

      // Add timestamp to file selection
      const timestamp = new Date().toLocaleString();
      this.showMessage(`Selected: ${file.name} at ${timestamp}`, "success");
    } else {
      this.showMessage("Please select a CSV file", "error");
      document.getElementById("uploadBtn").disabled = true;
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
      const response = await fetch("/api/students");
      const result = await response.json();

      if (result.success) {
        this.allApplicants = result.students;
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
            <div class="text-gray-400 text-6xl mb-4">🔍</div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">No results found</h3>
            <p>No applicants match your search criteria. Try adjusting your search terms.</p>
          </div>`;
      } else {
        container.innerHTML = `
          <div class="no-data-state">
            <div class="text-gray-400 text-6xl mb-4">📋</div>
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
              <th style="width: 23%;">Applicant</th>
              <th style="width: 11%;">User Code</th>
              <th style="width: 12%;">Student Number</th>
              <th style="width: 14%;">Application Status</th>
              <th style="width: 15%;">Submit Date</th>
              <th style="width: 12%;">Overall Rating</th>
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
                      </div>
                    </div>
                  </td>
                  <td class="text-center">
                    <span class="user-code-badge">${Math.floor(
                      parseFloat(applicant.user_code)
                    )}</span>
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
                          })}</div>
                      <div class="date-secondary">${new Date(
                        applicant.submit_date
                      ).toLocaleDateString("en-US", {
                        weekday: "short",
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
      return '<span class="status-badge status-progress">⏳ In Progress</span>';
    } else {
      return `<span class="status-badge status-unsubmitted">${status}</span>`;
    }
  }

  getOverallRatingDisplay(rating) {
    if (!rating || rating === null) {
      return '<div class="text-gray-400 text-sm">No ratings</div>';
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

  showApplicantModal(userCode, userName) {
    // Create modal if it doesn't exist
    let modal = document.getElementById("applicantModal");
    if (!modal) {
      modal = this.createApplicantModal();
      document.body.appendChild(modal);
    }

    // Update modal content
    document.getElementById("modalApplicantName").textContent = userName;
    document.getElementById("modalUserCode").textContent = userCode;

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

    // Load ratings and show Comments & Ratings tab by default
    this.showTab("comments-ratings");
    this.loadRatings(userCode);
    this.loadMyRating(userCode);
  }

  createApplicantModal() {
    const modal = document.createElement("div");
    modal.id = "applicantModal";
    modal.className =
      "fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50";

    modal.innerHTML = `
      <div class="relative top-10 mx-auto p-6 border w-11/12 max-w-4xl shadow-lg rounded-lg bg-white mb-10">
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
          <nav class="flex space-x-8">
            <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="general-info">
              General Info
            </button>
            <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="academic-info">
              Academic Info
            </button>
            <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap active" data-tab="comments-ratings">
              Comments & Ratings
            </button>
            <button class="tab-button py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap" data-tab="test-scores">
              Test Scores
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="mt-6">
          <!-- General Info Tab -->
          <div id="general-info" class="tab-content hidden">
            <p class="text-gray-600">General information will be displayed here.</p>
          </div>

          <!-- Academic Info Tab -->
          <div id="academic-info" class="tab-content hidden">
            <p class="text-gray-600">Academic information will be displayed here.</p>
          </div>

          <!-- Comments & Ratings Tab -->
          <div id="comments-ratings" class="tab-content">
            <div class="max-h-96 overflow-y-auto pr-2">
              <!-- Add/Edit Rating Section -->
              <div class="bg-blue-50 p-6 rounded-lg mb-6">
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

          <!-- Test Scores Tab -->
          <div id="test-scores" class="tab-content hidden">
            <p class="text-gray-600">Test scores will be displayed here.</p>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    modal.querySelector(".modal-close").addEventListener("click", () => {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    });

    // Tab switching
    modal.addEventListener("click", (e) => {
      if (e.target.matches(".tab-button")) {
        const tabName = e.target.dataset.tab;
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

    // Close modal when clicking outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
      }
    });

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
            <p>No ratings yet. Be the first to rate this applicant!</p>
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
}
