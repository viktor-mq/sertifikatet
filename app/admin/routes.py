import os
import csv
from flask import render_template, request, redirect, url_for, session, current_app, send_file, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import StringIO
from sqlalchemy import text, inspect
from . import admin_bp
from functools import wraps

from .utils import validate_question
from .. import db
from ..models import Question, Option, TrafficSign, QuizImage, User, AdminAuditLog
from ..security import AdminSecurityService

# Blueprint is already created in __init__.py, using the imported one

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not AdminSecurityService.is_admin_required(current_user):
            # Log the failed attempt
            if current_user.is_authenticated:
                AdminSecurityService.log_admin_login_attempt(current_user, success=False)
            flash('Du har ikke tilgang til denne siden', 'error')
            return redirect(url_for('main.index'))
        
        # Log successful admin access
        AdminSecurityService.log_admin_login_attempt(current_user, success=True)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def login():
    # Redirect to main login page
    flash('Logg inn som admin for å få tilgang til administrasjonspanelet', 'info')
    return redirect(url_for('auth.login', next=url_for('admin.admin_dashboard')))

@admin_bp.route('/logout')
def logout():
    # Use the main logout
    return redirect(url_for('auth.logout'))

@admin_bp.route('/dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():

    # Handle search/filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()

    validation_errors = []
    message = None

    # Image upload and metadata
    if request.method == 'POST':
        new_img = request.files.get('image')
        if new_img and new_img.filename:
            folder = request.form.get('folder')
            filename = secure_filename(new_img.filename)
            save_dir = os.path.join(current_app.static_folder, 'images', folder)
            os.makedirs(save_dir, exist_ok=True)
            new_img.save(os.path.join(save_dir, filename))

            if folder == 'signs':
                sign_code = request.form.get('sign_code')
                desc = request.form.get('descriptionSign') or request.form.get('description')
                
                # Check if sign exists
                existing_sign = TrafficSign.query.filter_by(code=sign_code).first()
                if existing_sign:
                    existing_sign.filename = filename
                    existing_sign.description = desc
                else:
                    ts = TrafficSign(code=sign_code, filename=filename, description=desc, name=desc)
                    db.session.add(ts)
            else:
                title = request.form.get('title') or request.form.get('titleCustom')
                desc = request.form.get('descriptionQuiz') or request.form.get('descriptionCustom')
                qi = QuizImage(filename=filename, folder=folder, title=title, description=desc)
                db.session.add(qi)

            db.session.commit()
            message = f'Bildet "{filename}" ble lastet opp i {folder}.'

    # Handle SQL console or question form
    if request.method == 'POST':
        if 'sql_query' in request.form:
            sql_query = request.form['sql_query']
            try:
                # Execute raw SQL for admin console
                result = db.session.execute(text(sql_query))
                db.session.commit()
                
                if sql_query.strip().upper().startswith('SELECT'):
                    results = result.fetchall()
                    message = f"Query executed successfully. Returned {len(results)} rows."
                else:
                    message = "Query executed successfully."
            except Exception as e:
                db.session.rollback()
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
                    # Update existing question
                    q = Question.query.get(question_id)
                    if q:
                        q.question = question_data['question']
                        q.correct_option = question_data['correct_option']
                        q.category = question_data['category']
                        q.image_filename = question_data['image_filename']
                        
                        # Delete existing options
                        Option.query.filter_by(question_id=q.id).delete()
                        
                        # Add new options
                        for letter, opt_text in [('a', question_data['option_a']),
                                             ('b', question_data['option_b']),
                                             ('c', question_data['option_c']),
                                             ('d', question_data['option_d'])]:
                            if opt_text:  # Only add non-empty options
                                db.session.add(Option(
                                    question_id=q.id, 
                                    option_letter=letter, 
                                    option_text=opt_text
                                ))
                else:
                    # Create new question
                    q = Question(
                        question=question_data['question'],
                        correct_option=question_data['correct_option'],
                        category=question_data['category'],
                        image_filename=question_data['image_filename']
                    )
                    db.session.add(q)
                    db.session.flush()  # Get the ID
                    
                    # Add options
                    for letter, opt_text in [('a', question_data['option_a']),
                                         ('b', question_data['option_b']),
                                         ('c', question_data['option_c']),
                                         ('d', question_data['option_d'])]:
                        if opt_text:  # Only add non-empty options
                            db.session.add(Option(
                                question_id=q.id, 
                                option_letter=letter, 
                                option_text=opt_text
                            ))
                
                db.session.commit()
                return redirect(url_for('admin.admin_dashboard'))

    # Fetch questions with options using ORM
    query = Question.query
    
    if search_query:
        query = query.filter(Question.question.ilike(f'%{search_query}%'))
    
    if category_filter:
        query = query.filter(Question.category == category_filter)
    
    all_questions = query.all()

    questions = []
    for q in all_questions:
        # Create a dict of options keyed by label
        opts = {opt.option_letter: opt.option_text for opt in q.options}
        questions.append({
            'id': q.id,
            'question': q.question,
            'category': q.category,
            'image_filename': q.image_filename,
            'option_a': opts.get('a', ''),
            'option_b': opts.get('b', ''),
            'option_c': opts.get('c', ''),
            'option_d': opts.get('d', ''),
            'correct_option': q.correct_option
        })

    # Statistics using ORM
    total = Question.query.count()
    
    # Count by category
    category_counts = db.session.query(
        Question.category, 
        db.func.count(Question.id)
    ).group_by(Question.category).all()
    by_category = dict(category_counts)
    
    # Count with/without images
    with_images = Question.query.filter(
        Question.image_filename.isnot(None), 
        Question.image_filename != ''
    ).count()
    without_images = total - with_images
    
    stats = {
        'total': total, 
        'by_category': by_category, 
        'with_images': with_images, 
        'without_images': without_images
    }

    # Get all unique categories
    categories = [cat[0] for cat in db.session.query(Question.category).distinct().all() if cat[0]]

    # Image list for gallery
    images = []
    
    # Traffic signs
    images_dir = os.path.join(current_app.static_folder, 'images')
    for ts in TrafficSign.query.all():
        # Dynamically find the subfolder under static/images containing this filename
        folder = ''
        for root, dirs, files in os.walk(images_dir):
            if ts.filename in files:
                folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                break
        images.append({
            'id': ts.id,
            'filename': ts.filename,
            'name': ts.description or ts.name,
            'folder': folder
        })

    # Quiz images
    for qi in QuizImage.query.all():
        display = qi.title or qi.description or qi.filename
        images.append({
            'id': qi.id, 
            'filename': qi.filename, 
            'name': display, 
            'folder': qi.folder
        })

    # Remove duplicates: keep unique (folder, filename)
    seen = set()
    unique_images = []
    for img in images:
        key = (img['folder'], img['filename'])
        if key not in seen:
            seen.add(key)
            unique_images.append(img)
    images = unique_images

    # Folders under static/images
    images_dir = os.path.join(current_app.static_folder, 'images')
    folders = []
    if os.path.isdir(images_dir):
        for name in os.listdir(images_dir):
            path = os.path.join(images_dir, name)
            if os.path.isdir(path):
                folders.append(name)

    # Tables for SQL console - get all tables dynamically
    tables = {}
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    
    for tbl in table_names:
        try:
            # Limit to 1000 rows for performance
            result = db.session.execute(text(f"SELECT * FROM {tbl} LIMIT 1000"))
            rows = result.fetchall()
            # Convert rows to dictionaries
            tables[tbl] = [dict(row._mapping) for row in rows]
        except Exception as e:
            print(f"[ADMIN] Feil ved henting av data fra tabell '{tbl}': {e}")
            tables[tbl] = [{"error": str(e)}]

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
@admin_required
def delete_question(question_id):
    
    # Delete question and its options (cascade will handle options)
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
    
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/bulk_delete', methods=['POST'])
@admin_required
def bulk_delete():
    
    ids = request.form.getlist('question_ids')
    
    # Delete questions (cascade will handle options)
    for qid in ids:
        question = Question.query.get(int(qid))
        if question:
            db.session.delete(question)
    
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_questions')
@admin_required
def export_questions():
    
    # Get all questions with their options
    questions = Question.query.all()
    
    # Create CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'category', 'image_filename'])
    
    for q in questions:
        # Get options as dict
        opts = {opt.option_letter: opt.option_text for opt in q.options}
        
        writer.writerow([
            q.id,
            q.question,
            opts.get('a', ''),
            opts.get('b', ''),
            opts.get('c', ''),
            opts.get('d', ''),
            q.correct_option,
            q.category,
            q.image_filename or ''
        ])
    
    output = si.getvalue()
    si.seek(0)
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='questions_export.csv'
    )

# ========================================
# ADMIN USER MANAGEMENT ROUTES
# ========================================

@admin_bp.route('/users')
@admin_required
def manage_users():
    """Admin user management page"""
    
    # Get all users with admin status
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get recent admin audit logs
    recent_logs = AdminSecurityService.get_admin_audit_log(limit=50)
    
    # Get admin statistics
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    
    stats = {
        'total_users': total_users,
        'admin_users': admin_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users
    }
    
    return render_template(
        'admin/manage_users.html',
        users=users,
        recent_logs=recent_logs,
        stats=stats
    )

@admin_bp.route('/users/<int:user_id>/grant_admin', methods=['POST'])
@admin_required
def grant_admin_privileges(user_id):
    """Grant admin privileges to a user"""
    
    target_user = User.query.get_or_404(user_id)
    
    # Use the security service to safely grant admin privileges
    result = AdminSecurityService.grant_admin_privileges(
        target_user=target_user,
        granting_admin=current_user
    )
    
    if result['success']:
        flash(result['message'], 'success')
        if result['warnings']:
            for warning in result['warnings']:
                flash(f"Warning: {warning}", 'warning')
    else:
        flash(result['message'], 'error')
        if result['warnings']:
            for warning in result['warnings']:
                flash(f"Warning: {warning}", 'warning')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/revoke_admin', methods=['POST'])
@admin_required
def revoke_admin_privileges(user_id):
    """Revoke admin privileges from a user"""
    
    target_user = User.query.get_or_404(user_id)
    
    # Prevent self-revocation
    if target_user.id == current_user.id:
        flash('Du kan ikke fjerne dine egne admin-rettigheter', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Use the security service to safely revoke admin privileges
    result = AdminSecurityService.revoke_admin_privileges(
        target_user=target_user,
        revoking_admin=current_user
    )
    
    if result['success']:
        flash(result['message'], 'success')
        if result['warnings']:
            for warning in result['warnings']:
                flash(f"Warning: {warning}", 'warning')
    else:
        flash(result['message'], 'error')
        if result['warnings']:
            for warning in result['warnings']:
                flash(f"Warning: {warning}", 'warning')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/security/audit-log')
@admin_required
def security_audit_log():
    """View detailed security audit log"""
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filter parameters
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user', '')
    
    # Build query
    query = AdminAuditLog.query
    
    if action_filter:
        query = query.filter(AdminAuditLog.action == action_filter)
    
    if user_filter:
        query = query.join(User, AdminAuditLog.target_user_id == User.id)
        query = query.filter(User.username.ilike(f'%{user_filter}%'))
    
    # Paginate results
    logs = query.order_by(AdminAuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique actions for filter dropdown
    actions = db.session.query(AdminAuditLog.action).distinct().all()
    actions = [action[0] for action in actions]
    
    return render_template(
        'admin/security_audit_log.html',
        logs=logs,
        actions=actions,
        action_filter=action_filter,
        user_filter=user_filter
    )
