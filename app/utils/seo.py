"""
SEO Configuration and Meta Tags for Sertifikatet
Comprehensive SEO implementation for driving theory platform
"""

from flask import request, url_for, current_app
from datetime import datetime
import json

class SEOConfig:
    """SEO configuration and meta tag generation"""
    
    # Default SEO settings
    DEFAULT_TITLE = "Sertifikatet - Norsk Førerkort Teori"
    DEFAULT_DESCRIPTION = "Lær førerkort teori med interaktive quizer, videoer og spill. Personalisert læring med AI. Gratis praksis og eksamen forberedelse for norsk førerkort."
    DEFAULT_KEYWORDS = "førerkort, teori, quiz, eksamen, norge, trafikkregler, trafikkskilt, kørekort, driving, license, theory, norway"
    
    SITE_NAME = "Sertifikatet"
    SITE_URL = "https://sertifikatet.no"
    DEFAULT_IMAGE = "/static/images/profiles/selskapslogo.png"
    
    # Social media handles
    TWITTER_HANDLE = "@sertifikatet"
    FACEBOOK_PAGE = "sertifikatet"
    
    # Organization info for structured data
    ORGANIZATION = {
        "name": "Sertifikatet",
        "url": "https://sertifikatet.no",
        "logo": "https://sertifikatet.no/static/images/profiles/selskapslogo.png",
        "description": "Norges ledende platform for førerkort teori læring",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "NO",
            "addressLocality": "Norge"
        }
    }

class SEOGenerator:
    """Generate SEO meta tags and structured data"""
    
    @staticmethod
    def generate_meta_tags(title=None, description=None, keywords=None, image=None, 
                          canonical_url=None, article_data=None, page_type="website", robots=None):
        """Generate comprehensive meta tags for a page"""
        
        # Use defaults if not provided
        title = title or SEOConfig.DEFAULT_TITLE
        description = description or SEOConfig.DEFAULT_DESCRIPTION
        keywords = keywords or SEOConfig.DEFAULT_KEYWORDS
        image = image or SEOConfig.DEFAULT_IMAGE
        canonical_url = canonical_url or request.url
        
        # Ensure image is absolute URL
        if image.startswith('/'):
            image = SEOConfig.SITE_URL + image
        
        meta_tags = {
            # Basic meta tags
            'title': title,
            'description': description,
            'keywords': keywords,
            'canonical_url': canonical_url,
            
            # Open Graph tags
            'og_title': title,
            'og_description': description,
            'og_image': image,
            'og_url': canonical_url,
            'og_type': page_type,
            'og_site_name': SEOConfig.SITE_NAME,
            
            # Twitter Card tags
            'twitter_card': 'summary_large_image',
            'twitter_site': SEOConfig.TWITTER_HANDLE,
            'twitter_title': title,
            'twitter_description': description,
            'twitter_image': image,
            
            # Additional meta tags
            'robots': robots or 'index, follow',
            'author': SEOConfig.SITE_NAME,
            'viewport': 'width=device-width, initial-scale=1.0',
            'charset': 'UTF-8',
            'language': 'no',
            'geo_region': 'NO',
            'geo_country': 'Norway'
        }
        
        # Article-specific tags
        if article_data:
            meta_tags.update({
                'article_author': article_data.get('author', SEOConfig.SITE_NAME),
                'article_published_time': article_data.get('published_time'),
                'article_modified_time': article_data.get('modified_time'),
                'article_section': article_data.get('section', 'Education'),
                'article_tag': article_data.get('tags', [])
            })
        
        return meta_tags
    
    @staticmethod
    def generate_structured_data(page_type="WebSite", page_data=None):
        """Generate JSON-LD structured data"""
        
        base_data = {
            "@context": "https://schema.org",
            "@type": page_type,
            "name": SEOConfig.SITE_NAME,
            "url": SEOConfig.SITE_URL,
            "description": SEOConfig.DEFAULT_DESCRIPTION,
            "inLanguage": "no",
            "publisher": SEOConfig.ORGANIZATION
        }
        
        if page_type == "WebSite":
            # Website schema
            base_data.update({
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{SEOConfig.SITE_URL}/quiz?q={{search_term_string}}",
                    "query-input": "required name=search_term_string"
                },
                "sameAs": [
                    f"https://facebook.com/{SEOConfig.FACEBOOK_PAGE}",
                    f"https://twitter.com/{SEOConfig.TWITTER_HANDLE.replace('@', '')}"
                ]
            })
        
        elif page_type == "EducationalOrganization":
            # Educational organization schema
            base_data.update({
                "@type": "EducationalOrganization",
                "hasOfferCatalog": {
                    "@type": "OfferCatalog",
                    "name": "Førerkort Teori Kurs",
                    "itemListElement": [
                        {
                            "@type": "Course",
                            "name": "Gratis Teori Quiz",
                            "description": "Gratis quiz for førerkort teori",
                            "provider": SEOConfig.ORGANIZATION
                        },
                        {
                            "@type": "Course",
                            "name": "Premium Teori Kurs",
                            "description": "Avansert teori kurs med AI-læring",
                            "provider": SEOConfig.ORGANIZATION
                        }
                    ]
                }
            })
        
        elif page_type == "Course" and page_data:
            # Course schema
            base_data.update({
                "@type": "Course",
                "name": page_data.get('name', 'Førerkort Teori'),
                "description": page_data.get('description', 'Lær førerkort teori'),
                "provider": SEOConfig.ORGANIZATION,
                "hasCourseInstance": {
                    "@type": "CourseInstance",
                    "courseMode": "online",
                    "inLanguage": "no"
                }
            })
        
        elif page_type == "Quiz" and page_data:
            # Quiz schema
            base_data.update({
                "@type": "Quiz",
                "name": page_data.get('name', 'Førerkort Quiz'),
                "description": page_data.get('description', 'Test din kunnskap'),
                "educationalLevel": "beginner",
                "learningResourceType": "quiz",
                "about": {
                    "@type": "Thing",
                    "name": "Førerkort Teori"
                }
            })
        
        elif page_type == "VideoObject" and page_data:
            # Video schema
            base_data.update({
                "@type": "VideoObject",
                "name": page_data.get('name'),
                "description": page_data.get('description'),
                "duration": page_data.get('duration'),
                "uploadDate": page_data.get('upload_date'),
                "thumbnailUrl": page_data.get('thumbnail'),
                "embedUrl": page_data.get('embed_url')
            })
        
        # Add page-specific data
        if page_data:
            base_data.update(page_data.get('additional_schema', {}))
        
        return json.dumps(base_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def generate_breadcrumbs(breadcrumb_list):
        """Generate breadcrumb structured data"""
        if not breadcrumb_list:
            return None
        
        breadcrumb_data = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        }
        
        for index, (name, url) in enumerate(breadcrumb_list):
            breadcrumb_data["itemListElement"].append({
                "@type": "ListItem",
                "position": index + 1,
                "name": name,
                "item": url if url.startswith('http') else SEOConfig.SITE_URL + url
            })
        
        return json.dumps(breadcrumb_data, ensure_ascii=False, indent=2)

class SEOPageConfigs:
    """Pre-configured SEO settings for different page types"""
    
    @staticmethod
    def homepage():
        return {
            'title': "Sertifikatet - Lær Førerkort Teori Online | Gratis Quiz og Eksamen",
            'description': "Norges beste platform for førerkort teori. Gratis quiz, interaktive videoer, AI-læring og eksamen forberedelse. Start din reise mot førerkort i dag!",
            'keywords': "førerkort teori, gratis quiz, eksamen forberedelse, trafikkregler, trafikkskilt, norge, ai læring, online kurs",
            'page_type': 'website',
            'structured_data_type': 'WebSite'
        }
    
    @staticmethod
    def quiz_page(category=None):
        title = f"Quiz: {category}" if category else "Førerkort Quiz"
        return {
            'title': f"{title} | Sertifikatet",
            'description': f"Test din kunnskap med {title.lower()}. Interaktive spørsmål med forklaringer og AI-tilpasset vanskelighetsgrad.",
            'keywords': f"quiz, {category.lower() if category else 'teori'}, spørsmål, eksamen, førerkort",
            'page_type': 'quiz',
            'structured_data_type': 'Quiz'
        }
    
    @staticmethod
    def video_page(video_title=None):
        title = video_title or "Læringsvideoer"
        return {
            'title': f"{title} | Sertifikatet",
            'description': f"Se {title.lower()} og lær førerkort teori visuelt. Interaktive videoer med quiz og notater.",
            'keywords': f"video, læring, {title.lower()}, førerkort, teori",
            'page_type': 'video',
            'structured_data_type': 'VideoObject'
        }
    
    @staticmethod
    def profile_page():
        return {
            'title': "Min Profil | Sertifikatet",
            'description': "Se din fremgang, statistikk og innstillinger. Tilpass din læringsopplevelse.",
            'keywords': "profil, fremgang, statistikk, innstillinger, personlig",
            'robots': 'noindex, nofollow'  # Private page
        }
    
    @staticmethod
    def subscription_page():
        return {
            'title': "Abonnement og Priser | Sertifikatet",
            'description': "Velg ditt abonnement. Premium funksjoner, AI-læring og ubegrenset tilgang til alle quiz og videoer.",
            'keywords': "abonnement, pris, premium, pro, ubegrenset tilgang",
            'page_type': 'product'
        }
