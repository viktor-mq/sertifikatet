from flask import jsonify, request, session, current_app
import os
from . import api_bp
from .. import db
from ..models import Question, User, QuizSession, TrafficSign
from ..services.progress_service import ProgressService
from ..services.achievement_service import AchievementService
from ..services.leaderboard_service import LeaderboardService


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
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    progress_service = ProgressService()
    dashboard_data = progress_service.get_user_dashboard_data(session['user_id'])
    
    return jsonify(dashboard_data)


@api_bp.route('/progress/category/<category>', methods=['GET'])
def get_category_progress(category):
    """Get detailed progress for a specific category"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    progress_service = ProgressService()
    dashboard_data = progress_service.get_user_dashboard_data(session['user_id'])
    
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
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    achievement_service = AchievementService()
    achievements = achievement_service.get_user_achievements(session['user_id'])
    
    return jsonify({
        'achievements': achievements,
        'total_earned': len([a for a in achievements if a['earned']]),
        'total_available': len(achievements)
    })


@api_bp.route('/achievements/check', methods=['POST'])
def check_achievements():
    """Check for new achievements and award them"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    achievement_service = AchievementService()
    new_achievements = achievement_service.check_achievements(session['user_id'])
    
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
    if 'user_id' in session:
        user_rank = leaderboard_service.get_user_rank(
            session['user_id'],
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
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    leaderboard_type = request.args.get('type', 'weekly')
    category = request.args.get('category', 'overall')
    
    leaderboard_service = LeaderboardService()
    user_rank = leaderboard_service.get_user_rank(
        session['user_id'],
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
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    leaderboard_service = LeaderboardService()
    leaderboard_service.update_leaderboards(session['user_id'])
    
    return jsonify({'message': 'Leaderboards updated successfully'})
