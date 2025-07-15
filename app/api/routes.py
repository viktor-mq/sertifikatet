from flask import jsonify, request, session, current_app
from flask_login import current_user
import os
import logging
from . import api_bp
from .. import db
from ..models import Question, User, QuizSession, TrafficSign, Achievement
from ..services.progress_service import ProgressService
from ..services.achievement_service import AchievementService
from ..services.leaderboard_service import LeaderboardService
from ..ml.service import ml_service

logger = logging.getLogger(__name__)


def add_ml_debug_info(response_data, include_sensitive=False):
    """
    Add ML debug information to API responses for internal debugging.
    Only includes sensitive info for admin users.
    """
    if current_user.is_authenticated and current_user.is_admin and include_sensitive:
        response_data['_ml_debug'] = {
            'ml_enabled': ml_service.is_ml_enabled(),
            'features': {
                'adaptive_learning': ml_service.is_feature_enabled('ml_adaptive_learning'),
                'skill_tracking': ml_service.is_feature_enabled('ml_skill_tracking'),
                'difficulty_prediction': ml_service.is_feature_enabled('ml_difficulty_prediction'),
                'data_collection': ml_service.is_feature_enabled('ml_data_collection'),
            }
        }
    return response_data


@api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    Internal system status endpoint (admin only).
    """
    if not (current_user.is_authenticated and current_user.is_admin):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        status = {
            'ml_system': {
                'enabled': ml_service.is_ml_enabled(),
                'features': {
                    'adaptive_learning': ml_service.is_feature_enabled('ml_adaptive_learning'),
                    'skill_tracking': ml_service.is_feature_enabled('ml_skill_tracking'),
                    'difficulty_prediction': ml_service.is_feature_enabled('ml_difficulty_prediction'),
                    'data_collection': ml_service.is_feature_enabled('ml_data_collection'),
                    'model_retraining': ml_service.is_feature_enabled('ml_model_retraining'),
                }
            },
            'database': {
                'connected': True,  # If we got here, DB is working
                'total_users': User.query.count(),
                'total_questions': Question.query.count(),
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': 'System status unavailable'}), 500


@api_bp.route('/questions', methods=['GET'])
def get_questions():
    """Get questions with optional filters"""
    category = request.args.get('category')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Question.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    total = query.count()
    
    if limit:
        query = query.limit(limit).offset(offset)
    
    questions = query.all()
    
    result = []
    images_dir = os.path.join(current_app.static_folder, 'images')
    
    for q in questions:
        # Dynamic discovery of image folder
        image_folder = ''
        if q.image_filename:
            for root, dirs, files in os.walk(images_dir):
                if q.image_filename in files:
                    image_folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                    break
        
        options = {}
        for opt in q.options:
            options[opt.option_letter] = opt.option_text
        
        result.append({
            'id': q.id,
            'question': q.question,
            'options': options,
            'category': q.category,
            'difficulty_level': q.difficulty_level,
            'image_filename': q.image_filename,
            'image_folder': image_folder
        })
    
    return jsonify({
        'questions': result,
        'total': total,
        'offset': offset,
        'limit': limit
    })


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique categories with question counts"""
    categories = db.session.query(
        Question.category,
        db.func.count(Question.id).label('count')
    ).filter(
        Question.is_active == True,
        Question.category.isnot(None)
    ).group_by(Question.category).all()
    
    result = [
        {'name': cat[0], 'count': cat[1]} 
        for cat in categories if cat[0]
    ]
    
    return jsonify(result)


@api_bp.route('/traffic-signs', methods=['GET'])
def get_traffic_signs():
    """Get all traffic signs"""
    category = request.args.get('category')
    
    query = TrafficSign.query
    
    if category:
        query = query.filter_by(category=category)
    
    signs = query.all()
    
    result = []
    for sign in signs:
        result.append({
            'id': sign.id,
            'sign_code': sign.sign_code,
            'description': sign.description,
            'category': sign.category,
            'filename': sign.filename,
            'explanation': sign.explanation
        })
    
    return jsonify(result)


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get general statistics"""
    stats = {
        'total_questions': Question.query.filter_by(is_active=True).count(),
        'total_users': User.query.count(),
        'total_quiz_sessions': QuizSession.query.count(),
        'total_traffic_signs': TrafficSign.query.count(),
        'categories': db.session.query(
            Question.category
        ).distinct().filter(
            Question.category.isnot(None),
            Question.is_active == True
        ).count()
    }
    
    return jsonify(stats)


# Progress API Endpoints
@api_bp.route('/progress/dashboard', methods=['GET'])
def get_progress_dashboard():
    """Get user progress dashboard data"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    progress_service = ProgressService()
    dashboard_data = progress_service.get_user_dashboard_data(current_user.id)
    
    return jsonify(dashboard_data)


@api_bp.route('/progress/category/<category>', methods=['GET'])
def get_category_progress(category):
    """Get detailed progress for a specific category"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    progress_service = ProgressService()
    dashboard_data = progress_service.get_user_dashboard_data(current_user.id)
    
    # Find the specific category
    category_data = None
    for cat in dashboard_data.get('category_performance', []):
        if cat['category'] == category:
            category_data = cat
            break
    
    if not category_data:
        return jsonify({'error': 'Category not found'}), 404
    
    return jsonify(category_data)


# Achievement API Endpoints
@api_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """Get all achievements for the current user"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    achievement_service = AchievementService()
    achievements = achievement_service.get_user_achievements(current_user.id)
    
    return jsonify({
        'achievements': achievements,
        'total_earned': len([a for a in achievements if a['earned']]),
        'total_available': len(achievements)
    })


@api_bp.route('/achievements/check', methods=['POST'])
def check_achievements():
    """Check for new achievements and award them"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    achievement_service = AchievementService()
    new_achievements = achievement_service.check_achievements(current_user.id)
    
    return jsonify({
        'new_achievements': [
            {
                'id': ach.id,
                'name': ach.name,
                'description': ach.description,
                'points': ach.points,
                'icon': ach.icon_filename
            } for ach in new_achievements
        ],
        'count': len(new_achievements)
    })


@api_bp.route('/achievement/metadata', methods=['GET'])
def get_achievement_metadata():
    """Get achievement metadata for admin dropdown population"""
    try:
        # Get unique categories from achievements table
        categories = db.session.query(Achievement.category).distinct().filter(
            Achievement.category.isnot(None),
            Achievement.category != ''
        ).all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        # Get unique requirement types from achievements table
        requirement_types = db.session.query(Achievement.requirement_type).distinct().filter(
            Achievement.requirement_type.isnot(None),
            Achievement.requirement_type != ''
        ).all()
        requirement_types = [req[0] for req in requirement_types if req[0]]
        
        return jsonify({
            'categories': sorted(categories),
            'requirement_types': sorted(requirement_types)
        })
        
    except Exception as e:
        logger.error(f"Error getting achievement metadata: {e}")
        return jsonify({'error': 'Failed to get achievement metadata'}), 500


# Leaderboard API Endpoints
@api_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard data"""
    leaderboard_type = request.args.get('type', 'weekly')
    category = request.args.get('category', 'overall')
    limit = request.args.get('limit', 10, type=int)
    
    leaderboard_service = LeaderboardService()
    leaderboard = leaderboard_service.get_leaderboard(
        leaderboard_type=leaderboard_type,
        category=category,
        limit=limit
    )
    
    # Get current user's rank if logged in
    user_rank = None
    if current_user.is_authenticated:
        user_rank = leaderboard_service.get_user_rank(
            current_user.id,
            leaderboard_type=leaderboard_type,
            category=category
        )
    
    return jsonify({
        'leaderboard': leaderboard,
        'user_rank': user_rank,
        'type': leaderboard_type,
        'category': category
    })


@api_bp.route('/leaderboard/user-rank', methods=['GET'])
def get_user_rank():
    """Get current user's rank in leaderboards"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    leaderboard_type = request.args.get('type', 'weekly')
    category = request.args.get('category', 'overall')
    
    leaderboard_service = LeaderboardService()
    user_rank = leaderboard_service.get_user_rank(
        current_user.id,
        leaderboard_type=leaderboard_type,
        category=category
    )
    
    if user_rank:
        return jsonify(user_rank)
    else:
        return jsonify({
            'rank': None,
            'score': 0,
            'total_players': 0,
            'message': 'No ranking data available'
        })


# Update leaderboards endpoint (typically called after quiz completion)
@api_bp.route('/leaderboard/update', methods=['POST'])
def update_leaderboards():
    """Update leaderboards for current user"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    leaderboard_service = LeaderboardService()
    leaderboard_service.update_leaderboards(current_user.id)
    
    return jsonify({'message': 'Leaderboards updated successfully'})
