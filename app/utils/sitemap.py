"""
XML Sitemap Generator for Sertifikatet
Automatically generates sitemap.xml for search engines
"""

from flask import Blueprint, Response, url_for, current_app
from datetime import datetime
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

sitemap_bp = Blueprint('sitemap', __name__)

class SitemapGenerator:
    """Generate XML sitemap for search engine crawlers"""
    
    @staticmethod
    def generate_sitemap():
        """Generate complete sitemap.xml"""
        
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        # Base URL
        base_url = current_app.config.get('SITE_URL', 'https://sertifikatet.no')
        
        # Homepage
        SitemapGenerator._add_url(urlset, base_url, 
                                 changefreq='daily', priority='1.0')
        
        # Static pages
        static_pages = [
            ('auth.login', 'weekly', '0.8'),
            ('auth.register', 'weekly', '0.8'),
            ('main.quiz_categories', 'daily', '0.9'),
            ('video.index', 'daily', '0.9'),
            ('game.index', 'weekly', '0.7'),
            ('learning.index', 'weekly', '0.7'),
            ('subscription.plans', 'monthly', '0.8'),
            ('legal.privacy', 'monthly', '0.5'),
            ('legal.terms', 'monthly', '0.5'),
        ]
        
        for endpoint, changefreq, priority in static_pages:
            try:
                url = url_for(endpoint, _external=True)
                SitemapGenerator._add_url(urlset, url, changefreq=changefreq, priority=priority)
            except Exception:
                # Skip if endpoint doesn't exist
                pass
        
        # Dynamic content (would need database queries in real implementation)
        # Quiz categories
        quiz_categories = [
            'trafikkregler', 'trafikkskilt', 'førstehjelp', 'miljø', 'sikkerhet'
        ]
        
        for category in quiz_categories:
            url = urljoin(base_url, f'/quiz/category/{category}')
            SitemapGenerator._add_url(urlset, url, changefreq='weekly', priority='0.8')
        
        # Video categories
        video_categories = [
            'trafikkregler', 'kjøreteknikk', 'sikkerhet', 'miljø'
        ]
        
        for category in video_categories:
            url = urljoin(base_url, f'/video/category/{category}')
            SitemapGenerator._add_url(urlset, url, changefreq='weekly', priority='0.7')
        
        # Game pages
        games = [
            'trafikkskilt', 'kjøresimulator', 'memory', 'puslespill'
        ]
        
        for game in games:
            url = urljoin(base_url, f'/game/{game}')
            SitemapGenerator._add_url(urlset, url, changefreq='monthly', priority='0.6')
        
        return ET.tostring(urlset, encoding='unicode', method='xml')
    
    @staticmethod
    def _add_url(urlset, loc, lastmod=None, changefreq=None, priority=None, images=None):
        """Add URL to sitemap"""
        url_elem = ET.SubElement(urlset, 'url')
        
        # Location (required)
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = loc
        
        # Last modification date
        if lastmod:
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = lastmod
        else:
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = datetime.now().strftime('%Y-%m-%d')
        
        # Change frequency
        if changefreq:
            changefreq_elem = ET.SubElement(url_elem, 'changefreq')
            changefreq_elem.text = changefreq
        
        # Priority
        if priority:
            priority_elem = ET.SubElement(url_elem, 'priority')
            priority_elem.text = priority
        
        # Images (for image sitemap)
        if images:
            for image in images:
                image_elem = ET.SubElement(url_elem, 'image:image')
                image_loc = ET.SubElement(image_elem, 'image:loc')
                image_loc.text = image.get('loc')
                if image.get('caption'):
                    image_caption = ET.SubElement(image_elem, 'image:caption')
                    image_caption.text = image.get('caption')

@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml"""
    sitemap_xml = SitemapGenerator.generate_sitemap()
    
    response = Response(sitemap_xml, mimetype='application/xml')
    response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
    
    return response

@sitemap_bp.route('/robots.txt')
def robots():
    """Serve robots.txt with environment-specific rules"""
    base_url = current_app.config.get('SITE_URL', 'https://sertifikatet.no')
    is_development = current_app.config.get('DEBUG') or current_app.config.get('ENVIRONMENT') == 'development'
    
    if is_development:
        # Development: Block all crawlers completely
        robots_content = f"""# DEVELOPMENT ENVIRONMENT - NO INDEXING ALLOWED
User-agent: *
Disallow: /

# Block all search engines during development
User-agent: Googlebot
Disallow: /

User-agent: Bingbot
Disallow: /

# No sitemap during development
# Sitemap: {base_url}/sitemap.xml
"""
    else:
        # Production: Normal SEO-friendly robots.txt
        robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /auth/profile
Disallow: /auth/logout
Disallow: /*?*
Disallow: /subscription/cancel
Disallow: /subscription/success

# Crawl-delay for polite crawling
Crawl-delay: 1

# Sitemap location
Sitemap: {base_url}/sitemap.xml

# Allow search engines to index main content
User-agent: Googlebot
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /auth/profile

User-agent: Bingbot
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /auth/profile
"""
    
    response = Response(robots_content, mimetype='text/plain')
    response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
    
    return response
