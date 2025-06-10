import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import json
import random
import csv
from io import StringIO
from datetime import datetime
import os

app = Flask(__name__)
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
            correct_answer TEXT NOT NULL,
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
               GROUP_CONCAT(o.option_letter || ':' || o.option_text, '|') as options_data
        FROM questions q
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
    conn.close()
    
    questions = []
    for row in rows:
        question_dict = dict(row)
        
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
            if selected == q['correct_answer']:
                score += 1
        return render_template('result.html', score=score, total=len(questions))

    questions = load_questions()
    random.shuffle(questions)
    return render_template('quiz.html', questions=questions)


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


def get_question_statistics():
    """Get statistics about questions"""
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # Total questions
    cursor.execute("SELECT COUNT(*) as total FROM questions")
    total = cursor.fetchone()[0]
    
    # Questions by category
    cursor.execute("SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY count DESC")
    by_category = cursor.fetchall()
    
    # Questions with/without images
    cursor.execute("SELECT COUNT(*) as with_images FROM questions WHERE image_filename IS NOT NULL AND image_filename != ''")
    with_images = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'by_category': by_category,
        'with_images': with_images,
        'without_images': total - with_images
    }


def validate_question(question_data, question_id=None):
    """Validate question data and check for duplicates"""
    errors = []
    
    # Check required fields
    required_fields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    for field in required_fields:
        if not question_data.get(field, '').strip():
            field_name = field.replace('_', ' ').capitalize()
            errors.append(f'{field_name} er påkrevd')
    
    # Validate correct answer
    if question_data.get('correct_answer', '').lower() not in ['a', 'b', 'c', 'd']:
        errors.append('Riktig svar må være a, b, c eller d')
    
    # Check for duplicate question
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    if question_id:
        cursor.execute("SELECT id FROM questions WHERE question = ? AND id != ?", 
                      (question_data.get('question', ''), question_id))
    else:
        cursor.execute("SELECT id FROM questions WHERE question = ?", 
                      (question_data.get('question', ''),))
    
    if cursor.fetchone():
        errors.append('Et spørsmål med samme tekst eksisterer allerede')
    
    conn.close()
    
    return errors


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    validation_errors = []
    message = None

    if request.method == 'POST':
        # Check if this is a SQL query
        if 'sql_query' in request.form:
            sql_query = request.form['sql_query']
            try:
                # Execute SQL query
                cursor.execute(sql_query)
                conn.commit()
                
                # If it's a SELECT query, fetch results
                if sql_query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    message = f"Query executed successfully. Returned {len(results)} rows."
                else:
                    message = "Query executed successfully."
            except Exception as e:
                message = f"SQL Error: {str(e)}"
        
        else:
            # Handle question form submission
            question_id = request.form.get('question_id')
            
            question_data = {
                'question': request.form['question'],
                'option_a': request.form['option_a'],
                'option_b': request.form['option_b'],
                'option_c': request.form['option_c'],
                'option_d': request.form['option_d'],
                'correct_answer': request.form['correct_answer'].lower(),
                'category': request.form['category'] or 'Ukategorisert',
                'image_filename': request.form['image_filename']
            }
            
            # Validate the question
            validation_errors = validate_question(question_data, question_id)
            
            if not validation_errors:
                if question_id:
                    # Update existing question
                    cursor.execute("""
                        UPDATE questions 
                        SET question=?, correct_answer=?, category=?, image_filename=?
                        WHERE id=?
                    """, (question_data['question'], question_data['correct_answer'], 
                          question_data['category'], question_data['image_filename'], question_id))
                    
                    # Update options for this question
                    cursor.execute("DELETE FROM options WHERE question_id=?", (question_id,))
                    
                    # Insert updated options
                    options = [
                        (question_id, 'a', question_data['option_a']),
                        (question_id, 'b', question_data['option_b']),
                        (question_id, 'c', question_data['option_c']),
                        (question_id, 'd', question_data['option_d'])
                    ]
                    cursor.executemany("INSERT INTO options (question_id, option_letter, option_text) VALUES (?, ?, ?)", options)
                    
                else:
                    # Insert new question
                    cursor.execute("""
                        INSERT INTO questions (question, correct_answer, category, image_filename)
                        VALUES (?, ?, ?, ?)
                    """, (question_data['question'], question_data['correct_answer'], 
                          question_data['category'], question_data['image_filename']))
                    
                    # Get the ID of the newly inserted question
                    new_question_id = cursor.lastrowid
                    
                    # Insert options for the new question
                    options = [
                        (new_question_id, 'a', question_data['option_a']),
                        (new_question_id, 'b', question_data['option_b']),
                        (new_question_id, 'c', question_data['option_c']),
                        (new_question_id, 'd', question_data['option_d'])
                    ]
                    cursor.executemany("INSERT INTO options (question_id, option_letter, option_text) VALUES (?, ?, ?)", options)
                
                conn.commit()
                return redirect(url_for('admin_dashboard'))

    # Load questions with filters
    questions = load_questions(category=category_filter, search=search_query)

    # Get all categories for filter dropdown
    cursor.execute("SELECT DISTINCT category FROM questions WHERE category IS NOT NULL AND category != '' ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]

    # Get traffic signs
    cursor.execute("SELECT * FROM traffic_signs")
    images = [dict(row) for row in cursor.fetchall()]

    # Get statistics
    stats = get_question_statistics()

    # Fetch all tables for the Database section
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row['name'] for row in cursor.fetchall()]
    tables = {}
    
    for tbl in table_names:
        try:
            cursor.execute(f"SELECT * FROM {tbl} LIMIT 100")  # Limit for performance
            tables[tbl] = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            tables[tbl] = []
    
    conn.close()

    return render_template('admin/admin_dashboard.html',
                           images=images,
                           questions=questions,
                           tables=tables,
                           categories=categories,
                           search_query=search_query,
                           category_filter=category_filter,
                           stats=stats,
                           validation_errors=validation_errors,
                           message=message)


@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    try:
        # Delete options first (foreign key constraint)
        cursor.execute("DELETE FROM options WHERE question_id = ?", (question_id,))
        
        # Delete the question
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error deleting question: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/bulk_delete', methods=['POST'])
def bulk_delete():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    
    question_ids = request.form.getlist('question_ids')
    
    if question_ids:
        conn = sqlite3.connect('questions.db')
        cursor = conn.cursor()
        
        try:
            # Delete options first
            for q_id in question_ids:
                cursor.execute("DELETE FROM options WHERE question_id = ?", (q_id,))
            
            # Delete questions
            placeholders = ','.join(['?' for _ in question_ids])
            cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", question_ids)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error in bulk delete: {e}")
        finally:
            conn.close()
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/export_questions')
def export_questions():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    
    questions = load_questions()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Question', 'Option A', 'Option B', 'Option C', 'Option D', 
                     'Correct Answer', 'Category', 'Image Filename'])
    
    # Write data
    for q in questions:
        writer.writerow([
            q.get('id', ''),
            q.get('question', ''),
            q.get('option_a', ''),
            q.get('option_b', ''),
            q.get('option_c', ''),
            q.get('option_d', ''),
            q.get('correct_answer', ''),
            q.get('category', ''),
            q.get('image_filename', '')
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=questions_export.csv'
    
    return response


@app.route('/admin/preview_question', methods=['POST'])
def preview_question():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    question_data = {
        'question': request.json.get('question', ''),
        'option_a': request.json.get('option_a', ''),
        'option_b': request.json.get('option_b', ''),
        'option_c': request.json.get('option_c', ''),
        'option_d': request.json.get('option_d', ''),
        'correct_answer': request.json.get('correct_answer', ''),
        'image_filename': request.json.get('image_filename', '')
    }
    
    return jsonify(question_data)


@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Create static directories if they don't exist
    os.makedirs('static/images/signs', exist_ok=True)
    
    app.run(debug=True)