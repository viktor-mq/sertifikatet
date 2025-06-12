from flask import jsonify, request
from . import api_bp
from .. import db
from ..models import Question, User, QuizSession, TrafficSign


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
    for q in questions:
        options = {}
        for opt in q.options:
            options[opt.option_letter] = opt.option_text
        
        result.append({
            'id': q.id,
            'question': q.question,
            'options': options,
            'category': q.category,
            'difficulty_level': q.difficulty_level,
            'image_filename': q.image_filename
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
