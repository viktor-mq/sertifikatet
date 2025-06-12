import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import json
import random
import csv
from io import StringIO
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.admin import admin_bp

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.secret_key = 'supersecretkey'  # Kreves for session


def init_db():
    """Initialize the database with tables if they don't exist"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # Create questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            category TEXT,
            image_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create options table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            option_letter TEXT NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
    ''')
    
    # Create traffic_signs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            sign_code TEXT
        )
    ''')
    
    # Create quiz_images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            folder TEXT NOT NULL,
            title TEXT,
            description TEXT
        )
    ''')
    
    # Insert sample traffic signs if table is empty
    cursor.execute("SELECT COUNT(*) FROM traffic_signs")
    if cursor.fetchone()[0] == 0:
        sample_signs = [
            ('speed_limit_50.jpg', 'Fartsgrense 50 km/t', 'Maksimal hastighet 50 km/t'),
            ('stop_sign.jpg', 'Stoppskilt', 'Fullstendig stopp påkrevd'),
            ('yield_sign.jpg', 'Vikeplikt', 'Gi vikeplikt for annen trafikk'),
            ('no_parking.jpg', 'Parkering forbudt', 'Parkering ikke tillatt')
        ]
        cursor.executemany(
            "INSERT INTO traffic_signs (filename, name, description) VALUES (?, ?, ?)",
            sample_signs
        )
    
    conn.commit()
    conn.close()


def load_questions(category=None, search=None):
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT q.*,
               qi.folder AS image_folder,
               GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
        FROM questions q
        LEFT JOIN quiz_images qi ON qi.filename = q.image_filename
        LEFT JOIN options o ON q.id = o.question_id
    """
    
    where_conditions = []
    params = []
    
    if category:
        where_conditions.append("q.category = ?")
        params.append(category)
    
    if search:
        where_conditions.append("q.question LIKE ?")
        params.append(f"%{search}%")
    
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    
    query += " GROUP BY q.id ORDER BY q.id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    questions = []
    for row in rows:
        question_dict = dict(row)
        # Default image_folder to 'signs' if not set
        question_dict['image_folder'] = row['image_folder'] or 'signs'
        # Parse options data
        if row['options_data']:
            options_list = row['options_data'].split('|')
            for opt in options_list:
                if ':' in opt:
                    letter, text = opt.split(':', 1)
                    question_dict[f'option_{letter}'] = text
        # Remove the temporary options_data field
        question_dict.pop('options_data', None)
        questions.append(question_dict)
    conn.close()
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
            if selected == q['correct_option']:
                score += 1
        return render_template('results.html', score=score, total=len(questions))

    questions = load_questions()
    random.shuffle(questions)
    return render_template('quiz.html', questions=questions)


# Error handlers
@app.errorhandler(400)
def handle_bad_request(e):
    app.logger.error(f'Bad Request: {e}')
    # Return a simple page with error message
    return f"<h1>400 Bad Request</h1><p>{e.description if hasattr(e, 'description') else str(e)}</p>", 400

@app.errorhandler(500)
def handle_server_error(e):
    app.logger.error(f'Server Error: {e}', exc_info=True)
    return f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>", 500


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Create static directories if they don't exist
    os.makedirs('static/images/signs', exist_ok=True)
    os.makedirs('static/images/quiz', exist_ok=True)
    os.makedirs('static/images/custom', exist_ok=True)
    
    app.run(debug=True)
