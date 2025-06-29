"""
SEO Rich Snippet Validation Helper
Tools to validate and test structured data for Google Rich Snippets
"""

import json
from flask import url_for, request

class RichSnippetValidator:
    """Helper class to validate and generate rich snippet data"""
    
    @staticmethod
    def validate_structured_data(structured_data_json):
        """
        Validate structured data format
        Returns: (is_valid, errors, warnings)
        """
        try:
            data = json.loads(structured_data_json) if isinstance(structured_data_json, str) else structured_data_json
            errors = []
            warnings = []
            
            # Basic validation
            if not isinstance(data, dict):
                errors.append("Structured data must be a JSON object")
                return False, errors, warnings
            
            # Required fields validation
            required_fields = ['@context', '@type']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Context validation
            if data.get('@context') != 'https://schema.org':
                warnings.append("@context should be 'https://schema.org'")
            
            # Type-specific validation
            schema_type = data.get('@type', '')
            
            if schema_type == 'WebSite':
                RichSnippetValidator._validate_website_schema(data, errors, warnings)
            elif schema_type == 'Quiz':
                RichSnippetValidator._validate_quiz_schema(data, errors, warnings)
            elif schema_type == 'Course':
                RichSnippetValidator._validate_course_schema(data, errors, warnings)
            elif schema_type == 'BreadcrumbList':
                RichSnippetValidator._validate_breadcrumb_schema(data, errors, warnings)
            
            is_valid = len(errors) == 0
            return is_valid, errors, warnings
            
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"], []
    
    @staticmethod
    def _validate_website_schema(data, errors, warnings):
        """Validate WebSite schema"""
        required = ['name', 'url']
        for field in required:
            if field not in data:
                errors.append(f"WebSite schema missing: {field}")
        
        # Check for search action
        if 'potentialAction' not in data:
            warnings.append("Consider adding potentialAction for sitelinks search box")
    
    @staticmethod
    def _validate_quiz_schema(data, errors, warnings):
        """Validate Quiz schema"""
        required = ['name', 'description']
        for field in required:
            if field not in data:
                errors.append(f"Quiz schema missing: {field}")
        
        recommended = ['educationalLevel', 'learningResourceType']
        for field in recommended:
            if field not in data:
                warnings.append(f"Quiz schema should include: {field}")
    
    @staticmethod
    def _validate_course_schema(data, errors, warnings):
        """Validate Course schema"""
        required = ['name', 'description', 'provider']
        for field in required:
            if field not in data:
                errors.append(f"Course schema missing: {field}")
    
    @staticmethod
    def _validate_breadcrumb_schema(data, errors, warnings):
        """Validate BreadcrumbList schema"""
        if 'itemListElement' not in data:
            errors.append("BreadcrumbList missing itemListElement")
            return
        
        items = data['itemListElement']
        if not isinstance(items, list) or len(items) == 0:
            errors.append("BreadcrumbList itemListElement must be non-empty array")
            return
        
        for i, item in enumerate(items):
            if item.get('@type') != 'ListItem':
                errors.append(f"Breadcrumb item {i} must have @type: ListItem")
            if 'position' not in item:
                errors.append(f"Breadcrumb item {i} missing position")
            if 'name' not in item:
                errors.append(f"Breadcrumb item {i} missing name")
    
    @staticmethod
    def generate_test_urls():
        """Generate URLs for testing structured data"""
        test_urls = {
            'google_rich_results': 'https://search.google.com/test/rich-results',
            'google_structured_data': 'https://developers.google.com/search/docs/appearance/structured-data',
            'schema_org_validator': 'https://validator.schema.org/',
            'json_ld_playground': 'https://json-ld.org/playground/'
        }
        return test_urls
    
    @staticmethod
    def get_testing_instructions():
        """Get step-by-step testing instructions"""
        return {
            'steps': [
                "1. Copy the structured data JSON from page source",
                "2. Go to Google Rich Results Test: https://search.google.com/test/rich-results",
                "3. Paste your URL or JSON-LD code",
                "4. Check for errors and warnings",
                "5. Validate with Schema.org validator: https://validator.schema.org/",
                "6. Test breadcrumbs appear correctly in search results"
            ],
            'common_issues': [
                "Missing required properties (name, description, url)",
                "Invalid URL formats (must be absolute URLs)",
                "Incorrect @type values",
                "Missing image properties for rich results",
                "Breadcrumb position values not sequential"
            ]
        }

class SEOTestingHelper:
    """Helper for SEO testing and validation"""
    
    @staticmethod
    def generate_sitemap_test_urls():
        """Generate URLs to test sitemap functionality"""
        base_url = request.url_root.rstrip('/')
        return {
            'sitemap_xml': f"{base_url}/sitemap.xml",
            'robots_txt': f"{base_url}/robots.txt",
            'google_search_console': 'https://search.google.com/search-console',
            'sitemap_validator': 'https://www.xml-sitemaps.com/validate-xml-sitemap.html'
        }
    
    @staticmethod
    def get_seo_checklist():
        """Get comprehensive SEO checklist"""
        return {
            'technical_seo': [
                "✓ Title tags optimized (50-60 characters)",
                "✓ Meta descriptions compelling (150-160 characters)", 
                "✓ Canonical URLs implemented",
                "✓ Robots.txt configured",
                "✓ XML sitemap generated",
                "✓ Structured data implemented",
                "✓ Page speed optimized",
                "✓ Mobile-friendly design",
                "✓ HTTPS enabled",
                "✓ 404 error pages handled"
            ],
            'content_seo': [
                "✓ Norwegian keywords targeted",
                "✓ Local SEO optimized for Norway",
                "✓ Header tags structured (H1, H2, H3)",
                "✓ Internal linking implemented",
                "✓ Image alt tags optimized",
                "✓ URL structure SEO-friendly",
                "✓ Content freshness maintained",
                "✓ User intent satisfied"
            ],
            'social_seo': [
                "✓ Open Graph tags implemented",
                "✓ Twitter Card tags added",
                "✓ Social media sharing optimized",
                "✓ Brand consistency maintained"
            ]
        }
    
    @staticmethod
    def validate_page_seo(title, description, url):
        """Validate basic page SEO"""
        issues = []
        warnings = []
        
        # Title validation
        if not title:
            issues.append("Missing page title")
        elif len(title) > 60:
            warnings.append(f"Title too long ({len(title)} chars, should be <60)")
        elif len(title) < 30:
            warnings.append(f"Title too short ({len(title)} chars, should be 30-60)")
        
        # Description validation
        if not description:
            issues.append("Missing meta description")
        elif len(description) > 160:
            warnings.append(f"Description too long ({len(description)} chars, should be <160)")
        elif len(description) < 120:
            warnings.append(f"Description too short ({len(description)} chars, should be 120-160)")
        
        # URL validation
        if not url:
            issues.append("Missing canonical URL")
        elif not url.startswith(('http://', 'https://')):
            issues.append("URL should be absolute (include http/https)")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
