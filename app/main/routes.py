from flask import render_template, request, redirect, url_for, session, jsonify, flash
import random
from datetime import datetime
from . import main_bp
from .. import db
from ..models import Question, Option, QuizSession, QuizResponse, User, UserProgress
from ..services.progress_service import ProgressService
from ..services.achievement_service import AchievementService
from ..services.leaderboard_service import LeaderboardService


@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


# Legacy route support for templates that use url_for('index')
@main_bp.route('/index')
def index_redirect():
    """Redirect legacy index route"""
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        flash('Du må logge inn for å se dashboardet', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash('Bruker ikke funnet', 'error')
        return redirect(url_for('main.index'))
    
    # Get comprehensive dashboard data using services
    progress_service = ProgressService()
    achievement_service = AchievementService()
    leaderboard_service = LeaderboardService()
    
    # Get user data with error handling
    try:
        dashboard_data = progress_service.get_user_dashboard_data(session['user_id'])
        achievements = achievement_service.get_user_achievements(session['user_id'])
        user_rank = leaderboard_service.get_user_rank(session['user_id'])
        
        # Get recent achievements (last 5 earned)
        recent_achievements = [a for a in achievements if a['earned']][-5:]
        
        # Get achievement stats
        achievement_stats = {
            'total_earned': len([a for a in achievements if a['earned']]),
            'total_available': len(achievements),
            'recent': recent_achievements
        }
    except Exception as e:
        # Fallback to basic data if services fail
        print(f"Dashboard data error: {e}")
        dashboard_data = None
        achievement_stats = None
        user_rank = None
    
    return render_template('dashboard.html', 
                         user=user, 
                         progress=user.progress,
                         dashboard_data=dashboard_data,
                         achievement_stats=achievement_stats,
                         user_rank=user_rank)


@main_bp.route('/practice')
def practice():
    """Practice mode page"""
    # Practice mode doesn't require login
    return redirect(url_for('main.quiz', type='practice'))


@main_bp.route('/exam')
def exam():
    """Mock exam page"""
    # Exam mode is available for all users
    return redirect(url_for('main.quiz', type='exam'))


@main_bp.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """Main quiz page"""
    # Get quiz parameters
    quiz_type = request.args.get('type', 'practice')
    category = request.args.get('category')
    limit = request.args.get('limit', type=int)
    
    # For exam mode, always use 45 questions
    if quiz_type == 'exam':
        limit = 45
    
    # Build query
    questions_query = Question.query.filter_by(is_active=True)
    
    # Apply category filter if specified
    if category:
        questions_query = questions_query.filter_by(category=category)
    
    # Get all questions
    questions_list = questions_query.all()
    
    # Shuffle questions for randomness
    random.shuffle(questions_list)
    
    # Apply limit if specified
    if limit:
        questions_list = questions_list[:limit]
    
    # Format questions for template
    questions = []
    for q in questions_list:
        question_data = {
            'id': q.id,
            'question': q.question,
            'category': q.category,
            'image_filename': q.image_filename,
            'image_folder': q.image_folder or 'signs',
            'correct_option': q.correct_option
        }
        
        # Add options
        for opt in q.options:
            question_data[f'option_{opt.option_letter}'] = opt.option_text
        
        questions.append(question_data)
    
    return render_template('quiz.html', questions=questions, quiz_type=quiz_type)


@main_bp.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    """Handle quiz submission"""
    quiz_type = request.form.get('quiz_type', 'practice')
    start_time = int(request.form.get('start_time', 0))
    
    # Calculate time spent
    end_time = int(datetime.now().timestamp() * 1000)
    time_spent_seconds = (end_time - start_time) // 1000 if start_time else 0
    
    # Process answers
    correct_count = 0
    total_questions = 0
    results = []
    
    # Get all answers from form
    for key in request.form:
        if key.startswith('answer_'):
            question_id = int(key.replace('answer_', ''))
            user_answer = request.form[key]
            
            # Get question
            question = Question.query.get(question_id)
            if question:
                total_questions += 1
                is_correct = user_answer == question.correct_option
                if is_correct:
                    correct_count += 1
                
                # Collect results for display
                results.append({
                    'question': question,
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'correct_answer': question.correct_option
                })
    
    # Calculate score
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # If user is logged in, save to database
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Create quiz session
        quiz_session = QuizSession(
            user_id=user_id,
            quiz_type=quiz_type,
            started_at=datetime.fromtimestamp(start_time / 1000) if start_time else datetime.utcnow(),
            time_spent_seconds=time_spent_seconds,
            total_questions=total_questions,
            correct_answers=correct_count,
            score=score,
            completed_at=datetime.utcnow()
        )
        db.session.add(quiz_session)
        db.session.flush()
        
        # Save individual responses
        for result in results:
            response = QuizResponse(
                session_id=quiz_session.id,
                question_id=result['question'].id,
                user_answer=result['user_answer'],
                is_correct=result['is_correct']
            )
            db.session.add(response)
        
        db.session.commit()
        
        # Update user progress using the service
        progress_service = ProgressService()
        progress_service.update_user_progress(user_id, quiz_session)
        
        # Check for new achievements
        achievement_service = AchievementService()
        new_achievements = achievement_service.check_achievements(user_id)
        
        # Update leaderboards
        leaderboard_service = LeaderboardService()
        leaderboard_service.update_leaderboards(user_id)
        
        # Store new achievements in session to show in results
        if new_achievements:
            session['new_achievements'] = [
                {
                    'name': ach.name,
                    'description': ach.description,
                    'points': ach.points,
                    'icon': ach.icon_filename
                } for ach in new_achievements
            ]
        
        # Redirect to results page
        return redirect(url_for('main.quiz_results', session_id=quiz_session.id))
    else:
        # For non-logged in users, store results in session
        session['temp_quiz_results'] = {
            'score': score,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'time_spent_seconds': time_spent_seconds,
            'results': results
        }
        return redirect(url_for('main.quiz_results_guest'))


@main_bp.route('/quiz/results/<int:session_id>')
def quiz_results(session_id):
    """Display quiz results"""
    if 'user_id' not in session:
        flash('Du må logge inn for å se resultatene', 'warning')
        return redirect(url_for('auth.login'))
    
    # Get quiz session
    quiz_session = QuizSession.query.filter_by(
        id=session_id,
        user_id=session['user_id']
    ).first()
    
    if not quiz_session:
        flash('Quiz ikke funnet', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get responses with questions
    responses = QuizResponse.query.filter_by(session_id=session_id).all()
    
    # Format results
    results = []
    for response in responses:
        question = response.question
        results.append({
            'question': question,
            'user_answer': response.user_answer,
            'is_correct': response.is_correct,
            'correct_answer': question.correct_option,
            'options': {opt.option_letter: opt.option_text for opt in question.options}
        })
    
    return render_template('quiz_results.html', 
                         session=quiz_session, 
                         results=results)


@main_bp.route('/quiz/results/guest')
def quiz_results_guest():
    """Display quiz results for guest users"""
    temp_results = session.get('temp_quiz_results')
    
    if not temp_results:
        flash('Ingen quiz resultater funnet', 'error')
        return redirect(url_for('main.quiz'))
    
    # Create a mock session object for template compatibility
    quiz_session = type('obj', (object,), {
        'score': temp_results['score'],
        'correct_answers': temp_results['correct_answers'],
        'total_questions': temp_results['total_questions'],
        'time_spent_seconds': temp_results['time_spent_seconds']
    })
    
    # Format results
    results = []
    for result in temp_results['results']:
        question = result['question']
        results.append({
            'question': question,
            'user_answer': result['user_answer'],
            'is_correct': result['is_correct'],
            'correct_answer': result['correct_answer'],
            'options': {opt.option_letter: opt.option_text for opt in question.options}
        })
    
    # Clear temp results
    session.pop('temp_quiz_results', None)
    
    # Add a flash message encouraging registration
    flash('Logg inn for å lagre resultatene dine og spore fremgangen din!', 'info')
    
    return render_template('quiz_results.html', 
                         session=quiz_session, 
                         results=results,
                         is_guest=True)


@main_bp.route('/quiz/categories')
def quiz_categories():
    """Quiz category selection page"""
    # Get all categories with question counts
    category_counts = db.session.query(
        Question.category,
        db.func.count(Question.id).label('count')
    ).filter(
        Question.is_active == True,
        Question.category.isnot(None)
    ).group_by(Question.category).all()
    
    # Format categories with icons and colors
    category_map = {
        'Fareskilt': {'icon': 'fa-exclamation-triangle', 'color': 'red', 'description': 'Lær om skilt som varsler om fare'},
        'Påbudsskilt': {'icon': 'fa-arrow-circle-right', 'color': 'blue', 'description': 'Skilt som påbyr bestemte handlinger'},
        'Forbudsskilt': {'icon': 'fa-ban', 'color': 'red', 'description': 'Skilt som forbyr bestemte handlinger'},
        'Vikeplikt': {'icon': 'fa-hand-paper', 'color': 'yellow', 'description': 'Regler for vikeplikt og forkjørsrett'},
        'Opplysningsskilt': {'icon': 'fa-info-circle', 'color': 'blue', 'description': 'Skilt som gir informasjon'},
        'Serviceskilt': {'icon': 'fa-concierge-bell', 'color': 'green', 'description': 'Skilt for service og fasiliteter'},
        'Vegvisningsskilt': {'icon': 'fa-directions', 'color': 'green', 'description': 'Skilt for vegvisning og retning'},
        'Trafikkregler': {'icon': 'fa-traffic-light', 'color': 'purple', 'description': 'Generelle trafikkregler og lover'}
    }
    
    categories = []
    total_questions = 0
    
    for cat_name, count in category_counts:
        total_questions += count
        cat_info = category_map.get(cat_name, {
            'icon': 'fa-question-circle',
            'color': 'gray',
            'description': 'Spørsmål i denne kategorien'
        })
        categories.append({
            'name': cat_name,
            'count': count,
            'icon': cat_info['icon'],
            'color': cat_info['color'],
            'description': cat_info['description']
        })
    
    # Sort by count descending
    categories.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template('quiz_categories.html', 
                         categories=categories,
                         total_questions=total_questions)


@main_bp.route('/api/questions')
def api_questions():
    """API endpoint to get questions"""
    category = request.args.get('category')
    limit = request.args.get('limit', type=int)
    
    query = Question.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if limit:
        query = query.limit(limit)
    
    questions = query.all()
    
    # Format for JSON response
    result = []
    for q in questions:
        options = {opt.option_letter: opt.option_text for opt in q.options}
        result.append({
            'id': q.id,
            'question': q.question,
            'options': options,
            'correct_option': q.correct_option,
            'category': q.category,
            'image_filename': q.image_filename
        })
    
    return jsonify(result)


@main_bp.route('/categories')
def categories():
    """Get all available categories"""
    cats = db.session.query(Question.category).distinct().filter(
        Question.category.isnot(None),
        Question.is_active == True
    ).all()
    
    category_list = [cat[0] for cat in cats if cat[0]]
    
    return jsonify(category_list)


@main_bp.route('/achievements')
def achievements():
    """Achievements page"""
    if 'user_id' not in session:
        flash('Du må logge inn for å se utmerkelser', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    
    # Get achievement stats for template
    achievement_service = AchievementService()
    achievements_data = achievement_service.get_user_achievements(session['user_id'])
    
    total_earned = len([a for a in achievements_data if a['earned']])
    total_available = len(achievements_data)
    
    return render_template('progress/achievements.html',
                         total_earned=total_earned,
                         total_available=total_available)


@main_bp.route('/leaderboard')
def leaderboard():
    """Leaderboard page"""
    return render_template('progress/leaderboard.html')
