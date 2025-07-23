// Reports Section Enhancement JavaScript - Support for multiple tables
(function() {
    'use strict';
    
    // CSRF token utility
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    let currentReportId = null;

    // Reports table state
    let reportsCurrentFilters = {};
    let reportsCurrentSort = { field: 'created_at', order: 'desc' };
    let reportsCurrentPage = 1;
    let reportsPerPage = 20;

    // Security Alerts table state
    let securityAlertsCurrentFilters = {};
    let securityAlertsCurrentSort = { field: 'created_at', order: 'desc' };
    let securityAlertsCurrentPage = 1;
    let securityAlertsPerPage = 20;

    // User Feedback table state
    let userFeedbackCurrentFilters = {};
    let userFeedbackCurrentSort = { field: 'created_at', order: 'desc' };
    let userFeedbackCurrentPage = 1;
    let userFeedbackPerPage = 20;

    // Debounce timers for search
    let reportsSearchTimeout;
    let securityAlertsSearchTimeout;
    let userFeedbackSearchTimeout;

    document.addEventListener('DOMContentLoaded', function() {
        // Only initialize if reports section exists and is active
        const reportsSection = document.getElementById('reportsSection');
        if (reportsSection && reportsSection.classList.contains('active')) {
            initializeReportsEnhancements();
        }
    });

    // Make functions globally available for section switching
    window.initializeReportsEnhancements = initializeReportsEnhancements;
    window.performReportsSearch = performReportsSearch;
    window.performSecurityAlertsSearch = performSecurityAlertsSearch;
    window.performUserFeedbackSearch = performUserFeedbackSearch;
    window.clearReportsFilters = clearReportsFilters;
    window.clearSecurityAlertsFilters = clearSecurityAlertsFilters;
    window.clearUserFeedbackFilters = clearUserFeedbackFilters;

    // Global function to initialize reports when section becomes active
    window.initializeReportsSection = function() {
        if (!window.reportsInitialized) {
            initializeReportsEnhancements();
            window.reportsInitialized = true;
        }
    };

    function initializeReportsEnhancements() {
        console.log('🔧 Initializing Reports section enhancements...');
        
        // Initialize search inputs with debouncing
        const reportsSearchInput = document.getElementById('reports-search');
        if (reportsSearchInput) {
            // Remove any existing event listeners and add new one
            reportsSearchInput.removeEventListener('input', debouncedReportsSearch);
            reportsSearchInput.addEventListener('input', debouncedReportsSearch);
        }
        
        const securityAlertsSearchInput = document.getElementById('security-alerts-search');
        if (securityAlertsSearchInput) {
            securityAlertsSearchInput.removeEventListener('input', debouncedSecurityAlertsSearch);
            securityAlertsSearchInput.addEventListener('input', debouncedSecurityAlertsSearch);
        }
        
        const userFeedbackSearchInput = document.getElementById('user-feedback-search');
        if (userFeedbackSearchInput) {
            userFeedbackSearchInput.removeEventListener('input', debouncedUserFeedbackSearch);
            userFeedbackSearchInput.addEventListener('input', debouncedUserFeedbackSearch);
        }
        
        // Initialize form event prevention
        const reportsForm = document.getElementById('reports-filter-form');
        if (reportsForm) {
            reportsForm.addEventListener('submit', function(e) {
                e.preventDefault();
                performReportsSearch();
                return false;
            });
        }
        
        const securityAlertsForm = document.getElementById('security-alerts-filter-form');
        if (securityAlertsForm) {
            securityAlertsForm.addEventListener('submit', function(e) {
                e.preventDefault();
                performSecurityAlertsSearch();
                return false;
            });
        }
        
        const userFeedbackForm = document.getElementById('user-feedback-filter-form');
        if (userFeedbackForm) {
            userFeedbackForm.addEventListener('submit', function(e) {
                e.preventDefault();
                performUserFeedbackSearch();
                return false;
            });
        }
        
        // Initialize sorting
        document.querySelectorAll('.sortable').forEach(header => {
            header.addEventListener('click', function() {
                const field = this.dataset.field;
                if (reportsCurrentSort.field === field) {
                    reportsCurrentSort.order = reportsCurrentSort.order === 'asc' ? 'desc' : 'asc';
                } else {
                    reportsCurrentSort.field = field;
                    reportsCurrentSort.order = 'asc';
                }
                reportsCurrentPage = 1;
                updateSortIndicators();
                performReportsSearch();
            });
        });
        
        // Initialize per-page selector
        const perPageSelect = document.getElementById('reports-per-page');
        if (perPageSelect) {
            perPageSelect.addEventListener('change', function() {
                reportsPerPage = parseInt(this.value);
                reportsCurrentPage = 1;
                performReportsSearch();
            });
        }
        
        // Initialize keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'f':
                        e.preventDefault();
                        const searchInput = document.getElementById('reports-search');
                        if (searchInput) searchInput.focus();
                        break;
                    case 'r':
                        e.preventDefault();
                        clearReportsFilters();
                        break;
                }
            }
            if (e.key === 'Escape') {
                const reportModal = document.getElementById('reportModal');
                if (reportModal && reportModal.style.display === 'block') {
                    closeReportModal();
                }
            }
        });
        
        console.log('✅ Reports section enhancements initialized successfully');
    }

    function debouncedReportsSearch() {
        clearTimeout(reportsSearchTimeout);
        reportsSearchTimeout = setTimeout(() => {
            reportsCurrentPage = 1;
            performReportsSearch();
        }, 300);
    }

    function debouncedSecurityAlertsSearch() {
        clearTimeout(securityAlertsSearchTimeout);
        securityAlertsSearchTimeout = setTimeout(() => {
            securityAlertsCurrentPage = 1;
            performSecurityAlertsSearch();
        }, 300);
    }

    function debouncedUserFeedbackSearch() {
        clearTimeout(userFeedbackSearchTimeout);
        userFeedbackSearchTimeout = setTimeout(() => {
            userFeedbackCurrentPage = 1;
            performUserFeedbackSearch();
        }, 300);
    }

    function performReportsSearch() {
        const form = document.getElementById('reports-filter-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        reportsCurrentFilters = {
            search: formData.get('search') || '',
            type: formData.get('type') || '',
            status: formData.get('status') || '',
            priority: formData.get('priority') || '',
            sort_by: reportsCurrentSort.field,
            sort_order: reportsCurrentSort.order,
            page: reportsCurrentPage,
            per_page: reportsPerPage
        };
        
        loadReportsData();
    }

    async function loadReportsData() {
        setReportsLoading(true);
        
        try {
            // For now, implement client-side filtering since we don't have API endpoints
            // In production, this would call: const data = await AdminEnhancements.fetchData('reports', reportsCurrentFilters);
            performClientSideReportsFiltering();
        } catch (error) {
            console.error('Error loading reports:', error);
            if (typeof AdminEnhancements !== 'undefined' && AdminEnhancements.showToast) {
                AdminEnhancements.showToast('Error loading reports: ' + error.message, 'error');
            }
        } finally {
            setReportsLoading(false);
        }
    }

    function performClientSideReportsFiltering() {
        const table = document.getElementById('reports-table');
        if (!table) return;
        
        const rows = Array.from(table.querySelectorAll('tbody tr:not(.no-results)'));
        let filteredRows = rows;
        
        // Apply search filter
        if (reportsCurrentFilters.search) {
            const searchTerm = reportsCurrentFilters.search.toLowerCase();
            filteredRows = filteredRows.filter(row => {
                const text = row.textContent.toLowerCase();
                return text.includes(searchTerm);
            });
        }
        
        // Apply type filter
        if (reportsCurrentFilters.type) {
            filteredRows = filteredRows.filter(row => {
                const typeCell = row.cells[2]; // Type is in 3rd column
                return typeCell.textContent.toLowerCase().includes(reportsCurrentFilters.type);
            });
        }
        
        // Apply status filter
        if (reportsCurrentFilters.status) {
            filteredRows = filteredRows.filter(row => {
                const statusCell = row.cells[5]; // Status is in 6th column
                return statusCell.textContent.toLowerCase().includes(reportsCurrentFilters.status);
            });
        }
        
        // Apply priority filter
        if (reportsCurrentFilters.priority) {
            filteredRows = filteredRows.filter(row => {
                const priorityCell = row.cells[1]; // Priority is in 2nd column
                return priorityCell.textContent.toLowerCase().includes(reportsCurrentFilters.priority);
            });
        }
        
        // Show/hide rows based on filters
        rows.forEach(row => row.style.display = 'none');
        filteredRows.forEach(row => row.style.display = '');
        
        // Update results info
        const totalRows = rows.length;
        updateReportsResultsInfo(filteredRows.length, totalRows);
        
        // Update status cards to reflect filtered data
        updateStatusCards();
    }

    function updateReportsResultsInfo(filtered, total) {
        const infoDiv = document.getElementById('reports-results-info');
        if (!infoDiv) return;
        
        if (filtered < total) {
            infoDiv.innerHTML = `Showing ${filtered} of ${total} reports`;
            infoDiv.style.display = 'block';
        } else {
            infoDiv.style.display = 'none';
        }
    }

    function updateReportsTable(data) {
        const tbody = document.querySelector('#reports-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (data.reports && data.reports.length > 0) {
            data.reports.forEach(report => {
                const row = createReportRow(report);
                tbody.appendChild(row);
            });
        } else {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = '<td colspan="9" style="text-align: center; color: #999; font-style: italic;">No reports found</td>';
            tbody.appendChild(emptyRow);
        }
    }

    function createReportRow(report) {
        const row = document.createElement('tr');
        row.className = report.priority === 'critical' ? 'table-danger' : (report.priority === 'high' ? 'table-warning' : '');
        
        const priorityBadge = getPriorityBadge(report.priority);
        const statusBadge = getStatusBadge(report.status);
        const typeBadge = `<span class="btn btn-secondary btn-small" style="cursor: default;">${report.report_type}</span>`;
        
        row.innerHTML = `
            <td>#${report.id}</td>
            <td>${priorityBadge}</td>
            <td>${typeBadge}</td>
            <td><strong>${truncateText(report.title, 50)}</strong></td>
            <td>${report.reported_by ? report.reported_by.username : '<em>System</em>'}</td>
            <td>${statusBadge}</td>
            <td>${formatDate(report.created_at)}</td>
            <td>${report.assigned_to ? report.assigned_to.username : '<em>Unassigned</em>'}</td>
            <td>
                <a href="/admin/reports/${report.id}" class="btn btn-small">👁️ View</a>
                ${report.status === 'new' && !report.assigned_to ? 
                    `<button onclick="assignReportAjax(${report.id})" class="btn btn-warning btn-small">👤 Assign</button>` : ''}
            </td>
        `;
        
        return row;
    }

    function getPriorityBadge(priority) {
        const badges = {
            'critical': '<span class="btn btn-danger btn-small" style="cursor: default;">CRITICAL</span>',
            'high': '<span class="btn btn-warning btn-small" style="cursor: default;">HIGH</span>',
            'medium': '<span class="btn btn-secondary btn-small" style="cursor: default;">MEDIUM</span>',
            'low': '<span class="btn btn-secondary btn-small" style="cursor: default;">LOW</span>'
        };
        return badges[priority] || badges.low;
    }

    function getStatusBadge(status) {
        const badges = {
            'new': '<span class="btn btn-secondary btn-small" style="cursor: default;">NEW</span>',
            'in_progress': '<span class="btn btn-warning btn-small" style="cursor: default;">IN PROGRESS</span>',
            'resolved': '<span class="btn btn-success btn-small" style="cursor: default;">RESOLVED</span>'
        };
        return badges[status] || `<span class="btn btn-secondary btn-small" style="cursor: default;">${status.toUpperCase()}</span>`;
    }

    function updateReportsPagination(pagination) {
        const container = document.getElementById('reports-pagination');
        if (!container || !pagination) return;
        
        let html = '<div class="pagination">';
        
        // Previous button
        if (pagination.has_prev) {
            html += `<button class="page-btn" onclick="goToReportsPage(${pagination.prev_num})">← Previous</button>`;
        } else {
            html += '<button class="page-btn" disabled>← Previous</button>';
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        if (startPage > 1) {
            html += '<button class="page-btn" onclick="goToReportsPage(1)">1</button>';
            if (startPage > 2) html += '<span class="page-btn" disabled>...</span>';
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            html += `<button class="page-btn ${activeClass}" onclick="goToReportsPage(${i})">${i}</button>`;
        }
        
        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) html += '<span class="page-btn" disabled>...</span>';
            html += `<button class="page-btn" onclick="goToReportsPage(${pagination.pages})">${pagination.pages}</button>`;
        }
        
        // Next button
        if (pagination.has_next) {
            html += `<button class="page-btn" onclick="goToReportsPage(${pagination.next_num})">Next →</button>`;
        } else {
            html += '<button class="page-btn" disabled>Next →</button>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    function goToReportsPage(page) {
        currentPage = page;
        performReportsSearch();
    }

    function updateResultsInfo(pagination) {
        const infoDiv = document.getElementById('reports-results-info');
        if (!infoDiv || !pagination) return;
        
        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total);
        
        infoDiv.innerHTML = `Showing ${start}-${end} of ${pagination.total} reports`;
    }

    function updateSortIndicators() {
        document.querySelectorAll('#reports-table .sort-indicator').forEach(indicator => {
            indicator.className = 'sort-indicator';
        });
        
        const activeHeader = document.querySelector(`#reports-table [data-field="${reportsCurrentSort.field}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.className = `sort-indicator ${reportsCurrentSort.order}`;
        }
    }

    function clearReportsFilters() {
        const form = document.getElementById('reports-filter-form');
        if (form) form.reset();
        
        reportsCurrentFilters = {};
        reportsCurrentSort = { field: 'created_at', order: 'desc' };
        reportsCurrentPage = 1;
        reportsPerPage = 20;
        updateSortIndicators();
        
        // Show all rows
        const table = document.getElementById('reports-table');
        if (table) {
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            rows.forEach(row => row.style.display = '');
        }
        
        // Hide results info
        const infoDiv = document.getElementById('reports-results-info');
        if (infoDiv) infoDiv.style.display = 'none';
        
        // Update status cards to reflect all data
        updateStatusCards();
    }

    function setReportsLoading(loading) {
        const indicator = document.getElementById('reports-loading');
        const table = document.getElementById('reports-table');
        
        if (indicator) {
            indicator.style.display = loading ? 'inline' : 'none';
        }
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }

    // Navigation Functions
    function openReportModal(reportId) {
        // Redirect to the HTML view instead of opening a modal
        window.location.href = `/admin/reports/${reportId}`;
    }

    function displayReportDetails(report) {
        const body = document.getElementById('reportModalBody');
        const title = document.getElementById('reportModalTitle');
        
        title.textContent = `Report #${report.id} - ${report.title}`;
        
        body.innerHTML = `
            <div class="report-details">
                <div class="detail-section">
                    <h4>Basic Information</h4>
                    <p><strong>Type:</strong> ${report.report_type}</p>
                    <p><strong>Priority:</strong> ${report.priority}</p>
                    <p><strong>Status:</strong> ${report.status}</p>
                    <p><strong>Created:</strong> ${formatDate(report.created_at)}</p>
                </div>
                
                <div class="detail-section">
                    <h4>People</h4>
                    <p><strong>Reported By:</strong> ${report.reported_by ? report.reported_by.username : 'System'}</p>
                    <p><strong>Assigned To:</strong> ${report.assigned_to ? report.assigned_to.username : 'Unassigned'}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Description</h4>
                    <p>${report.description || 'No description provided'}</p>
                </div>
                
                ${report.additional_info ? `
                <div class="detail-section">
                    <h4>Additional Information</h4>
                    <pre>${report.additional_info}</pre>
                </div>
                ` : ''}
            </div>
        `;
    }

    function closeReportModal() {
        document.getElementById('reportModal').style.display = 'none';
        currentReportId = null;
    }

    async function assignReportAjax(reportId) {
        try {
            const response = await fetch(`/admin/api/reports/${reportId}/assign`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to assign report');
            
            AdminEnhancements.showToast('Report assigned successfully', 'success');
            loadReportsData();
            
            if (currentReportId === reportId) {
                openReportModal(reportId); // Refresh modal
            }
        } catch (error) {
            AdminEnhancements.showToast('Error assigning report: ' + error.message, 'error');
        }
    }

    async function assignCurrentReport() {
        if (currentReportId) {
            await assignReportAjax(currentReportId);
        }
    }

    async function resolveCurrentReport() {
        if (!currentReportId) return;
        
        try {
            const response = await fetch(`/admin/api/reports/${currentReportId}/resolve`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to resolve report');
            
            AdminEnhancements.showToast('Report resolved successfully', 'success');
            closeReportModal();
            loadReportsData();
        } catch (error) {
            AdminEnhancements.showToast('Error resolving report: ' + error.message, 'error');
        }
    }

    // Security Alerts table functions
    function performSecurityAlertsSearch() {
        const form = document.getElementById('security-alerts-filter-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        securityAlertsCurrentFilters = {
            search: formData.get('search') || '',
            type: formData.get('type') || '',
            user: formData.get('user') || ''
        };
        
        loadSecurityAlertsData();
    }

    function loadSecurityAlertsData() {
        setSecurityAlertsLoading(true);
        
        try {
            // Client-side filtering of existing table data
            const table = document.getElementById('security-alerts-table');
            if (!table) return;
            
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            let filteredRows = rows;
            
            // Apply search filter
            if (securityAlertsCurrentFilters.search) {
                const searchTerm = securityAlertsCurrentFilters.search.toLowerCase();
                filteredRows = filteredRows.filter(row => {
                    const text = row.textContent.toLowerCase();
                    return text.includes(searchTerm);
                });
            }
            
            // Apply type filter
            if (securityAlertsCurrentFilters.type) {
                filteredRows = filteredRows.filter(row => {
                    const typeCell = row.cells[1];
                    return typeCell.textContent.toLowerCase().includes(securityAlertsCurrentFilters.type);
                });
            }
            
            // Show/hide rows based on filters
            rows.forEach(row => row.style.display = 'none');
            filteredRows.forEach(row => row.style.display = '');
            
            // Update results info
            const totalRows = rows.length;
            updateSecurityAlertsResultsInfo(filteredRows.length, totalRows);
            
        } catch (error) {
            console.error('Error filtering security alerts:', error);
        } finally {
            setSecurityAlertsLoading(false);
        }
    }

    function updateSecurityAlertsResultsInfo(filtered, total) {
        const infoDiv = document.getElementById('security-alerts-results-info');
        if (!infoDiv) return;
        
        if (filtered < total) {
            infoDiv.innerHTML = `Showing ${filtered} of ${total} security alerts`;
            infoDiv.style.display = 'block';
        } else {
            infoDiv.style.display = 'none';
        }
    }

    function updateSecurityAlertsSortIndicators() {
        document.querySelectorAll('#security-alerts-table .sort-indicator').forEach(indicator => {
            indicator.className = 'sort-indicator';
        });
        
        const activeHeader = document.querySelector(`#security-alerts-table [data-field="${securityAlertsCurrentSort.field}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.className = `sort-indicator ${securityAlertsCurrentSort.order}`;
        }
    }

    function clearSecurityAlertsFilters() {
        const form = document.getElementById('security-alerts-filter-form');
        if (form) form.reset();
        
        securityAlertsCurrentFilters = {};
        securityAlertsCurrentSort = { field: 'created_at', order: 'desc' };
        
        // Show all rows
        const table = document.getElementById('security-alerts-table');
        if (table) {
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            rows.forEach(row => row.style.display = '');
        }
        
        // Hide results info
        const infoDiv = document.getElementById('security-alerts-results-info');
        if (infoDiv) infoDiv.style.display = 'none';
    }

    function setSecurityAlertsLoading(loading) {
        const indicator = document.getElementById('security-alerts-loading');
        const table = document.getElementById('security-alerts-table');
        
        if (indicator) {
            indicator.style.display = loading ? 'inline' : 'none';
        }
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }

    // User Feedback table functions
    function performUserFeedbackSearch() {
        const form = document.getElementById('user-feedback-filter-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        userFeedbackCurrentFilters = {
            search: formData.get('search') || '',
            type: formData.get('type') || ''
        };
        
        loadUserFeedbackData();
    }

    function loadUserFeedbackData() {
        setUserFeedbackLoading(true);
        
        try {
            // Client-side filtering of existing table data
            const table = document.getElementById('user-feedback-table');
            if (!table) return;
            
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            let filteredRows = rows;
            
            // Apply search filter
            if (userFeedbackCurrentFilters.search) {
                const searchTerm = userFeedbackCurrentFilters.search.toLowerCase();
                filteredRows = filteredRows.filter(row => {
                    const text = row.textContent.toLowerCase();
                    return text.includes(searchTerm);
                });
            }
            
            // Apply type filter
            if (userFeedbackCurrentFilters.type) {
                filteredRows = filteredRows.filter(row => {
                    const typeCell = row.cells[1];
                    return typeCell.textContent.toLowerCase().includes(userFeedbackCurrentFilters.type);
                });
            }
            
            // Show/hide rows based on filters
            rows.forEach(row => row.style.display = 'none');
            filteredRows.forEach(row => row.style.display = '');
            
            // Update results info
            const totalRows = rows.length;
            updateUserFeedbackResultsInfo(filteredRows.length, totalRows);
            
        } catch (error) {
            console.error('Error filtering user feedback:', error);
        } finally {
            setUserFeedbackLoading(false);
        }
    }

    function updateUserFeedbackResultsInfo(filtered, total) {
        const infoDiv = document.getElementById('user-feedback-results-info');
        if (!infoDiv) return;
        
        if (filtered < total) {
            infoDiv.innerHTML = `Showing ${filtered} of ${total} feedback entries`;
            infoDiv.style.display = 'block';
        } else {
            infoDiv.style.display = 'none';
        }
    }

    function updateUserFeedbackSortIndicators() {
        document.querySelectorAll('#user-feedback-table .sort-indicator').forEach(indicator => {
            indicator.className = 'sort-indicator';
        });
        
        const activeHeader = document.querySelector(`#user-feedback-table [data-field="${userFeedbackCurrentSort.field}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.className = `sort-indicator ${userFeedbackCurrentSort.order}`;
        }
    }

    function clearUserFeedbackFilters() {
        const form = document.getElementById('user-feedback-filter-form');
        if (form) form.reset();
        
        userFeedbackCurrentFilters = {};
        userFeedbackCurrentSort = { field: 'created_at', order: 'desc' };
        
        // Show all rows
        const table = document.getElementById('user-feedback-table');
        if (table) {
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            rows.forEach(row => row.style.display = '');
        }
        
        // Hide results info
        const infoDiv = document.getElementById('user-feedback-results-info');
        if (infoDiv) infoDiv.style.display = 'none';
    }

    function setUserFeedbackLoading(loading) {
        const indicator = document.getElementById('user-feedback-loading');
        const table = document.getElementById('user-feedback-table');
        
        if (indicator) {
            indicator.style.display = loading ? 'inline' : 'none';
        }
        if (table) {
            table.style.opacity = loading ? '0.6' : '1';
        }
    }
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Click outside modal to close
    window.onclick = function(event) {
        const modal = document.getElementById('reportModal');
        if (event.target === modal) {
            closeReportModal();
        }
    }

    // ============================================================================
    // REPORT ASSIGNMENT FUNCTIONALITY
    // ============================================================================

    async function assignReportAjax(reportId) {
        console.log(`Assigning report ${reportId} to current user`);
        
        const confirmed = confirm(`Are you sure you want to assign report #${reportId} to yourself?`);
        if (!confirmed) return;
        
        try {
            setReportsLoading(true);
            
            const response = await fetch(`/admin/api/reports/${reportId}/assign`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                alert(`Report ${reportId} assigned! - This would make an API call`);
                
                // Redirect to the HTML view of the report after assignment
                setTimeout(() => {
                    window.location.href = `/admin/reports/${reportId}`;
                }, 1000);
                
            } else {
                alert(`❌ Error: ${result.error || 'Failed to assign report'}`);
            }
            
        } catch (error) {
            console.error('Error assigning report:', error);
            alert(`❌ Network error: ${error.message}`);
        } finally {
            setReportsLoading(false);
        }
    }

    function updateReportRowAssignment(reportId) {
        console.log(`Updating report row assignment for report ${reportId}`);
        
        // Find the report row
        const table = document.getElementById('reports-table');
        if (!table) {
            console.error('Reports table not found!');
            return;
        }
        
        const rows = table.querySelectorAll('tbody tr');
        let targetRow = null;
        
        rows.forEach(row => {
            const idCell = row.querySelector('td:first-child'); // First column should be ID
            if (idCell && idCell.textContent.includes(reportId.toString())) {
                targetRow = row;
            }
        });
        
        if (!targetRow) {
            console.error(`Report row with ID ${reportId} not found!`);
            return;
        }
        
        // Update the status column (index 5)
        const statusCell = targetRow.cells[5];
        if (statusCell) {
            statusCell.innerHTML = '<span class="btn btn-warning btn-small" style="cursor: default;">IN PROGRESS</span>';
        }
        
        // Update the assigned to column (index 7)
        const assignedCell = targetRow.cells[7];
        if (assignedCell) {
            assignedCell.innerHTML = 'You'; // Could be enhanced with actual username
        }
        
        // Update the actions column (index 8) - remove assign button
        const actionsCell = targetRow.cells[8];
        if (actionsCell) {
            // Keep only the View button
            const viewButton = actionsCell.querySelector('a');
            if (viewButton) {
                actionsCell.innerHTML = viewButton.outerHTML;
            }
        }
        
        console.log(`Successfully updated report row for report ${reportId}`);
    }

    function updateStatusCards() {
        // Update the status cards to reflect current visible data
        const table = document.getElementById('reports-table');
        if (!table) return;
        
        const visibleRows = Array.from(table.querySelectorAll('tbody tr')).filter(row => row.style.display !== 'none');
        
        let newCount = 0;
        let inProgressCount = 0;
        let highPriorityCount = 0;
        let totalCount = visibleRows.length;
        
        visibleRows.forEach(row => {
            const statusCell = row.cells[5];
            const priorityCell = row.cells[1];
            
            if (statusCell) {
                const statusText = statusCell.textContent.toLowerCase();
                if (statusText.includes('new')) {
                    newCount++;
                } else if (statusText.includes('in progress')) {
                    inProgressCount++;
                }
            }
            
            if (priorityCell && (priorityCell.textContent.includes('HIGH') || priorityCell.textContent.includes('CRITICAL'))) {
                highPriorityCount++;
            }
        });
        
        // Update the stat cards
        const statCards = document.querySelectorAll('.stat-card h3');
        if (statCards.length >= 4) {
            statCards[0].textContent = totalCount; // Total Reports
            statCards[1].textContent = newCount; // New Reports  
            statCards[2].textContent = inProgressCount; // In Progress
            statCards[3].textContent = highPriorityCount; // High Priority
        }
        
        console.log(`Updated status cards: Total=${totalCount}, New=${newCount}, InProgress=${inProgressCount}, HighPriority=${highPriorityCount}`);
    }

    // Make the function globally available
    window.assignReportAjax = assignReportAjax;
    window.updateStatusCards = updateStatusCards;
    window.openReportModal = openReportModal;
    window.viewReport = function(reportId) {
        window.location.href = `/admin/reports/${reportId}`;
    };
    window.assignReport = function(reportId) {
        if (confirm(`Assign report ${reportId} to yourself?`)) {
            assignReportAjax(reportId);
        }
    };

    // Initialize status cards update when filters change
    document.addEventListener('DOMContentLoaded', function() {
        // Update status cards on initial load
        setTimeout(updateStatusCards, 500);
        
        // Override the performReportsSearch function to include status card updates
        const originalPerformReportsSearch = window.performReportsSearch;
        if (originalPerformReportsSearch) {
            window.performReportsSearch = function() {
                originalPerformReportsSearch();
                setTimeout(updateStatusCards, 100); // Small delay to ensure DOM is updated
            };
        }
        
        // Also update status cards when clear filters is called
        const originalClearReportsFilters = window.clearReportsFilters;
        if (originalClearReportsFilters) {
            window.clearReportsFilters = function() {
                originalClearReportsFilters();
                setTimeout(updateStatusCards, 100);
            };
        }
    });
})();