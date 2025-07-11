// admin-learning.js - Learning Modules Admin Dashboard JavaScript
(function(window) {
    'use strict';
    // Learning Modules JavaScript Functions
    function initializeLearningModules() {
        console.log('Initializing Learning Modules section...');
        loadModulesData();
        loadModulesForDropdown();
        setupVideoUploadDropZone();
        setupFormHandlers();
    }

    function loadModulesData() {
        const loadingDiv = document.getElementById('learning-loading');
        const tableContainer = document.getElementById('modules-table');
        
        if (loadingDiv) loadingDiv.style.display = 'block';
        if (tableContainer) tableContainer.style.opacity = '0.5';
        
        // Get current filter values
        const statusFilter = document.getElementById('module-status-filter')?.value || '';
        const searchFilter = document.getElementById('module-search')?.value || '';
        
        const params = new URLSearchParams();
        if (statusFilter) params.append('status', statusFilter);
        if (searchFilter) params.append('search', searchFilter);
        
        fetch(`/admin/api/learning-modules?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                updateModulesTable(data.modules || []);
                updateModulesStats(data.stats || {});
            })
            .catch(error => {
                console.error('Error loading modules:', error);
                showError('Failed to load learning modules');
            })
            .finally(() => {
                if (loadingDiv) loadingDiv.style.display = 'none';
                if (tableContainer) tableContainer.style.opacity = '1';
            });
    }

    function updateModulesTable(modules) {
        const tbody = document.getElementById('modules-tbody');
        if (!tbody) return;
        
        if (modules.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="padding: 40px; text-align: center; color: #666;">
                        <i class="fas fa-graduation-cap fa-3x" style="margin-bottom: 15px; opacity: 0.3;"></i>
                        <p style="margin: 0; font-size: 16px;">No learning modules found</p>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">Create your first module to get started</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = modules.map(module => `
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">${module.module_number}</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">
                    <strong>${escapeHtml(module.title)}</strong>
                    ${module.description ? `<br><small style="color: #666;">${escapeHtml(module.description.substring(0, 100))}${module.description.length > 100 ? '...' : ''}</small>` : ''}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">${module.submodule_count || 0}</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">${module.video_count || 0}</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">
                    <span class="badge badge-${module.is_active ? 'success' : 'secondary'}" style="
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        font-size: 12px; 
                        font-weight: bold;
                        background: ${module.is_active ? '#28a745' : '#6c757d'};
                        color: white;
                    ">
                        ${module.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">${Math.round(module.completion_rate || 0)}%</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #e0e0e0;">
                    <button onclick="editModule(${module.id})" style="
                        background: #007bff; 
                        color: white; 
                        border: none; 
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        margin-right: 5px;
                        font-size: 12px;
                    ">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="deleteModule(${module.id})" style="
                        background: #dc3545; 
                        color: white; 
                        border: none; 
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        cursor: pointer;
                        font-size: 12px;
                    ">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');
    }

    function updateModulesStats(stats) {
        const statElements = {
            'total_modules': stats.total_modules || 0,
            'total_submodules': stats.total_submodules || 0,
            'total_videos': stats.total_videos || 0,
            'completion_rate': Math.round(stats.avg_completion_rate || 0) + '%'
        };
        
        Object.entries(statElements).forEach(([key, value]) => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) element.textContent = value;
        });
    }

    // Modal Functions
    function createNewModule() {
        const modal = document.getElementById('createModuleModal');
        if (modal) {
            modal.style.display = 'flex';
            document.getElementById('createModuleForm').reset();
        }
    }

    function closeCreateModuleModal() {
        const modal = document.getElementById('createModuleModal');
        if (modal) modal.style.display = 'none';
    }

    function uploadVideoModal() {
        const modal = document.getElementById('uploadVideoModal');
        if (modal) {
            modal.style.display = 'flex';
            document.getElementById('uploadVideoForm').reset();
            loadModulesForDropdown();
            resetVideoDropZone();
        }
    }

    function closeUploadVideoModal() {
        const modal = document.getElementById('uploadVideoModal');
        if (modal) modal.style.display = 'none';
    }

    function editModule(moduleId) {
        // Load module data and show edit modal
        fetch(`/admin/api/learning-modules/${moduleId}`)
            .then(response => response.json())
            .then(module => {
                if (module.error) {
                    showError(module.error);
                    return;
                }
                
                document.getElementById('editModuleId').value = module.id;
                document.getElementById('editModuleNumber').value = module.module_number;
                document.getElementById('editModuleTitle').value = module.title;
                document.getElementById('editModuleDescription').value = module.description || '';
                document.getElementById('editModuleHours').value = module.estimated_hours || '';
                document.getElementById('editModuleStatus').value = module.is_active ? '1' : '0';
                
                const modal = document.getElementById('editModuleModal');
                if (modal) modal.style.display = 'flex';
            })
            .catch(error => {
                console.error('Error loading module:', error);
                showError('Failed to load module data');
            });
    }

    function closeEditModuleModal() {
        const modal = document.getElementById('editModuleModal');
        if (modal) modal.style.display = 'none';
    }

    function deleteModule(moduleId) {
        if (confirm('Are you sure you want to delete this module? This action cannot be undone and will also delete all associated submodules and videos.')) {
            fetch(`/admin/api/learning-modules/${moduleId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess('Module deleted successfully');
                    loadModulesData();
                } else {
                    showError(data.message || 'Failed to delete module');
                }
            })
            .catch(error => {
                console.error('Error deleting module:', error);
                showError('Failed to delete module');
            });
        }
    }

    // Utility Functions
    function loadModulesForDropdown() {
        fetch('/admin/api/learning-modules')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('videoModule');
                if (select && data.modules) {
                    select.innerHTML = '<option value="">Select a module...</option>' +
                        data.modules.filter(module => module.is_active).map(module => 
                            `<option value="${module.id}">${module.module_number} - ${escapeHtml(module.title)}</option>`
                        ).join('');
                    
                    // Setup module change handler
                    select.addEventListener('change', loadSubmodulesForDropdown);
                }
            })
            .catch(error => console.error('Error loading modules for dropdown:', error));
    }

    function loadSubmodulesForDropdown() {
        const moduleSelect = document.getElementById('videoModule');
        const submoduleSelect = document.getElementById('videoSubmodule');
        
        if (!moduleSelect || !submoduleSelect) return;
        
        const moduleId = moduleSelect.value;
        
        if (!moduleId) {
            submoduleSelect.innerHTML = '<option value="">First select a module...</option>';
            return;
        }
        
        fetch(`/admin/api/learning-modules/${moduleId}/submodules`)
            .then(response => response.json())
            .then(data => {
                if (data.submodules && data.submodules.length > 0) {
                    submoduleSelect.innerHTML = '<option value="">Select a submodule...</option>' +
                        data.submodules.map(submodule => 
                            `<option value="${submodule.id}">${submodule.submodule_number} - ${escapeHtml(submodule.title)}</option>`
                        ).join('');
                } else {
                    submoduleSelect.innerHTML = '<option value="">No submodules available</option>';
                }
            })
            .catch(error => {
                console.error('Error loading submodules:', error);
                submoduleSelect.innerHTML = '<option value="">Error loading submodules</option>';
            });
    }

    function setupVideoUploadDropZone() {
        const dropZone = document.getElementById('video-drop-zone');
        const fileInput = document.getElementById('videoFile');
        
        if (dropZone && fileInput) {
            dropZone.addEventListener('click', () => fileInput.click());
            
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#007bff';
                dropZone.style.backgroundColor = '#f8f9ff';
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#ccc';
                dropZone.style.backgroundColor = '';
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#ccc';
                dropZone.style.backgroundColor = '';
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    updateDropZoneText(files[0].name);
                    validateVideoFile(files[0]);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    updateDropZoneText(e.target.files[0].name);
                    validateVideoFile(e.target.files[0]);
                }
            });
        }
    }

    function updateDropZoneText(filename) {
        const dropZone = document.getElementById('video-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-file-video fa-3x" style="color: #007bff; margin-bottom: 15px;"></i>
                <p style="margin: 0; color: #333; font-weight: bold;">${escapeHtml(filename)}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Click to change file</p>
            `;
        }
    }

    function resetVideoDropZone() {
        const dropZone = document.getElementById('video-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-cloud-upload-alt fa-3x" style="color: #ccc; margin-bottom: 15px;"></i>
                <p style="margin: 0; color: #666;">Drag and drop video file here or click to browse</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">Supported formats: MP4 (max 300MB)</p>
            `;
        }
    }

    function validateVideoFile(file) {
        const errors = [];
        
        // Check file type
        if (!file.type.includes('video/mp4')) {
            errors.push('Only MP4 video files are supported');
        }
        
        // Check file size (300MB = 300 * 1024 * 1024 bytes)
        if (file.size > 100 * 1024 * 1024) {
            errors.push('File size must be less than 300MB');
        }
        
        if (errors.length > 0) {
            showError(errors.join('. '));
            resetVideoDropZone();
            document.getElementById('videoFile').value = '';
            return false;
        }
        
        return true;
    }

    function applyModuleFilters() {
        loadModulesData(); // Reload with current filter values
    }

    function clearModuleFilters() {
        document.getElementById('module-status-filter').value = '';
        document.getElementById('module-search').value = '';
        loadModulesData();
    }

    function changeModuleTableDensity() {
        const density = document.getElementById('moduleTableDensitySelector').value;
        const table = document.querySelector('.modules-table');
        if (table) {
            table.className = `table-container modules-table ${density}`;
        }
    }

    // Form Handlers
    function setupFormHandlers() {
        // Create Module Form
        const createForm = document.getElementById('createModuleForm');
        if (createForm) {
            createForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = {
                    module_number: parseFloat(document.getElementById('moduleNumber').value),
                    title: document.getElementById('moduleTitle').value.trim(),
                    description: document.getElementById('moduleDescription').value.trim(),
                    estimated_hours: parseInt(document.getElementById('moduleHours').value) || null
                };
                
                // Validation
                if (!formData.title) {
                    showError('Module title is required');
                    return;
                }
                
                fetch('/admin/api/learning-modules', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSuccess('Module created successfully');
                        closeCreateModuleModal();
                        loadModulesData();
                        loadModulesForDropdown(); // Refresh dropdown
                    } else {
                        showError(data.message || 'Failed to create module');
                    }
                })
                .catch(error => {
                    console.error('Error creating module:', error);
                    showError('Failed to create module');
                });
            });
        }
        
        // Edit Module Form
        const editForm = document.getElementById('editModuleForm');
        if (editForm) {
            editForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const moduleId = document.getElementById('editModuleId').value;
                const formData = {
                    module_number: parseFloat(document.getElementById('editModuleNumber').value),
                    title: document.getElementById('editModuleTitle').value.trim(),
                    description: document.getElementById('editModuleDescription').value.trim(),
                    estimated_hours: parseInt(document.getElementById('editModuleHours').value) || null,
                    is_active: document.getElementById('editModuleStatus').value === '1'
                };
                
                // Validation
                if (!formData.title) {
                    showError('Module title is required');
                    return;
                }
                
                fetch(`/admin/api/learning-modules/${moduleId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSuccess('Module updated successfully');
                        closeEditModuleModal();
                        loadModulesData();
                        loadModulesForDropdown(); // Refresh dropdown
                    } else {
                        showError(data.message || 'Failed to update module');
                    }
                })
                .catch(error => {
                    console.error('Error updating module:', error);
                    showError('Failed to update module');
                });
            });
        }
        
        // Upload Video Form
        const uploadForm = document.getElementById('uploadVideoForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('videoFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    showError('Please select a video file');
                    return;
                }
                
                if (!validateVideoFile(file)) {
                    return;
                }
                
                const formData = new FormData();
                formData.append('video_file', file);
                formData.append('module_id', document.getElementById('videoModule').value);
                formData.append('submodule_id', document.getElementById('videoSubmodule').value);
                formData.append('title', document.getElementById('videoTitle').value.trim());
                formData.append('description', document.getElementById('videoDescription').value.trim());
                formData.append('sequence_order', document.getElementById('videoSequence').value);
                
                // Validation
                if (!formData.get('module_id')) {
                    showError('Please select a module');
                    return;
                }
                
                if (!formData.get('submodule_id')) {
                    showError('Please select a submodule');
                    return;
                }
                
                if (!formData.get('title')) {
                    showError('Video title is required');
                    return;
                }
                
                // Show progress
                const progressDiv = document.getElementById('upload-progress');
                const progressBar = document.getElementById('progress-bar');
                if (progressDiv) progressDiv.style.display = 'block';
                
                const xhr = new XMLHttpRequest();
                
                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        if (progressBar) {
                            progressBar.style.width = percentComplete + '%';
                            progressBar.textContent = Math.round(percentComplete) + '%';
                        }
                    }
                });
                
                xhr.addEventListener('load', function() {
                    if (progressDiv) progressDiv.style.display = 'none';
                    
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            showSuccess('Video uploaded successfully');
                            closeUploadVideoModal();
                            loadModulesData(); // Refresh table to show updated video counts
                        } else {
                            showError(response.message || 'Failed to upload video');
                        }
                    } catch (error) {
                        showError('Failed to parse server response');
                    }
                });
                
                xhr.addEventListener('error', function() {
                    if (progressDiv) progressDiv.style.display = 'none';
                    showError('Failed to upload video');
                });
                
                xhr.open('POST', '/admin/api/upload-video');
                xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
                xhr.send(formData);
            });
        }
    }

    // Utility functions
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    function showSuccess(message) {
        // Use existing admin flash message system or create toast
        console.log('Success:', message);
        
        // Create a temporary success message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 11000;
            padding: 15px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }

    function showError(message) {
        // Use existing admin flash message system or create toast
        console.error('Error:', message);
        
        // Create a temporary error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 11000;
            padding: 15px;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    // NEW FUNCTIONS FOR ENHANCED UPLOAD & EXPORT FUNCTIONALITY
    
    function exportContentModal() {
        const modal = document.getElementById('exportContentModal');
        if (modal) {
            modal.style.display = 'flex';
            loadModulesForExport();
            setupExportFormHandlers();
        }
    }

    function closeExportContentModal() {
        const modal = document.getElementById('exportContentModal');
        if (modal) modal.style.display = 'none';
    }

    function switchUploadTab(tabName) {
        // Hide all sections
        const sections = document.querySelectorAll('.upload-section');
        sections.forEach(section => section.style.display = 'none');
        
        // Show selected section
        const targetSection = document.getElementById(`upload-section-${tabName}`);
        if (targetSection) targetSection.style.display = 'block';
        
        // Update tab appearance
        const tabs = document.querySelectorAll('.upload-tab');
        tabs.forEach(tab => {
            tab.style.background = '#f8f9fa';
            tab.style.borderBottom = '1px solid #e0e0e0';
            tab.style.zIndex = '0';
        });
        
        const activeTab = document.getElementById(`upload-tab-${tabName}`);
        if (activeTab) {
            activeTab.style.background = 'white';
            activeTab.style.borderBottom = 'none';
            activeTab.style.zIndex = '1';
        }
        
        // Load data for content tab if needed
        if (tabName === 'content') {
            loadModulesForContentUpload();
        }
    }

    function loadModulesForExport() {
        fetch('/admin/api/learning-modules')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('exportModule');
                if (select && data.modules) {
                    select.innerHTML = '<option value="">Select a module...</option>' +
                        data.modules.filter(module => module.is_active).map(module => 
                            `<option value="${module.id}">${module.module_number} - ${escapeHtml(module.title)}</option>`
                        ).join('');
                }
            })
            .catch(error => console.error('Error loading modules for export:', error));
    }

    function loadModulesForContentUpload() {
        fetch('/admin/api/learning-modules')
            .then(response => response.json())
            .then(data => {
                if (data.modules) {
                    // Load modules for YAML upload
                    const yamlSelect = document.getElementById('yamlModule');
                    if (yamlSelect) {
                        yamlSelect.innerHTML = '<option value="">Select a module...</option>' +
                            data.modules.filter(module => module.is_active).map(module => 
                                `<option value="${module.id}">${module.module_number} - ${escapeHtml(module.title)}</option>`
                            ).join('');
                    }
                    
                    // Load modules for markdown upload
                    const markdownSelect = document.getElementById('markdownModule');
                    if (markdownSelect) {
                        markdownSelect.innerHTML = '<option value="">Select a module...</option>' +
                            data.modules.filter(module => module.is_active).map(module => 
                                `<option value="${module.id}">${module.module_number} - ${escapeHtml(module.title)}</option>`
                            ).join('');
                        
                        // Setup change handler for markdown module
                        markdownSelect.addEventListener('change', loadSubmodulesForMarkdown);
                    }
                }
            })
            .catch(error => console.error('Error loading modules for content upload:', error));
    }

    function loadSubmodulesForMarkdown() {
        const moduleSelect = document.getElementById('markdownModule');
        const submoduleSelect = document.getElementById('markdownSubmodule');
        
        if (!moduleSelect || !submoduleSelect) return;
        
        const moduleId = moduleSelect.value;
        
        if (!moduleId) {
            submoduleSelect.innerHTML = '<option value="">First select a module...</option>';
            return;
        }
        
        fetch(`/admin/api/learning-modules/${moduleId}/submodules`)
            .then(response => response.json())
            .then(data => {
                if (data.submodules && data.submodules.length > 0) {
                    submoduleSelect.innerHTML = '<option value="">Select a submodule...</option>' +
                        data.submodules.map(submodule => 
                            `<option value="${submodule.id}">${submodule.submodule_number} - ${escapeHtml(submodule.title)}</option>`
                        ).join('');
                } else {
                    submoduleSelect.innerHTML = '<option value="">No submodules available</option>';
                }
            })
            .catch(error => {
                console.error('Error loading submodules:', error);
                submoduleSelect.innerHTML = '<option value="">Error loading submodules</option>';
            });
    }

    function setupExportFormHandlers() {
        // Handle export type change
        const exportTypeRadios = document.querySelectorAll('input[name="export_type"]');
        exportTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                const moduleSelection = document.getElementById('module-selection');
                if (this.value === 'module') {
                    moduleSelection.style.display = 'block';
                } else {
                    moduleSelection.style.display = 'none';
                }
            });
        });
        
        // Handle export form submission
        const exportForm = document.getElementById('exportContentForm');
        if (exportForm) {
            exportForm.addEventListener('submit', function(e) {
                e.preventDefault();
                handleExportSubmission();
            });
        }
    }

    function handleExportSubmission() {
        const exportType = document.querySelector('input[name="export_type"]:checked').value;
        const exportFormat = document.querySelector('input[name="export_format"]:checked').value;
        const moduleId = document.getElementById('exportModule').value;
        
        // Get include options
        const includeVideos = document.getElementById('include-videos').checked;
        const includeMarkdown = document.getElementById('include-markdown').checked;
        const includeYaml = document.getElementById('include-yaml').checked;
        const includeProgress = document.getElementById('include-progress').checked;
        
        // Validation
        if (exportType === 'module' && !moduleId) {
            showError('Please select a module to export');
            return;
        }
        
        // Build export URL
        const params = new URLSearchParams({
            type: exportType,
            format: exportFormat,
            include_videos: includeVideos,
            include_markdown: includeMarkdown,
            include_yaml: includeYaml,
            include_progress: includeProgress
        });
        
        if (exportType === 'module' && moduleId) {
            params.append('module_id', moduleId);
        }
        
        // Start download
        const downloadUrl = `/admin/api/export-content?${params.toString()}`;
        window.open(downloadUrl, '_blank');
        
        showSuccess('Export started - download will begin shortly');
        closeExportContentModal();
    }

    function setupContentUploadDropZones() {
        // Setup YAML drop zone
        setupDropZone('yaml-drop-zone', 'yamlFile', ['.yaml', '.yml'], updateYamlDropZoneText);
        
        // Setup Markdown drop zone
        setupDropZone('markdown-drop-zone', 'markdownFile', ['.md', '.yaml', '.yml'], updateMarkdownDropZoneText);
    }

    function setupDropZone(dropZoneId, fileInputId, acceptedExtensions, updateTextCallback) {
        const dropZone = document.getElementById(dropZoneId);
        const fileInput = document.getElementById(fileInputId);
        
        if (dropZone && fileInput) {
            dropZone.addEventListener('click', () => fileInput.click());
            
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#007bff';
                dropZone.style.transform = 'scale(1.02)';
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = dropZone.style.borderColor.includes('6f42c1') ? '#6f42c1' : '#007bff';
                dropZone.style.transform = 'scale(1)';
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = dropZone.style.borderColor.includes('6f42c1') ? '#6f42c1' : '#007bff';
                dropZone.style.transform = 'scale(1)';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    if (validateFileType(files[0], acceptedExtensions)) {
                        fileInput.files = files;
                        updateTextCallback(files[0].name);
                    }
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    if (validateFileType(e.target.files[0], acceptedExtensions)) {
                        updateTextCallback(e.target.files[0].name);
                    }
                }
            });
        }
    }

    function validateFileType(file, acceptedExtensions) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!acceptedExtensions.includes(extension)) {
            showError(`Invalid file type. Accepted types: ${acceptedExtensions.join(', ')}`);
            return false;
        }
        return true;
    }

    function updateYamlDropZoneText(filename) {
        const dropZone = document.getElementById('yaml-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-file-code fa-2x" style="color: #6f42c1; margin-bottom: 10px;"></i>
                <p style="margin: 0; color: #6f42c1; font-weight: bold;">${escapeHtml(filename)}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Click to change file</p>
            `;
        }
    }

    function updateMarkdownDropZoneText(filename) {
        const dropZone = document.getElementById('markdown-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-file-alt fa-2x" style="color: #007bff; margin-bottom: 10px;"></i>
                <p style="margin: 0; color: #007bff; font-weight: bold;">${escapeHtml(filename)}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Click to change file</p>
            `;
        }
    }

    function setupContentUploadForms() {
        // Module YAML Upload Form
        const yamlForm = document.getElementById('uploadModuleYamlForm');
        if (yamlForm) {
            yamlForm.addEventListener('submit', function(e) {
                e.preventDefault();
                handleModuleYamlUpload();
            });
        }
        
        // Markdown Content Upload Form
        const markdownForm = document.getElementById('uploadMarkdownForm');
        if (markdownForm) {
            markdownForm.addEventListener('submit', function(e) {
                e.preventDefault();
                handleMarkdownUpload();
            });
        }
    }

    function handleModuleYamlUpload() {
        const moduleId = document.getElementById('yamlModule').value;
        const fileInput = document.getElementById('yamlFile');
        
        if (!moduleId) {
            showError('Please select a module');
            return;
        }
        
        if (!fileInput.files[0]) {
            showError('Please select a YAML file');
            return;
        }
        
        const formData = new FormData();
        formData.append('yaml_file', fileInput.files[0]);
        
        fetch(`/admin/api/learning-modules/${moduleId}/upload-yaml`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Module YAML uploaded successfully');
                document.getElementById('uploadModuleYamlForm').reset();
                resetYamlDropZone();
            } else {
                showError(data.message || 'Failed to upload YAML file');
            }
        })
        .catch(error => {
            console.error('Error uploading YAML:', error);
            showError('Failed to upload YAML file');
        });
    }

    function handleMarkdownUpload() {
        const moduleId = document.getElementById('markdownModule').value;
        const submoduleId = document.getElementById('markdownSubmodule').value;
        const contentType = document.getElementById('markdownType').value;
        const fileInput = document.getElementById('markdownFile');
        
        if (!moduleId || !submoduleId || !contentType) {
            showError('Please fill in all required fields');
            return;
        }
        
        if (!fileInput.files[0]) {
            showError('Please select a content file');
            return;
        }
        
        const formData = new FormData();
        formData.append('content_file', fileInput.files[0]);
        formData.append('content_type', contentType);
        
        const endpoint = contentType === 'metadata' 
            ? `/admin/api/learning-submodules/${submoduleId}/upload-metadata`
            : `/admin/api/learning-submodules/${submoduleId}/upload-content`;
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`${contentType.charAt(0).toUpperCase() + contentType.slice(1)} content uploaded successfully`);
                document.getElementById('uploadMarkdownForm').reset();
                resetMarkdownDropZone();
            } else {
                showError(data.message || 'Failed to upload content file');
            }
        })
        .catch(error => {
            console.error('Error uploading content:', error);
            showError('Failed to upload content file');
        });
    }

    function resetYamlDropZone() {
        const dropZone = document.getElementById('yaml-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-file-code fa-2x" style="color: #6f42c1; margin-bottom: 10px;"></i>
                <p style="margin: 0; color: #6f42c1; font-weight: bold;">Drop module.yaml here or click to browse</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Supported: .yaml, .yml files</p>
            `;
        }
    }

    function resetMarkdownDropZone() {
        const dropZone = document.getElementById('markdown-drop-zone');
        if (dropZone) {
            dropZone.innerHTML = `
                <i class="fas fa-file-alt fa-2x" style="color: #007bff; margin-bottom: 10px;"></i>
                <p style="margin: 0; color: #007bff; font-weight: bold;">Drop content file here or click to browse</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Supported: .md, .yaml, .yml files</p>
            `;
        }
    }

    // Expose functions globally for HTML onclick handlers
    window.initializeLearningModules = initializeLearningModules;
    window.createNewModule = createNewModule;
    window.closeCreateModuleModal = closeCreateModuleModal;
    window.uploadVideoModal = uploadVideoModal;
    window.closeUploadVideoModal = closeUploadVideoModal;
    window.exportContentModal = exportContentModal;
    window.closeExportContentModal = closeExportContentModal;
    window.switchUploadTab = switchUploadTab;
    window.editModule = editModule;
    window.closeEditModuleModal = closeEditModuleModal;
    window.deleteModule = deleteModule;
    window.applyModuleFilters = applyModuleFilters;
    window.clearModuleFilters = clearModuleFilters;
    window.changeModuleTableDensity = changeModuleTableDensity;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Don't auto-initialize, wait for section to be shown
            console.log('Learning modules JS loaded');
        });
    } else {
        console.log('Learning modules JS loaded');
    }
})(window);