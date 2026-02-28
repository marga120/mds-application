/**
 * Status Configuration Page Controller
 * Uses StatusService for all API calls. No direct fetch().
 */

import { statusService } from "../services/status-service.js";
import { Notification } from "../components/notification.js";

class StatusManager {
  constructor() {
    this.statuses = [];
    this.editingId = null;
    this.init();
  }

  async init() {
    await this.loadStatuses();
    this.setupEventListeners();
  }

  async loadStatuses() {
    try {
      this.statuses = await statusService.getAllStatuses();
      this.renderStatuses();
    } catch (error) {
      Notification.error("Error loading statuses: " + error.message);
    }
  }

  setupEventListeners() {
    document
      .getElementById("addStatusBtn")
      .addEventListener("click", () => this.showAddForm());
    document
      .getElementById("saveStatusBtn")
      .addEventListener("click", () => this.saveStatus());
    document
      .getElementById("cancelStatusBtn")
      .addEventListener("click", () => this.hideForm());
  }

  renderStatuses() {
    const container = document.getElementById("statusesList");

    if (this.statuses.length === 0) {
      container.innerHTML =
        '<div class="text-center text-gray-500 py-8">No statuses found</div>';
      return;
    }

    const html = this.statuses
      .map((status) => {
        const colorClass = this._getColorClass(status.badge_color);
        const isDefault = status.is_default
          ? '<span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Default</span>'
          : "";
        const activeIcon = status.is_active
          ? '<span class="text-green-500">●</span>'
          : '<span class="text-gray-400">○</span>';

        return `
                <div class="status-item flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-sm transition-shadow cursor-move"
                     data-id="${status.id}"
                     data-order="${status.display_order}"
                     draggable="true">
                    <div class="flex items-center gap-4 flex-1">
                        <div class="flex flex-col items-center gap-1 drag-handle">
                            <svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M7 2a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2V4a2 2 0 00-2-2H7zm3 14a1 1 0 100-2 1 1 0 000 2zm0-4a1 1 0 100-2 1 1 0 000 2zm0-4a1 1 0 100-2 1 1 0 000 2z"/>
                            </svg>
                        </div>
                        <span class="text-lg">${activeIcon}</span>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass}">
                            ${status.status_name}
                        </span>
                        ${isDefault}
                    </div>
                    <div class="flex gap-2">
                        <button onclick="window._statusManager.editStatus(${status.id})" class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded">
                            Edit
                        </button>
                        <button onclick="window._statusManager.deleteStatus(${status.id})" class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded ${status.is_default ? "invisible" : ""}">
                            Delete
                        </button>
                    </div>
                </div>
            `;
      })
      .join("");

    container.innerHTML = html;
    this._setupDragAndDrop();
  }

  showAddForm() {
    this.editingId = null;
    document.getElementById("formTitle").textContent = "Add New Status";
    document.getElementById("statusName").value = "";
    document.getElementById("badgeColor").value = "gray";
    document.getElementById("isActive").checked = true;
    document.getElementById("statusForm").classList.remove("hidden");
  }

  hideForm() {
    document.getElementById("statusForm").classList.add("hidden");
    this.editingId = null;
  }

  editStatus(id) {
    const status = this.statuses.find((s) => s.id === id);
    if (!status) return;

    this.editingId = id;
    document.getElementById("formTitle").textContent = "Edit Status";
    document.getElementById("statusName").value = status.status_name;
    document.getElementById("badgeColor").value = status.badge_color;
    document.getElementById("isActive").checked = status.is_active;
    document.getElementById("statusForm").classList.remove("hidden");
  }

  async saveStatus() {
    const statusName = document.getElementById("statusName").value.trim();
    const badgeColor = document.getElementById("badgeColor").value;
    const isActive = document.getElementById("isActive").checked;

    if (!statusName) {
      Notification.error("Status name is required");
      return;
    }

    try {
      if (this.editingId) {
        await statusService.updateStatus(this.editingId, {
          status_name: statusName,
          badge_color: badgeColor,
          is_active: isActive,
        });
      } else {
        await statusService.createStatus({
          status_name: statusName,
          badge_color: badgeColor,
          is_active: isActive,
        });
      }
      Notification.success("Status saved successfully");
      this.hideForm();
      await this.loadStatuses();
    } catch (error) {
      Notification.error("Error saving status: " + error.message);
    }
  }

  async deleteStatus(id) {
    const status = this.statuses.find((s) => s.id === id);
    if (!status) return;

    if (
      !confirm(
        `Delete "${status.status_name}"?\n\nAll applicants with this status will be moved to the default status.`,
      )
    ) {
      return;
    }

    try {
      await statusService.deleteStatus(id);
      Notification.success("Status deleted successfully");
      await this.loadStatuses();
    } catch (error) {
      Notification.error("Error deleting status: " + error.message);
    }
  }

  _setupDragAndDrop() {
    const statusItems = document.querySelectorAll(".status-item");
    let draggedElement = null;

    statusItems.forEach((item) => {
      item.addEventListener("dragstart", (e) => {
        draggedElement = item;
        item.classList.add("opacity-50");
        e.dataTransfer.effectAllowed = "move";
      });

      item.addEventListener("dragend", () => {
        item.classList.remove("opacity-50");
        statusItems.forEach((i) =>
          i.classList.remove("border-blue-500", "border-2"),
        );
      });

      item.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        if (draggedElement !== item)
          item.classList.add("border-blue-500", "border-2");
      });

      item.addEventListener("dragleave", () => {
        item.classList.remove("border-blue-500", "border-2");
      });

      item.addEventListener("drop", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        item.classList.remove("border-blue-500", "border-2");

        if (draggedElement !== item) {
          await this._reorderStatuses(
            parseInt(draggedElement.dataset.id),
            parseInt(item.dataset.id),
          );
        }
      });
    });
  }

  async _reorderStatuses(draggedId, targetId) {
    const draggedIndex = this.statuses.findIndex((s) => s.id === draggedId);
    const targetIndex = this.statuses.findIndex((s) => s.id === targetId);
    if (draggedIndex === -1 || targetIndex === -1) return;

    const newStatuses = [...this.statuses];
    const [dragged] = newStatuses.splice(draggedIndex, 1);
    newStatuses.splice(targetIndex, 0, dragged);

    const updates = newStatuses.map((s, i) => ({
      id: s.id,
      display_order: i + 1,
    }));

    try {
      await statusService.reorderStatuses(updates);
      Notification.success("Status order updated");
      await this.loadStatuses();
    } catch (error) {
      Notification.error("Error reordering: " + error.message);
    }
  }

  _getColorClass(color) {
    const map = {
      gray: "bg-gray-100 text-gray-800",
      red: "bg-red-100 text-red-800",
      yellow: "bg-yellow-100 text-yellow-800",
      green: "bg-green-100 text-green-800",
      blue: "bg-blue-100 text-blue-800",
      indigo: "bg-indigo-100 text-indigo-800",
      purple: "bg-purple-100 text-purple-800",
      pink: "bg-pink-100 text-pink-800",
      orange: "bg-orange-100 text-orange-800",
      teal: "bg-teal-100 text-teal-800",
    };
    return map[color] || map["gray"];
  }
}

// Expose for inline onclick handlers in rendered HTML
window._statusManager = new StatusManager();
