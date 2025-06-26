from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime

from . import quiz_bp
from .. import db
from ..models import Question, QuizSession, QuizResponse, User
from ..ml.service import ml_service
from ..utils.subscription_decorators import quiz_limit_check
from ..services.payment_service import SubscriptionService, UsageLimitService


@quiz_bp.route('/practice/<category>')
@login_required
@quiz_limit_check('practice')
def practice(category):
    """Practice mode for a specific category with ML-powered question selection"""
    try:
        # Check if ML is enabled and use adaptive questions
        if ml_service.is_ml_enabled():
            # Get personalized questions for this category
            questions = ml_service.get_adaptive_questions(
                user_id=current_user.id,
                category=category,
                num_questions=20  # Default practice session size
            )
            
            # Get user's learning insights for this category
            insights = ml_service.get_user_learning_insights(current_user.id)
            session_config = ml_service.get_next_session_config(current_user.id, category)
            
            return render_template('quiz/practice.html', 
                                 questions=questions, 
                                 category=category,
                                 insights=insights,
                                 session_config=session_config,
                                 ml_enabled=True)
        else:
            # Fallback to regular question selection
            questions = Question.query.filter_by(
                category=category,
                is_active=True
            ).limit(20).all()
            
            return render_template('quiz/practice.html', 
                                 questions=questions, 
                                 category=category,
                                 ml_enabled=False)
    
    except Exception as e:
        flash(f'Error loading practice questions: {str(e)}', 'error')
        # Fallback to basic question selection
        questions = Question.query.filter_by(
            category=category,
            is_active=True
        ).limit(20).all()
        
        return render_template('quiz/practice.html', 
                             questions=questions, 
                             category=category,
                             ml_enabled=False)


@quiz_bp.route('/adaptive-practice')
@login_required
def adaptive_practice():
    """Adaptive practice mode that selects optimal questions for the user"""
    try:
        # Get ML-recommended session configuration
        session_config = ml_service.get_next_session_config(current_user.id)
        
        # Get adaptively selected questions across weak areas
        questions = ml_service.get_adaptive_questions(
            user_id=current_user.id,
            num_questions=session_config.get('suggested_question_count', 15)
        )
        
        # Get learning insights
        insights = ml_service.get_user_learning_insights(current_user.id)
        
        return render_template('quiz/adaptive_practice.html',
                             questions=questions,
                             session_config=session_config,
                             insights=insights)
    
    except Exception as e:
        flash(f'Error starting adaptive practice: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@quiz_bp.route('/session/start', methods=['POST'])
@login_required
def start_session():
    """Start a new quiz session with ML tracking"""
    try:
        data = request.get_json()
        quiz_type = data.get('quiz_type', 'practice')
        
        # Check subscription limits before starting session
        can_take, message = SubscriptionService.can_user_take_quiz(current_user.id, quiz_type)
        if not can_take:
            return jsonify({
                'error': 'Subscription limit reached',
                'message': message,
                'success': False
            }), 403
        category = data.get('category')
        
        # Create new quiz session
        quiz_session = QuizSession(
            user_id=current_user.id,
            quiz_type=quiz_type,
            category=category,
            started_at=datetime.utcnow()
        )
        
        db.session.add(quiz_session)
        db.session.flush()  # Get the session ID
        
        # Get ML-optimized questions for this session
        if ml_service.is_ml_enabled():
            questions = ml_service.get_adaptive_questions(
                user_id=current_user.id,
                category=category,
                num_questions=data.get('num_questions', 15),
                session_id=quiz_session.id
            )
        else:
            # Fallback to random selection
            query = Question.query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)
            questions = query.order_by(db.func.random()).limit(data.get('num_questions', 15)).all()
        
        quiz_session.total_questions = len(questions)
        db.session.commit()
        
        # Record quiz usage for limits tracking
        UsageLimitService.record_quiz_taken(current_user.id, quiz_type)
        
        # Convert questions to JSON format
        questions_data = []
        for question in questions:
            question_data = {
                'id': question.id,
                'question': question.question,
                'category': question.category,
                'difficulty_level': question.difficulty_level,
                'image_filename': question.image_filename,
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
            'session_id': quiz_session.id,
            'questions': questions_data,
            'ml_enabled': ml_service.is_ml_enabled(),
            'success': True,
            'analytics_data': {
                'user_id': current_user.id,
                'quiz_type': quiz_type,
                'category': category,
                'difficulty_level': questions[0].difficulty_level if questions else 1,
                'session_id': quiz_session.id,
                'num_questions': len(questions)
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@quiz_bp.route('/session/<int:session_id>/submit', methods=['POST'])
@login_required
def submit_session(session_id):
    """Submit quiz session results with ML learning progress update"""
    try:
        # Validate session ownership
        quiz_session = QuizSession.query.get_or_404(session_id)
        if quiz_session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        responses = data.get('responses', [])
        
        if not responses:
            return jsonify({'error': 'No responses provided'}), 400
        
        # Process and save quiz responses
        correct_count = 0
        total_time = 0
        ml_responses = []  # For ML system
        
        for response_data in responses:
            question_id = response_data.get('question_id')
            user_answer = response_data.get('user_answer')
            time_spent = response_data.get('time_spent', 0)
            
            # Get the question to check correct answer
            question = Question.query.get(question_id)
            if not question:
                continue
            
            is_correct = (user_answer == question.correct_option)
            if is_correct:
                correct_count += 1
            
            total_time += time_spent
            
            # Save response to database
            quiz_response = QuizResponse(
                session_id=session_id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                time_spent_seconds=time_spent
            )
            db.session.add(quiz_response)
            
            # Prepare data for ML system
            ml_response = {
                'question_id': question_id,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'time_spent': time_spent,
                'quiz_response_id': None  # Will be set after commit
            }
            ml_responses.append(ml_response)
        
        # Update quiz session with results
        quiz_session.correct_answers = correct_count
        quiz_session.time_spent_seconds = total_time
        quiz_session.score = (correct_count / len(responses)) * 100 if responses else 0
        quiz_session.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Update ML system with performance data
        if ml_service.is_ml_enabled():
            try:
                ml_service.update_learning_progress(current_user.id, session_id, ml_responses)
            except Exception as ml_error:
                # Log ML error but don't fail the quiz submission
                print(f"ML update error: {ml_error}")
        
        # Calculate performance metrics
        accuracy = (correct_count / len(responses)) * 100
        avg_time_per_question = total_time / len(responses) if responses else 0
        
        # Get updated learning insights if ML is enabled
        updated_insights = {}
        if ml_service.is_ml_enabled():
            try:
                updated_insights = ml_service.get_user_learning_insights(current_user.id)
            except Exception:
                # nosec B110: Graceful fallback for ML service - acceptable pattern
                pass  # Graceful fallback
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'results': {
                'correct_answers': correct_count,
                'total_questions': len(responses),
                'accuracy': accuracy,
                'total_time': total_time,
                'avg_time_per_question': avg_time_per_question,
                'score': quiz_session.score
            },
            'ml_insights': updated_insights,
            'ml_enabled': ml_service.is_ml_enabled(),
            'analytics_data': {
                'user_id': current_user.id,
                'session_id': session_id,
                'quiz_type': quiz_session.quiz_type,
                'category': quiz_session.category,
                'score': quiz_session.score,
                'total_questions': len(responses),
                'correct_answers': correct_count,
                'time_spent_seconds': total_time,
                'passed': accuracy >= 70,  # Assuming 70% is passing
                'difficulty_level': 1  # Could be calculated from questions
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@quiz_bp.route('/results/<int:session_id>')
@login_required
def view_results(session_id):
    """View detailed quiz results with ML insights"""
    try:
        # Get session and validate ownership
        quiz_session = QuizSession.query.get_or_404(session_id)
        if quiz_session.user_id != current_user.id:
            flash('Unauthorized access to quiz results', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get all responses for this session
        responses = QuizResponse.query.filter_by(session_id=session_id).all()
        
        # Get ML insights if available
        ml_insights = {}
        recommendations = []
        if ml_service.is_ml_enabled():
            try:
                ml_insights = ml_service.get_user_learning_insights(current_user.id)
                recommendations = ml_service.get_study_recommendations(current_user.id)
            except Exception:
                # nosec B110: Graceful fallback for ML service - acceptable pattern
                pass  # Graceful fallback
        
        return render_template('quiz/results.html',
                             session=quiz_session,
                             responses=responses,
                             ml_insights=ml_insights,
                             recommendations=recommendations,
                             ml_enabled=ml_service.is_ml_enabled())
    
    except Exception as e:
        flash(f'Error loading quiz results: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))
