import os
import csv
from flask import render_template, request, redirect, url_for, session, current_app, send_file, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import StringIO, BytesIO
from sqlalchemy import text, inspect
from . import admin_bp
from functools import wraps

from .utils import validate_question
from .. import db
from ..models import Question, Option, TrafficSign, QuizImage, User, AdminAuditLog, AdminReport, UserFeedback, QuizSession, QuizResponse
from ..marketing_models import MarketingEmail, MarketingTemplate, MarketingEmailLog
from ..marketing_service import MarketingEmailService
from ..security.admin_security import AdminSecurityService
import json
from datetime import datetime, timedelta

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
    try:
        for ts in TrafficSign.query.all():
            # Dynamically find the subfolder under static/images containing this filename
            folder = ''
            if ts.filename:
                for root, dirs, files in os.walk(images_dir):
                    if ts.filename in files:
                        folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                        break
                images.append({
                    'id': ts.id,
                    'filename': ts.filename,
                    'name': ts.description or getattr(ts, 'name', '') or ts.filename,
                    'folder': folder
                })
    except Exception as e:
        print(f"[ADMIN] Error processing traffic signs: {e}")

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

    # Get data for Reports & Security section
    try:
        reports_stats = {
            'total': AdminReport.query.count(),
            'new': AdminReport.query.filter_by(status='new').count(),
            'in_progress': AdminReport.query.filter_by(status='in_progress').count(),
            'critical': AdminReport.query.filter_by(priority='critical', status='new').count(),
            'high': AdminReport.query.filter_by(priority='high', status='new').count()
        }
    except Exception as e:
        print(f"[ADMIN] Error fetching reports stats: {e}")
        reports_stats = {'total': 0, 'new': 0, 'in_progress': 0, 'critical': 0, 'high': 0}
    
    # Get recent security alerts
    try:
        recent_security_alerts = AdminReport.query.filter(
            AdminReport.report_type.in_(['security_alert', 'suspicious_activity', 'admin_change']),
            AdminReport.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(AdminReport.created_at.desc()).limit(10).all()
    except Exception as e:
        print(f"[ADMIN] Error fetching security alerts: {e}")
        recent_security_alerts = []
    
    # Get unresolved user feedback
    try:
        user_feedback = UserFeedback.query.filter_by(status='new').order_by(
            UserFeedback.created_at.desc()
        ).limit(10).all()
    except Exception as e:
        print(f"[ADMIN] Error fetching user feedback: {e}")
        user_feedback = []
    
    # Get recent reports for display
    try:
        recent_reports = AdminReport.query.order_by(AdminReport.created_at.desc()).limit(20).all()
    except Exception as e:
        print(f"[ADMIN] Error fetching recent reports: {e}")
        recent_reports = []
    
    # Get data for Manage Users section
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        recent_logs = AdminSecurityService.get_admin_audit_log(limit=50)
    except Exception as e:
        print(f"[ADMIN] Error fetching users data: {e}")
        users = []
        recent_logs = []
    
    try:
        user_stats = {
            'total_users': User.query.count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'inactive_users': User.query.count() - User.query.filter_by(is_active=True).count()
        }
    except Exception as e:
        print(f"[ADMIN] Error fetching user stats: {e}")
        user_stats = {'total_users': 0, 'admin_users': 0, 'active_users': 0, 'inactive_users': 0}
    
    # Get data for Audit Log section
    try:
        audit_logs = AdminSecurityService.get_admin_audit_log(limit=100)
        audit_actions = db.session.query(AdminAuditLog.action).distinct().all()
        audit_actions = [action[0] for action in audit_actions]
    except Exception as e:
        print(f"[ADMIN] Error fetching audit log data: {e}")
        audit_logs = []
        audit_actions = []

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
        message=message,
        # Reports & Security data
        reports_stats=reports_stats,
        recent_security_alerts=recent_security_alerts,
        user_feedback=user_feedback,
        reports=recent_reports,
        report_type_filter='',
        status_filter='',
        priority_filter='',
        # Manage Users data
        users=users,
        recent_logs=recent_logs,
        user_stats=user_stats,
        # Audit Log data
        logs=audit_logs,
        actions=audit_actions,
        action_filter='',
        user_filter=''
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

@admin_bp.route('/import_questions', methods=['POST'])
@admin_required
def import_questions():
    """Import questions from CSV file"""
    
    if 'csv_file' not in request.files:
        flash('Ingen fil ble lastet opp', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('Ingen fil valgt', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    if not file.filename.lower().endswith('.csv'):
        flash('Filen må være en CSV-fil (.csv)', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    overwrite_existing = request.form.get('overwrite_existing') == '1'
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Validate CSV headers
        expected_headers = ['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'category', 'image_filename']
        if not all(header in csv_reader.fieldnames for header in expected_headers):
            flash(f'CSV-filen må inneholde følgende kolonner: {", ".join(expected_headers)}', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        imported_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
            try:
                # Validate required fields
                if not row.get('question', '').strip():
                    errors.append(f'Rad {row_num}: Spørsmål er påkrevd')
                    error_count += 1
                    continue
                
                if not row.get('correct_option', '').strip().lower() in ['a', 'b', 'c', 'd']:
                    errors.append(f'Rad {row_num}: Riktig svar må være a, b, c eller d')
                    error_count += 1
                    continue
                
                # Check if question exists (if ID is provided)
                question_id = row.get('id', '').strip()
                existing_question = None
                if question_id and question_id.isdigit():
                    existing_question = Question.query.get(int(question_id))
                
                if existing_question and not overwrite_existing:
                    errors.append(f'Rad {row_num}: Spørsmål med ID {question_id} eksisterer allerede (bruk overskriv-alternativet for å oppdatere)')
                    error_count += 1
                    continue
                
                # Create or update question
                if existing_question and overwrite_existing:
                    # Update existing question
                    question = existing_question
                    updated_count += 1
                else:
                    # Create new question
                    question = Question()
                    imported_count += 1
                
                # Set question data
                question.question = row['question'].strip()
                question.correct_option = row['correct_option'].strip().lower()
                question.category = row.get('category', '').strip() or 'Ukategoriseret'
                question.image_filename = row.get('image_filename', '').strip() or None
                
                # Add new question to session if it's new
                if not existing_question:
                    db.session.add(question)
                    db.session.flush()  # Get the ID
                
                # Delete existing options if updating
                if existing_question:
                    Option.query.filter_by(question_id=question.id).delete()
                
                # Add options
                for letter, option_key in [('a', 'option_a'), ('b', 'option_b'), ('c', 'option_c'), ('d', 'option_d')]:
                    option_text = row.get(option_key, '').strip()
                    if option_text:
                        option = Option(
                            question_id=question.id,
                            option_letter=letter,
                            option_text=option_text
                        )
                        db.session.add(option)
                
            except Exception as e:
                errors.append(f'Rad {row_num}: {str(e)}')
                error_count += 1
                continue
        
        # Commit changes
        db.session.commit()
        
        # Create success message
        success_parts = []
        if imported_count > 0:
            success_parts.append(f'{imported_count} nye spørsmål importert')
        if updated_count > 0:
            success_parts.append(f'{updated_count} spørsmål oppdatert')
        
        if success_parts:
            flash(' og '.join(success_parts) + '!', 'success')
        
        if error_count > 0:
            flash(f'{error_count} feil oppstod under import. Se detaljene nedenfor.', 'warning')
            for error in errors[:10]:  # Show max 10 errors
                flash(error, 'error')
            if len(errors) > 10:
                flash(f'... og {len(errors) - 10} flere feil', 'error')
        
        # Log the import action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='questions_import',
            additional_info=json.dumps({
                'filename': file.filename,
                'imported': imported_count,
                'updated': updated_count,
                'errors': error_count,
                'overwrite_mode': overwrite_existing
            })
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Feil ved lesing av CSV-fil: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_questions')
@admin_required
def export_questions():
    """Export all questions to CSV file"""
    
    # Get all questions with their options
    questions = Question.query.all()
    
    # Create CSV in memory using BytesIO
    output = BytesIO()
    
    # Create a text wrapper for CSV writing
    text_stream = StringIO()
    writer = csv.writer(text_stream)
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
            q.category or 'Ukategoriseret',
            q.image_filename or ''
        ])
    
    # Convert string to bytes and write to BytesIO
    csv_content = text_stream.getvalue()
    output.write(csv_content.encode('utf-8-sig'))  # utf-8-sig adds BOM for Excel compatibility
    output.seek(0)
    
    # Log the export action
    AdminSecurityService.log_admin_action(
        admin_user=current_user,
        action='questions_export',
        additional_info=json.dumps({
            'question_count': len(questions)
        })
    )
    
    return send_file(
        output,
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

@admin_bp.route('/reports')
@admin_required
def reports():
    """View all admin reports - security critical page"""
    
    # Get filter parameters
    report_type_filter = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = AdminReport.query
    
    if report_type_filter:
        query = query.filter(AdminReport.report_type == report_type_filter)
    
    if status_filter:
        query = query.filter(AdminReport.status == status_filter)
    
    if priority_filter:
        query = query.filter(AdminReport.priority == priority_filter)
    
    # Order by priority and date
    priority_order = db.case(
        (AdminReport.priority == 'critical', 1),
        (AdminReport.priority == 'high', 2),
        (AdminReport.priority == 'medium', 3),
        (AdminReport.priority == 'low', 4),
        else_=5
    )
    
    reports = query.order_by(priority_order, AdminReport.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get counts for dashboard
    stats = {
        'total': AdminReport.query.count(),
        'new': AdminReport.query.filter_by(status='new').count(),
        'in_progress': AdminReport.query.filter_by(status='in_progress').count(),
        'critical': AdminReport.query.filter_by(priority='critical', status='new').count(),
        'high': AdminReport.query.filter_by(priority='high', status='new').count()
    }
    
    # Get recent security alerts
    recent_security_alerts = AdminReport.query.filter(
        AdminReport.report_type.in_(['security_alert', 'suspicious_activity', 'admin_change']),
        AdminReport.created_at >= datetime.now() - timedelta(days=7)
    ).order_by(AdminReport.created_at.desc()).limit(10).all()
    
    # Get unresolved user feedback
    user_feedback = UserFeedback.query.filter_by(status='new').order_by(
        UserFeedback.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/reports.html',
        reports=reports,
        stats=stats,
        recent_security_alerts=recent_security_alerts,
        user_feedback=user_feedback,
        report_type_filter=report_type_filter,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@admin_bp.route('/reports/<int:report_id>')
@admin_required
def view_report(report_id):
    """View detailed report"""
    
    report = AdminReport.query.get_or_404(report_id)
    
    # Parse metadata if exists
    metadata = {}
    if report.metadata_json:
        try:
            metadata = json.loads(report.metadata_json)
        except:
            metadata = {'raw': report.metadata_json}
    
    return render_template(
        'admin/view_report.html',
        report=report,
        metadata=metadata
    )

@admin_bp.route('/reports/<int:report_id>/update', methods=['POST'])
@admin_required
def update_report(report_id):
    """Update report status or assignment"""
    
    report = AdminReport.query.get_or_404(report_id)
    
    action = request.form.get('action')
    
    if action == 'assign':
        report.assigned_to_user_id = current_user.id
        report.status = 'in_progress'
        flash('Report assigned to you', 'success')
    
    elif action == 'resolve':
        report.resolved_by_user_id = current_user.id
        report.resolved_at = datetime.now()
        report.status = 'resolved'
        report.resolution_notes = request.form.get('resolution_notes', '')
        flash('Report marked as resolved', 'success')
    
    elif action == 'change_priority':
        new_priority = request.form.get('priority')
        if new_priority in ['low', 'medium', 'high', 'critical']:
            report.priority = new_priority
            flash(f'Priority changed to {new_priority}', 'success')
    
    elif action == 'archive':
        report.status = 'archived'
        flash('Report archived', 'success')
    
    db.session.commit()
    
    # Log the action
    AdminSecurityService.log_admin_action(
        admin_user=current_user,
        action=f'report_{action}',
        target_user_id=report.affected_user_id,
        additional_info=json.dumps({
            'report_id': report_id,
            'report_type': report.report_type,
            'action': action
        })
    )
    
    return redirect(url_for('admin.view_report', report_id=report_id))

@admin_bp.route('/reports/create-from-feedback/<int:feedback_id>', methods=['POST'])
@admin_required
def create_report_from_feedback(feedback_id):
    """Convert user feedback to admin report"""
    
    feedback = UserFeedback.query.get_or_404(feedback_id)
    
    # Create admin report from feedback
    report = AdminReport(
        report_type='user_feedback',
        priority='medium' if feedback.feedback_type != 'bug' else 'high',
        title=feedback.subject or f'User Feedback: {feedback.feedback_type}',
        description=feedback.message,
        reported_by_user_id=feedback.user_id,
        created_at=feedback.created_at,
        metadata_json=json.dumps({
            'original_feedback_id': feedback.id,
            'feedback_type': feedback.feedback_type
        })
    )
    
    db.session.add(report)
    
    # Update feedback status
    feedback.status = 'in-progress'
    
    db.session.commit()
    
    flash('Report created from user feedback', 'success')
    return redirect(url_for('admin.view_report', report_id=report.id))

# ========================================
# ML SETTINGS ROUTES
# ========================================

@admin_bp.route('/test')
@admin_required
def test_route():
    """Simple test route to verify admin routes are working"""
    return "ML Settings route is working!"

@admin_bp.route('/ml-settings')
@admin_required
def ml_settings():
    """Machine Learning settings and monitoring dashboard"""
    try:
        # Try to import ML modules
        try:
            from ..ml.service import ml_service
            from ..ml.models import UserSkillProfile, QuestionDifficultyProfile, AdaptiveQuizSession, LearningAnalytics, MLModel, EnhancedQuizResponse
            ml_available = True
        except ImportError as e:
            flash(f'ML modules not available: {str(e)}', 'warning')
            ml_available = False
            
        if not ml_available:
            # Return a basic page if ML is not available
            return render_template('admin/ml_settings.html',
                                 ml_status={'ml_enabled': False, 'error': 'ML modules not available'},
                                 stats={'total_users_with_profiles': 0, 'total_skill_profiles': 0, 'questions_with_difficulty_profiles': 0, 'adaptive_sessions_count': 0, 'learning_analytics_entries': 0, 'enhanced_responses': 0, 'ml_models': 0, 'active_ml_models': 0},
                                 top_performers=[],
                                 struggling_users=[],
                                 ml_models=[],
                                 recent_sessions=[],
                                 category_stats=[])
        
        # Get ML status and statistics
        ml_status = ml_service.get_ml_status()
        
        # Get comprehensive statistics
        stats = {
            'total_users_with_profiles': UserSkillProfile.query.distinct(UserSkillProfile.user_id).count() if ml_available else 0,
            'total_skill_profiles': UserSkillProfile.query.count() if ml_available else 0,
            'questions_with_difficulty_profiles': QuestionDifficultyProfile.query.count() if ml_available else 0,
            'adaptive_sessions_count': AdaptiveQuizSession.query.count() if ml_available else 0,
            'learning_analytics_entries': LearningAnalytics.query.count() if ml_available else 0,
            'enhanced_responses': EnhancedQuizResponse.query.count() if ml_available else 0,
            'ml_models': MLModel.query.count() if ml_available else 0,
            'active_ml_models': MLModel.query.filter_by(is_active=True).count() if ml_available else 0
        }
        
        # Get top performers and struggling users
        if ml_available:
            top_skill_profiles = db.session.query(
                UserSkillProfile.user_id,
                User.username,
                db.func.avg(UserSkillProfile.accuracy_score).label('avg_accuracy'),
                db.func.count(UserSkillProfile.id).label('profile_count')
            ).join(User, UserSkillProfile.user_id == User.id).group_by(
                UserSkillProfile.user_id, User.username
            ).order_by(db.desc('avg_accuracy')).limit(10).all()
            
            struggling_users = db.session.query(
                UserSkillProfile.user_id,
                User.username,
                db.func.avg(UserSkillProfile.accuracy_score).label('avg_accuracy'),
                db.func.count(UserSkillProfile.id).label('profile_count')
            ).join(User, UserSkillProfile.user_id == User.id).group_by(
                UserSkillProfile.user_id, User.username
            ).having(db.func.avg(UserSkillProfile.accuracy_score) < 0.4).order_by('avg_accuracy').limit(10).all()
            
            # Get recent adaptive sessions
            recent_sessions = db.session.query(
                AdaptiveQuizSession,
                User.username,
                QuizSession.total_questions,
                QuizSession.correct_answers
            ).join(User, AdaptiveQuizSession.user_id == User.id).join(
                QuizSession, AdaptiveQuizSession.quiz_session_id == QuizSession.id
            ).order_by(AdaptiveQuizSession.created_at.desc()).limit(20).all()
            
            # Get category distribution
            category_stats = db.session.query(
                UserSkillProfile.category,
                db.func.count(UserSkillProfile.id).label('profile_count'),
                db.func.avg(UserSkillProfile.accuracy_score).label('avg_accuracy')
            ).group_by(UserSkillProfile.category).order_by(db.desc('profile_count')).all()
            
            # Get model performance data
            ml_models = MLModel.query.order_by(MLModel.created_at.desc()).all()
        else:
            top_skill_profiles = []
            struggling_users = []
            recent_sessions = []
            category_stats = []
            ml_models = []
        
        return render_template('admin/ml_settings.html',
                             ml_status=ml_status,
                             stats=stats,
                             top_performers=top_skill_profiles,
                             struggling_users=struggling_users,
                             ml_models=ml_models,
                             recent_sessions=recent_sessions,
                             category_stats=category_stats)
    
    except Exception as e:
        flash(f'Error loading ML settings: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/ml-settings/cleanup-models', methods=['POST'])
@admin_required
def cleanup_ml_models():
    """Clean up old ML model records"""
    try:
        from ..ml.models import MLModel
        
        # Count models before cleanup
        before_count = MLModel.query.count()
        
        # Delete all model records
        MLModel.query.delete()
        db.session.commit()
        
        flash(f'Successfully cleaned up {before_count} old ML model records. Reactivate the ML system to create fresh models.', 'success')
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_models_cleanup',
            additional_info=json.dumps({
                'models_deleted': before_count
            })
        )
        
    except Exception as e:
        flash(f'Error cleaning up ML models: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.ml_settings'))

@admin_bp.route('/ml-settings/activate', methods=['POST'])
@admin_required
def activate_ml_system():
    """Activate and initialize the ML system"""
    try:
        from ..ml.service import ml_service
        
        # Force initialization
        ml_service.initialize()
        
        if ml_service.is_ml_enabled():
            # Run initial profile building if no data exists
            from ..ml.models import UserSkillProfile
            if UserSkillProfile.query.count() == 0:
                result = ml_service.engine.rebuild_all_profiles()
                if result.get('success', False):
                    flash(f'ML system activated successfully! Built {result.get("updated_profiles", 0)} user profiles.', 'success')
                else:
                    flash(f'ML system activated but profile building failed: {result.get("error", "Unknown error")}', 'warning')
            else:
                flash('ML system activated successfully!', 'success')
        else:
            flash('Failed to activate ML system. Check dependencies and logs.', 'error')
            
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_system_activate',
            additional_info=json.dumps({
                'success': ml_service.is_ml_enabled()
            })
        )
        
    except Exception as e:
        flash(f'Error activating ML system: {str(e)}', 'error')
    
    return redirect(url_for('admin.ml_settings'))

@admin_bp.route('/ml-settings/deactivate', methods=['POST'])
@admin_required
def deactivate_ml_system():
    """Deactivate the ML system"""
    try:
        from ..ml.service import ml_service
        
        # Reset ML service
        ml_service._initialized = False
        ml_service.engine.is_initialized = False
        
        flash('ML system deactivated successfully!', 'success')
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_system_deactivate',
            additional_info=json.dumps({
                'deactivated_at': datetime.now().isoformat()
            })
        )
        
    except Exception as e:
        flash(f'Error deactivating ML system: {str(e)}', 'error')
    
    return redirect(url_for('admin.ml_settings'))

@admin_bp.route('/ml-settings/rebuild-profiles', methods=['POST'])
@admin_required
def rebuild_ml_profiles():
    """Rebuild ML profiles for all users"""
    try:
        from ..ml.service import ml_service
        
        # This is an intensive operation - should be run in background
        # For now, we'll provide a simple rebuild
        result = ml_service.engine.rebuild_all_profiles()
        
        if result.get('success', False):
            flash(f'ML profiles rebuilt successfully. Updated {result.get("updated_profiles", 0)} profiles.', 'success')
        else:
            flash(f'Failed to rebuild ML profiles: {result.get("error", "Unknown error")}', 'error')
            
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_profiles_rebuild',
            additional_info=json.dumps(result)
        )
        
    except Exception as e:
        flash(f'Error rebuilding ML profiles: {str(e)}', 'error')
    
    return redirect(url_for('admin.ml_settings'))

@admin_bp.route('/ml-settings/retrain-models', methods=['POST'])
@admin_required
def retrain_ml_models():
    """Retrain ML models with latest data"""
    try:
        from ..ml.service import ml_service
        
        # Retrain difficulty prediction models
        result = ml_service.engine.retrain_models()
        
        if result.get('success', False):
            flash(f'ML models retrained successfully. {result.get("message", "")}', 'success')
        else:
            flash(f'Failed to retrain ML models: {result.get("error", "Unknown error")}', 'error')
            
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_models_retrain',
            additional_info=json.dumps(result)
        )
        
    except Exception as e:
        flash(f'Error retraining ML models: {str(e)}', 'error')
    
    return redirect(url_for('admin.ml_settings'))

@admin_bp.route('/ml-settings/export-analytics')
@admin_required
def export_ml_analytics():
    """Export ML analytics data to CSV"""
    try:
        from ..ml.models import LearningAnalytics, UserSkillProfile
        
        # Get analytics data
        analytics = db.session.query(
            LearningAnalytics,
            User.username
        ).join(User, LearningAnalytics.user_id == User.id).order_by(
            LearningAnalytics.date.desc()
        ).limit(10000).all()
        
        # Create CSV in memory
        output = BytesIO()
        text_stream = StringIO()
        writer = csv.writer(text_stream)
        
        # Write headers
        writer.writerow([
            'user_id', 'username', 'date', 'study_time_minutes', 'questions_attempted',
            'questions_correct', 'accuracy', 'avg_difficulty', 'avg_response_time',
            'learning_velocity', 'concept_mastery', 'recommended_difficulty'
        ])
        
        # Write data
        for analytics_entry, username in analytics:
            accuracy = (analytics_entry.questions_correct / analytics_entry.questions_attempted 
                       if analytics_entry.questions_attempted > 0 else 0)
            
            writer.writerow([
                analytics_entry.user_id,
                username,
                analytics_entry.date.isoformat(),
                analytics_entry.total_study_time_minutes,
                analytics_entry.questions_attempted,
                analytics_entry.questions_correct,
                f'{accuracy:.3f}',
                f'{analytics_entry.average_difficulty_attempted:.3f}' if analytics_entry.average_difficulty_attempted else '',
                f'{analytics_entry.avg_response_time:.1f}' if analytics_entry.avg_response_time else '',
                f'{analytics_entry.learning_velocity:.3f}' if analytics_entry.learning_velocity else '',
                f'{analytics_entry.concept_mastery_score:.3f}' if analytics_entry.concept_mastery_score else '',
                f'{analytics_entry.recommended_difficulty:.3f}' if analytics_entry.recommended_difficulty else ''
            ])
        
        # Convert to bytes
        csv_content = text_stream.getvalue()
        output.write(csv_content.encode('utf-8-sig'))
        output.seek(0)
        
        # Log the export
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_analytics_export',
            additional_info=json.dumps({
                'records_exported': len(analytics)
            })
        )
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ml_analytics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting ML analytics: {str(e)}', 'error')
        return redirect(url_for('admin.ml_settings'))

# ========================================
# MARKETING EMAIL ROUTES
# ========================================

@admin_bp.route('/marketing-emails')
@admin_required
def marketing_emails():
    """Marketing emails dashboard"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = MarketingEmail.query
    
    # Apply filters
    if status:
        query = query.filter(MarketingEmail.status == status)
    
    if search:
        query = query.filter(MarketingEmail.title.contains(search))
    
    # Paginate
    emails = query.order_by(MarketingEmail.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics
    stats = MarketingEmailService.get_marketing_statistics()
    
    return render_template('admin/marketing_emails.html', 
                         emails=emails, 
                         stats=stats, user=current_user)

@admin_bp.route('/marketing-emails/create', methods=['GET', 'POST'])
@admin_required
def create_marketing_email():
    """Create new marketing email campaign"""
    if request.method == 'POST':
        title = request.form.get('title')
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
        action = request.form.get('action')
        
        # Handle file upload
        html_file = request.files.get('html_file')
        if html_file and html_file.filename:
            html_content = html_file.read().decode('utf-8')
        
        # Targeting options
        target_free = bool(request.form.get('target_free_users'))
        target_premium = bool(request.form.get('target_premium_users'))
        target_pro = bool(request.form.get('target_pro_users'))
        target_active = bool(request.form.get('target_active_only'))
        
        # Validation
        if not all([title, subject, html_content]):
            flash('Please fill in all required fields', 'error')
            templates = MarketingTemplate.query.filter_by(is_active=True).all()
            return render_template('admin/create_marketing_email.html', 
                                 templates=templates, user=current_user)
        
        try:
            # Create email campaign
            email = MarketingEmailService.create_marketing_email(
                title=title,
                subject=subject,
                html_content=html_content,
                created_by_user_id=current_user.id,
                target_free=target_free,
                target_premium=target_premium,
                target_pro=target_pro,
                target_active_only=target_active
            )
            
            if action == 'send_now':
                # Send immediately
                result = MarketingEmailService.send_marketing_email(email.id)
                if result['success']:
                    flash(f'Marketing email campaign created and is being sent to {result["recipient_count"]} users!', 'success')
                else:
                    flash(f'Campaign created but failed to send: {result["error"]}', 'error')
            else:
                # Save as draft
                flash('Marketing email campaign saved as draft', 'success')
            
            return redirect(url_for('admin.marketing_emails'))
            
        except Exception as e:
            flash(f'Error creating campaign: {str(e)}', 'error')
    
    # GET request - show form
    templates = MarketingTemplate.query.filter_by(is_active=True).all()
    return render_template('admin/create_marketing_email.html', 
                         templates=templates, user=current_user)

@admin_bp.route('/marketing-emails/<int:id>')
@admin_required
def view_marketing_email(id):
    """View marketing email campaign details"""
    email = MarketingEmail.query.get_or_404(id)
    
    # Get send statistics
    logs = MarketingEmailLog.query.filter_by(marketing_email_id=id).all()
    
    return render_template('admin/view_marketing_email.html', 
                         email=email, 
                         logs=logs, user=current_user)

@admin_bp.route('/marketing-emails/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_marketing_email(id):
    """Edit marketing email campaign (only drafts)"""
    email = MarketingEmail.query.get_or_404(id)
    
    if email.status != 'draft':
        flash('Only draft campaigns can be edited', 'error')
        return redirect(url_for('admin.view_marketing_email', id=id))
    
    if request.method == 'POST':
        email.title = request.form.get('title')
        email.subject = request.form.get('subject')
        email.html_content = request.form.get('html_content')
        
        # Update targeting
        email.target_free_users = bool(request.form.get('target_free_users'))
        email.target_premium_users = bool(request.form.get('target_premium_users'))
        email.target_pro_users = bool(request.form.get('target_pro_users'))
        email.target_active_only = bool(request.form.get('target_active_only'))
        
        # Recalculate recipient count
        recipients = MarketingEmailService.get_eligible_recipients(
            email.target_free_users,
            email.target_premium_users,
            email.target_pro_users,
            email.target_active_only
        )
        email.recipients_count = len(recipients)
        
        db.session.commit()
        flash('Marketing email campaign updated', 'success')
        return redirect(url_for('admin.view_marketing_email', id=id))
    
    templates = MarketingTemplate.query.filter_by(is_active=True).all()
    return render_template('admin/edit_marketing_email.html', 
                         email=email, 
                         templates=templates, user=current_user)

@admin_bp.route('/api/marketing-recipients', methods=['GET', 'POST'])
@admin_required
def get_marketing_recipients():
    """Get count of marketing email recipients"""
    try:
        print(f"[DEBUG] Request method: {request.method}")
        print(f"[DEBUG] Request form data: {dict(request.form)}")
        print(f"[DEBUG] Request args: {dict(request.args)}")
        
        if request.method == 'POST':
            # Check if form data exists
            print(f"[DEBUG] Form keys: {list(request.form.keys())}")
            
            # Proper boolean parsing - handle 'true'/'false' strings from JavaScript
            target_free = request.form.get('target_free_users', '').lower() in ['true', 'on', '1']
            target_premium = request.form.get('target_premium_users', '').lower() in ['true', 'on', '1']
            target_pro = request.form.get('target_pro_users', '').lower() in ['true', 'on', '1']
            target_active = request.form.get('target_active_only', '').lower() in ['true', 'on', '1']
            
            print(f"[DEBUG] Parsed form data: free={target_free}, premium={target_premium}, pro={target_pro}, active={target_active}")
        else:
            email_id = request.args.get('email_id')
            if email_id:
                email = MarketingEmail.query.get(email_id)
                if email:
                    target_free = email.target_free_users
                    target_premium = email.target_premium_users
                    target_pro = email.target_pro_users
                    target_active = email.target_active_only
                else:
                    return jsonify({'success': False, 'error': 'Email not found', 'count': 0})
            else:
                target_free = target_premium = target_pro = True
                target_active = False
        
        # Debug logging
        print(f"[DEBUG] Final recipient query params: free={target_free}, premium={target_premium}, pro={target_pro}, active={target_active}")
        
        # Quick test: get all users first
        all_users = User.query.filter(
            User.is_active == True,
            User.is_verified == True
        ).all()
        print(f"[DEBUG] Total active/verified users: {len(all_users)}")
        
        # Test notification preferences
        from ..notification_models import UserNotificationPreferences
        marketing_users = db.session.query(User).join(
            UserNotificationPreferences, 
            User.id == UserNotificationPreferences.user_id
        ).filter(
            User.is_active == True,
            User.is_verified == True,
            UserNotificationPreferences.marketing_emails == True
        ).all()
        print(f"[DEBUG] Users with marketing enabled: {len(marketing_users)}")
        for u in marketing_users:
            print(f"[DEBUG]   - {u.username} ({u.subscription_tier})")
        
        recipients = MarketingEmailService.get_eligible_recipients(
            target_free, target_premium, target_pro, target_active
        )
        
        count = len(recipients)
        print(f"[DEBUG] Found {count} eligible recipients")
        for r in recipients:
            print(f"[DEBUG]   - {r.username} ({r.subscription_tier})")
        
        return jsonify({'success': True, 'count': count})
        
    except Exception as e:
        print(f"[ERROR] get_marketing_recipients failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'count': 0})

@admin_bp.route('/api/marketing-send', methods=['POST'])
@admin_required
def send_marketing_email():
    """Send marketing email campaign"""
    data = request.get_json()
    email_id = data.get('email_id')
    is_resend = data.get('resend', False)
    
    if not email_id:
        return jsonify({'success': False, 'error': 'Email ID required'})
    
    # If it's a resend, reset the email status to draft first
    if is_resend:
        email = MarketingEmail.query.get(email_id)
        if email and email.status in ['sent', 'failed', 'partially_sent']:
            email.status = 'draft'
            email.sent_count = 0
            email.failed_count = 0
            email.sent_at = None
            db.session.commit()
    
    result = MarketingEmailService.send_marketing_email(email_id)
    return jsonify(result)

@admin_bp.route('/marketing-emails/<int:id>/logs')
@admin_required
def marketing_email_logs(id):
    """View marketing email send logs"""
    email = MarketingEmail.query.get_or_404(id)
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = MarketingEmailLog.query.filter_by(marketing_email_id=id)
    
    if status:
        query = query.filter(MarketingEmailLog.status == status)
    
    logs = query.order_by(MarketingEmailLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/marketing_email_logs.html', 
                         email=email, 
                         logs=logs, user=current_user)

# Marketing Templates Routes

@admin_bp.route('/marketing-templates')
@admin_required
def marketing_templates():
    """Marketing email templates management"""
    templates = MarketingTemplate.query.order_by(MarketingTemplate.created_at.desc()).all()
    return render_template('admin/marketing_templates.html', 
                         templates=templates, user=current_user)

@admin_bp.route('/marketing-templates/create', methods=['GET', 'POST'])
@admin_required
def create_marketing_template():
    """Create new marketing email template"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        html_content = request.form.get('html_content')
        category = request.form.get('category')
        
        # Handle file upload
        html_file = request.files.get('html_file')
        if html_file and html_file.filename:
            html_content = html_file.read().decode('utf-8')
        
        if not all([name, html_content]):
            flash('Name and HTML content are required', 'error')
            return render_template('admin/create_marketing_template.html', user=current_user)
        
        template = MarketingTemplate(
            name=name,
            description=description,
            html_content=html_content,
            category=category,
            created_by_user_id=current_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Marketing template created successfully', 'success')
        return redirect(url_for('admin.marketing_templates'))
    
    return render_template('admin/create_marketing_template.html', user=current_user)

@admin_bp.route('/api/marketing-template')
@admin_required
def get_marketing_template():
    """Get marketing template content"""
    template_id = request.args.get('id')
    template = MarketingTemplate.query.get_or_404(template_id)
    
    return jsonify({
        'html_content': template.html_content,
        'name': template.name,
        'description': template.description
    })
