/**
 * utils/constants.js
 * Shared application constants. Import instead of hardcoding values.
 */

export const ROLES = {
  ADMIN: 1,
  FACULTY: 2,
  VIEWER: 3,
};

export const ROLE_NAMES = {
  1: "Admin",
  2: "Faculty",
  3: "Viewer",
};

export const API_PATHS = {
  AUTH: "/api/auth",
  APPLICANTS: "/api",
  SESSIONS: "/api/sessions",
  STATUSES: "/api/statuses",
  RATINGS: "/api/ratings",
  DOCUMENTS: "/api/documents",
  LOGS: "/api/logs",
  DATABASE: "/api/database",
  ADMIN_STATUSES: "/api/admin/statuses",
};

// Status names considered "submitted" (offer made)
export const STATUS_SUBMITTED = ["Offer", "Offer Accepted"];

// Status names considered "unsubmitted" / not progressed
export const STATUS_UNSUBMITTED = ["Not Reviewed", "Declined", "Waitlisted"];
