/**
 * utils/formatters.js
 * Pure formatting functions. No DOM, no API calls.
 * Import and use anywhere.
 */

/**
 * Returns a human-readable relative time string.
 * @param {string|Date} dateString
 * @returns {string} e.g. "just now", "5 minutes ago", "3 days ago", "Jan 15"
 */
export function getTimeAgo(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? "s" : ""} ago`;
  if (diffHr < 24) return `${diffHr} hour${diffHr !== 1 ? "s" : ""} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay !== 1 ? "s" : ""} ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/**
 * Formats a date as "Jan 15, 2025".
 * @param {string|Date} dateString
 * @returns {string}
 */
export function formatDate(dateString) {
  if (!dateString) return "";
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Formats a date as "Jan 15, 2025 3:42 PM".
 * @param {string|Date} dateString
 * @returns {string}
 */
export function formatDateTime(dateString) {
  if (!dateString) return "";
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * Returns the display name for a role ID.
 * @param {number} roleId
 * @returns {string}
 */
export function getRoleName(roleId) {
  const names = { 1: "Admin", 2: "Faculty", 3: "Viewer", 4: "Super Admin" };
  return names[roleId] ?? "Unknown";
}

/**
 * Returns Tailwind badge classes for a role ID.
 * @param {number} roleId
 * @returns {string}
 */
export function getRoleBadgeClass(roleId) {
  const classes = {
    1: "bg-red-100 text-red-800",
    2: "bg-blue-100 text-blue-800",
    3: "bg-gray-100 text-gray-800",
    4: "bg-purple-100 text-purple-800",
  };
  return classes[roleId] ?? "bg-gray-100 text-gray-800";
}

/**
 * Truncates a string to maxLen characters, appending ellipsis if needed.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
export function truncate(str, maxLen = 50) {
  if (!str) return "";
  return str.length <= maxLen ? str : str.slice(0, maxLen) + "...";
}
