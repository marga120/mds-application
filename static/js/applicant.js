class ApplicantManager {
  constructor() {
    this.allApplicants = [];
    this.initializeEventListeners();
    this.loadApplicants();
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
              <th style="width: 30%;">Applicant</th>
              <th style="width: 12%;">User Code</th>
              <th style="width: 18%;">Application Status</th>
              <th style="width: 18%;">Submit Date</th>
              <th style="width: 22%;">Last Updated</th>
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
                        <p class="text-xs text-gray-500">
                          ${
                            applicant.email && applicant.email !== "N/A"
                              ? `<a href="mailto:${applicant.email}" class="email-link">${applicant.email}</a>`
                              : "No email provided"
                          }
                        </p>
                      </div>
                    </div>
                  </td>
                  <td class="text-center">
                    <div class="space-y-1">
                      <div>
                        <span class="user-code-badge">${Math.floor(
                          parseFloat(applicant.user_code)
                        )}</span>
                      </div>
                      ${
                        applicant.student_number &&
                        applicant.student_number !== "NaN"
                          ? `<div class="text-xs text-gray-500">Student Number: ${applicant.student_number}</div>`
                          : '<div class="text-xs text-gray-400">No student number</div>'
                      }
                    </div>
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
                  <td>
                    <span class="${
                      this.isRecentUpdate(applicant.seconds_since_update)
                        ? "last-updated-recent"
                        : "last-updated"
                    }">
                      ${this.formatLastChanged(applicant.seconds_since_update)}
                    </span>
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

  isRecentUpdate(secondsAgo) {
    return secondsAgo < 60; // Less than 1 minute is considered recent
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
          applicant.user_code.toLowerCase().includes(searchTerm) ||
          (applicant.given_name &&
            applicant.given_name.toLowerCase().includes(searchTerm)) ||
          (applicant.family_name &&
            applicant.family_name.toLowerCase().includes(searchTerm)) ||
          (applicant.email &&
            applicant.email.toLowerCase().includes(searchTerm)) ||
          (applicant.student_number &&
            applicant.student_number
              .toString()
              .toLowerCase()
              .includes(searchTerm)) ||
          (applicant.status &&
            applicant.status.toLowerCase().includes(searchTerm))
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
}
