// static/js/video-player.js

class VideoPlayer {
    constructor() {
        this.videoId = null;
        this.player = null;
        this.checkpoints = [];
        this.currentTime = 0;
        this.duration = 0;
        this.progressInterval = null;
        this.passedCheckpoints = new Set();
        
        this.init();
    }
    
    init() {
        // Get video element or YouTube player
        const videoElement = document.getElementById('video-player');
        const youtubeFrame = document.getElementById('youtube-player');
        
        if (videoElement) {
            this.initHTML5Player(videoElement);
        } else if (youtubeFrame) {
            this.initYouTubePlayer();
        }
        
        // Initialize other components
        this.initCheckpoints();
        this.initRating();
        this.initBookmark();
        this.initNotes();
    }
    
    initHTML5Player(videoElement) {
        this.player = videoElement;
        this.videoId = videoElement.dataset.videoId;
        
        // Set up event listeners
        this.player.addEventListener('loadedmetadata', () => {
            this.duration = this.player.duration;
        });
        
        this.player.addEventListener('timeupdate', () => {
            this.onTimeUpdate();
        });
        
        this.player.addEventListener('play', () => {
            this.startProgressTracking();
        });
        
        this.player.addEventListener('pause', () => {
            this.stopProgressTracking();
        });
        
        this.player.addEventListener('ended', () => {
            this.onVideoEnd();
        });
        
        // Resume from last position
        const lastPosition = this.getLastPosition();
        if (lastPosition > 0) {
            this.player.currentTime = lastPosition;
        }
    }
    
    initYouTubePlayer() {
        // YouTube API will be loaded separately
        window.onYouTubeIframeAPIReady = () => {
            const iframe = document.getElementById('youtube-player');
            this.videoId = iframe.src.match(/embed\/([^?]+)/)[1];
            
            this.player = new YT.Player('youtube-player', {
                events: {
                    'onReady': (event) => this.onYouTubeReady(event),
                    'onStateChange': (event) => this.onYouTubeStateChange(event)
                }
            });
        };
        
        // Load YouTube API
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        document.body.appendChild(tag);
    }
    
    onYouTubeReady(event) {
        this.duration = this.player.getDuration();
        
        // Resume from last position
        const lastPosition = this.getLastPosition();
        if (lastPosition > 0) {
            this.player.seekTo(lastPosition);
        }
    }
    
    onYouTubeStateChange(event) {
        if (event.data === YT.PlayerState.PLAYING) {
            this.startProgressTracking();
        } else if (event.data === YT.PlayerState.PAUSED) {
            this.stopProgressTracking();
        } else if (event.data === YT.PlayerState.ENDED) {
            this.onVideoEnd();
        }
    }
    
    onTimeUpdate() {
        if (this.player.currentTime) {
            this.currentTime = this.player.currentTime;
            this.updateProgressBar();
            this.checkForCheckpoints();
        }
    }
    
    updateProgressBar() {
        const progressBar = document.getElementById('progress-bar');
        if (progressBar && this.duration > 0) {
            const progress = (this.currentTime / this.duration) * 100;
            progressBar.style.width = progress + '%';
        }
    }
    
    initCheckpoints() {
        const markers = document.querySelectorAll('.checkpoint-marker');
        markers.forEach(marker => {
            const checkpointId = marker.dataset.checkpointId;
            const timestamp = parseInt(marker.dataset.timestamp);
            
            this.checkpoints.push({
                id: checkpointId,
                timestamp: timestamp,
                element: marker
            });
            
            // Add click handler
            marker.addEventListener('click', () => {
                this.seekTo(timestamp);
            });
        });
    }
    
    checkForCheckpoints() {
        this.checkpoints.forEach(checkpoint => {
            if (!this.passedCheckpoints.has(checkpoint.id)) {
                if (this.currentTime >= checkpoint.timestamp && 
                    this.currentTime < checkpoint.timestamp + 2) {
                    this.triggerCheckpoint(checkpoint);
                }
            }
        });
    }
    
    triggerCheckpoint(checkpoint) {
        // Pause video
        if (this.player.pause) {
            this.player.pause();
        } else if (this.player.pauseVideo) {
            this.player.pauseVideo();
        }
        
        // Load checkpoint question
        fetch(`/api/video/checkpoint/${checkpoint.id}`)
            .then(response => response.json())
            .then(data => {
                this.showCheckpointModal(checkpoint, data);
            });
    }
    
    showCheckpointModal(checkpoint, questionData) {
        const modal = new bootstrap.Modal(document.getElementById('checkpointModal'));
        const questionDiv = document.getElementById('checkpoint-question');
        
        // Build question HTML
        let html = `
            <h5>${questionData.question}</h5>
            ${questionData.image ? `<img src="/static/images/questions/${questionData.image}" class="img-fluid mb-3">` : ''}
            <div class="options">
        `;
        
        ['a', 'b', 'c', 'd'].forEach(option => {
            if (questionData[`option_${option}`]) {
                html += `
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="radio" name="checkpoint-answer" 
                               id="option-${option}" value="${option}">
                        <label class="form-check-label" for="option-${option}">
                            ${questionData[`option_${option}`]}
                        </label>
                    </div>
                `;
            }
        });
        
        html += '</div>';
        questionDiv.innerHTML = html;
        
        // Handle submit
        const submitBtn = document.getElementById('submit-checkpoint-btn');
        submitBtn.onclick = () => {
            const selectedOption = document.querySelector('input[name="checkpoint-answer"]:checked');
            if (selectedOption) {
                this.submitCheckpointAnswer(checkpoint.id, selectedOption.value);
                modal.hide();
            } else {
                alert('Vennligst velg et svar');
            }
        };
        
        modal.show();
    }
    
    submitCheckpointAnswer(checkpointId, answer) {
        fetch(`/video/checkpoint/${checkpointId}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                video_id: this.videoId,
                answer: answer
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.passedCheckpoints.add(checkpointId);
                this.showToast(data.message, data.is_correct ? 'success' : 'warning');
                
                // Resume video
                if (this.player.play) {
                    this.player.play();
                } else if (this.player.playVideo) {
                    this.player.playVideo();
                }
            }
        });
    }
    
    startProgressTracking() {
        if (this.progressInterval) return;
        
        this.progressInterval = setInterval(() => {
            this.saveProgress();
        }, 5000); // Save every 5 seconds
    }
    
    stopProgressTracking() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
            this.saveProgress(); // Save immediately when paused
        }
    }
    
    saveProgress() {
        const currentTime = this.getCurrentTime();
        
        fetch('/video/update-progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                video_id: this.videoId,
                position: Math.floor(currentTime)
            })
        });
        
        // Save to localStorage as backup
        localStorage.setItem(`video_progress_${this.videoId}`, currentTime);
    }
    
    getCurrentTime() {
        if (this.player.currentTime !== undefined) {
            return this.player.currentTime;
        } else if (this.player.getCurrentTime) {
            return this.player.getCurrentTime();
        }
        return 0;
    }
    
    getLastPosition() {
        const saved = localStorage.getItem(`video_progress_${this.videoId}`);
        return saved ? parseFloat(saved) : 0;
    }
    
    seekTo(seconds) {
        if (this.player.currentTime !== undefined) {
            this.player.currentTime = seconds;
        } else if (this.player.seekTo) {
            this.player.seekTo(seconds);
        }
    }
    
    onVideoEnd() {
        // Mark as completed
        this.saveProgress();
        this.showToast('Video fullført! +50 XP', 'success');
        
        // Show next video or recommendations
        const nextBtn = document.querySelector('.next-video a');
        if (nextBtn) {
            setTimeout(() => {
                if (confirm('Vil du se neste video i spillelisten?')) {
                    window.location.href = nextBtn.href;
                }
            }, 2000);
        }
    }
    
    initRating() {
        const stars = document.querySelectorAll('.star-rating');
        stars.forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.value);
                this.rateVideo(rating);
            });
            
            star.addEventListener('mouseenter', (e) => {
                const value = parseInt(e.target.dataset.value);
                this.highlightStars(value);
            });
        });
        
        const starsContainer = document.querySelector('.stars');
        if (starsContainer) {
            starsContainer.addEventListener('mouseleave', () => {
                const currentRating = parseInt(starsContainer.dataset.rating);
                this.highlightStars(currentRating);
            });
        }
    }
    
    highlightStars(rating) {
        const stars = document.querySelectorAll('.star-rating');
        stars.forEach((star, index) => {
            star.style.color = index < rating ? '#ffc107' : '#dee2e6';
        });
    }
    
    rateVideo(rating) {
        fetch('/video/rate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                video_id: this.videoId,
                rating: rating
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.querySelector('.stars').dataset.rating = rating;
                this.highlightStars(rating);
                this.showToast('Takk for din vurdering!', 'success');
            }
        });
    }
    
    initBookmark() {
        const bookmarkBtn = document.getElementById('bookmark-btn');
        if (bookmarkBtn) {
            bookmarkBtn.addEventListener('click', () => {
                this.toggleBookmark();
            });
        }
    }
    
    toggleBookmark() {
        const bookmarkBtn = document.getElementById('bookmark-btn');
        const videoId = bookmarkBtn.dataset.videoId;
        
        fetch(`/video/bookmark/${videoId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const isBookmarked = data.bookmarked;
                bookmarkBtn.dataset.bookmarked = isBookmarked;
                
                const icon = bookmarkBtn.querySelector('i');
                icon.className = `fas fa-bookmark${isBookmarked ? '' : '-o'} me-2`;
                bookmarkBtn.textContent = isBookmarked ? 'Fjern bokmerke' : 'Bokmerk';
                bookmarkBtn.prepend(icon);
                
                this.showToast(
                    isBookmarked ? 'Video bokmerket!' : 'Bokmerke fjernet',
                    'success'
                );
            }
        });
    }
    
    initNotes() {
        // Add note button
        const addNoteBtn = document.getElementById('add-note-btn');
        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', () => {
                const timestamp = this.getCurrentTime();
                document.getElementById('note-timestamp').value = this.formatTime(timestamp);
                document.getElementById('note-timestamp').dataset.seconds = timestamp;
            });
        }
        
        // Save note button
        const saveNoteBtn = document.getElementById('save-note-btn');
        if (saveNoteBtn) {
            saveNoteBtn.addEventListener('click', () => {
                this.saveNote();
            });
        }
        
        // Edit/Delete note buttons
        document.querySelectorAll('.edit-note').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.editNote(e.target.closest('button').dataset.noteId);
            });
        });
        
        document.querySelectorAll('.delete-note').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.deleteNote(e.target.closest('button').dataset.noteId);
            });
        });
    }
    
    saveNote() {
        const timestampInput = document.getElementById('note-timestamp');
        const noteText = document.getElementById('note-text').value.trim();
        
        if (!noteText) {
            alert('Vennligst skriv inn et notat');
            return;
        }
        
        fetch('/video/note', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                video_id: this.videoId,
                timestamp: Math.floor(parseFloat(timestampInput.dataset.seconds)),
                text: noteText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast('Notat lagret!', 'success');
                
                // Close modal and refresh page to show new note
                bootstrap.Modal.getInstance(document.getElementById('noteModal')).hide();
                setTimeout(() => location.reload(), 1000);
            }
        });
    }
    
    editNote(noteId) {
        const noteItem = document.querySelector(`[data-note-id="${noteId}"]`);
        const noteText = noteItem.querySelector('.note-text');
        const currentText = noteText.textContent;
        
        const newText = prompt('Rediger notat:', currentText);
        if (newText && newText !== currentText) {
            fetch(`/video/note/${noteId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    text: newText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    noteText.textContent = newText;
                    this.showToast('Notat oppdatert!', 'success');
                }
            });
        }
    }
    
    deleteNote(noteId) {
        if (confirm('Er du sikker på at du vil slette dette notatet?')) {
            fetch(`/video/note/${noteId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const noteItem = document.querySelector(`[data-note-id="${noteId}"]`);
                    noteItem.remove();
                    this.showToast('Notat slettet!', 'success');
                }
            });
        }
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.content : '';
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to toast container or create one
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoPlayer();
});
