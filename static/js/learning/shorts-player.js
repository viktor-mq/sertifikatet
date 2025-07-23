/**
 * TikTok-Style Video Player for Sertifikatet Learning System
 * Phase 3 Implementation - Vertical Video Player with Swipe Navigation
 */

// CSRF token utility
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

class ShortsPlayer {
    constructor(container, videos = [], options = {}) {
        this.container = container;
        this.videos = videos;
        this.currentIndex = options.startVideoIndex || 0;  // Use starting index from options
        this.isPlaying = false;
        this.videoElements = [];
        this.touchStartY = 0;
        this.touchStartX = 0;
        this.mouseStartY = 0;
        this.mouseStartX = 0;
        this.isDragging = false;
        this.isTransitioning = false;
        this.progressUpdateInterval = null;
        this.autoplayTimeout = null;
        this.infoTimeout = null;
        this.infoVisible = true;
        this.videoCompletionTracked = false;
        this.crossModuleEnabled = options.crossModuleEnabled || false;
        this.startingSubmodule = options.startingSubmodule || null;
        
        // Track recommended session state
        this.isRecommendedSession = false;
        this.recommendedSessionCompleted = false;
        this.lastVideoInRecommendedSession = null;
        
        // Player settings
        this.settings = {
            swipeThreshold: 50,
            transitionDuration: 300,
            progressUpdateFrequency: 1000, // Update progress every second
            autoplayNext: true,
            preloadCount: 2, // Preload 2 videos ahead
            volume: 0.8
        };
        
        this.init();
    }
    
    init() {
        this.createPlayerStructure();
        this.setupEventListeners();
        
        // Load all videos if cross-module enabled
        if (this.crossModuleEnabled) {
            this.loadAllVideosForSession();
        } else {
            this.loadVideos();
            this.loadCurrentVideo();
        }
        
        // Check if this is a recommended session and identify the last video (AFTER videos are loaded)
        this.initializeRecommendedSession();
        
        // Show video info initially
        setTimeout(() => {
            this.showVideoInfo();
        }, 500);
        
        // Make container focusable and focused
        this.container.setAttribute('tabindex', '0');
        this.container.focus();
        
        // Add visual focus indicator
        this.container.style.outline = 'none';
    }
    
    initializeRecommendedSession() {
        const urlParams = new URLSearchParams(window.location.search);
        const scopeParam = urlParams.get('scope');

        if (scopeParam === 'submodule' && !this.crossModuleEnabled) {
            this.isRecommendedSession = true;

            // For scope=submodule sessions, find the last video in the submodule
            if (this.videos.length > 0) {
                // Get the submodule of the first video (they should all be the same in a submodule session)
                const submodule = this.videos[0].theory_module_ref;

                // Filter to get all videos for the submodule
                const submoduleVideos = this.videos.filter(v => v.theory_module_ref === submodule);
                
                if (submoduleVideos.length > 0) {
                    this.lastVideoInRecommendedSession = submoduleVideos[submoduleVideos.length - 1].id;
                    console.log(`Recommended session for submodule ${submodule} initialized. Last video ID: ${this.lastVideoInRecommendedSession}`);
                }
            }
        }
    }
    
    createPlayerStructure() {
        this.container.innerHTML = `
            <div class="shorts-player relative w-full h-full overflow-hidden bg-black">
                <!-- Video Stack -->
                <div id="video-stack" class="relative w-full h-full">
                    <!-- Videos will be dynamically added here -->
                </div>
                
                <!-- UI Overlay -->
                <div class="absolute inset-0 pointer-events-none">
                    <!-- Progress Bar -->
                    <div class="absolute top-4 left-4 right-4 pointer-events-auto">
                        <div class="flex space-x-1">
                            ${this.videos.map((_, index) => `
                                <div class="flex-1 h-1 bg-white/30 rounded-full overflow-hidden">
                                    <div class="progress-bar h-full bg-white transition-all duration-300" style="width: 0%"></div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Video Info -->
                    <div id="video-info-overlay" class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 via-black/40 to-transparent pointer-events-auto transition-opacity duration-300">
                        <div class="flex items-end justify-between">
                            <div class="flex-1 mr-4">
                                <h3 id="video-title" class="text-white font-bold text-lg mb-1"></h3>
                                <p id="video-description" class="text-white/80 text-sm mb-2"></p>
                                <div class="flex items-center space-x-4 text-white/60 text-sm">
                                    <span id="video-counter">1 / ${this.videos.length}</span>
                                    <span id="video-duration">0:00</span>
                                </div>
                            </div>
                            
                            <!-- Side Actions -->
                            <div class="flex flex-col items-center space-y-6">
                                <button id="like-btn" class="action-btn text-white hover:text-red-400 transition-colors">
                                    <i class="fas fa-heart fa-2x"></i>
                                    <span class="like-count text-xs mt-1">0</span>
                                </button>
                                <button id="share-btn" class="action-btn text-white hover:text-blue-400 transition-colors">
                                    <i class="fas fa-share fa-2x"></i>
                                </button>
                                <button id="bookmark-btn" class="action-btn text-white hover:text-yellow-400 transition-colors">
                                    <i class="fas fa-bookmark fa-2x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Center Play/Pause -->
                    <div id="play-pause-overlay" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div id="play-pause-btn" class="w-20 h-20 rounded-full bg-black/50 flex items-center justify-center text-white opacity-0 transition-opacity duration-300 pointer-events-auto">
                            <i class="fas fa-play fa-2x"></i>
                        </div>
                    </div>
                    
                    <!-- Navigation Hints -->
                    <div class="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/40 animate-pulse">
                        <div class="text-center">
                            <i class="fas fa-chevron-up fa-lg mb-1"></i>
                            <p class="text-xs">Neste</p>
                        </div>
                    </div>
                    
                    <!-- Loading Indicator -->
                    <div id="loading-indicator" class="absolute inset-0 flex items-center justify-center bg-black/50 hidden">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                    </div>
                </div>
            </div>
        `;
        
        this.videoStack = this.container.querySelector('#video-stack');
        this.playPauseBtn = this.container.querySelector('#play-pause-btn');
        this.progressBars = this.container.querySelectorAll('.progress-bar');
    }
    
    setupEventListeners() {
        // Touch events for mobile
        this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events for desktop
        this.container.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.container.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });
        
        // Keyboard events
        document.addEventListener('keydown', this.handleKeydown.bind(this));
        
        // Click to play/pause
        this.container.addEventListener('click', this.handleClick.bind(this));
        
        // Action buttons
        this.container.querySelector('#like-btn').addEventListener('click', this.handleLike.bind(this));
        this.container.querySelector('#share-btn').addEventListener('click', this.handleShare.bind(this));
        this.container.querySelector('#bookmark-btn').addEventListener('click', this.handleBookmark.bind(this));
        
        // Visibility change (pause when tab is not active)
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }
    
    loadVideos() {
        this.videos.forEach((video, index) => {
            const videoElement = document.createElement('video');
            videoElement.className = `absolute inset-0 w-full h-full object-cover ${index === 0 ? 'z-10' : 'z-0'}`;
            videoElement.style.transform = index === 0 ? 'translateY(0%)' : 'translateY(100%)';
            videoElement.preload = index < this.settings.preloadCount ? 'auto' : 'metadata';
            videoElement.muted = false;
            videoElement.volume = this.settings.volume;
            videoElement.playsInline = true;
            
            // Add video sources
            if (video.file_path) {
                videoElement.src = video.file_path;
            }
            
            // Event listeners for video
            videoElement.addEventListener('loadedmetadata', () => {
                this.updateVideoInfo(index);
            });
            
            videoElement.addEventListener('timeupdate', () => {
                if (index === this.currentIndex) {
                    this.updateProgress();
                }
            });
            
            videoElement.addEventListener('ended', () => {
                if (index === this.currentIndex) {
                    // Track completion when video ends naturally
                    this.trackVideoCompletion(index);
                    
                    if (this.settings.autoplayNext) {
                        this.nextVideo();
                    }
                }
            });
            
            videoElement.addEventListener('error', (e) => {
                console.error('Video loading error:', e);
                this.showError(`Failed to load video: ${video.title}`);
            });
            
            this.videoElements.push(videoElement);
            this.videoStack.appendChild(videoElement);
        });
    }
    
    loadCurrentVideo() {
        if (this.videos.length === 0) return;
        
        const currentVideo = this.videoElements[this.currentIndex];
        if (currentVideo && currentVideo.readyState < 2) {
            this.showLoading(true);
            currentVideo.addEventListener('loadeddata', () => {
                this.showLoading(false);
            }, { once: true });
        }
        
        this.updateVideoInfo(this.currentIndex);
        this.updateProgressBars();
    }
    
    handleTouchStart(e) {
        if (this.isTransitioning) return;
        
        this.touchStartY = e.touches[0].clientY;
        this.touchStartX = e.touches[0].clientX;
        e.preventDefault();
    }
    
    handleTouchMove(e) {
        if (this.isTransitioning) return;
        e.preventDefault();
    }
    
    handleTouchEnd(e) {
        if (this.isTransitioning) return;
        
        const touchEndY = e.changedTouches[0].clientY;
        const touchEndX = e.changedTouches[0].clientX;
        const deltaY = this.touchStartY - touchEndY;
        const deltaX = Math.abs(this.touchStartX - touchEndX);
        
        // Vertical swipe (video navigation)
        if (Math.abs(deltaY) > this.settings.swipeThreshold && deltaX < this.settings.swipeThreshold) {
            if (deltaY > 0) {
                this.nextVideo();
            } else {
                this.previousVideo();
            }
        }
        // Horizontal swipe or tap (play/pause)
        else if (Math.abs(deltaY) < this.settings.swipeThreshold) {
            this.togglePlayPause();
        }
    }
    
    handleMouseDown(e) {
        // Don't interfere with action buttons
        if (e.target.closest('.action-btn') || e.target.closest('#play-pause-btn')) return;
        
        // Start mouse drag tracking
        this.mouseStartY = e.clientY;
        this.mouseStartX = e.clientX;
        this.isDragging = true;
        
        // Add mouse move and up listeners
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        e.preventDefault();
    }
    
    handleMouseMove(e) {
        if (!this.isDragging || this.isTransitioning) return;
        
        const deltaY = this.mouseStartY - e.clientY;
        const deltaX = Math.abs(this.mouseStartX - e.clientX);
        
        // Show visual feedback for dragging
        if (Math.abs(deltaY) > 10) {
            this.container.style.cursor = deltaY > 0 ? 'n-resize' : 's-resize';
        }
    }
    
    handleMouseUp(e) {
        if (!this.isDragging) return;
        
        const deltaY = this.mouseStartY - e.clientY;
        const deltaX = Math.abs(this.mouseStartX - e.clientX);
        
        // Reset cursor
        this.container.style.cursor = 'pointer';
        
        // Clean up listeners
        document.removeEventListener('mousemove', this.handleMouseMove.bind(this));
        document.removeEventListener('mouseup', this.handleMouseUp.bind(this));
        
        this.isDragging = false;
        
        // Check if it's a swipe gesture
        if (Math.abs(deltaY) > this.settings.swipeThreshold && deltaX < this.settings.swipeThreshold) {
            if (deltaY > 0) {
                this.nextVideo();
            } else {
                this.previousVideo();
            }
        }
        // Otherwise it's a simple click
        else if (Math.abs(deltaY) < 10 && deltaX < 10) {
            this.togglePlayPause();
        }
    }
    
    handleWheel(e) {
        if (this.isTransitioning) return;
        
        e.preventDefault();
        if (e.deltaY > 0) {
            this.nextVideo();
        } else {
            this.previousVideo();
        }
    }
    
    handleKeydown(e) {
        if (this.isTransitioning) return;
        
        // Only handle keys if player is in focus or visible
        const playerRect = this.container.getBoundingClientRect();
        const isPlayerVisible = playerRect.top < window.innerHeight && playerRect.bottom > 0;
        
        if (!isPlayerVisible) return;
        
        switch(e.key) {
            case 'ArrowUp':
                e.preventDefault(); // Prevent page scroll
                e.stopPropagation();
                this.nextVideo();
                break;
            case 'ArrowDown':
                e.preventDefault(); // Prevent page scroll
                e.stopPropagation();
                this.previousVideo();
                break;
            case ' ':
                e.preventDefault(); // Prevent page scroll
                e.stopPropagation();
                this.togglePlayPause();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                e.stopPropagation();
                this.seekBackward();
                break;
            case 'ArrowRight':
                e.preventDefault();
                e.stopPropagation();
                this.seekForward();
                break;
        }
    }
    
    handleClick(e) {
        if (e.target.closest('.action-btn') || e.target.closest('#play-pause-btn')) return;
        
        // Check if clicking in bottom area (video info zone)
        const rect = this.container.getBoundingClientRect();
        const clickY = e.clientY - rect.top;
        const containerHeight = rect.height;
        const bottomThreshold = containerHeight * 0.7; // Bottom 30% of screen
        
        if (clickY > bottomThreshold) {
            // Clicked in bottom area - toggle video info
            this.toggleVideoInfo();
        } else {
            // Clicked elsewhere - play/pause
            this.togglePlayPause();
        }
    }
    
    handleLike(e) {
        e.stopPropagation();
        const video = this.videos[this.currentIndex];
        this.toggleLike(video.id);
    }
    
    handleShare(e) {
        e.stopPropagation();
        const video = this.videos[this.currentIndex];
        this.shareVideo(video);
    }
    
    handleBookmark(e) {
        e.stopPropagation();
        const video = this.videos[this.currentIndex];
        this.toggleBookmark(video.id);
    }
    
    handleVisibilityChange() {
        if (document.hidden && this.isPlaying) {
            this.pause();
        }
    }
    
    nextVideo() {
        if (this.currentIndex < this.videos.length - 1) {
            this.navigateToVideo(this.currentIndex + 1);
        }
    }
    
    previousVideo() {
        if (this.currentIndex > 0) {
            this.navigateToVideo(this.currentIndex - 1);
        }
    }
    
    navigateToVideo(newIndex) {
        if (this.isTransitioning || newIndex === this.currentIndex) return;
        
        this.isTransitioning = true;
        const currentElement = this.videoElements[this.currentIndex];
        const nextElement = this.videoElements[newIndex];
        
        // Pause current video
        this.pause();
        
        // Track completion if moving forward
        if (newIndex > this.currentIndex) {
            this.trackVideoCompletion(this.currentIndex);
        }
        
        // Animate transition
        const direction = newIndex > this.currentIndex ? -100 : 100;
        
        currentElement.style.transition = `transform ${this.settings.transitionDuration}ms ease-out`;
        nextElement.style.transition = `transform ${this.settings.transitionDuration}ms ease-out`;
        
        currentElement.style.transform = `translateY(${-direction}%)`;
        nextElement.style.transform = 'translateY(0%)';
        
        setTimeout(() => {
            // Reset positions
            this.videoElements.forEach((el, index) => {
                el.style.transition = '';
                if (index === newIndex) {
                    el.style.transform = 'translateY(0%)';
                    el.style.zIndex = '10';
                } else if (index > newIndex) {
                    el.style.transform = 'translateY(100%)';
                    el.style.zIndex = '0';
                } else {
                    el.style.transform = 'translateY(-100%)';
                    el.style.zIndex = '0';
                }
            });
            
            this.currentIndex = newIndex;
            this.updateVideoInfo(newIndex);
            this.updateProgressBars();
            this.showVideoInfo(); // Show info when video changes
            this.videoCompletionTracked = false; // Reset completion tracking for new video
            this.isTransitioning = false;
            
            // Auto-play new video
            this.play();
            
        }, this.settings.transitionDuration);
    }
    
    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    play() {
        const currentVideo = this.videoElements[this.currentIndex];
        if (currentVideo) {
            currentVideo.play().then(() => {
                this.isPlaying = true;
                this.playPauseBtn.querySelector('i').className = 'fas fa-pause fa-2x';
                this.startProgressTracking();
                this.hidePlayPauseButton();
            }).catch(console.error);
        }
    }
    
    pause() {
        const currentVideo = this.videoElements[this.currentIndex];
        if (currentVideo) {
            currentVideo.pause();
            this.isPlaying = false;
            this.playPauseBtn.querySelector('i').className = 'fas fa-play fa-2x';
            this.stopProgressTracking();
            this.showPlayPauseButton();
        }
    }
    
    seekForward() {
        const currentVideo = this.videoElements[this.currentIndex];
        if (currentVideo) {
            currentVideo.currentTime = Math.min(currentVideo.duration, currentVideo.currentTime + 10);
        }
    }
    
    seekBackward() {
        const currentVideo = this.videoElements[this.currentIndex];
        if (currentVideo) {
            currentVideo.currentTime = Math.max(0, currentVideo.currentTime - 10);
        }
    }
    
    updateVideoInfo(index) {
        const video = this.videos[index];
        if (!video) return;
        
        this.container.querySelector('#video-title').textContent = video.title || 'Untitled';
        this.container.querySelector('#video-description').textContent = video.description || '';
        this.container.querySelector('#video-counter').textContent = `${index + 1} / ${this.videos.length}`;
        
        const videoElement = this.videoElements[index];
        if (videoElement && videoElement.duration) {
            this.container.querySelector('#video-duration').textContent = this.formatTime(videoElement.duration);
        }
    }
    
    updateProgress() {
        const currentVideo = this.videoElements[this.currentIndex];
        if (!currentVideo || !currentVideo.duration) return;
        
        const progress = (currentVideo.currentTime / currentVideo.duration) * 100;
        const progressBar = this.progressBars[this.currentIndex];
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Track progress periodically and check for completion
        const isCompleted = progress >= 95;
        
        // Check for recommended session completion FIRST (before stopping progress tracking)
        if (this.isRecommendedSession && !this.recommendedSessionCompleted && progress >= 100) {
            const currentVideo = this.videos[this.currentIndex];
            if (currentVideo && currentVideo.id === this.lastVideoInRecommendedSession) {
                console.log('Last video in recommended session completed!');
                this.recommendedSessionCompleted = true;
                this.stopProgressTracking(); // Stop all further updates
                this.showRecommendedSessionCompletionPopup();
            }
        }
        
        // Only track progress if recommended session is not completed
        if (!this.recommendedSessionCompleted) {
            this.trackVideoProgress(this.currentIndex, currentVideo.currentTime, isCompleted);
        }
        
        // Track completion when reaching 95% (only once per video)
        if (isCompleted && !this.videoCompletionTracked) {
            this.trackVideoCompletion(this.currentIndex);
            this.videoCompletionTracked = true;
        }
    }
    
    updateProgressBars() {
        this.progressBars.forEach((bar, index) => {
            if (index < this.currentIndex) {
                bar.style.width = '100%';
            } else if (index === this.currentIndex) {
                const currentVideo = this.videoElements[index];
                if (currentVideo && currentVideo.duration) {
                    const progress = (currentVideo.currentTime / currentVideo.duration) * 100;
                    bar.style.width = `${progress}%`;
                }
            } else {
                bar.style.width = '0%';
            }
        });
    }
    
    startProgressTracking() {
        this.stopProgressTracking();
        this.progressUpdateInterval = setInterval(() => {
            this.updateProgress();
        }, this.settings.progressUpdateFrequency);
    }
    
    stopProgressTracking() {
        if (this.progressUpdateInterval) {
            clearInterval(this.progressUpdateInterval);
            this.progressUpdateInterval = null;
        }
    }
    
    showPlayPauseButton() {
        this.playPauseBtn.style.opacity = '1';
    }
    
    hidePlayPauseButton() {
        this.playPauseBtn.style.opacity = '0';
    }
    
    showLoading(show) {
        const loader = this.container.querySelector('#loading-indicator');
        loader.style.display = show ? 'flex' : 'none';
    }
    
    showError(message) {
        console.error('Video Player Error:', message);
        // Could implement toast notification here
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Video Info Visibility Methods
    
    showVideoInfo() {
        const infoOverlay = this.container.querySelector('#video-info-overlay');
        if (!infoOverlay) return;
        
        infoOverlay.style.opacity = '1';
        this.infoVisible = true;
        
        // Auto-hide after 3 seconds
        clearTimeout(this.infoTimeout);
        this.infoTimeout = setTimeout(() => {
            this.hideVideoInfo();
        }, 3000);
    }
    
    hideVideoInfo() {
        const infoOverlay = this.container.querySelector('#video-info-overlay');
        if (!infoOverlay) return;
        
        infoOverlay.style.opacity = '0';
        this.infoVisible = false;
    }
    
    toggleVideoInfo() {
        clearTimeout(this.infoTimeout); // Cancel auto-hide when manually toggling
        
        if (this.infoVisible) {
            this.hideVideoInfo();
        } else {
            this.showVideoInfo();
        }
    }
    
    // API Integration Methods
    
    async toggleLike(videoId) {
        try {
            const endpoint = `/learning/api/shorts/${videoId}/like`;
                
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ shorts_id: videoId })
            });
            
            const result = await response.json();
            if (result.success) {
                const likeBtn = this.container.querySelector('#like-btn');
                const likeCount = likeBtn.querySelector('.like-count');
                
                if (result.liked) {
                    likeBtn.classList.add('text-red-400');
                    likeCount.textContent = parseInt(likeCount.textContent) + 1;
                } else {
                    likeBtn.classList.remove('text-red-400');
                    likeCount.textContent = Math.max(0, parseInt(likeCount.textContent) - 1);
                }
            }
        } catch (error) {
            console.error('Error toggling like:', error);
        }
    }
    
    async shareVideo(video) {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: video.title,
                    text: video.description,
                    url: window.location.href
                });
            } catch (error) {
                console.log('Share cancelled');
            }
        } else {
            // Fallback: Copy to clipboard
            navigator.clipboard.writeText(window.location.href);
            // Could show toast notification
        }
    }
    
    async toggleBookmark(videoId) {
        // Implementation depends on your bookmarking system
        console.log('Toggle bookmark for video:', videoId);
    }
    
    async trackVideoProgress(index, currentTime, completed) {
        const video = this.videos[index];
        if (!video) return;
        
        try {
            const endpoint = `/learning/api/shorts/${video.id}/progress`;
                
            await fetch(endpoint, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    shorts_id: video.id,
                    watch_percentage: completed ? 100 : (currentTime / this.videoElements[index].duration) * 100,
                    watch_time_seconds: currentTime,
                    swipe_direction: 'none'
                })
            });
        } catch (error) {
            console.error('Error tracking video progress:', error);
        }
    }
    
    async trackVideoCompletion(index) {
        const video = this.videos[index];
        const videoElement = this.videoElements[index];
        
        if (!video || !videoElement) return;
        
        try {
            const endpoint = `/learning/api/shorts/${video.id}/progress`;
                
            await fetch(endpoint, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    shorts_id: video.id,
                    watch_percentage: 100,
                    watch_time_seconds: videoElement.duration,
                    swipe_direction: 'up'
                })
            });
            
            // Only check submodule completion if not already handled in updateProgress
            if (!this.isRecommendedSession || !this.recommendedSessionCompleted) {
                this.checkSubmoduleCompletion(index);
            }
            
        } catch (error) {
            console.error('Error tracking video completion:', error);
        }
    }
    
    checkSubmoduleCompletion(completedIndex) {
        console.log('checkSubmoduleCompletion called:', { 
            completedIndex, 
            totalVideos: this.videos.length, 
            isRecommendedSession: this.isRecommendedSession 
        });
        
        // Use existing state variables instead of re-parsing URL parameters
        if (this.isRecommendedSession && completedIndex === this.videos.length - 1) {
            const currentVideo = this.videos[completedIndex];
            if (currentVideo && currentVideo.theory_module_ref) {
                const currentSubmodule = currentVideo.theory_module_ref;
                console.log('Showing completion popup for submodule:', currentSubmodule);
                this.showSubmoduleCompletionPopup(currentSubmodule, this.videos.length);
            }
        }
    }
    
    showRecommendedSessionCompletionPopup() {
        // Get current video info for display
        const currentVideo = this.videos[this.currentIndex];
        const submodule = currentVideo ? (currentVideo.theory_module_ref || currentVideo.submodule_id || 'Anbefaling') : 'Anbefaling';
        const submoduleVideos = this.videos.filter(v => (v.theory_module_ref || v.submodule_id) === (currentVideo.theory_module_ref || currentVideo.submodule_id));
        
        this.showSubmoduleCompletionPopup(submodule, submoduleVideos.length);
    }
    
    showSubmoduleCompletionPopup(submodule, videosCompleted) {
        // Create completion modal with two-button design
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-gradient-to-br from-green-500 to-teal-600 rounded-2xl p-8 max-w-md w-full text-center text-white shadow-2xl">
                <div class="mb-8">
                    <div class="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <i class="fas fa-check-circle fa-4x text-white"></i>
                    </div>
                    <h2 class="text-3xl font-bold mb-3">Gratulerer! 🎉</h2>
                    <p class="text-green-100 text-lg mb-2">Du har fullført anbefalingen!</p>
                    <p class="text-green-200 text-sm">Modul ${submodule || 'Anbefaling'} - ${videosCompleted || 0} videoer sett</p>
                </div>
                
                <div class="space-y-4">
                    <button id="continue-learning" class="w-full bg-white text-green-600 font-bold py-4 px-6 rounded-xl hover:bg-green-50 transition-all duration-300 transform hover:scale-105">
                        <i class="fas fa-play mr-2"></i>
                        Fortsett læring
                    </button>
                    <button id="back-to-dashboard" class="w-full bg-transparent border-2 border-white text-white font-bold py-4 px-6 rounded-xl hover:bg-white hover:text-green-600 transition-all duration-300">
                        <i class="fas fa-home mr-2"></i>
                        Tilbake til oversikt
                    </button>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('#continue-learning').addEventListener('click', async () => {
            modal.remove();
            await this.continueToNextIncompleteVideos();
        });
        
        modal.querySelector('#back-to-dashboard').addEventListener('click', () => {
            modal.remove();
            window.location.href = '/learning/theory';
        });
        
        // Track completion event for analytics
        if (window.gtag) {
            gtag('event', 'submodule_completion', {
                'event_category': 'learning',
                'event_label': `submodule_${submodule}`,
                'value': videosCompleted
            });
        }
    }
    
    async continueToNextIncompleteVideos() {
        try {
            // Call the backend to get all incomplete videos ordered from lowest to highest
            const response = await fetch('/learning/api/shorts/incomplete-session');
            const data = await response.json();
            
            if (data.success && data.videos && data.videos.length > 0) {
                // Transition to incomplete videos session
                this.videos = data.videos;
                this.currentIndex = 0;
                this.videoCompletionTracked = false;
                
                // Reset recommendation session state for normal tracking
                this.isRecommendedSession = false;
                this.recommendedSessionCompleted = false;
                this.lastVideoInRecommendedSession = null;
                
                // Change URL to reflect the new session type
                window.history.replaceState({}, '', '/learning/shorts/continue-learning');
                
                // Rebuild video elements
                this.videoStack.innerHTML = '';
                this.videoElements = [];
                this.loadVideos();
                this.loadCurrentVideo();
                this.updateVideoInfo(0);
                
                // Start playing the first incomplete video
                setTimeout(() => {
                    this.play();
                }, 500);
                
            } else {
                // No incomplete videos found - redirect to dashboard
                window.location.href = '/learning/theory';
            }
            
        } catch (error) {
            console.error('Error loading incomplete videos:', error);
            // Fallback to dashboard
            window.location.href = '/learning/theory';
        }
    }
    
    async loadAllVideosForSession() {
        try {
            // Extract start_video parameter from URL
            const urlParams = new URLSearchParams(window.location.search);
            const startVideoId = urlParams.get('start_video');
            
            // Build API URL with both submodule and video parameters
            let apiUrl = '/learning/api/shorts/all-session';
            const params = new URLSearchParams();
            
            if (this.startingSubmodule) {
                params.set('start', this.startingSubmodule);
            }
            if (startVideoId) {
                params.set('start_video', startVideoId);
            }
            
            if (params.toString()) {
                apiUrl += '?' + params.toString();
            }
            
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            if (data.success) {
                this.videos = data.videos;
                this.loadVideos(); // Rebuild video elements
                this.loadCurrentVideo();
                this.updateVideoInfo(this.currentIndex);
            }
        } catch (error) {
            console.error('Error loading all session videos:', error);
            // Fallback to provided videos
            this.loadVideos();
            this.loadCurrentVideo();
        }
    }

    // Public Methods
    
    getCurrentVideo() {
        return this.videos[this.currentIndex];
    }
    
    getCurrentIndex() {
        return this.currentIndex;
    }
    
    destroy() {
        this.stopProgressTracking();
        clearTimeout(this.infoTimeout);
        this.videoElements.forEach(video => {
            video.pause();
            video.src = '';
        });
        
        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeydown.bind(this));
        document.removeEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }
}

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const playerContainer = document.querySelector('#video-container');
    const videosData = window.shortsData || [];
    
    if (playerContainer && videosData.length > 0) {
        window.shortsPlayer = new ShortsPlayer(playerContainer, videosData, {
            crossModuleEnabled: window.playerConfig.crossModuleEnabled || false,  // Use dynamic setting
            startingSubmodule: window.submoduleId,
            startVideoIndex: window.playerConfig.startVideoIndex
        });
        
        // Auto-play first video after 500ms
        setTimeout(() => {
            if (window.shortsPlayer) {
                window.shortsPlayer.play();
            }
        }, 500);
    }
});
