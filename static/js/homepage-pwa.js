/**
 * Homepage PWA Banner Enhancement
 * Professional install prompt for homepage only
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on homepage
    if (window.location.pathname !== '/' && !window.location.pathname.endsWith('/index.html')) {
        return;
    }

    const banner = document.getElementById('pwa-install-banner');
    if (!banner) return;

    // Enhanced banner controller
    class HomepagePWABanner {
        constructor(bannerElement) {
            this.banner = bannerElement;
            this.installBtn = this.banner.querySelector('#pwa-install-btn');
            this.dismissBtn = this.banner.querySelector('#pwa-dismiss-btn');
            this.isVisible = false;
            
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.checkIfShouldShow();
        }

        setupEventListeners() {
            // Install button with enhanced feedback
            if (this.installBtn) {
                this.installBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleInstallClick();
                });

                // Add pulse effect on hover
                this.installBtn.addEventListener('mouseenter', () => {
                    this.installBtn.classList.add('pulse');
                });

                this.installBtn.addEventListener('mouseleave', () => {
                    this.installBtn.classList.remove('pulse');
                });
            }

            // Dismiss button with smooth animation
            if (this.dismissBtn) {
                this.dismissBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleDismissClick();
                });
            }

            // Listen for PWA events from main PWA installer
            window.addEventListener('pwa-installable', () => {
                this.showBanner();
            });

            window.addEventListener('pwa-installed', () => {
                this.hideBanner();
            });
        }

        checkIfShouldShow() {
            // Check if PWA is installable and not already dismissed
            const dismissed = localStorage.getItem('pwa-install-dismissed');
            const lastDismissed = localStorage.getItem('pwa-install-dismissed-time');
            
            // Show again after 7 days
            const canShow = !dismissed || (Date.now() - parseInt(lastDismissed) > 7 * 24 * 60 * 60 * 1000);
            
            if (canShow && window.pwaInstaller && window.pwaInstaller.isInstallable) {
                setTimeout(() => {
                    this.showBanner();
                }, 3000); // Show after 3 seconds on homepage
            }
        }

        showBanner() {
            if (this.isVisible) return;

            this.banner.style.display = 'block';
            this.banner.classList.add('banner-animate-in');
            
            // Smooth reveal animation
            setTimeout(() => {
                this.banner.style.opacity = '1';
                this.banner.style.transform = 'translateY(0)';
                this.isVisible = true;
            }, 100);

            // Track banner impression
            this.trackEvent('pwa_banner_shown', { location: 'homepage' });
        }

        hideBanner() {
            if (!this.isVisible) return;

            this.banner.style.opacity = '0';
            this.banner.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                this.banner.style.display = 'none';
                this.isVisible = false;
            }, 300);
        }

        handleInstallClick() {
            // Add loading state
            const originalText = this.installBtn.innerHTML;
            this.installBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Installerer...';
            this.installBtn.disabled = true;

            // Track click event
            this.trackEvent('pwa_install_clicked', { location: 'homepage' });

            // Trigger install via main PWA installer
            if (window.pwaInstaller) {
                window.pwaInstaller.installPWA().then(() => {
                    // Reset button state
                    this.installBtn.innerHTML = originalText;
                    this.installBtn.disabled = false;
                }).catch(() => {
                    // Reset button state on error
                    this.installBtn.innerHTML = originalText;
                    this.installBtn.disabled = false;
                });
            }
        }

        handleDismissClick() {
            this.trackEvent('pwa_banner_dismissed', { location: 'homepage' });
            
            // Store dismissal
            localStorage.setItem('pwa-install-dismissed', 'true');
            localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
            
            this.hideBanner();
        }

        trackEvent(eventName, parameters = {}) {
            // Google Analytics tracking
            if (typeof gtag !== 'undefined') {
                gtag('event', eventName, {
                    'event_category': 'PWA',
                    'event_label': 'Homepage Banner',
                    ...parameters
                });
            }

            // Console logging for development
            console.log(`PWA Event: ${eventName}`, parameters);
        }
    }

    // Initialize the homepage banner
    const homepageBanner = new HomepagePWABanner(banner);

    // Make it globally accessible
    window.homepagePWABanner = homepageBanner;

    // Enhanced scroll-based visibility (optional)
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const scrollProgress = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
            
            // Show banner when user scrolls 30% down the page (if not already shown)
            if (scrollProgress > 0.3 && !homepageBanner.isVisible) {
                homepageBanner.checkIfShouldShow();
            }
        }, 100);
    });
});
