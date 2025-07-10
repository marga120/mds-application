// Main JavaScript for MDS Application with Htmx
import 'htmx.org'

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('MDS Application with Htmx loaded');
    
    // Set up global Htmx error handling
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('Htmx request failed:', evt.detail);
        showMessage('Request failed. Please try again.', 'error');
    });

    // Handle successful responses
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const xhr = evt.detail.xhr;
        
        // Handle JSON responses (like from login/logout)
        if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
            try {
                const response = JSON.parse(xhr.response);
                if (response.message) {
                    showMessage(response.message, response.success ? 'success' : 'error');
                }
            } catch (e) {
                // Not JSON, ignore
            }
        }
    });

    // Handle file upload responses
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.detail.pathInfo.requestPath === '/api/upload') {
            const xhr = evt.detail.xhr;
            try {
                const response = JSON.parse(xhr.response);
                if (response.success) {
                    showMessage(`${response.records_processed} records uploaded successfully`, 'success');
                } else {
                    showMessage(response.message || 'Upload failed', 'error');
                }
            } catch (e) {
                showMessage('Upload response error', 'error');
            }
        }
    });

    // Set up search functionality
    setupSearch();
});

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchFilter = document.querySelector('select[name="filter"]');
    
    if (searchInput && searchFilter) {
        // Add search parameter handling
        document.body.addEventListener('htmx:configRequest', function(evt) {
            if (evt.detail.path === '/fragments/students') {
                const search = searchInput.value.trim();
                const filter = searchFilter.value;
                
                if (search) {
                    evt.detail.parameters['search'] = search;
                    evt.detail.parameters['filter'] = filter;
                }
            }
        });
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `mt-4 p-4 rounded-md ${
            type === 'success' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-red-100 text-red-700'
        }`;
        messageDiv.classList.remove('hidden');

        // Hide message after 5 seconds
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }
}

// Auto-refresh functionality for students list
function startAutoRefresh() {
    setInterval(() => {
        htmx.trigger('#studentsContainer', 'refresh-students');
    }, 30000); // Refresh every 30 seconds
}

// Export functions for global use
window.MDS = {
    showMessage,
    startAutoRefresh
};