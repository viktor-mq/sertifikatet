/**
 * Admin Base JavaScript
 * Common functions and utilities used across all admin sections
 */

// Common admin utilities and helper functions
const AdminUtils = {
    
    /**
     * Toast Notification System
     * Professional notification system used across all admin sections
     */
    showToast: function(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        
        const icons = { 
            success: '✅', 
            error: '❌', 
            warning: '⚠️', 
            info: 'ℹ️' 
        };
        
        const colors = { 
            success: '#d4edda', 
            error: '#f8d7da', 
            warning: '#fff3cd', 
            info: '#d1ecf1' 
        };
        
        const borderColors = {
            success: '#c3e6cb',
            error: '#f5c6cb',
            warning: '#ffeaa7',
            info: '#bee5eb'
        };
        
        toast.innerHTML = `
            <div style="background: ${colors[type]}; border: 1px solid ${borderColors[type]}; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 10px; position: relative; overflow: hidden;">
                <span style="font-size: 18px;">${icons[type]}</span>
                <span style="flex: 1; color: #333;">${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 18px; cursor: pointer; padding: 0; color: #666; margin-left: 10px;">×</button>
                <div style="position: absolute; bottom: 0; left: 0; height: 3px; background: ${borderColors[type]}; animation: toast-progress ${duration}ms linear forwards;"></div>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    },

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
        return container;
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml: function(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Generic AJAX helper function
     */
    makeAjaxRequest: function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };

        return fetch(url, mergedOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                this.showToast('Network error: ' + error.message, 'error');
                throw error;
            });
    },

    /**
     * Set loading state for any element
     */
    setLoadingState: function(element, isLoading, loadingText = 'Loading...') {
        if (isLoading) {
            element.style.opacity = '0.6';
            element.style.pointerEvents = 'none';
            
            // Add loading overlay if it doesn't exist
            if (!element.querySelector('.loading-overlay')) {
                const overlay = document.createElement('div');
                overlay.className = 'loading-overlay';
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10;
                `;
                overlay.innerHTML = `
                    <div style="text-align: center;">
                        <div style="width: 30px; height: 30px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
                        <div style="color: #666;">${loadingText}</div>
                    </div>
                `;
                element.style.position = 'relative';
                element.appendChild(overlay);
            }
        } else {
            element.style.opacity = '1';
            element.style.pointerEvents = '';
            
            // Remove loading overlay
            const overlay = element.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    },

    /**
     * Generate smart page numbers with ellipsis for pagination
     */
    generatePageNumbers: function(currentPage, totalPages, maxButtons = 5) {
        const pages = [];
        
        if (totalPages <= maxButtons) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            
            if (currentPage > 3) {
                pages.push('...');
            }
            
            const start = Math.max(2, currentPage - 1);
            const end = Math.min(totalPages - 1, currentPage + 1);
            
            for (let i = start; i <= end; i++) {
                if (!pages.includes(i)) {
                    pages.push(i);
                }
            }
            
            if (currentPage < totalPages - 2) {
                pages.push('...');
            }
            
            if (!pages.includes(totalPages)) {
                pages.push(totalPages);
            }
        }
        
        return pages;
    },

    /**
     * Initialize sortable table headers
     */
    initializeSorting: function(sortableSelector, onSortCallback) {
        const sortableHeaders = document.querySelectorAll(sortableSelector);
        
        sortableHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-column');
                if (onSortCallback) {
                    onSortCallback(column);
                }
            });

            // Add keyboard support
            header.setAttribute('tabindex', '0');
            header.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const column = this.getAttribute('data-column');
                    if (onSortCallback) {
                        onSortCallback(column);
                    }
                }
            });
        });
    },

    /**
     * Update sort indicators for table headers
     */
    updateSortIndicators: function(currentSortBy, currentSortOrder, sortableSelector = '.sortable') {
        document.querySelectorAll(sortableSelector).forEach(header => {
            const indicator = header.querySelector('.sort-indicator');
            const column = header.getAttribute('data-column');
            
            if (column === currentSortBy) {
                header.style.backgroundColor = '#e3f2fd';
                header.style.fontWeight = 'bold';
                if (indicator) {
                    indicator.innerHTML = currentSortOrder === 'asc' ? 
                        '<span style="color: green;">↑</span>' : 
                        '<span style="color: red;">↓</span>';
                }
            } else {
                header.style.backgroundColor = '';
                header.style.fontWeight = '';
                if (indicator) {
                    indicator.innerHTML = '<span style="color: #ccc;">↕</span>';
                }
            }
        });
    },

    /**
     * Debounce function for search inputs
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Set current year in footer (common across admin pages)
     */
    setCurrentYear: function() {
        const yearSpan = document.getElementById('currentYear');
        if (yearSpan) {
            yearSpan.textContent = new Date().getFullYear();
        }
    }
};

// Initialize common admin functionality
document.addEventListener('DOMContentLoaded', function() {
    // Set current year in footer
    AdminUtils.setCurrentYear();
    
    // Add toast progress animation CSS if not exists
    if (!document.querySelector('#toast-progress-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-progress-styles';
        style.textContent = `
            @keyframes toast-progress {
                0% { width: 100%; }
                100% { width: 0%; }
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
});

// Export for use in other admin scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminUtils;
}
