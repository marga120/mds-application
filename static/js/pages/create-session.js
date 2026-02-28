/**
 * Create Session Page Controller
 * Uses SessionService for all API calls. No direct fetch().
 */

import { sessionService } from "../services/session-service.js";
import { Notification } from "../components/notification.js";

class SessionManager {
  constructor() {
    this.initializeYearDropdown();
    this.initializeEventListeners();
    this.updateSessionNamePreview();
  }

  initializeYearDropdown() {
    const yearSelect = document.getElementById("sessionYear");
    if (!yearSelect) return;

    const currentYear = new Date().getFullYear();
    for (let year = 2024; year <= 2035; year++) {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      if (year === currentYear) option.selected = true;
      yearSelect.appendChild(option);
    }
  }

  initializeEventListeners() {
    const createBtn = document.getElementById("createSessionBtn");
    const updatePreview = () => this.updateSessionNamePreview();

    if (createBtn)
      createBtn.addEventListener("click", () => this.createSession());

    const programCode = document.getElementById("programCode");
    if (programCode) {
      programCode.addEventListener("input", (e) => {
        e.target.value = e.target.value.toUpperCase();
        updatePreview();
      });
    }

    document
      .getElementById("programName")
      ?.addEventListener("input", updatePreview);
    document
      .getElementById("sessionYear")
      ?.addEventListener("change", updatePreview);
    document
      .getElementById("sessionTerm")
      ?.addEventListener("change", updatePreview);

    document
      .querySelectorAll('input[name="campus"]')
      .forEach((r) => r.addEventListener("change", updatePreview));
  }

  _getSelectedCampus() {
    return (
      document.querySelector('input[name="campus"]:checked')?.value || "UBC-V"
    );
  }

  updateSessionNamePreview() {
    const preview = document.getElementById("sessionNamePreview");
    if (!preview) return;

    const code =
      document.getElementById("programCode")?.value.trim().toUpperCase() ||
      "OGMMDS";
    const year = document.getElementById("sessionYear")?.value || "2025";
    const term = document.getElementById("sessionTerm")?.value || "W1";
    const campus = this._getSelectedCampus();
    const campusShort = campus === "UBC-O" ? "O" : "V";

    preview.textContent = `${code}-${campusShort} ${year}${term}`;
  }

  _validateForm() {
    const errors = [];
    const code = document.getElementById("programCode")?.value.trim() || "";
    const name = document.getElementById("programName")?.value.trim() || "";
    const year = document.getElementById("sessionYear")?.value || "";
    const term = document.getElementById("sessionTerm")?.value || "";
    const campus = this._getSelectedCampus();

    if (!code) errors.push("Program code is required");
    else if (code.length < 2 || code.length > 10)
      errors.push("Program code must be 2-10 characters");
    else if (!/^[A-Z]+$/.test(code))
      errors.push("Program code must contain only uppercase letters");

    if (!name) errors.push("Program name is required");
    else if (name.length > 100)
      errors.push("Program name must be 100 characters or less");

    if (!year) errors.push("Year is required");
    else {
      const y = parseInt(year, 10);
      if (y < 2024 || y > 2035)
        errors.push("Year must be between 2024 and 2035");
    }

    if (!term) errors.push("Term is required");
    else if (!["W1", "W2", "S"].includes(term))
      errors.push("Invalid term selection");

    if (!campus || !["UBC-V", "UBC-O"].includes(campus))
      errors.push("Please select a campus");

    return { isValid: errors.length === 0, errors };
  }

  async createSession() {
    const validation = this._validateForm();
    if (!validation.isValid) {
      this._showMessage(validation.errors.join(". "), "error");
      return;
    }

    const createBtn = document.getElementById("createSessionBtn");
    const originalText = createBtn.textContent;
    createBtn.disabled = true;
    createBtn.textContent = "Creating Session...";

    try {
      const code = document
        .getElementById("programCode")
        .value.trim()
        .toUpperCase();
      const name = document.getElementById("programName").value.trim();
      const year = parseInt(document.getElementById("sessionYear").value, 10);
      const term = document.getElementById("sessionTerm").value;
      const campus = this._getSelectedCampus();
      const description =
        document.getElementById("sessionDescription")?.value.trim() || "";

      const result = await sessionService.createSession({
        program_code: code,
        program: name,
        session_abbrev: `${year}${term}`,
        year,
        campus,
        description,
      });

      this._showMessage(
        `Session "${result.session.name}" created successfully!`,
        "success",
      );

      if (window.SessionStore && result.session) {
        SessionStore.setCurrentSessionId(result.session.id, {
          name: result.session.name,
          campus: result.session.campus,
          year: result.session.year,
        });
      }

      setTimeout(() => {
        window.location.href = "/";
      }, 2000);
    } catch (error) {
      this._showMessage(error.message || "Failed to create session", "error");
      createBtn.disabled = false;
      createBtn.textContent = originalText;
    }
  }

  _showMessage(text, type) {
    const msg = document.getElementById("sessionMessage");
    if (!msg) return;
    msg.textContent = text;
    msg.className = `p-4 rounded-md ${type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`;
    msg.classList.remove("hidden");
    if (type === "error") setTimeout(() => msg.classList.add("hidden"), 5000);
  }
}

new SessionManager();
