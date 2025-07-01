/**
 * Admin Reports & Security JavaScript
 * Enhanced reports management functionality with AJAX, real-time alerts, and advanced filtering
 */

(function() {
    'use strict';

    // Check if we're on a page with the reports section
    if (!document.getElementById('reportsSection')) {
        console.log('[Reports] Section not found, skipping initialization');
        return; // Exit early if not on reports page
    }

    console.log('[Reports] Initializing reports section JavaScript');

    // Reports management state
    let reportsCurrentPage = 1;
    let reportsPerPage = 20;
    let reportsSortBy = 'created_at';
    let reportsSortOrder = 'desc';
    let reportsSearchTimeout;
    let currentReportAction = null;

    // Initialize Reports Section
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('reportsSection')) {
            initializeReportsSection();
        }
    });

    function initializeReportsSection() {
        // Load initial data
        performReportsSearch();
        
        // Start real-time security alerts
        refreshSecurityAlerts();
        
        // Set up periodic refresh for security alerts (every 30 seconds)
        setInterval(refreshSecurityAlerts, 30000);
        
        // Initialize sort indicators
        updateReportsSortIndicators();
        
        console.log('[Reports] Section initialized');
    }

    // AJAX Functions
    function performReportsSearch(resetPage = false) {
        if (resetPage) {
            reportsCurrentPage = 1;
        }
        
        const searchQuery = document.getElementById('reportsSearchInput')?.value || '';
        const typeFilter = document.getElementById('typeFilter')?.value || '';
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        const priorityFilter = document.getElementById('priorityFilter')?.value || '';
        
        // Show loading
        setReportsLoading(true);
        
        const params = new URLSearchParams({
            search: searchQuery,
            type: typeFilter,
            status: statusFilter,
            priority: priorityFilter,
            page: reportsCurrentPage,
            per_page: reportsPerPage,
            sort_by: reportsSortBy,
            sort_order: reportsSortOrder
        });
        
        AdminUtils.makeAjaxRequest(`/admin/api/reports?${params}`)
            .then(data => {
                if (data.success) {
                    updateReportsTable(data.reports);
                    updateReportsPagination(data.pagination);
                    updateReportsStats(data.stats);
                    updateReportsResultsCounter(data.pagination);
                } else {
                    AdminUtils.showToast('Error loading reports: ' + data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Reports search error:', error);
                AdminUtils.showToast('Failed to load reports', 'error');
            })
            .finally(() => {
                setReportsLoading(false);
            });
    }

    function debouncedReportsSearch() {
        clearTimeout(reportsSearchTimeout);
        reportsSearchTimeout = setTimeout(() => performReportsSearch(true), 300);
    }

    function refreshSecurityAlerts() {
        AdminUtils.makeAjaxRequest('/admin/api/security-alerts')
            .then(data => {
                if (data.success) {
                    updateSecurityAlerts(data.alerts, data.critical_count);
                }
            })
            .catch(error => {
                console.error('Security alerts error:', error);
            });
    }

    function updateReportStatus(reportId, action, additionalData = {}) {
        const requestData = {
            action: action,
            ...additionalData
        };
        
        setReportsLoading(true);
        
        AdminUtils.makeAjaxRequest(`/admin/api/report/update-status/${reportId}`, {
            method: 'POST',
            body: JSON.stringify(requestData)
        })
        .then(data => {
            if (data.success) {
                AdminUtils.showToast(data.message, 'success');
                // Refresh the reports table
                performReportsSearch();
                closeReportActionModal();
            } else {
                AdminUtils.showToast('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Update status error:', error);
            AdminUtils.showToast('Failed to update report status', 'error');
        })
        .finally(() => {
            setReportsLoading(false);
        });
    }

    // UI Update Functions
    function updateReportsTable(reports) {
        const tbody = document.getElementById('reportsTableBody');
        if (!tbody) return;
        
        if (reports.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; color: #999; font-style: italic; padding: 40px;">
                        No reports found matching your criteria
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = reports.map(report => {
            const priorityClass = `priority-${report.priority}`;
            const statusClass = `status-${report.status}`;
            const rowClass = report.priority === 'critical' ? 'table-danger' : 
                            report.priority === 'high' ? 'table-warning' : '';
            
            return `
                <tr class="${rowClass}" data-report-id="${report.id}">
                    <td>#${report.id}</td>
                    <td>
                        <span class="${priorityClass}">${report.priority.toUpperCase()}</span>
                    </td>
                    <td>
                        <span class="btn btn-secondary btn-small" style="cursor: default;">${report.report_type}</span>
                    </td>
                    <td>
                        <strong onclick="viewReportDetails(${report.id})" style="cursor: pointer; color: #007bff;">
                            ${report.title.length > 50 ? report.title.substring(0, 50) + '...' : report.title}
                        </strong>
                    </td>
                    <td>${report.reported_by}</td>
                    <td>
                        <span class="${statusClass}">${report.status.replace('_', ' ').toUpperCase()}</span>
                    </td>
                    <td>
                        <small>${new Date(report.created_at).toLocaleDateString()} ${new Date(report.created_at).toLocaleTimeString()}</small>
                    </td>
                    <td>${report.assigned_to || '<em>Unassigned</em>'}</td>
                    <td>
                        <button onclick="viewReportDetails(${report.id})" class="action-btn action-view" title="View details">
                            👁️
                        </button>
                        ${generateReportActionButtons(report)}
                    </td>
                </tr>
            `;
        }).join('');
    }

    function generateReportActionButtons(report) {
        let buttons = '';
        
        if (report.status === 'new' && !report.assigned_to) {
            buttons += `
                <button onclick="quickAssignReport(${report.id})" class="action-btn action-assign" title="Assign to me">
                    👤
                </button>
            `;
        }
        
        if (report.status === 'in_progress') {
            buttons += `
                <button onclick="quickResolveReport(${report.id})" class="action-btn action-resolve" title="Mark as resolved">
                    ✅
                </button>
            `;
        }
        
        if (report.status === 'resolved') {
            buttons += `
                <button onclick="quickArchiveReport(${report.id})" class="action-btn action-archive" title="Archive report">
                    📦
                </button>
            `;
        }
        
        return buttons;
    }

    function updateSecurityAlerts(alerts, criticalCount) {
        const alertsPanel = document.getElementById('liveAlertsPanel');
        const criticalBanner = document.getElementById('criticalAlertBanner');
        const alertsList = document.getElementById('alertsList');
        const alertsCounter = document.getElementById('alertsCounter');
        const criticalCountSpan = document.getElementById('criticalCount');
        
        // Update critical banner
        if (criticalBanner && criticalCountSpan) {
            if (criticalCount > 0) {
                criticalBanner.style.display = 'block';
                criticalCountSpan.textContent = criticalCount;
            } else {
                criticalBanner.style.display = 'none';
            }
        }
        
        // Update alerts panel
        if (alertsPanel && alertsList && alertsCounter) {
            if (alerts.length > 0) {
                alertsPanel.style.display = 'block';
                alertsCounter.textContent = alerts.length;
                
                alertsList.innerHTML = alerts.map(alert => {
                    const alertClass = alert.priority === 'critical' ? 'alert-critical' : 
                                      alert.priority === 'high' ? 'alert-high' : 'live-alert';
                    
                    return `
                        <div class="live-alert ${alertClass}" onclick="viewReportDetails(${alert.id})" style="cursor: pointer;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${alert.title}</strong>
                                    ${alert.affected_user ? ` (${alert.affected_user})` : ''}
                                </div>
                                <div style="font-size: 12px; color: #666;">
                                    ${alert.created_at}
                                </div>
                            </div>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                ${alert.description}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                alertsPanel.style.display = 'none';
            }
        }
    }

    function updateReportsStats(stats) {
        const totalReportsCount = document.getElementById('totalReportsCount');
        const newReportsCount = document.getElementById('newReportsCount');
        const progressReportsCount = document.getElementById('progressReportsCount');
        const criticalReportsCount = document.getElementById('criticalReportsCount');
        
        if (totalReportsCount) totalReportsCount.textContent = stats.total;
        if (newReportsCount) newReportsCount.textContent = stats.new;
        if (progressReportsCount) progressReportsCount.textContent = stats.in_progress;
        if (criticalReportsCount) criticalReportsCount.textContent = stats.critical + stats.high;
    }

    function updateReportsPagination(pagination) {
        const container = document.getElementById('reportsPaginationContainer');
        const controls = document.getElementById('reportsPaginationControls');
        const info = document.getElementById('reportsPaginationInfo');
        
        if (!container) return;
        
        if (pagination.pages <= 1) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        
        // Generate pagination buttons
        let buttons = '';
        
        // Previous button
        if (pagination.has_prev) {
            buttons += `<button onclick="goToReportsPage(${pagination.prev_num})" class="btn btn-secondary btn-small">← Previous</button>`;
        }
        
        // Page numbers with smart ellipsis
        const pages = AdminUtils.generatePageNumbers(pagination.page, pagination.pages);
        pages.forEach(page => {
            if (page === '...') {
                buttons += `<span class="btn btn-secondary btn-small" style="cursor: default;">...</span>`;
            } else if (page === pagination.page) {
                buttons += `<button class="btn btn-primary btn-small" style="cursor: default;">${page}</button>`;
            } else {
                buttons += `<button onclick="goToReportsPage(${page})" class="btn btn-secondary btn-small">${page}</button>`;
            }
        });
        
        // Next button
        if (pagination.has_next) {
            buttons += `<button onclick="goToReportsPage(${pagination.next_num})" class="btn btn-secondary btn-small">Next →</button>`;
        }
        
        if (controls) controls.innerHTML = buttons;
        
        // Update pagination info
        if (info) {
            const start = ((pagination.page - 1) * pagination.per_page) + 1;
            const end = Math.min(pagination.page * pagination.per_page, pagination.total);
            info.textContent = `Showing ${start}-${end} of ${pagination.total} reports`;
        }
    }

    function updateReportsResultsCounter(pagination) {
        const counter = document.getElementById('reportsResultsCounter');
        const filteredCount = document.getElementById('filteredCount');
        const totalCount = document.getElementById('totalCount');
        
        if (filteredCount) filteredCount.textContent = pagination.total;
        if (totalCount) totalCount.textContent = pagination.total;
        
        if (counter) {
            if (pagination.total > 0) {
                counter.style.display = 'block';
            } else {
                counter.style.display = 'none';
            }
        }
    }

    // Modal and Action Functions
    function viewReportDetails(reportId) {
        // Open report in new tab for now
        window.open(`/admin/reports/${reportId}`, '_blank');
    }

    // Quick Action Functions
    function quickAssignReport(reportId) {
        updateReportStatus(reportId, 'assign');
    }

    function quickResolveReport(reportId) {
        if (confirm('Are you sure you want to mark this report as resolved?')) {
            updateReportStatus(reportId, 'resolve');
        }
    }

    function quickArchiveReport(reportId) {
        if (confirm('Are you sure you want to archive this report?')) {
            updateReportStatus(reportId, 'archive');
        }
    }

    // Pagination Functions
    function goToReportsPage(page) {
        reportsCurrentPage = page;
        performReportsSearch();
    }

    // Sorting Functions
    function toggleReportsSort(column) {
        if (reportsSortBy === column) {
            reportsSortOrder = reportsSortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            reportsSortBy = column;
            reportsSortOrder = 'desc';
        }
        
        updateReportsSortIndicators();
        performReportsSearch(true);
    }

    function updateReportsSortIndicators() {
        AdminUtils.updateSortIndicators(reportsSortBy, reportsSortOrder, '#reportsSection .sortable');
    }

    // Modal Functions
    function openReportActionModal(reportId, action, title, content) {
        currentReportAction = { reportId, action };
        
        const actionModal = document.getElementById('reportActionModal');
        const actionModalTitle = document.getElementById('actionModalTitle');
        const actionModalContent = document.getElementById('actionModalContent');
        const actionExecuteBtn = document.getElementById('actionExecuteBtn');
        
        if (actionModalTitle) actionModalTitle.textContent = title;
        if (actionModalContent) actionModalContent.innerHTML = content;
        if (actionExecuteBtn) actionExecuteBtn.textContent = 'Execute';
        if (actionModal) actionModal.style.display = 'block';
    }

    function closeReportActionModal() {
        const actionModal = document.getElementById('reportActionModal');
        if (actionModal) actionModal.style.display = 'none';
        currentReportAction = null;
    }

    // Utility Functions
    function setReportsLoading(loading) {
        const loadingDiv = document.getElementById('reportsTableLoading');
        const filterLoading = document.getElementById('reportsFilterLoading');
        
        if (loadingDiv) {
            loadingDiv.style.display = loading ? 'flex' : 'none';
        }
        if (filterLoading) {
            filterLoading.style.display = loading ? 'block' : 'none';
        }
    }

    // Make functions available globally for onclick handlers
    window.viewReportDetails = viewReportDetails;
    window.quickAssignReport = quickAssignReport;
    window.quickResolveReport = quickResolveReport;
    window.quickArchiveReport = quickArchiveReport;
    window.goToReportsPage = goToReportsPage;
    window.toggleReportsSort = toggleReportsSort;

    console.log('[Reports] Enhanced JavaScript loaded successfully');

})(); // End of IIFE - this was the missing closing brace causing the syntax error
