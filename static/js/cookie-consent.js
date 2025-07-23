/* Enhanced Cookie Consent for Analytics + Ads */
/* Extends your existing cookie-consent.js */

// CSRF token utility
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

class EnhancedCookieConsentManager {
    constructor() {
        this.STORAGE_KEY = 'sertifikatet_cookie_banner_shown';
        this.GOOGLE_ANALYTICS_ID = 'G-353HJJCNYR'; // Your existing GA4 ID
        this.GTM_ID = 'GTM-XXXXXXX'; // Add your GTM ID here when ready
        this.useGTM = false; // Set to true when you implement GTM
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
                // First time visitor - set defaults based on user tier
                this.setDefaultPreferences();
                // Show consent modal
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
    
    setDefaultPreferences() {
        // Set smart defaults based on user tier
        const userTier = this.getUserTier();
        const isPremiumUser = userTier === 'premium' || userTier === 'pro';
        
        if (isPremiumUser) {
            // Premium users: Analytics ON, Marketing OFF (they don't see ads anyway)
            this.currentPreferences = {
                necessary: true,
                analytics: true,
                marketing: false  // Default OFF for premium users
            };
        } else {
            // Free users: Both ON (they benefit from personalized ads)
            this.currentPreferences = {
                necessary: true,
                analytics: true,
                marketing: true
            };
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
    
    applyPreferences() {
        // Apply Analytics (GA4 or GTM)
        if (this.currentPreferences.analytics) {
            if (this.useGTM) {
                this.loadGTMWithConsent();
            } else {
                this.loadGoogleAnalytics(); // Your existing method
            }
        }
        
        // Apply Marketing/Ads - Load ads for all free users (personalized or not based on consent)
        const userTier = this.getUserTier();
        if (userTier === 'free' && window.adsenseEnabled) {
            // Free users always see ads, but personalization depends on marketing consent
            this.loadAdSystems();
        } else if (this.currentPreferences.marketing && window.adsenseEnabled) {
            // Premium users would only see ads if they somehow had marketing consent (shouldn't happen)
            this.loadAdSystems();
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
                anonymize_ip: true,
                allow_google_signals: false,
                allow_ad_personalization_signals: false,
                
                // Cookie settings
                cookie_flags: 'SameSite=None;Secure',
                cookie_expires: 60 * 60 * 24 * 365,
                
                // Data collection settings
                send_page_view: true,
                linker: {
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
    
    loadAdSystems() {
        console.log('Loading ad systems with user consent');
        
        // Only proceed if user is not premium and AdSense is enabled
        if (!window.adsenseEnabled) {
            console.log('Ad systems disabled: Premium/Pro subscription');
            return;
        }
        
        // For free users, always load ads (personalized or non-personalized based on consent)
        this.loadGoogleAdSense();
        
        // Load other ad networks if needed
        this.loadNorwegianAdNetworks();
        
        // Initialize ad management system
        if (window.adManager) {
            window.adManager.enableAds();
        }
    }
    
    loadGoogleAdSense() {
        // Check if AdSense is enabled for this user
        if (!window.adsenseEnabled) {
            console.log('AdSense disabled for this user (Premium/Pro subscription)');
            return;
        }
        
        // Check if already loaded
        const existingScript = document.getElementById('adsense-script');
        if (!existingScript) {
            console.log('AdSense script not found in DOM');
            return;
        }
        
        if (existingScript.style.display !== 'none') {
            console.log('AdSense already activated');
            return;
        }
        
        console.log('Activating Google AdSense with GDPR compliance');
        
        // Activate the existing script
        existingScript.style.display = 'block';
        
        // Initialize AdSense
        window.adsbygoogle = window.adsbygoogle || [];
        
        // Configure AdSense for GDPR compliance
        try {
            const userTier = this.getUserTier();
            const hasMarketingConsent = this.currentPreferences.marketing;
            
            window.adsbygoogle.push({
                params: {
                    google_ad_client: window.adsensePublisherId,
                    enable_page_level_ads: true,
                    overlays: {bottom: true},
                    // GDPR settings - key change here
                    tag_for_child_directed_treatment: -1,
                    tag_for_under_age_of_consent: -1,
                    // Restrict data processing if user declined marketing cookies
                    restricted_data_processing: !hasMarketingConsent
                }
            });
            
            // Log the ad configuration for debugging
            if (hasMarketingConsent) {
                console.log('✅ Google AdSense activated: Personalized ads enabled');
            } else {
                console.log('✅ Google AdSense activated: Non-personalized ads only (GDPR compliance)');
            }
            
            // Track ad loading type for analytics
            if (window.gtag) {
                gtag('event', 'ads_loaded', {
                    'user_tier': userTier,
                    'personalized': hasMarketingConsent,
                    'ad_type': hasMarketingConsent ? 'personalized' : 'non_personalized'
                });
            }
            
        } catch (error) {
            console.error('Error initializing AdSense:', error);
        }
    }
    
    loadNorwegianAdNetworks() {
        // Placeholder for Norwegian ad networks
        console.log('Norwegian ad networks integration ready');
    }
    
    showConsentModal() {
        // Get user's subscription tier
        const userTier = this.getUserTier();
        const isPremiumUser = userTier === 'premium' || userTier === 'pro';
        
        // Dynamic description based on user tier
        const description = isPremiumUser 
            ? 'Du kan velge hvilke cookies vi bruker for å forbedre din opplevelse på Sertifikatet.'
            : 'Sertifikatet er gratis å bruke takket være annonser. Du kan velge hvilke cookies vi bruker, eller oppgradere til Premium for en reklamefri opplevelse.';
        
        // Dynamic marketing cookie description
        const marketingDescription = isPremiumUser
            ? 'Brukes for personalisert markedsføring via e-post og partnertilbud. Som Premium-bruker ser du ingen annonser på nettsiden. Du kan velge å motta markedsførings-e-post.'
            : 'Gjør at vi kan vise <strong>personaliserte annonser</strong> som finansierer gratis tilgang. Hvis du velger "Nei", vil du fortsatt se annonser, men de vil ikke være tilpasset dine interesser. <strong>Oppgrader til Premium for å fjerne alle annonser!</strong>';
        
        // Premium upgrade notice (only show for free users)
        const upgradeNoticeHTML = isPremiumUser ? '' : `
            <div class="cookie-consent-upgrade-notice">
                <div class="upgrade-highlight">
                    💎 <strong>Premium-brukere:</strong> Ingen annonser, ingen tracking cookies!
                    <a href="/payment/subscription" class="upgrade-link">Oppgrader nå →</a>
                </div>
            </div>
        `;
        
        // Premium user success notice (only show for premium users)
        const premiumNoticeHTML = isPremiumUser ? `
            <div class="cookie-consent-premium-notice">
                <div class="premium-highlight">
                    ✨ <strong>Takk for at du støtter Sertifikatet!</strong> Du har en reklamefri opplevelse.
                </div>
            </div>
        ` : '';
        
        // Create modal HTML with dynamic content
        const modalHTML = `
            <div class="cookie-consent-overlay" id="cookieConsentOverlay">
                <div class="cookie-consent-modal">
                    <div class="cookie-consent-header">
                        <div class="cookie-consent-icon">🍪</div>
                        <h2 class="cookie-consent-title">Vi respekterer ditt personvern</h2>
                    </div>
                    
                    <p class="cookie-consent-description">
                        ${description}
                    </p>
                    
                    ${premiumNoticeHTML}
                    
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
                                Inkluderer Google Analytics for statistikk.
                            </div>
                        </div>
                        
                        <div class="cookie-category">
                            <div class="cookie-category-header">
                                <div class="cookie-category-name">
                                    <span class="cookie-category-icon">🎯</span>
                                    Personaliserte annonser
                                </div>
                                <button class="cookie-toggle active" id="marketingToggle" onclick="window.cookieConsent.toggleCategory('marketing')">
                                    <div class="cookie-toggle-slider"></div>
                                </button>
                            </div>
                            <div class="cookie-category-description">
                                ${marketingDescription}
                            </div>
                            ${isPremiumUser ? '' : '<div class="cookie-category-note"><small><strong>Merk:</strong> Som gratis bruker vil du se annonser uansett. Denne innstillingen kontrollerer kun om annonsene er personaliserte.</small></div>'}
                        </div>
                    </div>
                    
                    ${upgradeNoticeHTML}
                    
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
                        ${isPremiumUser ? '' : '<a href="/payment/subscription" target="_blank">Premium (reklamefritt)</a>'}
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Set correct toggle states immediately based on current preferences
        setTimeout(() => {
            const analyticsToggle = document.getElementById('analyticsToggle');
            const marketingToggle = document.getElementById('marketingToggle');
            
            if (analyticsToggle) {
                analyticsToggle.classList.toggle('active', this.currentPreferences.analytics);
            }
            if (marketingToggle) {
                marketingToggle.classList.toggle('active', this.currentPreferences.marketing);
            }
        }, 50);
        
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
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(this.currentPreferences)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save preferences');
            }
            
            // Mark banner as shown
            localStorage.setItem(this.STORAGE_KEY, 'true');
            
            // Apply preferences and update existing consent
            this.applyPreferences();
            this.updateConsentMode();
            this.updateViewOnlyDisplays();
            
            // Track consent choice
            this.trackConsentChoice();
            
            this.closeModal();
            
        } catch (error) {
            console.error('Error saving cookie preferences:', error);
            alert('Feil ved lagring av cookie-innstillinger. Prøv igjen.');
            
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
    
    updateConsentMode() {
        // Update consent mode for existing GTM/GA4
        if (window.dataLayer) {
            window.dataLayer.push({
                'event': 'consent_update',
                'analytics_storage': this.currentPreferences.analytics ? 'granted' : 'denied',
                'ad_storage': this.currentPreferences.marketing ? 'granted' : 'denied',
                'ad_user_data': this.currentPreferences.marketing ? 'granted' : 'denied',
                'ad_personalization': this.currentPreferences.marketing ? 'granted' : 'denied'
            });
        }
        
        // Update GA4 consent if using direct implementation
        if (window.gtag && !this.useGTM) {
            window.gtag('consent', 'update', {
                'analytics_storage': this.currentPreferences.analytics ? 'granted' : 'denied',
                'ad_storage': this.currentPreferences.marketing ? 'granted' : 'denied',
                'ad_user_data': this.currentPreferences.marketing ? 'granted' : 'denied',
                'ad_personalization': this.currentPreferences.marketing ? 'granted' : 'denied'
            });
        }
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
    
    trackConsentChoice() {
        // Track how users respond to cookie consent
        if (window.dataLayer || window.gtag) {
            const consentData = {
                'event': 'cookie_consent_choice',
                'analytics_consent': this.currentPreferences.analytics,
                'marketing_consent': this.currentPreferences.marketing,
                'user_tier': this.getUserTier()
            };
            
            if (window.dataLayer) {
                window.dataLayer.push(consentData);
            } else if (window.gtag) {
                window.gtag('event', 'cookie_consent_choice', consentData);
            }
        }
    }
    
    getUserTier() {
        const tierMeta = document.querySelector('meta[name="user-subscription-tier"]');
        return tierMeta ? tierMeta.content : 'free';
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

// CSS for the enhanced modal
const enhancedModalCSS = `
.cookie-consent-upgrade-notice {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
    text-align: center;
}

.cookie-consent-premium-notice {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 20px 0;
    text-align: center;
}

.upgrade-highlight {
    color: white;
    font-size: 14px;
    line-height: 1.5;
}

.premium-highlight {
    color: white;
    font-size: 14px;
    line-height: 1.5;
}

.upgrade-link {
    color: #ffd700;
    text-decoration: none;
    font-weight: bold;
    margin-left: 8px;
}

.upgrade-link:hover {
    color: #ffed4a;
    text-decoration: underline;
}

.cookie-consent-btn.loading {
    opacity: 0.7;
    cursor: not-allowed;
}

.cookie-consent-btn.loading::after {
    content: '';
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #ffffff;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 1s ease-in-out infinite;
    margin-left: 8px;
}

.cookie-category-note {
    margin-top: 8px;
    padding: 8px 12px;
    background: rgba(59, 130, 246, 0.1);
    border-left: 3px solid #3b82f6;
    border-radius: 4px;
    color: #e5e7eb;
}

.cookie-category-note small {
    font-size: 12px;
    line-height: 1.4;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
`;

// Inject CSS into page
if (!document.querySelector('#enhanced-cookie-consent-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'enhanced-cookie-consent-styles';
    styleElement.textContent = enhancedModalCSS;
    document.head.appendChild(styleElement);
}

// Initialize enhanced cookie consent manager
window.cookieConsent = new EnhancedCookieConsentManager();

// Global function for "Manage Cookies" button
function manageCookies() {
    window.cookieConsent.showSettings();
}
