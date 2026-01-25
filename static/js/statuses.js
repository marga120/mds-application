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
        this.setupDragAndDrop();
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

    setupDragAndDrop() {
        const statusItems = document.querySelectorAll('.status-item');
        let draggedElement = null;
        
        statusItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                draggedElement = item;
                item.classList.add('opacity-50');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', item.innerHTML);
            });
            
            item.addEventListener('dragend', (e) => {
                item.classList.remove('opacity-50');
                // Remove all drag-over highlighting
                statusItems.forEach(i => i.classList.remove('border-blue-500', 'border-2'));
            });
            
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                if (draggedElement !== item) {
                    item.classList.add('border-blue-500', 'border-2');
                }
            });
            
            item.addEventListener('dragleave', (e) => {
                item.classList.remove('border-blue-500', 'border-2');
            });
            
            item.addEventListener('drop', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                item.classList.remove('border-blue-500', 'border-2');
                
                if (draggedElement !== item) {
                    const draggedId = parseInt(draggedElement.dataset.id);
                    const targetId = parseInt(item.dataset.id);
                    
                    await this.reorderStatuses(draggedId, targetId);
                }
            });
        });
    }
    
    async reorderStatuses(draggedId, targetId) {
        // Find the dragged and target statuses
        const draggedIndex = this.statuses.findIndex(s => s.id === draggedId);
        const targetIndex = this.statuses.findIndex(s => s.id === targetId);
        
        if (draggedIndex === -1 || targetIndex === -1) return;
        
        // Create new order array
        const newStatuses = [...this.statuses];
        const [draggedStatus] = newStatuses.splice(draggedIndex, 1);
        newStatuses.splice(targetIndex, 0, draggedStatus);
        
        // Update display_order for all affected statuses
        const updates = newStatuses.map((status, index) => ({
            id: status.id,
            display_order: index + 1
        }));
        
        try {
            // Send batch update to server
            const response = await fetch('/api/admin/statuses/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ statuses: updates })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Status order updated successfully');
                await this.loadStatuses();
            } else {
                this.showError(result.message || 'Failed to reorder statuses');
            }
        } catch (error) {
            this.showError('Error reordering statuses: ' + error.message);
        }
    }

    async moveStatus(id, direction) {
        const index = this.statuses.findIndex(s => s.id === id);
        if (index === -1) return;

        // Calculate target index
        let targetIndex;
        if (direction === 'up') {
            if (index === 0) return; // Already at top
            targetIndex = index - 1;
        } else {
            if (index === this.statuses.length - 1) return; // Already at bottom
            targetIndex = index + 1;
        }
        
        // Use the same reorder logic
        await this.reorderStatuses(this.statuses[index].id, this.statuses[targetIndex].id);
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
