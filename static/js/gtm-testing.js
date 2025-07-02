/* static/js/gtm-testing.js */

/**
 * GTM Testing and Validation Utilities
 * This file provides testing functions to validate GTM implementation
 */

class GTMTester {
    constructor() {
        this.testResults = [];
        this.isDebugMode = window.location.hostname === 'localhost' || window.location.search.includes('gtm_debug=1');
    }
    
    /**
     * Run comprehensive GTM validation tests
     */
    runAllTests() {
        console.log('🧪 Starting GTM Integration Tests...');
        
        this.testResults = [];
        
        // Core GTM tests
        this.testGTMLoaded();
        this.testDataLayerExists();
        this.testGTMContainerID();
        this.testUserDataInDataLayer();
        this.testCookieConsentIntegration();
        
        // Event tracking tests
        this.testBasicEventTracking();
        this.testEnhancedEventTracking();
        this.testEcommerceTracking();
        
        // Analytics service tests
        this.testAnalyticsServiceIntegration();
        this.testEventQueueing();
        
        // Debug and reporting
        this.generateTestReport();
        
        return this.testResults;
    }
    
    /**
     * Test if GTM is properly loaded
     */
    testGTMLoaded() {
        const test = {
            name: 'GTM Container Loaded',
            passed: false,
            details: {}
        };
        
        // Check if GTM script is loaded
        const gtmScripts = document.querySelectorAll('script[src*="googletagmanager.com"]');
        test.details.scriptFound = gtmScripts.length > 0;
        
        // Check if dataLayer exists
        test.details.dataLayerExists = window.dataLayer !== undefined;
        
        // Check if GTM container ID is set
        test.details.containerIdSet = window.gtmContainerId !== undefined;
        
        // Check if gtag function exists
        test.details.gtagExists = typeof window.gtag === 'function';
        
        test.passed = test.details.scriptFound && test.details.dataLayerExists && test.details.containerIdSet;
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test dataLayer structure and content
     */
    testDataLayerExists() {
        const test = {
            name: 'DataLayer Structure',
            passed: false,
            details: {}
        };
        
        if (window.dataLayer) {
            test.details.isArray = Array.isArray(window.dataLayer);
            test.details.length = window.dataLayer.length;
            test.details.hasGTMStart = window.dataLayer.some(item => item['gtm.start']);
            test.details.recentEvents = window.dataLayer.slice(-5).map(item => item.event || 'no-event');
            
            test.passed = test.details.isArray && test.details.hasGTMStart;
        } else {
            test.details.error = 'dataLayer not found';
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test GTM container ID configuration
     */
    testGTMContainerID() {
        const test = {
            name: 'GTM Container ID',
            passed: false,
            details: {}
        };
        
        test.details.containerIdExists = window.gtmContainerId !== undefined;
        test.details.containerId = window.gtmContainerId;
        test.details.formatValid = /^GTM-[A-Z0-9]+$/.test(window.gtmContainerId || '');
        test.details.expectedContainer = 'GTM-M26JWCMT';
        test.details.matchesExpected = window.gtmContainerId === 'GTM-M26JWCMT';
        
        test.passed = test.details.containerIdExists && test.details.formatValid;
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test user data in dataLayer
     */
    testUserDataInDataLayer() {
        const test = {
            name: 'User Data in DataLayer',
            passed: false,
            details: {}
        };
        
        if (window.currentUser) {
            test.details.userObjectExists = true;
            test.details.hasUserId = window.currentUser.id !== undefined;
            test.details.hasSubscriptionTier = window.currentUser.subscriptionTier !== undefined;
            test.details.hasLevel = window.currentUser.level !== undefined;
            
            // Check if user data was pushed to dataLayer
            const userDataEvent = window.dataLayer?.find(item => item.event === 'user_data_ready');
            test.details.userDataPushed = userDataEvent !== undefined;
            test.details.userDataContent = userDataEvent;
            
            test.passed = test.details.userObjectExists && test.details.userDataPushed;
        } else {
            test.details.userObjectExists = false;
            test.details.reason = 'User not logged in or data not available';
            test.passed = true; // This is okay for anonymous users
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test cookie consent integration
     */
    testCookieConsentIntegration() {
        const test = {
            name: 'Cookie Consent Integration',
            passed: false,
            details: {}
        };
        
        test.details.cookieConsentExists = window.cookieConsent !== undefined;
        test.details.hasPreferences = window.cookieConsent?.currentPreferences !== undefined;
        test.details.analyticsConsent = window.cookieConsent?.currentPreferences?.analytics;
        test.details.gtmLoadedBasedOnConsent = window.gtmLoaded !== undefined;
        
        // Test consent event listener
        test.details.hasConsentListener = true; // We can't easily test this
        
        test.passed = test.details.cookieConsentExists && (test.details.analyticsConsent ? test.details.gtmLoadedBasedOnConsent : true);
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test basic event tracking
     */
    testBasicEventTracking() {
        const test = {
            name: 'Basic Event Tracking',
            passed: false,
            details: {}
        };
        
        try {
            // Test gtag event
            if (window.gtag) {
                window.gtag('event', 'test_event', {
                    'test_parameter': 'test_value',
                    'event_category': 'testing'
                });
                test.details.gtagTest = 'success';
            } else {
                test.details.gtagTest = 'gtag not available';
            }
            
            // Test dataLayer push
            if (window.dataLayer) {
                window.dataLayer.push({
                    'event': 'test_datalayer_event',
                    'test_parameter': 'test_value'
                });
                test.details.dataLayerTest = 'success';
            }
            
            test.passed = test.details.gtagTest === 'success' || test.details.dataLayerTest === 'success';
            
        } catch (error) {
            test.details.error = error.message;
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test enhanced event tracking
     */
    testEnhancedEventTracking() {
        const test = {
            name: 'Enhanced Event Tracking',
            passed: false,
            details: {}
        };
        
        try {
            // Test enhanced events class
            test.details.enhancedEventsExists = window.gtmEnhancedEvents !== undefined;
            test.details.gtmHelperExists = window.gtmHelper !== undefined;
            
            // Test convenience functions
            test.details.trackGTMEventExists = typeof window.trackGTMEvent === 'function';
            test.details.trackEnhancedEventExists = typeof window.trackEnhancedEvent === 'function';
            
            if (window.trackGTMEvent) {
                window.trackGTMEvent('test_enhanced_event', {
                    'category': 'testing',
                    'value': 1
                });
                test.details.enhancedEventTest = 'success';
            }
            
            test.passed = test.details.enhancedEventsExists && test.details.trackGTMEventExists;
            
        } catch (error) {
            test.details.error = error.message;
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test ecommerce tracking
     */
    testEcommerceTracking() {
        const test = {
            name: 'Ecommerce Tracking',
            passed: false,
            details: {}
        };
        
        try {
            test.details.trackPurchaseExists = typeof window.trackPurchase === 'function';
            test.details.trackSubscriptionExists = typeof window.trackSubscriptionEvent === 'function';
            
            if (window.trackPurchase) {
                // Test purchase tracking (with test data)
                window.trackPurchase({
                    transactionId: 'test_' + Date.now(),
                    value: 149,
                    planId: 'premium',
                    planName: 'Premium Plan',
                    fromTier: 'free',
                    toTier: 'premium'
                });
                test.details.purchaseTest = 'success';
            }
            
            test.passed = test.details.trackPurchaseExists && test.details.trackSubscriptionExists;
            
        } catch (error) {
            test.details.error = error.message;
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test analytics service integration
     */
    testAnalyticsServiceIntegration() {
        const test = {
            name: 'Analytics Service Integration',
            passed: false,
            details: {}
        };
        
        test.details.analyticsServiceExists = window.analyticsService !== undefined;
        test.details.isEnabled = window.analyticsService?.isEnabled;
        test.details.debugMode = window.analyticsService?.debugMode;
        test.details.eventQueueLength = window.analyticsService?.eventQueue?.length || 0;
        
        // Test if analytics service can send events
        if (window.analyticsService && window.analyticsService.sendEvent) {
            try {
                window.analyticsService.sendEvent('test_analytics_service', {
                    'test_parameter': 'test_value'
                });
                test.details.sendEventTest = 'success';
            } catch (error) {
                test.details.sendEventTest = error.message;
            }
        }
        
        test.passed = test.details.analyticsServiceExists;
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Test event queueing functionality
     */
    testEventQueueing() {
        const test = {
            name: 'Event Queueing',
            passed: false,
            details: {}
        };
        
        if (window.analyticsService) {
            test.details.queueExists = window.analyticsService.eventQueue !== undefined;
            test.details.initialQueueLength = window.analyticsService.eventQueue?.length || 0;
            test.details.processQueueMethodExists = typeof window.analyticsService.processEventQueue === 'function';
            
            test.passed = test.details.queueExists && test.details.processQueueMethodExists;
        } else {
            test.details.error = 'Analytics service not available';
        }
        
        this.testResults.push(test);
        this.logTest(test);
    }
    
    /**
     * Generate comprehensive test report
     */
    generateTestReport() {
        const passedTests = this.testResults.filter(test => test.passed).length;
        const totalTests = this.testResults.length;
        const successRate = (passedTests / totalTests * 100).toFixed(1);
        
        const report = {
            summary: {
                total_tests: totalTests,
                passed_tests: passedTests,
                failed_tests: totalTests - passedTests,
                success_rate: successRate + '%',
                timestamp: new Date().toISOString()
            },
            tests: this.testResults,
            recommendations: this.generateRecommendations()
        };
        
        console.log('📊 GTM Test Report:', report);
        
        // Store report globally for debugging
        window.gtmTestReport = report;
        
        return report;
    }
    
    /**
     * Generate recommendations based on test results
     */
    generateRecommendations() {
        const recommendations = [];
        
        this.testResults.forEach(test => {
            if (!test.passed) {
                switch (test.name) {
                    case 'GTM Container Loaded':
                        recommendations.push('GTM container may not be loading properly. Check network requests and cookie consent.');
                        break;
                    case 'DataLayer Structure':
                        recommendations.push('DataLayer is not properly initialized. Ensure GTM script loads before other tracking code.');
                        break;
                    case 'GTM Container ID':
                        recommendations.push('GTM container ID is missing or invalid. Check environment configuration.');
                        break;
                    case 'User Data in DataLayer':
                        recommendations.push('User data is not being pushed to dataLayer. Check user authentication and data flow.');
                        break;
                    case 'Cookie Consent Integration':
                        recommendations.push('Cookie consent integration may have issues. Verify consent management system.');
                        break;
                    default:
                        recommendations.push(`${test.name} failed. Check implementation details.`);
                }
            }
        });
        
        if (recommendations.length === 0) {
            recommendations.push('All tests passed! GTM integration is working correctly.');
        }
        
        return recommendations;
    }
    
    /**
     * Log individual test results
     */
    logTest(test) {
        const icon = test.passed ? '✅' : '❌';
        const method = test.passed ? 'log' : 'warn';
        
        console[method](`${icon} ${test.name}:`, test.details);
    }
    
    /**
     * Test specific GTM triggers and events
     */
    testGTMTriggers() {
        console.log('🎯 Testing GTM Triggers...');
        
        // Test page view trigger
        window.dataLayer.push({
            'event': 'test_page_view',
            'page_title': 'Test Page',
            'page_location': window.location.href
        });
        
        // Test custom event trigger
        window.dataLayer.push({
            'event': 'test_custom_event',
            'event_category': 'test',
            'event_action': 'trigger_test'
        });
        
        console.log('🎯 Trigger tests sent to dataLayer');
    }
}

// Initialize GTM tester
window.gtmTester = new GTMTester();

// Convenience functions for manual testing
window.testGTM = () => window.gtmTester.runAllTests();
window.testGTMTriggers = () => window.gtmTester.testGTMTriggers();

// Auto-run tests in debug mode
if (window.location.search.includes('gtm_debug=1')) {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            console.log('🧪 Auto-running GTM tests in debug mode...');
            window.testGTM();
        }, 2000);
    });
}

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GTMTester;
}
