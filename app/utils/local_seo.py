"""
Local SEO and Content Optimization for Norwegian Market
"""

from flask import current_app
from .seo import SEOGenerator

class LocalSEO:
    """Local SEO optimization for Norwegian market"""
    
    # Norwegian driving theory keywords
    NORWEGIAN_KEYWORDS = [
        # Primary keywords
        'førerkort', 'teori', 'eksamen', 'quiz', 'norge',
        'trafikkregler', 'trafikkskilt', 'kjøreskole',
        
        # Secondary keywords
        'førerkortprøve', 'teorieksamenet', 'trafikkopplæring',
        'kjøreprøve', 'mc førerkort', 'bil førerkort',
        'teoriprøve', 'statens vegvesen', 'kjøretest',
        
        # Long-tail keywords
        'gratis førerkort quiz online',
        'førerkort teori på nett',
        'øv til teorieksamenet',
        'trafikkregler norway',
        'lær trafikkskilt',
        'hvordan ta førerkort i norge',
        'best score teorieksamenet',
        
        # Location-based
        'førerkort oslo', 'førerkort bergen', 'førerkort trondheim',
        'kjøreskole norge', 'teoriprøve online',
        
        # Question types
        'førstehjelpsspørsmål', 'miljøspørsmål', 'sikkerhetsspørsmål',
        'hastighetsspørsmål', 'vikepliktsregler'
    ]
    
    # Norwegian cities for local SEO
    NORWEGIAN_CITIES = [
        'Oslo', 'Bergen', 'Trondheim', 'Stavanger', 'Kristiansand',
        'Fredrikstad', 'Sandnes', 'Tromsø', 'Sarpsborg', 'Skien',
        'Ålesund', 'Drammen', 'Halden', 'Tønsberg', 'Moss'
    ]
    
    @staticmethod
    def generate_local_content_meta():
        """Generate local SEO meta tags"""
        return {
            'geo_region': 'NO',
            'geo_country': 'Norway',
            'geo_placename': 'Norway',
            'language': 'nb',
            'content_language': 'no',
            'distribution': 'Norway',
            'target_country': 'NO'
        }
    
    @staticmethod
    def generate_driving_education_schema():
        """Generate educational organization schema for driving theory"""
        return {
            "@context": "https://schema.org",
            "@type": "EducationalOrganization",
            "name": "Sertifikatet",
            "url": "https://sertifikatet.no",
            "description": "Norges ledende online platform for førerkort teori læring og eksamen forberedelse",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "NO",
                "addressRegion": "Norge"
            },
            "areaServed": {
                "@type": "Country",
                "name": "Norway"
            },
            "inLanguage": "nb",
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "Førerkort Teori Kurs",
                "itemListElement": [
                    {
                        "@type": "Course",
                        "name": "Gratis Førerkort Quiz",
                        "description": "Gratis online quiz for å øve til teorieksamenet",
                        "provider": {
                            "@type": "Organization",
                            "name": "Sertifikatet"
                        },
                        "hasCourseInstance": {
                            "@type": "CourseInstance",
                            "courseMode": "online",
                            "inLanguage": "nb"
                        },
                        "educationalLevel": "beginner",
                        "learningResourceType": "quiz",
                        "about": {
                            "@type": "Thing",
                            "name": "Norsk Førerkort Teori"
                        }
                    },
                    {
                        "@type": "Course", 
                        "name": "Premium Teori Kurs",
                        "description": "Avansert førerkort teori kurs med AI-tilpasset læring",
                        "provider": {
                            "@type": "Organization",
                            "name": "Sertifikatet"
                        },
                        "offers": {
                            "@type": "Offer",
                            "price": "149",
                            "priceCurrency": "NOK",
                            "availability": "https://schema.org/InStock"
                        }
                    }
                ]
            },
            "sameAs": [
                "https://www.facebook.com/sertifikatet",
                "https://www.instagram.com/sertifikatet"
            ]
        }

class ContentOptimizer:
    """Optimize content for driving education keywords"""
    
    @staticmethod
    def optimize_page_content(page_type, content_data=None):
        """Generate SEO-optimized content suggestions"""
        
        optimizations = {
            'homepage': {
                'h1': 'Lær Førerkort Teori Online - Gratis Quiz og Eksamen Forberedelse',
                'h2_suggestions': [
                    'Gratis Førerkort Quiz på Norsk',
                    'AI-Drevet Personlig Læring',
                    'Øv til Teorieksamenet',
                    'Alle Kategorier av Trafikkspørsmål'
                ],
                'content_keywords': [
                    'førerkort teori', 'gratis quiz', 'teorieksamenet',
                    'trafikkregler', 'trafikkskilt', 'norsk førerkort'
                ],
                'meta_description': 'Lær førerkort teori med Norges beste online platform. Gratis quiz, videoer og AI-læring. Perfekt forberedelse til teorieksamenet.',
                'faq_suggestions': [
                    'Hvor mange spørsmål er det på teorieksamenet?',
                    'Hvor mye koster det å ta førerkort i Norge?',
                    'Hvor ofte kan jeg ta teorieksamenet?',
                    'Hvilke dokumenter trenger jeg for førerkort?'
                ]
            },
            'quiz_page': {
                'h1': f'Førerkort Quiz: {content_data.get("category", "Alle Kategorier") if content_data else "Alle Kategorier"}',
                'h2_suggestions': [
                    'Øv på Ekte Eksamensspørsmål',
                    'Detaljerte Forklaringer',
                    'Spor Fremgangen Din'
                ],
                'content_keywords': [
                    'quiz', 'spørsmål', 'eksamen', 'øving',
                    content_data.get('category', '').lower() if content_data else ''
                ],
                'internal_links': [
                    ('Alle Quiz Kategorier', 'main.quiz_categories'),
                    ('Videoer', 'video.index'),
                    ('Min Fremgang', 'auth.profile')
                ]
            },
            'video_page': {
                'h1': 'Læringsvideoer for Førerkort Teori',
                'h2_suggestions': [
                    'Visuell Læring av Trafikkregler',
                    'Interaktive Video-Quiz',
                    'Ekspertforklaringer'
                ],
                'content_keywords': [
                    'video', 'læring', 'visuell', 'forklaring',
                    'kjøreteknikk', 'sikkerhet'
                ]
            }
        }
        
        return optimizations.get(page_type, {})
    
    @staticmethod
    def generate_faq_schema(faq_data):
        """Generate FAQ structured data"""
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for question, answer in faq_data:
            faq_schema["mainEntity"].append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer
                }
            })
        
        return faq_schema
    
    @staticmethod
    def generate_howto_schema(title, steps):
        """Generate HowTo structured data for guides"""
        howto_schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
            "step": []
        }
        
        for i, step in enumerate(steps, 1):
            howto_schema["step"].append({
                "@type": "HowToStep",
                "position": i,
                "name": step["name"],
                "text": step["description"]
            })
        
        return howto_schema
