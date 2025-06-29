"""
SEO Template Context Processor
Injects SEO data into all templates
"""

from flask import request, url_for
from .seo import SEOGenerator, SEOPageConfigs

def inject_seo_context():
    """Inject SEO context into all templates"""
    
    # Get current route
    endpoint = request.endpoint
    
    # Determine page type and generate appropriate SEO data
    seo_data = None
    structured_data = None
    breadcrumb_data = None
    breadcrumbs = None  # For template compatibility
    
    if endpoint == 'main.index':
        # Homepage
        config = SEOPageConfigs.homepage()
        seo_data = SEOGenerator.generate_meta_tags(
            title=config['title'],
            description=config['description'],
            keywords=config['keywords'],
            page_type=config['page_type']
        )
        structured_data = SEOGenerator.generate_structured_data(
            page_type=config['structured_data_type']
        )
        
    elif endpoint and 'quiz' in endpoint:
        # Quiz pages
        category = request.args.get('category', 'Generell')
        config = SEOPageConfigs.quiz_page(category)
        seo_data = SEOGenerator.generate_meta_tags(
            title=config['title'],
            description=config['description'],
            keywords=config['keywords'],
            page_type=config['page_type']
        )
        structured_data = SEOGenerator.generate_structured_data(
            page_type=config['structured_data_type'],
            page_data={'name': f'Quiz: {category}', 'description': config['description']}
        )
        
        # Generate breadcrumbs for quiz pages
        breadcrumb_list = [('Hjem', url_for('main.index'))]
        
        if endpoint == 'main.quiz_categories':
            breadcrumb_list.append(('Quiz Kategorier', request.url))
        elif endpoint in ['main.quiz', 'quiz.quiz']:
            breadcrumb_list.append(('Quiz', url_for('main.quiz_categories')))
            if category != 'Generell':
                breadcrumb_list.append((category, request.url))
            else:
                breadcrumb_list.append(('Øvingsmodus', request.url))
        elif endpoint == 'main.quiz_results':
            breadcrumb_list.extend([
                ('Quiz', url_for('main.quiz_categories')),
                ('Resultater', request.url)
            ])
        else:
            breadcrumb_list.append(('Quiz', request.url))
            
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list  # For template usage
        
    elif endpoint and 'video' in endpoint:
        # Video pages
        video_title = request.args.get('title', 'Læringsvideoer')
        config = SEOPageConfigs.video_page(video_title)
        seo_data = SEOGenerator.generate_meta_tags(
            title=config['title'],
            description=config['description'],
            keywords=config['keywords'],
            page_type=config['page_type']
        )
        structured_data = SEOGenerator.generate_structured_data(
            page_type=config['structured_data_type'],
            page_data={'name': video_title, 'description': config['description']}
        )
        
        # Generate breadcrumbs for video pages
        breadcrumb_list = [('Hjem', url_for('main.index'))]
        
        if endpoint == 'video.index':
            breadcrumb_list.append(('Videoer', request.url))
        elif endpoint == 'video.watch':
            breadcrumb_list.extend([
                ('Videoer', url_for('video.index')),
                (video_title, request.url)
            ])
        elif endpoint == 'video.category':
            category = request.view_args.get('category', 'Kategori')
            breadcrumb_list.extend([
                ('Videoer', url_for('video.index')),
                (category.title(), request.url)
            ])
        else:
            breadcrumb_list.append(('Videoer', request.url))
            
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
        
    elif endpoint == 'auth.profile':
        # Profile page
        config = SEOPageConfigs.profile_page()
        seo_data = SEOGenerator.generate_meta_tags(
            title=config['title'],
            description=config['description'],
            keywords=config['keywords'],
            robots=config['robots']
        )
        breadcrumb_list = [('Hjem', url_for('main.index')), ('Min Profil', request.url)]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
        
    elif endpoint and 'subscription' in endpoint:
        # Subscription pages
        config = SEOPageConfigs.subscription_page()
        seo_data = SEOGenerator.generate_meta_tags(
            title=config['title'],
            description=config['description'],
            keywords=config['keywords'],
            page_type=config['page_type']
        )
        structured_data = SEOGenerator.generate_structured_data(
            page_type='EducationalOrganization'
        )
        breadcrumb_list = [('Hjem', url_for('main.index')), ('Abonnement', request.url)]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
    
    # Add more specific page handling
    # Note: Dashboard functionality is handled by the index route for authenticated users
        
    elif endpoint == 'main.achievements':
        # Achievements page
        seo_data = SEOGenerator.generate_meta_tags(
            title='Prestasjoner - Sertifikatet',
            description='Se dine låste prestasjoner og badges for førerkort teori læring.',
            keywords='prestasjoner, badges, achievement, belønninger'
        )
        breadcrumb_list = [('Hjem', url_for('main.index')), ('Prestasjoner', request.url)]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
        
    elif endpoint == 'main.leaderboard':
        # Leaderboard page
        seo_data = SEOGenerator.generate_meta_tags(
            title='Ledertavle - Sertifikatet',
            description='Se topp spillere og din ranking i førerkort teori læring.',
            keywords='ledertavle, ranking, konkurranse, topp spillere'
        )
        breadcrumb_list = [('Hjem', url_for('main.index')), ('Ledertavle', request.url)]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
        
    elif endpoint == 'game.index':
        # Games page
        seo_data = SEOGenerator.generate_meta_tags(
            title='Spill - Sertifikatet',
            description='Lær førerkort teori gjennom morsomme og interaktive spill.',
            keywords='spill, læring, interaktiv, gamification, quiz spill'
        )
        breadcrumb_list = [('Hjem', url_for('main.index')), ('Spill', request.url)]
        breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
        breadcrumbs = breadcrumb_list
    
    # Set default breadcrumbs for pages without specific handling
    if breadcrumbs is None and endpoint and endpoint != 'main.index':
        try:
            page_name = endpoint.split('.')[-1].replace('_', ' ').title()
            breadcrumb_list = [('Hjem', url_for('main.index')), (page_name, request.url)]
            breadcrumb_data = SEOGenerator.generate_breadcrumbs(breadcrumb_list)
            breadcrumbs = breadcrumb_list
        except Exception:
            # Fallback if URL generation fails
            breadcrumbs = None
            breadcrumb_data = None
    
    return {
        'seo': seo_data,
        'structured_data': structured_data,
        'breadcrumb_data': breadcrumb_data,
        'breadcrumbs': breadcrumbs  # For template compatibility
    }
