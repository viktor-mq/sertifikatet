// Quiz-Gamification Integration
// This script handles the connection between quiz completion and gamification rewards

class QuizGamificationIntegration {
    constructor() {
        this.initializeQuizSubmission();
    }

    initializeQuizSubmission() {
        // Listen for quiz form submissions
        const quizForms = document.querySelectorAll('form[data-quiz-form]');
        quizForms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleQuizSubmission(e));
        });

        // Listen for AJAX quiz completions
        document.addEventListener('quiz-ajax-complete', (e) => {
            this.handleQuizCompletion(e.detail);
        });
    }

    async handleQuizSubmission(event) {
        event.preventDefault();
        
        const form = event.target;
        const sessionId = form.dataset.sessionId;
        
        if (!sessionId) {
            console.error('No session ID found for quiz submission');
            return;
        }

        // Show loading state
        this.showLoadingState(form);

        try {
            // Collect quiz responses
            const responses = this.collectQuizResponses(form);
            
            // Submit quiz via AJAX
            const result = await this.submitQuizAjax(sessionId, responses);
            
            if (result.success) {
                // Handle gamification rewards
                if (result.gamification) {
                    this.processGamificationRewards(result.gamification);
                }
                
                // Redirect to results or show success
                this.handleQuizSuccess(result);
            } else {
                this.handleQuizError(result.error);
            }
            
        } catch (error) {
            console.error('Quiz submission error:', error);
            this.handleQuizError('En feil oppstod under innsending av quiz');
        } finally {
            this.hideLoadingState(form);
        }
    }

    collectQuizResponses(form) {
        const responses = [];
        const questions = form.querySelectorAll('[data-question-id]');
        
        questions.forEach(questionEl => {
            const questionId = questionEl.dataset.questionId;
            const selectedAnswer = questionEl.querySelector('input[type="radio"]:checked');
            
            if (selectedAnswer) {
                responses.push({
                    question_id: parseInt(questionId),
                    user_answer: selectedAnswer.value,
                    time_spent: this.getQuestionTimeSpent(questionId) || 30 // fallback to 30 seconds
                });
            }
        });
        
        return responses;
    }

    getQuestionTimeSpent(questionId) {
        // Try to get time spent from any existing quiz timer
        if (window.quizTimer && window.quizTimer.getQuestionTime) {
            return window.quizTimer.getQuestionTime(questionId);
        }
        return null;
    }

    async submitQuizAjax(sessionId, responses) {
        const response = await fetch(`/quiz/session/${sessionId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ responses })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    getCSRFToken() {
        const tokenEl = document.querySelector('meta[name="csrf-token"]');
        return tokenEl ? tokenEl.getAttribute('content') : '';
    }

    processGamificationRewards(rewards) {
        // Create custom event for gamification system
        const gamificationEvent = new CustomEvent('quiz-completed', {
            detail: { gamification: rewards }
        });
        
        document.dispatchEvent(gamificationEvent);

        // Update any visible XP displays immediately
        this.updateVisibleXPDisplays(rewards);
        
        // Show immediate feedback if we're on the quiz page
        this.showImmediateRewardFeedback(rewards);
    }

    updateVisibleXPDisplays(rewards) {
        // Update any XP counters visible on the page
        const xpDisplays = document.querySelectorAll('[data-user-xp]');
        xpDisplays.forEach(display => {
            const currentXP = parseInt(display.textContent) || 0;
            const newXP = currentXP + rewards.xp_earned;
            display.textContent = newXP;
            display.classList.add('xp-updated');
            setTimeout(() => display.classList.remove('xp-updated'), 600);
        });
    }

    showImmediateRewardFeedback(rewards) {
        if (rewards.xp_earned > 0) {
            this.showQuickXPFeedback(rewards.xp_earned);
        }
    }

    showQuickXPFeedback(xpEarned) {
        // Create a quick XP gained indicator
        const indicator = document.createElement('div');
        indicator.className = 'quiz-xp-indicator';
        indicator.innerHTML = `<span class="xp-icon">⭐</span> +${xpEarned} XP`;
        
        // Style the indicator
        Object.assign(indicator.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: 'rgba(139, 92, 246, 0.9)',
            color: 'white',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            zIndex: '10000',
            transform: 'translateX(300px)',
            transition: 'transform 0.3s ease-out',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        });

        document.body.appendChild(indicator);

        // Animate in
        setTimeout(() => {
            indicator.style.transform = 'translateX(0)';
        }, 10);

        // Animate out and remove
        setTimeout(() => {
            indicator.style.transform = 'translateX(300px)';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }, 3000);
    }

    handleQuizSuccess(result) {
        // Trigger the new modal-based results system
        const event = new CustomEvent('quiz-ajax-complete', {
            detail: result
        });
        document.dispatchEvent(event);
        
        // Legacy fallback if modal system isn't available
        if (!window.QuizResultsModal) {
            console.warn('Modal system not available, using fallback');
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                const message = `Quiz completed! Score: ${result.results.score}% (${result.results.correct_answers}/${result.results.total_questions})`;
                if (confirm(message + '\\n\\nWould you like to view detailed results?')) {
                    window.location.href = `/quiz/results/${result.session_id}`;
                }
            }
        }
    }

    handleQuizError(error) {
        alert('Feil ved innsending av quiz: ' + error);
    }

    showLoadingState(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sender inn...';
        }
    }

    hideLoadingState(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send inn quiz';
        }
    }

    // Helper method to trigger gamification from external scripts
    static triggerGamificationRewards(rewards) {
        const event = new CustomEvent('quiz-completed', {
            detail: { gamification: rewards }
        });
        document.dispatchEvent(event);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new QuizGamificationIntegration();
});

// Export for external use
window.QuizGamificationIntegration = QuizGamificationIntegration;
