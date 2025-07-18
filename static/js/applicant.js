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
    container.innerHTML = '<div class="loading">Loading...</div>';

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
        container.innerHTML =
          '<div class="no-data">No applicants match your search criteria.</div>';
      } else {
        container.innerHTML =
          '<div class="no-data">No applicants found. Upload a CSV file.</div>';
      }
      return;
    }

    const searchInput = document.getElementById("searchInput");
    const isSearching = searchInput.value.trim() !== "";
    const resultText = isSearching
      ? `<div class="search-results">Showing ${applicants.length} of ${this.allApplicants.length} applicants</div>`
      : "";

    const table = `
            ${resultText}
            <table>
                <thead>
                    <tr>
                        <th>User Code</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Student Number</th>
                        <th>Status</th>
                        <th>Submit Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${applicants
                      .map(
                        (applicant) => `
                        <tr>
                            <td>${applicant.user_code}</td>
                            <td>${applicant.given_name} ${
                          applicant.family_name
                        }</td>
                            <td>${applicant.email || "N/A"}</td>
                            <td>${applicant.student_number || "N/A"}</td>
                            <td>${applicant.status || "N/A"}</td>
                            <td>${
                              applicant.submit_date
                                ? new Date(
                                    applicant.submit_date
                                  ).toLocaleDateString()
                                : "N/A"
                            }</td>
                        </tr>
                    `
                      )
                      .join("")}
                </tbody>
            </table>
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
