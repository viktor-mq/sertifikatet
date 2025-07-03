// static/js/admin/admin-audit-log.js

document.addEventListener('DOMContentLoaded', function() {
    initializeAuditEnhancements();
});

function initializeAuditEnhancements() {
    const form = document.getElementById('audit-filter-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            performAuditSearch();
        });
    }

    // Initial data load
    performAuditSearch();
}

function performAuditSearch() {
    const form = document.getElementById('audit-filter-form');
    const params = new URLSearchParams(new FormData(form));
    loadAuditData(params.toString());
}

async function loadAuditData(queryParams) {
    setAuditLoading(true);
    try {
        const response = await fetch(`/admin/api/audit-logs?${queryParams}`);
        const data = await response.json();
        if (data.success) {
            updateAuditTable(data.logs);
            updateAuditPagination(data.pagination);
            updateAuditStats(data.pagination);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        setAuditLoading(false);
    }
}

function updateAuditTable(logs) {
    const tbody = document.querySelector('#audit-table tbody');
    tbody.innerHTML = '';
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No logs found.</td></tr>';
        return;
    }
    logs.forEach(log => {
        const row = `<tr>
            <td>${log.id}</td>
            <td>${log.created_at}</td>
            <td>${log.action}</td>
            <td>${log.admin_user}</td>
            <td>${log.target_user ? log.target_user : 'N/A'}</td>
            <td>${log.ip_address}</td>
            <td>${log.user_agent}</td>
            <td>${log.additional_info}</td>
        </tr>`;
        tbody.innerHTML += row;
    });
}

function updateAuditPagination(pagination) {
    const container = document.getElementById('audit-pagination');
    container.innerHTML = '';
    if (pagination.pages > 1) {
        let html = '<nav><ul class="pagination">';
        if (pagination.has_prev) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.prev_num}">Previous</a></li>`;
        }
        for (let i = 1; i <= pagination.pages; i++) {
            html += `<li class="page-item ${i === pagination.page ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        if (pagination.has_next) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.next_num}">Next</a></li>`;
        }
        html += '</ul></nav>';
        container.innerHTML = html;

        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.target.dataset.page;
                const form = document.getElementById('audit-filter-form');
                const params = new URLSearchParams(new FormData(form));
                params.set('page', page);
                loadAuditData(params.toString());
            });
        });
    }
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
            let content = '';
            
            content += '<h4>Recent Security Actions (Last 7 Days)</h4>';
            content += '<ul>';
            data.recent_actions.forEach(log => {
                content += `<li>${log.created_at}: ${log.action} by ${log.admin_user}</li>`;
            });
            content += '</ul>';

            content += '<h4>Most Frequent Actions</h4>';
            content += '<ul>';
            for (const [action, count] of Object.entries(data.top_actions)) {
                content += `<li>${action}: ${count} times</li>`;
            }
            content += '</ul>';

            content += '<h4>Recent Login Attempts</h4>';
            content += '<ul>';
            data.login_attempts.forEach(log => {
                content += `<li class="${log.action === 'admin_login_success' ? 'text-success' : 'text-danger'}">${log.created_at}: ${log.admin_user} - ${log.action}</li>`;
            });
            content += '</ul>';

            content += '<h4>Top Active Admins</h4>';
            content += '<ul>';
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
    const form = document.getElementById('audit-filter-form');
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    const exportUrl = `/admin/api/audit-log/export?format=${format}&${params.toString()}`;
    
    const loadingIndicator = document.getElementById('export-loading');
    loadingIndicator.style.display = 'block';

    fetch(exportUrl)
        .then(response => {
            if (response.ok) return response.blob();
            throw new Error('Export failed.');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `audit_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            alert(error.message);
        })
        .finally(() => {
            loadingIndicator.style.display = 'none';
        });
}

function refreshAuditLog() {
    performAuditSearch();
}

function setAuditLoading(loading) {
    const indicator = document.getElementById('audit-loading');
    if (indicator) {
        indicator.style.display = loading ? 'block' : 'none';
    }
}
