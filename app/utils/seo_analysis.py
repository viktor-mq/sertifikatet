"""
SEO Analysis and Testing Routes (Development Only)
Provides tools to test and validate SEO implementation
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from ..utils.seo_validation import RichSnippetValidator, SEOTestingHelper
from ..utils.seo import SEOGenerator
from ..utils.seo_context import inject_seo_context
import json

seo_analysis_bp = Blueprint('seo_analysis', __name__, url_prefix='/seo')

@seo_analysis_bp.route('/test')
def seo_test_page():
    """SEO testing dashboard (development only)"""
    if not current_app.config.get('DEBUG'):
        return "SEO testing only available in development mode", 403
    
    # Get current page SEO data
    seo_context = inject_seo_context()
    
    # Generate testing URLs
    test_urls = RichSnippetValidator.generate_test_urls()
    sitemap_urls = SEOTestingHelper.generate_sitemap_test_urls()
    checklist = SEOTestingHelper.get_seo_checklist()
    instructions = RichSnippetValidator.get_testing_instructions()
    
    return render_template('seo/test_dashboard.html',
                         seo_context=seo_context,
                         test_urls=test_urls,
                         sitemap_urls=sitemap_urls,
                         checklist=checklist,
                         instructions=instructions)

@seo_analysis_bp.route('/validate', methods=['POST'])
def validate_structured_data():
    """Validate structured data JSON"""
    if not current_app.config.get('DEBUG'):
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        data = request.get_json()
        if not data or 'structured_data' not in data:
            return jsonify({'error': 'No structured data provided'}), 400
        
        structured_data = data['structured_data']
        is_valid, errors, warnings = RichSnippetValidator.validate_structured_data(structured_data)
        
        return jsonify({
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'test_urls': RichSnippetValidator.generate_test_urls()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_analysis_bp.route('/validate-page', methods=['POST'])
def validate_page_seo():
    """Validate page SEO elements"""
    if not current_app.config.get('DEBUG'):
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title', '')
        description = data.get('description', '')
        url = data.get('url', '')
        
        validation_result = SEOTestingHelper.validate_page_seo(title, description, url)
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_analysis_bp.route('/generate-sample/<schema_type>')
def generate_sample_schema(schema_type):
    """Generate sample structured data for testing"""
    if not current_app.config.get('DEBUG'):
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        if schema_type == 'website':
            sample_data = SEOGenerator.generate_structured_data('WebSite')
        elif schema_type == 'quiz':
            sample_data = SEOGenerator.generate_structured_data('Quiz', {
                'name': 'Trafikkskilt Quiz',
                'description': 'Test din kunnskap om norske trafikkskilt'
            })
        elif schema_type == 'course':
            sample_data = SEOGenerator.generate_structured_data('Course', {
                'name': 'Førerkort Teori Kurs',
                'description': 'Komplett kurs i førerkort teori'
            })
        elif schema_type == 'breadcrumb':
            sample_data = SEOGenerator.generate_breadcrumbs([
                ('Hjem', '/'),
                ('Quiz', '/quiz'),
                ('Trafikkskilt', '/quiz?category=Trafikkskilt')
            ])
        else:
            return jsonify({'error': 'Unknown schema type'}), 400
        
        return jsonify({
            'schema_type': schema_type,
            'structured_data': json.loads(sample_data) if isinstance(sample_data, str) else sample_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
