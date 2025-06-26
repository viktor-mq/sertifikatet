/* static/js/analytics-service.js */

class AnalyticsService {
    constructor() {
        this.isEnabled = false;
        this.debugMode = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        this.eventQueue = []; // Queue events if GA not loaded yet
        
        // Initialize when consent is given
        this.init();
    }
    
    init() {
        // Check if analytics is enabled via cookie consent
        window.addEventListener('cookiePreferencesApplied', (event) => {
            this.isEnabled = event.detail.analytics;
            
            if (this.isEnabled && window.gtag) {
                // Process queued events
                this.processEventQueue();
            }
        });
        
        // Check current state
        this.checkAnalyticsStatus();
    }
    
    checkAnalyticsStatus() {
        // Check if gtag is already available and user has consented
        if (window.gtag && window.cookieConsent) {
            this.isEnabled = window.cookieConsent.currentPreferences?.analytics || false;
        }
    }
    
    processEventQueue() {
        if (this.eventQueue.length > 0) {
            console.log(`Processing ${this.eventQueue.length} queued analytics events`);
            this.eventQueue.forEach(event => {
                this.sendEvent(event.name, event.parameters, true);
            });
            this.eventQueue = [];
        }
    }
    
    /**
     * Send analytics event
     * @param {string} eventName - The event name
     * @param {object} parameters - Event parameters
     * @param {boolean} skipQueue - Skip queueing if GA not available
     */
    sendEvent(eventName, parameters = {}, skipQueue = false) {
        // Add debug logging
        if (this.debugMode) {
            console.log('📊 Analytics Event:', eventName, parameters);
        }
        
        // If analytics not enabled, log and return
        if (!this.isEnabled) {
            if (this.debugMode) {
                console.log('📊 Analytics disabled - event not sent:', eventName);
            }
            return;
        }
        
        // If gtag not available, queue the event
        if (!window.gtag && !skipQueue) {
            this.eventQueue.push({ name: eventName, parameters });
            if (this.debugMode) {
                console.log('📊 Analytics not ready - event queued:', eventName);
            }
            return;
        }
        
        // Send the event
        if (window.gtag) {
            try {
                gtag('event', eventName, {
                    ...parameters,
                    // Add common parameters
                    timestamp: new Date().toISOString(),
                    page_location: window.location.href,
                    page_title: document.title
                });
                
                if (this.debugMode) {
                    console.log('📊 Analytics event sent:', eventName, parameters);
                }
            } catch (error) {
                console.error('Analytics error:', error);
            }
        }
    }
    
    // =====================================
    // USER LIFECYCLE EVENTS
    // =====================================
    
    trackUserRegistration(userData = {}) {
        this.sendEvent('user_registration', {
            method: userData.method || 'email',
            user_id: userData.userId,
            timestamp: userData.timestamp || new Date().toISOString()
        });
    }
    
    trackEmailVerification(userId) {
        this.sendEvent('email_verification_completed', {
            user_id: userId,
            verification_method: 'email'
        });
    }
    
    trackSubscriptionUpgrade(subscriptionData) {
        this.sendEvent('subscription_upgrade', {
            user_id: subscriptionData.userId,
            from_tier: subscriptionData.fromTier,
            to_tier: subscriptionData.toTier,
            plan_id: subscriptionData.planId,
            value: subscriptionData.priceNok,
            currency: 'NOK',
            transaction_id: subscriptionData.transactionId
        });
    }
    
    trackSubscriptionCancel(subscriptionData) {
        this.sendEvent('subscription_cancel', {
            user_id: subscriptionData.userId,
            tier: subscriptionData.tier,
            reason: subscriptionData.reason || 'unknown',
            days_subscribed: subscriptionData.daysSubscribed
        });
    }
    
    // =====================================
    // LEARNING ACTIVITY EVENTS
    // =====================================
    
    trackQuizStarted(quizData) {
        this.sendEvent('quiz_started', {
            user_id: quizData.userId,
            quiz_type: quizData.quizType, // 'practice', 'exam', 'adaptive'
            category: quizData.category,
            difficulty_level: quizData.difficultyLevel,
            session_id: quizData.sessionId
        });
    }
    
    trackQuizCompleted(quizResults) {
        this.sendEvent('quiz_completed', {
            user_id: quizResults.userId,
            session_id: quizResults.sessionId,
            quiz_type: quizResults.quizType,
            category: quizResults.category,
            score: quizResults.score,
            total_questions: quizResults.totalQuestions,
            correct_answers: quizResults.correctAnswers,
            time_spent_seconds: quizResults.timeSpentSeconds,
            passed: quizResults.passed,
            difficulty_level: quizResults.difficultyLevel
        });
    }
    
    trackVideoWatched(videoData) {
        this.sendEvent('video_watched', {
            user_id: videoData.userId,
            video_id: videoData.videoId,
            video_title: videoData.videoTitle,
            category: videoData.category,
            completion_percentage: videoData.completionPercentage,
            watch_time_seconds: videoData.watchTimeSeconds,
            total_duration_seconds: videoData.totalDurationSeconds,
            checkpoints_passed: videoData.checkpointsPassed
        });
    }
    
    trackAchievementEarned(achievementData) {
        this.sendEvent('achievement_earned', {
            user_id: achievementData.userId,
            achievement_id: achievementData.achievementId,
            achievement_name: achievementData.achievementName,
            category: achievementData.category,
            points_earned: achievementData.pointsEarned,
            level: achievementData.userLevel
        });
    }
    
    // =====================================
    // ENGAGEMENT EVENTS
    // =====================================
    
    trackStreakMilestone(streakData) {
        this.sendEvent('daily_streak_milestone', {
            user_id: streakData.userId,
            streak_days: streakData.streakDays,
            milestone_type: this.getStreakMilestoneType(streakData.streakDays)
        });
    }
    
    trackStudySessionCompleted(sessionData) {
        this.sendEvent('study_session_completed', {
            user_id: sessionData.userId,
            session_duration_minutes: Math.round(sessionData.durationSeconds / 60),
            activities_completed: sessionData.activitiesCompleted,
            xp_earned: sessionData.xpEarned,
            session_type: sessionData.sessionType // 'quiz', 'video', 'mixed'
        });
    }
    
    trackFeatureUsed(featureData) {
        this.sendEvent('feature_used', {
            user_id: featureData.userId,
            feature_name: featureData.featureName,
            feature_category: featureData.category, // 'ai_adaptive', 'playlist', 'premium'
            subscription_tier: featureData.subscriptionTier
        });
    }
    
    // =====================================
    // BUSINESS METRICS
    // =====================================
    
    trackConversionFunnel(conversionData) {
        this.sendEvent('conversion_funnel', {
            user_id: conversionData.userId,
            funnel_step: conversionData.step, // 'trial_started', 'payment_initiated', 'subscription_completed'
            from_tier: conversionData.fromTier,
            to_tier: conversionData.toTier,
            value: conversionData.value,
            currency: 'NOK'
        });
    }
    
    trackFeatureAdoption(adoptionData) {
        this.sendEvent('feature_adoption', {
            user_id: adoptionData.userId,
            feature_name: adoptionData.featureName,
            first_use: adoptionData.firstUse,
            subscription_tier: adoptionData.subscriptionTier,
            days_since_registration: adoptionData.daysSinceRegistration
        });
    }
    
    trackChurnIndicator(churnData) {
        this.sendEvent('churn_indicator', {
            user_id: churnData.userId,
            indicator_type: churnData.type, // 'low_activity', 'support_request', 'downgrade_attempt'
            days_since_last_activity: churnData.daysSinceLastActivity,
            subscription_tier: churnData.subscriptionTier,
            risk_score: churnData.riskScore
        });
    }
    
    // =====================================
    // HELPER METHODS
    // =====================================
    
    getStreakMilestoneType(days) {
        if (days >= 100) return 'centurion';
        if (days >= 50) return 'champion';
        if (days >= 30) return 'master';
        if (days >= 14) return 'expert';
        if (days >= 7) return 'committed';
        if (days >= 3) return 'consistent';
        return 'starter';
    }
    
    // Set user properties for segmentation
    setUserProperties(userProps) {
        if (!this.isEnabled || !window.gtag) return;
        
        gtag('config', 'G-353HJJCNYR', {
            user_properties: userProps
        });
    }
    
    // Page view tracking (automatic with enhanced data)
    trackPageView(pageData = {}) {
        this.sendEvent('page_view', {
            page_title: pageData.title || document.title,
            page_location: pageData.url || window.location.href,
            content_group1: pageData.section || this.getPageSection(),
            user_engagement_time: pageData.engagementTime
        });
    }
    
    getPageSection() {
        const path = window.location.pathname;
        if (path.includes('/quiz')) return 'quiz';
        if (path.includes('/video')) return 'video';
        if (path.includes('/auth')) return 'auth';
        if (path.includes('/admin')) return 'admin';
        if (path.includes('/payment')) return 'payment';
        return 'general';
    }
}

// Initialize global analytics service
window.analyticsService = new AnalyticsService();

// Backwards compatibility
window.trackEvent = (eventName, parameters) => {
    window.analyticsService.sendEvent(eventName, parameters);
};
