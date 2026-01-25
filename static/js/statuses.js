/**
 * Status Configuration Management
 * 
 * Admin interface for managing review status options. Allows create, update, delete, 
 * and reorder of application review statuses. Changes are reflected in all dropdowns 
 * across the application.
 */

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
            const response = await fetch('/api/admin/statuses');
            const result = await response.json();
            
            if (result.success) {
                this.statuses = result.statuses;
                this.renderStatuses();
            } else {
                this.showError('Failed to load statuses: ' + result.message);
            }
        } catch (error) {
            this.showError('Error loading statuses: ' + error.message);
        }
    }

    setupEventListeners() {
        document.getElementById('addStatusBtn').addEventListener('click', () => this.showAddForm());
        document.getElementById('saveStatusBtn').addEventListener('click', () => this.saveStatus());
        document.getElementById('cancelStatusBtn').addEventListener('click', () => this.hideForm());
    }

    renderStatuses() {
        const container = document.getElementById('statusesList');
        
        if (this.statuses.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 py-8">No statuses found</div>';
            return;
        }

        const html = this.statuses.map((status, index) => {
            const colorClass = this.getColorClass(status.badge_color);
            const isDefault = status.is_default ? '<span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Default</span>' : '';
            const activeIcon = status.is_active 
                ? '<span class="text-green-500">●</span>' 
                : '<span class="text-gray-400">○</span>';
            
            return `
                <div class="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-sm transition-shadow" data-id="${status.id}">
                    <div class="flex items-center gap-4 flex-1">
                        <div class="flex flex-col items-center gap-1">
                            <button class="text-gray-400 hover:text-gray-600 ${index === 0 ? 'invisible' : ''}" onclick="statusManager.moveStatus(${status.id}, 'up')">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"/></svg>
                            </button>
                            <button class="text-gray-400 hover:text-gray-600 ${index === this.statuses.length - 1 ? 'invisible' : ''}" onclick="statusManager.moveStatus(${status.id}, 'down')">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"/></svg>
                            </button>
                        </div>
                        <span class="text-lg">${activeIcon}</span>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass}">
                            ${status.status_name}
                        </span>
                        ${isDefault}
                    </div>
                    <div class="flex gap-2">
                        <button onclick="statusManager.editStatus(${status.id})" class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded">
                            Edit
                        </button>
                        <button onclick="statusManager.deleteStatus(${status.id})" class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded ${status.is_default ? 'invisible' : ''}">
                            Delete
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    showAddForm() {
        this.editingId = null;
        document.getElementById('formTitle').textContent = 'Add New Status';
        document.getElementById('statusName').value = '';
        document.getElementById('badgeColor').value = 'gray';
        document.getElementById('isActive').checked = true;
        document.getElementById('statusForm').classList.remove('hidden');
    }

    hideForm() {
        document.getElementById('statusForm').classList.add('hidden');
        this.editingId = null;
    }

    editStatus(id) {
        const status = this.statuses.find(s => s.id === id);
        if (!status) return;

        this.editingId = id;
        document.getElementById('formTitle').textContent = 'Edit Status';
        document.getElementById('statusName').value = status.status_name;
        document.getElementById('badgeColor').value = status.badge_color;
        document.getElementById('isActive').checked = status.is_active;
        document.getElementById('statusForm').classList.remove('hidden');
    }

    async saveStatus() {
        const statusName = document.getElementById('statusName').value.trim();
        const badgeColor = document.getElementById('badgeColor').value;
        const isActive = document.getElementById('isActive').checked;

        if (!statusName) {
            this.showError('Status name is required');
            return;
        }

        const url = this.editingId ? `/api/admin/statuses/${this.editingId}` : '/api/admin/statuses';
        const method = this.editingId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status_name: statusName,
                    badge_color: badgeColor,
                    is_active: isActive
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.hideForm();
                await this.loadStatuses();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Error saving status: ' + error.message);
        }
    }

    async deleteStatus(id) {
        const status = this.statuses.find(s => s.id === id);
        if (!status) return;

        if (!confirm(`Delete "${status.status_name}"?\n\nAll applicants with this status will be moved to the default status.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/statuses/${id}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                await this.loadStatuses();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Error deleting status: ' + error.message);
        }
    }

    async moveStatus(id, direction) {
        const index = this.statuses.findIndex(s => s.id === id);
        if (index === -1) return;

        const newOrder = direction === 'up' ? index : index + 2;
        
        try {
            const response = await fetch(`/api/admin/statuses/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ display_order: newOrder })
            });

            const result = await response.json();

            if (result.success) {
                await this.loadStatuses();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Error reordering status: ' + error.message);
        }
    }

    getColorClass(color) {
        const colorMap = {
            'gray': 'bg-gray-100 text-gray-800',
            'red': 'bg-red-100 text-red-800',
            'yellow': 'bg-yellow-100 text-yellow-800',
            'green': 'bg-green-100 text-green-800',
            'blue': 'bg-blue-100 text-blue-800',
            'indigo': 'bg-indigo-100 text-indigo-800',
            'purple': 'bg-purple-100 text-purple-800',
            'pink': 'bg-pink-100 text-pink-800',
            'orange': 'bg-orange-100 text-orange-800',
            'teal': 'bg-teal-100 text-teal-800'
        };
        return colorMap[color] || colorMap['gray'];
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        const notificationMessage = document.getElementById('notificationMessage');
        
        notificationMessage.textContent = message;
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg ${
            type === 'error' ? 'bg-red-500' : 'bg-green-500'
        } text-white`;
        notification.classList.remove('hidden');

        setTimeout(() => {
            notification.classList.add('hidden');
        }, 3000);
    }
}

let statusManager;
document.addEventListener('DOMContentLoaded', () => {
    statusManager = new StatusManager();
});
