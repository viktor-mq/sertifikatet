from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime
import logging

from . import quiz_bp
from .. import db
from ..models import Question, QuizSession, QuizResponse, User
from ..ml.service import ml_service
from ..utils.subscription_decorators import quiz_limit_check
from ..services.payment_service import SubscriptionService, UsageLimitService

logger = logging.getLogger(__name__)


def get_questions_with_ml_check(user_id=None, category=None, num_questions=20, quiz_type='practice'):
    """
    Get questions with proper ML settings integration and fallback.
    This function respects ML activation settings and gracefully degrades.
    """
    try:
        # Check if ML system is enabled and user-specific features
        if (ml_service.is_ml_enabled() and 
            ml_service.is_feature_enabled('ml_adaptive_learning') and 
            user_id):
            
            logger.info(f"Using ML adaptive question selection for user {user_id}")
            questions = ml_service.get_adaptive_questions(
                user_id=user_id,
                category=category,
                num_questions=num_questions
            )
            
            if questions:
                return questions, True  # ML was used
                
        # Fallback to settings-aware selection
        return get_fallback_questions(category, num_questions), False
        
    except Exception as e:
        logger.error(f"Error in ML question selection: {e}")
        # Ultimate fallback
        return get_fallback_questions(category, num_questions), False


def get_fallback_questions(category=None, num_questions=20):
    """
    Get questions using fallback mode based on settings.
    """
    try:
        # Get fallback mode from settings
        from ..utils.settings_service import settings_service
        fallback_mode = settings_service.get_setting('ml_fallback_mode', default='random')
        
        logger.info(f"Using fallback mode: {fallback_mode}")
        
        query = Question.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        
        if fallback_mode == 'difficulty':
            # Order by difficulty level
            questions = query.order_by(Question.difficulty_level, Question.id).limit(num_questions).all()
        elif fallback_mode == 'category':
            # Distribute across categories
            questions = query.order_by(Question.category, Question.id).limit(num_questions).all()
        elif fallback_mode == 'legacy':
            # Use legacy system if available
            questions = query.order_by(Question.difficulty_level, Question.id).limit(num_questions).all()
        else:  # random
            questions = query.order_by(db.func.random()).limit(num_questions).all()
            
        return questions
        
    except Exception as e:
        logger.error(f"Error in fallback question selection: {e}")
        # Ultimate fallback - simple query
        query = Question.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        return query.limit(num_questions).all()


@quiz_bp.route('/practice/<category>')
@login_required
@quiz_limit_check('practice')
def practice(category):
    """Practice mode for a specific category with ML-powered question selection"""
    try:
        # Get questions using ML-aware selection with proper fallback
        questions, ml_used = get_questions_with_ml_check(
            user_id=current_user.id,
            category=category,
            num_questions=20,
            quiz_type='practice'
        )
        
        # Get ML insights and session config if ML features are enabled
        insights = {}
        session_config = {}
        
        if (ml_service.is_ml_enabled() and 
            ml_service.is_feature_enabled('ml_skill_tracking')):
            try:
                insights = ml_service.get_user_learning_insights(current_user.id)
            except Exception as e:
                logger.warning(f"Could not get ML insights: {e}")
                
        if (ml_service.is_ml_enabled() and 
            ml_service.is_feature_enabled('ml_adaptive_learning')):
            try:
                session_config = ml_service.get_next_session_config(current_user.id, category)
            except Exception as e:
                logger.warning(f"Could not get session config: {e}")
        
        return render_template('quiz/practice.html', 
                             questions=questions, 
                             category=category,
                             insights=insights,
                             session_config=session_config,
                             ml_enabled=ml_service.is_ml_enabled(),
                             ml_used=ml_used)
    
    except Exception as e:
        logger.error(f"Error in practice route: {e}")
        flash(f'Error loading practice questions: {str(e)}', 'error')
        
        # Ultimate fallback to basic question selection
        questions = Question.query.filter_by(
            category=category,
            is_active=True
        ).limit(20).all()
        
        return render_template('quiz/practice.html', 
                             questions=questions, 
                             category=category,
                             ml_enabled=False,
                             ml_used=False)


@quiz_bp.route('/adaptive-practice')
@login_required
def adaptive_practice():
    """Adaptive practice mode that selects optimal questions for the user"""
    try:
        # Check if adaptive learning is enabled
        if not (ml_service.is_ml_enabled() and 
                ml_service.is_feature_enabled('ml_adaptive_learning')):
            flash('Adaptive practice is currently disabled. Using regular practice mode.', 'info')
            return redirect(url_for('quiz.practice', category='all'))
        
        # Get ML-recommended session configuration
        session_config = ml_service.get_next_session_config(current_user.id)
        
        # Get adaptively selected questions across weak areas
        questions = ml_service.get_adaptive_questions(
            user_id=current_user.id,
            num_questions=session_config.get('suggested_question_count', 15)
        )
        
        # Get learning insights if skill tracking is enabled
        insights = {}
        if ml_service.is_feature_enabled('ml_skill_tracking'):
            try:
                insights = ml_service.get_user_learning_insights(current_user.id)
            except Exception as e:
                logger.warning(f"Could not get ML insights: {e}")
        
        return render_template('quiz/adaptive_practice.html',
                             questions=questions,
                             session_config=session_config,
                             insights=insights,
                             ml_enabled=True)
    
    except Exception as e:
        logger.error(f"Error in adaptive practice: {e}")
        flash(f'Error starting adaptive practice: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@quiz_bp.route('/start-practice', methods=['POST'])
@login_required
@quiz_limit_check('practice')
def start_practice():
    """Start a practice quiz session and redirect to quiz interface"""
    try:
        # Get form data
        category = request.form.get('category', 'all')
        num_questions = int(request.form.get('num_questions', 20))
        
        # Validate inputs
        if num_questions not in [10, 20, 30, 45]:
            num_questions = 20
        
        if category == 'all':
            category = None
        
        # Check subscription limits
        can_take, message = SubscriptionService.can_user_take_quiz(current_user.id, 'practice')
        if not can_take:
            flash(message, 'error')
            return redirect(url_for('quiz.practice', category=category or 'all'))
        
        # Create new quiz session
        quiz_session = QuizSession(
            user_id=current_user.id,
            quiz_type='practice',
            category=category,
            total_questions=num_questions,
            started_at=datetime.utcnow()
        )
        
        db.session.add(quiz_session)
        db.session.flush()  # Get the session ID
        
        # Record quiz usage for limits tracking
        UsageLimitService.record_quiz_taken(current_user.id, 'practice')
        
        db.session.commit()
        
        # Redirect to quiz interface
        return redirect(url_for('quiz.take_quiz', session_id=quiz_session.id))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error starting practice quiz: {e}')
        flash(f'Feil ved start av quiz: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@quiz_bp.route('/session/<int:session_id>')
@login_required
def take_quiz(session_id):
    """Display quiz interface for taking a quiz"""
    try:
        # Get session and validate ownership
        quiz_session = QuizSession.query.get_or_404(session_id)
        if quiz_session.user_id != current_user.id:
            flash('Uautorisert tilgang til quiz-økt', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Check if session is already completed
        if quiz_session.completed_at:
            flash('Denne quiz-økten er allerede fullført', 'info')
            return redirect(url_for('quiz.view_results', session_id=session_id))
        
        # Get questions for this session
        questions = []
        
        # 🎯 For daily challenges: Skip ML and use direct filtering (supports subcategory)
        is_daily_challenge = (quiz_session.quiz_type == 'daily_challenge' or 
                             (hasattr(quiz_session, 'challenge_id') and quiz_session.challenge_id))
        
        if not is_daily_challenge and ml_service.is_ml_enabled():
            try:
                # Use ML for regular practice sessions
                questions = ml_service.get_adaptive_questions(
                    user_id=current_user.id,
                    category=quiz_session.category, 
                    num_questions=quiz_session.total_questions,
                    session_id=session_id
                )
            except Exception as e:
                logger.warning(f'Could not get ML questions for session {session_id}: {e}')
        
        # Direct question selection for daily challenges or ML fallback
        if not questions:
            query = Question.query.filter_by(is_active=True)
            if quiz_session.category:
                # 🏞️ Use Norwegian category names directly, search both category AND subcategory
                category_norwegian = quiz_session.category  # Should be Norwegian (e.g., "vikepliktregler")
                
                # Search in both category and subcategory fields for flexibility
                query = query.filter(
                    db.or_(
                        Question.category == category_norwegian,
                        Question.subcategory == category_norwegian
                    )
                )
                logger.info(f"Filtering questions by Norwegian category/subcategory: {category_norwegian}")
                        
            questions = query.order_by(db.func.random()).limit(quiz_session.total_questions).all()
        
        if not questions:
            flash('Ingen spørsmål funnet for denne kategorien', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Add image folder discovery for each question (like working quiz template)
        import os
        from flask import current_app
        
        images_dir = os.path.join(current_app.static_folder, 'images')
        
        for question in questions:
            # Dynamic discovery of image folder
            image_folder = ''
            if question.image_filename:
                for root, dirs, files in os.walk(images_dir):
                    if question.image_filename in files:
                        image_folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                        break
            # Add image_folder attribute to question object
            question.image_folder = image_folder
        
        return render_template('quiz/quiz_session.html',
                             session=quiz_session,
                             questions=questions,
                             category=quiz_session.category or 'Generell')
    
    except Exception as e:
        logger.error(f'Error loading quiz session {session_id}: {e}')
        flash(f'Feil ved lasting av quiz: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@quiz_bp.route('/test-xp-integration')
@login_required
def test_xp_integration():
    """Test endpoint to verify XP integration is working"""
    try:
        from ..gamification.quiz_integration import process_quiz_completion
        from ..gamification.services import GamificationService
        
        # Test XP calculation
        test_xp = GamificationService.calculate_quiz_xp(
            correct_answers=15,
            total_questions=20, 
            score=75
        )
        
        return jsonify({
            'success': True,
            'message': 'XP integration working correctly',
            'test_calculation': test_xp,
            'current_user_xp': current_user.total_xp,
            'gamification_methods_available': {
                'get_xp_reward': hasattr(GamificationService, 'get_xp_reward'),
                'award_xp': hasattr(GamificationService, 'award_xp'),
                'check_achievements': hasattr(GamificationService, 'check_achievements'),
                'update_daily_challenge_progress': hasattr(GamificationService, 'update_daily_challenge_progress'),
                'check_and_update_streak': hasattr(GamificationService, 'check_and_update_streak')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'XP integration has issues'
        }), 500


@quiz_bp.route('/test-modal')
@login_required
def test_modal():
    """Test route to demonstrate the quiz results modal system"""
    # This is a test route to demonstrate the modal functionality
    return render_template('quiz/test_modal.html')


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
                category=question.category,  # Store actual question category
                subcategory=question.subcategory,  # Store granular subcategory
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
        
        # GAMIFICATION INTEGRATION: Process rewards and achievements
        gamification_rewards = {'xp_earned': 0, 'achievements': [], 'level_ups': [], 'daily_challenges': []}
        try:
            from ..gamification.quiz_integration import process_quiz_completion
            gamification_rewards = process_quiz_completion(current_user, quiz_session)
            
            # Handle daily challenge progress if this is a daily challenge
            if quiz_session.quiz_type == 'daily_challenge' and quiz_session.challenge_id:
                from ..gamification.services import GamificationService
                completed_challenges = GamificationService.update_daily_challenge_progress(
                    current_user, 'quiz', 1, quiz_session.category
                )
                if completed_challenges:
                    gamification_rewards['daily_challenges'] = completed_challenges
                    
        except Exception as gamification_error:
            # Log gamification error but don't fail the quiz submission
            print(f"Gamification integration error: {gamification_error}")
        
        # Update user progress using the service (like regular quiz)
        from ..services.progress_service import ProgressService
        progress_service = ProgressService()
        progress_service.update_user_progress(current_user.id, quiz_session)
        
        # Record quiz usage for limits tracking (like regular quiz)
        UsageLimitService.record_quiz_taken(current_user.id, quiz_session.quiz_type)
        
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
            'gamification': gamification_rewards,  # Add gamification rewards
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


@quiz_bp.route('/session/<int:session_id>/review')
@login_required
def review_session(session_id):
    """Get detailed review data for quiz session (for modal system)"""
    try:
        # Validate session ownership
        quiz_session = QuizSession.query.get_or_404(session_id)
        if quiz_session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        # Get all responses with question details
        responses = db.session.query(
            QuizResponse,
            Question
        ).join(
            Question, QuizResponse.question_id == Question.id
        ).filter(
            QuizResponse.session_id == session_id
        ).all()
        
        questions_data = []
        for response, question in responses:
            # Get question options
            options = [{
                'letter': opt.option_letter,
                'text': opt.option_text
            } for opt in question.options]
            
            # Add image folder discovery (same as take_quiz function)
            image_folder = ''
            if question.image_filename:
                import os
                from flask import current_app
                images_dir = os.path.join(current_app.static_folder, 'images')
                for root, dirs, files in os.walk(images_dir):
                    if question.image_filename in files:
                        image_folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                        break
            
            question_data = {
                'question_id': question.id,
                'question_text': question.question,
                'image_filename': question.image_filename,
                'image_folder': image_folder,
                'options': options,
                'correct_answer': question.correct_option,
                'user_answer': response.user_answer,
                'is_correct': response.is_correct,
                'time_spent': response.time_spent_seconds,
                'explanation': question.explanation,
                'category': question.category
            }
            questions_data.append(question_data)
        
        return jsonify({
            'success': True,
            'questions': questions_data,
            'session_info': {
                'id': quiz_session.id,
                'total_questions': quiz_session.total_questions,
                'correct_answers': quiz_session.correct_answers,
                'score': quiz_session.score,
                'time_spent': quiz_session.time_spent_seconds
            }
        })
    
    except Exception as e:
        logger.error(f'Error loading review data: {e}')
        return jsonify({'error': str(e), 'success': False}), 500


@quiz_bp.route('/daily-challenge/<int:challenge_id>')
@login_required
def daily_challenge(challenge_id):
    """Start or continue a daily challenge quiz"""
    try:
        from ..gamification_models import DailyChallenge, UserDailyChallenge
        
        # Get the challenge
        challenge = DailyChallenge.query.get_or_404(challenge_id)
        
        # Check if user has progress on this challenge
        user_challenge = UserDailyChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first()
        
        if user_challenge and user_challenge.completed:
            flash('Du har allerede fullført denne utfordringen!', 'info')
            return redirect(url_for('main.index'))
        
        # Create new quiz session for daily challenge
        quiz_session = QuizSession(
            user_id=current_user.id,
            quiz_type='daily_challenge',
            category=challenge.category,
            total_questions=challenge.requirement_value,
            started_at=datetime.utcnow()
        )
        
        db.session.add(quiz_session)
        db.session.flush()  # Get the session ID
        
        # Add challenge metadata to session
        quiz_session.challenge_id = challenge_id
        
        db.session.commit()
        
        # Redirect to quiz interface with challenge context
        return redirect(url_for('quiz.take_quiz', session_id=quiz_session.id, challenge=True))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error starting daily challenge {challenge_id}: {e}')
        flash(f'Feil ved start av daglig utfordring: {str(e)}', 'error')
        return redirect(url_for('main.index'))


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
        
        # Add image folder discovery for each question (same as take_quiz function)
        import os
        from flask import current_app
        
        images_dir = os.path.join(current_app.static_folder, 'images')
        
        for response in responses:
            if response.question and response.question.image_filename:
                # Dynamic discovery of image folder
                image_folder = ''
                for root, dirs, files in os.walk(images_dir):
                    if response.question.image_filename in files:
                        image_folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                        break
                # Add image_folder attribute to question object
                response.question.image_folder = image_folder
        
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
