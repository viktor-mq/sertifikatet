
// ============================================================================
// ENHANCED ACTIVITY TABLE FUNCTIONALITY
// ============================================================================

// CSRF token utility
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

(function() {
    'use strict';
    function initializeActivitySection() {
        
        // Set up real-time search for activity table
        const searchInput = document.getElementById('activityRealTimeSearch');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(activitySearchDebounceTimer);
                activitySearchDebounceTimer = setTimeout(() => {
                    activityCurrentPage = 1;
                    applyActivityFilters();
                }, 300);
            });
        }

        // Set up filter dropdowns for activity
        const actionFilter = document.getElementById('activityActionFilter');
        const timeFilter = document.getElementById('activityTimeFilter');
        
        if (actionFilter) {
            actionFilter.addEventListener('change', () => {
                activityCurrentPage = 1;
                applyActivityFilters();
            });
        }
        
        if (timeFilter) {
            timeFilter.addEventListener('change', () => {
                activityCurrentPage = 1;
                applyActivityFilters();
            });
        }

        // Set up column visibility checkboxes for activity
        const columnCheckboxes = document.querySelectorAll('.activity-column-checkbox');
        columnCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleActivityColumnVisibility(this.dataset.column, this.checked);
            });
        });

        // Initialize activity table if it exists
        if (document.getElementById('activity-table')) {
            loadActivityData();
        } else {
        }
    }

    function applyActivityFilters() {
        const searchValue = document.getElementById('activityRealTimeSearch')?.value || '';
        const action = document.getElementById('activityActionFilter')?.value || '';
        const timeRange = document.getElementById('activityTimeFilter')?.value || '';
        const searchColumn = document.getElementById('activityAdvancedSearchColumn')?.value || 'all';

        activityCurrentFilters = {
            search: searchValue,
            action: action,
            time_range: timeRange,
            search_column: searchColumn
        };

        showActivityLoading(true);
        loadActivityData();
    }

    function loadActivityData() {
        
        showActivityLoading(true);
        
        // Prepare API parameters
        const params = {
            page: activityCurrentPage,
            per_page: activityPerPage,
            sort_by: activityCurrentSort.field,
            sort_order: activityCurrentSort.order,
            ...activityCurrentFilters
        };
        
        // Build query string
        const queryString = new URLSearchParams(params).toString();
        
        fetch(`/admin/api/activity-logs?${queryString}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            
            // Update the activity table
            updateActivityTable(data.logs);
            
            // Update pagination
            updateActivityPagination(data.pagination.page, data.pagination.pages);
            
            // Update info
            updateActivityInfo(data.pagination.total, data.pagination.page, data.pagination.per_page);
            
            // Update sort indicators
            updateActivitySortIndicators();
            
        })
        .catch(error => {
            console.error('Error loading activity data:', error);
            
            // Show error message in table
            const tbody = document.querySelector('#activity-table tbody');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; color: #ef4444; font-style: italic;">
                            Error loading activity data: ${error.message}
                        </td>
                    </tr>
                `;
            }
        })
        .finally(() => {
            showActivityLoading(false);
        });
    }
    
    function updateActivityTable(logs) {
        
        const tbody = document.querySelector('#activity-table tbody');
        if (!tbody) {
            console.error('Activity table tbody not found!');
            return;
        }
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        if (logs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: #999; font-style: italic;">
                        No activity records found
                    </td>
                </tr>
            `;
            return;
        }
        
        // Add new rows
        logs.forEach(log => {
            const row = document.createElement('tr');
            
            // Format action badge
            let actionBadge = '';
            switch(log.action) {
                case 'grant_admin':
                    actionBadge = '<span class="btn btn-warning btn-small" style="cursor: default;">🛡️ Admin Granted</span>';
                    break;
                case 'revoke_admin':
                    actionBadge = '<span class="btn btn-danger btn-small" style="cursor: default;">❌ Admin Revoked</span>';
                    break;
                case 'admin_login_success':
                    actionBadge = '<span class="btn btn-success btn-small" style="cursor: default;">✅ Admin Login</span>';
                    break;
                case 'admin_login_failure':
                    actionBadge = '<span class="btn btn-danger btn-small" style="cursor: default;">❌ Login Failed</span>';
                    break;
                default:
                    actionBadge = `<span class="btn btn-secondary btn-small" style="cursor: default;">${log.action}</span>`;
            }
            
            row.innerHTML = `
                <td data-column="timestamp">${log.created_at}</td>
                <td data-column="action">${actionBadge}</td>
                <td data-column="target_user">${log.target_user.username}</td>
                <td data-column="admin_user">${log.admin_user.username}</td>
                <td data-column="ip_address"><code>${log.ip_address}</code></td>
            `;
            
            tbody.appendChild(row);
        });
    }

    function toggleActivitySort(field) {
        console.log(`Toggling activity sort for field: ${field}`);
        
        if (activityCurrentSort.field === field) {
            activityCurrentSort.order = activityCurrentSort.order === 'asc' ? 'desc' : 'asc';
        } else {
            activityCurrentSort.field = field;
            activityCurrentSort.order = 'asc';
        }
        
        activityCurrentPage = 1;
        loadActivityData();
    }

    function updateActivitySortIndicators() {
        // Clear all indicators
        document.querySelectorAll('#activity-table .sort-indicator').forEach(indicator => {
            indicator.textContent = '';
            indicator.className = 'sort-indicator';
        });
        
        // Set active indicator
        const activeIndicator = document.querySelector(`#activity-table [data-sortable="${activityCurrentSort.field}"] .sort-indicator`);
        if (activeIndicator) {
            activeIndicator.textContent = activityCurrentSort.order === 'asc' ? '↑' : '↓';
            activeIndicator.className = `sort-indicator ${activityCurrentSort.order}`;
        }
    }

    function changeActivityTableDensity() {
        const density = document.getElementById('activityTableDensity').value;
        const table = document.getElementById('activity-table');
        if (table) {
            table.className = table.className.replace(/density-\w+/g, '');
            table.classList.add(`density-${density}`);
        }
    }

    function toggleActivityColumnVisibilityDropdown() {
        const dropdown = document.getElementById('activityColumnVisibilityDropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }

    function toggleActivityColumnVisibility(column, visible) {
        const table = document.getElementById('activity-table');
        if (!table) return;
        
        const elements = table.querySelectorAll(`[data-column="${column}"]`);
        elements.forEach(el => {
            el.style.display = visible ? '' : 'none';
        });
    }

    function clearAllActivityFilters() {
        console.log('Clearing all activity filters');
        
        // Reset form fields
        document.getElementById('activityRealTimeSearch').value = '';
        document.getElementById('activityActionFilter').value = '';
        document.getElementById('activityTimeFilter').value = '';
        document.getElementById('activityAdvancedSearchColumn').value = 'all';
        
        // Reset filter state
        activityCurrentFilters = {};
        activityCurrentPage = 1;
        
        // Reload data from API
        loadActivityData();
    }

    function changeActivityPerPage() {
        activityPerPage = parseInt(document.getElementById('activityPerPageSelector').value);
        activityCurrentPage = 1;
        loadActivityData();
    }

    function updateActivityInfo(total, page, perPage) {
        const info = document.getElementById('activityPaginationInfo');
        if (info) {
            const start = (page - 1) * perPage + 1;
            const end = Math.min(page * perPage, total);
            info.textContent = `Showing ${start}-${end} of ${total} activity records`;
        }
    }

    function updateActivityPagination(currentPage, totalPages) {
        const container = document.getElementById('activityPaginationButtons');
        if (!container) return;
        
        let buttonsHtml = '';
        
        // Previous button
        if (currentPage > 1) {
            buttonsHtml += `<button onclick="goToActivityPage(${currentPage - 1})" class="btn btn-secondary">Previous</button>`;
        }
        
        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage;
            buttonsHtml += `<button onclick="goToActivityPage(${i})" class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}">${i}</button>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            buttonsHtml += `<button onclick="goToActivityPage(${currentPage + 1})" class="btn btn-secondary">Next</button>`;
        }
        
        container.innerHTML = buttonsHtml;
    }

    function goToActivityPage(page) {
        activityCurrentPage = page;
        loadActivityData();
    }

    function showActivityLoading(loading) {
        const indicator = document.getElementById('activityFilterLoadingIndicator');
        if (indicator) {
            indicator.style.display = loading ? 'flex' : 'none';
        }
        
        const table = document.getElementById('activity-table');
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }

    // ============================================================================
    // LIVE TABLE UPDATE FUNCTIONS
    // ============================================================================

    function updateUserRowAdminStatus(userId, isAdmin, username) {
        console.log(`Updating user row for ${username} (ID: ${userId}) - Admin: ${isAdmin}`);
        
        // Find the user row
        const table = document.getElementById('users-table-enhanced');
        if (!table) {
            console.error('Users table not found!');
            return;
        }
        
        const rows = table.querySelectorAll('tbody tr');
        let targetRow = null;
        
        rows.forEach(row => {
            const idCell = row.querySelector('[data-column="id"]');
            if (idCell && parseInt(idCell.textContent) === userId) {
                targetRow = row;
            }
        });
        
        if (!targetRow) {
            console.error(`User row with ID ${userId} not found!`);
            return;
        }
        
        // Update the admin status column
        const adminCell = targetRow.querySelector('[data-column="admin"]');
        if (adminCell) {
            if (isAdmin) {
                adminCell.innerHTML = '<span class="btn btn-danger btn-small" style="cursor: default;">🛡️ Admin</span>';
                targetRow.classList.add('table-warning'); // Add admin highlighting
            } else {
                adminCell.innerHTML = '<span class="btn btn-secondary btn-small" style="cursor: default;">User</span>';
                targetRow.classList.remove('table-warning'); // Remove admin highlighting
            }
        }
        
        // Update the actions column
        const actionsCell = targetRow.querySelector('[data-column="actions"]');
        if (actionsCell) {
            // Keep the View button
            const viewButton = `<button onclick="openUserModal(${userId})" class="btn btn-info btn-small" style="margin-right: 5px;">
                👁️ View
              </button>`;
            
            // Update the admin action button
            let adminActionButton;
            if (isAdmin) {
                adminActionButton = `<button onclick="revokeAdminAjax(${userId}, '${username}')" class="btn btn-danger btn-small">
                  👤❌ Revoke Admin
                </button>`;
            } else {
                adminActionButton = `<button onclick="grantAdminAjax(${userId}, '${username}')" class="btn btn-warning btn-small">
                  🛡️ Grant Admin
                </button>`;
            }
            
            actionsCell.innerHTML = viewButton + adminActionButton;
        }
        
        console.log(`Successfully updated user row for ${username}`);
    }

    // ============================================================================
    // ADMIN PRIVILEGE MANAGEMENT FUNCTIONS - GRANT & REVOKE
    // ============================================================================

    async function grantAdminAjax(userId, username) {
        console.log(`🛡️ Grant Admin clicked for user ${userId} (${username})`);
        
        const confirmed = confirm(`Are you sure you want to GRANT admin privileges to ${username}?\n\nThis action will:\n- Give full admin access\n- Send email alerts to all existing admins\n- Be permanently logged for security audit\n\nOnly proceed if you trust this user completely.`);
        
        if (!confirmed) {
            console.log('Grant admin cancelled by user');
            return;
        }
        
        try {
            console.log(`Making API call to: /admin/api/users/${userId}/grant-admin`);
            
            showUsersLoading(true);
            
            const response = await fetch(`/admin/api/users/${userId}/grant-admin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            console.log('API Response status:', response.status);
            
            const result = await response.json();
            console.log('API Response data:', result);
            
            if (result.success) {
                alert(`✅ Admin privileges granted to ${username}`);
                
                // Update the user row in the table instead of reloading
                updateUserRowAdminStatus(userId, true, username);
                
            } else {
                alert(`❌ Error: ${result.error || 'Failed to grant admin privileges'}`);
            }
            
        } catch (error) {
            console.error('Error granting admin privileges:', error);
            alert(`❌ Network error: ${error.message}`);
        } finally {
            showUsersLoading(false);
        }
    }

    async function revokeAdminAjax(userId, username) {
        console.log(`👤❌ Revoke Admin clicked for user ${userId} (${username})`);
        
        const confirmed = confirm(`Are you sure you want to REVOKE admin privileges from ${username}?\n\nThis action will:\n- Remove all admin access\n- Send email notifications to all admins\n- Be logged in the security audit trail`);
        
        if (!confirmed) {
            console.log('Revoke admin cancelled by user');
            return;
        }
        
        try {
            console.log(`Making API call to: /admin/api/users/${userId}/revoke-admin`);
            
            showUsersLoading(true);
            
            const response = await fetch(`/admin/api/users/${userId}/revoke-admin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            console.log('API Response status:', response.status);
            
            const result = await response.json();
            console.log('API Response data:', result);
            
            if (result.success) {
                alert(`✅ Admin privileges revoked from ${username}`);
                
                // Update the user row in the table instead of reloading
                updateUserRowAdminStatus(userId, false, username);
                
            } else {
                alert(`❌ Error: ${result.error || 'Failed to revoke admin privileges'}`);
            }
            
        } catch (error) {
            console.error('Error revoking admin privileges:', error);
            alert(`❌ Network error: ${error.message}`);
        } finally {
            showUsersLoading(false);
        }
    }

    // Enhanced Users Section JavaScript - Full Reports-style Implementation

    // Global state for Users table
    let usersCurrentPage = 1;
    let usersPerPage = 50;
    let usersTotalPages = 1;
    let usersTotalRecords = 0;
    let usersCurrentSort = { field: 'created_at', order: 'desc' };
    let usersCurrentFilters = {};
    let usersSearchDebounceTimer = null;
    let usersAllData = []; // Store all data for client-side filtering

    // Global state for Activity table
    let activityCurrentPage = 1;
    let activityPerPage = 50;
    let activityTotalPages = 1;
    let activityTotalRecords = 0;
    let activityCurrentSort = { field: 'created_at', order: 'desc' };
    let activityCurrentFilters = {};
    let activitySearchDebounceTimer = null;
    let activityAllData = []; // Store all data for client-side filtering

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeUsersSection();
            initializeActivitySection();
        
        // Force our event listeners to override any conflicting ones
        setTimeout(() => {
                    
            const searchInput = document.getElementById('usersRealTimeSearch');
            const adminFilter = document.getElementById('usersAdminStatusFilter');
            const statusFilter = document.getElementById('usersStatusFilter');
            
            if (searchInput) {
                // Clone elements to remove all existing event listeners
                const newSearchInput = searchInput.cloneNode(true);
                const newAdminFilter = adminFilter.cloneNode(true);
                const newStatusFilter = statusFilter.cloneNode(true);
                
                // Replace the old elements
                searchInput.parentNode.replaceChild(newSearchInput, searchInput);
                adminFilter.parentNode.replaceChild(newAdminFilter, adminFilter);
                statusFilter.parentNode.replaceChild(newStatusFilter, statusFilter);
                
                // Add OUR event listeners
                newSearchInput.addEventListener('input', function() {
                    applyUsersFilters();
                });
                
                newAdminFilter.addEventListener('change', function() {
                    applyUsersFilters();
                });
                
                newStatusFilter.addEventListener('change', function() {
                    applyUsersFilters();
                });
                
                        }
        }, 1000); // Wait 1 second for other scripts to load
    });

    document.addEventListener('DOMContentLoaded', function() {
        // Only initialize if users section exists and is active
        const usersSection = document.getElementById('manageUsersSection');
        if (usersSection && usersSection.classList.contains('active')) {
            initializeUsersEnhancements();
        }
    });

    // Global function to initialize users when section becomes active
    window.initializeUsersSection = function() {
        if (!window.usersInitialized) {
            initializeUsersEnhancements();
            window.usersInitialized = true;
        }
    };

    function initializeUsersEnhancements() {
        // Initialize search with debouncing
        const searchInput = document.getElementById('users-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    currentUsersPage = 1;
                    performUsersSearch();
                }, 300);
            });
        }
        
        // Initialize sorting
        document.querySelectorAll('#manageUsersSection #users-table-enhanced .sortable').forEach(header => {
            header.addEventListener('click', function() {
                const field = this.dataset.sortable;
                if (currentUsersSort.field === field) {
                    currentUsersSort.order = currentUsersSort.order === 'asc' ? 'desc' : 'asc';
                } else {
                    currentUsersSort.field = field;
                    currentUsersSort.order = 'asc';
                }
                currentUsersPage = 1;
                updateUsersSortIndicators();
                performUsersSearch();
            });
        });
        
        // Initialize per-page selector
        const perPageSelect = document.getElementById('users-per-page');
        if (perPageSelect) {
            perPageSelect.addEventListener('change', function() {
                usersPerPage = parseInt(this.value);
                currentUsersPage = 1;
                performUsersSearch();
            });
        }
        
        // Initialize filter selectors
        document.querySelectorAll('#users-filter-form select').forEach(select => {
            select.addEventListener('change', function() {
                currentUsersPage = 1;
                performUsersSearch();
            });
        });
        
        // Initialize keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'u':
                        e.preventDefault();
                        document.getElementById('users-search').focus();
                        break;
                }
            }
        });
    }

    function performUsersSearch() {
        const form = document.getElementById('users-filter-form');
        const formData = new FormData(form);
        
        usersCurrentFilters = {
            search: formData.get('search') || '',
            admin_status: formData.get('admin_status') || '',
            status: formData.get('status') || '',
            sort_by: currentUsersSort.field,
            sort_order: currentUsersSort.order,
            page: currentUsersPage,
            per_page: usersPerPage
        };
        
        loadUsersData();
    }

    async function loadUsersData() {
        setUsersLoading(true);
        
        try {
            const data = await AdminEnhancements.fetchData('users', usersCurrentFilters);
            updateUsersTable(data);
            updateUsersPagination(data.pagination);
            updateUsersResultsInfo(data.pagination);
        } catch (error) {
            AdminEnhancements.showToast('Error loading users: ' + error.message, 'error');
        } finally {
            setUsersLoading(false);
        }
    }

    function updateUsersTable(data) {
        const tbody = document.querySelector('#users-table-enhanced tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (data.users && data.users.length > 0) {
            data.users.forEach(user => {
                const row = createUserRow(user);
                tbody.appendChild(row);
            });
        } else {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = '<td colspan="9" style="text-align: center; color: #999; font-style: italic;">No users found</td>';
            tbody.appendChild(emptyRow);
        }
    }

    function createUserRow(user) {
        const row = document.createElement('tr');
        row.className = user.is_admin ? 'table-warning' : '';
        
        const statusBadges = [];
        if (user.is_active) {
            statusBadges.push('<span class="btn btn-success btn-small" style="cursor: default;">Active</span>');
        } else {
            statusBadges.push('<span class="btn btn-secondary btn-small" style="cursor: default;">Inactive</span>');
        }
        if (user.is_verified) {
            statusBadges.push('<span class="btn btn-secondary btn-small" style="cursor: default;">Verified</span>');
        }
        
        const adminBadge = user.is_admin ? 
            '<span class="btn btn-danger btn-small" style="cursor: default;">🛡️ Admin</span>' :
            '<span class="btn btn-secondary btn-small" style="cursor: default;">User</span>';
        
        const youBadge = user.is_current_user ? 
            '<span class="btn btn-secondary btn-small" style="cursor: default; margin-left: 5px;">You</span>' : '';
            
        const actionButtons = user.is_current_user ? 
            '<small style="color: #999; font-style: italic;">Cannot modify own privileges</small>' :
            (user.is_admin ? 
                `<button onclick="revokeAdminAjax(${user.id}, '${user.username}')" class="btn btn-danger btn-small">👤❌ Revoke Admin</button>` :
                `<button onclick="grantAdminAjax(${user.id}, '${user.username}')" class="btn btn-warning btn-small">🛡️ Grant Admin</button>`);
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td><strong>${user.username}</strong>${youBadge}</td>
            <td>${user.email}</td>
            <td>${user.full_name || '-'}</td>
            <td>${statusBadges.join(' ')}</td>
            <td>${adminBadge}</td>
            <td><small>${formatDate(user.created_at)}</small></td>
            <td><small>${user.last_login ? formatDate(user.last_login) : 'Never'}</small></td>
            <td>${actionButtons}</td>
        `;
        
        return row;
    }

    function updateUsersPagination(pagination) {
        const container = document.getElementById('users-pagination');
        if (!container || !pagination) return;
        
        let html = '<div class="pagination">';
        
        // Previous button
        if (pagination.has_prev) {
            html += `<button class="page-btn" onclick="goToUsersPage(${pagination.prev_num})">← Previous</button>`;
        } else {
            html += '<button class="page-btn" disabled>← Previous</button>';
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        if (startPage > 1) {
            html += '<button class="page-btn" onclick="goToUsersPage(1)">1</button>';
            if (startPage > 2) html += '<span class="page-btn" disabled>...</span>';
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            html += `<button class="page-btn ${activeClass}" onclick="goToUsersPage(${i})">${i}</button>`;
        }
        
        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) html += '<span class="page-btn" disabled>...</span>';
            html += `<button class="page-btn" onclick="goToUsersPage(${pagination.pages})">${pagination.pages}</button>`;
        }
        
        // Next button
        if (pagination.has_next) {
            html += `<button class="page-btn" onclick="goToUsersPage(${pagination.next_num})">Next →</button>`;
        } else {
            html += '<button class="page-btn" disabled>Next →</button>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    function goToUsersPage(page) {
        currentUsersPage = page;
        performUsersSearch();
    }

    function updateUsersResultsInfo(pagination) {
        const infoDiv = document.getElementById('users-results-info');
        if (!infoDiv || !pagination) return;
        
        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total);
        
        infoDiv.innerHTML = `Showing ${start}-${end} of ${pagination.total} users`;
    }

    function updateUsersSortIndicators() {
        document.querySelectorAll('#users-table-enhanced .sort-indicator').forEach(indicator => {
            indicator.className = 'sort-indicator';
        });
        
        const activeHeader = document.querySelector(`#manageUsersSection #users-table-enhanced [data-field="${currentUsersSort.field}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.className = `sort-indicator ${currentUsersSort.order}`;
        }
    }

    function clearUsersFilters() {
        document.getElementById('users-filter-form').reset();
        usersCurrentFilters = {};
        currentUsersSort = { field: 'created_at', order: 'desc' };
        currentUsersPage = 1;
        usersPerPage = 20;
        updateUsersSortIndicators();
        loadUsersData();
    }

    function setUsersLoading(loading) {
        const indicator = document.getElementById('users-loading');
        const table = document.getElementById('users-table-enhanced');
        
        if (indicator) {
            indicator.style.display = loading ? 'inline' : 'none';
        }
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }

    // Admin privilege management functions
    async function grantAdminAjax(userId, username) {
        const confirmed = confirm(`Are you sure you want to GRANT admin privileges to ${username}?

    This action will:
    - Give full admin access
    - Send email alerts to all existing admins  
    - Be permanently logged for security audit

    Only proceed if you trust this user completely.`);
        
        if (!confirmed) return;
        
        try {
            const response = await fetch(`/admin/api/users/${userId}/grant-admin`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to grant admin privileges');
            
            AdminEnhancements.showToast(`Admin privileges granted to ${username}`, 'success');
            loadUsersData();
        } catch (error) {
            AdminEnhancements.showToast('Error granting admin privileges: ' + error.message, 'error');
        }
    }

    async function revokeAdminAjax(userId, username) {
        const confirmed = confirm(`Are you sure you want to REVOKE admin privileges from ${username}?

    This action will:
    - Remove all admin access
    - Send email notifications to all admins
    - Be logged in the security audit trail`);
        
        if (!confirmed) return;
        
        try {
            const response = await fetch(`/admin/api/users/${userId}/revoke-admin`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to revoke admin privileges');
            
            AdminEnhancements.showToast(`Admin privileges revoked from ${username}`, 'success');
            loadUsersData();
        } catch (error) {
            AdminEnhancements.showToast('Error revoking admin privileges: ' + error.message, 'error');
        }
    }

    // Utility Functions
    function formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // ============================================================================
    // ENHANCED USERS TABLE FUNCTIONALITY
    // ============================================================================

    function initializeUsersSection() {
        // Set up real-time search
        const searchInput = document.getElementById('usersRealTimeSearch');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(usersSearchDebounceTimer);
                usersSearchDebounceTimer = setTimeout(() => {
                    usersCurrentPage = 1;
                    applyUsersFilters();
                }, 300);
            });
        }

        // Set up filter dropdowns
        const adminStatusFilter = document.getElementById('usersAdminStatusFilter');
        const statusFilter = document.getElementById('usersStatusFilter');
        
        if (adminStatusFilter) {
            adminStatusFilter.addEventListener('change', () => {
                usersCurrentPage = 1;
                applyUsersFilters();
            });
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                usersCurrentPage = 1;
                applyUsersFilters();
            });
        }

        // Set up column visibility checkboxes
        const columnCheckboxes = document.querySelectorAll('.users-column-checkbox');
        columnCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleUsersColumnVisibility(this.dataset.column, this.checked);
            });
        });

        // Load initial data if available
        if (typeof loadUsersData === 'function') {
            loadUsersData();
        }
    }

    function applyUsersFilters() {
        const searchValue = document.getElementById('usersRealTimeSearch')?.value || '';
        const adminStatus = document.getElementById('usersAdminStatusFilter')?.value || '';
        const status = document.getElementById('usersStatusFilter')?.value || '';
        const searchColumn = document.getElementById('usersAdvancedSearchColumn')?.value || 'all';

        usersCurrentFilters = {
            search: searchValue,
            admin_status: adminStatus,
            status: status,
            search_column: searchColumn
        };

        performUsersSearch();
    }

    function toggleUsersSort(field) {
        console.log(`Toggling sort for field: ${field}`);
        
        if (usersCurrentSort.field === field) {
            usersCurrentSort.order = usersCurrentSort.order === 'asc' ? 'desc' : 'asc';
        } else {
            usersCurrentSort.field = field;
            usersCurrentSort.order = 'asc';
        }
        
        usersCurrentPage = 1;
        updateUsersSortIndicators();
        performUsersSearch();
    }

    function updateUsersSortIndicators() {
        // Clear all indicators
        document.querySelectorAll('#manageUsersSection #users-table-enhanced .sort-indicator').forEach(indicator => {
            indicator.textContent = '';
            indicator.className = 'sort-indicator';
        });
        
        // Set active indicator
        const activeIndicator = document.querySelector(`#users-table-enhanced [data-sortable="${usersCurrentSort.field}"] .sort-indicator`);
        if (activeIndicator) {
            activeIndicator.textContent = usersCurrentSort.order === 'asc' ? '↑' : '↓';
            activeIndicator.className = `sort-indicator ${usersCurrentSort.order}`;
        }
    }

    function changeUsersTableDensity() {
        const density = document.getElementById('usersTableDensity').value;
        const table = document.getElementById('users-table-enhanced');
        if (table) {
            table.className = table.className.replace(/density-\w+/g, '');
            table.classList.add(`density-${density}`);
        }
    }

    function toggleUsersColumnVisibilityDropdown() {
        const dropdown = document.getElementById('usersColumnVisibilityDropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }

    function toggleUsersColumnVisibility(column, visible) {
        const table = document.getElementById('users-table-enhanced');
        if (!table) return;
        
        const elements = table.querySelectorAll(`[data-column="${column}"]`);
        elements.forEach(el => {
            el.style.display = visible ? '' : 'none';
        });
    }

    function clearAllUsersFilters() {
        console.log('Clearing all users filters');
        
        // Reset form fields
        document.getElementById('usersRealTimeSearch').value = '';
        document.getElementById('usersAdminStatusFilter').value = '';
        document.getElementById('usersStatusFilter').value = '';
        document.getElementById('usersAdvancedSearchColumn').value = 'all';
        
        // Reset filter state
        usersCurrentFilters = {};
        usersCurrentPage = 1;
        
        // Show all rows
        const table = document.getElementById('users-table-enhanced');
        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                row.style.display = '';
            });
            updateUsersInfo(rows.length, 1, rows.length);
        }
    }

    function changeUsersPerPage() {
        usersPerPage = parseInt(document.getElementById('usersPerPageSelector').value);
        usersCurrentPage = 1;
        if (typeof loadUsersData === 'function') {
            loadUsersData();
        }
    }

    function updateUsersInfo(total, page, perPage) {
        const info = document.getElementById('usersPaginationInfo');
        if (info) {
            const start = (page - 1) * perPage + 1;
            const end = Math.min(page * perPage, total);
            info.textContent = `Showing ${start}-${end} of ${total} users`;
        }
    }

    function updateUsersPagination(currentPage, totalPages) {
        const container = document.getElementById('usersPaginationButtons');
        if (!container) return;
        
        let buttonsHtml = '';
        
        // Previous button
        if (currentPage > 1) {
            buttonsHtml += `<button onclick="goToUsersPage(${currentPage - 1})" class="btn btn-secondary">Previous</button>`;
        }
        
        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage;
            buttonsHtml += `<button onclick="goToUsersPage(${i})" class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}">${i}</button>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            buttonsHtml += `<button onclick="goToUsersPage(${currentPage + 1})" class="btn btn-secondary">Next</button>`;
        }
        
        container.innerHTML = buttonsHtml;
    }

    function goToUsersPage(page) {
        usersCurrentPage = page;
        if (typeof loadUsersData === 'function') {
            loadUsersData();
        }
    }

    function showUsersLoading(loading) {
        const indicator = document.getElementById('usersFilterLoadingIndicator');
        if (indicator) {
            indicator.style.display = loading ? 'flex' : 'none';
        }
        
        const table = document.getElementById('users-table-enhanced');
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }
    
    // Alias for backward compatibility


    // ============================================================================
    // USER MODAL FUNCTIONALITY
    // ============================================================================

    async function openUserModal(userId) {
        console.log(`Opening user modal for user ID: ${userId}`);
        
        try {
            showUsersLoading(true);
            
            const response = await fetch(`/admin/api/users/${userId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch user details: ${response.statusText}`);
            }
            
            const user = await response.json();
            
            // Update modal title
            document.getElementById('userModalTitle').textContent = `User Details: ${user.username}`;
            
            // Format user data for display
            const userDetails = [
                { label: 'User ID', value: user.id },
                { label: 'Username', value: user.username },
                { label: 'Email', value: user.email },
                { label: 'Full Name', value: user.full_name || 'Not provided' },
                { label: 'Status', value: user.is_active ? 'Active' : 'Inactive' },
                { label: 'Verified', value: user.is_verified ? 'Yes' : 'No' },
                { label: 'Admin', value: user.is_admin ? 'Yes' : 'No' },
                { label: 'Created', value: user.created_at ? formatDate(user.created_at) : 'Unknown' },
                { label: 'Last Login', value: user.last_login ? formatDate(user.last_login) : 'Never' },
                { label: 'Total XP', value: user.total_xp || 0 },
                { label: 'Current Plan', value: user.subscription_tier || 'Free' },
                { label: 'Profile Picture', value: user.profile_picture ? 'Yes' : 'No' },
                { label: 'Preferred Language', value: user.preferred_language || 'Norwegian' }
            ];
            
            // Generate HTML for user details
            let detailsHtml = '';
            userDetails.forEach(detail => {
                detailsHtml += `
                    <div class="user-detail-row">
                        <span class="user-detail-label">${detail.label}:</span>
                        <span class="user-detail-value">${detail.value}</span>
                    </div>
                `;
            });
            
            // Update modal body
            document.getElementById('userModalBody').innerHTML = detailsHtml;
            
            // Show modal
            document.getElementById('userModal').style.display = 'block';
            
        } catch (error) {
            console.error('Error opening user modal:', error);
            alert(`Error loading user details: ${error.message}`);
        } finally {
            showUsersLoading(false);
        }
    }

    function closeUserModal() {
        document.getElementById('userModal').style.display = 'none';
    }

    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('userModal');
        if (event.target === modal) {
            closeUserModal();
        }
    });

    // ============================================================================
    // PROPER FUNCTION IMPLEMENTATIONS
    // ============================================================================

    function performUsersSearch() {
        
        // Show loading
        showUsersLoading(true);
        
        // Apply client-side filtering for now (could be replaced with server-side later)
        const table = document.getElementById('users-table-enhanced');
        if (!table) {
            showUsersLoading(false);
            return;
        }
        
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        // Convert NodeList to Array for sorting
        const rowsArray = Array.from(rows);
        
        // Apply filters
        const filteredRows = rowsArray.filter(row => {
            let shouldShow = true;
            
            // Apply search filter
            if (usersCurrentFilters.search) {
                const searchText = usersCurrentFilters.search.toLowerCase();
                const rowText = row.textContent.toLowerCase();
                
                if (usersCurrentFilters.search_column && usersCurrentFilters.search_column !== 'all') {
                    const specificCell = row.querySelector(`[data-column="${usersCurrentFilters.search_column}"]`);
                    shouldShow = shouldShow && specificCell && specificCell.textContent.toLowerCase().includes(searchText);
                } else {
                    shouldShow = shouldShow && rowText.includes(searchText);
                }
            }
            
            // Apply admin status filter
            if (usersCurrentFilters.admin_status) {
                const adminCell = row.querySelector('[data-column="admin"]');
                if (adminCell) {
                    const isAdmin = adminCell.textContent.includes('Admin');
                    if (usersCurrentFilters.admin_status === 'admin' && !isAdmin) {
                        shouldShow = false;
                    } else if (usersCurrentFilters.admin_status === 'user' && isAdmin) {
                        shouldShow = false;
                    }
                }
            }
            
            // Apply status filter
            if (usersCurrentFilters.status) {
                const statusCell = row.querySelector('[data-column="status"]');
                if (statusCell) {
                    const statusText = statusCell.textContent.toLowerCase();
                    if (usersCurrentFilters.status === 'active' && !statusText.includes('active')) {
                        shouldShow = false;
                    } else if (usersCurrentFilters.status === 'inactive' && !statusText.includes('inactive')) {
                        shouldShow = false;
                    } else if (usersCurrentFilters.status === 'verified' && !statusText.includes('verified')) {
                        shouldShow = false;
                    } else if (usersCurrentFilters.status === 'unverified' && statusText.includes('verified')) {
                        shouldShow = false;
                    }
                }
            }
            
            return shouldShow;
        });
        
        // Apply sorting
        if (usersCurrentSort.field) {
            filteredRows.sort((a, b) => {
                const aCell = a.querySelector(`[data-column="${usersCurrentSort.field}"]`);
                const bCell = b.querySelector(`[data-column="${usersCurrentSort.field}"]`);
                
                if (!aCell || !bCell) return 0;
                
                let aValue = aCell.textContent.trim();
                let bValue = bCell.textContent.trim();
                
                // Handle numeric fields
                if (usersCurrentSort.field === 'id') {
                    aValue = parseInt(aValue) || 0;
                    bValue = parseInt(bValue) || 0;
                    return usersCurrentSort.order === 'asc' ? aValue - bValue : bValue - aValue;
                }
                
                // Handle date fields
                if (usersCurrentSort.field === 'created_at' || usersCurrentSort.field === 'last_login') {
                    const aDate = new Date(aValue);
                    const bDate = new Date(bValue);
                    if (aValue === 'Never') return usersCurrentSort.order === 'asc' ? 1 : -1;
                    if (bValue === 'Never') return usersCurrentSort.order === 'asc' ? -1 : 1;
                    return usersCurrentSort.order === 'asc' ? aDate - bDate : bDate - aDate;
                }
                
                // Handle text fields
                return usersCurrentSort.order === 'asc' 
                    ? aValue.localeCompare(bValue) 
                    : bValue.localeCompare(aValue);
            });
        }
        
        // Hide all rows first
        rowsArray.forEach(row => {
            row.style.display = 'none';
        });
        
        // Show filtered and sorted rows
        const tbody = table.querySelector('tbody');
        filteredRows.forEach((row, index) => {
            row.style.display = '';
            tbody.appendChild(row); // Re-append in sorted order
        });
        
        visibleCount = filteredRows.length;
        
        // Update results info
        updateUsersInfo(visibleCount, 1, visibleCount);
        
        // Update sort indicators
        updateUsersSortIndicators();
        
        showUsersLoading(false);
    }

    // ============================================================================
    // GLOBAL FUNCTION EXPORTS
    // ============================================================================

    window.initializeUsersSection = initializeUsersSection;
    window.initializeActivitySection = initializeActivitySection;
    window.grantAdminAjax = grantAdminAjax;
    window.revokeAdminAjax = revokeAdminAjax;
    window.openUserModal = openUserModal;
    window.closeUserModal = closeUserModal;
    window.updateUserRowAdminStatus = updateUserRowAdminStatus;
    window.toggleUsersSort = toggleUsersSort;
    window.toggleActivitySort = toggleActivitySort;
    window.toggleUsersColumnVisibilityDropdown = toggleUsersColumnVisibilityDropdown;
    window.changeUsersTableDensity = changeUsersTableDensity;
    window.clearAllUsersFilters = clearAllUsersFilters;
    window.changeUsersPerPage = changeUsersPerPage;
    window.toggleActivityColumnVisibilityDropdown = toggleActivityColumnVisibilityDropdown;
    window.changeActivityTableDensity = changeActivityTableDensity;
    window.clearAllActivityFilters = clearAllActivityFilters;
    window.changeActivityPerPage = changeActivityPerPage;
    window.goToActivityPage = goToActivityPage;
})();