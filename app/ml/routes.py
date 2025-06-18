# app/ml/routes.py
"""
Routes for machine learning features and adaptive learning.
Provides API endpoints for ML-powered personalization.
"""
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user

from . import ml_bp
from .service import ml_service
from ..models import User, Question, QuizSession
from .. import db

@ml_bp.route('/insights')
@login_required
def learning_insights():
    """Display comprehensive learning insights for the current user"""
    try:
        insights = ml_service.get_user_learning_insights(current_user.id)
        skill_assessment = ml_service.get_skill_assessment(current_user.id)
        session_config = ml_service.get_next_session_config(current_user.id)
        ml_status = ml_service.get_ml_status()
        
        return render_template('ml/insights.html',
                             insights=insights,
                             skill_assessment=skill_assessment,
                             session_config=session_config,
                             ml_status=ml_status)
    except Exception as e:
        flash(f'Error loading learning insights: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@ml_bp.route('/api/adaptive-questions')
@login_required
def api_adaptive_questions():
    """API endpoint to get adaptively selected questions"""
    try:
        category = request.args.get('category')
        num_questions = request.args.get('num_questions', 10, type=int)
        session_id = request.args.get('session_id', type=int)
        
        # Validate input
        if num_questions < 1 or num_questions > 50:
            return jsonify({'error': 'Invalid number of questions'}), 400
        
        questions = ml_service.get_adaptive_questions(
            user_id=current_user.id,
            category=category,
            num_questions=num_questions,
            session_id=session_id
        )
        
        # Convert questions to JSON format
        questions_data = []
        for question in questions:
            question_data = {
                'id': question.id,
                'question': question.question,
                'category': question.category,
                'subcategory': question.subcategory,
                'difficulty_level': question.difficulty_level,
                'image_filename': question.image_filename,
                'explanation': question.explanation,
                'options': [
                    {
                        'letter': opt.option_letter,
                        'text': opt.option_text
                    }
                    for opt in question.options
                ],
                'correct_option': question.correct_option
            }
            questions_data.append(question_data)
        
        return jsonify({
            'questions': questions_data,
            'total_count': len(questions_data),
            'ml_enabled': ml_service.is_ml_enabled(),
            'personalization_applied': ml_service.is_ml_enabled()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/api/skill-assessment')
@login_required
def api_skill_assessment():
    """API endpoint to get current skill assessment"""
    try:
        assessment = ml_service.get_skill_assessment(current_user.id)
        return jsonify(assessment)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/api/study-recommendations')
@login_required
def api_study_recommendations():
    """API endpoint to get personalized study recommendations"""
    try:
        recommendations = ml_service.get_study_recommendations(current_user.id)
        weak_areas = ml_service.get_weak_areas(current_user.id)
        difficulty = ml_service.get_personalized_difficulty(current_user.id)
        
        return jsonify({
            'recommendations': recommendations,
            'weak_areas': weak_areas,
            'recommended_difficulty': difficulty,
            'ml_enabled': ml_service.is_ml_enabled()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/api/session-config')
@login_required
def api_session_config():
    """API endpoint to get recommended session configuration"""
    try:
        category = request.args.get('category')
        config = ml_service.get_next_session_config(current_user.id, category)
        
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/api/update-progress', methods=['POST'])
@login_required
def api_update_progress():
    """API endpoint to update learning progress after quiz completion"""
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'responses' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        session_id = data['session_id']
        responses = data['responses']
        
        # Validate that the session belongs to the current user
        session = QuizSession.query.get(session_id)
        if not session or session.user_id != current_user.id:
            return jsonify({'error': 'Invalid session'}), 403
        
        # Update ML models with the new performance data
        ml_service.update_learning_progress(current_user.id, session_id, responses)
        
        # Get updated insights
        updated_insights = ml_service.get_user_learning_insights(current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Learning progress updated successfully',
            'updated_insights': updated_insights
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ml_bp.route('/learning-dashboard')
@login_required
def learning_dashboard():
    """Comprehensive learning dashboard with ML insights"""
    try:
        # Get all ML-powered insights
        insights = ml_service.get_user_learning_insights(current_user.id)
        skill_assessment = ml_service.get_skill_assessment(current_user.id)
        session_config = ml_service.get_next_session_config(current_user.id)
        recommendations = ml_service.get_study_recommendations(current_user.id)
        weak_areas = ml_service.get_weak_areas(current_user.id)
        ml_status = ml_service.get_ml_status()
        
        # Get recent quiz sessions for progress tracking
        recent_sessions = QuizSession.query.filter_by(user_id=current_user.id)\
            .order_by(QuizSession.completed_at.desc()).limit(10).all()
        
        return render_template('ml/learning_dashboard.html',
                             insights=insights,
                             skill_assessment=skill_assessment,
                             session_config=session_config,
                             recommendations=recommendations,
                             weak_areas=weak_areas,
                             ml_status=ml_status,
                             recent_sessions=recent_sessions)
    except Exception as e:
        flash(f'Error loading learning dashboard: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@ml_bp.route('/personalized-quiz')
@login_required
def personalized_quiz():
    """Start a personalized quiz session"""
    try:
        category = request.args.get('category')
        
        # Get recommended session configuration
        session_config = ml_service.get_next_session_config(current_user.id, category)
        
        # Get user's learning insights
        insights = ml_service.get_user_learning_insights(current_user.id)
        
        return render_template('ml/personalized_quiz.html',
                             session_config=session_config,
                             insights=insights,
                             category=category)
    except Exception as e:
        flash(f'Error starting personalized quiz: {str(e)}', 'error')
        return redirect(url_for('quiz.practice', category=category or 'general'))
