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
    testCookieConsentIntegration() {\n        const test = {\n            name: 'Cookie Consent Integration',\n            passed: false,\n            details: {}\n        };\n        \n        test.details.cookieConsentExists = window.cookieConsent !== undefined;\n        test.details.hasPreferences = window.cookieConsent?.currentPreferences !== undefined;\n        test.details.analyticsConsent = window.cookieConsent?.currentPreferences?.analytics;\n        test.details.gtmLoadedBasedOnConsent = window.gtmLoaded !== undefined;\n        \n        // Test consent event listener\n        test.details.hasConsentListener = true; // We can't easily test this\n        \n        test.passed = test.details.cookieConsentExists && (test.details.analyticsConsent ? test.details.gtmLoadedBasedOnConsent : true);\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Test basic event tracking\n     */\n    testBasicEventTracking() {\n        const test = {\n            name: 'Basic Event Tracking',\n            passed: false,\n            details: {}\n        };\n        \n        try {\n            // Test gtag event\n            if (window.gtag) {\n                window.gtag('event', 'test_event', {\n                    'test_parameter': 'test_value',\n                    'event_category': 'testing'\n                });\n                test.details.gtagTest = 'success';\n            } else {\n                test.details.gtagTest = 'gtag not available';\n            }\n            \n            // Test dataLayer push\n            if (window.dataLayer) {\n                window.dataLayer.push({\n                    'event': 'test_datalayer_event',\n                    'test_parameter': 'test_value'\n                });\n                test.details.dataLayerTest = 'success';\n            }\n            \n            test.passed = test.details.gtagTest === 'success' || test.details.dataLayerTest === 'success';\n            \n        } catch (error) {\n            test.details.error = error.message;\n        }\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Test enhanced event tracking\n     */\n    testEnhancedEventTracking() {\n        const test = {\n            name: 'Enhanced Event Tracking',\n            passed: false,\n            details: {}\n        };\n        \n        try {\n            // Test enhanced events class\n            test.details.enhancedEventsExists = window.gtmEnhancedEvents !== undefined;\n            test.details.gtmHelperExists = window.gtmHelper !== undefined;\n            \n            // Test convenience functions\n            test.details.trackGTMEventExists = typeof window.trackGTMEvent === 'function';\n            test.details.trackEnhancedEventExists = typeof window.trackEnhancedEvent === 'function';\n            \n            if (window.trackGTMEvent) {\n                window.trackGTMEvent('test_enhanced_event', {\n                    'category': 'testing',\n                    'value': 1\n                });\n                test.details.enhancedEventTest = 'success';\n            }\n            \n            test.passed = test.details.enhancedEventsExists && test.details.trackGTMEventExists;\n            \n        } catch (error) {\n            test.details.error = error.message;\n        }\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Test ecommerce tracking\n     */\n    testEcommerceTracking() {\n        const test = {\n            name: 'Ecommerce Tracking',\n            passed: false,\n            details: {}\n        };\n        \n        try {\n            test.details.trackPurchaseExists = typeof window.trackPurchase === 'function';\n            test.details.trackSubscriptionExists = typeof window.trackSubscriptionEvent === 'function';\n            \n            if (window.trackPurchase) {\n                // Test purchase tracking (with test data)\n                window.trackPurchase({\n                    transactionId: 'test_' + Date.now(),\n                    value: 149,\n                    planId: 'premium',\n                    planName: 'Premium Plan',\n                    fromTier: 'free',\n                    toTier: 'premium'\n                });\n                test.details.purchaseTest = 'success';\n            }\n            \n            test.passed = test.details.trackPurchaseExists && test.details.trackSubscriptionExists;\n            \n        } catch (error) {\n            test.details.error = error.message;\n        }\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Test analytics service integration\n     */\n    testAnalyticsServiceIntegration() {\n        const test = {\n            name: 'Analytics Service Integration',\n            passed: false,\n            details: {}\n        };\n        \n        test.details.analyticsServiceExists = window.analyticsService !== undefined;\n        test.details.isEnabled = window.analyticsService?.isEnabled;\n        test.details.debugMode = window.analyticsService?.debugMode;\n        test.details.eventQueueLength = window.analyticsService?.eventQueue?.length || 0;\n        \n        // Test if analytics service can send events\n        if (window.analyticsService && window.analyticsService.sendEvent) {\n            try {\n                window.analyticsService.sendEvent('test_analytics_service', {\n                    'test_parameter': 'test_value'\n                });\n                test.details.sendEventTest = 'success';\n            } catch (error) {\n                test.details.sendEventTest = error.message;\n            }\n        }\n        \n        test.passed = test.details.analyticsServiceExists;\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Test event queueing functionality\n     */\n    testEventQueueing() {\n        const test = {\n            name: 'Event Queueing',\n            passed: false,\n            details: {}\n        };\n        \n        if (window.analyticsService) {\n            test.details.queueExists = window.analyticsService.eventQueue !== undefined;\n            test.details.initialQueueLength = window.analyticsService.eventQueue?.length || 0;\n            test.details.processQueueMethodExists = typeof window.analyticsService.processEventQueue === 'function';\n            \n            test.passed = test.details.queueExists && test.details.processQueueMethodExists;\n        } else {\n            test.details.error = 'Analytics service not available';\n        }\n        \n        this.testResults.push(test);\n        this.logTest(test);\n    }\n    \n    /**\n     * Generate comprehensive test report\n     */\n    generateTestReport() {\n        const passedTests = this.testResults.filter(test => test.passed).length;\n        const totalTests = this.testResults.length;\n        const successRate = (passedTests / totalTests * 100).toFixed(1);\n        \n        const report = {\n            summary: {\n                total_tests: totalTests,\n                passed_tests: passedTests,\n                failed_tests: totalTests - passedTests,\n                success_rate: successRate + '%',\n                timestamp: new Date().toISOString()\n            },\n            tests: this.testResults,\n            recommendations: this.generateRecommendations()\n        };\n        \n        console.log('📊 GTM Test Report:', report);\n        \n        // Store report globally for debugging\n        window.gtmTestReport = report;\n        \n        return report;\n    }\n    \n    /**\n     * Generate recommendations based on test results\n     */\n    generateRecommendations() {\n        const recommendations = [];\n        \n        this.testResults.forEach(test => {\n            if (!test.passed) {\n                switch (test.name) {\n                    case 'GTM Container Loaded':\n                        recommendations.push('GTM container may not be loading properly. Check network requests and cookie consent.');\n                        break;\n                    case 'DataLayer Structure':\n                        recommendations.push('DataLayer is not properly initialized. Ensure GTM script loads before other tracking code.');\n                        break;\n                    case 'GTM Container ID':\n                        recommendations.push('GTM container ID is missing or invalid. Check environment configuration.');\n                        break;\n                    case 'User Data in DataLayer':\n                        recommendations.push('User data is not being pushed to dataLayer. Check user authentication and data flow.');\n                        break;\n                    case 'Cookie Consent Integration':\n                        recommendations.push('Cookie consent integration may have issues. Verify consent management system.');\n                        break;\n                    default:\n                        recommendations.push(`${test.name} failed. Check implementation details.`);\n                }\n            }\n        });\n        \n        if (recommendations.length === 0) {\n            recommendations.push('All tests passed! GTM integration is working correctly.');\n        }\n        \n        return recommendations;\n    }\n    \n    /**\n     * Log individual test results\n     */\n    logTest(test) {\n        const icon = test.passed ? '✅' : '❌';\n        const method = test.passed ? 'log' : 'warn';\n        \n        console[method](`${icon} ${test.name}:`, test.details);\n    }\n    \n    /**\n     * Test specific GTM triggers and events\n     */\n    testGTMTriggers() {\n        console.log('🎯 Testing GTM Triggers...');\n        \n        // Test page view trigger\n        window.dataLayer.push({\n            'event': 'test_page_view',\n            'page_title': 'Test Page',\n            'page_location': window.location.href\n        });\n        \n        // Test custom event trigger\n        window.dataLayer.push({\n            'event': 'test_custom_event',\n            'event_category': 'test',\n            'event_action': 'trigger_test'\n        });\n        \n        console.log('🎯 Trigger tests sent to dataLayer');\n    }\n}\n\n// Initialize GTM tester\nwindow.gtmTester = new GTMTester();\n\n// Convenience functions for manual testing\nwindow.testGTM = () => window.gtmTester.runAllTests();\nwindow.testGTMTriggers = () => window.gtmTester.testGTMTriggers();\n\n// Auto-run tests in debug mode\nif (window.location.search.includes('gtm_debug=1')) {\n    document.addEventListener('DOMContentLoaded', () => {\n        setTimeout(() => {\n            console.log('🧪 Auto-running GTM tests in debug mode...');\n            window.testGTM();\n        }, 2000);\n    });\n}\n\n// Export for external use\nif (typeof module !== 'undefined' && module.exports) {\n    module.exports = GTMTester;\n}"