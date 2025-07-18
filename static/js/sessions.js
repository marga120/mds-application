class SessionManager {
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

    if (sessionName) {
      sessionName.addEventListener("input", () => {
        this.validateSessionForm();
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
    const sessionName = document.getElementById("sessionName");
    const createSessionBtn = document.getElementById("createSessionBtn");

    if (!sessionName || !createSessionBtn) return;

    const sessionNameValue = sessionName.value.trim();
    const isValid = sessionNameValue && this.selectedSessionFile;
    createSessionBtn.disabled = !isValid;
  }

  async createSession() {
    const sessionNameElement = document.getElementById("sessionName");
    const sessionDescriptionElement =
      document.getElementById("sessionDescription");

    if (!sessionNameElement) return;

    const sessionName = sessionNameElement.value.trim();
    const sessionDescription = sessionDescriptionElement
      ? sessionDescriptionElement.value.trim()
      : "";

    if (!this.selectedSessionFile || !sessionName) {
      this.showSessionMessage(
        "Please provide both session name and CSV file",
        "error"
      );
      return;
    }

    const createSessionBtn = document.getElementById("createSessionBtn");
    createSessionBtn.disabled = true;
    createSessionBtn.textContent = "Creating Session...";

    try {
      // For now, just simulate the API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      this.showSessionMessage(
        `Session "${sessionName}" would be created! (Backend not implemented yet)`,
        "success"
      );

      // Clear form after successful creation
      sessionNameElement.value = "";
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
