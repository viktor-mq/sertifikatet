/**
 * ML Settings Administration JavaScript
 * Handles ML dashboard functionality and admin controls
 */

// ML Configuration Batching System
const MLConfigBatcher = {
    pendingChanges: {},
    timer: null,
    batchDelay: 10000, // 10 seconds
    isActive: false,
    notificationElement: null,
    
    // Queue a configuration change for batch processing
    queueChange(settingKey, value) {
        console.log(`🔄 Queuing ML setting: ${settingKey} = ${value}`);
        
        // Add to pending changes
        this.pendingChanges[settingKey] = value;
        
        // Reset the timer
        this.resetTimer();
        
        // Update UI to show pending state
        this.updatePendingUI();
        
        // Show batching notification
        this.showBatchingNotification();
    },
    
    // Reset the batch timer
    resetTimer() {
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        this.timer = setTimeout(() => {
            this.sendBatch();
        }, this.batchDelay);
        
        this.isActive = true;
    },
    
    // Send all pending changes as a batch
    sendBatch() {
        if (Object.keys(this.pendingChanges).length === 0) {
            return;
        }
        
        console.log('📤 Sending ML configuration batch:', this.pendingChanges);
        
        // Show sending notification
        this.showSendingNotification();
        
        // Send the batch request
        fetch('/admin/api/ml/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(this.pendingChanges)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('✅ ML configuration batch successful');
                this.showSuccessNotification();
                
                // Process each successful change
                Object.entries(this.pendingChanges).forEach(([key, value]) => {
                    handleMLSettingUpdate(key, value);
                });
                
                // Refresh ML data
                loadMLData();
            } else {
                console.error('❌ ML configuration batch failed:', data.error);
                this.showErrorNotification(data.error);
                this.revertPendingChanges();
            }
        })
        .catch(error => {
            console.error('❌ Error sending ML configuration batch:', error);
            this.showErrorNotification('Network error occurred');
            this.revertPendingChanges();
        })
        .finally(() => {
            this.clearBatch();
        });
    },
    
    // Force send the batch immediately
    sendNow() {
        if (this.timer) {
            clearTimeout(this.timer);
        }
        this.sendBatch();
    },
    
    // Cancel all pending changes
    cancelBatch() {
        console.log('❌ Cancelling ML configuration batch');
        
        // Revert UI changes
        this.revertPendingChanges();
        
        // Clear the batch
        this.clearBatch();
        
        // Show cancellation notification
        this.showCancelNotification();
    },
    
    // Clear the current batch
    clearBatch() {
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
        
        this.pendingChanges = {};
        this.isActive = false;
        
        // Hide batch notification
        this.hideBatchingNotification();
        
        // Clear pending UI states
        this.clearPendingUI();
    },
    
    // Revert pending changes in the UI
    revertPendingChanges() {
        Object.entries(this.pendingChanges).forEach(([settingKey, attemptedValue]) => {
            const control = document.getElementById(settingKey) || 
                          document.querySelector(`[data-setting="${settingKey}"]`) ||
                          document.querySelector(`input[name="${settingKey}"]`);
            
            if (control) {
                if (control.type === 'checkbox') {
                    control.checked = !attemptedValue;
                } else if (control.type === 'range') {
                    // For sliders, we'd need to store the previous value somewhere
                    console.log(`Would revert ${settingKey} slider - need previous value`);
                }
            }
        });
    },
    
    // Update UI to show pending state
    updatePendingUI() {
        Object.keys(this.pendingChanges).forEach(settingKey => {
            const control = document.getElementById(settingKey) || 
                          document.querySelector(`[data-setting="${settingKey}"]`) ||
                          document.querySelector(`input[name="${settingKey}"]`);
            
            if (control) {
                control.classList.add('ml-setting-pending');
            }
        });
    },
    
    // Clear pending UI state
    clearPendingUI() {
        document.querySelectorAll('.ml-setting-pending').forEach(element => {
            element.classList.remove('ml-setting-pending');
        });
    },
    
    // Show batching notification with countdown and controls
    showBatchingNotification() {
        const changeCount = Object.keys(this.pendingChanges).length;
        const changeText = changeCount === 1 ? 'change' : 'changes';
        
        this.createNotificationElement();
        
        // Start countdown
        this.updateCountdown();
    },
    
    // Create the notification element
    createNotificationElement() {
        // Remove existing notification
        this.hideBatchingNotification();
        
        this.notificationElement = document.createElement('div');
        this.notificationElement.className = 'ml-batch-notification';
        this.notificationElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
            font-size: 14px;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(this.notificationElement);
    },
    
    // Update countdown display
    updateCountdown() {
        if (!this.notificationElement || !this.isActive) return;
        
        const changeCount = Object.keys(this.pendingChanges).length;
        const changeText = changeCount === 1 ? 'change' : 'changes';
        
        // Calculate remaining time
        const remainingMs = this.batchDelay;
        const remainingSeconds = Math.ceil(remainingMs / 1000);
        
        this.notificationElement.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">
                        ⏱️ ML Configuration Batch
                    </div>
                    <div style="font-size: 13px; opacity: 0.9;">
                        ${changeCount} ${changeText} queued • Sending in <span id="mlBatchCountdown">${remainingSeconds}</span>s
                    </div>
                </div>
                <div style="margin-left: 15px;">
                    <button onclick="MLConfigBatcher.sendNow()" style="
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.3);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        cursor: pointer;
                        margin-right: 5px;
                    ">Send Now</button>
                    <button onclick="MLConfigBatcher.cancelBatch()" style="
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.3);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        cursor: pointer;
                    ">Cancel</button>
                </div>
            </div>
        `;
        
        // Start real-time countdown
        this.startCountdownTimer();
    },
    
    // Start the visual countdown timer
    startCountdownTimer() {
        const startTime = Date.now();
        
        const countdownInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const remaining = Math.max(0, this.batchDelay - elapsed);
            const seconds = Math.ceil(remaining / 1000);
            
            const countdownElement = document.getElementById('mlBatchCountdown');
            if (countdownElement) {
                countdownElement.textContent = seconds;
            }
            
            // Stop when countdown reaches 0 or batch is no longer active
            if (remaining <= 0 || !this.isActive) {
                clearInterval(countdownInterval);
            }
        }, 100);
    },
    
    // Show sending notification
    showSendingNotification() {
        this.createNotificationElement();
        this.notificationElement.style.background = '#ffc107';
        this.notificationElement.style.color = '#212529';
        this.notificationElement.innerHTML = `
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; border: 2px solid #212529; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px;"></div>
                <div>
                    <div style="font-weight: bold;">🔄 Updating ML Configuration</div>
                    <div style="font-size: 13px; opacity: 0.8; margin-top: 2px;">Sending ${Object.keys(this.pendingChanges).length} changes...</div>
                </div>
            </div>
        `;
    },
    
    // Show success notification
    showSuccessNotification() {
        const changeCount = Object.keys(this.pendingChanges).length;
        const settingNames = Object.keys(this.pendingChanges).join(', ');
        
        this.createNotificationElement();
        this.notificationElement.style.background = '#28a745';
        this.notificationElement.innerHTML = `
            <div>
                <div style="font-weight: bold; margin-bottom: 5px;">✅ ML Configuration Updated</div>
                <div style="font-size: 13px; opacity: 0.9;">Successfully updated ${changeCount} settings</div>
                <div style="font-size: 11px; opacity: 0.7; margin-top: 3px;">${settingNames}</div>
            </div>
        `;
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            this.hideBatchingNotification();
        }, 4000);
    },
    
    // Show error notification
    showErrorNotification(error) {
        this.createNotificationElement();
        this.notificationElement.style.background = '#dc3545';
        this.notificationElement.innerHTML = `
            <div>
                <div style="font-weight: bold; margin-bottom: 5px;">❌ ML Configuration Failed</div>
                <div style="font-size: 13px; opacity: 0.9;">${error || 'Unknown error occurred'}</div>
                <div style="font-size: 11px; opacity: 0.7; margin-top: 3px;">Settings have been reverted</div>
            </div>
        `;
        
        // Auto-hide after 6 seconds
        setTimeout(() => {
            this.hideBatchingNotification();
        }, 6000);
    },
    
    // Show cancellation notification
    showCancelNotification() {
        this.createNotificationElement();
        this.notificationElement.style.background = '#6c757d';
        this.notificationElement.innerHTML = `
            <div>
                <div style="font-weight: bold; margin-bottom: 5px;">⏹️ Batch Cancelled</div>
                <div style="font-size: 13px; opacity: 0.9;">Pending ML configuration changes have been cancelled</div>
            </div>
        `;
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hideBatchingNotification();
        }, 3000);
    },
    
    // Hide batching notification
    hideBatchingNotification() {
        if (this.notificationElement) {
            this.notificationElement.style.opacity = '0';
            setTimeout(() => {
                if (this.notificationElement && this.notificationElement.parentNode) {
                    this.notificationElement.parentNode.removeChild(this.notificationElement);
                }
                this.notificationElement = null;
            }, 300);
        }
    }
};

// Page unload warning for pending changes
window.addEventListener('beforeunload', function(e) {
    if (MLConfigBatcher.isActive && Object.keys(MLConfigBatcher.pendingChanges).length > 0) {
        const message = 'You have unsaved ML configuration changes. They will be lost if you leave this page.';
        e.returnValue = message;
        return message;
    }
});

// Initialize ML Settings section
function initializeMLSettings() {
    console.log('🤖 Initializing ML Settings section...');
    
    try {
        // Set up event listeners for ML controls
        setupMLEventListeners();
        
        // Load initial ML data
        loadMLData();
    
        // Load current configuration
        loadMLConfiguration();
        
        // Initialize batching system
        console.log('📝 Batching system ready for ML configuration changes');
        
        console.log('✅ ML Settings section initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing ML Settings:', error);
    }
}

// NEW: Update ML Setting (now uses batching system)
function updateMLSetting(settingKey, value) {
    console.log(`🔄 ML Setting changed: ${settingKey} = ${value}`);
    
    // Use the batching system instead of immediate API call
    MLConfigBatcher.queueChange(settingKey, value);
}

// Handle ML setting updates in the UI
function handleMLSettingUpdate(settingKey, value) {
    if (settingKey === 'ml_system_enabled') {
        const featureControls = document.getElementById('mlFeatureControls');
        if (featureControls) {
            if (value) {
                // Enable the feature controls section
                featureControls.classList.remove('disabled');
                // Re-enable all individual checkboxes
                document.querySelectorAll('#mlFeatureControls input[type="checkbox"]').forEach(input => {
                    input.disabled = false;
                });
            } else {
                // Disable the feature controls section
                featureControls.classList.add('disabled');
                // Disable all individual checkboxes
                document.querySelectorAll('#mlFeatureControls input[type="checkbox"]').forEach(input => {
                    input.disabled = true;
                });
            }
        }
        
        // Update impact indicator
        updateMLImpactIndicator('mlMasterImpact', value);
        
        // Show impact warnings for critical changes
        showMLImpactWarning(settingKey, value);
        
        // NEW: Update dashboard sections when master toggle changes
        updateDashboardSections(value);
    }
    
    // Update real-time impact statistics
    updateRealTimeImpactStats();
    
    // Update slider values if this is a range setting
    if (settingKey === 'ml_learning_rate') {
        const valueDisplay = document.getElementById('mlLearningRateValue');
        if (valueDisplay) {
            valueDisplay.textContent = value.toFixed(2);
        }
    }
    
    if (settingKey === 'ml_adaptation_strength') {
        const valueDisplay = document.getElementById('mlAdaptationStrengthValue');
        if (valueDisplay) {
            valueDisplay.textContent = value.toFixed(1);
        }
    }
}

// NEW: Update dashboard sections when master toggle changes
function updateDashboardSections(mlSystemEnabled) {
    console.log(`🔄 Updating dashboard sections: ML System ${mlSystemEnabled ? 'Enabled' : 'Disabled'}`);
    
    // Calculate ML models count dynamically based on system state
    function calculateModelsActiveFromToggle(systemEnabled) {
        if (!systemEnabled) {
            return 0; // No models active when system disabled
        }
        
        // When system is enabled, check individual feature toggles to count active models
        let activeCount = 0;
        
        // Check if individual ML features are enabled (these control the models)
        const difficultyEnabled = document.getElementById('mlDifficultyPrediction')?.checked !== false;
        const adaptiveEnabled = document.getElementById('mlAdaptiveLearning')?.checked !== false;
        const skillTrackingEnabled = document.getElementById('mlSkillTracking')?.checked !== false;
        
        if (difficultyEnabled) activeCount++;
        if (adaptiveEnabled) activeCount++;
        if (skillTrackingEnabled) activeCount++; // This represents question_analyzer
        
        return activeCount;
    }
    
    // Update algorithm version card
    const algorithmVersionElement = document.getElementById('algorithmVersion');
    if (algorithmVersionElement) {
        if (mlSystemEnabled) {
            algorithmVersionElement.textContent = 'v1.2.3'; // Or fetch from API
        } else {
            algorithmVersionElement.textContent = 'Inactive';
        }
    }
    
    // Update status banner
    updateMLStatusBanner({ ml_enabled: mlSystemEnabled });
    
    // Update current impact stats based on master toggle state
    if (!mlSystemEnabled) {
        // When ML is disabled, set impact stats to reflect inactive state
        updateElement('usersAffected', 0);
        updateElement('profilesActive', 0);
        updateElement('modelsActive', 0);        // Show 0 models when ML disabled
        updateElement('fallbackUsage', '100%');  // Show 100% fallback usage
    } else {
        // When ML is enabled, refresh actual stats with dynamic models count
        updateRealTimeImpactStats();
        
        // Override models count with dynamic calculation
        const dynamicModelsCount = calculateModelsActiveFromToggle(true);
        updateElement('modelsActive', dynamicModelsCount);
    }
    
    // Trigger diagnostics refresh if the modal is open
    const diagnosticsModal = document.querySelector('.modal-overlay');
    if (diagnosticsModal) {
        // Refresh diagnostics data if modal is currently open
        showMLDiagnostics();
    }
}

// Update ML impact indicator
function updateMLImpactIndicator(elementId, enabled) {
    const indicator = document.getElementById(elementId);
    if (indicator) {
        indicator.classList.remove('enabled', 'disabled', 'warning');
        if (enabled) {
            indicator.classList.add('enabled');
            indicator.textContent = 'Enabled';
        } else {
            indicator.classList.add('disabled');
            indicator.textContent = 'Disabled';
        }
    }
}

// Show impact warning for critical ML changes
function showMLImpactWarning(settingKey, value) {
    const warningsContainer = document.getElementById('mlImpactWarnings');
    if (!warningsContainer) return;
    
    let warningHtml = '';
    
    if (settingKey === 'ml_system_enabled' && !value) {
        warningHtml = `
            <div class="alert alert-warning" style="margin: 10px 0; padding: 12px; border-radius: 6px; border-left: 4px solid #ffc107;">
                <strong>⚠️ Impact Warning:</strong> Disabling the ML system will affect all users. 
                Questions will be selected using the fallback mode instead of personalized recommendations.
            </div>`;
    } else if (settingKey === 'ml_adaptive_learning' && !value) {
        warningHtml = `
            <div class="alert alert-info" style="margin: 10px 0; padding: 12px; border-radius: 6px; border-left: 4px solid #007bff;">
                <strong>ℹ️ Note:</strong> Adaptive question selection is now disabled. 
                Users will receive questions based on the fallback mode.
            </div>`;
    }
    
    warningsContainer.innerHTML = warningHtml;
    
    // Auto-hide warning after 10 seconds
    if (warningHtml) {
        setTimeout(() => {
            warningsContainer.innerHTML = '';
        }, 10000);
    }
}

// Update real-time impact statistics
function updateRealTimeImpactStats() {
    // This would normally fetch from an API endpoint
    // For now, we'll simulate the update
    setTimeout(() => {
        fetch('/admin/api/ml/status')
            .then(response => response.json())
            .then(data => {
                if (data.stats) {
                    const stats = data.stats;
                    updateStatElement('usersAffected', stats.users_using_ml || 0);
                    updateStatElement('profilesActive', stats.active_profiles || 0);
                    updateStatElement('modelsActive', stats.models_active || 0);
                    updateStatElement('fallbackUsage', stats.fallback_usage || 0);
                }
            })
            .catch(error => {
                console.warn('Could not update impact stats:', error);
            });
    }, 1000);
}

// Helper function to update stat elements
function updateStatElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// Show ML update progress (legacy - now used by other functions)
function showMLUpdateProgress(settingKey, isLoading) {
    // You could show spinners or loading states here
    console.log(`${settingKey} update progress: ${isLoading ? 'loading' : 'complete'}`);
}

// Set up event listeners for ML controls
function setupMLEventListeners() {
    // Configuration checkboxes
    document.querySelectorAll('.config-item input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            console.log(`Config changed: ${this.name || this.id || 'unknown'} = ${this.checked}`);
            
            // Use the batching system for checkbox changes
            const settingKey = this.id || this.name;
            if (settingKey) {
                updateMLSetting(settingKey, this.checked);
            }
        });
    });
    
    // Configuration select dropdowns
    document.querySelectorAll('.config-select').forEach(select => {
        select.addEventListener('change', function() {
            console.log(`Config changed: ${this.name || this.id || 'unknown'} = ${this.value}`);
            
            // Use the batching system for select changes
            const settingKey = this.id || this.name;
            if (settingKey) {
                updateMLSetting(settingKey, this.value);
            }
        });
    });
    
    // ML-specific sliders with proper IDs
    setupMLSliders();
}

// Initialize ML-specific sliders
function setupMLSliders() {
    // Learning Rate slider
    const learningRateSlider = document.getElementById('mlLearningRate');
    if (learningRateSlider) {
        // Update display value on input
        learningRateSlider.addEventListener('input', function() {
            const valueDisplay = document.getElementById('mlLearningRateValue');
            if (valueDisplay) {
                valueDisplay.textContent = parseFloat(this.value).toFixed(2);
            }
        });
        
        // Save to backend on change (when user releases slider)
        learningRateSlider.addEventListener('change', function() {
            const value = parseFloat(this.value);
            console.log(`Learning rate changed: ${value}`);
            updateMLSetting('ml_learning_rate', value);
        });
    }
    
    // Adaptation Strength slider
    const adaptationSlider = document.getElementById('mlAdaptationStrength');
    if (adaptationSlider) {
        // Update display value on input
        adaptationSlider.addEventListener('input', function() {
            const valueDisplay = document.getElementById('mlAdaptationStrengthValue');
            if (valueDisplay) {
                valueDisplay.textContent = parseFloat(this.value).toFixed(1);
            }
        });
        
        // Save to backend on change (when user releases slider)
        adaptationSlider.addEventListener('change', function() {
            const value = parseFloat(this.value);
            console.log(`Adaptation strength changed: ${value}`);
            updateMLSetting('ml_adaptation_strength', value);
        });
    }
    
    // Generic slider handler for any additional sliders
    document.querySelectorAll('input[type="range"][data-ml-setting]').forEach(slider => {
        const settingKey = slider.getAttribute('data-ml-setting');
        const valueDisplayId = slider.getAttribute('data-value-display');
        
        // Update display value on input
        slider.addEventListener('input', function() {
            if (valueDisplayId) {
                const valueDisplay = document.getElementById(valueDisplayId);
                if (valueDisplay) {
                    const precision = slider.step && slider.step.includes('.') ? 
                        slider.step.split('.')[1].length : 0;
                    valueDisplay.textContent = parseFloat(this.value).toFixed(precision);
                }
            }
        });
        
        // Save to backend on change
        slider.addEventListener('change', function() {
            const value = parseFloat(this.value);
            console.log(`ML slider changed: ${settingKey} = ${value}`);
            updateMLSetting(settingKey, value);
        });
    });
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

// Helper function to convert snake_case to camelCase
function snakeToCamel(str) {
    return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
}

// Update configuration form with loaded values
function updateMLConfiguration(config) {
    console.log('Updating ML configuration with:', config);
    
    // Define the mapping of API keys to their corresponding elements
    const toggleMappings = {
        'ml_system_enabled': 'mlSystemEnabled',
        'ml_adaptive_learning': 'mlAdaptiveLearning', 
        'ml_skill_tracking': 'mlSkillTracking',
        'ml_difficulty_prediction': 'mlDifficultyPrediction',
        'ml_data_collection': 'mlDataCollection',
        'ml_model_retraining': 'mlModelRetraining'
    };
    
    // Update toggle switches
    Object.entries(toggleMappings).forEach(([apiKey, elementId]) => {
        if (config[apiKey] !== undefined) {
            const toggle = document.getElementById(elementId);
            if (toggle) {
                toggle.checked = config[apiKey];
                console.log(`✅ Updated ${elementId}:`, config[apiKey]);
            } else {
                console.warn(`❌ Toggle ${elementId} not found`);
            }
        }
    });
    
    // Update sliders using correct property names and element IDs
    if (config.ml_learning_rate !== undefined) {
        const learningRateSlider = document.getElementById('mlLearningRate');
        if (learningRateSlider) {
            learningRateSlider.value = config.ml_learning_rate;
            // Update display value if it exists
            const valueDisplay = document.getElementById('mlLearningRateValue');
            if (valueDisplay) {
                valueDisplay.textContent = config.ml_learning_rate.toFixed(2);
            }
            console.log('✅ Updated learning rate slider:', config.ml_learning_rate);
        } else {
            console.warn('❌ Learning rate slider not found');
        }
    }
    
    if (config.ml_adaptation_strength !== undefined) {
        const adaptationSlider = document.getElementById('mlAdaptationStrength');
        if (adaptationSlider) {
            adaptationSlider.value = config.ml_adaptation_strength;
            // Update display value if it exists
            const valueDisplay = document.getElementById('mlAdaptationStrengthValue');
            if (valueDisplay) {
                valueDisplay.textContent = config.ml_adaptation_strength.toFixed(1);
            }
            console.log('✅ Updated adaptation strength slider:', config.ml_adaptation_strength);
        } else {
            console.warn('❌ Adaptation strength slider not found');
        }
    }
    
    // Update fallback mode dropdown if it exists
    if (config.ml_fallback_mode !== undefined) {
        const fallbackSelect = document.querySelector('select[name="fallback_mode"]') || 
                              document.getElementById('fallbackMode') ||
                              document.getElementById('mlFallbackMode');
        if (fallbackSelect) {
            fallbackSelect.value = config.ml_fallback_mode;
            console.log('✅ Updated fallback mode:', config.ml_fallback_mode);
        }
    }
    
    // Update model update frequency dropdown if it exists
    if (config.ml_update_frequency !== undefined) {
        const updateFrequencySelect = document.getElementById('mlUpdateFrequency');
        if (updateFrequencySelect) {
            updateFrequencySelect.value = config.ml_update_frequency;
            console.log('✅ Updated update frequency:', config.ml_update_frequency);
        }
    }
    
    // Update the other checkboxes if they exist in config
    const otherCheckboxes = {
        'collect_response_times': 'collectResponseTimes',
        'track_confidence': 'trackConfidence', 
        'analyze_patterns': 'analyzePatterns'
    };
    
    Object.entries(otherCheckboxes).forEach(([apiKey, elementId]) => {
        if (config[apiKey] !== undefined) {
            const checkbox = document.getElementById(elementId);
            if (checkbox) {
                checkbox.checked = config[apiKey];
                console.log(`✅ Updated ${elementId}:`, config[apiKey]);
            }
        }
    });
    
    // NEW: Apply master toggle dependency logic after loading configuration
    applyMasterToggleLogic(config);
    
    console.log('🎯 ML Configuration update complete');
}

// NEW: Apply master toggle dependency logic
function applyMasterToggleLogic(config) {
    console.log('🔒 Applying master toggle dependency logic...');
    
    const masterToggleEnabled = config && config.ml_system_enabled;
    const featureControls = document.getElementById('mlFeatureControls');
    
    if (featureControls) {
        if (masterToggleEnabled) {
            // Enable the feature controls section
            featureControls.classList.remove('disabled');
            // Enable all individual checkboxes
            document.querySelectorAll('#mlFeatureControls input[type="checkbox"]').forEach(input => {
                input.disabled = false;
            });
            console.log('✅ Individual features enabled (master toggle is ON)');
        } else {
            // Disable the feature controls section
            featureControls.classList.add('disabled');
            // Disable all individual checkboxes
            document.querySelectorAll('#mlFeatureControls input[type="checkbox"]').forEach(input => {
                input.disabled = true;
            });
            console.log('❌ Individual features disabled (master toggle is OFF)');
        }
    }
    
    // Update master impact indicator
    const masterImpact = document.getElementById('mlMasterImpact');
    if (masterImpact) {
        masterImpact.classList.remove('enabled', 'disabled', 'warning');
        if (masterToggleEnabled) {
            masterImpact.classList.add('enabled');
            masterImpact.textContent = 'Enabled';
        } else {
            masterImpact.classList.add('disabled');
            masterImpact.textContent = 'Disabled';
        }
    }
    
    // Update dashboard sections based on master toggle state
    updateDashboardSections(masterToggleEnabled);
    
    console.log(`🎯 Master toggle logic applied: ${masterToggleEnabled ? 'System Active' : 'System Inactive'}`);
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
    
    // Calculate ML models active count dynamically from model status
    function calculateMLModelsActive(status) {
        if (!status || !status.models) {
            // Fallback: check if ML is initialized from other status indicators
            if (status && status.ml_initialized) {
                return 3; // Default when ML is active but no detailed model info
            }
            return 0;
        }
        
        let activeCount = 0;
        const models = status.models;
        
        // Count individual active models (same logic as diagnostics)
        if (models.difficulty_prediction && models.difficulty_prediction.active) activeCount++;
        if (models.adaptive_learning && models.adaptive_learning.active) activeCount++;
        if (models.question_analyzer && models.question_analyzer.active) activeCount++;
        
        return activeCount;
    }
    
    // Update statistics
    if (data.stats) {
        updateElement('totalUsers', data.stats.total_users || 0);
        updateElement('activeProfiles', data.stats.active_profiles || 0);
        updateElement('mlSessions', data.stats.ml_sessions || 0);
        updateElement('algorithmVersion', data.stats.algorithm_version || 'v1.0');
        
        // Update the Current Impact elements with dynamic ML models count
        updateElement('usersAffected', data.stats.users_using_ml || 0);
        updateElement('profilesActive', data.stats.active_profiles || 0);
        
        // Use dynamic calculation for ML models count instead of static backend value
        const dynamicModelsActive = calculateMLModelsActive(data.status);
        updateElement('modelsActive', dynamicModelsActive);
        
        updateElement('fallbackUsage', data.stats.fallback_usage || 0);
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
    // Calculate total active models dynamically
    function calculateTotalActive(models) {
        if (!models) return 'No Data';
        
        let activeCount = 0;
        
        // Count individual active models
        if (models.difficulty_prediction && models.difficulty_prediction.active) activeCount++;
        if (models.adaptive_learning && models.adaptive_learning.active) activeCount++;
        if (models.question_analyzer && models.question_analyzer.active) activeCount++;
        
        return activeCount > 0 ? activeCount : 'Inactive';
    }
    
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
    
    // Calculate the dynamic total
    const totalActive = calculateTotalActive(diagnostics.models);
    
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
                    ${Object.entries(diagnostics.models || {}).filter(([name]) => name !== 'total_active').map(([name, status]) => `
                        <div>${name}: <strong style="color: ${status.active ? '#28a745' : '#dc3545'};">${status.active ? 'Active' : 'Inactive'}</strong></div>
                    `).join('')}
                    <div>total_active: <strong style="color: ${totalActive === 'Inactive' ? '#dc3545' : '#28a745'};">${totalActive}</strong></div>
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
        
        /* New styles for batching system */
        .ml-setting-pending {
            background-color: #fff3cd !important;
            border: 2px solid #ffc107 !important;
            box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.25) !important;
            transition: all 0.3s ease;
        }
        
        .ml-setting-pending::after {
            content: "⏱️";
            position: absolute;
            top: 50%;
            right: 8px;
            transform: translateY(-50%);
            font-size: 12px;
            opacity: 0.7;
        }
        
        .ml-batch-notification {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12) !important;
            backdrop-filter: blur(10px);
        }
        
        .ml-batch-notification button:hover {
            background: rgba(255,255,255,0.3) !important;
            transform: translateY(-1px);
            transition: all 0.2s ease;
        }
    `;
    document.head.appendChild(style);
}

// Make functions globally available for inline onclick handlers
window.refreshMLData = refreshMLData;
window.exportMLInsights = exportMLInsights;
window.resetMLModels = resetMLModels;
window.showMLDiagnostics = showMLDiagnostics;
