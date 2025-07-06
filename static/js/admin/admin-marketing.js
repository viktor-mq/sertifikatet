(function () { 'use strict';
    // Marketing Section - Full AJAX Implementation
    
    // State management
    let currentEmailId = null;
    let marketingCurrentFilters = { search: '', status: '' };
    let marketingCurrentSort = { field: 'created_at', order: 'desc' };
    let marketingCurrentPage = 1;
    let marketingPerPage = 20;
    let marketingSearchTimeout;
    
    // Template preview state
    let currentPreviewTemplate = null;

    // Modal management
    function openTemplatesModal() {
        document.getElementById('templatesModal').style.display = 'flex';
        loadTemplatesInModal();
    }
    
    function closeTemplatesModal() {
        document.getElementById('templatesModal').style.display = 'none';
    }
    
    function openTemplatePreviewModal(template) {
        currentPreviewTemplate = template;
        document.getElementById('previewTemplateTitle').textContent = template.name;
        document.getElementById('previewTemplateDescription').textContent = template.description || 'No description available';
        
        // Create preview HTML with sample data
        const previewHtml = template.html_content
            .replace(/\{\{user\.full_name\}\}/g, 'Ola Nordmann')
            .replace(/\{\{user\.username\}\}/g, 'olanordmann')
            .replace(/\{\{user\.email\}\}/g, 'ola@example.com')
            .replace(/\{\{user\.current_plan\}\}/g, 'Premium')
            .replace(/\{\{unsubscribe_url\}\}/g, '#unsubscribe')
            .replace(/\{\{settings_url\}\}/g, '#settings');
        
        // Load content into iframe
        const iframe = document.getElementById('templatePreviewFrame');
        iframe.srcdoc = previewHtml;
        
        document.getElementById('templatePreviewModal').style.display = 'flex';
    }
    
    function closeTemplatePreviewModal() {
        document.getElementById('templatePreviewModal').style.display = 'none';
        currentPreviewTemplate = null;
    }
    
    function useTemplateFromPreview() {
        if (currentPreviewTemplate) {
            window.open(`/admin/marketing-emails/create?template_id=${currentPreviewTemplate.id}`, '_blank');
            closeTemplatePreviewModal();
            closeTemplatesModal();
        }
    }
    
    function loadTemplatesInModal() {
        const templatesContent = document.getElementById('templatesContent');
        if (!templatesContent) return;
        
        templatesContent.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Loading templates...</div>';
        
        fetch('/admin/api/marketing-templates', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderTemplatesModal(data.templates);
            } else {
                templatesContent.innerHTML = '<div class="alert alert-danger">Error loading templates: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            templatesContent.innerHTML = '<div class="alert alert-danger">Error loading templates.</div>';
        });
    }
    
    function renderTemplatesModal(templates) {
        const templatesContent = document.getElementById('templatesContent');
        
        let html = `
            <div style="margin-bottom: 30px; text-align: center;">
                <button onclick="window.open('/admin/marketing-templates/create', '_blank'); closeTemplatesModal();" style="
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                ">
                    <i class="fas fa-plus"></i> Create New Template
                </button>
            </div>
        `;
        
        if (templates.length === 0) {
            html += `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <i class="fas fa-file-alt fa-3x" style="margin-bottom: 20px; opacity: 0.5;"></i>
                    <h4>No saved templates yet</h4>
                    <p>Create your first marketing email template to get started.</p>
                </div>
            `;
        } else {
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">';
            
            templates.forEach(template => {
                const categoryIcon = getCategoryIcon(template.category);
                const categoryColor = getCategoryColor(template.category);
                
                html += `
                    <div style="
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 20px;
                        background: white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                        transition: all 0.2s ease;
                        cursor: pointer;
                        position: relative;
                    " 
                    onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'; this.style.transform='translateY(-2px)'"
                    onmouseout="this.style.boxShadow='0 2px 4px rgba(0,0,0,0.05)'; this.style.transform='translateY(0)'"
                    onclick="openTemplatePreviewModal(${escapeJson(template)})">
                        
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="
                                background: ${categoryColor};
                                color: white;
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin-right: 15px;
                                font-size: 18px;
                            ">
                                ${categoryIcon}
                            </div>
                            <div>
                                <h5 style="margin: 0; color: #333; font-size: 16px;">${escapeHtml(template.name)}</h5>
                                <small style="color: #666; text-transform: capitalize;">${template.category || 'General'}</small>
                            </div>
                        </div>
                        
                        <p style="
                            color: #666;
                            font-size: 14px;
                            line-height: 1.4;
                            margin-bottom: 15px;
                            display: -webkit-box;
                            -webkit-line-clamp: 3;
                            -webkit-box-orient: vertical;
                            overflow: hidden;
                        ">
                            ${escapeHtml(template.description || 'No description available')}
                        </p>
                        
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-size: 12px;
                            color: #999;
                        ">
                            <span>Created: ${formatDate(template.created_at)}</span>
                            <span>Used ${template.times_used || 0} times</span>
                        </div>
                        
                        <div style="
                            position: absolute;
                            top: 15px;
                            right: 15px;
                            background: #f8f9fa;
                            border: 1px solid #e0e0e0;
                            border-radius: 4px;
                            padding: 5px 8px;
                            font-size: 10px;
                            color: #666;
                            text-transform: uppercase;
                            font-weight: bold;
                        ">
                            Preview
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        templatesContent.innerHTML = html;
    }
    
    // Email sending modal
    function sendEmail(emailId) {
        currentEmailId = emailId;
        
        // Get recipient count
        fetch(`/admin/api/marketing-recipients?email_id=${emailId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('recipientCount').innerHTML = 
                `<p><strong>Recipients:</strong> ${data.count} users will receive this email</p>`;
            
            document.getElementById('sendEmailModal').style.display = 'flex';
        })
        .catch(error => {
            console.error('Error getting recipient count:', error);
            showNotification('Error getting recipient count', 'error');
        });
    }
    
    function closeSendEmailModal() {
        document.getElementById('sendEmailModal').style.display = 'none';
        currentEmailId = null;
    }
    
    // Marketing data loading
    function loadMarketingData() {
        console.log('Loading marketing data with filters:', marketingCurrentFilters);
        
        showMarketingLoading(true);
        
        // Load stats and emails in parallel
        Promise.all([
            loadMarketingStats(),
            loadMarketingEmails()
        ]).then(() => {
            showMarketingLoading(false);
        }).catch(error => {
            console.error('Error loading marketing data:', error);
            showMarketingLoading(false);
            showNotification('Error loading marketing data', 'error');
        });
    }
    
    function loadMarketingStats() {
        return fetch('/admin/api/marketing-stats', {
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
            if (data.success) {
                updateMarketingStats(data.stats);
            } else {
                console.error('Error loading stats:', data.error);
                // Set default stats on error
                updateMarketingStats({
                    total_campaigns: 0,
                    opted_in_users: 0,
                    sent_this_month: 0,
                    success_rate: 0
                });
            }
        })
        .catch(error => {
            console.error('Failed to load marketing stats:', error);
            // Set default stats on network error
            updateMarketingStats({
                total_campaigns: 0,
                opted_in_users: 0,
                sent_this_month: 0,
                success_rate: 0
            });
        });
    }
    
    function loadMarketingEmails() {
        const params = {
            page: marketingCurrentPage,
            per_page: marketingPerPage,
            sort_by: marketingCurrentSort.field,
            sort_order: marketingCurrentSort.order,
            ...marketingCurrentFilters
        };
        
        const queryString = new URLSearchParams(params).toString();
        
        return fetch(`/admin/api/marketing-emails?${queryString}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateMarketingTable(data.emails, data.pagination);
            } else {
                console.error('Error loading emails:', data.error);
                showNotification('Error loading emails: ' + data.error, 'error');
            }
        });
    }
    
    function updateMarketingStats(stats) {
        const elements = {
            totalCampaigns: document.querySelector('[data-stat="total_campaigns"]'),
            optedInUsers: document.querySelector('[data-stat="opted_in_users"]'),
            sentThisMonth: document.querySelector('[data-stat="sent_this_month"]'),
            successRate: document.querySelector('[data-stat="success_rate"]')
        };
        
        // Ensure stats object exists and has the required properties
        if (!stats || typeof stats !== 'object') {
            console.warn('Invalid stats object received:', stats);
            stats = {
                total_campaigns: 0,
                opted_in_users: 0,
                sent_this_month: 0,
                success_rate: 0
            };
        }
        
        if (elements.totalCampaigns) {
            elements.totalCampaigns.textContent = stats.total_campaigns || 0;
        }
        if (elements.optedInUsers) {
            elements.optedInUsers.textContent = stats.opted_in_users || 0;
        }
        if (elements.sentThisMonth) {
            elements.sentThisMonth.textContent = stats.sent_this_month || 0;
        }
        if (elements.successRate) {
            const successRate = stats.success_rate || 0;
            // Ensure success_rate is a number before calling toFixed
            const formattedRate = typeof successRate === 'number' ? successRate.toFixed(1) : '0.0';
            elements.successRate.textContent = formattedRate + '%';
        }
    }
    
    function updateMarketingTable(emails, pagination) {
        const tableBody = document.getElementById('marketing-emails-tbody');
        if (!tableBody) return;
        
        if (emails.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center p-4">
                        <i class="fas fa-envelope fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No marketing campaigns found</h5>
                        <p class="text-muted">Create your first marketing email campaign to get started.</p>
                        <button class="btn btn-primary" onclick="window.open('/admin/marketing-emails/create', '_blank')">
                            <i class="fas fa-plus"></i> Create Campaign
                        </button>
                    </td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        emails.forEach(email => {
            const statusClass = getStatusClass(email.status);
            const statusIcon = getStatusIcon(email.status);
            
            html += `
                <tr>
                    <td>
                        <strong>${escapeHtml(email.title)}</strong>
                        <br><small class="text-muted">by ${escapeHtml(email.created_by?.username || 'Unknown')}</small>
                    </td>
                    <td>${escapeHtml(email.subject)}</td>
                    <td>
                        <span class="badge ${statusClass}">
                            <i class="${statusIcon}"></i> ${email.status.charAt(0).toUpperCase() + email.status.slice(1)}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-link p-0 recipient-count-btn" 
                                onclick="showRecipientModal(${email.id})" 
                                title="View recipients">
                            ${email.sent_count} / ${email.recipients_count}
                        </button>
                        ${email.failed_count > 0 ? `<br><small class="text-danger">${email.failed_count} failed</small>` : ''}
                    </td>
                    <td>
                        ${email.recipients_count > 0 ? `${((email.sent_count / email.recipients_count) * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td>
                        ${email.created_at}
                        ${email.sent_at ? `<br><small class="text-muted">Sent: ${email.sent_at}</small>` : ''}
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewEmailDetails(${email.id})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${email.status === 'draft' ? `
                                <button class="btn btn-outline-warning" onclick="editEmail(${email.id})" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-outline-success" onclick="sendEmail(${email.id})" title="Send Now">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteEmail(${email.id})" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                            ${email.status === 'sent' || email.status === 'failed' ? `
                                <button class="btn btn-outline-info" onclick="viewEmailLogs(${email.id})" title="View Logs">
                                    <i class="fas fa-list"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
        updateMarketingPagination(pagination);
    }
    
    function updateMarketingPagination(pagination) {
        const paginationContainer = document.getElementById('marketing-pagination');
        if (!paginationContainer) return;
        
        let html = '';
        
        // Previous button
        html += `
            <li class="page-item ${!pagination.has_prev ? 'disabled' : ''}">
                <button class="page-link" onclick="goToMarketingPage(${pagination.prev_num || 1})" ${!pagination.has_prev ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
            </li>
        `;
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === pagination.page ? 'active' : ''}">
                    <button class="page-link" onclick="goToMarketingPage(${i})">${i}</button>
                </li>
            `;
        }
        
        // Next button
        html += `
            <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
                <button class="page-link" onclick="goToMarketingPage(${pagination.next_num || pagination.pages})" ${!pagination.has_next ? 'disabled' : ''}>
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </li>
        `;
        
        paginationContainer.innerHTML = html;
        
        // Update pagination info
        const paginationInfo = document.getElementById('marketing-pagination-info');
        if (paginationInfo) {
            paginationInfo.textContent = `Showing ${((pagination.page - 1) * pagination.per_page) + 1}-${Math.min(pagination.page * pagination.per_page, pagination.total)} of ${pagination.total} campaigns`;
        }
    }
    
    // Event handlers
    function goToMarketingPage(page) {
        marketingCurrentPage = page;
        loadMarketingEmails();
    }
    
    function applyMarketingFilters() {
        const searchValue = document.getElementById('marketing-search')?.value || '';
        const statusValue = document.getElementById('marketing-status-filter')?.value || '';
        
        marketingCurrentFilters = {
            search: searchValue,
            status: statusValue
        };
        
        marketingCurrentPage = 1;
        loadMarketingEmails();
    }
    
    function clearMarketingFilters() {
        const searchInput = document.getElementById('marketing-search');
        const statusFilter = document.getElementById('marketing-status-filter');
        
        if (searchInput) searchInput.value = '';
        if (statusFilter) statusFilter.value = '';
        
        marketingCurrentFilters = { search: '', status: '' };
        marketingCurrentPage = 1;
        loadMarketingEmails();
    }
    
    // Email actions
    function deleteEmail(emailId) {
        if (!confirm('Are you sure you want to delete this email campaign? This action cannot be undone.')) {
            return;
        }
        
        fetch(`/admin/api/marketing-email/${emailId}/delete`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                loadMarketingEmails(); // Refresh the table
            } else {
                showNotification('Error deleting email: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting email:', error);
            showNotification('Error deleting email', 'error');
        });
    }
    
    function viewEmailDetails(emailId) {
        window.open(`/admin/marketing-emails/${emailId}`, '_blank');
    }
    
    function editEmail(emailId) {
        window.open(`/admin/marketing-emails/${emailId}/edit`, '_blank');
    }
    
    function viewEmailLogs(emailId) {
        window.open(`/admin/marketing-emails/${emailId}/logs`, '_blank');
    }
    
    // Utility functions
    function getCategoryIcon(category) {
        const icons = {
            'newsletter': '📰',
            'promotion': '🎁',
            'announcement': '📢',
            'welcome': '👋',
            'reminder': '⏰',
            'seasonal': '🎭'
        };
        return icons[category] || '📄';
    }
    
    function getCategoryColor(category) {
        const colors = {
            'newsletter': '#007bff',
            'promotion': '#28a745',
            'announcement': '#6c757d',
            'welcome': '#17a2b8',
            'reminder': '#ffc107',
            'seasonal': '#6f42c1'
        };
        return colors[category] || '#6c757d';
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('no-NO', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    function escapeJson(obj) {
        return JSON.stringify(obj).replace(/'/g, "&#39;");
    }
    
    function getStatusClass(status) {
        const statusClasses = {
            'draft': 'badge-secondary',
            'scheduled': 'badge-warning',
            'sending': 'badge-info',
            'sent': 'badge-success',
            'failed': 'badge-danger',
            'partially_sent': 'badge-warning'
        };
        return statusClasses[status] || 'badge-secondary';
    }
    
    function getStatusIcon(status) {
        const statusIcons = {
            'draft': 'fas fa-file-alt',
            'scheduled': 'fas fa-clock',
            'sending': 'fas fa-spinner fa-spin',
            'sent': 'fas fa-check',
            'failed': 'fas fa-times',
            'partially_sent': 'fas fa-exclamation-triangle'
        };
        return statusIcons[status] || 'fas fa-file-alt';
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showMarketingLoading(show) {
        const loadingEl = document.getElementById('marketing-loading');
        const tableEl = document.getElementById('marketing-table');
        
        if (show) {
            if (loadingEl) loadingEl.style.display = 'block';
            if (tableEl) tableEl.style.opacity = '0.5';
        } else {
            if (loadingEl) loadingEl.style.display = 'none';
            if (tableEl) tableEl.style.opacity = '1';
        }
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Template functions
    function useTemplate(templateId) {
        window.open(`/admin/marketing-emails/create?template_id=${templateId}`, '_blank');
        closeTemplatesModal();
    }
    
    function previewTemplate(templateId) {
        fetch(`/admin/api/marketing-template?id=${templateId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.html_content) {
                // Open preview in new window
                const previewWindow = window.open('', '_blank', 'width=800,height=600');
                previewWindow.document.write(data.html_content);
                previewWindow.document.close();
            }
        })
        .catch(error => {
            console.error('Error previewing template:', error);
            showNotification('Error previewing template', 'error');
        });
    }
    
    // Table density control
    function changeMarketingTableDensity() {
        const densitySelector = document.getElementById('marketingTableDensitySelector');
        const tableContainer = document.querySelector('.marketing-table');
        
        if (!densitySelector || !tableContainer) return;
        
        const density = densitySelector.value;
        
        // Remove existing density classes
        tableContainer.classList.remove('compact', 'comfortable', 'spacious');
        
        // Add new density class
        tableContainer.classList.add(density);
        
        console.log(`Marketing table density changed to: ${density}`);
    }

    // Main initialization function
    function initializeMarketing() {
        console.log('Marketing section initialized');
        
        // Ensure marketing section is visible
        const marketingSection = document.getElementById('marketingSection');
        if (marketingSection) {
            marketingSection.style.display = 'block';
            console.log('Marketing section display set to block');
        } else {
            console.error('Marketing section not found!');
            return;
        }
        
        // Initialize search with debouncing
        const searchInput = document.getElementById('marketing-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(marketingSearchTimeout);
                marketingSearchTimeout = setTimeout(() => {
                    applyMarketingFilters();
                }, 300);
            });
        }
        
        // Initialize status filter
        const statusFilter = document.getElementById('marketing-status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', applyMarketingFilters);
        }
        
        // Load initial data
        loadMarketingData();
    }
    
    // Email sending functionality
    function handleEmailSend() {
        const confirmSendBtn = document.getElementById('confirmSend');
        if (!confirmSendBtn || !currentEmailId) return;
        
        // Show loading state
        const originalText = confirmSendBtn.innerHTML;
        confirmSendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        confirmSendBtn.disabled = true;
        
        // Send the email
        fetch('/admin/api/marketing-send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({email_id: currentEmailId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Email campaign sent successfully!', 'success');
                closeSendEmailModal();
                loadMarketingEmails(); // Refresh the table
            } else {
                showNotification('Error sending email: ' + data.error, 'error');
                confirmSendBtn.innerHTML = originalText;
                confirmSendBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error sending email:', error);
            showNotification('Error sending email', 'error');
            confirmSendBtn.innerHTML = originalText;
            confirmSendBtn.disabled = false;
        });
    }
    
    // Modal event handlers
    function setupModalEvents() {
        // Close modals when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === document.getElementById('templatesModal')) {
                closeTemplatesModal();
            }
            if (event.target === document.getElementById('templatePreviewModal')) {
                closeTemplatePreviewModal();
            }
            if (event.target === document.getElementById('sendEmailModal')) {
                closeSendEmailModal();
            }
        });
        
        // Set up confirm send button event listener
        document.addEventListener('DOMContentLoaded', function() {
            const confirmSendBtn = document.getElementById('confirmSend');
            if (confirmSendBtn) {
                confirmSendBtn.addEventListener('click', handleEmailSend);
            }
        });
    }

    // Recipient Modal Functions
function showRecipientModal(emailId) {
    currentEmailId = emailId;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('recipientsModal'));
    modal.show();
    
    // Reset filters and load data
    clearRecipientFilters();
    loadRecipientData(emailId);
}

    
    // Initialize modal events
    setupModalEvents();
    
    // Expose functions globally
    window.openTemplatesModal = openTemplatesModal;
    window.closeTemplatesModal = closeTemplatesModal;
    window.openTemplatePreviewModal = openTemplatePreviewModal;
    window.closeTemplatePreviewModal = closeTemplatePreviewModal;
    window.useTemplateFromPreview = useTemplateFromPreview;
    window.sendEmail = sendEmail;
    window.closeSendEmailModal = closeSendEmailModal;
    window.initializeMarketing = initializeMarketing;
    window.loadMarketingData = loadMarketingData;
    window.applyMarketingFilters = applyMarketingFilters;
    window.clearMarketingFilters = clearMarketingFilters;
    window.goToMarketingPage = goToMarketingPage;
    window.deleteEmail = deleteEmail;
    window.viewEmailDetails = viewEmailDetails;
    window.editEmail = editEmail;
    window.viewEmailLogs = viewEmailLogs;
    window.useTemplate = useTemplate;
    window.previewTemplate = previewTemplate;
    window.changeMarketingTableDensity = changeMarketingTableDensity;
    window.loadMarketingEmails = loadMarketingEmails;
    window.showRecipientModal = showRecipientModal;
    window.updateMarketingTable = updateMarketingTable;
    window.updateMarketingStats = updateMarketingStats;
    
})();