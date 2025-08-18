// Initialize the app when the page loads
document.addEventListener("DOMContentLoaded", function () {
  window.applicantsManager = new ApplicantsManager();
  new AuthManager();
  new SessionsManager();
});
