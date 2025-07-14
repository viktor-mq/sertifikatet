/**
 * Quiz Mobile Enhancement JavaScript
 * Phase 10: Mobile Responsiveness
 */

class QuizMobileEnhancer {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.currentQuestionIndex = 0;
        this.totalQuestions = 0;
        this.startTime = Date.now();
        this.timerInterval = null;
        this.isSwipeEnabled = true;
        this.swipeThreshold = 50; // Minimum distance for swipe
        this.swipeVelocityThreshold = 0.3; // Minimum velocity for swipe
        
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupQuiz();
            this.setupSwipeGestures();
            this.setupMobileOptimizations();
            this.setupKeyboardShortcuts();
        });
    }

    setupQuiz() {
        // Get total questions
        this.totalQuestions = document.querySelectorAll('.question-card').length;
        
        if (this.totalQuestions === 0) return;

        // Set start time
        const startTimeInput = document.getElementById('startTime');
        if (startTimeInput) {
            startTimeInput.value = this.startTime;
        }

        // Show first question
        this.showQuestion(0);
        
        // Start timer
        this.startTimer();
        
        // Setup answer selection
        this.setupAnswerSelection();
        
        // Setup form submission
        this.setupFormSubmission();
    }

    setupSwipeGestures() {
        const questionsContainer = document.getElementById('questionsContainer');
        if (!questionsContainer) return;

        // Prevent default touch behaviors that might interfere
        questionsContainer.style.touchAction = 'pan-y pinch-zoom';

        // Touch start
        questionsContainer.addEventListener('touchstart', (e) => {
            this.handleTouchStart(e);
        }, { passive: true });

        // Touch move - prevent horizontal scrolling during swipe
        questionsContainer.addEventListener('touchmove', (e) => {
            this.handleTouchMove(e);
        }, { passive: false });

        // Touch end
        questionsContainer.addEventListener('touchend', (e) => {
            this.handleTouchEnd(e);
        }, { passive: true });

        // Mouse events for desktop testing
        questionsContainer.addEventListener('mousedown', (e) => {
            this.handleMouseStart(e);
        });

        questionsContainer.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });

        questionsContainer.addEventListener('mouseup', (e) => {
            this.handleMouseEnd(e);
        });
    }

    handleTouchStart(e) {
        if (!this.isSwipeEnabled) return;
        
        const touch = e.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;
        this.touchStartTime = Date.now();
    }

    handleTouchMove(e) {
        if (!this.isSwipeEnabled) return;

        const touch = e.touches[0];
        const deltaX = Math.abs(touch.clientX - this.touchStartX);
        const deltaY = Math.abs(touch.clientY - this.touchStartY);

        // If horizontal movement is greater than vertical, prevent scrolling
        if (deltaX > deltaY && deltaX > 10) {
            e.preventDefault();
        }
    }

    handleTouchEnd(e) {
        if (!this.isSwipeEnabled) return;

        const touch = e.changedTouches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const deltaY = touch.clientY - this.touchStartY;
        const deltaTime = Date.now() - this.touchStartTime;
        
        this.processSwipe(deltaX, deltaY, deltaTime);
    }

    handleMouseStart(e) {
        if (!this.isSwipeEnabled) return;
        
        this.touchStartX = e.clientX;
        this.touchStartY = e.clientY;
        this.touchStartTime = Date.now();
        this.isMouseDown = true;
    }

    handleMouseMove(e) {
        if (!this.isSwipeEnabled || !this.isMouseDown) return;

        const deltaX = Math.abs(e.clientX - this.touchStartX);
        const deltaY = Math.abs(e.clientY - this.touchStartY);

        // Visual feedback for desktop swipe
        if (deltaX > 30) {
            document.body.style.cursor = deltaX > 0 ? 'e-resize' : 'w-resize';
        }
    }

    handleMouseEnd(e) {
        if (!this.isSwipeEnabled || !this.isMouseDown) return;

        const deltaX = e.clientX - this.touchStartX;
        const deltaY = e.clientY - this.touchStartY;
        const deltaTime = Date.now() - this.touchStartTime;
        
        this.isMouseDown = false;
        document.body.style.cursor = 'default';
        
        this.processSwipe(deltaX, deltaY, deltaTime);
    }

    processSwipe(deltaX, deltaY, deltaTime) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        // Check if horizontal swipe
        if (absX > absY && absX > this.swipeThreshold) {
            const velocity = absX / deltaTime;
            
            if (velocity > this.swipeVelocityThreshold) {
                if (deltaX > 0) {
                    // Swipe right - previous question
                    this.navigateToPrevious();
                } else {
                    // Swipe left - next question
                    this.navigateToNext();
                }
            }
        }
    }

    navigateToPrevious() {
        if (this.currentQuestionIndex > 0) {
            this.changeQuestion(-1);
            this.showSwipeFeedback('previous');
        }
    }

    navigateToNext() {
        if (this.currentQuestionIndex < this.totalQuestions - 1) {
            this.changeQuestion(1);
            this.showSwipeFeedback('next');
        }
    }

    showSwipeFeedback(direction) {
        // Create visual feedback for swipe
        const feedback = document.createElement('div');
        feedback.className = `fixed top-1/2 ${direction === 'next' ? 'right-4' : 'left-4'} transform -translate-y-1/2 
                             bg-purple-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 
                             animate-pulse pointer-events-none`;
        feedback.innerHTML = `<i class="fas fa-chevron-${direction === 'next' ? 'right' : 'left'}"></i>`;
        
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            feedback.remove();
        }, 500);
    }

    setupMobileOptimizations() {
        // Add mobile-specific styles
        const style = document.createElement('style');
        style.textContent = `
            /* Mobile Quiz Optimizations */
            @media (max-width: 768px) {
                .question-card {
                    margin-bottom: 1rem !important;
                    padding: 1.5rem !important;
                }
                
                .question-card h2 {
                    font-size: 1.25rem !important;
                    line-height: 1.4 !important;
                }
                
                .answer-option div {
                    padding: 1rem !important;
                    font-size: 0.95rem !important;
                }
                
                .question-nav {
                    width: 2.5rem !important;
                    height: 2.5rem !important;
                    font-size: 0.875rem !important;
                }
                
                /* Swipe hint */
                .quiz-container::after {
                    content: 'Sveip for å navigere mellom spørsmål';
                    position: fixed;
                    bottom: 1rem;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 0.5rem;
                    font-size: 0.75rem;
                    opacity: 0.7;
                    z-index: 40;
                    animation: fadeInOut 3s ease-in-out;
                    animation-delay: 1s;
                    animation-fill-mode: both;
                }
                
                /* Larger touch targets */
                .answer-option {
                    margin-bottom: 0.75rem !important;
                }
                
                .answer-option div {
                    min-height: 3.5rem !important;
                }
                
                /* Hide navigation hint after first interaction */
                .quiz-container.interacted::after {
                    display: none;
                }
            }
            
            @keyframes fadeInOut {
                0%, 100% { opacity: 0; }
                20%, 80% { opacity: 0.7; }
            }
            
            /* Pull to refresh indicator */
            .pull-refresh {
                position: fixed;
                top: -60px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(147, 51, 234, 0.9);
                color: white;
                padding: 1rem 2rem;
                border-radius: 0 0 1rem 1rem;
                transition: top 0.3s ease;
                z-index: 50;
            }
            
            .pull-refresh.active {
                top: 0;
            }
        `;
        document.head.appendChild(style);

        // Add quiz container class for mobile hints
        const container = document.querySelector('.max-w-4xl');
        if (container) {
            container.classList.add('quiz-container');
        }

        // Hide hint after first interaction
        let hasInteracted = false;
        const hideHint = () => {
            if (!hasInteracted) {
                container?.classList.add('interacted');
                hasInteracted = true;
            }
        };

        document.addEventListener('touchstart', hideHint, { once: true });
        document.addEventListener('click', hideHint, { once: true });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return; // Don't interfere with input fields
            }

            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigateToPrevious();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateToNext();
                    break;
                case '1':
                case '2':
                case '3':
                case '4':
                    e.preventDefault();
                    this.selectAnswer(e.key);
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    if (this.currentQuestionIndex === this.totalQuestions - 1) {
                        this.submitQuiz();
                    } else {
                        this.navigateToNext();
                    }
                    break;
            }
        });
    }

    selectAnswer(optionNumber) {
        const currentQuestion = document.querySelectorAll('.question-card')[this.currentQuestionIndex];
        if (!currentQuestion) return;

        const options = ['a', 'b', 'c', 'd'];
        const optionLetter = options[parseInt(optionNumber) - 1];
        const radioButton = currentQuestion.querySelector(`input[value="${optionLetter}"]`);
        
        if (radioButton) {
            radioButton.checked = true;
            radioButton.dispatchEvent(new Event('change'));
        }
    }

    setupAnswerSelection() {
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                // Mark question as answered
                const questionIndex = Array.from(document.querySelectorAll('.question-card')).findIndex(
                    card => card.dataset.questionId === e.target.dataset.questionId
                );
                
                const navButton = document.querySelector(`[data-question-index="${questionIndex}"]`);
                if (navButton) {
                    navButton.classList.add('answered');
                }
                
                // Auto-advance to next question after short delay (mobile UX)
                if (window.innerWidth <= 768) {
                    setTimeout(() => {
                        if (this.currentQuestionIndex < this.totalQuestions - 1) {
                            this.changeQuestion(1);
                        }
                    }, 600);
                } else {
                    setTimeout(() => {
                        if (this.currentQuestionIndex < this.totalQuestions - 1) {
                            this.changeQuestion(1);
                        }
                    }, 300);
                }
            });
        });
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            const timerElement = document.getElementById('timer');
            if (timerElement) {
                timerElement.textContent = `${minutes}:${seconds}`;
            }
        }, 1000);
    }

    showQuestion(index) {
        // Hide all questions
        document.querySelectorAll('.question-card').forEach(card => {
            card.style.display = 'none';
        });
        
        // Show current question
        const questions = document.querySelectorAll('.question-card');
        if (questions[index]) {
            questions[index].style.display = 'block';
        }
        
        // Update progress
        this.updateProgress(index);
        
        // Update navigation
        this.updateNavigation(index);
        
        // Store current index
        this.currentQuestionIndex = index;
    }

    updateProgress(index) {
        // Update progress bar
        const progress = ((index + 1) / this.totalQuestions) * 100;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Update question counter
        const currentQuestionElement = document.getElementById('currentQuestion');
        if (currentQuestionElement) {
            currentQuestionElement.textContent = index + 1;
        }
        
        // Update navigation buttons
        document.querySelectorAll('.question-nav').forEach(btn => {
            btn.classList.remove('current');
        });
        const currentButton = document.querySelector(`[data-question-index="${index}"]`);
        if (currentButton) {
            currentButton.classList.add('current');
        }
    }

    updateNavigation(index) {
        // Previous button
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) {
            prevBtn.disabled = index === 0;
        }
        
        // Next/Submit button
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');
        
        if (index === this.totalQuestions - 1) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (submitBtn) submitBtn.style.display = 'block';
        } else {
            if (nextBtn) nextBtn.style.display = 'block';
            if (submitBtn) submitBtn.style.display = 'none';
        }
    }

    changeQuestion(direction) {
        const newIndex = this.currentQuestionIndex + direction;
        if (newIndex >= 0 && newIndex < this.totalQuestions) {
            this.showQuestion(newIndex);
        }
    }

    goToQuestion(index) {
        if (index >= 0 && index < this.totalQuestions) {
            this.showQuestion(index);
        }
    }

    setupFormSubmission() {
        const form = document.getElementById('quizForm');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Count answered questions
            const answered = document.querySelectorAll('.question-nav.answered').length;
            const unanswered = this.totalQuestions - answered;
            
            let message = 'Er du sikker på at du vil levere quizen?';
            if (unanswered > 0) {
                message = `Du har ${unanswered} ubesvarte spørsmål. Er du sikker på at du vil levere?`;
            }
            
            if (confirm(message)) {
                if (this.timerInterval) {
                    clearInterval(this.timerInterval);
                }
                
                // Use AJAX submission instead of form.submit() to integrate with modal system
                this.submitQuizAjax(form);
            }
        });
    }
    
    async submitQuizAjax(form) {
        // Add data-quiz-form attribute for quiz-gamification integration
        form.setAttribute('data-quiz-form', 'true');
        
        // Get session ID from form or URL
        const sessionId = form.dataset.sessionId || this.getSessionIdFromUrl();
        if (!sessionId) {
            console.error('No session ID found for quiz submission');
            alert('Kunne ikke finne quiz-økt ID. Prøv å laste siden på nytt.');
            return;
        }
        
        // Show loading state
        this.showQuizLoadingState();
        
        try {
            // Trigger the quiz-gamification integration
            const event = new CustomEvent('submit', { 
                target: form,
                preventDefault: () => {} // Mock preventDefault
            });
            
            // Set session ID if not already set
            form.dataset.sessionId = sessionId;
            
            // Dispatch to quiz-gamification.js handler
            if (window.QuizGamificationIntegration) {
                // Create a mock event that quiz-gamification expects
                await window.QuizGamificationIntegration.prototype.handleQuizSubmission.call(
                    new window.QuizGamificationIntegration(), 
                    { target: form, preventDefault: () => {} }
                );
            } else {
                // Fallback to direct submission
                await this.directAjaxSubmission(form, sessionId);
            }
            
        } catch (error) {
            console.error('Quiz submission error:', error);
            alert('En feil oppstod under innsending av quiz. Prøv igjen.');
            this.hideQuizLoadingState();
        }
    }
    
    async directAjaxSubmission(form, sessionId) {
        // Collect quiz responses
        const responses = this.collectQuizResponses(form);
        
        // Submit via AJAX
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

        const result = await response.json();
        
        if (result.success) {
            // Trigger modal system
            const event = new CustomEvent('quiz-ajax-complete', {
                detail: result
            });
            document.dispatchEvent(event);
        } else {
            throw new Error(result.error || 'Quiz submission failed');
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
                    time_spent: this.getQuestionTimeSpent(questionId) || 30
                });
            }
        });
        
        return responses;
    }
    
    getQuestionTimeSpent(questionId) {
        // Try to get time spent from quiz timer if available
        if (window.quizTimer && window.quizTimer.getQuestionTime) {
            return window.quizTimer.getQuestionTime(questionId);
        }
        return null;
    }
    
    getCSRFToken() {
        const tokenEl = document.querySelector('meta[name="csrf-token"]');
        return tokenEl ? tokenEl.getAttribute('content') : '';
    }
    
    getSessionIdFromUrl() {
        // Extract session ID from URL if available
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('session_id') || null;
    }
    
    showQuizLoadingState() {
        const submitBtn = document.querySelector('#submitBtn, button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sender inn...';
        }
        
        // Show loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'quiz-loading-overlay';
        loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        loadingOverlay.innerHTML = `
            <div class="bg-white bg-opacity-20 rounded-lg p-8 text-center">
                <i class="fas fa-spinner fa-spin text-4xl text-white mb-4"></i>
                <p class="text-white font-semibold">Sender inn quiz...</p>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    hideQuizLoadingState() {
        const submitBtn = document.querySelector('#submitBtn, button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Send inn quiz';
        }
        
        const loadingOverlay = document.getElementById('quiz-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    submitQuiz() {
        const form = document.getElementById('quizForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
}

// Global functions for backwards compatibility
let quizEnhancer;

function changeQuestion(direction) {
    if (quizEnhancer) {
        quizEnhancer.changeQuestion(direction);
    }
}

function goToQuestion(index) {
    if (quizEnhancer) {
        quizEnhancer.goToQuestion(index);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    quizEnhancer = new QuizMobileEnhancer();
} else {
    quizEnhancer = new QuizMobileEnhancer();
}
