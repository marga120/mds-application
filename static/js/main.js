class StudentManager {
  constructor() {
    this.allStudents = [];
    this.initializeEventListeners();
    this.loadStudents();
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
      this.filterStudents();
    });

    searchFilter.addEventListener("change", () => {
      this.filterStudents();
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

        this.loadStudents();
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

  async loadStudents() {
    const container = document.getElementById("studentsContainer");
    container.innerHTML = '<div class="loading">Loading...</div>';

    try {
      const response = await fetch("/api/students");
      const result = await response.json();

      if (result.success) {
        this.allStudents = result.students;
        this.displayStudents(this.allStudents);
      } else {
        container.innerHTML = `<div class="no-data">Error: ${result.message}</div>`;
      }
    } catch (error) {
      container.innerHTML = `<div class="no-data">Failed to load: ${error.message}</div>`;
    }
  }

  displayStudents(students) {
    const container = document.getElementById("studentsContainer");

    if (students.length === 0) {
      const searchInput = document.getElementById("searchInput");
      const isSearching = searchInput.value.trim() !== "";

      if (isSearching) {
        container.innerHTML =
          '<div class="no-data">No students match your search criteria.</div>';
      } else {
        container.innerHTML =
          '<div class="no-data">No students found. Upload a CSV file.</div>';
      }
      return;
    }

    const searchInput = document.getElementById("searchInput");
    const isSearching = searchInput.value.trim() !== "";
    const resultText = isSearching
      ? `<div class="search-results">Showing ${students.length} of ${this.allStudents.length} students</div>`
      : "";

    const table = `
            ${resultText}
            <table>
                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>Name</th>
                        <th>University</th>
                        <th>Year</th>
                        <th>Degree</th>
                        <th>Last Changed</th>
                    </tr>
                </thead>
                <tbody>
                    ${students
                      .map(
                        (student) => `
                        <tr>
                            <td>${student.student_id}</td>
                            <td>${student.student_name}</td>
                            <td>${student.university}</td>
                            <td>${student.year}</td>
                            <td>${student.degree}</td>
                            <td class="timestamp">
                                ${this.formatLastChanged(
                                  student.seconds_since_update
                                )}
                            </td>
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

  filterStudents() {
    const searchTerm = document
      .getElementById("searchInput")
      .value.toLowerCase()
      .trim();
    const filterBy = document.getElementById("searchFilter").value;

    if (searchTerm === "") {
      this.displayStudents(this.allStudents);
      return;
    }

    const filteredStudents = this.allStudents.filter((student) => {
      if (filterBy === "all") {
        return (
          student.student_id.toLowerCase().includes(searchTerm) ||
          student.student_name.toLowerCase().includes(searchTerm) ||
          student.university.toLowerCase().includes(searchTerm) ||
          student.degree.toLowerCase().includes(searchTerm) ||
          student.year.toString().includes(searchTerm)
        );
      } else {
        const fieldValue = student[filterBy];
        return fieldValue.toString().toLowerCase().includes(searchTerm);
      }
    });

    this.displayStudents(filteredStudents);
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

class AuthManager {
  constructor() {
    this.checkAuthentication();
    this.initializeLogout();
  }

  async checkAuthentication() {
    try {
      const response = await fetch("/api/auth/check-session");
      const result = await response.json();

      if (!result.authenticated) {
        window.location.href = "/login";
        return;
      }

      // Update UI with user info
      this.updateUserInfo(result.user);
    } catch (error) {
      console.error("Auth check failed:", error);
      window.location.href = "/login";
    }
  }

  updateUserInfo(user) {
    // Add user info to the left (where purple arrow points)
    const userInfoArea = document.getElementById("userInfo");
    if (userInfoArea) {
      userInfoArea.innerHTML = `
                <div class="text-left">
                    <div class="text-white text-base font-medium">Welcome, ${user.full_name}</div>
                    <div class="text-ubc-gray-light text-sm">${user.role}</div>
                </div>
            `;
    }

    // Add logout button to the far right (where red arrow points)
    const logoutArea = document.getElementById("logoutArea");
    if (logoutArea) {
      logoutArea.innerHTML = `
                <button id="logoutBtn" class="bg-white text-ubc-blue hover:bg-gray-100 px-6 py-2 rounded text-sm font-medium transition-colors shadow-sm">
                    Logout
                </button>
            `;
    }
  }

  initializeLogout() {
    document.addEventListener("click", (e) => {
      if (e.target.id === "logoutBtn") {
        this.handleLogout();
      }
    });
  }

  async handleLogout() {
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });

      const result = await response.json();

      if (result.success) {
        window.location.href = "/login";
      }
    } catch (error) {
      console.error("Logout error:", error);
      // Force redirect anyway
      window.location.href = "/login";
    }
  }
}

// Initialize the app when the page loads
document.addEventListener("DOMContentLoaded", function () {
  const studentManager = new StudentManager();
  new AuthManager();
});
