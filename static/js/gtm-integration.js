/* static/js/gtm-integration.js */

/**
 * Google Tag Manager Integration Helper
 * This file provides utilities for enhanced GTM integration and dataLayer management
 */

class GTMHelper {
    constructor() {
        this.isReady = false;
        this.init();
    }
    
    init() {
        // Wait for GTM to load
        window.addEventListener('gtmLoaded', () => {
            this.isReady = true;
            this.setupUserData();
            this.setupPageData();
        });
        
        // If GTM is already loaded
        if (window.gtmLoaded || window.dataLayer) {
            this.isReady = true;
            this.setupUserData();
            this.setupPageData();
        }
    }
    
    /**
     * Set up user data in dataLayer for enhanced targeting and analytics
     */
    setupUserData() {
        if (!window.currentUser || !window.dataLayer) return;
        
        window.dataLayer.push({
            'event': 'user_data_ready',
            'user_id': window.currentUser.id,
            'user_subscription_tier': window.currentUser.subscriptionTier,
            'user_level': window.currentUser.level,
            'user_verified': window.currentUser.isVerified,
            'user_registration_date': window.currentUser.registrationDate,
            'user_type': window.currentUser.subscriptionTier === 'free' ? 'free_user' : 'premium_user'
        });
    }
    
    /**
     * Set up page-specific data
     */
    setupPageData() {
        if (!window.dataLayer) return;
        
        const pageSection = this.getPageSection();
        const pageData = {
            'event': 'page_data_ready',
            'page_section': pageSection,
            'page_type': this.getPageType(),
            'content_group': pageSection,
            'site_name': 'Sertifikatet'
        };
        
        // Add subscription-specific data for targeting
        if (window.currentUser) {
            pageData['content_access_level'] = window.currentUser.subscriptionTier;
        }
        
        window.dataLayer.push(pageData);
    }
    
    /**
     * Enhanced event tracking with better categorization
     */
    trackEnhancedEvent(eventName, eventData = {}) {
        if (!window.dataLayer) {
            console.warn('GTM dataLayer not available for event:', eventName);
            return;
        }
        
        const enhancedData = {
            'event': eventName,
            'event_category': eventData.category || this.getPageSection(),
            'event_timestamp': new Date().toISOString(),
            'page_section': this.getPageSection(),
            ...eventData
        };
        
        // Add user context if available
        if (window.currentUser) {
            enhancedData['user_tier'] = window.currentUser.subscriptionTier;
            enhancedData['user_level'] = window.currentUser.level;
        }
        
        window.dataLayer.push(enhancedData);
    }
    
    /**
     * Track ecommerce events for subscription conversions
     */
    trackPurchase(transactionData) {
        if (!window.dataLayer) return;
        
        window.dataLayer.push({
            'event': 'purchase',
            'ecommerce': {
                'transaction_id': transactionData.transactionId,
                'value': transactionData.value,
                'currency': 'NOK',
                'items': [{
                    'item_id': transactionData.planId,
                    'item_name': transactionData.planName,
                    'category': 'subscription',
                    'quantity': 1,
                    'price': transactionData.value
                }]
            },
            'user_tier_from': transactionData.fromTier,
            'user_tier_to': transactionData.toTier
        });
    }
    
    /**
     * Track subscription events (upgrades, cancellations)
     */
    trackSubscriptionEvent(eventType, subscriptionData) {
        const eventMap = {
            'upgrade': 'subscription_upgrade',
            'downgrade': 'subscription_downgrade', 
            'cancel': 'subscription_cancel',
            'renew': 'subscription_renew'
        };
        
        this.trackEnhancedEvent(eventMap[eventType] || eventType, {
            'category': 'subscription',
            'subscription_tier': subscriptionData.tier,
            'subscription_value': subscriptionData.value || 0,
            'billing_cycle': subscriptionData.billingCycle || 'monthly'
        });
    }
    
    /**
     * Track learning progress events
     */
    trackLearningProgress(progressData) {
        this.trackEnhancedEvent('learning_progress', {
            'category': 'education',
            'progress_type': progressData.type, // 'quiz_completed', 'video_watched', 'achievement_earned'
            'progress_value': progressData.value,
            'learning_category': progressData.learningCategory
        });
    }
    
    /**
     * Track ad interactions for revenue analytics
     */
    trackAdInteraction(adData) {
        this.trackEnhancedEvent('ad_interaction', {
            'category': 'advertising',
            'ad_type': adData.adType,
            'ad_placement': adData.placement,
            'interaction_type': adData.action, // 'impression', 'click', 'dismiss'
            'ad_provider': adData.provider || 'google_adsense'
        });
    }
    
    /**
     * Track conversion funnel steps
     */
    trackFunnelStep(stepName, stepData = {}) {
        this.trackEnhancedEvent('funnel_step', {
            'category': 'conversion',
            'funnel_step': stepName,
            'funnel_value': stepData.value || 0,
            'funnel_position': stepData.position || 1
        });
    }
    
    /**
     * Utility functions
     */
    getPageSection() {
        const path = window.location.pathname;
        if (path.includes('/quiz')) return 'quiz';
        if (path.includes('/video')) return 'video';
        if (path.includes('/game')) return 'game';
        if (path.includes('/auth')) return 'auth';
        if (path.includes('/admin')) return 'admin';
        if (path.includes('/payment')) return 'payment';
        if (path.includes('/subscription')) return 'subscription';
        if (path.includes('/gamification')) return 'gamification';
        return 'general';
    }
    
    getPageType() {
        const path = window.location.pathname;
        if (path === '/' || path === '/index') return 'homepage';
        if (path.includes('/login') || path.includes('/register')) return 'auth_page';
        if (path.includes('/profile')) return 'user_profile';
        if (path.includes('/dashboard')) return 'dashboard';
        if (path.includes('/pricing')) return 'pricing_page';
        return 'content_page';
    }
    
    /**
     * Set custom dimensions for advanced segmentation
     */
    setCustomDimensions(dimensions) {
        if (!window.dataLayer) return;
        
        window.dataLayer.push({
            'event': 'custom_dimensions',
            ...dimensions
        });
    }
}

// Initialize GTM Helper
window.gtmHelper = new GTMHelper();

// Backwards compatibility and convenience functions
window.trackGTMEvent = (eventName, eventData) => {
    window.gtmHelper.trackEnhancedEvent(eventName, eventData);
};

window.trackPurchase = (transactionData) => {
    window.gtmHelper.trackPurchase(transactionData);
};

window.trackSubscriptionEvent = (eventType, subscriptionData) => {
    window.gtmHelper.trackSubscriptionEvent(eventType, subscriptionData);
};

// Auto-track page views with enhanced data
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure GTM has loaded
    setTimeout(() => {
        if (window.dataLayer) {
            window.gtmHelper.trackEnhancedEvent('enhanced_page_view', {
                'category': 'navigation',
                'page_load_time': performance.now()
            });
        }
    }, 500);
});
