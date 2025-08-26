/**
 * SESSIONS MANAGER
 * 
 * This file manages academic session information and display.
 * It handles loading and displaying the current academic session name
 * throughout the application interface for proper context.
 */

class SessionsManager {
  constructor() {
    this.selectedSessionFile = null;
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    const sessionFileInput = document.getElementById("sessionFileInput");
    const createSessionBtn = document.getElementById("createSessionBtn");
    const sessionName = document.getElementById("sessionName");
    const sessionDescription = document.getElementById("sessionDescription");

    if (sessionFileInput) {
      sessionFileInput.addEventListener("change", (e) => {
        this.handleSessionFileSelect(e.target.files[0]);
      });
    }

    if (createSessionBtn) {
      createSessionBtn.addEventListener("click", () => {
        this.createSession();
      });
    }

    if (sessionDescription) {
      sessionDescription.addEventListener("input", () => {
        this.validateSessionForm();
      });
    }
  }

  handleSessionFileSelect(file) {
    if (file && file.name.endsWith(".csv")) {
      this.selectedSessionFile = file;
      this.validateSessionForm();
      const fileStatusElement = document.getElementById("sessionFileStatus");
      if (fileStatusElement) {
        fileStatusElement.textContent = file.name;
      }

      const timestamp = new Date().toLocaleString();
      this.showSessionMessage(
        `Selected: ${file.name} at ${timestamp}`,
        "success"
      );

      // Show preview section if we're on the create session page
      const previewSection = document.getElementById("previewSection");
      if (previewSection) {
        previewSection.classList.remove("hidden");
        this.showSchemaPreview(file);
      }
    } else {
      this.showSessionMessage("Please select a CSV file", "error");
      this.selectedSessionFile = null;
      this.validateSessionForm();
      const fileStatusElement = document.getElementById("sessionFileStatus");
      if (fileStatusElement) {
        fileStatusElement.textContent = "No file chosen";
      }

      // Hide preview section
      const previewSection = document.getElementById("previewSection");
      if (previewSection) {
        previewSection.classList.add("hidden");
      }
    }
  }

  showSchemaPreview(file) {
    const schemaPreview = document.getElementById("schemaPreview");
    if (schemaPreview) {
      schemaPreview.innerHTML = `
        <div class="space-y-2">
          <p class="text-sm font-medium text-gray-700">File: ${file.name}</p>
          <p class="text-sm text-gray-600">Size: ${(file.size / 1024).toFixed(
            2
          )} KB</p>
          <p class="text-sm text-gray-500 italic">Schema detection will be implemented when CSV processing is added</p>
        </div>
      `;
    }
  }

  validateSessionForm() {
    const createSessionBtn = document.getElementById("createSessionBtn");

    if (!createSessionBtn) return;

    const isValid = this.selectedSessionFile;
    createSessionBtn.disabled = !isValid;
  }

  async createSession() {
    const sessionDescriptionElement =
      document.getElementById("sessionDescription");

    const sessionDescription = sessionDescriptionElement
      ? sessionDescriptionElement.value.trim()
      : "";

    if (!this.selectedSessionFile) {
      this.showSessionMessage("Please provide a CSV file", "error");
      return;
    }

    const createSessionBtn = document.getElementById("createSessionBtn");
    createSessionBtn.disabled = true;
    createSessionBtn.textContent = "Creating Session...";

    try {
      // For now, just simulate the API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      this.showSessionMessage(
        `Session will be created with auto-generated name! (Backend not implemented yet)`,
        "success"
      );

      if (sessionDescriptionElement) sessionDescriptionElement.value = "";

      const sessionFileInput = document.getElementById("sessionFileInput");
      if (sessionFileInput) sessionFileInput.value = "";

      this.selectedSessionFile = null;
      this.validateSessionForm();

      // Hide preview section
      const previewSection = document.getElementById("previewSection");
      if (previewSection) {
        previewSection.classList.add("hidden");
      }
    } catch (error) {
      this.showSessionMessage(`Error: ${error.message}`, "error");
    } finally {
      createSessionBtn.disabled = false;
      createSessionBtn.textContent = "Create Session";
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

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }
}
