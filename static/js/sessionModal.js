/**
 * Session Modal - Session Switcher UI Component
 * 
 * Provides a modal dialog for switching between academic sessions.
 * Displays sessions organized by campus (UBC Vancouver / UBC Okanagan)
 * with tabs for navigation. Shows applicant counts and highlights
 * the currently selected session.
 * 
 * Modal Structure:
 * +---------------------------------------------+
 * | Switch Session                            X |
 * +---------------------------------------------+
 * | [UBC Vancouver]  [UBC Okanagan]             |
 * +---------------------------------------------+
 * | * MDS 2027W          (145 applicants)       |
 * | o MDS 2026W          (132 applicants)       |
 * | o MDS 2025W          (128 applicants)       |
 * +---------------------------------------------+
 * |                    [Cancel]  [Switch]       |
 * +---------------------------------------------+
 * 
 * @module sessionModal
 */

class SessionModal {
    /**
     * Create a new SessionModal instance.
     * 
     * Initializes the modal component, creates the DOM elements,
     * and sets up event listeners. Does not show the modal until
     * open() is called.
     * 
     * @param {Object} options - Configuration options
     * @param {string} [options.containerId='sessionModalContainer'] - ID for modal container
     * @param {Function} [options.onSwitch] - Callback when session is switched
     * @param {Function} [options.onCancel] - Callback when modal is cancelled
     * 
     * @example
     *     const modal = new SessionModal({
     *         onSwitch: (session) => {
     *             console.log('Switched to:', session.name);
     *             reloadApplicants();
     *         }
     *     });
     */
    constructor(options = {}) {
        this.options = options;
        this.sessions = { 'UBC-V': [], 'UBC-O': [] };
        this.selectedSessionId = null;
        this.currentTab = 'UBC-V';
        this.isLoading = false;
        this.modalElement = null;
        
        this._createModalDOM();
        this._setupEventListeners();
    }

    /**
     * Create the modal DOM structure.
     * 
     * Builds the complete modal HTML including header, tabs,
     * session list container, and action buttons. Appends to body.
     * 
     * @private
     */
    _createModalDOM() {
        const modalHTML = `
            <div id="sessionModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden z-50 flex items-center justify-center">
                <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
                    <!-- Header -->
                    <div class="flex justify-between items-center px-6 py-4 border-b border-gray-200">
                        <h3 class="text-xl font-semibold text-gray-900">Switch Session</h3>
                        <button id="sessionModalClose" class="text-gray-400 hover:text-gray-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>

                    <!-- Campus Tabs -->
                    <div class="flex border-b border-gray-200">
                        <button id="tabUBC-V" class="campus-tab campus-tab-active flex-1 px-6 py-3 text-sm font-medium">
                            UBC Vancouver
                        </button>
                        <button id="tabUBC-O" class="campus-tab flex-1 px-6 py-3 text-sm font-medium">
                            UBC Okanagan
                        </button>
                    </div>

                    <!-- Session List -->
                    <div id="sessionListContainer" class="px-6 py-4 max-h-96 overflow-y-auto">
                        <!-- Sessions will be populated here -->
                    </div>

                    <!-- Footer -->
                    <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
                        <button id="sessionModalCancel" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
                            Cancel
                        </button>
                        <button id="sessionModalSwitch" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed" disabled>
                            Switch
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modalElement = document.getElementById('sessionModal');
    }

    /**
     * Set up event listeners for modal interactions.
     * 
     * Attaches click handlers for close button, backdrop click,
     * tab switching, session selection, and action buttons.
     * 
     * @private
     */
    _setupEventListeners() {
        // Close button
        document.getElementById('sessionModalClose').addEventListener('click', () => this.close());
        
        // Cancel button
        document.getElementById('sessionModalCancel').addEventListener('click', () => this.close());
        
        // Switch button
        document.getElementById('sessionModalSwitch').addEventListener('click', () => this.confirmSwitch());
        
        // Tab buttons
        document.getElementById('tabUBC-V').addEventListener('click', () => this.switchTab('UBC-V'));
        document.getElementById('tabUBC-O').addEventListener('click', () => this.switchTab('UBC-O'));
        
        // Backdrop click
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                this.close();
            }
        });
        
        // Escape key
        this.escapeHandler = (e) => {
            if (e.key === 'Escape' && !this.modalElement.classList.contains('hidden')) {
                this.close();
            }
        };
        document.addEventListener('keydown', this.escapeHandler);
    }

    /**
     * Open the modal and load sessions.
     * 
     * Shows the modal dialog, fetches sessions from the API,
     * and populates the session list. Highlights the currently
     * selected session.
     * 
     * @returns {Promise<void>}
     * 
     * @example
     *     await sessionModal.open();
     */
    async open() {
        this.modalElement.classList.remove('hidden');
        this._showLoading();
        
        try {
            // Fetch sessions from API
            const sessions = await this._fetchSessions();
            this.sessions = sessions;
            
            // Get current session
            this.selectedSessionId = SessionStore.getCurrentSessionId();
            
            // Render list for current tab
            this._renderSessionList();
            this._hideLoading();
        } catch (error) {
            console.error('Error loading sessions:', error);
            this._showError('Failed to load sessions. Please try again.');
        }
    }

    /**
     * Close the modal.
     * 
     * Hides the modal dialog and resets selection state.
     * Calls onCancel callback if provided and no switch was made.
     * 
     * @example
     *     sessionModal.close();
     */
    close() {
        this.modalElement.classList.add('hidden');
        if (this.options.onCancel) {
            this.options.onCancel();
        }
    }

    /**
     * Switch to a different campus tab.
     * 
     * Updates the active tab and re-renders the session list
     * for the selected campus.
     * 
     * @param {string} campus - Campus code ('UBC-V' or 'UBC-O')
     * 
     * @example
     *     sessionModal.switchTab('UBC-O');
     */
    switchTab(campus) {
        this.currentTab = campus;
        
        // Update tab styles
        document.querySelectorAll('.campus-tab').forEach(tab => {
            tab.classList.remove('campus-tab-active');
        });
        document.getElementById(`tab${campus}`).classList.add('campus-tab-active');
        
        // Re-render session list
        this._renderSessionList();
    }

    /**
     * Select a session from the list.
     * 
     * Updates the selection state and highlights the selected
     * session in the UI. Does not persist until confirmSwitch().
     * 
     * @param {number} sessionId - ID of the session to select
     * 
     * @example
     *     sessionModal.selectSession(5);
     */
    selectSession(sessionId) {
        this.selectedSessionId = sessionId;
        
        // Update UI
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('session-item-selected');
            const radio = item.querySelector('.session-radio');
            if (radio) {
                radio.textContent = '○';
                radio.classList.remove('session-radio-selected');
            }
        });
        
        const selectedItem = document.getElementById(`session-${sessionId}`);
        if (selectedItem) {
            selectedItem.classList.add('session-item-selected');
            const radio = selectedItem.querySelector('.session-radio');
            if (radio) {
                radio.textContent = '●';
                radio.classList.add('session-radio-selected');
            }
        }
        
        // Enable switch button
        document.getElementById('sessionModalSwitch').disabled = false;
    }

    /**
     * Confirm and apply the session switch.
     * 
     * Persists the selected session to SessionStore, closes the
     * modal, and triggers the onSwitch callback to reload data.
     * 
     * @example
     *     sessionModal.confirmSwitch();
     */
    confirmSwitch() {
        if (!this.selectedSessionId) return;
        
        // Find selected session data
        const allSessions = [...this.sessions['UBC-V'], ...this.sessions['UBC-O']];
        const session = allSessions.find(s => s.id === this.selectedSessionId);
        
        if (!session) return;
        
        // Save to SessionStore
        SessionStore.setCurrentSessionId(session.id, {
            name: session.name,
            campus: session.campus,
            year: session.year
        });
        
        // Close modal
        this.close();
        
        // Call callback
        if (this.options.onSwitch) {
            this.options.onSwitch(session);
        }
        
        // Reload page to update data
        window.location.reload();
    }

    /**
     * Render the session list for the current tab.
     * 
     * Generates and injects HTML for all sessions in the current
     * campus tab. Shows applicant counts and selection state.
     * 
     * @private
     */
    _renderSessionList() {
        const container = document.getElementById('sessionListContainer');
        const sessions = this.sessions[this.currentTab] || [];
        
        if (sessions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                    </svg>
                    <p>No sessions found for ${this.currentTab === 'UBC-V' ? 'UBC Vancouver' : 'UBC Okanagan'}</p>
                </div>
            `;
            return;
        }
        
        // Sort by year descending
        const sortedSessions = [...sessions].sort((a, b) => b.year - a.year);
        
        const html = sortedSessions.map(session => 
            this._renderSessionItem(session, session.id === this.selectedSessionId)
        ).join('');
        
        container.innerHTML = html;
        
        // Attach click handlers
        container.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = parseInt(item.dataset.sessionId);
                this.selectSession(sessionId);
            });
        });
    }

    /**
     * Render a single session item.
     * 
     * Generates HTML for one session in the list including
     * selection indicator, name, and applicant count.
     * 
     * @private
     * @param {Object} session - Session data object
     * @param {number} session.id - Session ID
     * @param {string} session.name - Display name
     * @param {number} session.applicant_count - Number of applicants
     * @param {boolean} isSelected - Whether this session is selected
     * @returns {string} HTML string for the session item
     */
    _renderSessionItem(session, isSelected) {
        return `
            <div id="session-${session.id}" 
                 class="session-item ${isSelected ? 'session-item-selected' : ''}" 
                 data-session-id="${session.id}">
                <div class="flex items-center justify-between p-4 border border-gray-200 rounded-md mb-2 cursor-pointer hover:bg-gray-50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="session-radio ${isSelected ? 'session-radio-selected' : ''}">
                            ${isSelected ? '●' : '○'}
                        </div>
                        <div>
                            <div class="font-medium text-gray-900">${session.name}</div>
                            <div class="text-sm text-gray-500">${session.session_abbrev || ''}</div>
                        </div>
                    </div>
                    <div class="text-sm text-gray-600">
                        <span class="bg-gray-100 px-3 py-1 rounded-full">
                            ${session.applicant_count || 0} applicants
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Show loading state in the modal.
     * 
     * Displays a loading spinner in the session list area
     * while fetching data from the API.
     * 
     * @private
     */
    _showLoading() {
        this.isLoading = true;
        const container = document.getElementById('sessionListContainer');
        container.innerHTML = `
            <div class="flex justify-center items-center py-12">
                <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
        `;
        document.getElementById('sessionModalSwitch').disabled = true;
    }

    /**
     * Hide loading state.
     * 
     * Removes the loading spinner after data is loaded.
     * 
     * @private
     */
    _hideLoading() {
        this.isLoading = false;
    }

    /**
     * Show error state in the modal.
     * 
     * Displays an error message if session loading fails.
     * 
     * @private
     * @param {string} message - Error message to display
     */
    _showError(message) {
        const container = document.getElementById('sessionListContainer');
        container.innerHTML = `
            <div class="text-center py-8">
                <svg class="w-12 h-12 mx-auto mb-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div class="text-red-600 mb-4">${message}</div>
                <button id="retryLoadSessions" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                    Retry
                </button>
            </div>
        `;
        
        document.getElementById('retryLoadSessions').addEventListener('click', () => {
            this.open();
        });
    }

    /**
     * Fetch sessions from the API.
     * 
     * Retrieves all non-archived sessions grouped by campus.
     * 
     * @private
     * @returns {Promise<Object>} Sessions grouped by campus
     */
    async _fetchSessions() {
        const response = await fetch('/api/sessions');
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message || 'Failed to fetch sessions');
        }
        
        return result.sessions || { 'UBC-V': [], 'UBC-O': [] };
    }

    /**
     * Destroy the modal instance.
     * 
     * Removes the modal from the DOM and cleans up event listeners.
     * Call this when the modal is no longer needed.
     * 
     * @example
     *     sessionModal.destroy();
     */
    destroy() {
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler);
        }
        if (this.modalElement) {
            this.modalElement.remove();
        }
        this.modalElement = null;
        this.sessions = null;
    }
}

// Export for use in other modules
window.SessionModal = SessionModal;
