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
        cursor.execute('SELECT * FROM questions WHERE category = ?', (category,))
    else:
        cursor.execute('SELECT * FROM questions')
    rows = cursor.fetchall()
    conn.close()
    questions = []
    for row in rows:
        questions.append({
            'question': row['question'],
            'a': row['option_a'],
            'b': row['option_b'],
            'c': row['option_c'],
            'd': row['option_d'],
            'correct': row['correct_answer']
        })
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


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['correct_answer']
        category = request.form['category']
        image_filename = request.form['image_filename']

        cursor.execute("""
            INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_answer, category, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (question, option_a, option_b, option_c, option_d, correct_answer, category, image_filename))
        conn.commit()

    cursor.execute("SELECT * FROM traffic_signs")
    images = cursor.fetchall()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
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
        tables[tbl] = cursor.fetchall()
    conn.close()

    return render_template('admin/admin_dashboard.html',
                           images=images,
                           questions=questions,
                           tables=tables)

if __name__ == '__main__':
    app.run(debug=True)
