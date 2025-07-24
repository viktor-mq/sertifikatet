/**
 * PWA Installer and Mobile Enhancements
 * Phase 10: Mobile Responsiveness and PWA
 */

class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isInstallable = false;
        
        this.init();
    }

    init() {
        this.registerServiceWorker();
        this.setupInstallPrompt();
        this.setupOfflineDetection();
        this.createInstallBanner();
        this.setupMobileOptimizations();
        this.initializeNotifications();
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });

                
                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailable();
                        }
                    });
                });
                
                // Listen for service worker messages
                navigator.serviceWorker.addEventListener('message', (event) => {
                    this.handleServiceWorkerMessage(event.data);
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    setupInstallPrompt() {
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('PWA install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.isInstallable = true;
            this.showInstallBanner();
        });

        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.isInstalled = true;
            this.hideInstallBanner();
            this.showInstalledMessage();
        });

        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            console.log('PWA is already installed');
        }
    }

    setupOfflineDetection() {
        // Online/offline event listeners
        window.addEventListener('online', () => {
            this.handleOnline();
        });

        window.addEventListener('offline', () => {
            this.handleOffline();
        });

        // Initial status
        if (!navigator.onLine) {
            this.handleOffline();
        }
    }

    createInstallBanner() {
        // Check if we're on the homepage
        if (!this.isHomePage()) {
            return;
        }

        // Check if banner already exists in HTML
        const existingBanner = document.getElementById('pwa-install-banner');
        if (existingBanner) {
            // Use existing banner from HTML
            this.setupBannerEventListeners();
            return;
        }

        // Fallback: Create banner dynamically if not in HTML
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'fixed bottom-4 left-4 right-4 md:left-auto md:w-96 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 rounded-lg shadow-lg z-50 transform translate-y-full transition-transform duration-300';
        banner.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <h4 class="font-semibold mb-1">Installer Sertifikatet</h4>
                    <p class="text-sm opacity-90">Få raskere tilgang og offline støtte</p>
                </div>
                <div class="flex space-x-2 ml-4">
                    <button id="pwa-install-btn" class="bg-white text-purple-600 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gray-100 transition">
                        Installer
                    </button>
                    <button id="pwa-dismiss-btn" class="text-white/80 hover:text-white px-2" aria-label="Lukk">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        this.setupBannerEventListeners();
    }

    isHomePage() {
        // Check if current page is homepage
        return window.location.pathname === '/' || window.location.pathname === '/index' || window.location.pathname.endsWith('/index.html');
    }

    setupBannerEventListeners() {
        const installBtn = document.getElementById('pwa-install-btn');
        const dismissBtn = document.getElementById('pwa-dismiss-btn');
        
        if (installBtn) {
            installBtn.addEventListener('click', () => {
                this.installPWA();
            });
        }
        
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => {
                this.dismissInstallBanner();
            });
        }
    }

    showInstallBanner() {
        // Only show on homepage
        if (!this.isHomePage()) {
            return;
        }

        const banner = document.getElementById('pwa-install-banner');
        if (banner && this.isInstallable && !this.isInstalled) {
            // Check if user previously dismissed
            const dismissed = localStorage.getItem('pwa-install-dismissed');
            const lastDismissed = localStorage.getItem('pwa-install-dismissed-time');
            
            // Show again after 7 days
            if (!dismissed || (Date.now() - parseInt(lastDismissed) > 7 * 24 * 60 * 60 * 1000)) {
                // Remove inline style display:none and show banner
                banner.style.display = 'block';
                
                // Add smooth animation
                setTimeout(() => {
                    banner.style.opacity = '0';
                    banner.style.transform = 'translateY(-20px)';
                    banner.style.transition = 'all 0.5s ease-out';
                    
                    setTimeout(() => {
                        banner.style.opacity = '1';
                        banner.style.transform = 'translateY(0)';
                    }, 100);
                }, 2000); // Show after 2 seconds
            }
        }
    }

    hideInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                banner.style.display = 'none';
            }, 300);
        }
    }

    dismissInstallBanner() {
        this.hideInstallBanner();
        localStorage.setItem('pwa-install-dismissed', 'true');
        localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
        
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'pwa_install_dismissed', {
                'event_category': 'PWA',
                'event_label': 'Install Banner Dismissed'
            });
        }
    }

    async installPWA() {
        if (this.deferredPrompt) {
            try {
                this.deferredPrompt.prompt();
                const { outcome } = await this.deferredPrompt.userChoice;
                
                if (outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'pwa_install_accepted', {
                            'event_category': 'PWA',
                            'event_label': 'Install Accepted'
                        });
                    }
                } else {
                    console.log('User dismissed the install prompt');
                    
                    // Analytics tracking
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'pwa_install_declined', {
                            'event_category': 'PWA',
                            'event_label': 'Install Declined'
                        });
                    }
                }
                
                this.deferredPrompt = null;
                this.hideInstallBanner();
                
            } catch (error) {
                console.error('Error during PWA installation:', error);
            }
        }
    }

    showInstalledMessage() {
        this.showNotification({
            title: 'App installert!',
            message: 'Sertifikatet er nå tilgjengelig på hjemmeskjermen din.',
            type: 'success',
            duration: 5000
        });
    }

    showUpdateAvailable() {
        const notification = this.showNotification({
            title: 'Oppdatering tilgjengelig',
            message: 'En ny versjon av appen er klar.',
            type: 'info',
            persistent: true,
            actions: [
                {
                    text: 'Oppdater',
                    action: () => {
                        if (navigator.serviceWorker.controller) {
                            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
                            window.location.reload();
                        }
                    }
                },
                {
                    text: 'Senere',
                    action: () => notification.remove()
                }
            ]
        });
    }

    handleOnline() {
        console.log('App is back online');
        this.showNotification({
            title: 'Tilbake online!',
            message: 'Internettforbindelsen er gjenopprettet.',
            type: 'success',
            duration: 3000
        });
        
        // Hide offline indicator
        const offlineIndicator = document.getElementById('offline-indicator');
        if (offlineIndicator) {
            offlineIndicator.remove();
        }
    }

    handleOffline() {
        console.log('App is offline');
        this.showOfflineIndicator();
        
        this.showNotification({
            title: 'Du er offline',
            message: 'Du kan fortsatt bruke appen. Data synkroniseres når du kommer online.',
            type: 'warning',
            duration: 5000
        });
    }

    showOfflineIndicator() {
        if (document.getElementById('offline-indicator')) {
            return; // Already showing
        }
        
        const indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.className = 'fixed top-0 left-0 right-0 bg-yellow-600 text-white py-2 px-4 text-center text-sm z-50';
        indicator.innerHTML = `
            <i class="fas fa-wifi-slash mr-2"></i>
            Du er offline - Data lagres lokalt og synkroniseres senere
        `;
        
        document.body.appendChild(indicator);
    }

    setupMobileOptimizations() {
        // Add mobile-specific meta tags if not present
        if (!document.querySelector('meta[name="theme-color"]')) {
            const themeColor = document.createElement('meta');
            themeColor.name = 'theme-color';
            themeColor.content = '#7c3aed';
            document.head.appendChild(themeColor);
        }

        // Add touch icons if not present
        if (!document.querySelector('link[rel="apple-touch-icon"]')) {
            const touchIcon = document.createElement('link');
            touchIcon.rel = 'apple-touch-icon';
            touchIcon.href = '/static/images/icons/icon-192x192.png';
            document.head.appendChild(touchIcon);
        }

        // Setup pull-to-refresh (basic implementation)
        this.setupPullToRefresh();
        
        // Setup haptic feedback for mobile
        this.setupHapticFeedback();
        
        // Setup mobile keyboard optimizations
        this.setupMobileKeyboard();
    }

    setupPullToRefresh() {
        let startY = 0;
        let isPulling = false;
        const threshold = 100;
        
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (window.scrollY === 0 && startY > 0) {
                const currentY = e.touches[0].clientY;
                const pullDistance = currentY - startY;
                
                if (pullDistance > 10) {
                    isPulling = true;
                    
                    if (pullDistance > threshold) {
                        this.showPullToRefreshIndicator(true);
                    } else {
                        this.showPullToRefreshIndicator(false);
                    }
                }
            }
        }, { passive: true });
        
        document.addEventListener('touchend', () => {
            if (isPulling) {
                const indicator = document.getElementById('pull-refresh-indicator');
                if (indicator && indicator.classList.contains('active')) {
                    this.triggerRefresh();
                }
                this.hidePullToRefreshIndicator();
                isPulling = false;
                startY = 0;
            }
        }, { passive: true });
    }

    showPullToRefreshIndicator(active) {
        let indicator = document.getElementById('pull-refresh-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'pull-refresh-indicator';
            indicator.className = 'fixed top-0 left-1/2 transform -translate-x-1/2 -translate-y-full bg-purple-600 text-white px-4 py-2 rounded-b-lg transition-transform duration-300 z-50';
            indicator.innerHTML = '<i class="fas fa-arrow-down mr-2"></i>Dra for å oppdatere';
            document.body.appendChild(indicator);
        }
        
        if (active) {
            indicator.classList.add('active');
            indicator.innerHTML = '<i class="fas fa-sync-alt mr-2"></i>Slipp for å oppdatere';
            indicator.style.transform = 'translateX(-50%) translateY(0)';
        } else {
            indicator.classList.remove('active');
            indicator.innerHTML = '<i class="fas fa-arrow-down mr-2"></i>Dra for å oppdatere';
            indicator.style.transform = 'translateX(-50%) translateY(-50%)';
        }
    }

    hidePullToRefreshIndicator() {
        const indicator = document.getElementById('pull-refresh-indicator');
        if (indicator) {
            indicator.style.transform = 'translateX(-50%) translateY(-100%)';
            setTimeout(() => {
                indicator.remove();
            }, 300);
        }
    }

    triggerRefresh() {
        // Show loading and refresh the page
        window.location.reload();
    }

    setupHapticFeedback() {
        // Add haptic feedback for button clicks on mobile
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button, .btn, .answer-option');
            if (target && 'vibrate' in navigator) {
                navigator.vibrate(10); // Very short vibration
            }
        });
    }

    setupMobileKeyboard() {
        // Prevent zoom on input focus on iOS
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
                    input.style.fontSize = '16px';
                }
            });
            
            input.addEventListener('blur', () => {
                input.style.fontSize = '';
            });
        });
    }

    initializeNotifications() {
        // Request notification permission for PWA
        if ('Notification' in window && 'serviceWorker' in navigator) {
            if (Notification.permission === 'default') {
                // Don't ask immediately, wait for user interaction
                setTimeout(() => {
                    if (this.isInstalled) {
                        this.requestNotificationPermission();
                    }
                }, 5000);
            }
        }
    }

    async requestNotificationPermission() {
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                this.showNotification({
                    title: 'Notifikasjoner aktivert!',
                    message: 'Du vil få varsler om nye utmerkelser og fremgang.',
                    type: 'success'
                });
            }
        }
    }

    showNotification({ title, message, type = 'info', duration = 4000, persistent = false, actions = [] }) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 max-w-sm bg-white dark:bg-gray-800 border-l-4 ${
            type === 'success' ? 'border-green-500' : 
            type === 'error' ? 'border-red-500' : 
            type === 'warning' ? 'border-yellow-500' : 'border-blue-500'
        } p-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas fa-${
                        type === 'success' ? 'check-circle text-green-500' : 
                        type === 'error' ? 'exclamation-circle text-red-500' : 
                        type === 'warning' ? 'exclamation-triangle text-yellow-500' : 'info-circle text-blue-500'
                    }"></i>
                </div>
                <div class="ml-3 flex-1">
                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white">${title}</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">${message}</p>
                    ${actions.length > 0 ? `
                        <div class="mt-3 flex space-x-2">
                            ${actions.map(action => `
                                <button class="notification-action text-xs px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition"
                                        data-action="${action.text}">
                                    ${action.text}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="ml-4">
                    <button class="notification-close text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Add event listeners
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        // Handle action buttons
        actions.forEach((action, index) => {
            const button = notification.querySelector(`[data-action="${action.text}"]`);
            if (button) {
                button.addEventListener('click', () => {
                    action.action();
                    if (!persistent) {
                        this.hideNotification(notification);
                    }
                });
            }
        });
        
        // Auto-hide after duration (unless persistent)
        if (!persistent && duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    this.hideNotification(notification);
                }
            }, duration);
        }
        
        return notification;
    }

    hideNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }

    handleServiceWorkerMessage(data) {
        const { type } = data;
        
        switch (type) {
            case 'SYNC_SUCCESS':
                this.showNotification({
                    title: 'Synkronisert!',
                    message: 'Offline data har blitt synkronisert.',
                    type: 'success',
                    duration: 2000
                });
                break;
            case 'CACHE_UPDATED':
                this.showNotification({
                    title: 'Innhold oppdatert',
                    message: 'Nytt innhold er tilgjengelig offline.',
                    type: 'info',
                    duration: 3000
                });
                break;
        }
    }
}

// Initialize PWA installer when DOM is ready
let pwaInstaller;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        pwaInstaller = new PWAInstaller();
    });
} else {
    pwaInstaller = new PWAInstaller();
}

// Export for global access
window.pwaInstaller = pwaInstaller;
