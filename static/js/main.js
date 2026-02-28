/**
 * MAIN APPLICATION ENTRY POINT
 *
 * Initializes auth and session UI on pages where auth.js is loaded.
 * ApplicantsManager is initialized in pages/index.js (ES module).
 */

document.addEventListener("DOMContentLoaded", function () {
  new AuthManager();
});
