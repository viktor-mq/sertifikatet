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

    // Campaign preview functionality
    function previewCampaign(emailId) {
        const modal = document.getElementById('campaignPreviewModal');
        const title = document.getElementById('campaignPreviewTitle');
        const subject = document.getElementById('campaignPreviewSubject');
        const content = document.getElementById('campaignPreviewContent');
        
        // Show modal
        modal.style.display = 'flex';
        
        // Show loading state
        content.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
                <p style="margin-top: 15px; color: #666;">Loading campaign preview...</p>
            </div>
        `;
        
        // Fetch the full campaign page and extract the preview content
        fetch(`/admin/marketing-emails/${emailId}`, {
            method: 'GET',
            headers: {
                'Accept': 'text/html',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // Parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract campaign title from the page
            const titleElement = doc.querySelector('h1.h3');
            const campaignTitle = titleElement ? titleElement.textContent.trim() : 'Campaign Preview';
            title.textContent = campaignTitle;
            
            // Extract subject from the page - look in the details section
            const subjectElement = doc.querySelector('dd');
            const campaignSubject = subjectElement ? subjectElement.textContent.trim() : 'No subject';
            subject.textContent = `Subject: ${campaignSubject}`;
            
            // Extract the email preview content from the card body
            const previewCard = doc.querySelector('.card .border');
            let emailContent = '<p>No content available</p>';
            
            if (previewCard) {
                emailContent = previewCard.innerHTML;
            } else {
                // Fallback: look for any element with email content
                const fallbackContent = doc.querySelector('.card-body .border');
                if (fallbackContent) {
                    emailContent = fallbackContent.innerHTML;
                }
            }
            
            // Clean up the content by removing any fixed width/height constraints
            // and other styling that might interfere with modal display
            let cleanedContent = emailContent
                // Remove any width/height constraints
                .replace(/width\s*:\s*[^;"']+[;"']/gi, '')
                .replace(/height\s*:\s*[^;"']+[;"']/gi, '')
                .replace(/max-width\s*:\s*[^;"']+[;"']/gi, '')
                .replace(/min-width\s*:\s*[^;"']+[;"']/gi, '')
                // Remove position constraints that might cause issues
                .replace(/position\s*:\s*fixed[;"']/gi, '')
                .replace(/position\s*:\s*absolute[;"']/gi, '')
                // Ensure tables and content are responsive
                .replace(/<table([^>]*)>/gi, '<table$1 style="width: 100%; max-width: 100%; table-layout: auto; border-collapse: collapse;">')
                .replace(/<td([^>]*)>/gi, '<td$1 style="word-wrap: break-word; max-width: 100%;">')
                .replace(/<img([^>]*?)style="([^"]*?)"([^>]*?)>/gi, function(match, before, style, after) {
                    // Make images responsive
                    const newStyle = style.replace(/width\s*:\s*[^;]+;?/gi, '').replace(/height\s*:\s*[^;]+;?/gi, '') + '; max-width: 100%; height: auto;';
                    return `<img${before}style="${newStyle}"${after}>`;
                })
                .replace(/<img([^>]*?)(?!style)([^>]*?)>/gi, '<img$1 style="max-width: 100%; height: auto;"$2>'); // For images without style attribute
            
            // Process template variables with sample data
            const processedContent = cleanedContent
                .replace(/\{\{user\.full_name\}\}/g, 'Ola Nordmann')
                .replace(/\{\{user\.username\}\}/g, 'olanordmann')
                .replace(/\{\{user\.email\}\}/g, 'ola@example.com')
                .replace(/\{\{user\.current_plan\}\}/g, 'Premium')
                .replace(/\{\{unsubscribe_url\}\}/g, '#unsubscribe')
            
            // Display the processed content with proper modal styling
            content.innerHTML = `
                <div style="
                    background: white;
                    border-radius: 4px;
                    max-height: 600px;
                    overflow-y: auto;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                ">
                    <div style="
                        max-width: 100%;
                        margin: 0 auto;
                        padding: 20px;
                        box-sizing: border-box;
                    ">
                        ${processedContent}
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading campaign preview:', error);
            content.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger mb-3"></i>
                    <p style="color: #dc3545;">Error loading campaign preview</p>
                    <p style="color: #666; font-size: 14px;">Please check that the campaign exists and try again.</p>
                </div>
            `;
        });
    }
    
    function closeCampaignPreview() {
        const modal = document.getElementById('campaignPreviewModal');
        modal.style.display = 'none';
    }

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
        
        let html = '';
        
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
            
            // Add "Create New Template" button as first grid item
            html += `
                <div style="
                    border: 2px dashed #007bff;
                    border-radius: 8px;
                    padding: 40px 20px;
                    background: #f8f9fa;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    min-height: 200px;
                "
                onmouseover="this.style.background='#e3f2fd'; this.style.transform='translateY(-2px)'"
                onmouseout="this.style.background='#f8f9fa'; this.style.transform='translateY(0)'"
                onclick="window.open('/admin/marketing-emails/create', '_blank'); closeTemplatesModal();">
                    <i class="fas fa-plus fa-3x" style="color: #007bff; margin-bottom: 15px;"></i>
                    <h5 style="color: #007bff; margin: 0; font-weight: bold;">Create New Template</h5>
                </div>
            `;
            
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
            const successRate = parseFloat(stats.success_rate) || 0;
            const formattedRate = successRate.toFixed(1);
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
                        <span class="btn btn-${getStatusBtnClass(email.status)} btn-small" style="cursor: default;">
                            ${email.status.charAt(0).toUpperCase() + email.status.slice(1)}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-info btn-small" 
                                onclick="showRecipientModal(${email.id})" 
                                title="View recipients"
                                style="cursor: default;">
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
                            <button class="btn btn-info btn-small" onclick="previewCampaign(${email.id})" title="Preview" style="margin-right: 5px;">
                                👁️ View
                            </button>
                            ${email.status === 'draft' ? `
                                <button class="btn btn-warning btn-small" onclick="editEmail(${email.id})" title="Edit" style="margin-right: 5px;">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-success btn-small" onclick="sendEmail(${email.id})" title="Send Now" style="margin-right: 5px;">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-danger btn-small" onclick="deleteEmail(${email.id})" title="Delete">
                                🗑️ Delete
                            </button>
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
        if (pagination.has_prev) {
            html += `<a class="page-btn" href="#" onclick="goToMarketingPage(${pagination.prev_num || 1}); return false;">Previous</a>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            if (i === pagination.page) {
                html += `<span class="page-btn active">${i}</span>`;
            } else {
                html += `<a class="page-btn" href="#" onclick="goToMarketingPage(${i}); return false;">${i}</a>`;
            }
        }
        
        // Next button
        if (pagination.has_next) {
            html += `<a class="page-btn" href="#" onclick="goToMarketingPage(${pagination.next_num || pagination.pages}); return false;">Next</a>`;
        }
        
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
        // Use preview modal instead of opening new tab
        previewCampaign(emailId);
    }
    
    function editEmail(emailId) {
        window.open(`/admin/marketing-emails/${emailId}/edit`, '_blank');
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
    
    function getStatusBtnClass(status) {
        const statusBtnClasses = {
            'draft': 'secondary',
            'scheduled': 'warning',
            'sending': 'info',
            'sent': 'success',
            'failed': 'danger',
            'partially_sent': 'warning'
        };
        return statusBtnClasses[status] || 'secondary';
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

    // Recipient modal variables
    let recipientData = [];
    let filteredRecipients = [];
    let currentPage = 1;
    const itemsPerPage = 20;

    function loadRecipientData(emailId) {
        // Show loading state
        document.getElementById('recipientTableContainer').innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mt-2">Loading recipients...</p>
            </div>
        `;
        
        // Fetch recipient data
        fetch(`/admin/api/marketing-recipients?email_id=${emailId}&details=true`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load recipients');
            }
            return response.json();
        })
        .then(data => {
            recipientData = data.recipients || [];
            filteredRecipients = [...recipientData];
            currentPage = 1;
            renderRecipientTable();
            updateRecipientCount();
        })
        .catch(error => {
            console.error('Error loading recipients:', error);
            document.getElementById('recipientTableContainer').innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exclamation-triangle fa-2x text-muted mb-3"></i>
                    <p class="text-muted">Error loading recipients: ${error.message}</p>
                    <button class="btn btn-outline-primary" onclick="loadRecipientData(${emailId})">Retry</button>
                </div>
            `;
        });
    }

    function renderRecipientTable() {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageData = filteredRecipients.slice(startIndex, endIndex);
        
        if (pageData.length === 0) {
            document.getElementById('recipientTableContainer').innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-users fa-2x text-muted mb-3"></i>
                    <p class="text-muted">No recipients found with current filters.</p>
                </div>
            `;
            document.getElementById('recipientPaginationNav').classList.add('d-none');
            return;
        }
        
        const tableHtml = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead>
                        <tr>
                            <th>Full Name</th>
                            <th>Email</th>
                            <th>Subscription</th>
                            <th>Account Type</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${pageData.map(recipient => `
                            <tr>
                                <td>${escapeHtml(recipient.full_name || 'N/A')}</td>
                                <td>${escapeHtml(recipient.email)}</td>
                                <td>
                                    <span class="badge bg-${getSubscriptionBadgeClass(recipient.subscription)}">
                                        ${recipient.subscription.charAt(0).toUpperCase() + recipient.subscription.slice(1)}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-${recipient.is_admin ? 'warning' : 'secondary'}">
                                        ${recipient.is_admin ? 'Admin' : 'User'}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-${getStatusBadgeClass(recipient.status || 'sent')}">
                                        ${(recipient.status || 'sent').charAt(0).toUpperCase() + (recipient.status || 'sent').slice(1)}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('recipientTableContainer').innerHTML = tableHtml;
        
        // FORCE APPLY STYLES AFTER TABLE IS CREATED
        setTimeout(() => {
            const modal = document.getElementById('recipientsModal');
            const table = modal?.querySelector('table');
            const thead = table?.querySelector('thead');
            const ths = table?.querySelectorAll('th');
            
            if (thead && ths && ths.length > 0) {
                console.log('🎨 Applying Recipients Modal table styles...');
                
                // Apply styles with maximum specificity
                thead.style.cssText = `
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    background-color: #3b82f6 ;
                    background-image: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    font-size: 14px ;
                `;
                
                ths.forEach(th => {
                    th.style.cssText = `
                        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) ;
                        background-color: #3b82f6 ;
                        background-image: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) ;
                        color: white ;
                        font-weight: 600 ;
                        padding: 12px 16px ;
                        border-bottom: 2px solid #1e40af ;
                        text-align: left ;
                    `;
                });
                
                console.log('✅ Recipients Modal table styles applied successfully!');
            }
        }, 50); // Small delay to ensure DOM is updated
        
        renderPagination();
    }

    function renderPagination() {
        // Always update the showing range, even for single page
        const startIndex = (currentPage - 1) * itemsPerPage + 1;
        const endIndex = Math.min(currentPage * itemsPerPage, filteredRecipients.length);
        
        // Update showing range regardless of pagination visibility
        const showingRangeEl = document.getElementById('showingRange');
        const totalCountEl = document.getElementById('totalCount');
        
        if (showingRangeEl) {
            showingRangeEl.textContent = `${startIndex}-${endIndex}`;
        }
        if (totalCountEl) {
            totalCountEl.textContent = filteredRecipients.length;
        }
        
        const totalPages = Math.ceil(filteredRecipients.length / itemsPerPage);
        
        if (totalPages <= 1) {
            document.getElementById('recipientPaginationNav').classList.add('d-none');
            document.getElementById('recipientPagination').classList.remove('d-none'); // Keep pagination info visible
            return; // Exit after updating the text
        }
        
        document.getElementById('recipientPaginationNav').classList.remove('d-none');
        document.getElementById('recipientPagination').classList.remove('d-none');
        
        // Generate pagination HTML
        let paginationHtml = '';
        
        // Previous button
        if (currentPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage - 1})">Previous</a></li>`;
        } else {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">Previous</span></li>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(1)">1</a></li>`;
            if (startPage > 2) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                paginationHtml += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${i})">${i}</a></li>`;
            }
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${totalPages})">${totalPages}</a></li>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage + 1})">Next</a></li>`;
        } else {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">Next</span></li>`;
        }
        
        document.getElementById('recipientPaginationList').innerHTML = paginationHtml;
     }

    function goToPage(page) {
        currentPage = page;
        renderRecipientTable();
    }

    function filterRecipients() {
        const searchTerm = document.getElementById('recipientSearch').value.toLowerCase();
        const subscriptionFilter = document.getElementById('subscriptionFilter').value;
        const adminFilter = document.getElementById('adminFilter').value;
        
        filteredRecipients = recipientData.filter(recipient => {
            // Search filter
            const searchMatch = !searchTerm || 
                (recipient.full_name && recipient.full_name.toLowerCase().includes(searchTerm)) ||
                recipient.email.toLowerCase().includes(searchTerm);
            
            // Subscription filter
            const subscriptionMatch = !subscriptionFilter || recipient.subscription === subscriptionFilter;
            
            // Admin filter
            let adminMatch = true;
            if (adminFilter === 'admin') {
                adminMatch = recipient.is_admin;
            } else if (adminFilter === 'user') {
                adminMatch = !recipient.is_admin;
            }
            
            return searchMatch && subscriptionMatch && adminMatch;
        });
        
        currentPage = 1;
        renderRecipientTable();
        updateRecipientCount();
    }

    function clearRecipientFilters() {
        document.getElementById('recipientSearch').value = '';
        document.getElementById('subscriptionFilter').value = '';
        document.getElementById('adminFilter').value = '';
        
        if (recipientData.length > 0) {
            filteredRecipients = [...recipientData];
            currentPage = 1;
            renderRecipientTable();
            updateRecipientCount();
        }
    }

    function updateRecipientCount() {
        document.getElementById('recipientCount').textContent = filteredRecipients.length;
    }

    function exportRecipients(format) {
        if (!currentEmailId) {
            alert('No email selected for export');
            return;
        }
        
        // Get current filter parameters
        const searchTerm = document.getElementById('recipientSearch').value;
        const subscriptionFilter = document.getElementById('subscriptionFilter').value;
        const adminFilter = document.getElementById('adminFilter').value;
        
        // Build export URL with filters
        const params = new URLSearchParams({
            email_id: currentEmailId,
            format: format,
            search: searchTerm,
            subscription: subscriptionFilter,
            admin_filter: adminFilter
        });
        
        // Remove empty parameters
        for (let [key, value] of params.entries()) {
            if (!value) {
                params.delete(key);
            }
        }
        
        const exportUrl = `/admin/api/marketing-recipients/export?${params.toString()}`;
        
        // Create temporary link and click it to trigger download
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = `recipients_${format}_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function getStatusBtnClass(status) {
        const statusBtnClasses = {
            'draft': 'secondary',
            'scheduled': 'warning',
            'sending': 'info',
            'sent': 'success',
            'failed': 'danger',
            'partially_sent': 'warning'
        };
        return statusBtnClasses[status] || 'secondary';
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

    function getSubscriptionBadgeClass(subscription) {
        switch (subscription) {
            case 'free': return 'secondary';
            case 'premium': return 'primary';
            case 'pro': return 'dark';
            default: return 'secondary';
        }
    }
    
    function getStatusBadgeClass(status) {
        switch (status) {
            case 'sent': return 'success';
            case 'failed': return 'danger';
            case 'bounced': return 'warning';
            case 'pending': return 'info';
            default: return 'success';
        }
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function escapeJson(obj) {
        return JSON.stringify(obj).replace(/'/g, "&#39;");
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('no-NO', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
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

    // Debounce function for search input
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

    // Set up event listeners for recipient modal
    function setupRecipientEventListeners() {
        const searchInput = document.getElementById('recipientSearch');
        const subscriptionSelect = document.getElementById('subscriptionFilter');
        const adminSelect = document.getElementById('adminFilter');
        
        if (searchInput) {
            searchInput.addEventListener('input', debounce(filterRecipients, 300));
        }
        if (subscriptionSelect) {
            subscriptionSelect.addEventListener('change', filterRecipients);
        }
        if (adminSelect) {
            adminSelect.addEventListener('change', filterRecipients);
        }
    }
    
    // Missing functions needed by the marketing system
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
    
    function initializeMarketing() {
        console.log('Marketing section initialized');
        
        // Ensure marketing section is visible
        const marketingSection = document.getElementById('marketingSection');
        if (marketingSection) {
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

    
    // Additional functions for email actions
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
        // Use preview modal instead of opening new tab
        previewCampaign(emailId);
    }
    
    function editEmail(emailId) {
        window.open(`/admin/marketing-emails/${emailId}/edit`, '_blank');
    }
    
    
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

    
    // Initialize modal events
    setupModalEvents();
    
    // Expose all functions globally
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
    window.useTemplate = useTemplate;
    window.previewTemplate = previewTemplate;
    window.changeMarketingTableDensity = changeMarketingTableDensity;
    window.loadMarketingEmails = loadMarketingEmails;
    window.updateMarketingTable = updateMarketingTable;
    window.updateMarketingStats = updateMarketingStats;
    
    // Recipient modal functions
    window.showRecipientModal = showRecipientModal;
    window.clearRecipientFilters = clearRecipientFilters;
    window.loadRecipientData = loadRecipientData;
    window.exportRecipients = exportRecipients;
    window.goToPage = goToPage;
    window.filterRecipients = filterRecipients;
    window.updateRecipientCount = updateRecipientCount;
    window.renderRecipientTable = renderRecipientTable;
    window.renderPagination = renderPagination;
    window.getSubscriptionBadgeClass = getSubscriptionBadgeClass;
    window.getStatusBadgeClass = getStatusBadgeClass;
    window.escapeHtml = escapeHtml;
    window.escapeJson = escapeJson;
    window.previewCampaign = previewCampaign;
    window.closeCampaignPreview = closeCampaignPreview;
    
    // Set up recipient modal event listeners when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        setupRecipientEventListeners();
    });
    
})();