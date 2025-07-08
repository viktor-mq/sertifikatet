"""
SEO Analytics Integration
Track SEO performance and search-related metrics
"""

from flask import request
import json

class SEOAnalytics:
    """Track SEO-related events and metrics"""
    
    @staticmethod
    def track_search_query(query, results_count=0, source='internal'):
        """Track search queries for SEO insights"""
        if not query:
            return
        
        search_data = {
            'event': 'site_search',
            'search_term': query.lower(),
            'search_results': results_count,
            'search_source': source,  # 'internal', 'google', 'direct'
            'page_url': request.url,
            'user_intent': SEOAnalytics._classify_search_intent(query)
        }
        
        # Send to GTM dataLayer
        return f"""
        <script>
            if (window.dataLayer) {{
                window.dataLayer.push({json.dumps(search_data)});
            }}
        </script>
        """
    
    @staticmethod
    def track_page_performance(page_type, load_time=None):
        """Track page performance metrics"""
        performance_data = {
            'event': 'page_performance',
            'page_type': page_type,
            'load_time': load_time,
            'page_url': request.url
        }
        
        return f"""
        <script>
            if (window.dataLayer) {{
                window.dataLayer.push({json.dumps(performance_data)});
            }}
            
            // Track Core Web Vitals
            if ('web-vitals' in window) {{
                window.webVitals.getCLS(function(metric) {{
                    window.dataLayer.push({{
                        'event': 'core_web_vital',
                        'metric_name': 'CLS',
                        'metric_value': metric.value,
                        'page_type': '{page_type}'
                    }});
                }});
                
                window.webVitals.getFID(function(metric) {{
                    window.dataLayer.push({{
                        'event': 'core_web_vital',
                        'metric_name': 'FID',
                        'metric_value': metric.value,
                        'page_type': '{page_type}'
                    }});
                }});
                
                window.webVitals.getLCP(function(metric) {{
                    window.dataLayer.push({{
                        'event': 'core_web_vital',
                        'metric_name': 'LCP',
                        'metric_value': metric.value,
                        'page_type': '{page_type}'
                    }});
                }});
            }}
        </script>
        """
    
    @staticmethod
    def track_seo_conversion(conversion_type, value=0):
        """Track SEO-driven conversions"""
        referrer = request.headers.get('Referer', '')
        is_organic = any(search_engine in referrer for search_engine in 
                        ['google.', 'bing.', 'yahoo.', 'duckduckgo.'])
        
        conversion_data = {
            'event': 'seo_conversion',
            'conversion_type': conversion_type,  # 'registration', 'subscription', 'quiz_completion'
            'conversion_value': value,
            'traffic_source': 'organic' if is_organic else 'direct',
            'referrer': referrer
        }
        
        return f"""
        <script>
            if (window.dataLayer) {{
                window.dataLayer.push({json.dumps(conversion_data)});
            }}
        </script>
        """
    
    @staticmethod
    def _classify_search_intent(query):
        """Classify search intent for better SEO understanding"""
        query_lower = query.lower()
        
        # Informational intent
        if any(word in query_lower for word in ['hva', 'hvordan', 'når', 'hvor', 'hva er', 'hvorfor']):
            return 'informational'
        
        # Navigational intent  
        if any(word in query_lower for word in ['login', 'profil', 'dashboard', 'min side']):
            return 'navigational'
            
        # Transactional intent
        if any(word in query_lower for word in ['kjøp', 'abonnement', 'premium', 'registrer', 'meld deg på']):
            return 'transactional'
            
        # Educational intent (specific to driving theory)
        if any(word in query_lower for word in ['lær', 'øv', 'quiz', 'eksamen', 'teori']):
            return 'educational'
        
        return 'general'

class SearchConsoleIntegration:
    """Integration helpers for Google Search Console"""
    
    @staticmethod
    def generate_search_console_meta():
        """Generate meta tags for Search Console verification"""
        # This would contain the actual verification meta tag
        # Format: <meta name="google-site-verification" content="VERIFICATION_CODE">
        return {
            'google_verification': None,  # Add actual verification code
            'bing_verification': None,    # Add Bing verification code
            'yandex_verification': None   # Add Yandex verification code
        }
    
    @staticmethod
    def track_search_appearance():
        """Track how pages appear in search results"""
        return """
        <script>
            // Track search result impressions (when available)
            if ('IntersectionObserver' in window) {
                // Track when content comes into view
                const observer = new IntersectionObserver(function(entries) {
                    entries.forEach(function(entry) {
                        if (entry.isIntersecting) {
                            if (window.dataLayer) {
                                window.dataLayer.push({
                                    'event': 'content_view',
                                    'content_id': entry.target.id || 'unknown',
                                    'content_type': entry.target.tagName.toLowerCase()
                                });
                            }
                        }
                    });
                });
                
                // Observe important content sections
                document.querySelectorAll('h1, h2, .quiz-section, .video-section').forEach(function(el) {
                    observer.observe(el);
                });
            }
        </script>
        """

# Template filters for SEO
def register_seo_filters(app):
    """Register SEO-related template filters"""
    
    @app.template_filter('seo_title')
    def seo_title_filter(title, max_length=60):
        """Optimize title length for SEO"""
        if len(title) <= max_length:
            return title
        return title[:max_length-3] + '...'
    
    @app.template_filter('seo_description')
    def seo_description_filter(description, max_length=160):
        """Optimize description length for SEO"""
        if len(description) <= max_length:
            return description
        return description[:max_length-3] + '...'
    
    @app.template_filter('keywords_list')
    def keywords_list_filter(keywords):
        """Convert keywords list to comma-separated string"""
        if isinstance(keywords, list):
            return ', '.join(keywords)
        return keywords
