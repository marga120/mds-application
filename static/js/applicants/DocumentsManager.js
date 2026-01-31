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
    this.selectedDocumentId = null;
    this.userRole = null;
    this.loadDocumentTypes();
    this.loadUserRole();
  }

  /**
   * Load current user's role from API
   */
  async loadUserRole() {
    try {
      const response = await fetch('/api/auth/check-session');
      const result = await response.json();
      if (result.authenticated && result.user) {
        this.userRole = result.user.role;
      }
    } catch (error) {
      console.error('Failed to load user role:', error);
    }
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

    // Ensure user role is loaded
    if (!this.userRole) {
      await this.loadUserRole();
    }

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
    this.selectedDocumentId = null;
    this.renderContainer();
    this.updateTabBadge();
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

    // Reset PDF viewer when loading new applicant
    this.closePdfViewer();

    if (this.isLoading) {
      container.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-ubc-blue mx-auto mb-2"></div>
          Loading documents...
        </div>
      `;
      return;
    }

    const isAdmin = this.userRole === 'Admin';
    const isFaculty = this.userRole === 'Faculty';
    const canUpload = isAdmin || isFaculty;

    container.innerHTML = `
      ${canUpload ? this.renderUploadForm() : ''}
      <div class="mt-4">
        <h4 class="text-sm font-semibold text-ubc-blue mb-3 flex items-center">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          Documents (${this.documents.length})
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
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-3 rounded-lg border border-blue-200 mb-3">
        <h4 class="text-sm font-semibold text-ubc-blue mb-2 flex items-center">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
          </svg>
          Upload PDF
        </h4>

        <form id="documentUploadForm" class="space-y-2">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Type</label>
            <select id="documentType" class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue">
              ${typeOptions}
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Description (Optional)</label>
            <input type="text" id="documentDescription"
                   class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue"
                   placeholder="Brief description...">
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">PDF File (Max 16MB)</label>
            <input type="file" id="documentFile" accept=".pdf"
                   class="w-full text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ubc-blue file:mr-2 file:py-1 file:px-2 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-ubc-blue file:text-white hover:file:bg-blue-700">
          </div>

          <button type="submit" id="uploadDocumentBtn"
                  class="w-full px-3 py-2 bg-ubc-blue text-white text-sm rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
            </svg>
            Upload Document
          </button>
        </form>

        <div id="uploadFeedback" class="hidden mt-2 p-2 rounded-lg flex items-center">
          <span id="uploadFeedbackText" class="text-xs font-medium"></span>
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
        <div class="text-center py-6 text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
          <svg class="w-10 h-10 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-xs">No documents uploaded</p>
        </div>
      `;
    }

    const isAdmin = this.userRole === 'Admin';

    return `
      <div class="space-y-2">
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
    const isSelected = doc.id === this.selectedDocumentId;

    return `
      <div class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer ${isSelected ? 'ring-2 ring-ubc-blue bg-blue-50' : ''}"
           data-document-id="${doc.id}"
           onclick="documentsManager.viewDocument(${doc.id})">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h5 class="text-sm font-medium text-gray-900 truncate" title="${doc.original_filename}">${doc.original_filename}</h5>
            <p class="text-xs text-gray-500 mt-1">
              <span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                ${typeLabel}
              </span>
              <span class="ml-1">${fileSize}</span>
            </p>
            <p class="text-xs text-gray-400 mt-1 truncate">
              ${uploadDate}${doc.uploaded_by_name ? ` - ${doc.uploaded_by_name}` : ''}
            </p>
          </div>
          <div class="flex flex-col gap-1">
            <button onclick="event.stopPropagation(); documentsManager.openInNewTab(${doc.id})"
                    class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Open in New Tab">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
              </svg>
            </button>
            ${canDelete ? `
              <button onclick="event.stopPropagation(); documentsManager.deleteDocument(${doc.id}, '${doc.original_filename.replace(/'/g, "\\'")}')"
                      class="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
   * View a document inline in the PDF viewer panel
   * @param {number} documentId - Document ID
   */
  viewDocument(documentId) {
    this.selectedDocumentId = documentId;
    const doc = this.documents.find(d => d.id === documentId);

    const viewerContainer = document.getElementById('pdfViewerContainer');
    if (!viewerContainer) {
      // Fallback to new tab if viewer not available
      window.open(`/api/documents/view/${documentId}`, '_blank');
      return;
    }

    viewerContainer.innerHTML = `
      <div class="w-full h-full flex flex-col">
        <div class="flex items-center justify-between bg-gray-800 text-white px-4 py-2 rounded-t-lg">
          <div class="flex items-center gap-2 min-w-0">
            <svg class="w-5 h-5 flex-shrink-0 text-red-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z"/>
            </svg>
            <span class="text-sm font-medium truncate">${doc ? doc.original_filename : 'Document'}</span>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="documentsManager.openInNewTab(${documentId})"
                    class="p-1.5 hover:bg-gray-700 rounded transition-colors"
                    title="Open in New Tab">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
              </svg>
            </button>
            <button onclick="documentsManager.downloadDocument(${documentId})"
                    class="p-1.5 hover:bg-gray-700 rounded transition-colors"
                    title="Download">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
              </svg>
            </button>
            <button onclick="documentsManager.closePdfViewer()"
                    class="p-1.5 hover:bg-gray-700 rounded transition-colors"
                    title="Close">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        <iframe
          src="/api/documents/view/${documentId}"
          class="flex-1 w-full rounded-b-lg border-0"
          style="min-height: 500px;">
        </iframe>
      </div>
    `;

    // Update document list to show selection
    this.updateDocumentSelection();
  }

  /**
   * Open document in a new browser tab
   * @param {number} documentId - Document ID
   */
  openInNewTab(documentId) {
    window.open(`/api/documents/view/${documentId}`, '_blank');
  }

  /**
   * Close the PDF viewer and show placeholder
   */
  closePdfViewer() {
    this.selectedDocumentId = null;
    const viewerContainer = document.getElementById('pdfViewerContainer');
    if (viewerContainer) {
      viewerContainer.innerHTML = `
        <div class="text-center text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-sm">Select a document to preview</p>
        </div>
      `;
    }
    this.updateDocumentSelection();
  }

  /**
   * Update visual selection state for documents
   */
  updateDocumentSelection() {
    const cards = document.querySelectorAll('[data-document-id]');
    cards.forEach(card => {
      const docId = parseInt(card.getAttribute('data-document-id'));
      if (docId === this.selectedDocumentId) {
        card.classList.add('ring-2', 'ring-ubc-blue', 'bg-blue-50');
      } else {
        card.classList.remove('ring-2', 'ring-ubc-blue', 'bg-blue-50');
      }
    });
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
