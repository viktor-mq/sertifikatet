// static/js/admin/admin-audit-log.js

(function(window) {
    'use strict';

    let currentAuditFilters = {};
    let currentAuditSort = { field: 'created_at', order: 'desc' };
    let currentAuditPage = 1;
    let auditPerPage = 50;
    let auditSearchTimeout;
    let columnVisibility = {};

    function initialize() {
        if (window.auditInitialized) return;
        console.log('🔧 Initializing Audit Log enhancements...');

        const searchInput = document.getElementById('audit-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(auditSearchTimeout);
                auditSearchTimeout = setTimeout(() => {
                    currentAuditPage = 1;
                    performAuditSearch();
                }, 300);
            });
        }

        document.querySelectorAll('#audit-filter-form select').forEach(element => {
            element.addEventListener('change', () => {
                currentAuditPage = 1;
                performAuditSearch();
            });
        });

        document.querySelectorAll('#audit-table .sortable').forEach(header => {
            header.addEventListener('click', function() {
                const field = this.dataset.field;
                if (currentAuditSort.field === field) {
                    currentAuditSort.order = currentAuditSort.order === 'asc' ? 'desc' : 'asc';
                } else {
                    currentAuditSort.field = field;
                    currentAuditSort.order = 'asc';
                }
                currentAuditPage = 1;
                performAuditSearch();
            });
        });

        // Table view controls
        document.querySelectorAll('#view-mode-menu a').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const view = this.dataset.view;
                document.getElementById('audit-table').className = 'view-' + view;
                document.querySelector('#view-mode-menu a.active').classList.remove('active');
                this.classList.add('active');
                document.getElementById('view-mode-btn').textContent = this.textContent;
                localStorage.setItem('auditLog_viewMode', view);
            });
        });

        // Column visibility controls
        initializeColumnToggles();

        // Load saved preferences
        loadPreferences();

        performAuditSearch(); // Initial data load
        window.auditInitialized = true;
        console.log('✅ Audit Log enhancements initialized.');
    }

    function initializeColumnToggles() {
        const menu = document.getElementById('column-toggle-menu');
        const headers = document.querySelectorAll('#audit-table th');
        headers.forEach((header, index) => {
            const field = header.dataset.field || `col_${index}`;
            const text = header.textContent.replace('↑', '').replace('↓', '').trim();
            if (!text) return;

            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `<input type="checkbox" id="col-toggle-${field}" data-index="${index}" checked> <label for="col-toggle-${field}">${text}</label>`;
            menu.appendChild(item);

            item.querySelector('input').addEventListener('change', function() {
                const isChecked = this.checked;
                const colIndex = this.dataset.index;
                const table = document.getElementById('audit-table');
                table.querySelectorAll(`tr`).forEach(row => {
                    row.cells[colIndex].style.display = isChecked ? '' : 'none';
                });
                columnVisibility[field] = isChecked;
                localStorage.setItem('auditLog_columnVisibility', JSON.stringify(columnVisibility));
            });
        });
    }

    function loadPreferences() {
        // Load view mode
        const savedView = localStorage.getItem('auditLog_viewMode') || 'comfortable';
        document.getElementById('audit-table').className = 'view-' + savedView;
        const activeButton = document.querySelector(`#view-mode-menu a[data-view="${savedView}"]`);
        if (activeButton) {
            document.querySelectorAll('#view-mode-menu a').forEach(link => link.classList.remove('active'));
            activeButton.classList.add('active');
            document.getElementById('view-mode-btn').textContent = activeButton.textContent;
        }

        // Load column visibility
        const savedCols = JSON.parse(localStorage.getItem('auditLog_columnVisibility') || '{}');
        columnVisibility = savedCols;
        Object.entries(columnVisibility).forEach(([field, isVisible]) => {
            const checkbox = document.getElementById(`col-toggle-${field}`);
            if (checkbox) {
                checkbox.checked = isVisible;
                if (!isVisible) {
                    const colIndex = checkbox.dataset.index;
                    const table = document.getElementById('audit-table');
                    table.querySelectorAll(`tr`).forEach(row => {
                        row.cells[colIndex].style.display = 'none';
                    });
                }
            }
        });
    }

    async function performAuditSearch() {
        const form = document.getElementById('audit-filter-form');
        const formData = new FormData(form);

        currentAuditFilters = {
            search: formData.get('search') || '',
            action: formData.get('action') || '',
        };

        const params = {
            ...currentAuditFilters,
            sort_by: currentAuditSort.field,
            sort_order: currentAuditSort.order,
            page: currentAuditPage,
            per_page: document.getElementById('audit-per-page').value
        };

        await loadAuditData(params);
    }

    async function loadAuditData(params) {
        setAuditLoading(true);
        try {
            const response = await fetch('/admin/api/audit-logs?' + new URLSearchParams(params));
            const data = await response.json();
            if (data.success) {
                updateAuditTable(data.logs);
                updateAuditPagination(data.pagination);
                updateAuditStats(data.pagination);
                updateAuditSortIndicators();
            } else {
                throw new Error(data.error || 'Failed to load audit logs.');
            }
        } catch (error) {
            console.error('Error loading audit data:', error);
            alert('Error loading audit data: ' + error.message);
        } finally {
            setAuditLoading(false);
        }
    }

    function updateAuditTable(logs) {
        const tbody = document.querySelector('#audit-table tbody');
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#888;">No audit log entries found.</td></tr>';
            return;
        }
        logs.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.id}</td>
                <td><small>${new Date(log.created_at).toLocaleString('no-NO')}</small></td>
                <td>${getActionBadge(log.action)}</td>
                <td>${log.admin_user || '<em>System</em>'}</td>
                <td>${log.target_user || '-'}</td>
                <td>${log.ip_address ? `<code>${log.ip_address}</code>` : '-'}</td>
                <td><small title="${log.user_agent}">${log.user_agent ? log.user_agent.substring(0, 30) + '...' : '-'}</small></td>
                <td><small title="${log.additional_info}">${log.additional_info ? log.additional_info.substring(0, 40) + '...' : '-'}</small></td>
            `;
            tbody.appendChild(row);
        });
        // Re-apply column visibility after rendering
        loadPreferences();
    }

    function getActionBadge(action) {
        const badges = {
            'grant_admin': '🛡️ Admin Granted',
            'revoke_admin': '❌ Admin Revoked',
            'admin_login_success': '✅ Admin Login',
            'admin_login_failure': '❌ Login Failed',
        };
        const badgeClass = action.includes('fail') || action.includes('revoke') ? 'btn-danger' : 'btn-secondary';
        return `<span class="btn ${badgeClass} btn-small" style="cursor:default;">${badges[action] || action.replace(/_/g, ' ')}</span>`;
    }

    function updateAuditPagination(pagination) {
        const container = document.getElementById('audit-pagination');
        container.innerHTML = '';
        if (!pagination || pagination.pages <= 1) return;

        let html = '<div class="pagination">';
        html += `<button class="page-btn" onclick="goToAuditPage(${pagination.prev_num})" ${!pagination.has_prev ? 'disabled' : ''}>← Previous</button>`;

        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);

        if (startPage > 1) {
            html += '<button class="page-btn" onclick="goToAuditPage(1)">1</button>';
            if (startPage > 2) html += '<span class="page-btn disabled">...</span>';
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === pagination.page ? 'active' : ''}" onclick="goToAuditPage(${i})">${i}</button>`;
        }

        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) html += '<span class="page-btn disabled">...</span>';
            html += `<button class="page-btn" onclick="goToAuditPage(${pagination.pages})">${pagination.pages}</button>`;
        }

        html += `<button class="page-btn" onclick="goToAuditPage(${pagination.next_num})" ${!pagination.has_next ? 'disabled' : ''}>Next →</button>`;
        html += '</div>';
        container.innerHTML = html;
    }

    function goToAuditPage(page) {
        if (page) {
            currentAuditPage = page;
            performAuditSearch();
        }
    }

    function updateAuditSortIndicators() {
        document.querySelectorAll('#audit-table .sort-indicator').forEach(indicator => {
            indicator.textContent = '';
            indicator.className = 'sort-indicator';
        });
        const activeHeader = document.querySelector(`#audit-table [data-field="${currentAuditSort.field}"]`);
        if (activeHeader) {
            const indicator = activeHeader.querySelector('.sort-indicator');
            indicator.className = `sort-indicator ${currentAuditSort.order}`;
        }
    }

    function clearAuditFilters() {
        document.getElementById('audit-filter-form').reset();
        currentAuditFilters = {};
        currentAuditSort = { field: 'created_at', order: 'desc' };
        currentAuditPage = 1;
        performAuditSearch();
    }

    function setAuditLoading(loading) {
        const indicator = document.getElementById('audit-loading');
        if (indicator) indicator.style.display = loading ? 'inline' : 'none';
        const table = document.getElementById('audit-table');
        if (table) table.style.opacity = loading ? '0.5' : '1';
    }

    function updateAuditStats(pagination) {
        document.getElementById('total-logs').textContent = pagination.total || '0';
        document.getElementById('unique-actions').textContent = pagination.unique_actions || '0';
        document.getElementById('current-page').textContent = pagination.page || '1';
        document.getElementById('total-pages').textContent = pagination.pages || '1';
    }

    async function showSecuritySummary() {
        const modal = document.getElementById('securitySummaryModal');
        const body = document.getElementById('securitySummaryBody');
        modal.style.display = 'block';
        body.innerHTML = '<div class="loading-indicator">Loading summary...</div>';

        try {
            const response = await fetch('/admin/api/audit-log/summary');
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                let content = '<h4>Recent Security Actions (Last 7 Days)</h4><ul>';
                data.recent_actions.forEach(log => {
                    content += `<li>${new Date(log.created_at).toLocaleString('no-NO')}: ${log.action} by ${log.admin_user}</li>`;
                });
                content += '</ul><h4>Most Frequent Actions</h4><ul>';
                for (const [action, count] of Object.entries(data.top_actions)) {
                    content += `<li>${action}: ${count} times</li>`;
                }
                content += '</ul><h4>Recent Login Attempts</h4><ul>';
                data.login_attempts.forEach(log => {
                    content += `<li class="${log.action.includes('success') ? 'text-success' : 'text-danger'}">${new Date(log.created_at).toLocaleString('no-NO')}: ${log.admin_user} - ${log.action}</li>`;
                });
                content += '</ul><h4>Top Active Admins</h4><ul>';
                for (const [username, count] of Object.entries(data.top_admins)) {
                    content += `<li>${username}: ${count} actions</li>`;
                }
                content += '</ul>';
                body.innerHTML = content;
            } else {
                body.innerHTML = `<div class="text-danger">Error: ${result.error}</div>`;
            }
        } catch (error) {
            body.innerHTML = `<div class="text-danger">Error: ${error.message}</div>`;
        }
    }

    function closeSecuritySummary() {
        document.getElementById('securitySummaryModal').style.display = 'none';
    }

    function exportAuditLog(format) {
        const loadingIndicator = document.getElementById('export-loading');
        loadingIndicator.style.display = 'inline';

        const params = {
            ...currentAuditFilters,
            sort_by: currentAuditSort.field,
            sort_order: currentAuditSort.order,
            format: format
        };
        const exportUrl = `/admin/api/audit-log/export?` + new URLSearchParams(params);

        fetch(exportUrl)
            .then(response => {
                if (!response.ok) throw new Error('Export failed: ' + response.statusText);
                const disposition = response.headers.get('Content-Disposition');
                const filename = disposition ? disposition.split('filename=')[1] : `audit_log.${format}`;
                return Promise.all([response.blob(), filename]);
            })
            .then(([blob, filename]) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch(error => {
                console.error('Export error:', error);
                alert('Could not export data. ' + error.message);
            })
            .finally(() => {
                loadingIndicator.style.display = 'none';
            });
    }

    function refreshAuditLog() {
        performAuditSearch();
    }

    // Expose functions to global scope
    window.initializeAuditEnhancements = initialize;
    window.performAuditSearch = performAuditSearch;
    window.goToAuditPage = goToAuditPage;
    window.clearAuditFilters = clearAuditFilters;
    window.showSecuritySummary = showSecuritySummary;
    window.closeSecuritySummary = closeSecuritySummary;
    window.exportAuditLog = exportAuditLog;
    window.refreshAuditLog = refreshAuditLog;

})(window);
