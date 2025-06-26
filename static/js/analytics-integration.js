/* static/js/analytics-integration.js */

/**
 * Analytics Integration for Quiz and Video Systems
 * This file handles the integration between the quiz/video systems and analytics service
 */

// Quiz Analytics Integration
class QuizAnalytics {
    static trackQuizStarted(analyticsData) {
        if (window.analyticsService && analyticsData) {
            window.analyticsService.trackQuizStarted({
                userId: analyticsData.user_id,
                quizType: analyticsData.quiz_type,
                category: analyticsData.category,
                difficultyLevel: analyticsData.difficulty_level,
                sessionId: analyticsData.session_id
            });
        }
    }
    
    static trackQuizCompleted(analyticsData) {
        if (window.analyticsService && analyticsData) {
            window.analyticsService.trackQuizCompleted({
                userId: analyticsData.user_id,
                sessionId: analyticsData.session_id,
                quizType: analyticsData.quiz_type,
                category: analyticsData.category,
                score: analyticsData.score,
                totalQuestions: analyticsData.total_questions,
                correctAnswers: analyticsData.correct_answers,
                timeSpentSeconds: analyticsData.time_spent_seconds,
                passed: analyticsData.passed,
                difficultyLevel: analyticsData.difficulty_level
            });
        }
    }
}

// Video Analytics Integration  
class VideoAnalytics {
    static trackVideoWatched(analyticsData) {
        if (window.analyticsService && analyticsData) {
            window.analyticsService.trackVideoWatched({
                userId: analyticsData.user_id,
                videoId: analyticsData.video_id,
                videoTitle: analyticsData.video_title,
                category: analyticsData.category,
                completionPercentage: analyticsData.completion_percentage,
                watchTimeSeconds: analyticsData.watch_time_seconds,
                totalDurationSeconds: analyticsData.total_duration_seconds,
                checkpointsPassed: analyticsData.checkpoints_passed
            });
        }
    }
}

// Achievement Analytics Integration
class AchievementAnalytics {
    static trackAchievementEarned(analyticsData) {
        if (window.analyticsService && analyticsData) {
            // Handle single achievement or array of achievements
            const achievements = Array.isArray(analyticsData) ? analyticsData : [analyticsData];
            
            achievements.forEach(achievement => {
                window.analyticsService.trackAchievementEarned({
                    userId: achievement.user_id,
                    achievementId: achievement.achievement_id,
                    achievementName: achievement.achievement_name,
                    category: achievement.category,
                    pointsEarned: achievement.points_earned,
                    level: achievement.user_level
                });
            });
        }
    }
}

// Engagement Analytics
class EngagementAnalytics {
    static trackStudySessionCompleted(sessionData) {
        if (window.analyticsService && sessionData) {
            window.analyticsService.trackStudySessionCompleted({
                userId: sessionData.user_id,
                sessionDurationMinutes: Math.round(sessionData.duration_seconds / 60),
                activitiesCompleted: sessionData.activities_completed,
                xpEarned: sessionData.xp_earned,
                sessionType: sessionData.session_type
            });
        }
    }
    
    static trackFeatureUsed(featureData) {
        if (window.analyticsService && featureData) {
            window.analyticsService.trackFeatureUsed({
                userId: featureData.user_id,
                featureName: featureData.feature_name,
                category: featureData.category,
                subscriptionTier: featureData.subscription_tier
            });
        }
    }
}

// Auto-integration with existing page events
document.addEventListener('DOMContentLoaded', function() {
    // Track page view with enhanced data
    if (window.analyticsService) {
        window.analyticsService.trackPageView({
            section: window.analyticsService.getPageSection(),
            url: window.location.href,
            title: document.title
        });
    }
    
    // Enhanced quiz integration
    if (typeof startQuizSession === 'function') {
        const originalStartQuiz = startQuizSession;
        startQuizSession = function(...args) {
            const result = originalStartQuiz.apply(this, args);
            
            // Track quiz started if result contains analytics data
            if (result && result.then) {
                result.then(response => {
                    if (response.analytics_data) {
                        QuizAnalytics.trackQuizStarted(response.analytics_data);
                    }
                });
            }
            
            return result;
        };
    }
    
    // Enhanced video progress tracking
    if (typeof updateVideoProgress === 'function') {
        const originalUpdateProgress = updateVideoProgress;
        updateVideoProgress = function(...args) {
            const result = originalUpdateProgress.apply(this, args);
            
            // Track video completion if analytics data is present
            if (result && result.then) {
                result.then(response => {
                    if (response.analytics_data) {
                        VideoAnalytics.trackVideoWatched(response.analytics_data);
                    }
                });
            }
            
            return result;
        };
    }
});

// Global analytics helpers
window.QuizAnalytics = QuizAnalytics;
window.VideoAnalytics = VideoAnalytics;
window.AchievementAnalytics = AchievementAnalytics;
window.EngagementAnalytics = EngagementAnalytics;

// Backwards compatibility
window.trackQuizStarted = QuizAnalytics.trackQuizStarted;
window.trackQuizCompleted = QuizAnalytics.trackQuizCompleted;
window.trackVideoWatched = VideoAnalytics.trackVideoWatched;
window.trackAchievementEarned = AchievementAnalytics.trackAchievementEarned;
