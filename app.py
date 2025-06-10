import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
import json
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Kreves for session


def load_questions(category=None):
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT q.*, 
                   GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
            FROM questions q
            LEFT JOIN options o ON q.id = o.question_id
            WHERE q.category = ?
            GROUP BY q.id
        """, (category,))
    else:
        cursor.execute("""
            SELECT q.*, 
                   GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
            FROM questions q
            LEFT JOIN options o ON q.id = o.question_id
            GROUP BY q.id
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        question_dict = {
            'question': row['question'],
            'correct': row['correct_answer']
        }
        
        # Parse options data
        if row['options_data']:
            options_list = row['options_data'].split('|')
            for opt in options_list:
                letter, text = opt.split(':', 1)
                question_dict[letter] = text
        
        questions.append(question_dict)
    
    return questions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        questions = load_questions()
        score = 0
        for i, q in enumerate(questions):
            selected = request.form.get(f'q{i}')
            if selected == q['correct']:
                score += 1
        return render_template('result.html', score=score, total=len(questions))

    questions = load_questions()
    random.shuffle(questions)
    return render_template('quiz.html', questions=questions)


# Admin login and dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'creative':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/admin_login.html', error='Feil passord.')
    return render_template('admin/admin_login.html')

def dict_from_row(row):
    return {key: row[key] for key in row.keys()}

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        # Check if this is an update (has question_id) or a new question
        question_id = request.form.get('question_id')
        
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['correct_answer']
        category = request.form['category']
        image_filename = request.form['image_filename']

        if question_id:
            # Update existing question
            cursor.execute("""
                UPDATE questions 
                SET question=?, correct_answer=?, category=?, image_filename=?
                WHERE id=?
            """, (question, correct_answer, category, image_filename, question_id))
            
            # Update options for this question
            cursor.execute("DELETE FROM options WHERE question_id=?", (question_id,))
            
            # Insert updated options
            options = [
                (question_id, 'a', option_a),
                (question_id, 'b', option_b),
                (question_id, 'c', option_c),
                (question_id, 'd', option_d)
            ]
            cursor.executemany("INSERT INTO options (question_id, option_letter, option_text) VALUES (?, ?, ?)", options)
            
        else:
            # Insert new question
            cursor.execute("""
                INSERT INTO questions (question, correct_answer, category, image_filename)
                VALUES (?, ?, ?, ?)
            """, (question, correct_answer, category, image_filename))
            
            # Get the ID of the newly inserted question
            new_question_id = cursor.lastrowid
            
            # Insert options for the new question
            options = [
                (new_question_id, 'a', option_a),
                (new_question_id, 'b', option_b),
                (new_question_id, 'c', option_c),
                (new_question_id, 'd', option_d)
            ]
            cursor.executemany("INSERT INTO options (question_id, option_letter, option_text) VALUES (?, ?, ?)", options)
        
        conn.commit()

    # Fetch questions with their options
    cursor.execute("""
        SELECT q.*, 
               GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
        FROM questions q
        LEFT JOIN options o ON q.id = o.question_id
        GROUP BY q.id
    """)
    questions_raw = cursor.fetchall()
    
    # Process questions to include options as separate fields
    questions = []
    for q in questions_raw:
        question_dict = dict_from_row(q)
        
        # Parse options data
        if question_dict['options_data']:
            options_list = question_dict['options_data'].split('|')
            for opt in options_list:
                letter, text = opt.split(':', 1)
                question_dict[f'option_{letter}'] = text
        
        # Remove the temporary options_data field
        question_dict.pop('options_data', None)
        questions.append(question_dict)

    cursor.execute("SELECT * FROM traffic_signs")
    images = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    # Fetch all tables for the Database section
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row['name'] for row in cursor.fetchall()]
    tables = {}
    for tbl in table_names:
        cursor.execute(f"SELECT * FROM {tbl}")
        tables[tbl] = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('admin/admin_dashboard.html',
                           images=images,
                           questions=questions,
                           tables=tables)

if __name__ == '__main__':
    app.run(debug=True)
