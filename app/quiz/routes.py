from flask import render_template, request, redirect, url_for, session, jsonify, flash
from . import quiz_bp
import sqlite3
import random
import json
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn

@quiz_bp.route('/')
def quiz_home():
    """Display quiz selection page"""
    return render_template('quiz/quiz_home.html')

@quiz_bp.route('/practice')
def practice():
    """Practice mode - random questions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get categories for filter
    cursor.execute("SELECT DISTINCT category FROM questions WHERE category IS NOT NULL")
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    return render_template('quiz/practice.html', categories=categories)

@quiz_bp.route('/practice/start', methods=['POST'])
def start_practice():
    """Start a practice session"""
    category = request.form.get('category', 'all')
    num_questions = int(request.form.get('num_questions', 20))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get questions based on category
    if category == 'all':
        cursor.execute("""
            SELECT q.*, GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
            FROM questions q
            LEFT JOIN options o ON q.id = o.question_id
            GROUP BY q.id
        """)
    else:
        cursor.execute("""
            SELECT q.*, GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
            FROM questions q
            LEFT JOIN options o ON q.id = o.question_id
            WHERE q.category = ?
            GROUP BY q.id
        """, (category,))
    
    questions = []
    for row in cursor.fetchall():
        question = dict(row)
        # Parse options
        if row['options_data']:
            options = {}
            for opt in row['options_data'].split('|'):
                if ':' in opt:
                    letter, text = opt.split(':', 1)
                    options[f'option_{letter}'] = text
            question.update(options)
        questions.append(question)
    
    conn.close()
    
    # Shuffle and limit questions
    random.shuffle(questions)
    questions = questions[:num_questions]
    
    # Store in session
    session['practice_questions'] = questions
    session['current_question'] = 0
    session['practice_answers'] = {}
    session['practice_score'] = 0
    
    return redirect(url_for('quiz.practice_question'))

@quiz_bp.route('/practice/question')
def practice_question():
    """Display current practice question"""
    if 'practice_questions' not in session:
        return redirect(url_for('quiz.practice'))
    
    questions = session['practice_questions']
    current = session['current_question']
    
    if current >= len(questions):
        return redirect(url_for('quiz.practice_results'))
    
    question = questions[current]
    progress = ((current + 1) / len(questions)) * 100
    
    return render_template('quiz/practice_question.html', 
                           question=question, 
                           current=current + 1,
                           total=len(questions),
                           progress=progress)

@quiz_bp.route('/practice/answer', methods=['POST'])
def practice_answer():
    """Handle practice answer submission"""
    if 'practice_questions' not in session:
        return jsonify({'error': 'No active session'}), 400
    
    answer = request.json.get('answer')
    current = session['current_question']
    questions = session['practice_questions']
    
    if current >= len(questions):
        return jsonify({'error': 'Invalid question index'}), 400
    
    question = questions[current]
    correct = answer == question['correct_option']
    
    # Store answer
    session['practice_answers'][str(question['id'])] = {
        'answer': answer,
        'correct': correct,
        'correct_answer': question['correct_option']
    }
    
    if correct:
        session['practice_score'] += 1
    
    # Move to next question
    session['current_question'] += 1
    session.modified = True
    
    return jsonify({
        'correct': correct,
        'correct_answer': question['correct_option'],
        'explanation': f"Riktig svar er {question['correct_option'].upper()}: {question.get(f'option_{question['correct_option']}', '')}"
    })

@quiz_bp.route('/practice/results')
def practice_results():
    """Display practice results"""
    if 'practice_questions' not in session:
        return redirect(url_for('quiz.practice'))
    
    questions = session['practice_questions']
    answers = session['practice_answers']
    score = session['practice_score']
    
    # Calculate statistics
    total = len(questions)
    percentage = (score / total * 100) if total > 0 else 0
    
    # Category breakdown
    category_stats = {}
    for q in questions:
        cat = q.get('category', 'Ukategorisert')
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'correct': 0}
        category_stats[cat]['total'] += 1
        
        answer_data = answers.get(str(q['id']), {})
        if answer_data.get('correct'):
            category_stats[cat]['correct'] += 1
    
    # Clear session
    session.pop('practice_questions', None)
    session.pop('current_question', None)
    session.pop('practice_answers', None)
    session.pop('practice_score', None)
    
    return render_template('quiz/practice_results.html',
                           score=score,
                           total=total,
                           percentage=percentage,
                           category_stats=category_stats)

@quiz_bp.route('/exam')
def exam():
    """Exam mode - simulated test"""
    return render_template('quiz/exam.html')

@quiz_bp.route('/exam/start', methods=['POST'])
def start_exam():
    """Start an exam session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get 45 questions (standard exam format)
    # Should follow official distribution of categories
    cursor.execute("""
        SELECT q.*, GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
        FROM questions q
        LEFT JOIN options o ON q.id = o.question_id
        GROUP BY q.id
        ORDER BY RANDOM()
        LIMIT 45
    """)
    
    questions = []
    for row in cursor.fetchall():
        question = dict(row)
        # Parse options
        if row['options_data']:
            options = {}
            for opt in row['options_data'].split('|'):
                if ':' in opt:
                    letter, text = opt.split(':', 1)
                    options[f'option_{letter}'] = text
            question.update(options)
        questions.append(question)
    
    conn.close()
    
    # Store in session
    session['exam_questions'] = questions
    session['exam_current'] = 0
    session['exam_answers'] = {}
    session['exam_start_time'] = datetime.now().isoformat()
    
    return redirect(url_for('quiz.exam_question'))

@quiz_bp.route('/exam/question')
def exam_question():
    """Display current exam question"""
    if 'exam_questions' not in session:
        return redirect(url_for('quiz.exam'))
    
    questions = session['exam_questions']
    current = session['exam_current']
    
    if current >= len(questions):
        return redirect(url_for('quiz.exam_submit'))
    
    question = questions[current]
    
    # Calculate time remaining (45 minutes standard)
    start_time = datetime.fromisoformat(session['exam_start_time'])
    elapsed = (datetime.now() - start_time).total_seconds()
    time_remaining = max(0, 45 * 60 - elapsed)  # 45 minutes in seconds
    
    return render_template('quiz/exam_question.html',
                           question=question,
                           current=current + 1,
                           total=len(questions),
                           time_remaining=int(time_remaining),
                           answers=session.get('exam_answers', {}))

@quiz_bp.route('/exam/answer', methods=['POST'])
def exam_answer():
    """Handle exam answer submission"""
    if 'exam_questions' not in session:
        return jsonify({'error': 'No active exam'}), 400
    
    question_id = request.json.get('question_id')
    answer = request.json.get('answer')
    
    # Store answer
    session['exam_answers'][str(question_id)] = answer
    session.modified = True
    
    return jsonify({'success': True})

@quiz_bp.route('/exam/navigate', methods=['POST'])
def exam_navigate():
    """Navigate to specific question in exam"""
    if 'exam_questions' not in session:
        return jsonify({'error': 'No active exam'}), 400
    
    question_num = request.json.get('question_num', 0)
    session['exam_current'] = question_num
    session.modified = True
    
    return jsonify({'success': True})

@quiz_bp.route('/exam/submit', methods=['GET', 'POST'])
def exam_submit():
    """Submit exam and show results"""
    if 'exam_questions' not in session:
        return redirect(url_for('quiz.exam'))
    
    questions = session['exam_questions']
    answers = session['exam_answers']
    
    # Calculate score
    correct = 0
    for q in questions:
        if answers.get(str(q['id'])) == q['correct_option']:
            correct += 1
    
    # Calculate statistics
    total = len(questions)
    percentage = (correct / total * 100) if total > 0 else 0
    passed = percentage >= 85  # 85% is typical passing grade
    
    # Calculate time taken
    start_time = datetime.fromisoformat(session['exam_start_time'])
    time_taken = int((datetime.now() - start_time).total_seconds())
    
    # Clear session
    session.pop('exam_questions', None)
    session.pop('exam_current', None)
    session.pop('exam_answers', None)
    session.pop('exam_start_time', None)
    
    return render_template('quiz/exam_results.html',
                           score=correct,
                           total=total,
                           percentage=percentage,
                           passed=passed,
                           time_taken=time_taken)

@quiz_bp.route('/review/<int:question_id>')
def review_question(question_id):
    """Review a specific question with explanation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT q.*, GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
        FROM questions q
        LEFT JOIN options o ON q.id = o.question_id
        WHERE q.id = ?
        GROUP BY q.id
    """, (question_id,))
    
    row = cursor.fetchone()
    if not row:
        flash('Spørsmål ikke funnet', 'error')
        return redirect(url_for('quiz.quiz_home'))
    
    question = dict(row)
    # Parse options
    if row['options_data']:
        options = {}
        for opt in row['options_data'].split('|'):
            if ':' in opt:
                letter, text = opt.split(':', 1)
                options[f'option_{letter}'] = text
        question.update(options)
    
    conn.close()
    
    return render_template('quiz/review_question.html', question=question)
