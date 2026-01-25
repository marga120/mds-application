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
        // TODO: Store options
        // TODO: Initialize state variables
        // TODO: Create modal DOM structure
        // TODO: Append to document body
        this.options = options;
        this.sessions = { 'UBC-V': [], 'UBC-O': [] };
        this.selectedSessionId = null;
        this.currentTab = 'UBC-V';
        this.isLoading = false;
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
        // TODO: Create modal container div
        // TODO: Create overlay backdrop
        // TODO: Create modal content wrapper
        // TODO: Create header with title and close button
        // TODO: Create campus tabs (UBC-V, UBC-O)
        // TODO: Create session list container
        // TODO: Create footer with Cancel/Switch buttons
        // TODO: Append to document body
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
        // TODO: Close button click -> close()
        // TODO: Backdrop click -> close()
        // TODO: Tab click -> switchTab()
        // TODO: Session item click -> selectSession()
        // TODO: Cancel button click -> close()
        // TODO: Switch button click -> confirmSwitch()
        // TODO: Escape key -> close()
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
        // TODO: Show modal (remove hidden class)
        // TODO: Set loading state
        // TODO: Fetch sessions from /api/sessions
        // TODO: Store sessions grouped by campus
        // TODO: Get current session ID from SessionStore
        // TODO: Render session list for current tab
        // TODO: Clear loading state
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
        // TODO: Hide modal (add hidden class)
        // TODO: Reset selected session to original
        // TODO: Call onCancel callback if applicable
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
        // TODO: Update currentTab state
        // TODO: Update tab button styles (active/inactive)
        // TODO: Re-render session list for new campus
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
        // TODO: Update selectedSessionId state
        // TODO: Update UI to show selection (radio button style)
        // TODO: Enable/disable Switch button based on selection
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
        // TODO: Get selected session data
        // TODO: Call SessionStore.setCurrentSessionId()
        // TODO: Close modal
        // TODO: Call onSwitch callback with session data
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
        // TODO: Get sessions for current campus tab
        // TODO: Sort by year descending
        // TODO: Generate HTML for each session item
        // TODO: Include radio button, name, applicant count
        // TODO: Highlight currently selected session
        // TODO: Inject HTML into session list container
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
        // TODO: Create session item HTML with:
        //   - Radio button or checkmark indicator
        //   - Session name
        //   - Applicant count badge
        //   - Click handler attribute
        // TODO: Add 'selected' class if isSelected
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
        // TODO: Set isLoading = true
        // TODO: Show spinner in session list container
        // TODO: Disable Switch button
    }

    /**
     * Hide loading state.
     * 
     * Removes the loading spinner after data is loaded.
     * 
     * @private
     */
    _hideLoading() {
        // TODO: Set isLoading = false
        // TODO: Remove spinner from container
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
        // TODO: Display error message in session list container
        // TODO: Add retry button
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
        // TODO: Fetch /api/sessions
        // TODO: Parse response JSON
        // TODO: Return sessions object or throw error
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
        // TODO: Remove modal element from DOM
        // TODO: Remove event listeners
        // TODO: Clear references
    }
}

// Export for use in other modules
window.SessionModal = SessionModal;
