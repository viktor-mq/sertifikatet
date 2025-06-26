/* static/js/cookie-consent.js */

class CookieConsentManager {
    constructor() {
        this.STORAGE_KEY = 'sertifikatet_cookie_banner_shown';
        this.GOOGLE_ANALYTICS_ID = 'G-353HJJCNYR';
        this.currentPreferences = {
            necessary: true,
            analytics: true,  // Default for first-time users only
            marketing: true   // Default for first-time users only
        };
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        try {
            // Check if banner was already shown in this browser
            const bannerShown = localStorage.getItem(this.STORAGE_KEY);
            
            // Get existing preferences from server
            const existingPreferences = await this.getExistingPreferences();
            
            if (existingPreferences && existingPreferences.preferences) {
                // User has made a choice - apply preferences
                this.currentPreferences = existingPreferences.preferences;
                this.applyPreferences();
                
                // Update view-only displays if on notification settings page
                this.updateViewOnlyDisplays();
                
                // Mark banner as shown
                localStorage.setItem(this.STORAGE_KEY, 'true');
            } else if (!bannerShown) {
                // First time visitor - show consent modal
                this.showConsentModal();
            } else {
                // Banner was shown before but no server preferences found
                // This shouldn't happen in normal flow, but handle gracefully
                this.updateViewOnlyDisplays();
            }
            
        } catch (error) {
            console.error('Cookie consent initialization error:', error);
        }
    }
    
    async getExistingPreferences() {
        try {
            const response = await fetch('/api/cookie-consent');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching preferences:', error);
        }
        return null;
    }
    
    showConsentModal() {
        // Create modal HTML
        const modalHTML = `
            <div class="cookie-consent-overlay" id="cookieConsentOverlay">
                <div class="cookie-consent-modal">
                    <div class="cookie-consent-header">
                        <div class="cookie-consent-icon">🍪</div>
                        <h2 class="cookie-consent-title">Vi respekterer ditt personvern</h2>
                    </div>
                    
                    <p class="cookie-consent-description">
                        Vi bruker cookies for å forbedre din opplevelse på Sertifikatet. Begge alternativene 
                        er forvalgte for å gi deg den beste opplevelsen, men du kan enkelt endre valgene dine 
                        før du lagrer. Dine valg påvirker ikke tilgangen til tjenesten.
                    </p>
                    
                    <div class="cookie-categories">
                        <div class="cookie-category">
                            <div class="cookie-category-header">
                                <div class="cookie-category-name">
                                    <span class="cookie-category-icon">🔒</span>
                                    Nødvendige cookies
                                </div>
                                <button class="cookie-toggle active disabled" disabled>
                                    <div class="cookie-toggle-slider"></div>
                                </button>
                            </div>
                            <div class="cookie-category-description">
                                Kreves for pålogging, sikkerhet og grunnleggende funksjonalitet. 
                                Kan ikke deaktiveres.
                            </div>
                        </div>
                        
                        <div class="cookie-category">
                            <div class="cookie-category-header">
                                <div class="cookie-category-name">
                                    <span class="cookie-category-icon">📊</span>
                                    Analyse cookies
                                </div>
                                <button class="cookie-toggle active" id="analyticsToggle" onclick="window.cookieConsent.toggleCategory('analytics')">
                                    <div class="cookie-toggle-slider"></div>
                                </button>
                            </div>
                            <div class="cookie-category-description">
                                Hjelper oss forstå hvordan du bruker tjenesten for å forbedre opplevelsen. 
                                Inkluderer Google Analytics.
                            </div>
                        </div>
                        
                        <div class="cookie-category">
                            <div class="cookie-category-header">
                                <div class="cookie-category-name">
                                    <span class="cookie-category-icon">🎯</span>
                                    Markedsføring cookies
                                </div>
                                <button class="cookie-toggle active" id="marketingToggle" onclick="window.cookieConsent.toggleCategory('marketing')">
                                    <div class="cookie-toggle-slider"></div>
                                </button>
                            </div>
                            <div class="cookie-category-description">
                                Brukes for personalisert reklame og målrettet markedsføring. 
                                Kun for gratis brukere.
                            </div>
                        </div>
                    </div>
                    
                    <div class="cookie-consent-buttons">
                        <button class="cookie-consent-btn cookie-consent-btn-secondary" onclick="window.cookieConsent.rejectAll()">
                            Kun nødvendige
                        </button>
                        <button class="cookie-consent-btn cookie-consent-btn-primary" onclick="window.cookieConsent.savePreferences()">
                            Lagre valg
                        </button>
                        <button class="cookie-consent-btn cookie-consent-btn-accept-all" onclick="window.cookieConsent.acceptAll()">
                            Godta alle
                        </button>
                    </div>
                    
                    <div class="cookie-consent-links">
                        <a href="/legal/privacy" target="_blank">Personvernerklæring</a>
                        <a href="/legal/terms" target="_blank">Vilkår</a>
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal with animation
        setTimeout(() => {
            document.getElementById('cookieConsentOverlay').classList.add('show');
        }, 100);
    }
    
    toggleCategory(category) {
        if (category === 'necessary') return; // Can't toggle necessary
        
        this.currentPreferences[category] = !this.currentPreferences[category];
        
        const toggle = document.getElementById(category + 'Toggle');
        if (toggle) {
            toggle.classList.toggle('active', this.currentPreferences[category]);
        }
    }
    
    async rejectAll() {
        this.currentPreferences = {
            necessary: true,
            analytics: false,
            marketing: false
        };
        
        // Update UI to show unchecked state
        document.getElementById('analyticsToggle')?.classList.remove('active');
        document.getElementById('marketingToggle')?.classList.remove('active');
        
        await this.saveAndClose();
    }
    
    async acceptAll() {
        this.currentPreferences = {
            necessary: true,
            analytics: true,
            marketing: true
        };
        await this.saveAndClose();
    }
    
    async savePreferences() {
        await this.saveAndClose();
    }
    
    async saveAndClose() {
        try {
            // Show loading state
            const buttons = document.querySelectorAll('.cookie-consent-btn');
            buttons.forEach(btn => {
                btn.classList.add('loading');
                btn.disabled = true;
            });
            
            // Save to server
            const response = await fetch('/api/cookie-consent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentPreferences)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save preferences');
            }
            
            // Mark banner as shown
            localStorage.setItem(this.STORAGE_KEY, 'true');
            
            // Apply preferences
            this.applyPreferences();
            
            // Update any view-only displays on the page
            this.updateViewOnlyDisplays();
            
            // Close modal
            this.closeModal();
            
        } catch (error) {
            console.error('Error saving cookie preferences:', error);
            alert('Feil ved lagring av cookie-innstillinger. Prøv igjen.');
            
            // Remove loading state
            const buttons = document.querySelectorAll('.cookie-consent-btn');
            buttons.forEach(btn => {
                btn.classList.remove('loading');
                btn.disabled = false;
            });
        }
    }
    
    closeModal() {
        const overlay = document.getElementById('cookieConsentOverlay');
        if (overlay) {
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }
    
    applyPreferences() {
        // Apply Google Analytics
        if (this.currentPreferences.analytics) {
            this.loadGoogleAnalytics();
        }
        
        // Apply marketing scripts
        if (this.currentPreferences.marketing) {
            this.loadMarketingScripts();
        }
        
        // Trigger custom event for other scripts
        window.dispatchEvent(new CustomEvent('cookiePreferencesApplied', {
            detail: this.currentPreferences
        }));
    }
    
    loadGoogleAnalytics() {
        // Only load if not already loaded and user has consented
        if (window.gtag || document.querySelector(`script[src*="googletagmanager.com/gtag/js?id=${this.GOOGLE_ANALYTICS_ID}"]`)) {
            console.log('Google Analytics already loaded');
            return;
        }
        
        console.log('Loading Google Analytics with user consent');
        
        // Load Google Analytics script
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.GOOGLE_ANALYTICS_ID}`;
        document.head.appendChild(script);
        
        // Initialize gtag with enhanced privacy settings
        script.onload = () => {
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            window.gtag = gtag;
            
            gtag('js', new Date());
            
            // Enhanced privacy configuration for GDPR compliance
            gtag('config', this.GOOGLE_ANALYTICS_ID, {
                // Privacy settings
                anonymize_ip: true,                    // Anonymize IP addresses
                allow_google_signals: false,          // Disable advertising features
                allow_ad_personalization_signals: false, // No ad personalization
                
                // Cookie settings
                cookie_flags: 'SameSite=None;Secure',  // Secure cookie handling
                cookie_expires: 60 * 60 * 24 * 365,   // 1 year expiration
                
                // Data collection settings
                send_page_view: true,                  // Enable page view tracking
                linker: {                              // Cross-domain tracking disabled
                    accept_incoming: false
                },
                
                // Custom parameters
                custom_map: {
                    'custom_parameter_1': 'user_subscription_tier',
                    'custom_parameter_2': 'user_level'
                }
            });
            
            // Set user properties for segmentation
            this.setUserProperties();
            
            console.log('Google Analytics loaded successfully with GDPR compliance');
        };
    }
    
    loadMarketingScripts() {
        // Placeholder for marketing scripts (Facebook Pixel, etc.)
        // Only load if user is on free plan and has consented
        console.log('Marketing scripts would be loaded here');
    }
    
    setUserProperties() {
        // Set user properties for analytics segmentation
        if (window.gtag) {
            try {
                // Get user info from the page if available
                const userInfo = this.getUserInfo();
                
                gtag('config', this.GOOGLE_ANALYTICS_ID, {
                    user_properties: {
                        subscription_tier: userInfo.subscriptionTier || 'free',
                        user_level: userInfo.userLevel || 1,
                        is_verified: userInfo.isVerified || false,
                        registration_date: userInfo.registrationDate || null
                    }
                });
                
                console.log('User properties set for analytics', userInfo);
            } catch (error) {
                console.warn('Could not set user properties:', error);
            }
        }
    }
    
    getUserInfo() {
        // Extract user information from page meta tags or global variables
        const userInfo = {};
        
        // Try to get from meta tags first
        const subscriptionMeta = document.querySelector('meta[name="user-subscription-tier"]');
        if (subscriptionMeta) {
            userInfo.subscriptionTier = subscriptionMeta.content;
        }
        
        const levelMeta = document.querySelector('meta[name="user-level"]');
        if (levelMeta) {
            userInfo.userLevel = parseInt(levelMeta.content) || 1;
        }
        
        const verifiedMeta = document.querySelector('meta[name="user-verified"]');
        if (verifiedMeta) {
            userInfo.isVerified = verifiedMeta.content === 'true';
        }
        
        const regDateMeta = document.querySelector('meta[name="user-registration-date"]');
        if (regDateMeta) {
            userInfo.registrationDate = regDateMeta.content;
        }
        
        // Fallback to global window variables if available
        if (window.currentUser) {
            userInfo.subscriptionTier = window.currentUser.subscriptionTier || userInfo.subscriptionTier;
            userInfo.userLevel = window.currentUser.level || userInfo.userLevel;
            userInfo.isVerified = window.currentUser.isVerified !== undefined ? window.currentUser.isVerified : userInfo.isVerified;
        }
        
        return userInfo;
    }
    
    // Update view-only displays on notification settings page
    updateViewOnlyDisplays() {
        const categories = ['analytics', 'marketing'];
        
        categories.forEach(category => {
            const display = document.querySelector(`.cookie-preferences-display[data-category="${category}"]`);
            if (display) {
                const toggleElement = display.querySelector('div');
                const slider = display.querySelector('div > div');
                
                if (this.currentPreferences[category]) {
                    toggleElement.classList.remove('bg-gray-700');
                    toggleElement.classList.add('bg-purple-600');
                    slider.classList.remove('left-[2px]');
                    slider.classList.add('right-[2px]');
                } else {
                    toggleElement.classList.remove('bg-purple-600');
                    toggleElement.classList.add('bg-gray-700');
                    slider.classList.remove('right-[2px]');
                    slider.classList.add('left-[2px]');
                }
            }
        });
        
        // Trigger update event for notification settings page
        if (typeof updateCookieToggles === 'function') {
            updateCookieToggles(this.currentPreferences);
        }
    }
    
    // Public method to show settings (called from "Manage Cookies" link)
    async showSettings() {
        // Load current preferences from server first
        const existingPreferences = await this.getExistingPreferences();
        if (existingPreferences && existingPreferences.preferences) {
            this.currentPreferences = existingPreferences.preferences;
        }
        
        // Remove existing modal if any
        const existing = document.getElementById('cookieConsentOverlay');
        if (existing) {
            existing.remove();
        }
        
        // Show modal
        this.showConsentModal();
        
        // Set current preferences in UI
        setTimeout(() => {
            const analyticsToggle = document.getElementById('analyticsToggle');
            const marketingToggle = document.getElementById('marketingToggle');
            
            if (analyticsToggle) {
                analyticsToggle.classList.toggle('active', this.currentPreferences.analytics);
            }
            if (marketingToggle) {
                marketingToggle.classList.toggle('active', this.currentPreferences.marketing);
            }
        }, 150);
    }
}

// Initialize cookie consent manager
window.cookieConsent = new CookieConsentManager();

// Global function for "Manage Cookies" button
function manageCookies() {
    window.cookieConsent.showSettings();
}
