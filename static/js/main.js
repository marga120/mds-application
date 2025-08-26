/**
 * MAIN APPLICATION ENTRY POINT
 * 
 * This file initializes the core application components when the page loads.
 * It coordinates the startup of ApplicantsManager, AuthManager, and SessionsManager
 * to ensure proper initialization order and component communication.
 */

// Initialize the app when the page loads
document.addEventListener("DOMContentLoaded", function () {
  window.applicantsManager = new ApplicantsManager();
  new AuthManager();
  new SessionsManager();
});
