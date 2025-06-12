

import os
import sqlite3
import csv
from flask import render_template, request, redirect, url_for, session, current_app, send_file, flash, jsonify
from werkzeug.utils import secure_filename
from io import StringIO
from . import admin_bp

from .utils import validate_question

# Blueprint is already created in __init__.py, using the imported one

def get_db_connection():
    db_path = current_app.config.get('DATABASE_PATH') or os.path.join(current_app.root_path, 'questions.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@admin_bp.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        # Use ADMIN_PASSWORD from config or default 'creative'
        if password and password == current_app.config.get('ADMIN_PASSWORD', 'creative'):
            session['admin'] = True
            return redirect(url_for('admin.admin_dashboard'))
        else:
            error = 'Feil passord'
    return render_template('admin/admin_login.html', error=error)

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle search/filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()

    validation_errors = []
    message = None

    # Image upload and metadata
    if request.method == 'POST':
        # Image upload form field named 'image'
        new_img = request.files.get('image')
        if new_img and new_img.filename:
            folder = request.form.get('folder')
            filename = secure_filename(new_img.filename)
            save_dir = os.path.join(current_app.static_folder, 'images', folder)
            os.makedirs(save_dir, exist_ok=True)
            new_img.save(os.path.join(save_dir, filename))

            if folder == 'signs':
                sign_code = request.form.get('sign_code')
                # name or description field:
                desc = request.form.get('descriptionSign') or request.form.get('description')
                cursor.execute(
                    "INSERT OR REPLACE INTO traffic_signs (sign_code, filename, description) VALUES (?, ?, ?)",
                    (sign_code, filename, desc)
                )
            else:
                title = request.form.get('title') or request.form.get('titleCustom')
                desc  = request.form.get('descriptionQuiz') or request.form.get('descriptionCustom')
                cursor.execute(
                    "INSERT INTO quiz_images (filename, folder, title, description) VALUES (?, ?, ?, ?)",
                    (filename, folder, title, desc)
                )
            conn.commit()
            message = f'Bildet "{filename}" ble lastet opp i {folder}.'

    # Handle SQL console or question form
    if request.method == 'POST':
        if 'sql_query' in request.form:
            sql_query = request.form['sql_query']
            try:
                cursor.execute(sql_query)
                conn.commit()
                if sql_query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    message = f"Query executed successfully. Returned {len(results)} rows."
                else:
                    message = "Query executed successfully."
            except Exception as e:
                message = f"SQL Error: {str(e)}"
        else:
            # Handle question add/edit
            question_id = request.form.get('question_id')
            question_data = {
                'question': request.form.get('question'),
                'option_a': request.form.get('option_a'),
                'option_b': request.form.get('option_b'),
                'option_c': request.form.get('option_c'),
                'option_d': request.form.get('option_d'),
                'correct_option': request.form.get('correct_option', '').lower(),
                'category': request.form.get('category') or 'Ukategorisert',
                'image_filename': request.form.get('image_filename')
            }
            validation_errors = validate_question(question_data, question_id)
            if not validation_errors:
                if question_id:
                    # Update question
                    cursor.execute("""
                        UPDATE questions 
                        SET question=?, correct_option=?, category=?, image_filename=?
                        WHERE id=?
                    """, (question_data['question'], question_data['correct_option'], 
                          question_data['category'], question_data['image_filename'], question_id))
                    # Update options: delete and insert
                    cursor.execute("DELETE FROM options WHERE question_id=?", (question_id,))
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
                        INSERT INTO questions (question, correct_option, category, image_filename)
                        VALUES (?, ?, ?, ?)
                    """, (question_data['question'], question_data['correct_option'], 
                          question_data['category'], question_data['image_filename']))
                    new_qid = cursor.lastrowid
                    options = [
                        (new_qid, 'a', question_data['option_a']),
                        (new_qid, 'b', question_data['option_b']),
                        (new_qid, 'c', question_data['option_c']),
                        (new_qid, 'd', question_data['option_d'])
                    ]
                    cursor.executemany("INSERT INTO options (question_id, option_letter, option_text) VALUES (?, ?, ?)", options)
                conn.commit()
                return redirect(url_for('admin.admin_dashboard'))

    # Fetch questions with options
    query = "SELECT q.id, q.question, q.category, q.image_filename, q.correct_option FROM questions q"
    params = []
    if search_query:
        query += " WHERE q.question LIKE ?"
        params.append(f'%{search_query}%')
    if category_filter:
        if 'WHERE' in query:
            query += " AND q.category = ?"
        else:
            query += " WHERE q.category = ?"
        params.append(category_filter)
    cursor.execute(query, params)
    questions = []
    for row in cursor.fetchall():
        qid = row['id']
        # Fetch options
        cursor.execute("SELECT option_letter, option_text FROM options WHERE question_id=? ORDER BY option_letter", (qid,))
        opts = {r['option_letter']: r['option_text'] for r in cursor.fetchall()}
        questions.append({
            'id': qid,
            'question': row['question'],
            'category': row['category'],
            'image_filename': row['image_filename'],
            'option_a': opts.get('a',''),
            'option_b': opts.get('b',''),
            'option_c': opts.get('c',''),
            'option_d': opts.get('d',''),
            'correct_option': row['correct_option']
        })

    # Stats
    cursor.execute("SELECT COUNT(*) AS total FROM questions")
    total = cursor.fetchone()['total']
    cursor.execute("SELECT category, COUNT(*) AS cnt FROM questions GROUP BY category")
    by_cat = {r['category']: r['cnt'] for r in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) AS cnt FROM questions WHERE image_filename IS NOT NULL AND image_filename!=''")
    with_images = cursor.fetchone()['cnt']
    without_images = total - with_images
    stats = {
        'total': total,
        'by_category': by_cat,
        'with_images': with_images,
        'without_images': without_images
    }

    # Categories list
    cursor.execute("SELECT DISTINCT category FROM questions")
    categories = [r['category'] for r in cursor.fetchall() if r['category']]

    # Image list for gallery: traffic_signs and quiz_images
    images = []
    # traffic_signs
    cursor.execute("SELECT id, filename, description FROM traffic_signs")
    for r in cursor.fetchall():
        images.append({'id': r['id'], 'filename': r['filename'], 'name': r['description'], 'folder': 'signs'})
    # quiz_images
    cursor.execute("SELECT id, filename, folder, title, description FROM quiz_images")
    for r in cursor.fetchall():
        display = r['title'] or r['description'] or r['filename']
        images.append({'id': r['id'], 'filename': r['filename'], 'name': display, 'folder': r['folder']})

    # Folders under static/images
    images_dir = os.path.join(current_app.static_folder, 'images')
    folders = []
    if os.path.isdir(images_dir):
        for name in os.listdir(images_dir):
            path = os.path.join(images_dir, name)
            if os.path.isdir(path):
                folders.append(name)

    # Tables for SQL console
    tables = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tbl_names = [r['name'] for r in cursor.fetchall()]
    for tbl in tbl_names:
        try:
            cursor.execute(f"SELECT * FROM {tbl} LIMIT 1000")
            rows = cursor.fetchall()
            # Convert Row to dict for template
            tables[tbl] = [dict(row) for row in rows]
        except Exception:
            tables[tbl] = []

    conn.close()

    return render_template(
        'admin/admin_dashboard.html',
        questions=questions,
        stats=stats,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
        validation_errors=validation_errors,
        images=images,
        folders=folders,
        tables=tables,
        message=message
    )

@admin_bp.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM options WHERE question_id=?", (question_id,))
    cursor.execute("DELETE FROM questions WHERE id=?", (question_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/bulk_delete', methods=['POST'])
def bulk_delete():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
    ids = request.form.getlist('question_ids')
    conn = get_db_connection()
    cursor = conn.cursor()
    for qid in ids:
        cursor.execute("DELETE FROM options WHERE question_id=?", (qid,))
        cursor.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_questions')
def export_questions():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, correct_option, category, image_filename FROM questions")
    questions = cursor.fetchall()
    # Gather options
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','question','option_a','option_b','option_c','option_d','correct_option','category','image_filename'])
    for row in questions:
        qid = row['id']
        cursor.execute("SELECT option_letter, option_text FROM options WHERE question_id=? ORDER BY option_letter", (qid,))
        opts = {r['option_letter']: r['option_text'] for r in cursor.fetchall()}
        writer.writerow([
            qid,
            row['question'],
            opts.get('a',''),
            opts.get('b',''),
            opts.get('c',''),
            opts.get('d',''),
            row['correct_option'],
            row['category'],
            row['image_filename']
        ])
    output = si.getvalue()
    conn.close()
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='questions_export.csv'
    )