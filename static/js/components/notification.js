/**
 * components/notification.js
 * Self-contained toast notification system.
 * Replaces ALL showMessage() implementations across the codebase.
 * No dependencies — works anywhere.
 *
 * Usage:
 *   import { Notification } from '../components/notification.js';
 *   Notification.success('User created successfully.');
 *   Notification.error('Something went wrong.');
 */

const STYLES = {
  success: {
    container: "bg-green-50 border-green-400 text-green-800",
    icon: "✓",
    iconClass: "text-green-500",
  },
  error: {
    container: "bg-red-50 border-red-400 text-red-800",
    icon: "✕",
    iconClass: "text-red-500",
  },
  warning: {
    container: "bg-yellow-50 border-yellow-400 text-yellow-800",
    icon: "⚠",
    iconClass: "text-yellow-500",
  },
  info: {
    container: "bg-blue-50 border-blue-400 text-blue-800",
    icon: "ℹ",
    iconClass: "text-blue-500",
  },
};

export class Notification {
  /**
   * Show a toast notification.
   * @param {string} message
   * @param {'success'|'error'|'warning'|'info'} type
   * @param {number} duration - milliseconds before auto-dismiss
   */
  static show(message, type = "info", duration = 4000) {
    const el = Notification._createToastDOM(message, type);
    document.body.appendChild(el);

    // Animate in
    requestAnimationFrame(() => {
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    });

    const timer = setTimeout(() => Notification._removeToast(el), duration);

    // Close button dismisses immediately
    el.querySelector("[data-close]").addEventListener("click", () => {
      clearTimeout(timer);
      Notification._removeToast(el);
    });
  }

  /** @param {string} message @param {number} [duration] */
  static success(message, duration = 4000) {
    Notification.show(message, "success", duration);
  }

  /** @param {string} message @param {number} [duration] */
  static error(message, duration = 5000) {
    Notification.show(message, "error", duration);
  }

  /** @param {string} message @param {number} [duration] */
  static warning(message, duration = 4000) {
    Notification.show(message, "warning", duration);
  }

  /** @param {string} message @param {number} [duration] */
  static info(message, duration = 4000) {
    Notification.show(message, "info", duration);
  }

  /**
   * @param {string} message
   * @param {string} type
   * @returns {HTMLElement}
   */
  static _createToastDOM(message, type) {
    const style = STYLES[type] || STYLES.info;

    const el = document.createElement("div");
    el.className = [
      "fixed bottom-4 right-4 z-50",
      "flex items-start gap-3",
      "max-w-sm w-full",
      "px-4 py-3",
      "rounded-lg border shadow-lg",
      "transition-all duration-300",
      style.container,
    ].join(" ");

    // Start hidden for animation
    el.style.opacity = "0";
    el.style.transform = "translateY(8px)";

    el.innerHTML = `
      <span class="text-lg leading-none ${style.iconClass}" aria-hidden="true">${style.icon}</span>
      <p class="flex-1 text-sm font-medium">${Notification._escapeHtml(message)}</p>
      <button data-close class="ml-1 text-current opacity-50 hover:opacity-100 leading-none text-lg" aria-label="Dismiss">&times;</button>
    `;

    return el;
  }

  /** @param {HTMLElement} el */
  static _removeToast(el) {
    el.style.opacity = "0";
    el.style.transform = "translateY(8px)";
    setTimeout(() => el.remove(), 300);
  }

  /** @param {string} str */
  static _escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
