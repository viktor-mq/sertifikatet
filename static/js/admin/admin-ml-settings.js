// static/js/admin/admin-ml-settings.js

/**
 * ML Settings Administration JavaScript
 * Handles ML dashboard functionality and admin controls
 */

// Initialize ML Settings section
function initializeMLSettings() {
    console.log('🤖 Initializing ML Settings section...');
    
    try {
        // Set up event listeners for ML controls
        setupMLEventListeners();
        
        // Initialize configuration sliders
        initializeConfigSliders();
        
        // Load initial ML data
        loadMLData();
    
    // Load current configuration
    loadMLConfiguration();
        
        console.log('✅ ML Settings section initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing ML Settings:', error);
    }
}

// Set up event listeners for ML controls
function setupMLEventListeners() {
    // Configuration checkboxes
    document.querySelectorAll('.config-item input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            console.log(`Config changed: ${this.name || 'unknown'} = ${this.checked}`);
            // Auto-save configuration changes
            debouncedSaveConfig();
        });
    });
    
    // Configuration select dropdowns
    document.querySelectorAll('.config-select').forEach(select => {
        select.addEventListener('change', function() {
            console.log(`Config changed: ${this.name || 'unknown'} = ${this.value}`);
            // Auto-save configuration changes
            debouncedSaveConfig();
        });
    });
}

// Initialize configuration sliders
function initializeConfigSliders() {
    document.querySelectorAll('.config-slider').forEach(slider => {
        // Update displayed value when slider changes
        slider.addEventListener('input', function() {
            const valueSpan = this.nextElementSibling;
            if (valueSpan && valueSpan.classList.contains('config-value')) {
                valueSpan.textContent = this.value;
            }
        });
        
        // Save configuration when slider changes
        slider.addEventListener('change', function() {
            console.log(`Slider changed: ${this.name || 'unknown'} = ${this.value}`);
            debouncedSaveConfig();
        });
    });
}

// Debounced save configuration function
let saveConfigTimeout;
function debouncedSaveConfig() {
    clearTimeout(saveConfigTimeout);
    saveConfigTimeout = setTimeout(() => {
        saveMLConfiguration();
    }, 1000); // Save after 1 second of no changes
}

// Load ML configuration settings
function loadMLConfiguration() {
    console.log('Loading ML configuration...');
    
    fetch('/admin/api/ml/config')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(config => {
            updateMLConfiguration(config);
            console.log('✅ ML configuration loaded successfully');
        })
        .catch(error => {
            console.error('❌ Error loading ML configuration:', error);
            // Don't show notification for config loading errors, as it's not critical
        });
}

// Update configuration form with loaded values
function updateMLConfiguration(config) {
    // Update sliders
    const learningRateSlider = document.querySelector('input[type="range"]:nth-of-type(1)');
    const adaptationSlider = document.querySelector('input[type="range"]:nth-of-type(2)');
    
    if (learningRateSlider && config.learning_rate !== undefined) {
        learningRateSlider.value = config.learning_rate;
        const valueSpan = learningRateSlider.nextElementSibling;
        if (valueSpan) valueSpan.textContent = config.learning_rate;
    }
    
    if (adaptationSlider && config.adaptation_strength !== undefined) {
        adaptationSlider.value = config.adaptation_strength;
        const valueSpan = adaptationSlider.nextElementSibling;
        if (valueSpan) valueSpan.textContent = config.adaptation_strength;
    }
    
    // Update checkboxes
    const checkboxes = document.querySelectorAll('.config-item input[type="checkbox"]');
    if (checkboxes.length >= 3) {
        if (config.collect_response_times !== undefined) checkboxes[0].checked = config.collect_response_times;
        if (config.track_confidence !== undefined) checkboxes[1].checked = config.track_confidence;
        if (config.analyze_patterns !== undefined) checkboxes[2].checked = config.analyze_patterns;
    }
    
    // Update select dropdown
    const frequencySelect = document.querySelector('.config-select');
    if (frequencySelect && config.update_frequency) {
        frequencySelect.value = config.update_frequency;
    }
}

// Load ML data and refresh dashboard
function loadMLData() {
    console.log('Loading ML data...');
    
    // Show loading state
    setMLLoadingState(true);
    
    // Simulate API call to get fresh ML data
    fetch('/admin/api/ml/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            updateMLDashboard(data);
            console.log('✅ ML data loaded successfully');
        })
        .catch(error => {
            console.error('❌ Error loading ML data:', error);
            showMLNotification('Error loading ML data: ' + error.message, 'error');
        })
        .finally(() => {
            setMLLoadingState(false);
        });
}

// Update ML dashboard with fresh data
function updateMLDashboard(data) {
    console.log('Updating dashboard with data:', data);
    console.log('Looking for element totalUsers:', document.getElementById('totalUsers'));
    // Update statistics
    if (data.stats) {
        updateElement('totalUsers', data.stats.total_users || 0);
        updateElement('activeProfiles', data.stats.active_profiles || 0);
        updateElement('mlSessions', data.stats.adaptive_sessions || 0);
        updateElement('algorithmVersion', `v${data.status.algorithm_version || '1.0'}`);
    }
    
    // Update status banner
    updateMLStatusBanner(data.status);
    
    // Update model performance cards
    if (data.model_performance) {
        updateModelPerformanceCards(data.model_performance);
    }
    
    // Update recent activity
    if (data.recent_activity) {
        updateRecentActivity(data.recent_activity);
    }
}

// Update ML status banner
function updateMLStatusBanner(status) {
    const banner = document.querySelector('.ml-status-container .alert');
    if (!banner || !status) return;
    
    if (status.ml_enabled) {
        banner.className = 'alert alert-success';
        banner.innerHTML = `
            <span style="margin-right: 10px;">✅</span>
            <div>
                <strong>ML System Active</strong>
                <span style="margin-left: 10px; font-size: 0.9em;">Algorithm v${status.algorithm_version}</span>
            </div>
        `;
    } else {
        banner.className = 'alert alert-warning';
        banner.innerHTML = `
            <span style="margin-right: 10px;">⚠️</span>
            <div>
                <strong>ML System Initializing</strong>
                <span style="margin-left: 10px; font-size: 0.9em;">More data needed for full personalization</span>
            </div>
        `;
    }
}

// Update model performance cards
function updateModelPerformanceCards(performance) {
    // Update difficulty model card
    if (performance.difficulty_model) {
        const card = document.querySelector('.model-card:nth-of-type(1) .model-metrics');
        if (card) {
            card.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <span>Accuracy:</span>
                    <strong style="color: #28a745;">${(performance.difficulty_model.accuracy * 100).toFixed(1)}%</strong>
                </div>
                <div style="margin-bottom: 10px;">
                    <span>Predictions Made:</span>
                    <strong>${performance.difficulty_model.predictions_count}</strong>
                </div>
                <div>
                    <span>Last Updated:</span>
                    <span style="font-size: 0.9em; color: #666;">${formatDateTime(performance.difficulty_model.last_updated)}</span>
                </div>
            `;
        }
    }
    
    // Update adaptive model card
    if (performance.adaptive_model) {
        const card = document.querySelector('.model-card:nth-of-type(2) .model-metrics');
        if (card) {
            card.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <span>Personalization Rate:</span>
                    <strong style="color: #007bff;">${(performance.adaptive_model.personalization_rate * 100).toFixed(1)}%</strong>
                </div>
                <div style="margin-bottom: 10px;">
                    <span>Active Users:</span>
                    <strong>${performance.adaptive_model.active_users}</strong>
                </div>
                <div>
                    <span>Improvement Avg:</span>
                    <strong style="color: #28a745;">+${(performance.adaptive_model.avg_improvement * 100).toFixed(1)}%</strong>
                </div>
            `;
        }
    }
    
    // Update question analytics card
    if (performance.question_model) {
        const card = document.querySelector('.model-card:nth-of-type(3) .model-metrics');
        if (card) {
            card.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <span>Questions Analyzed:</span>
                    <strong>${performance.question_model.questions_analyzed}</strong>
                </div>
                <div style="margin-bottom: 10px;">
                    <span>Difficulty Profiles:</span>
                    <strong>${performance.question_model.difficulty_profiles}</strong>
                </div>
                <div>
                    <span>Discrimination Power:</span>
                    <strong style="color: #17a2b8;">${performance.question_model.avg_discrimination.toFixed(2)}</strong>
                </div>
            `;
        }
    }
}

// Update recent activity list
function updateRecentActivity(activities) {
    const container = document.querySelector('.activity-list');
    if (!container) return;
    
    if (activities && activities.length > 0) {
        container.innerHTML = activities.map(activity => `
            <div class="activity-item" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-bottom: 8px; background: #f8f9fa; border-radius: 4px;">
                <div>
                    <strong>${escapeHtml(activity.action)}</strong>
                    <span style="margin-left: 10px; color: #666;">${escapeHtml(activity.details || '')}</span>
                </div>
                <span style="font-size: 0.9em; color: #999;">${formatTime(activity.timestamp)}</span>
            </div>
        `).join('');
    } else {
        container.innerHTML = `
            <div style="text-align: center; color: #666; padding: 20px;">
                <p>No recent ML activity</p>
                <small>System is ready for adaptive learning</small>
            </div>
        `;
    }
}

// Set ML loading state
function setMLLoadingState(loading) {
    const section = document.getElementById('mlSettings2Section');
    if (!section) return;
    
    if (loading) {
        section.style.opacity = '0.7';
        section.style.pointerEvents = 'none';
        
        // Add loading indicator if not exists
        if (!document.getElementById('mlLoadingIndicator')) {
            const indicator = document.createElement('div');
            indicator.id = 'mlLoadingIndicator';
            indicator.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 20px;
                border-radius: 8px;
                z-index: 9999;
            `;
            indicator.innerHTML = `
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; border: 2px solid #fff; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>
                    Loading ML data...
                </div>
            `;
            document.body.appendChild(indicator);
        }
    } else {
        section.style.opacity = '1';
        section.style.pointerEvents = 'auto';
        
        // Remove loading indicator
        const indicator = document.getElementById('mlLoadingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }
}

// Action button functions
function refreshMLData() {
    console.log('🔄 Refreshing ML data...');
    showMLNotification('Refreshing ML data...', 'info');
    loadMLData();
}

function exportMLInsights() {
    console.log('📊 Exporting ML insights...');
    
    setMLLoadingState(true);
    
    fetch('/admin/api/ml/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ml-insights-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMLNotification('ML insights exported successfully!', 'success');
    })
    .catch(error => {
        console.error('❌ Error exporting ML insights:', error);
        showMLNotification('Error exporting ML insights: ' + error.message, 'error');
    })
    .finally(() => {
        setMLLoadingState(false);
    });
}

function resetMLModels() {
    if (!confirm('Are you sure you want to reset all ML models? This action cannot be undone and will clear all learned patterns.')) {
        return;
    }
    
    console.log('⚙️ Resetting ML models...');
    setMLLoadingState(true);
    
    fetch('/admin/api/ml/reset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        showMLNotification('ML models reset successfully!', 'success');
        // Refresh the dashboard
        setTimeout(() => {
            loadMLData();
        }, 1000);
    })
    .catch(error => {
        console.error('❌ Error resetting ML models:', error);
        showMLNotification('Error resetting ML models: ' + error.message, 'error');
    })
    .finally(() => {
        setMLLoadingState(false);
    });
}

function showMLDiagnostics() {
    console.log('🔍 Showing ML diagnostics...');
    
    fetch('/admin/api/ml/diagnostics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            showMLDiagnosticsModal(data);
        })
        .catch(error => {
            console.error('❌ Error loading ML diagnostics:', error);
            showMLNotification('Error loading ML diagnostics: ' + error.message, 'error');
        });
}

function saveMLConfiguration() {
    console.log('💾 Saving ML configuration...');
    
    // Collect configuration data
    const config = {
        learning_rate: parseFloat(document.querySelector('input[type="range"]:nth-of-type(1)').value),
        adaptation_strength: parseFloat(document.querySelector('input[type="range"]:nth-of-type(2)').value),
        collect_response_times: document.querySelector('input[type="checkbox"]:nth-of-type(1)').checked,
        track_confidence: document.querySelector('input[type="checkbox"]:nth-of-type(2)').checked,
        analyze_patterns: document.querySelector('input[type="checkbox"]:nth-of-type(3)').checked,
        update_frequency: document.querySelector('.config-select').value
    };
    
    fetch('/admin/api/ml/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        showMLNotification('Configuration saved successfully!', 'success');
    })
    .catch(error => {
        console.error('❌ Error saving ML configuration:', error);
        showMLNotification('Error saving configuration: ' + error.message, 'error');
    });
}

// Show ML diagnostics modal
function showMLDiagnosticsModal(diagnostics) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 20px;
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;
    
    modal.innerHTML = `
        <h3 style="margin-top: 0; color: #333;">🔍 ML Diagnostics</h3>
        <div class="diagnostics-content">
            <div style="margin-bottom: 20px;">
                <h4>System Health</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px;">
                    <div>Status: <strong style="color: ${diagnostics.healthy ? '#28a745' : '#dc3545'};">${diagnostics.healthy ? 'Healthy' : 'Issues Detected'}</strong></div>
                    <div>Uptime: <strong>${diagnostics.uptime || 'Unknown'}</strong></div>
                    <div>Memory Usage: <strong>${diagnostics.memory_usage || 'N/A'}</strong></div>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4>Model Status</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px;">
                    ${Object.entries(diagnostics.models || {}).map(([name, status]) => `
                        <div>${name}: <strong style="color: ${status.active ? '#28a745' : '#dc3545'};">${status.active ? 'Active' : 'Inactive'}</strong></div>
                    `).join('')}
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4>Performance Metrics</h4>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px;">
                    ${Object.entries(diagnostics.metrics || {}).map(([metric, value]) => `
                        <div>${metric}: <strong>${value}</strong></div>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <div style="text-align: right; margin-top: 20px;">
            <button onclick="this.closest('.modal-overlay').remove()" class="btn btn-secondary">Close</button>
        </div>
    `;
    
    overlay.className = 'modal-overlay';
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
}

// Show ML notification
function showMLNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#bee5eb'};
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 9999;
        max-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${escapeHtml(message)}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 18px; color: inherit; cursor: pointer; margin-left: 10px;">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('no-NO') + ' ' + date.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' });
}

function formatTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' });
}

// Add CSS animation for notifications
if (!document.getElementById('mlSettingsStyles')) {
    const style = document.createElement('style');
    style.id = 'mlSettingsStyles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .config-slider {
            width: 100%;
            margin: 5px 0;
        }
        
        .config-value {
            font-weight: bold;
            color: #007bff;
            margin-left: 10px;
        }
        
        .ml-dashboard-container .analysis-card:hover,
        .ml-dashboard-container .model-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transition: box-shadow 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}

// Make functions globally available for inline onclick handlers
window.refreshMLData = refreshMLData;
window.exportMLInsights = exportMLInsights;
window.resetMLModels = resetMLModels;
window.showMLDiagnostics = showMLDiagnostics;
window.saveMLConfiguration = saveMLConfiguration;
