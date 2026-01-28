/**
 * Session Store - localStorage Session Management
 * 
 * Manages the currently selected academic session in localStorage.
 * Provides methods for getting, setting, and clearing the session selection.
 * Used by the session switcher UI and all data-fetching components to maintain
 * session context across page navigation and browser sessions.
 * 
 * Storage Key: 'mds_current_session_id'
 * 
 * @module sessionStore
 */

const SessionStore = {
    /**
     * localStorage key for storing current session ID
     * @constant {string}
     */
    STORAGE_KEY: 'mds_current_session_id',

    /**
     * localStorage key for storing current session metadata (name, campus)
     * @constant {string}
     */
    METADATA_KEY: 'mds_current_session_metadata',

    /**
     * Get the currently selected session ID from localStorage.
     * 
     * Retrieves the stored session ID. Returns null if no session is stored
     * or if the stored value is invalid.
     * 
     * @returns {number|null} The current session ID, or null if not set
     * 
     * @example
     *     const sessionId = SessionStore.getCurrentSessionId();
     *     if (sessionId) {
     *         fetch(`/api/applicants?session_id=${sessionId}`);
     *     }
     */
    getCurrentSessionId: function() {
        try {
            const sessionId = localStorage.getItem(this.STORAGE_KEY);
            if (!sessionId) return null;
            
            const parsed = parseInt(sessionId, 10);
            return isNaN(parsed) ? null : parsed;
        } catch (error) {
            console.error('Error getting session ID:', error);
            return null;
        }
    },

    /**
     * Set the current session ID in localStorage.
     * 
     * Stores the selected session ID for persistence across page loads.
     * Also stores session metadata for display purposes.
     * 
     * @param {number} sessionId - The session ID to store
     * @param {Object} [metadata] - Optional metadata about the session
     * @param {string} [metadata.name] - Session display name (e.g., 'MDS-V 2027W')
     * @param {string} [metadata.campus] - Campus code ('UBC-V' or 'UBC-O')
     * @param {number} [metadata.year] - Academic year
     * 
     * @example
     *     SessionStore.setCurrentSessionId(5, {
     *         name: 'MDS-V 2027W',
     *         campus: 'UBC-V',
     *         year: 2027
     *     });
     */
    setCurrentSessionId: function(sessionId, metadata = null) {
        try {
            localStorage.setItem(this.STORAGE_KEY, sessionId.toString());
            
            if (metadata) {
                localStorage.setItem(this.METADATA_KEY, JSON.stringify(metadata));
            }
            
            this._dispatchChange(sessionId, metadata);
        } catch (error) {
            console.error('Error setting session ID:', error);
        }
    },

    /**
     * Clear the current session from localStorage.
     * 
     * Removes both the session ID and metadata. Used when user logs out
     * or when session needs to be reset.
     * 
     * @example
     *     SessionStore.clearCurrentSession();
     */
    clearCurrentSession: function() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
            localStorage.removeItem(this.METADATA_KEY);
            
            this._dispatchChange(null, null);
        } catch (error) {
            console.error('Error clearing session:', error);
        }
    },

    /**
     * Get stored session metadata.
     * 
     * Retrieves the cached session metadata (name, campus, year) without
     * making an API call. Returns null if no metadata is stored.
     * 
     * @returns {Object|null} Session metadata object or null
     * @returns {string} returns.name - Session display name
     * @returns {string} returns.campus - Campus code
     * @returns {number} returns.year - Academic year
     * 
     * @example
     *     const metadata = SessionStore.getSessionMetadata();
     *     if (metadata) {
     *         document.getElementById('sessionBadge').textContent = metadata.name;
     *     }
     */
    getSessionMetadata: function() {
        try {
            const metadata = localStorage.getItem(this.METADATA_KEY);
            if (!metadata) return null;
            
            return JSON.parse(metadata);
        } catch (error) {
            console.error('Error getting session metadata:', error);
            return null;
        }
    },

    /**
     * Check if a session is currently selected.
     * 
     * Quick check to determine if user has an active session selection.
     * 
     * @returns {boolean} True if a session is selected, false otherwise
     * 
     * @example
     *     if (!SessionStore.hasSession()) {
     *         showSessionWarning();
     *     }
     */
    hasSession: function() {
        return this.getCurrentSessionId() !== null;
    },

    /**
     * Initialize session from API if none stored.
     * 
     * Checks if a session is stored; if not, fetches the most recent session
     * from the API and stores it. Used during app initialization.
     * 
     * @returns {Promise<number|null>} Promise resolving to session ID or null
     * 
     * @example
     *     await SessionStore.initializeSession();
     *     // Session is now set (either from storage or API)
     */
    initializeSession: async function() {
        // Check if session already stored
        const existingId = this.getCurrentSessionId();
        if (existingId) {
            return existingId;
        }
        
        // Fetch most recent session from API
        try {
            const response = await fetch('/api/sessions/current');
            const result = await response.json();
            
            if (result.success && result.session) {
                const session = result.session;
                this.setCurrentSessionId(session.id, {
                    name: session.name,
                    campus: session.campus,
                    year: session.year
                });
                return session.id;
            }
            
            return null;
        } catch (error) {
            console.error('Error initializing session:', error);
            return null;
        }
    },

    /**
     * Add listener for session changes.
     * 
     * Registers a callback to be invoked when the session changes.
     * Used by components that need to reload data on session switch.
     * 
     * @param {Function} callback - Function to call when session changes
     * @param {number|null} callback.sessionId - New session ID (null if cleared)
     * @param {Object|null} callback.metadata - New session metadata
     * 
     * @example
     *     SessionStore.onSessionChange((sessionId, metadata) => {
     *         console.log(`Switched to session: ${metadata?.name}`);
     *         reloadApplicants(sessionId);
     *     });
     */
    onSessionChange: function(callback) {
        const handler = (event) => {
            callback(event.detail.sessionId, event.detail.metadata);
        };
        window.addEventListener('sessionChange', handler);
        
        // Store reference for removal
        if (!this._listeners) {
            this._listeners = new WeakMap();
        }
        this._listeners.set(callback, handler);
    },

    /**
     * Remove session change listener.
     * 
     * Unregisters a previously registered callback.
     * 
     * @param {Function} callback - The callback to remove
     * 
     * @example
     *     SessionStore.offSessionChange(myCallback);
     */
    offSessionChange: function(callback) {
        if (this._listeners && this._listeners.has(callback)) {
            const handler = this._listeners.get(callback);
            window.removeEventListener('sessionChange', handler);
            this._listeners.delete(callback);
        }
    },

    /**
     * Dispatch session change event.
     * 
     * Internal method to notify listeners of session changes.
     * Called by setCurrentSessionId and clearCurrentSession.
     * 
     * @private
     * @param {number|null} sessionId - The new session ID
     * @param {Object|null} metadata - The new session metadata
     */
    _dispatchChange: function(sessionId, metadata) {
        const event = new CustomEvent('sessionChange', {
            detail: { sessionId, metadata }
        });
        window.dispatchEvent(event);
    }
};

// Export for use in other modules
window.SessionStore = SessionStore;
