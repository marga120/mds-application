/**
 * DOCUMENTS MANAGER
 *
 * Handles document upload, viewing, and deletion for applicants.
 * Provides PDF document management functionality integrated with the applicant modal.
 */

class DocumentsManager {
  constructor() {
    this.currentUserCode = null;
    this.documents = [];
    this.documentTypes = [];
    this.isLoading = false;
    this.loadDocumentTypes();
  }

  /**
   * Load available document types from API
   */
  async loadDocumentTypes() {
    try {
      const response = await fetch('/api/documents/types');
      const result = await response.json();
      if (result.success) {
        this.documentTypes = result.types;
      }
    } catch (error) {
      console.error('Failed to load document types:', error);
      // Default types if API fails
      this.documentTypes = [
        { value: 'transcript', label: 'Transcript' },
        { value: 'recommendation_letter', label: 'Recommendation Letter' },
        { value: 'cv_resume', label: 'CV/Resume' },
        { value: 'statement_of_purpose', label: 'Statement of Purpose' },
        { value: 'other', label: 'Other' }
      ];
    }
  }

  /**
   * Load documents for an applicant
   * @param {string} userCode - Applicant's user code
   */
  async loadDocuments(userCode) {
    this.currentUserCode = userCode;
    this.isLoading = true;
    this.renderContainer();

    try {
      const response = await fetch(`/api/documents/${userCode}`);
      const result = await response.json();

      if (result.success) {
        this.documents = result.documents;
      } else {
        this.documents = [];
        console.error('Failed to load documents:', result.message);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      this.documents = [];
    }

    this.isLoading = false;
    this.renderContainer();
  }

  /**
   * Get document count for badge display
   * @param {string} userCode - Applicant's user code
   * @returns {Promise<number>} Document count
   */
  async getDocumentCount(userCode) {
    try {
      const response = await fetch(`/api/documents/count/${userCode}`);
      const result = await response.json();
      return result.success ? result.count : 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Render the documents container
   */
  renderContainer() {
    const container = document.getElementById('documentsContainer');
    if (!container) return;

    if (this.isLoading) {
      container.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
          Loading documents...
        </div>
      `;
      return;
    }

    const isAdmin = window.userRole === 'Admin';
    const isFaculty = window.userRole === 'Faculty';
    const canUpload = isAdmin || isFaculty;

    container.innerHTML = `
      ${canUpload ? this.renderUploadForm() : ''}
      <div class="mt-6">
        <h4 class="text-lg font-semibold text-ubc-blue mb-4 flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Uploaded Documents (${this.documents.length})
        </h4>
        ${this.renderDocumentsList()}
      </div>
    `;

    // Attach event listeners
    this.attachEventListeners();
  }

  /**
   * Render the upload form
   */
  renderUploadForm() {
    const typeOptions = this.documentTypes.map(t =>
      `<option value="${t.value}">${t.label}</option>`
    ).join('');

    return `
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 mb-4">
        <h4 class="text-md font-semibold text-ubc-blue mb-3 flex items-center">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
          </svg>
          Upload Document
        </h4>

        <form id="documentUploadForm" class="space-y-3">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
              <select id="documentType" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue">
                ${typeOptions}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
              <input type="text" id="documentDescription"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue"
                     placeholder="Brief description...">
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Select PDF File</label>
            <div class="flex items-center gap-3">
              <input type="file" id="documentFile" accept=".pdf"
                     class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-ubc-blue file:text-white hover:file:bg-blue-700">
              <button type="submit" id="uploadDocumentBtn"
                      class="px-4 py-2 bg-ubc-blue text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                </svg>
                Upload
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-1">Maximum file size: 16MB. Only PDF files are accepted.</p>
          </div>
        </form>

        <div id="uploadFeedback" class="hidden mt-3 p-3 rounded-lg flex items-center">
          <span id="uploadFeedbackText" class="text-sm font-medium"></span>
        </div>
      </div>
    `;
  }

  /**
   * Render the list of documents
   */
  renderDocumentsList() {
    if (this.documents.length === 0) {
      return `
        <div class="text-center py-8 text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-sm">No documents uploaded yet</p>
        </div>
      `;
    }

    const isAdmin = window.userRole === 'Admin';

    return `
      <div class="space-y-3">
        ${this.documents.map(doc => this.renderDocumentCard(doc, isAdmin)).join('')}
      </div>
    `;
  }

  /**
   * Render a single document card
   * @param {Object} doc - Document object
   * @param {boolean} canDelete - Whether user can delete
   */
  renderDocumentCard(doc, canDelete) {
    const typeLabel = this.documentTypes.find(t => t.value === doc.document_type)?.label || doc.document_type;
    const fileSize = this.formatFileSize(doc.file_size);
    const uploadDate = this.formatDate(doc.created_at);

    return `
      <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between">
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h5 class="text-sm font-medium text-gray-900 truncate">${doc.original_filename}</h5>
              <p class="text-xs text-gray-500 mt-1">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                  ${typeLabel}
                </span>
                ${fileSize}
              </p>
              ${doc.description ? `<p class="text-xs text-gray-600 mt-1">${doc.description}</p>` : ''}
              <p class="text-xs text-gray-400 mt-1">
                Uploaded ${uploadDate}${doc.uploaded_by_name ? ` by ${doc.uploaded_by_name}` : ''}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2 ml-3">
            <button onclick="documentsManager.viewDocument(${doc.id})"
                    class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="View Document">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
            </button>
            <button onclick="documentsManager.downloadDocument(${doc.id})"
                    class="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="Download Document">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
              </svg>
            </button>
            ${canDelete ? `
              <button onclick="documentsManager.deleteDocument(${doc.id}, '${doc.original_filename.replace(/'/g, "\\'")}')"
                      class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Document">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Attach event listeners to the form
   */
  attachEventListeners() {
    const form = document.getElementById('documentUploadForm');
    if (form) {
      form.addEventListener('submit', (e) => this.handleUpload(e));
    }
  }

  /**
   * Handle document upload
   * @param {Event} e - Submit event
   */
  async handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('documentFile');
    const typeInput = document.getElementById('documentType');
    const descInput = document.getElementById('documentDescription');
    const uploadBtn = document.getElementById('uploadDocumentBtn');

    if (!fileInput.files || fileInput.files.length === 0) {
      this.showFeedback('Please select a file to upload', 'error');
      return;
    }

    const file = fileInput.files[0];

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.showFeedback('Only PDF files are allowed', 'error');
      return;
    }

    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
      this.showFeedback('File size exceeds 16MB limit', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', typeInput.value);
    formData.append('description', descInput.value);

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = `
      <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Uploading...
    `;

    try {
      const response = await fetch(`/api/documents/${this.currentUserCode}`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        this.showFeedback('Document uploaded successfully', 'success');
        // Clear form
        fileInput.value = '';
        descInput.value = '';
        // Reload documents
        await this.loadDocuments(this.currentUserCode);
        // Update tab badge
        this.updateTabBadge();
      } else {
        this.showFeedback(result.message || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      this.showFeedback('Upload failed. Please try again.', 'error');
    }

    uploadBtn.disabled = false;
    uploadBtn.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
      </svg>
      Upload
    `;
  }

  /**
   * View a document in a new tab
   * @param {number} documentId - Document ID
   */
  viewDocument(documentId) {
    window.open(`/api/documents/view/${documentId}`, '_blank');
  }

  /**
   * Download a document
   * @param {number} documentId - Document ID
   */
  downloadDocument(documentId) {
    window.location.href = `/api/documents/view/${documentId}?download=true`;
  }

  /**
   * Delete a document
   * @param {number} documentId - Document ID
   * @param {string} filename - Filename for confirmation
   */
  async deleteDocument(documentId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
      });

      const result = await response.json();

      if (result.success) {
        this.showFeedback('Document deleted successfully', 'success');
        await this.loadDocuments(this.currentUserCode);
        this.updateTabBadge();
      } else {
        this.showFeedback(result.message || 'Delete failed', 'error');
      }
    } catch (error) {
      console.error('Delete error:', error);
      this.showFeedback('Delete failed. Please try again.', 'error');
    }
  }

  /**
   * Show feedback message
   * @param {string} message - Message to display
   * @param {string} type - 'success' or 'error'
   */
  showFeedback(message, type) {
    const feedback = document.getElementById('uploadFeedback');
    const text = document.getElementById('uploadFeedbackText');

    if (!feedback || !text) return;

    text.textContent = message;
    feedback.className = `mt-3 p-3 rounded-lg flex items-center ${
      type === 'success'
        ? 'bg-green-100 text-green-800'
        : 'bg-red-100 text-red-800'
    }`;
    feedback.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
      feedback.classList.add('hidden');
    }, 5000);
  }

  /**
   * Update the documents tab badge count
   */
  async updateTabBadge() {
    const badge = document.getElementById('documentsTabBadge');
    if (badge) {
      badge.textContent = this.documents.length;
      badge.style.display = this.documents.length > 0 ? 'inline-flex' : 'none';
    }
  }

  /**
   * Format file size for display
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted file size
   */
  formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  }

  /**
   * Format date for display
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date
   */
  formatDate(dateString) {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  }
}

// Create global instance
const documentsManager = new DocumentsManager();
