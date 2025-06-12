from flask import render_template, request, redirect, url_for, session, jsonify
import random
from . import main_bp
from .. import db
from ..models import Question, Option, QuizSession, QuizResponse


@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


# Legacy route support for templates that use url_for('index')
@main_bp.route('/index')
def index_redirect():
    """Redirect legacy index route"""
    return redirect(url_for('main.index'))


@main_bp.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """Main quiz page"""
    if request.method == 'POST':
        # Process quiz submission
        questions = Question.query.filter_by(is_active=True).all()
        score = 0
        
        # Create a new quiz session if user is logged in
        # For now, we'll just calculate the score
        for i, q in enumerate(questions):
            selected = request.form.get(f'q{i}')
            if selected == q.correct_option:
                score += 1
        
        return render_template('results.html', score=score, total=len(questions))
    
    # Get questions with their options
    questions_query = Question.query.filter_by(is_active=True)
    
    # Apply category filter if specified
    category = request.args.get('category')
    if category:
        questions_query = questions_query.filter_by(category=category)
    
    # Apply search filter if specified
    search = request.args.get('search')
    if search:
        questions_query = questions_query.filter(Question.question.ilike(f'%{search}%'))
    
    questions_list = questions_query.all()
    
    # Shuffle questions for randomness
    random.shuffle(questions_list)
    
    # Format questions for template
    questions = []
    for q in questions_list:
        question_data = {
            'id': q.id,
            'question': q.question,
            'category': q.category,
            'image_filename': q.image_filename,
            'correct_option': q.correct_option
        }
        
        # Add options
        for opt in q.options:
            question_data[f'option_{opt.option_letter}'] = opt.option_text
        
        # Determine image folder (default to 'signs' if not specified)
        question_data['image_folder'] = 'signs'  # Could be made dynamic based on category
        
        questions.append(question_data)
    
    return render_template('quiz.html', questions=questions)


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
