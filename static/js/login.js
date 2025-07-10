// Login functionality with Htmx
import 'htmx.org'

document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page with Htmx loaded');
    
    // Check for existing session
    checkExistingSession();
    
    // Handle login form responses
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (evt.detail.pathInfo.requestPath === '/api/auth/login') {
            const xhr = evt.detail.xhr;
            
            try {
                const response = JSON.parse(xhr.response);
                
                if (response.success) {
                    showMessage('Login successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = response.redirect || '/';
                    }, 1000);
                } else {
                    showMessage(response.message || 'Login failed', 'error');
                }
            } catch (e) {
                showMessage('Login error occurred', 'error');
            }
        }
    });

    // Handle network errors
    document.body.addEventListener('htmx:responseError', function(evt) {
        showMessage('Network error. Please try again.', 'error');
    });
});

async function checkExistingSession() {
    try {
        const response = await fetch('/api/auth/check-session');
        const result = await response.json();

        if (result.authenticated) {
            // User is already logged in, redirect to dashboard
            window.location.href = '/';
        }
    } catch (error) {
        console.log('No existing session');
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `p-4 rounded-md ${
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