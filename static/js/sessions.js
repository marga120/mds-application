/**
 * SESSIONS MANAGER
 *
 * This file manages academic session creation and display.
 * It handles the form-based session creation with validation,
 * real-time name preview, and API integration.
 */

class SessionManager {
  constructor() {
    this.initializeYearDropdown();
    this.initializeEventListeners();
    this.updateSessionNamePreview();
  }

  /**
   * Populate the year dropdown with years from 2024 to 2035
   */
  initializeYearDropdown() {
    const yearSelect = document.getElementById("sessionYear");
    if (!yearSelect) return;

    const currentYear = new Date().getFullYear();
    const startYear = 2024;
    const endYear = 2035;

    for (let year = startYear; year <= endYear; year++) {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      // Default to current year
      if (year === currentYear) {
        option.selected = true;
      }
      yearSelect.appendChild(option);
    }
  }

  initializeEventListeners() {
    const createSessionBtn = document.getElementById("createSessionBtn");
    const programCode = document.getElementById("programCode");
    const programName = document.getElementById("programName");
    const sessionYear = document.getElementById("sessionYear");
    const sessionTerm = document.getElementById("sessionTerm");
    const campusRadios = document.querySelectorAll('input[name="campus"]');

    // Create session button
    if (createSessionBtn) {
      createSessionBtn.addEventListener("click", () => {
        this.createSession();
      });
    }

    // Update preview on any field change
    const updatePreview = () => this.updateSessionNamePreview();

    if (programCode) {
      programCode.addEventListener("input", (e) => {
        // Force uppercase
        e.target.value = e.target.value.toUpperCase();
        updatePreview();
      });
    }

    if (programName) {
      programName.addEventListener("input", updatePreview);
    }

    if (sessionYear) {
      sessionYear.addEventListener("change", updatePreview);
    }

    if (sessionTerm) {
      sessionTerm.addEventListener("change", updatePreview);
    }

    campusRadios.forEach((radio) => {
      radio.addEventListener("change", updatePreview);
    });
  }

  /**
   * Get the currently selected campus value
   */
  getSelectedCampus() {
    const selected = document.querySelector('input[name="campus"]:checked');
    return selected ? selected.value : "UBC-V";
  }

  /**
   * Get campus short code (V or O) from full campus value
   */
  getCampusShort(campus) {
    return campus === "UBC-O" ? "O" : "V";
  }

  /**
   * Update the session name preview based on current form values
   */
  updateSessionNamePreview() {
    const previewElement = document.getElementById("sessionNamePreview");
    if (!previewElement) return;

    const programCode =
      document.getElementById("programCode")?.value.trim().toUpperCase() ||
      "OGMMDS";
    const year = document.getElementById("sessionYear")?.value || "2025";
    const term = document.getElementById("sessionTerm")?.value || "W1";
    const campus = this.getSelectedCampus();
    const campusShort = this.getCampusShort(campus);

    // Generate preview name: {program_code}-{campus_short} {year}{term}
    const sessionName = `${programCode}-${campusShort} ${year}${term}`;
    previewElement.textContent = sessionName;
  }

  /**
   * Validate all form fields
   * @returns {Object} { isValid: boolean, errors: string[] }
   */
  validateForm() {
    const errors = [];

    const programCode =
      document.getElementById("programCode")?.value.trim() || "";
    const programName =
      document.getElementById("programName")?.value.trim() || "";
    const year = document.getElementById("sessionYear")?.value || "";
    const term = document.getElementById("sessionTerm")?.value || "";
    const campus = this.getSelectedCampus();

    // Program code validation
    if (!programCode) {
      errors.push("Program code is required");
    } else if (programCode.length < 2 || programCode.length > 10) {
      errors.push("Program code must be 2-10 characters");
    } else if (!/^[A-Z]+$/.test(programCode)) {
      errors.push("Program code must contain only uppercase letters");
    }

    // Program name validation
    if (!programName) {
      errors.push("Program name is required");
    } else if (programName.length > 100) {
      errors.push("Program name must be 100 characters or less");
    }

    // Year validation
    if (!year) {
      errors.push("Year is required");
    } else {
      const yearNum = parseInt(year, 10);
      if (yearNum < 2024 || yearNum > 2035) {
        errors.push("Year must be between 2024 and 2035");
      }
    }

    // Term validation
    if (!term) {
      errors.push("Term is required");
    } else if (!["W1", "W2", "S"].includes(term)) {
      errors.push("Invalid term selection");
    }

    // Campus validation
    if (!campus || !["UBC-V", "UBC-O"].includes(campus)) {
      errors.push("Please select a campus");
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  /**
   * Create a new session via API
   */
  async createSession() {
    const validation = this.validateForm();

    if (!validation.isValid) {
      this.showSessionMessage(validation.errors.join(". "), "error");
      return;
    }

    const createSessionBtn = document.getElementById("createSessionBtn");
    const originalText = createSessionBtn.textContent;
    createSessionBtn.disabled = true;
    createSessionBtn.textContent = "Creating Session...";

    try {
      const programCode =
        document.getElementById("programCode")?.value.trim().toUpperCase() ||
        "";
      const programName =
        document.getElementById("programName")?.value.trim() || "";
      const year = parseInt(
        document.getElementById("sessionYear")?.value || "0",
        10
      );
      const term = document.getElementById("sessionTerm")?.value || "";
      const campus = this.getSelectedCampus();
      const description =
        document.getElementById("sessionDescription")?.value.trim() || "";

      // Generate session abbreviation: {year}{term}
      const sessionAbbrev = `${year}${term}`;

      const response = await fetch("/api/sessions/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          program_code: programCode,
          program: programName,
          session_abbrev: sessionAbbrev,
          year: year,
          campus: campus,
          description: description || '',
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Show success message
        this.showSessionMessage(
          `Session "${result.session.name}" created successfully!`,
          "success"
        );

        // Auto-switch to the newly created session using SessionStore
        if (window.SessionStore && result.session) {
          SessionStore.setCurrentSessionId(result.session.id, {
            name: result.session.name,
            campus: result.session.campus,
            year: result.session.year,
          });
        }

        // Redirect to applicants page after delay
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      } else {
        this.showSessionMessage(
          result.message || "Failed to create session",
          "error"
        );
        createSessionBtn.disabled = false;
        createSessionBtn.textContent = originalText;
      }
    } catch (error) {
      console.error("Error creating session:", error);
      this.showSessionMessage(`Error: ${error.message}`, "error");
      createSessionBtn.disabled = false;
      createSessionBtn.textContent = originalText;
    }
  }

  showSessionMessage(text, type) {
    const messageDiv = document.getElementById("sessionMessage");
    if (!messageDiv) return;

    messageDiv.textContent = text;
    messageDiv.className = `p-4 rounded-md ${
      type === "success"
        ? "bg-green-100 text-green-700"
        : "bg-red-100 text-red-700"
    }`;
    messageDiv.classList.remove("hidden");

    // Only auto-hide error messages
    if (type === "error") {
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    }
  }
}
