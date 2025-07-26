/**
 * Quiz Image Enhancements
 * Provides advanced mobile image handling, zoom functionality, and responsive adjustments
 */

class QuizImageEnhancer {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.enhanceImages();
        this.addImageLoadHandlers();
        this.addTouchZoom();
        this.addKeyboardAccessibility();
        this.handleOrientationChange();
    }

    enhanceImages() {
        const images = document.querySelectorAll('.question-image');
        
        images.forEach(img => {
            // Add error handling
            img.addEventListener('error', this.handleImageError.bind(this));
            
            // Add load optimization
            img.addEventListener('load', this.handleImageLoad.bind(this));
            
            // Add click handler for zoom on mobile
            img.addEventListener('click', this.handleImageClick.bind(this));
            
            // Ensure proper aspect ratio
            this.adjustImageSize(img);
        });
    }

    handleImageError(event) {
        const img = event.target;
        console.warn('Quiz image failed to load:', img.src);
        
        // Create fallback placeholder
        const container = img.closest('.question-image-container');
        if (container) {
            container.innerHTML = `
                <div class="image-placeholder bg-gray-200 border-2 border-dashed border-gray-400 rounded-lg p-8 text-center max-w-full">
                    <i class="fas fa-image text-4xl text-gray-400 mb-2"></i>
                    <p class="text-gray-600">Bildet kunne ikke lastes</p>
                </div>
            `;
        }
    }

    handleImageLoad(event) {
        const img = event.target;
        
        // Check if image is too large and adjust
        this.adjustImageSize(img);
        
        // Add loaded class for animations
        img.classList.add('image-loaded');
    }

    adjustImageSize(img) {
        // Get container dimensions
        const container = img.closest('.question-image-container') || img.parentElement;
        if (!container) return;

        // Get container's available space
        const containerRect = container.getBoundingClientRect();
        const containerWidth = containerRect.width;
        
        // Get parent card/section for height reference
        const questionCard = img.closest('.question-card') || container.closest('.glass');
        const cardRect = questionCard ? questionCard.getBoundingClientRect() : containerRect;
        
        // Calculate available height (card height minus padding and other content)
        const cardPadding = 64; // Approximate padding from .p-8 class
        const otherContentHeight = 200; // Approximate space for question text and options
        const availableHeight = Math.max(cardRect.height - cardPadding - otherContentHeight, 200);
        
        // Use container dimensions with reasonable limits
        const maxWidth = Math.min(containerWidth, 800); // Never wider than 800px
        const maxHeight = Math.min(availableHeight, 400); // Never taller than 400px
        
        // Set dynamic constraints based on container, not viewport
        img.style.maxHeight = `${maxHeight}px`;
        img.style.maxWidth = `${maxWidth}px`;
        
        // Ensure the image fits within its container
        img.style.width = 'auto';
        img.style.height = 'auto';
    }

    handleImageClick(event) {
        // Only on mobile/touch devices
        if (!this.isTouchDevice()) return;
        
        const img = event.target;
        this.showImageModal(img);
    }

    showImageModal(img) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'image-modal-overlay';
        modal.innerHTML = `
            <div class="image-modal-content">
                <button class="image-modal-close" aria-label="Lukk bilde">
                    <i class="fas fa-times"></i>
                </button>
                <img src="${img.src}" alt="${img.alt}" class="image-modal-img">
            </div>
        `;

        // Add styles
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        `;

        const content = modal.querySelector('.image-modal-content');
        content.style.cssText = `
            position: relative;
            max-width: 95%;
            max-height: 95%;
            text-align: center;
        `;

        const modalImg = modal.querySelector('.image-modal-img');
        modalImg.style.cssText = `
            max-width: 100%;
            max-height: 90vh;
            width: auto;
            height: auto;
            object-fit: contain;
            border-radius: 8px;
        `;

        const closeBtn = modal.querySelector('.image-modal-close');
        closeBtn.style.cssText = `
            position: absolute;
            top: -40px;
            right: 0;
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            color: #333;
        `;

        // Add to page
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        // Close handlers
        const closeModal = () => {
            document.body.removeChild(modal);
            document.body.style.overflow = '';
        };

        closeBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Keyboard close
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        });
    }

    addTouchZoom() {
        if (!this.isTouchDevice()) return;

        const images = document.querySelectorAll('.question-image');

        images.forEach(img => {
            let touchStartTime = 0;
            
            img.addEventListener('touchstart', (e) => {
                touchStartTime = Date.now();
            });

            img.addEventListener('touchend', (event) => {
                const touchDuration = Date.now() - touchStartTime;
                
                // Quick tap (under 200ms) = zoom toggle
                if (touchDuration < 200 && event.touches.length === 0) {
                    event.preventDefault();
                    this.toggleImageZoom(img);
                }
            });
        });
    }

    toggleImageZoom(img) {
        const isZoomed = img.classList.contains('zoomed');
        
        if (isZoomed) {
            img.classList.remove('zoomed');
            img.style.transform = '';
            img.style.position = '';
            img.style.zIndex = '';
        } else {
            img.classList.add('zoomed');
            img.style.transform = 'scale(1.5)';
            img.style.position = 'relative';
            img.style.zIndex = '10';
            
            // Auto-unzoom after 3 seconds
            setTimeout(() => {
                if (img.classList.contains('zoomed')) {
                    this.toggleImageZoom(img);
                }
            }, 3000);
        }
    }

    addKeyboardAccessibility() {
        const images = document.querySelectorAll('.question-image');
        
        images.forEach(img => {
            // Make images focusable
            img.setAttribute('tabindex', '0');
            img.setAttribute('role', 'button');
            img.setAttribute('aria-label', 'Trykk for å forstørre bildet');

            img.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.handleImageClick(e);
                }
            });
        });
    }

    handleOrientationChange() {
        window.addEventListener('orientationchange', () => {
            // Wait for orientation change to complete
            setTimeout(() => {
                const images = document.querySelectorAll('.question-image');
                images.forEach(img => this.adjustImageSize(img));
            }, 100);
        });

        // Also handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const images = document.querySelectorAll('.question-image');
                images.forEach(img => this.adjustImageSize(img));
            }, 150);
        });
    }

    addImageLoadHandlers() {
        // Intersection Observer for lazy loading optimization
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.optimizeImageLoading(img);
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('.question-image[loading="lazy"]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    optimizeImageLoading(img) {
        // Add loading animation
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease';
        
        img.addEventListener('load', () => {
            img.style.opacity = '1';
        }, { once: true });
    }

    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
}

// Auto-initialize when script loads
if (typeof window !== 'undefined') {
    window.QuizImageEnhancer = QuizImageEnhancer;
    
    // Auto-start for quiz pages
    if (document.querySelector('.question-image')) {
        new QuizImageEnhancer();
    }
}

// CSS animations for modal
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .image-loaded {
        animation: slideInImage 0.4s ease-out;
    }
    
    @keyframes slideInImage {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .question-image.zoomed {
        transition: transform 0.3s ease;
    }
`;
document.head.appendChild(style);