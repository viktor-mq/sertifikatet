// Gamification real-time updates
class GamificationUpdater {
    constructor() {
        this.showLoadingState();
        this.updateLevelDisplay(); // Load data immediately on page load
        this.initializeEventListeners();
    }
    
    showLoadingState() {
        // Show loading animation while fetching data
        const levelBadge = document.querySelector('.level-badge');
        if (levelBadge) {
            levelBadge.innerHTML = '<div style="animation: spin 1s linear infinite; font-size: 1.5rem;">⟳</div>';
        }
        
        const xpText = document.querySelector('.xp-text');
        if (xpText) {
            xpText.textContent = 'Loading...';
        }
    }

    initializeEventListeners() {
        // Listen for quiz completion events
        document.addEventListener('quiz-completed', (event) => {
            const rewards = event.detail.gamification;
            if (rewards) {
                this.displayRewards(rewards);
                this.updateLevelDisplay();
            }
        });

        // Auto-refresh level info every 10 seconds
        setInterval(() => {
            this.updateLevelDisplay();
        }, 10000);
    }

    async updateLevelDisplay() {
        try {
            const response = await fetch('/gamification/api/level-info');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update level badge (remove loading spinner)
            const levelBadge = document.querySelector('.level-badge');
            if (levelBadge) {
                levelBadge.textContent = data.current_level;
            }

            // Update XP progress bar
            const xpProgress = document.querySelector('.xp-progress-bar');
            if (xpProgress) {
                xpProgress.style.width = `${data.progress_percentage}%`;
            }

            // Update XP text
            const xpText = document.querySelector('.xp-text');
            if (xpText) {
                xpText.textContent = `${data.current_xp} / ${data.next_level_xp} XP`;
            }

            // Update percentage text
            const percentageText = document.querySelector('.xp-percentage');
            if (percentageText) {
                percentageText.textContent = `${data.progress_percentage}%`;
            }

            // Update total XP
            const totalXpText = document.querySelector('.total-xp');
            if (totalXpText) {
                totalXpText.textContent = data.total_xp;
            }

        } catch (error) {
            console.error('Error updating level display:', error);
            
            // Show error state
            const levelBadge = document.querySelector('.level-badge');
            if (levelBadge) {
                levelBadge.textContent = '?';
            }
            
            const xpText = document.querySelector('.xp-text');
            if (xpText) {
                xpText.textContent = 'Error loading';
            }
        }
    }

    displayRewards(rewards) {
        // Show XP gained notification
        if (rewards.xp_earned > 0) {
            this.showXpNotification(rewards.xp_earned);
        }

        // Show achievement notifications
        rewards.achievements.forEach(achievement => {
            this.showAchievementNotification(achievement);
        });

        // Show level up notifications
        rewards.level_ups.forEach(level => {
            this.showLevelUpNotification(level);
        });

        // Show daily challenge completion
        rewards.daily_challenges.forEach(challenge => {
            this.showChallengeNotification(challenge);
        });
    }

    showXpNotification(xpEarned) {
        const notification = this.createNotification({
            type: 'xp',
            icon: '⭐',
            title: 'XP Earned!',
            message: `+${xpEarned} XP`,
            duration: 3000
        });
        this.displayNotification(notification);
    }

    showAchievementNotification(achievement) {
        const notification = this.createNotification({
            type: 'achievement',
            icon: '🏆',
            title: 'Achievement Unlocked!',
            message: achievement.name,
            description: achievement.description,
            duration: 5000
        });
        this.displayNotification(notification);
    }

    showLevelUpNotification(level) {
        const notification = this.createNotification({
            type: 'level-up',
            icon: '🎉',
            title: 'Level Up!',
            message: `Level ${level} Reached!`,
            duration: 4000
        });
        this.displayNotification(notification);
    }

    showChallengeNotification(challenge) {
        const notification = this.createNotification({
            type: 'challenge',
            icon: '✅',
            title: 'Challenge Complete!',
            message: challenge.title,
            duration: 3000
        });
        this.displayNotification(notification);
    }

    createNotification({type, icon, title, message, description, duration}) {
        const notification = document.createElement('div');
        notification.className = `gamification-notification ${type}-notification`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icon}</div>
                <div class="notification-text">
                    <h4>${title}</h4>
                    <p>${message}</p>
                    ${description ? `<small>${description}</small>` : ''}
                </div>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add click to close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // Auto-remove after duration
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);

        return notification;
    }

    displayNotification(notification) {
        let container = document.querySelector('.gamification-notifications');
        if (!container) {
            container = document.createElement('div');
            container.className = 'gamification-notifications';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
    }

    removeNotification(notification) {
        notification.classList.add('hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// Initialize when DOM is loaded
function initGamification() {
    if (document.querySelector('.gamification-dashboard') || 
        document.querySelector('[data-gamification="true"]')) {
        new GamificationUpdater();
    }
}

// Handle both cases: DOM already loaded OR still loading
if (document.readyState === 'loading') {
    // DOM not ready yet, wait for it
    document.addEventListener('DOMContentLoaded', initGamification);
} else {
    // DOM already ready, initialize immediately
    initGamification();
}

// Export for use in quiz system
window.GamificationUpdater = GamificationUpdater;
