/**
 * Admin User Management JavaScript
 * Enhanced user management functionality with AJAX, filtering, sorting, and pagination
 * Matches the Spørsmål section UI features and functionality
 */

(function() {
    'use strict';

    // Check if we're on the user management page
    if (!document.getElementById('user-search')) {
        return; // Exit if not on user management page
    }

    // User management state
    let currentUserData = {
        search: '',
        adminStatus: '',
        activity: '',
        subscription: '',
        page: 1,
        perPage: 25,
        sortBy: 'created_at',
        sortOrder: 'desc'
    };
    
    let currentUserId = window.currentUserId || null;
    let searchTimeout;

    // Initialize user management functionality
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[UserManagement] DOM loaded, initializing...');
        initializeUserManagement();
    });

    // Initialize on immediate load for better responsiveness
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeUserManagement);
    } else {
        // DOM already loaded
        console.log('[UserManagement] DOM already loaded, initializing immediately...');
        setTimeout(initializeUserManagement, 100);
    }

    // Fallback initialization with error catching
    setTimeout(() => {
        if (!document.getElementById('user-search')) {
            console.log('[UserManagement] Elements not found, retrying...');
            return;
        }
        if (!window.userManagementInitialized) {
            console.log('[UserManagement] Fallback initialization...');
            initializeUserManagement();
        }
    }, 1000);

    /**
     * Initialize complete user management system
     */
    function initializeUserManagement() {
        if (window.userManagementInitialized) {
            console.log('[UserManagement] Already initialized, skipping...');
            return;
        }
        
        console.log('[UserManagement] Initializing enhanced user management...');
        
        try {
            initializeUserFiltering();
            initializeUserSorting();
            initializeEnhancedFeatures();
            initializeKeyboardShortcuts();
            
            // Mark as initialized
            window.userManagementInitialized = true;
            
            // Load initial data with enhanced error handling
            setTimeout(() => {
                console.log('[UserManagement] Starting initial data load...');
                loadUsers();
            }, 500);
            
            console.log('[UserManagement] Enhanced user management initialized successfully');
        } catch (error) {
            console.error('[UserManagement] Initialization error:', error);
        }
    }

    /**
     * Initialize enhanced features matching Spørsmål section
     */
    function initializeEnhancedFeatures() {
        try {
            // Add enhanced results display
            addEnhancedResultsDisplay();
            
            // Add keyboard accessibility to sortable headers
            addKeyboardSortSupport();
            
            // Initialize loading states
            initializeLoadingStates();
            
            // Add smooth transitions
            addSmoothTransitions();
            
            console.log('[UserManagement] Enhanced features initialized successfully');
        } catch (error) {
            console.error('[UserManagement] Error initializing enhanced features:', error);
        }
    }

    /**
     * Add enhanced results display above table
     */
    function addEnhancedResultsDisplay() {
        const tableContainer = document.querySelector('.table-container');
        if (!tableContainer) {
            console.log('[UserManagement] Table container not found');
            return;
        }
        
        // Check if enhanced results display already exists
        if (document.getElementById('enhanced-results-display')) {
            console.log('[UserManagement] Enhanced results display already exists');
            return;
        }
        
        // Find a safe insertion point - insert before the table itself
        const table = tableContainer.querySelector('table');
        if (!table) {
            console.log('[UserManagement] Table not found in container');
            return;
        }
        
        // Add results counter and controls
        const resultsDisplay = document.createElement('div');
        resultsDisplay.id = 'enhanced-results-display';
        resultsDisplay.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        `;
        
        resultsDisplay.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px;">
                <div id="users-results-counter" style="color: #666; font-size: 14px;">
                    <span id="filtered-users-count">0</span> of <span id="total-users-count">0</span> users
                </div>
                <div id="users-filter-status" style="color: #28a745; font-size: 12px; font-weight: bold; display: none;">
                    ✓ Filters Active
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <button id="refresh-users-btn" class="btn btn-secondary btn-small" title="Refresh user data (Ctrl+R)">
                    🔄 Refresh
                </button>
                <button id="clear-all-filters-btn" class="btn btn-secondary btn-small" title="Clear all filters (Ctrl+X)" style="display: none;">
                    🗑️ Clear All
                </button>
            </div>
        `;
        
        // Insert before the table
        tableContainer.insertBefore(resultsDisplay, table);
        
        // Add event listeners with error handling
        try {
            const refreshBtn = document.getElementById('refresh-users-btn');
            const clearBtn = document.getElementById('clear-all-filters-btn');
            
            if (refreshBtn) {
                refreshBtn.addEventListener('click', refreshUsers);
            }
            if (clearBtn) {
                clearBtn.addEventListener('click', clearAllUserFilters);
            }
            
            console.log('[UserManagement] Enhanced results display added successfully');
        } catch (error) {
            console.error('[UserManagement] Error adding event listeners:', error);
        }
    }

    /**
     * Add keyboard support for sortable headers
     */
    function addKeyboardSortSupport() {
        try {
            const sortableHeaders = document.querySelectorAll('.sortable');
            
            if (sortableHeaders.length === 0) {
                console.log('[UserManagement] No sortable headers found');
                return;
            }
            
            sortableHeaders.forEach(header => {
                header.setAttribute('tabindex', '0');
                header.setAttribute('role', 'button');
                header.setAttribute('aria-label', `Sort by ${header.textContent.trim()}`);
                
                header.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const column = this.getAttribute('data-column');
                        if (column) {
                            toggleUserSort(column);
                        }
                    }
                });
            });
            
            console.log(`[UserManagement] Keyboard support added to ${sortableHeaders.length} sortable headers`);
        } catch (error) {
            console.error('[UserManagement] Error adding keyboard sort support:', error);
        }
    }

    /**
     * Initialize loading states and animations
     */
    function initializeLoadingStates() {
        // Add CSS for loading animations if not exists
        if (!document.querySelector('#user-loading-styles')) {
            const style = document.createElement('style');
            style.id = 'user-loading-styles';
            style.textContent = `
                .user-table-loading {
                    opacity: 0.6;
                    pointer-events: none;
                    transition: opacity 0.3s ease;
                }
                
                .user-row-highlight {
                    background-color: #e3f2fd !important;
                    transition: background-color 0.5s ease;
                }
                
                .user-row-fade-in {
                    animation: userRowFadeIn 0.5s ease;
                }
                
                @keyframes userRowFadeIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .users-pagination-loading {
                    opacity: 0.5;
                    pointer-events: none;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Add smooth transitions for table updates
     */
    function addSmoothTransitions() {
        const usersTable = document.getElementById('users-table');
        if (usersTable) {
            usersTable.style.transition = 'opacity 0.3s ease';
        }
    }

    /**
     * Initialize keyboard shortcuts
     */
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Only activate shortcuts when user management page is active
            if (!document.getElementById('user-search')) return;
            
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'f':
                        e.preventDefault();
                        document.getElementById('user-search').focus();
                        AdminUtils.showToast('Search users field focused', 'info');
                        break;
                    case 'r':
                        e.preventDefault();
                        refreshUsers();
                        break;
                    case 'x':
                        e.preventDefault();
                        clearAllUserFilters();
                        break;
                }
            }
            
            // ESC to clear search
            if (e.key === 'Escape') {
                const searchInput = document.getElementById('user-search');
                if (searchInput.value) {
                    searchInput.value = '';
                    currentUserData.search = '';
                    performFilteredUserSearch(true);
                    AdminUtils.showToast('Search cleared', 'info');
                }
            }
        });
    }

    /**
     * Initialize user filtering controls
     */
    function initializeUserFiltering() {
        try {
            const searchInput = document.getElementById('user-search');
            const adminStatusFilter = document.getElementById('admin-status-filter');
            const activityFilter = document.getElementById('activity-filter');
            const clearFiltersBtn = document.getElementById('clear-filters-btn');
            const perPageSelect = document.getElementById('per-page-select');

            if (!searchInput) {
                console.log('[UserManagement] Search input not found - filtering may not work properly');
                return;
            }

            // Real-time search with debouncing
            searchInput.addEventListener('input', AdminUtils.debounce(function() {
                currentUserData.search = searchInput.value.trim();
                performFilteredUserSearch(true);
                updateFilterStatus();
            }, 300));

            // Filter change handlers
            if (adminStatusFilter) {
                adminStatusFilter.addEventListener('change', function() {
                    currentUserData.adminStatus = this.value;
                    performFilteredUserSearch(true);
                    updateFilterStatus();
                });
            } else {
                console.log('[UserManagement] Admin status filter not found');
            }

            if (activityFilter) {
                activityFilter.addEventListener('change', function() {
                    currentUserData.activity = this.value;
                    performFilteredUserSearch(true);
                    updateFilterStatus();
                });
            } else {
                console.log('[UserManagement] Activity filter not found');
            }

            // Per page selector
            if (perPageSelect) {
                perPageSelect.addEventListener('change', function() {
                    currentUserData.perPage = parseInt(this.value);
                    performFilteredUserSearch(true);
                });
            } else {
                console.log('[UserManagement] Per page selector not found');
            }

            // Clear filters
            if (clearFiltersBtn) {
                clearFiltersBtn.addEventListener('click', function() {
                    clearAllUserFilters();
                });
            } else {
                console.log('[UserManagement] Clear filters button not found');
            }
            
            console.log('[UserManagement] User filtering initialized successfully');
        } catch (error) {
            console.error('[UserManagement] Error initializing user filtering:', error);
        }
    }

    /**
     * Update filter status indicator
     */
    function updateFilterStatus() {
        const hasFilters = currentUserData.search || 
                          currentUserData.adminStatus || 
                          currentUserData.activity;
        
        const filterStatus = document.getElementById('users-filter-status');
        const clearAllBtn = document.getElementById('clear-all-filters-btn');
        
        if (filterStatus) {
            filterStatus.style.display = hasFilters ? 'block' : 'none';
        }
        
        if (clearAllBtn) {
            clearAllBtn.style.display = hasFilters ? 'inline-block' : 'none';
        }
    }

    /**
     * Initialize user table sorting
     */
    function initializeUserSorting() {
        AdminUtils.initializeSorting('.sortable', function(column) {
            toggleUserSort(column);
        });
        updateUserSortIndicators();
    }

    /**
     * Toggle sort column/order
     */
    function toggleUserSort(column) {
        if (currentUserData.sortBy === column) {
            currentUserData.sortOrder = currentUserData.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            currentUserData.sortBy = column;
            currentUserData.sortOrder = 'asc';
        }
        
        updateUserSortIndicators();
        performFilteredUserSearch(true);
        
        AdminUtils.showToast(`Sorted by ${column} (${currentUserData.sortOrder})`, 'info');
    }

    /**
     * Update visual sort indicators
     */
    function updateUserSortIndicators() {
        AdminUtils.updateSortIndicators(currentUserData.sortBy, currentUserData.sortOrder);
    }

    /**
     * Perform filtered user search
     */
    function performFilteredUserSearch(resetPage = false) {
        if (resetPage) {
            currentUserData.page = 1;
        }
        
        setUserFilterLoading(true);
        loadUsers();
    }

    /**
     * Set loading state for filters
     */
    function setUserFilterLoading(isLoading) {
        const loadingDiv = document.getElementById('filter-loading');
        if (loadingDiv) {
            loadingDiv.style.display = isLoading ? 'block' : 'none';
        }
    }

    /**
     * Clear all filters with animation
     */
    function clearAllUserFilters() {
        currentUserData = {
            search: '',
            adminStatus: '',
            activity: '',
            subscription: '',
            page: 1,
            perPage: 25,
            sortBy: 'created_at',
            sortOrder: 'desc'
        };

        // Reset form elements with animation
        const searchInput = document.getElementById('user-search');
        const adminStatusFilter = document.getElementById('admin-status-filter');
        const activityFilter = document.getElementById('activity-filter');
        const perPageSelect = document.getElementById('per-page-select');

        if (searchInput) {
            searchInput.style.transition = 'all 0.3s ease';
            searchInput.value = '';
        }
        if (adminStatusFilter) adminStatusFilter.value = '';
        if (activityFilter) activityFilter.value = '';
        if (perPageSelect) perPageSelect.value = '25';

        updateUserSortIndicators();
        updateFilterStatus();
        performFilteredUserSearch();
        
        AdminUtils.showToast('All filters cleared', 'success');
    }

    /**
     * Refresh users data
     */
    function refreshUsers() {
        AdminUtils.showToast('Refreshing user data...', 'info');
        loadUsers();
    }

    /**
     * Load users via AJAX with enhanced UI updates
     */
    function loadUsers() {
        const params = new URLSearchParams({
            search: currentUserData.search,
            admin_status: currentUserData.adminStatus,
            activity: currentUserData.activity,
            page: currentUserData.page,
            per_page: currentUserData.perPage,
            sort_by: currentUserData.sortBy,
            sort_order: currentUserData.sortOrder
        });

        const tableContainer = document.querySelector('.table-container');
        const usersTable = document.getElementById('users-table');
        
        // Enhanced loading state
        if (tableContainer) {
            AdminUtils.setLoadingState(tableContainer, true, 'Loading users...');
        }
        
        if (usersTable) {
            usersTable.classList.add('user-table-loading');
        }

        AdminUtils.makeAjaxRequest(`/admin/api/users?${params}`)
            .then(data => {
                console.log('[UserManagement] API Response received:', data);
                
                if (data && data.success) {
                    console.log('[UserManagement] Processing successful response...');
                    updateUsersTable(data.users);
                    updateUserPagination(data.pagination);
                    updateUserStats(data.stats);
                    updateResultsCounter(data.stats.filtered, data.stats.total_users);
                    updateEnhancedResultsDisplay(data.pagination, data.stats);
                    AdminUtils.showToast(`Successfully loaded ${data.users.length} users`, 'success', 3000);
                } else {
                    console.error('[UserManagement] API returned error:', data);
                    AdminUtils.showToast('Error loading users: ' + (data?.error || 'Unknown error'), 'error');
                }
            })
            .catch(error => {
                console.error('Error loading users:', error);
                AdminUtils.showToast('Failed to load users', 'error');
            })
            .finally(() => {
                if (tableContainer) {
                    AdminUtils.setLoadingState(tableContainer, false);
                }
                if (usersTable) {
                    usersTable.classList.remove('user-table-loading');
                }
                setUserFilterLoading(false);
            });
    }

    /**
     * Update enhanced results display
     */
    function updateEnhancedResultsDisplay(pagination, stats) {
        const filteredCount = document.getElementById('filtered-users-count');
        const totalCount = document.getElementById('total-users-count');
        
        if (filteredCount) filteredCount.textContent = pagination.total;
        if (totalCount) totalCount.textContent = stats.total_users;
    }

    /**
     * Update users table with enhanced animations
     */
    function updateUsersTable(users) {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #666;">No users found matching the current filters</td></tr>';
            return;
        }

        tbody.innerHTML = users.map((user, index) => {
            const isCurrentUser = user.id === currentUserId;
            const rowClass = user.is_admin ? 'table-warning' : '';
            
            return `
                <tr class="${rowClass} user-row-fade-in" data-user-id="${user.id}" style="animation-delay: ${index * 0.05}s;">
                    <td>${user.id}</td>
                    <td>
                        <strong>${AdminUtils.escapeHtml(user.username)}</strong>
                        ${isCurrentUser ? '<span class="btn btn-secondary btn-small" style="cursor: default; margin-left: 5px;">You</span>' : ''}
                    </td>
                    <td>${AdminUtils.escapeHtml(user.email)}</td>
                    <td>${AdminUtils.escapeHtml(user.full_name) || '-'}</td>
                    <td>
                        <span class="btn ${user.is_active ? 'btn-success' : 'btn-secondary'} btn-small" style="cursor: default;">
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                        ${user.is_verified ? '<span class="btn btn-secondary btn-small" style="cursor: default; margin-left: 5px;">Verified</span>' : ''}
                    </td>
                    <td>
                        <span class="btn ${user.is_admin ? 'btn-danger' : 'btn-secondary'} btn-small" style="cursor: default;">
                            ${user.is_admin ? '🛡️ Admin' : 'User'}
                        </span>
                    </td>
                    <td>
                        <small>${user.created_at || '-'}</small>
                    </td>
                    <td>
                        <small>${user.last_login || 'Never'}</small>
                    </td>
                    <td>
                        ${generateUserActionButtons(user, isCurrentUser)}
                    </td>
                </tr>
            `;
        }).join('');
    }

    /**
     * Generate action buttons for user with enhanced styling
     */
    function generateUserActionButtons(user, isCurrentUser) {
        if (isCurrentUser) {
            return '<small style="color: #999; font-style: italic;">Cannot modify own privileges</small>';
        }

        const buttons = [];

        // Admin privilege buttons with enhanced styling
        if (user.is_admin) {
            buttons.push(`
                <button onclick="updateUserPrivileges(${user.id}, 'revoke_admin')" 
                        class="btn btn-danger btn-small enhanced-btn"
                        title="Revoke admin privileges"
                        style="transition: all 0.2s ease;">
                    👤❌ Revoke Admin
                </button>
            `);
        } else {
            buttons.push(`
                <button onclick="updateUserPrivileges(${user.id}, 'grant_admin')" 
                        class="btn btn-warning btn-small enhanced-btn"
                        title="Grant admin privileges"
                        style="transition: all 0.2s ease;">
                    🛡️ Grant Admin
                </button>
            `);
        }

        // Active status toggle with enhanced styling
        buttons.push(`
            <button onclick="updateUserPrivileges(${user.id}, 'toggle_active')" 
                    class="btn ${user.is_active ? 'btn-secondary' : 'btn-success'} btn-small enhanced-btn"
                    title="${user.is_active ? 'Deactivate' : 'Activate'} user"
                    style="margin-left: 5px; transition: all 0.2s ease;">
                ${user.is_active ? '🚫 Deactivate' : '✅ Activate'}
            </button>
        `);

        return buttons.join('');
    }
    /**
     * Update user stats display
     */
    function updateUserStats(stats) {
        console.log('[UserManagement] Updating stats:', stats);
        
        const totalUsersEl = document.getElementById('total-users-stat');
        const adminUsersEl = document.getElementById('admin-users-stat');
        const activeUsersEl = document.getElementById('active-users-stat');
        const inactiveUsersEl = document.getElementById('inactive-users-stat');
        
        if (totalUsersEl) totalUsersEl.textContent = stats.total_users || 0;
        if (adminUsersEl) adminUsersEl.textContent = stats.admin_users || 0;
        if (activeUsersEl) activeUsersEl.textContent = stats.active_users || 0;
        if (inactiveUsersEl) inactiveUsersEl.textContent = stats.inactive_users || 0;
    }

    /**
     * Update results counter
     */
    function updateResultsCounter(filtered, total) {
        const filteredCount = document.getElementById('filtered-users-count');
        const totalCount = document.getElementById('total-users-count');
        
        if (filteredCount) filteredCount.textContent = filtered;
        if (totalCount) totalCount.textContent = total;
    }
    /**
     * Update user pagination controls with enhanced UI (matching Spørsmål section)
     */
    function updateUserPagination(pagination) {
        const container = document.getElementById('pagination-container');
        if (!container) return;
        
        if (pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        // Create enhanced pagination matching Spørsmål section
        let paginationHTML = `
            <div class="enhanced-pagination-container" style="
                background: rgba(255, 255, 255, 0.9);
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 15px;
            ">
                <!-- Pagination Info -->
                <div class="pagination-info" style="color: #666; font-size: 14px; display: flex; align-items: center; gap: 10px;">
                    <span style="font-weight: 500;">
                        Showing ${((pagination.page - 1) * pagination.per_page) + 1}-${Math.min(pagination.page * pagination.per_page, pagination.total)} 
                        of ${pagination.total} users
                    </span>
                    ${pagination.total !== pagination.total ? `
                        <span style="color: #28a745; font-size: 12px; background: rgba(40, 167, 69, 0.1); padding: 2px 8px; border-radius: 12px;">
                            Filtered Results
                        </span>
                    ` : ''}
                </div>
                
                <!-- Pagination Controls -->
                <div class="pagination-controls" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        `;
        
        // Previous button
        if (pagination.has_prev) {
            paginationHTML += `
                <button onclick="goToUserPage(${pagination.prev_num})" 
                        class="btn btn-secondary btn-small pagination-btn"
                        title="Previous page"
                        style="display: flex; align-items: center; gap: 5px; transition: all 0.2s ease;">
                    ← Previous
                </button>
            `;
        }
        
        // Page numbers with smart ellipsis (matching Spørsmål section)
        const pages = AdminUtils.generatePageNumbers(pagination.page, pagination.pages);
        pages.forEach(page => {
            if (page === '...') {
                paginationHTML += '<span style="padding: 8px 12px; color: #999; font-weight: 500;">...</span>';
            } else if (page === pagination.page) {
                paginationHTML += `
                    <button class="btn btn-primary btn-small pagination-btn active" 
                            style="cursor: default; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; font-weight: bold;">
                        ${page}
                    </button>
                `;
            } else {
                paginationHTML += `
                    <button onclick="goToUserPage(${page})" 
                            class="btn btn-secondary btn-small pagination-btn"
                            style="transition: all 0.2s ease;">
                        ${page}
                    </button>
                `;
            }
        });
        
        // Next button
        if (pagination.has_next) {
            paginationHTML += `
                <button onclick="goToUserPage(${pagination.next_num})" 
                        class="btn btn-secondary btn-small pagination-btn"
                        title="Next page"
                        style="display: flex; align-items: center; gap: 5px; transition: all 0.2s ease;">
                    Next →
                </button>
            `;
        }
        
        paginationHTML += `
                </div>
            </div>
        `;
        
        container.innerHTML = paginationHTML;
        
        // Add hover effects to pagination buttons
        container.querySelectorAll('.pagination-btn:not(.active)').forEach(btn => {
            btn.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-1px)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            });
            
            btn.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '';
            });
        });
    }

    /**
     * Update user privileges (global function)
     */
    window.updateUserPrivileges = function(userId, action) {
        if (!userId || !action) {
            AdminUtils.showToast('Invalid parameters for user privilege update', 'error');
            return;
        }

        // Show confirmation for admin actions
        let confirmMessage = '';
        if (action === 'grant_admin') {
            confirmMessage = 'Are you sure you want to GRANT admin privileges to this user?\n\nThis action will:\n- Give full admin access\n- Send email alerts to all existing admins\n- Be permanently logged for security audit\n\nOnly proceed if you trust this user completely.';
        } else if (action === 'revoke_admin') {
            confirmMessage = 'Are you sure you want to REVOKE admin privileges from this user?\n\nThis action will:\n- Remove all admin access\n- Send email notifications to all admins\n- Be logged in the security audit trail';
        } else if (action === 'toggle_active') {
            confirmMessage = 'Are you sure you want to change this user\'s active status?';
        }

        if (confirmMessage && !confirm(confirmMessage)) {
            return;
        }

        // Show loading toast
        AdminUtils.showToast('Updating user privileges...', 'info', 2000);

        // Make AJAX request
        fetch(`/admin/api/user/update-privileges/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: action })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                AdminUtils.showToast(data.message, 'success');
                
                // Show warnings if any
                if (data.warnings && data.warnings.length > 0) {
                    data.warnings.forEach(warning => {
                        AdminUtils.showToast(`Warning: ${warning}`, 'warning');
                    });
                }
                
                // Refresh the users table
                loadUsers();
            } else {
                AdminUtils.showToast(data.error || 'Failed to update user privileges', 'error');
                
                // Show warnings if any
                if (data.warnings && data.warnings.length > 0) {
                    data.warnings.forEach(warning => {
                        AdminUtils.showToast(`Warning: ${warning}`, 'warning');
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error updating user privileges:', error);
            AdminUtils.showToast('Network error occurred while updating user privileges', 'error');
        });
    };

    /**
     * Go to specific page (global function)
     */
    window.goToUserPage = function(page) {
        currentUserData.page = page;
        performFilteredUserSearch();
    };

})();

// Add enhanced button styles
if (!document.querySelector('#enhanced-user-styles')) {
    const style = document.createElement('style');
    style.id = 'enhanced-user-styles';
    style.textContent = `
        .enhanced-btn:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        
        .pagination-btn {
            min-width: 40px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .enhanced-pagination-container {
            animation: fadeInUp 0.5s ease;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

