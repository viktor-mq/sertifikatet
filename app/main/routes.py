from flask import render_template, request, redirect, url_for, session, jsonify, flash
import random
from datetime import datetime
from . import main_bp
from .. import db
from ..models import Question, Option, QuizSession, QuizResponse, User, UserProgress


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
    
    # Get user progress
    progress = user.progress
    
    return render_template('dashboard.html', user=user, progress=progress)


@main_bp.route('/practice')
def practice():
    """Practice mode page"""
    if 'user_id' not in session:
        flash('Du må logge inn for å øve', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    
    # TODO: Implement practice mode
    return redirect(url_for('main.quiz'))


@main_bp.route('/exam')
def exam():
    """Mock exam page"""
    if 'user_id' not in session:
        flash('Du må logge inn for å ta prøveeksamen', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    
    # TODO: Implement exam mode
    return redirect(url_for('main.quiz'))


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
    if 'user_id' not in session:
        flash('Du må logge inn for å lagre resultatene', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    quiz_type = request.form.get('quiz_type', 'practice')
    start_time = int(request.form.get('start_time', 0))
    
    # Calculate time spent
    end_time = int(datetime.now().timestamp() * 1000)
    time_spent_seconds = (end_time - start_time) // 1000 if start_time else 0
    
    # Create quiz session
    quiz_session = QuizSession(
        user_id=user_id,
        quiz_type=quiz_type,
        started_at=datetime.fromtimestamp(start_time / 1000) if start_time else datetime.utcnow(),
        time_spent_seconds=time_spent_seconds
    )
    db.session.add(quiz_session)
    db.session.flush()
    
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
                
                # Save response
                response = QuizResponse(
                    session_id=quiz_session.id,
                    question_id=question_id,
                    user_answer=user_answer,
                    is_correct=is_correct
                )
                db.session.add(response)
                
                # Collect results for display
                results.append({
                    'question': question,
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'correct_answer': question.correct_option
                })
    
    # Update quiz session
    quiz_session.total_questions = total_questions
    quiz_session.correct_answers = correct_count
    quiz_session.score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    quiz_session.completed_at = datetime.utcnow()
    
    # Update user progress
    user = User.query.get(user_id)
    if user and user.progress:
        progress = user.progress
        progress.total_quizzes_taken += 1
        progress.total_questions_answered += total_questions
        progress.correct_answers += correct_count
        progress.last_activity_date = datetime.utcnow().date()
        
        # Update streak
        today = datetime.utcnow().date()
        if progress.last_activity_date:
            days_diff = (today - progress.last_activity_date).days
            if days_diff == 1:
                progress.current_streak_days += 1
            elif days_diff > 1:
                progress.current_streak_days = 1
        else:
            progress.current_streak_days = 1
        
        # Update longest streak
        if progress.current_streak_days > progress.longest_streak_days:
            progress.longest_streak_days = progress.current_streak_days
    
    db.session.commit()
    
    # Redirect to results page
    return redirect(url_for('main.quiz_results', session_id=quiz_session.id))


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
