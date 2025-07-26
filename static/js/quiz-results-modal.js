/**
 * Quiz Results Modal System for Sertifikatet Platform
 * Integrates with existing gamification system and provides beautiful animated results
 */

class QuizResultsModal {
    constructor() {
        this.isOpen = false;
        this.currentReviewQuestion = 0;
        this.reviewQuestions = [];
        this.sessionId = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Listen for quiz completion from existing quiz-gamification.js
        document.addEventListener('quiz-ajax-complete', (event) => {
            this.handleQuizCompletion(event.detail);
        });

        // Listen for direct calls from quiz system
        document.addEventListener('show-quiz-results', (event) => {
            this.handleQuizCompletion(event.detail);
        });

        // Keyboard support
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    async handleQuizCompletion(data) {
        if (!data.success) {
            console.error('Quiz completion failed:', data.error);
            return;
        }

        this.sessionId = data.session_id;
        await this.showResultsModal(data);
    }

    async showResultsModal(data) {
        const { results, gamification } = data;
        
        // Create modal backdrop
        this.createModalBackdrop();
        
        // Create primary results modal
        const modal = this.createPrimaryModal(results, gamification);
        document.body.appendChild(modal);
        
        // Trigger animations
        await this.animateModalEntrance(modal);
        
        // Process gamification rewards with existing system
        if (gamification && window.GamificationUpdater) {
            const updater = new window.GamificationUpdater();
            updater.displayRewards(gamification);
        }
        
        this.isOpen = true;
    }

    createModalBackdrop() {
        const backdrop = document.createElement('div');
        backdrop.id = 'quiz-results-backdrop';
        backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-[1000] opacity-0 transition-opacity duration-300';
        backdrop.addEventListener('click', () => this.closeModal());
        document.body.appendChild(backdrop);
        
        // Animate in
        setTimeout(() => {
            backdrop.classList.remove('opacity-0');
            backdrop.classList.add('opacity-100');
        }, 10);
    }

    createPrimaryModal(results, gamification) {
        const modal = document.createElement('div');
        modal.id = 'quiz-results-modal';
        modal.className = `
            fixed inset-4 sm:inset-8 md:inset-auto 
            md:top-1/2 md:left-1/2 md:transform md:-translate-x-1/2 md:-translate-y-1/2
            w-auto md:w-full md:max-w-md lg:max-w-lg xl:max-w-xl 2xl:max-w-2xl
            max-h-[90vh] md:max-h-[85vh] lg:max-h-[80vh]
            glass rounded-xl shadow-2xl z-[1001] p-4 sm:p-6 overflow-y-auto
            scale-75 opacity-0 transition-all duration-300
        `;

        const accuracy = Math.round(results.accuracy);
        const timeFormatted = this.formatTime(results.total_time);
        const scoreColor = accuracy >= 90 ? 'text-green-400' : accuracy >= 70 ? 'text-yellow-400' : 'text-red-400';
        const progressColor = accuracy >= 90 ? 'from-green-500 to-emerald-500' : accuracy >= 70 ? 'from-yellow-500 to-orange-500' : 'from-red-500 to-pink-500';

        modal.innerHTML = `
            <!-- Header -->
            <div class="text-center mb-6">
                <div class="text-4xl mb-2">${accuracy >= 90 ? '🎉' : accuracy >= 70 ? '👍' : '📚'}</div>
                <h2 class="text-2xl font-bold text-white mb-1">Quiz Fullført!</h2>
                <p class="text-purple-200">Flott jobbet med teorien!</p>
            </div>

            <!-- Score Section -->
            <div class="text-center mb-6">
                <div class="relative inline-block">
                    <!-- Circular Progress Ring -->
                    <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="54" stroke="rgba(255,255,255,0.1)" stroke-width="8" fill="none"/>
                        <circle id="progress-circle" cx="60" cy="60" r="54" 
                                stroke="url(#gradient)" stroke-width="8" fill="none"
                                stroke-linecap="round" stroke-dasharray="339.29" stroke-dashoffset="339.29"
                                class="transition-all duration-2000 ease-out"/>
                        <defs>
                            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" class="stop-color-from-purple-500"/>
                                <stop offset="100%" class="stop-color-to-pink-500"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    
                    <!-- Score Display -->
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <div id="score-counter" class="text-3xl font-bold ${scoreColor}" data-target="${accuracy}">0</div>
                        <div class="text-sm text-purple-200">%</div>
                    </div>
                </div>
                
                <div class="mt-4 text-center">
                    <div class="text-white text-lg font-semibold">${results.correct_answers}/${results.total_questions} riktige</div>
                    <div class="text-purple-200 text-sm">Tid brukt: ${timeFormatted}</div>
                </div>
            </div>

            <!-- Gamification Section -->
            ${gamification ? this.createGamificationSection(gamification) : ''}

            <!-- Performance Insights -->
            <div class="bg-white bg-opacity-10 rounded-lg p-4 mb-6">
                <h3 class="text-white font-semibold mb-2">📊 Prestasjon</h3>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <div class="text-purple-200">Nøyaktighet</div>
                        <div class="text-white font-semibold">${accuracy}%</div>
                    </div>
                    <div>
                        <div class="text-purple-200">Gjennomsnittlig tid</div>
                        <div class="text-white font-semibold">${this.formatTime(results.total_time / results.total_questions)}</div>
                    </div>
                </div>
                ${this.getPerformanceMessage(accuracy)}
            </div>

            <!-- Action Buttons -->
            <div class="space-y-3">
                <button id="review-answers-btn" 
                        class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 
                               text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 
                               transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500">
                    📝 Se gjennom svar
                </button>
                
                <div class="grid grid-cols-2 gap-3">
                    <button id="new-quiz-btn" 
                            class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium py-2 px-4 
                                   rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white">
                        🔄 Ny quiz
                    </button>
                    <button id="dashboard-btn" 
                            class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium py-2 px-4 
                                   rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white">
                        🏠 Dashboard
                    </button>
                </div>
                
                <button id="share-score-btn" 
                        class="w-full bg-white bg-opacity-10 hover:bg-opacity-20 text-white font-medium py-2 px-4 
                               rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white">
                    📤 Del resultat
                </button>
            </div>

            <!-- Close Button -->
            <button id="close-modal-btn" 
                    class="absolute top-4 right-4 text-white hover:text-purple-200 text-2xl 
                           focus:outline-none transition-colors duration-200">
                ×
            </button>
        `;

        this.setupPrimaryModalEventListeners(modal);
        return modal;
    }

    createGamificationSection(gamification) {
        if (!gamification.xp_earned && !gamification.achievements.length) {
            return '';
        }

        return `
            <div class="bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg p-4 mb-6">
                <h3 class="text-white font-semibold mb-3 flex items-center">
                    ⭐ Belønninger
                </h3>
                
                ${gamification.xp_earned > 0 ? `
                    <div class="flex items-center justify-between bg-white bg-opacity-20 rounded-lg p-3 mb-3">
                        <div class="flex items-center">
                            <div class="text-2xl mr-3">🎯</div>
                            <div>
                                <div class="text-white font-medium">XP Opptjent</div>
                                <div class="text-purple-100 text-sm">Erfaring for gjennomføring</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div id="xp-counter" class="text-2xl font-bold text-yellow-300" data-target="${gamification.xp_earned}">0</div>
                            <div class="text-purple-200 text-xs">XP</div>
                        </div>
                    </div>
                ` : ''}

                ${gamification.achievements.length > 0 ? `
                    <div class="space-y-2">
                        ${gamification.achievements.map(achievement => `
                            <div class="flex items-center bg-white bg-opacity-20 rounded-lg p-3 achievement-unlock">
                                <div class="text-2xl mr-3">🏆</div>
                                <div>
                                    <div class="text-white font-medium">${achievement.name}</div>
                                    <div class="text-purple-100 text-sm">+${achievement.points} XP bonus</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    setupPrimaryModalEventListeners(modal) {
        // Review answers button
        modal.querySelector('#review-answers-btn').addEventListener('click', () => {
            this.showAnswerReviewModal();
        });

        // New quiz button
        modal.querySelector('#new-quiz-btn').addEventListener('click', () => {
            this.closeModal();
            // Trigger new quiz - you can customize this
            const event = new CustomEvent('start-new-quiz');
            document.dispatchEvent(event);
        });

        // Dashboard button
        modal.querySelector('#dashboard-btn').addEventListener('click', () => {
            this.closeModal();
            window.location.href = '/dashboard';
        });

        // Share score button
        modal.querySelector('#share-score-btn').addEventListener('click', () => {
            this.shareScore();
        });

        // Close button
        modal.querySelector('#close-modal-btn').addEventListener('click', () => {
            this.closeModal();
        });
    }

    async showAnswerReviewModal() {
        if (!this.sessionId) {
            console.error('No session ID available for review');
            return;
        }

        try {
            // Fetch detailed question data
            const response = await fetch(`/quiz/session/${this.sessionId}/review`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load review data');
            }

            this.reviewQuestions = data.questions;
            this.currentReviewQuestion = 0;
            
            // Hide primary modal
            const primaryModal = document.getElementById('quiz-results-modal');
            primaryModal.style.display = 'none';
            
            // Create review modal
            const reviewModal = this.createReviewModal();
            document.body.appendChild(reviewModal);
            
            // Animate in
            setTimeout(() => {
                reviewModal.classList.remove('scale-75', 'opacity-0');
                reviewModal.classList.add('scale-100', 'opacity-100');
            }, 10);
            
        } catch (error) {
            console.error('Error loading review data:', error);
            alert('Kunne ikke laste inn detaljerte svar. Prøv igjen senere.');
        }
    }

    createReviewModal() {
        const modal = document.createElement('div');
        modal.id = 'quiz-review-modal';
        modal.className = `
            fixed inset-4 md:inset-8 glass rounded-xl shadow-2xl z-[1002] p-6 overflow-hidden
            scale-75 opacity-0 transition-all duration-300 flex flex-col
        `;

        modal.innerHTML = `
            <!-- Header -->
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h2 class="text-xl font-bold text-white">📝 Gjennomgang av svar</h2>
                    <p class="text-purple-200 text-sm">Spørsmål <span id="current-question-num">1</span> av <span id="total-questions-num">${this.reviewQuestions.length}</span></p>
                </div>
                <button id="close-review-btn" 
                        class="text-white hover:text-purple-200 text-2xl focus:outline-none transition-colors duration-200">
                    ×
                </button>
            </div>

            <!-- Progress Bar -->
            <div class="bg-white bg-opacity-20 rounded-full h-2 mb-6">
                <div id="review-progress" class="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300" 
                     style="width: ${((this.currentReviewQuestion + 1) / this.reviewQuestions.length) * 100}%"></div>
            </div>

            <!-- Question Content -->
            <div id="review-content" class="flex-1 overflow-y-auto mb-6">
                ${this.createReviewQuestionContent(0)}
            </div>

            <!-- Navigation -->
            <div class="flex items-center justify-between">
                <button id="prev-question-btn" 
                        class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium py-2 px-4 
                               rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white
                               disabled:opacity-50 disabled:cursor-not-allowed"
                        ${this.currentReviewQuestion === 0 ? 'disabled' : ''}>
                    ← Forrige
                </button>

                <!-- Question Navigation Dots -->
                <div class="flex space-x-2">
                    ${this.reviewQuestions.map((_, index) => `
                        <button class="w-3 h-3 rounded-full question-dot transition-all duration-200 
                                       ${index === this.currentReviewQuestion ? 'bg-white' : 'bg-white bg-opacity-30'}"
                                data-question-index="${index}"></button>
                    `).join('')}
                </div>

                <button id="next-question-btn" 
                        class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium py-2 px-4 
                               rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white
                               disabled:opacity-50 disabled:cursor-not-allowed"
                        ${this.currentReviewQuestion === this.reviewQuestions.length - 1 ? 'disabled' : ''}>
                    Neste →
                </button>
            </div>
        `;

        this.setupReviewModalEventListeners(modal);
        return modal;
    }

    createReviewQuestionContent(questionIndex) {
        const question = this.reviewQuestions[questionIndex];
        if (!question) return '<div class="text-white">Ingen spørsmål funnet</div>';

        const userAnswer = question.user_answer;
        const correctAnswer = question.correct_answer;
        const isCorrect = userAnswer === correctAnswer;

        return `
            <div class="space-y-6">
                <!-- Question -->
                <div class="bg-white bg-opacity-10 rounded-lg p-4">
                    <h3 class="text-white font-semibold mb-2">Spørsmål</h3>
                    <p class="text-purple-100">${question.question_text}</p>
                    ${question.image_filename ? `
                        <img src="/static/images/${question.image_folder ? question.image_folder + '/' : ''}${question.image_filename}" 
                             alt="Spørsmålsbilde" 
                             class="mt-3 rounded-lg max-w-full h-auto">
                    ` : ''}
                </div>

                <!-- Answer Options -->
                <div class="space-y-3">
                    <h4 class="text-white font-semibold">Svaralternativer</h4>
                    ${question.options.map(option => {
                        const isUserAnswer = option.letter === userAnswer;
                        const isCorrectOption = option.letter === correctAnswer;
                        
                        let bgClass = 'bg-white bg-opacity-10';
                        let borderClass = 'border-transparent';
                        let iconClass = '';
                        
                        if (isCorrectOption) {
                            bgClass = 'bg-green-500 bg-opacity-30 border-green-400';
                            borderClass = 'border-green-400';
                            iconClass = '<span class="text-green-400 ml-2">✓</span>';
                        } else if (isUserAnswer && !isCorrect) {
                            bgClass = 'bg-red-500 bg-opacity-30 border-red-400';
                            borderClass = 'border-red-400';
                            iconClass = '<span class="text-red-400 ml-2">✗</span>';
                        }
                        
                        return `
                            <div class="p-4 rounded-lg border-2 ${bgClass} ${borderClass} transition-all duration-200">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <span class="bg-white bg-opacity-20 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold mr-3">
                                            ${option.letter.toUpperCase()}
                                        </span>
                                        <span class="text-white">${option.text}</span>
                                    </div>
                                    ${iconClass}
                                </div>
                                ${isUserAnswer ? '<div class="text-purple-200 text-sm mt-2">Ditt svar</div>' : ''}
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Result Summary -->
                <div class="bg-white bg-opacity-10 rounded-lg p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <div class="text-2xl mr-3">${isCorrect ? '✅' : '❌'}</div>
                            <div>
                                <div class="text-white font-semibold">${isCorrect ? 'Riktig svar!' : 'Feil svar'}</div>
                                <div class="text-purple-200 text-sm">Du svarte: ${userAnswer ? userAnswer.toUpperCase() : 'Ikke besvart'}</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-purple-200 text-sm">Tid brukt</div>
                            <div class="text-white font-semibold">${this.formatTime(question.time_spent || 0)}</div>
                        </div>
                    </div>
                </div>

                <!-- Explanation -->
                ${question.explanation ? `
                    <div class="bg-blue-500 bg-opacity-20 border-l-4 border-blue-400 rounded-lg p-4">
                        <h4 class="text-white font-semibold mb-2 flex items-center">
                            <span class="mr-2">💡</span>
                            Forklaring
                        </h4>
                        <p class="text-blue-100">${question.explanation}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    setupReviewModalEventListeners(modal) {
        // Close button
        modal.querySelector('#close-review-btn').addEventListener('click', () => {
            this.closeReviewModal();
        });

        // Navigation buttons
        modal.querySelector('#prev-question-btn').addEventListener('click', () => {
            this.navigateReviewQuestion(-1);
        });

        modal.querySelector('#next-question-btn').addEventListener('click', () => {
            this.navigateReviewQuestion(1);
        });

        // Question dots
        modal.querySelectorAll('.question-dot').forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.goToReviewQuestion(index);
            });
        });
    }

    navigateReviewQuestion(direction) {
        const newIndex = this.currentReviewQuestion + direction;
        if (newIndex >= 0 && newIndex < this.reviewQuestions.length) {
            this.goToReviewQuestion(newIndex);
        }
    }

    goToReviewQuestion(index) {
        this.currentReviewQuestion = index;
        
        const modal = document.getElementById('quiz-review-modal');
        const content = modal.querySelector('#review-content');
        
        // Update content
        content.innerHTML = this.createReviewQuestionContent(index);
        
        // Update progress
        const progress = ((index + 1) / this.reviewQuestions.length) * 100;
        modal.querySelector('#review-progress').style.width = `${progress}%`;
        
        // Update question number
        modal.querySelector('#current-question-num').textContent = index + 1;
        
        // Update navigation buttons
        const prevBtn = modal.querySelector('#prev-question-btn');
        const nextBtn = modal.querySelector('#next-question-btn');
        
        prevBtn.disabled = index === 0;
        nextBtn.disabled = index === this.reviewQuestions.length - 1;
        
        // Update dots
        modal.querySelectorAll('.question-dot').forEach((dot, dotIndex) => {
            if (dotIndex === index) {
                dot.classList.remove('bg-opacity-30');
                dot.classList.add('bg-white');
            } else {
                dot.classList.add('bg-opacity-30');
                dot.classList.remove('bg-white');
            }
        });
    }

    closeReviewModal() {
        const reviewModal = document.getElementById('quiz-review-modal');
        if (reviewModal) {
            reviewModal.classList.add('scale-75', 'opacity-0');
            setTimeout(() => {
                reviewModal.remove();
            }, 300);
        }
        
        // Show primary modal again
        const primaryModal = document.getElementById('quiz-results-modal');
        if (primaryModal) {
            primaryModal.style.display = 'block';
        }
    }

    async animateModalEntrance(modal) {
        // Animate modal in
        setTimeout(() => {
            modal.classList.remove('scale-75', 'opacity-0');
            modal.classList.add('scale-100', 'opacity-100');
        }, 10);

        // Animate circular progress
        setTimeout(() => {
            const circle = modal.querySelector('#progress-circle');
            const scoreCounter = modal.querySelector('#score-counter');
            const xpCounter = modal.querySelector('#xp-counter');
            
            if (circle && scoreCounter) {
                const targetScore = parseInt(scoreCounter.dataset.target);
                const circumference = 339.29;
                const offset = circumference - (targetScore / 100) * circumference;
                
                circle.style.strokeDashoffset = offset;
                this.animateCounter(scoreCounter, targetScore, 2000);
            }

            if (xpCounter) {
                const targetXP = parseInt(xpCounter.dataset.target);
                setTimeout(() => {
                    this.animateCounter(xpCounter, targetXP, 1500);
                }, 500);
            }

            // Animate achievement unlocks
            modal.querySelectorAll('.achievement-unlock').forEach((achievement, index) => {
                setTimeout(() => {
                    achievement.style.transform = 'translateY(0)';
                    achievement.style.opacity = '1';
                }, 1000 + index * 200);
            });
        }, 300);
    }

    animateCounter(element, target, duration) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    getPerformanceMessage(accuracy) {
        if (accuracy >= 90) {
            return '<div class="mt-2 text-green-300 text-sm">🌟 Utmerket! Du har god kontroll på teorien.</div>';
        } else if (accuracy >= 70) {
            return '<div class="mt-2 text-yellow-300 text-sm">👍 Bra jobbet! Fortsett å øve for enda bedre resultater.</div>';
        } else {
            return '<div class="mt-2 text-orange-300 text-sm">📚 Fortsett å studere - du er på rett vei!</div>';
        }
    }

    shareScore() {
        const modal = document.getElementById('quiz-results-modal');
        const scoreElement = modal.querySelector('#score-counter');
        const score = scoreElement ? scoreElement.textContent : '0';
        
        const shareText = `Jeg scoret ${score}% på teoriprøven på Sertifikatet! 🚗📚 #kørekort #teoriprøve`;
        
        if (navigator.share) {
            navigator.share({
                title: 'Mitt teoriprøve resultat',
                text: shareText,
                url: window.location.origin
            });
        } else {
            navigator.clipboard.writeText(shareText).then(() => {
                // Show temporary success message
                const btn = modal.querySelector('#share-score-btn');
                const originalText = btn.textContent;
                btn.textContent = '✓ Kopiert!';
                btn.classList.add('bg-green-500', 'bg-opacity-30');
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('bg-green-500', 'bg-opacity-30');
                }, 2000);
            });
        }
    }

    handleKeyboard(e) {
        if (!this.isOpen) return;

        switch(e.key) {
            case 'Escape':
                e.preventDefault();
                this.closeModal();
                break;
            case 'ArrowLeft':
                if (document.getElementById('quiz-review-modal')) {
                    e.preventDefault();
                    this.navigateReviewQuestion(-1);
                }
                break;
            case 'ArrowRight':
                if (document.getElementById('quiz-review-modal')) {
                    e.preventDefault();
                    this.navigateReviewQuestion(1);
                }
                break;
        }
    }

    closeModal() {
        const backdrop = document.getElementById('quiz-results-backdrop');
        const modal = document.getElementById('quiz-results-modal');
        const reviewModal = document.getElementById('quiz-review-modal');

        // Check if we're closing the review modal or the main modal
        const isClosingReviewOnly = reviewModal && !modal;

        if (modal) {
            modal.classList.add('scale-75', 'opacity-0');
        }
        
        if (reviewModal) {
            reviewModal.classList.add('scale-75', 'opacity-0');
        }
        
        if (backdrop) {
            backdrop.classList.remove('opacity-100');
            backdrop.classList.add('opacity-0');
        }

        setTimeout(() => {
            [backdrop, modal, reviewModal].forEach(el => {
                if (el && el.parentNode) {
                    el.parentNode.removeChild(el);
                }
            });
            
            // Only redirect if we're closing the main modal (not just the review)
            if (!isClosingReviewOnly) {
                // Redirect to dashboard to prevent quiz retaking (with cache busting)
                window.location.href = '/dashboard?updated=' + Date.now();
            }
        }, 300);

        this.isOpen = false;
    }

    // Static method to trigger modal from external scripts
    static show(data) {
        const event = new CustomEvent('show-quiz-results', { detail: data });
        document.dispatchEvent(event);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quizResultsModal = new QuizResultsModal();
});

// Export for external use
window.QuizResultsModal = QuizResultsModal;