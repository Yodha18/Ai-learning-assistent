// Main JavaScript file for AI Learning Assistant

// Toast notification system
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = getToastIcon(type);
    
    toast.innerHTML = `
        <span class="material-symbols-outlined">${icon}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check_circle',
        error: 'error',
        info: 'info',
        warning: 'warning'
    };
    return icons[type] || icons.info;
}

// API helper functions
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        const contentType = response.headers.get('content-type') || '';
        const payload = contentType.includes('application/json')
            ? await response.json()
            : { detail: await response.text() };
        
        if (!response.ok) {
            throw new Error(payload.detail || 'Request failed');
        }
        
        return payload;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

const nativeFetch = window.fetch.bind(window);
window.fetch = (input, options = {}) => {
    const url = typeof input === 'string' ? input : input.url;
    const token = localStorage.getItem('access_token');
    if (token && url.startsWith('/api/')) {
        const headers = new Headers(options.headers || {});
        headers.set('Authorization', `Bearer ${token}`);
        return nativeFetch(input, { ...options, headers });
    }
    return nativeFetch(input, options);
};

function setupAuthForm(formId, endpoint, redirectPath) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(form).entries());
        if (formId === 'register-form' && payload.password !== payload.confirm_password) {
            showToast('Passwords do not match', 'error');
            return;
        }
        delete payload.confirm_password;
        if (!payload.semester) delete payload.semester;
        if (payload.semester) payload.semester = Number(payload.semester);
        if (payload.daily_study_time) payload.daily_study_time = Number(payload.daily_study_time);

        try {
            const response = await apiRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            if (response.access_token) {
                localStorage.setItem('access_token', response.access_token);
                localStorage.setItem('user_id', response.user_id);
            }
            window.location.href = redirectPath;
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

// Format helpers
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
}

// Local storage helpers
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

function getFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Error removing from localStorage:', error);
    }
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 digit
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return re.test(password);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard', 'success');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showToast('Failed to copy', 'error');
    }
}

// Generate random ID
function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Add global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
    });
    
    // Add unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
    });
    
    // Initialize tooltips if using a library
    // This is a placeholder for tooltip initialization
});

setupAuthForm('register-form', '/api/auth/register', '/login');
setupAuthForm('login-form', '/api/auth/login', '/dashboard');

// Export functions for use in other files
window.AIAssistant = {
    showToast,
    apiRequest,
    formatDate,
    formatTime,
    formatDuration,
    saveToLocalStorage,
    getFromLocalStorage,
    removeFromLocalStorage,
    validateEmail,
    validatePassword,
    debounce,
    throttle,
    copyToClipboard,
    generateId,
    getAuthHeaders
};
