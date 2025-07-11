import os
import csv
import logging
from flask import render_template, request, redirect, url_for, session, current_app, send_file, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import StringIO, BytesIO
from sqlalchemy import text, inspect, func
from . import admin_bp
from functools import wraps

from .utils import validate_question
from .. import db
from ..models import Question, Option, TrafficSign, QuizImage, User, AdminAuditLog, AdminReport, UserFeedback, QuizSession, QuizResponse, LearningModules, LearningSubmodules, VideoShorts, UserShortsProgress
from ..marketing_models import MarketingEmail, MarketingTemplate, MarketingEmailLog
from ..marketing_service import MarketingEmailService
from ..security.admin_security import AdminSecurityService
import json
from datetime import datetime, timedelta

# Setup logger for admin operations
logger = logging.getLogger(__name__)

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
    subcategory_filter = request.args.get('subcategory', '').strip()
    difficulty_filter = request.args.get('difficulty', '').strip()
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    sort_by = request.args.get('sort_by', 'id')  # Default sort by ID
    sort_order = request.args.get('sort_order', 'asc')  # asc or desc
    
    # Validate per_page options
    if per_page not in [20, 50, 100] and per_page != -1:  # -1 means "All"
        per_page = 50

    validation_errors = []
    message = None

    # Handle POST requests
    if request.method == 'POST':
        # Image upload and metadata
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
        elif 'sql_query' in request.form:
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
        
        # Handle question add/edit (only if question fields are present)
        elif any(field in request.form for field in ['question', 'option_a', 'option_b', 'option_c', 'option_d']):
            question_id = request.form.get('question_id')
            question_data = {
                'question': request.form.get('question'),
                'option_a': request.form.get('option_a'),
                'option_b': request.form.get('option_b'),
                'option_c': request.form.get('option_c'),
                'option_d': request.form.get('option_d'),
                'correct_option': request.form.get('correct_option', '').lower(),
                'category': request.form.get('category') or 'Ukategorisert',
                'subcategory': request.form.get('subcategory'),
                'difficulty_level': int(request.form.get('difficulty_level', 1)),
                'explanation': request.form.get('explanation'),
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
                        q.subcategory = question_data['subcategory']
                        q.difficulty_level = question_data['difficulty_level']
                        q.explanation = question_data['explanation']
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
                        subcategory=question_data['subcategory'],
                        difficulty_level=question_data['difficulty_level'],
                        explanation=question_data['explanation'],
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
    
    # Fetch questions with options using ORM with advanced filtering
    query = Question.query
    
    # Apply search filter
    if search_query:
        query = query.filter(Question.question.ilike(f'%{search_query}%'))
    
    # Apply category filter
    if category_filter and category_filter != 'all':
        query = query.filter(Question.category == category_filter)
    
    # Apply subcategory filter
    if subcategory_filter and subcategory_filter != 'all':
        query = query.filter(Question.subcategory == subcategory_filter)
    
    # Apply difficulty filter
    if difficulty_filter and difficulty_filter != 'all':
        try:
            difficulty_int = int(difficulty_filter)
            query = query.filter(Question.difficulty_level == difficulty_int)
        except ValueError:
            pass  # Invalid difficulty filter, ignore
    
    # Apply sorting
    valid_sort_columns = ['id', 'question', 'category', 'subcategory', 'difficulty_level']
    if sort_by in valid_sort_columns:
        sort_column = getattr(Question, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Question.id.asc())  # Default sort
    
    # Get total count for pagination info (before applying pagination)
    total_questions = query.count()
    
    # Apply pagination
    if per_page == -1:  # Show all
        all_questions = query.all()
        paginated_questions = None
    else:
        paginated_questions = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        all_questions = paginated_questions.items

    questions = []
    for q in all_questions:
        # Create a dict of options keyed by label
        opts = {opt.option_letter: opt.option_text for opt in q.options}
        questions.append({
            'id': q.id,
            'question': q.question,
            'category': q.category,
            'subcategory': q.subcategory,
            'difficulty_level': q.difficulty_level,
            'explanation': q.explanation,
            'image_filename': q.image_filename,
            'option_a': opts.get('a', ''),
            'option_b': opts.get('b', ''),
            'option_c': opts.get('c', ''),
            'option_d': opts.get('d', ''),
            'correct_option': q.correct_option
        })

    # Statistics using ORM (based on all questions, not filtered)
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
        'filtered': total_questions,  # Add filtered count
        'by_category': by_category, 
        'with_images': with_images, 
        'without_images': without_images
    }

    # Get all unique categories and subcategories for filters
    categories = [cat[0] for cat in db.session.query(Question.category).distinct().order_by(Question.category).all() if cat[0]]
    
    # Get subcategories (all or filtered by category)
    if category_filter and category_filter != 'all':
        subcategories = [sub[0] for sub in db.session.query(Question.subcategory).filter(
            Question.category == category_filter,
            Question.subcategory.isnot(None),
            Question.subcategory != ''
        ).distinct().order_by(Question.subcategory).all() if sub[0]]
    else:
        subcategories = [sub[0] for sub in db.session.query(Question.subcategory).filter(
            Question.subcategory.isnot(None),
            Question.subcategory != ''
        ).distinct().order_by(Question.subcategory).all() if sub[0]]
    
    # Pagination info
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total_questions,
        'pages': (total_questions + per_page - 1) // per_page if per_page != -1 else 1,
        'has_prev': page > 1 if per_page != -1 else False,
        'has_next': page < ((total_questions + per_page - 1) // per_page) if per_page != -1 else False,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if per_page != -1 and page < ((total_questions + per_page - 1) // per_page) else None
    }

    # Image list for gallery
    images = []
    
    # Traffic signs
    images_dir = os.path.join(current_app.static_folder, 'images')
    try:
        for ts in TrafficSign.query.all():
            # Filter out macOS hidden files and ensure file exists
            if ts.filename and not ts.filename.startswith('._'):
                # Dynamically find the subfolder under static/images containing this filename
                folder = ''
                file_found = False
                for root, dirs, files in os.walk(images_dir):
                    # Filter out hidden files from the file list
                    clean_files = [f for f in files if not f.startswith('._')]
                    if ts.filename in clean_files:
                        # Verify the file actually exists
                        file_path = os.path.join(root, ts.filename)
                        if os.path.exists(file_path):
                            folder = os.path.relpath(root, images_dir).replace(os.sep, '/')
                            file_found = True
                            break
                
                # Only add to images list if file actually exists
                if file_found:
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
        # Filter out macOS hidden files and verify file exists
        if qi.filename and not qi.filename.startswith('._'):
            # Verify the file actually exists
            file_path = os.path.join(images_dir, qi.folder or '', qi.filename)
            if os.path.exists(file_path):
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
            # Filter out hidden directories and macOS metadata
            if not name.startswith('.') and not name.startswith('._'):
                path = os.path.join(images_dir, name)
                if os.path.isdir(path):
                    folders.append(name)

    # Tables for SQL console - get all tables dynamically
    tables = {}
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    
    for tbl in table_names:
        try:
            # Security: Validate table name against allowed tables to prevent injection
            if not tbl.isalnum() and '_' not in tbl:
                print(f"[ADMIN] Skipping potentially unsafe table name: {tbl}")
                continue
                
            # Use parameterized query to prevent SQL injection
            # Note: table names cannot be parameterized, so we validate the name above
            result = db.session.execute(text(f"SELECT * FROM `{tbl}` LIMIT 1000"))
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
    
    # Marketing data
    try:
        marketing_stats = MarketingEmailService.get_marketing_statistics()
    except Exception as e:
        logger.error(f'Error loading marketing stats in admin dashboard: {e}')
        marketing_stats = {
            'total_campaigns': 0,
            'opted_in_users': 0,
            'sent_this_month': 0,
            'success_rate': 0
        }
    
    marketing_emails = []

    return render_template(
        'admin/admin_dashboard.html',
        questions=questions,
        stats=stats,
        categories=categories,
        subcategories=subcategories,
        search_query=search_query,
        category_filter=category_filter,
        subcategory_filter=subcategory_filter,
        difficulty_filter=difficulty_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        pagination=pagination_info,
        current_per_page=per_page,  # Pass current per_page to template
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
        user_filter='',
        # Marketing data
        marketing_stats=marketing_stats,
        marketing_emails=marketing_emails)
        
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

@admin_bp.route('/delete_question/<int:question_id>', methods=['POST'])
@admin_required
def delete_question(question_id):
    
    # Delete question and its options (cascade will handle options)
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
    
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_image', methods=['POST'])
@admin_required
def delete_image():
    """Delete an image file and its database record"""
    
    image_id = request.form.get('image_id')
    image_type = request.form.get('image_type')  # 'traffic_sign' or 'quiz_image'
    
    if not image_id or not image_type:
        flash('Invalid image deletion request', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        if image_type == 'traffic_sign':
            image_record = TrafficSign.query.get(image_id)
            if image_record:
                # Delete physical file
                if image_record.filename:
                    # Find the file in the images directory
                    images_dir = os.path.join(current_app.static_folder, 'images')
                    for root, dirs, files in os.walk(images_dir):
                        if image_record.filename in files:
                            file_path = os.path.join(root, image_record.filename)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                break
                
                # Delete database record
                db.session.delete(image_record)
                flash(f'Traffic sign "{image_record.filename}" deleted successfully', 'success')
        
        elif image_type == 'quiz_image':
            image_record = QuizImage.query.get(image_id)
            if image_record:
                # Delete physical file
                if image_record.filename:
                    images_dir = os.path.join(current_app.static_folder, 'images')
                    file_path = os.path.join(images_dir, image_record.folder or '', image_record.filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Delete database record
                db.session.delete(image_record)
                flash(f'Quiz image "{image_record.filename}" deleted successfully', 'success')
        
        else:
            flash('Unknown image type', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        db.session.commit()
        
        # Log the deletion action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='image_delete',
            additional_info=json.dumps({
                'image_type': image_type,
                'image_id': image_id,
                'filename': image_record.filename if image_record else 'unknown'
            })
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    
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
    
    if not (file.filename.lower().endswith('.csv') or file.filename.lower().endswith('.json')):
        flash('Filen må være en CSV-fil (.csv) eller JSON-fil (.json)', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    overwrite_existing = request.form.get('overwrite_existing') == '1'
    csv_delimiter = request.form.get('csv_delimiter', ';')  # Default to semicolon for Norway
    
    # Handle automatic delimiter detection
    if csv_delimiter == 'auto':
        csv_delimiter = None  # Will be detected automatically
    
    try:
        # Read file content
        file_content = file.read().decode('utf-8-sig')
        
        # Determine if this is JSON or CSV
        is_json = file.filename.lower().endswith('.json')
        
        if is_json:
            # JSON Import
            try:
                questions_data = json.loads(file_content)
                if not isinstance(questions_data, list):
                    flash('JSON-filen må inneholde en liste med spørsmål', 'error')
                    return redirect(url_for('admin.admin_dashboard'))
                
                # Convert JSON to CSV-like format for processing
                expected_fields = ['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'category', 'subcategory', 'difficulty_level', 'explanation', 'image_filename']
                csv_data = []
                
                for item in questions_data:
                    if not isinstance(item, dict):
                        continue
                    # Ensure all required fields exist
                    row = {field: item.get(field, '') for field in expected_fields}
                    csv_data.append(row)
                
                # Create a fake CSV reader-like iterator
                class JSONReader:
                    def __init__(self, data):
                        self.data = data
                        self.fieldnames = expected_fields
                    
                    def __iter__(self):
                        return iter(self.data)
                
                csv_reader = JSONReader(csv_data)
                logger.info(f"Processing JSON file with {len(csv_data)} questions")
                
            except json.JSONDecodeError as e:
                flash(f'Ugyldig JSON-format: {str(e)}', 'error')
                return redirect(url_for('admin.admin_dashboard'))
        
        else:
            # CSV Import
            # Auto-detect delimiter if requested
            if csv_delimiter is None:
                import csv as csv_module
                sniffer = csv_module.Sniffer()
                try:
                    # Try to detect delimiter from first few lines
                    sample = file_content[:1024]
                    csv_delimiter = sniffer.sniff(sample, delimiters=';,\t|').delimiter
                    logger.info(f"Auto-detected CSV delimiter: '{csv_delimiter}'")
                except:
                    # Fallback to semicolon if detection fails
                    csv_delimiter = ';'
                    logger.info("Could not auto-detect delimiter, using semicolon (;)")
            
            # Handle tab character
            if csv_delimiter == '\\t':
                csv_delimiter = '\t'
                
            csv_reader = csv.DictReader(StringIO(file_content), delimiter=csv_delimiter)
        
        # Validate headers (works for both CSV and JSON)
        expected_headers = ['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'category', 'subcategory', 'difficulty_level', 'explanation', 'image_filename']
        actual_headers = csv_reader.fieldnames or []
        
        # Debug info
        if not is_json:
            logger.info(f"Using delimiter: '{csv_delimiter}'")
        logger.info(f"Found headers: {actual_headers}")
        logger.info(f"Expected headers: {expected_headers}")
        
        if not all(header in actual_headers for header in expected_headers):
            missing_headers = [h for h in expected_headers if h not in actual_headers]
            file_type = 'JSON-filen' if is_json else 'CSV-filen'
            if is_json:
                flash(f'{file_type} mangler følgende felt: {", ".join(missing_headers)}. Funnet felt: {", ".join(actual_headers)}.', 'error')
            else:
                flash(f'{file_type} mangler følgende kolonner: {", ".join(missing_headers)}. Funnet kolonner: {", ".join(actual_headers)}. Prøv et annet skilletegn.', 'error')
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
                question.subcategory = row.get('subcategory', '').strip() or None
                question.difficulty_level = int(row.get('difficulty_level', '1').strip() or 1)
                question.explanation = row.get('explanation', '').strip() or None
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
        log_info = {
            'filename': file.filename,
            'imported': imported_count,
            'updated': updated_count,
            'errors': error_count,
            'overwrite_mode': overwrite_existing,
            'format': 'json' if is_json else 'csv'
        }
        if not is_json:
            log_info['csv_delimiter'] = csv_delimiter
            
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='questions_import',
            additional_info=json.dumps(log_info)
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Feil ved lesing av CSV-fil: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_questions')
@admin_required
def export_questions():
    """Export all questions in CSV or JSON format with delimiter options"""
    
    # Get export parameters from query string
    export_format = request.args.get('format', 'csv').lower()  # 'csv' or 'json'
    csv_delimiter = request.args.get('delimiter', ',')  # Default to comma
    
    # Handle tab character
    if csv_delimiter == '\\t':
        csv_delimiter = '\t'
    
    # Get all questions with their options
    questions = Question.query.all()
    
    if export_format == 'json':
        # JSON Export
        questions_data = []
        for q in questions:
            # Get options as dict
            opts = {opt.option_letter: opt.option_text for opt in q.options}
            
            question_data = {
                'id': q.id,
                'question': q.question,
                'option_a': opts.get('a', ''),
                'option_b': opts.get('b', ''),
                'option_c': opts.get('c', ''),
                'option_d': opts.get('d', ''),
                'correct_option': q.correct_option,
                'category': q.category or 'Ukategoriseret',
                'subcategory': q.subcategory or '',
                'difficulty_level': q.difficulty_level or 1,
                'explanation': q.explanation or '',
                'image_filename': q.image_filename or ''
            }
            questions_data.append(question_data)
        
        # Create JSON in memory
        output = BytesIO()
        json_content = json.dumps(questions_data, ensure_ascii=False, indent=2)
        output.write(json_content.encode('utf-8'))
        output.seek(0)
        
        # Log the export action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='questions_export',
            additional_info=json.dumps({
                'question_count': len(questions),
                'format': 'json'
            })
        )
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name='questions_export.json'
        )
    
    else:
        # CSV Export with specified delimiter
        output = BytesIO()
        
        # Create a text wrapper for CSV writing
        text_stream = StringIO()
        writer = csv.writer(text_stream, delimiter=csv_delimiter)
        writer.writerow(['id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'category', 'subcategory', 'difficulty_level', 'explanation', 'image_filename'])
        
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
                q.subcategory or '',
                q.difficulty_level or 1,
                q.explanation or '',
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
                'question_count': len(questions),
                'format': 'csv',
                'delimiter': csv_delimiter
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

@admin_bp.route('/api/audit-log/summary', methods=['GET'])
@admin_required
def get_audit_log_summary():
    """AJAX endpoint for security summary modal."""
    try:
        # Recent security actions (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_actions = AdminAuditLog.query.filter(
            AdminAuditLog.created_at >= seven_days_ago
        ).order_by(AdminAuditLog.created_at.desc()).limit(10).all()

        # Most frequent admin actions
        top_actions = db.session.query(
            AdminAuditLog.action, db.func.count(AdminAuditLog.action).label('count')
        ).group_by(AdminAuditLog.action).order_by(db.desc('count')).limit(5).all()

        # Recent login attempts
        login_attempts = AdminAuditLog.query.filter(
            AdminAuditLog.action.in_(['admin_login_success', 'admin_login_failure'])
        ).order_by(AdminAuditLog.created_at.desc()).limit(10).all()

        # Top active admins
        top_admins = db.session.query(
            User.username, db.func.count(AdminAuditLog.id).label('action_count')
        ).join(User, AdminAuditLog.admin_user_id == User.id).group_by(User.username).order_by(db.desc('action_count')).limit(5).all()

        summary_data = {
            'recent_actions': [log.to_dict() for log in recent_actions],
            'top_actions': {action: count for action, count in top_actions},
            'login_attempts': [log.to_dict() for log in login_attempts],
            'top_admins': {username: count for username, count in top_admins}
        }
        return jsonify({'success': True, 'data': summary_data})

    except Exception as e:
        logger.error(f"Error in get_audit_log_summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/audit-log/export', methods=['GET'])
@admin_required
def export_audit_log():
    """Export audit log to CSV or JSON with filters."""
    try:
        # Get filter parameters from request
        search = request.args.get('search', '')
        action = request.args.get('action', '')
        ip = request.args.get('ip', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        export_format = request.args.get('format', 'csv').lower()

        # Build query with filters
        query = AdminAuditLog.query.join(User, User.id == AdminAuditLog.admin_user_id, isouter=True)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(db.or_(
                AdminAuditLog.action.ilike(search_term),
                User.username.ilike(search_term),
                AdminAuditLog.ip_address.ilike(search_term),
                AdminAuditLog.additional_info.ilike(search_term)
            ))
        if action:
            query = query.filter(AdminAuditLog.action == action)
        if ip:
            query = query.filter(AdminAuditLog.ip_address == ip)

        # Sorting
        sort_column = getattr(AdminAuditLog, sort_by, AdminAuditLog.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        logs = query.all()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"audit_log_{timestamp}.{export_format}"

        if export_format == 'json':
            output = jsonify([log.to_dict() for log in logs])
            output.headers["Content-Disposition"] = f"attachment; filename={filename}"
            output.headers["Content-Type"] = "application/json"
            return output
        else: # CSV
            def generate():
                data = StringIO()
                writer = csv.writer(data)
                writer.writerow(['ID', 'Timestamp', 'Action', 'Admin User', 'Target User', 'IP Address', 'User Agent', 'Info'])
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
                for log in logs:
                    writer.writerow([
                        log.id, log.created_at, log.action, 
                        log.admin_user.username if log.admin_user else 'N/A', 
                        log.target_user.username if log.target_user else 'N/A', 
                        log.ip_address, log.user_agent, log.additional_info
                    ])
                    yield data.getvalue()
                    data.seek(0)
                    data.truncate(0)
            
            headers = {"Content-Disposition": f"attachment; filename={filename}"}
            return current_app.response_class(generate(), mimetype='text/csv', headers=headers)

    except Exception as e:
        logger.error(f"Error exporting audit log: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/audit-logs', methods=['GET'])
@admin_required
def api_get_audit_logs():
    """AJAX endpoint for getting filtered/paginated audit logs."""
    try:
        # Get parameters
        search = request.args.get('search', '').strip()
        action = request.args.get('action', '').strip()
        ip = request.args.get('ip', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Build query
        query = AdminAuditLog.query.join(User, User.id == AdminAuditLog.admin_user_id, isouter=True)

        if search:
            search_term = f'%{search}%'
            query = query.filter(db.or_(
                AdminAuditLog.action.ilike(search_term),
                User.username.ilike(search_term),
                AdminAuditLog.ip_address.ilike(search_term),
                AdminAuditLog.additional_info.ilike(search_term)
            ))
        if action:
            query = query.filter(AdminAuditLog.action == action)
        if ip:
            query = query.filter(AdminAuditLog.ip_address == ip)

        # Sorting
        sort_column = getattr(AdminAuditLog, sort_by, AdminAuditLog.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        paginated_logs = query.paginate(page=page, per_page=per_page, error_out=False)
        logs = [log.to_dict() for log in paginated_logs.items]

        # Stats
        total_logs = paginated_logs.total
        unique_actions = db.session.query(db.func.count(db.distinct(AdminAuditLog.action))).scalar()

        return jsonify({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': paginated_logs.page,
                'per_page': paginated_logs.per_page,
                'total': total_logs,
                'pages': paginated_logs.pages,
                'has_prev': paginated_logs.has_prev,
                'has_next': paginated_logs.has_next,
                'prev_num': paginated_logs.prev_num,
                'next_num': paginated_logs.next_num,
                'unique_actions': unique_actions
            }
        })

    except Exception as e:
        logger.error(f"Error in api_get_audit_logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
# AJAX API ENDPOINTS FOR REPORTS
# ========================================

@admin_bp.route('/api/reports/<int:report_id>/assign', methods=['POST'])
@admin_required
def api_assign_report(report_id):
    """AJAX endpoint to assign a report to the current user."""
    try:
        report = AdminReport.query.get_or_404(report_id)
        
        if report.assigned_to_user_id:
            return jsonify({'success': False, 'error': 'Report is already assigned.'}), 400

        report.assigned_to_user_id = current_user.id
        report.status = 'in_progress'
        db.session.commit()

        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='report_assign_ajax',
            target_user_id=report.affected_user_id,
            additional_info=json.dumps({
                'report_id': report.id,
                'report_type': report.report_type
            })
        )
        
        return jsonify({
            'success': True, 
            'message': 'Report assigned successfully',
            'assigned_to': current_user.username,
            'status': 'in_progress'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in api_assign_report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# ML SETTINGS ROUTES
# ========================================

@admin_bp.route('/test')
@admin_required
def test_route():
    """Simple test route to verify admin routes are working"""
    return "ML Settings route is working!"

@admin_bp.route('/test-notifications')
@admin_required
def test_notifications():
    """Test route to generate sample notifications for testing dismissal functionality"""
    flash('Admin privileges successfully granted to gabini', 'success')
    flash('Warning: Account created within last 24 hours', 'warning')
    flash('Warning: User has never taken a quiz', 'warning')
    flash('Warning: Email notification failed', 'warning')
    flash('Test info notification', 'info')
    flash('Test error notification', 'error')
    return redirect(url_for('admin.admin_dashboard'))





# ========================================
# AJAX API ENDPOINTS FOR QUESTION MANAGEMENT
# ========================================

@admin_bp.route('/api/questions', methods=['GET'])
@admin_required
def api_get_questions():
    """AJAX endpoint for getting filtered/paginated questions"""
    try:
        # Get parameters
        search_query = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        subcategory_filter = request.args.get('subcategory', '').strip()
        difficulty_filter = request.args.get('difficulty', '').strip()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Validate per_page options
        if per_page not in [20, 50, 100] and per_page != -1:
            per_page = 50

        # Build query
        query = Question.query
        
        # Apply search filter
        if search_query:
            query = query.filter(Question.question.ilike(f'%{search_query}%'))
        
        # Apply category filter
        if category_filter and category_filter != 'all':
            query = query.filter(Question.category == category_filter)
        
        # Apply subcategory filter
        if subcategory_filter and subcategory_filter != 'all':
            query = query.filter(Question.subcategory == subcategory_filter)
        
        # Apply difficulty filter
        if difficulty_filter and difficulty_filter != 'all':
            try:
                difficulty_int = int(difficulty_filter)
                query = query.filter(Question.difficulty_level == difficulty_int)
            except ValueError:
                pass
        
        # Apply sorting
        valid_sort_columns = ['id', 'question', 'category', 'subcategory', 'difficulty_level']
        if sort_by in valid_sort_columns:
            sort_column = getattr(Question, sort_by)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Question.id.asc())
        
        # Get total count for pagination
        total_questions = query.count()
        total_in_db = Question.query.count()
        
        # Apply pagination
        if per_page == -1:  # Show all
            all_questions = query.all()
            pages = 1
            has_prev = False
            has_next = False
            prev_num = None
            next_num = None
        else:
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            all_questions = paginated.items
            pages = paginated.pages
            has_prev = paginated.has_prev
            has_next = paginated.has_next
            prev_num = paginated.prev_num
            next_num = paginated.next_num

        # Convert questions to JSON format
        questions = []
        for q in all_questions:
            opts = {opt.option_letter: opt.option_text for opt in q.options}
            questions.append({
                'id': q.id,
                'question': q.question,
                'category': q.category,
                'subcategory': q.subcategory,
                'difficulty_level': q.difficulty_level,
                'explanation': q.explanation,
                'image_filename': q.image_filename,
                'option_a': opts.get('a', ''),
                'option_b': opts.get('b', ''),
                'option_c': opts.get('c', ''),
                'option_d': opts.get('d', ''),
                'correct_option': q.correct_option
            })

        # Statistics
        category_counts = db.session.query(
            Question.category, 
            db.func.count(Question.id)
        ).group_by(Question.category).all()
        by_category = dict(category_counts)
        
        with_images = Question.query.filter(
            Question.image_filename.isnot(None), 
            Question.image_filename != ''
        ).count()
        
        stats = {
            'total': total_in_db,
            'filtered': total_questions,
            'by_category': by_category,
            'with_images': with_images,
            'without_images': total_in_db - with_images
        }

        # Pagination info
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_questions,
            'total_in_db': total_in_db,
            'pages': pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': prev_num,
            'next_num': next_num,
            'filtered': total_questions
        }

        return jsonify({
            'success': True,
            'questions': questions,
            'pagination': pagination,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error in api_get_questions: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/question/create', methods=['POST'])
@admin_required
def api_create_question():
    """AJAX endpoint for creating a new question"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('question', '').strip():
            return jsonify({'success': False, 'error': 'Question text is required'})
        
        if not data.get('correct_option', '').strip().lower() in ['a', 'b', 'c', 'd']:
            return jsonify({'success': False, 'error': 'Valid correct option (a, b, c, d) is required'})
        
        # Create new question
        question = Question(
            question=data['question'].strip(),
            correct_option=data['correct_option'].strip().lower(),
            category=data.get('category', '').strip() or 'Ukategoriseret',
            subcategory=data.get('subcategory', '').strip() or None,
            difficulty_level=int(data.get('difficulty_level', 1)),
            explanation=data.get('explanation', '').strip() or None,
            image_filename=data.get('image_filename', '').strip() or None
        )
        
        db.session.add(question)
        db.session.flush()  # Get the ID
        
        # Add options
        for letter, option_key in [('a', 'option_a'), ('b', 'option_b'), ('c', 'option_c'), ('d', 'option_d')]:
            option_text = data.get(option_key, '').strip()
            if option_text:
                option = Option(
                    question_id=question.id,
                    option_letter=letter,
                    option_text=option_text
                )
                db.session.add(option)
        
        db.session.commit()
        
        # Return the created question data
        opts = {opt.option_letter: opt.option_text for opt in question.options}
        question_data = {
            'id': question.id,
            'question': question.question,
            'category': question.category,
            'subcategory': question.subcategory,
            'difficulty_level': question.difficulty_level,
            'explanation': question.explanation,
            'image_filename': question.image_filename,
            'option_a': opts.get('a', ''),
            'option_b': opts.get('b', ''),
            'option_c': opts.get('c', ''),
            'option_d': opts.get('d', ''),
            'correct_option': question.correct_option
        }
        
        return jsonify({'success': True, 'question': question_data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/question/update/<int:question_id>', methods=['POST'])
@admin_required
def api_update_question(question_id):
    """AJAX endpoint for updating an existing question"""
    try:
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        # Validate required fields
        if not data.get('question', '').strip():
            return jsonify({'success': False, 'error': 'Question text is required'})
        
        if not data.get('correct_option', '').strip().lower() in ['a', 'b', 'c', 'd']:
            return jsonify({'success': False, 'error': 'Valid correct option (a, b, c, d) is required'})
        
        # Update question data
        question.question = data['question'].strip()
        question.correct_option = data['correct_option'].strip().lower()
        question.category = data.get('category', '').strip() or 'Ukategoriseret'
        question.subcategory = data.get('subcategory', '').strip() or None
        question.difficulty_level = int(data.get('difficulty_level', 1))
        question.explanation = data.get('explanation', '').strip() or None
        question.image_filename = data.get('image_filename', '').strip() or None
        
        # Delete existing options and add new ones
        Option.query.filter_by(question_id=question.id).delete()
        
        for letter, option_key in [('a', 'option_a'), ('b', 'option_b'), ('c', 'option_c'), ('d', 'option_d')]:
            option_text = data.get(option_key, '').strip()
            if option_text:
                option = Option(
                    question_id=question.id,
                    option_letter=letter,
                    option_text=option_text
                )
                db.session.add(option)
        
        db.session.commit()
        
        # Return the updated question data
        opts = {opt.option_letter: opt.option_text for opt in question.options}
        question_data = {
            'id': question.id,
            'question': question.question,
            'category': question.category,
            'subcategory': question.subcategory,
            'difficulty_level': question.difficulty_level,
            'explanation': question.explanation,
            'image_filename': question.image_filename,
            'option_a': opts.get('a', ''),
            'option_b': opts.get('b', ''),
            'option_c': opts.get('c', ''),
            'option_d': opts.get('d', ''),
            'correct_option': question.correct_option
        }
        
        return jsonify({'success': True, 'question': question_data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/question/delete/<int:question_id>', methods=['DELETE'])
@admin_required
def api_delete_question(question_id):
    """AJAX endpoint for deleting a question"""
    try:
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Question deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/subcategories')
@admin_required
def api_get_subcategories():
    """AJAX endpoint to get subcategories for a given category"""
    category = request.args.get('category')
    
    if not category or category == 'all':
        # Return all subcategories
        subcategories = db.session.query(Question.subcategory).filter(
            Question.subcategory.isnot(None),
            Question.subcategory != ''
        ).distinct().order_by(Question.subcategory).all()
    else:
        # Return subcategories for specific category
        subcategories = db.session.query(Question.subcategory).filter(
            Question.category == category,
            Question.subcategory.isnot(None),
            Question.subcategory != ''
        ).distinct().order_by(Question.subcategory).all()
    
    subcategory_list = [sub[0] for sub in subcategories if sub[0]]
    
    return jsonify({'subcategories': subcategory_list})

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
            
            return redirect(url_for('admin.admin_dashboard') + '#marketing')
            
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
    try:
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
                             
    except Exception as e:
        current_app.logger.error(f'Error in edit_marketing_email: {str(e)}')
        flash('Error updating marketing email campaign', 'error')
        return redirect(url_for('admin.marketing_emails'))

@admin_bp.route('/api/marketing-templates', methods=['GET'])
@admin_required
def api_marketing_templates():
    """API endpoint for marketing templates"""
    try:
        templates = MarketingTemplate.query.filter_by(is_active=True).order_by(
            MarketingTemplate.created_at.desc()
        ).all()
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'html_content': template.html_content,
                'created_at': template.created_at.strftime('%d.%m.%Y %H:%M') if template.created_at else '',
                'created_by': {
                    'id': template.created_by.id,
                    'username': template.created_by.username
                } if template.created_by else None
            })
        
        return jsonify({
            'success': True,
            'templates': templates_data
        })
        
    except Exception as e:
        logger.error(f'Error in api_marketing_templates: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/marketing-recipients', methods=['GET', 'POST'])
@admin_required
def get_marketing_recipients_count():
   """Get count of marketing email recipients"""
   try:
       print(f"[DEBUG] Request method: {request.method}")
       print(f"[DEBUG] Request form data: {dict(request.form)}")
       print(f"[DEBUG] Request args: {dict(request.args)}")
       
       # Check for details parameter
       details = request.args.get('details', '').lower() == 'true'
       
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
       
       # Return detailed data if requested
       if details:
           return jsonify({
               'success': True,
               'recipients': [
                   {
                       'full_name': user.full_name,
                       'email': user.email,
                       'subscription': user.subscription_tier or 'free',
                       'is_admin': user.is_admin
                   }
                   for user in recipients
               ],
               'count': count
           })
       
       return jsonify({'success': True, 'count': count})
       
   except Exception as e:
       print(f"[ERROR] get_marketing_recipients failed: {str(e)}")
       import traceback
       traceback.print_exc()
       return jsonify({'success': False, 'error': str(e), 'count': 0})


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

# ===========================
# Enhanced Admin API Endpoints
# ===========================

@admin_bp.route('/api/reports')
@admin_required
def api_reports():
    """API endpoint for reports with filtering, sorting, and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        report_type = request.args.get('type', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = AdminReport.query
        
        # Apply filters
        if search:
            query = query.filter(
                AdminReport.title.contains(search) |
                AdminReport.description.contains(search) |
                AdminReport.additional_info.contains(search)
            )
        
        if report_type:
            query = query.filter(AdminReport.report_type == report_type)
        
        if status:
            query = query.filter(AdminReport.status == status)
        
        if priority:
            query = query.filter(AdminReport.priority == priority)
        
        # Apply sorting
        if hasattr(AdminReport, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(AdminReport, sort_by).desc())
            else:
                query = query.order_by(getattr(AdminReport, sort_by))
        
        # Paginate
        reports = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        reports_data = []
        for report in reports.items:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'report_type': report.report_type,
                'priority': report.priority,
                'status': report.status,
                'created_at': report.created_at.isoformat(),
                'additional_info': report.additional_info,
                'reported_by': {
                    'id': report.reported_by.id,
                    'username': report.reported_by.username
                } if report.reported_by else None,
                'assigned_to': {
                    'id': report.assigned_to.id,
                    'username': report.assigned_to.username
                } if report.assigned_to else None
            })
        
        return jsonify({
            'reports': reports_data,
            'pagination': {
                'page': reports.page,
                'pages': reports.pages,
                'per_page': reports.per_page,
                'total': reports.total,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev,
                'next_num': reports.next_num,
                'prev_num': reports.prev_num
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================================
# LEARNING MODULES ADMIN API ROUTES
# ===================================

@admin_bp.route('/api/learning-modules', methods=['GET'])
@admin_required
def get_learning_modules():
    """Get all learning modules with statistics"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        search_filter = request.args.get('search', '')
        
        # Build query
        query = LearningModules.query
        
        # Apply filters
        if status_filter == 'active':
            query = query.filter(LearningModules.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(LearningModules.is_active == False)
            
        if search_filter:
            query = query.filter(
                db.or_(
                    LearningModules.title.ilike(f'%{search_filter}%'),
                    LearningModules.description.ilike(f'%{search_filter}%')
                )
            )
        
        # Order by module number
        modules = query.order_by(LearningModules.module_number).all()
        
        # Format modules with additional stats
        modules_data = []
        for module in modules:
            # Get submodule count
            submodule_count = LearningSubmodules.query.filter_by(
                module_id=module.id, is_active=True
            ).count()
            
            # Get video count for this module
            video_count = db.session.query(VideoShorts).join(
                LearningSubmodules,
                func.cast(VideoShorts.submodule_id, db.Float) == LearningSubmodules.submodule_number
            ).filter(
                LearningSubmodules.module_id == module.id,
                VideoShorts.is_active == True
            ).count()
            
            module_dict = module.to_dict()
            module_dict['submodule_count'] = submodule_count
            module_dict['video_count'] = video_count
            modules_data.append(module_dict)
        
        # Calculate overall statistics
        total_modules = LearningModules.query.count()
        total_submodules = LearningSubmodules.query.filter_by(is_active=True).count()
        total_videos = VideoShorts.query.filter_by(is_active=True).count()
        
        # Calculate average completion rate
        avg_completion = db.session.query(func.avg(LearningModules.completion_rate)).scalar() or 0
        
        stats = {
            'total_modules': total_modules,
            'total_submodules': total_submodules,
            'total_videos': total_videos,
            'avg_completion_rate': float(avg_completion)
        }
        
        return jsonify({
            'modules': modules_data,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting learning modules: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-modules', methods=['POST'])
@admin_required
def create_learning_module():
    """Create a new learning module"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'error': 'Module title is required'}), 400
            
        if not data.get('module_number'):
            return jsonify({'error': 'Module number is required'}), 400
        
        # Check if module number already exists
        existing = LearningModules.query.filter_by(
            module_number=data['module_number']
        ).first()
        if existing:
            return jsonify({'error': 'Module number already exists'}), 400
        
        # Create new module
        module = LearningModules(
            module_number=float(data['module_number']),
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            estimated_hours=data.get('estimated_hours'),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(module)
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Created learning module: {module.title} (#{module.module_number})"
        )
        
        return jsonify({
            'success': True,
            'message': 'Module created successfully',
            'module': module.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating learning module: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['GET'])
@admin_required
def get_learning_module(module_id):
    """Get a specific learning module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        return jsonify(module.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting learning module {module_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['PUT'])
@admin_required
def update_learning_module(module_id):
    """Update a learning module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'error': 'Module title is required'}), 400
            
        if not data.get('module_number'):
            return jsonify({'error': 'Module number is required'}), 400
        
        # Check if module number conflicts with another module
        if float(data['module_number']) != module.module_number:
            existing = LearningModules.query.filter(
                LearningModules.module_number == data['module_number'],
                LearningModules.id != module_id
            ).first()
            if existing:
                return jsonify({'error': 'Module number already exists'}), 400
        
        # Update module
        module.module_number = float(data['module_number'])
        module.title = data['title'].strip()
        module.description = data.get('description', '').strip() or None
        module.estimated_hours = data.get('estimated_hours')
        module.is_active = data.get('is_active', True)
        module.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Updated learning module: {module.title} (#{module.module_number})"
        )
        
        return jsonify({
            'success': True,
            'message': 'Module updated successfully',
            'module': module.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating learning module {module_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['DELETE'])
@admin_required
def delete_learning_module(module_id):
    """Delete a learning module and all associated content"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        
        # Store module info for logging
        module_info = f"{module.title} (#{module.module_number})"
        
        # Delete associated submodules and their videos
        submodules = LearningSubmodules.query.filter_by(module_id=module_id).all()
        for submodule in submodules:
            # Delete videos associated with this submodule
            videos = VideoShorts.query.filter(
                func.cast(VideoShorts.submodule_id, db.Float) == submodule.submodule_number
            ).all()
            for video in videos:
                # Delete video progress records
                UserShortsProgress.query.filter_by(shorts_id=video.id).delete()
                # Delete video file if it exists
                if video.file_path and os.path.exists(video.file_path):
                    try:
                        os.remove(video.file_path)
                    except OSError:
                        pass  # Continue even if file deletion fails
                db.session.delete(video)
            
            db.session.delete(submodule)
        
        # Delete the module itself
        db.session.delete(module)
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Deleted learning module: {module_info}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Module deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting learning module {module_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-modules/<int:module_id>/submodules', methods=['GET'])
@admin_required
def get_module_submodules(module_id):
    """Get submodules for a specific module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        
        submodules = LearningSubmodules.query.filter_by(
            module_id=module_id,
            is_active=True
        ).order_by(LearningSubmodules.submodule_number).all()
        
        submodules_data = []
        for submodule in submodules:
            submodule_dict = {
                'id': submodule.id,
                'submodule_number': submodule.submodule_number,
                'title': submodule.title,
                'description': submodule.description,
                'estimated_minutes': submodule.estimated_minutes,
                'has_video_shorts': submodule.has_video_shorts,
                'is_active': submodule.is_active
            }
            submodules_data.append(submodule_dict)
        
        return jsonify({
            'submodules': submodules_data
        })
        
    except Exception as e:
        logger.error(f"Error getting submodules for module {module_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/upload-video', methods=['POST'])
@admin_required
def upload_video():
    """Upload a video short to a submodule"""
    try:
        # Check if video file is present
        if 'video_file' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        video_file = request.files['video_file']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
        
        # Get form data
        module_id = request.form.get('module_id')
        submodule_id = request.form.get('submodule_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        sequence_order = request.form.get('sequence_order', 1)
        
        # Validation
        if not module_id or not submodule_id:
            return jsonify({'error': 'Module and submodule selection required'}), 400
            
        if not title:
            return jsonify({'error': 'Video title is required'}), 400
        
        # Verify module and submodule exist
        module = LearningModules.query.get(module_id)
        if not module:
            return jsonify({'error': 'Module not found'}), 404
            
        submodule = LearningSubmodules.query.get(submodule_id)
        if not submodule or submodule.module_id != int(module_id):
            return jsonify({'error': 'Submodule not found or does not belong to module'}), 404
        
        # Validate file type
        if not video_file.filename.lower().endswith('.mp4'):
            return jsonify({'error': 'Only MP4 video files are supported'}), 400
        
        # Create upload directory
        upload_dir = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'uploads'),
            'learning',
            f'{module.module_number}-{module.title.replace(" ", "_").lower()}',
            f'{submodule.submodule_number}-{submodule.title.replace(" ", "_").lower()}',
            'videos'
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        original_filename = secure_filename(video_file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{original_filename}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        video_file.save(file_path)
        
        # Get file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Create video record
        video_short = VideoShorts(
            submodule_id=str(submodule.submodule_number),
            title=title,
            description=description or None,
            filename=filename,
            file_path=file_path,
            sequence_order=int(sequence_order),
            file_size_mb=file_size_mb,
            aspect_ratio='9:16',  # Default for shorts
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(video_short)
        
        # Update submodule to indicate it has video shorts
        submodule.has_video_shorts = True
        submodule.shorts_count = VideoShorts.query.filter(
            func.cast(VideoShorts.submodule_id, db.Float) == submodule.submodule_number
        ).count() + 1  # +1 for the one we're adding
        
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Uploaded video: {title} to module {module.title}, submodule {submodule.title}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'video': {
                'id': video_short.id,
                'title': video_short.title,
                'filename': video_short.filename,
                'file_size_mb': video_short.file_size_mb
            }
        })
        
    except Exception as e:
        db.session.rollback()
        # Clean up uploaded file if database operation failed
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"Error uploading video: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Learning Modules API Routes
@admin_bp.route('/api/learning-modules')
@admin_required
def api_learning_modules():
    """API endpoint for learning modules with filtering and stats"""
    try:
        # Import here to avoid circular imports
        from ..models import LearningModules, LearningSubmodules, VideoShorts
        
        # Get filter parameters
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # Build query
        query = LearningModules.query
        
        # Apply filters
        if status == 'active':
            query = query.filter(LearningModules.is_active == True)
        elif status == 'inactive':
            query = query.filter(LearningModules.is_active == False)
            
        if search:
            query = query.filter(
                LearningModules.title.contains(search) |
                LearningModules.description.contains(search)
            )
        
        # Get modules ordered by module_number
        modules = query.order_by(LearningModules.module_number).all()
        
        # Format modules data with counts
        modules_data = []
        for module in modules:
            # Count submodules
            submodule_count = LearningSubmodules.query.filter_by(module_id=module.id, is_active=True).count()
            
            # Count videos (through submodules)
            video_count = db.session.query(VideoShorts).join(
                LearningSubmodules, 
                VideoShorts.submodule_id == LearningSubmodules.submodule_number
            ).filter(
                LearningSubmodules.module_id == module.id,
                VideoShorts.is_active == True
            ).count()
            
            modules_data.append({
                'id': module.id,
                'module_number': module.module_number,
                'title': module.title,
                'description': module.description,
                'estimated_hours': module.estimated_hours,
                'is_active': module.is_active,
                'completion_rate': module.completion_rate or 0,
                'submodule_count': submodule_count,
                'video_count': video_count,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'updated_at': module.updated_at.isoformat() if module.updated_at else None
            })
        
        # Calculate stats
        total_modules = len(modules)
        total_submodules = LearningSubmodules.query.filter_by(is_active=True).count()
        total_videos = VideoShorts.query.filter_by(is_active=True).count()
        avg_completion_rate = db.session.query(func.avg(LearningModules.completion_rate)).scalar() or 0
        
        stats = {
            'total_modules': total_modules,
            'total_submodules': total_submodules,
            'total_videos': total_videos,
            'avg_completion_rate': float(avg_completion_rate) if avg_completion_rate else 0
        }
        
        return jsonify({
            'modules': modules_data,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in api_learning_modules: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules', methods=['POST'])
@admin_required
def api_create_learning_module():
    """Create a new learning module"""
    try:
        from ..models import LearningModules
        
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'}), 400
            
        if not data.get('module_number'):
            return jsonify({'success': False, 'message': 'Module number is required'}), 400
        
        # Check if module number already exists
        existing = LearningModules.query.filter_by(module_number=data['module_number']).first()
        if existing:
            return jsonify({'success': False, 'message': 'Module number already exists'}), 400
        
        # Create new module
        module = LearningModules(
            module_number=data['module_number'],
            title=data['title'],
            description=data.get('description', ''),
            estimated_hours=data.get('estimated_hours'),
            is_active=True
        )
        
        db.session.add(module)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Module created successfully',
            'module': {
                'id': module.id,
                'module_number': module.module_number,
                'title': module.title
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating learning module: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>')
@admin_required
def api_get_learning_module(module_id):
    """Get a specific learning module"""
    try:
        from ..models import LearningModules
        
        module = LearningModules.query.get_or_404(module_id)
        
        return jsonify({
            'id': module.id,
            'module_number': module.module_number,
            'title': module.title,
            'description': module.description,
            'estimated_hours': module.estimated_hours,
            'is_active': module.is_active,
            'completion_rate': module.completion_rate or 0,
            'created_at': module.created_at.isoformat() if module.created_at else None,
            'updated_at': module.updated_at.isoformat() if module.updated_at else None
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting learning module: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['PUT'])
@admin_required
def api_update_learning_module(module_id):
    """Update a learning module"""
    try:
        from ..models import LearningModules
        
        module = LearningModules.query.get_or_404(module_id)
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'}), 400
            
        # Check if module number conflicts (excluding current module)
        if data.get('module_number') and data['module_number'] != module.module_number:
            existing = LearningModules.query.filter(
                LearningModules.module_number == data['module_number'],
                LearningModules.id != module_id
            ).first()
            if existing:
                return jsonify({'success': False, 'message': 'Module number already exists'}), 400
        
        # Update module
        if 'module_number' in data:
            module.module_number = data['module_number']
        if 'title' in data:
            module.title = data['title']
        if 'description' in data:
            module.description = data['description']
        if 'estimated_hours' in data:
            module.estimated_hours = data['estimated_hours']
        if 'is_active' in data:
            module.is_active = data['is_active']
            
        module.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Module updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating learning module: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['DELETE'])
@admin_required
def api_delete_learning_module(module_id):
    """Delete a learning module"""
    try:
        from ..models import LearningModules
        
        module = LearningModules.query.get_or_404(module_id)
        
        # In a production system, you might want to soft delete or check for dependencies
        db.session.delete(module)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Module deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting learning module: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>/submodules')
@admin_required
def api_get_module_submodules(module_id):
    """Get submodules for a specific module"""
    try:
        from ..models import LearningModules, LearningSubmodules
        
        module = LearningModules.query.get_or_404(module_id)
        submodules = LearningSubmodules.query.filter_by(
            module_id=module_id, 
            is_active=True
        ).order_by(LearningSubmodules.submodule_number).all()
        
        submodules_data = []
        for submodule in submodules:
            submodules_data.append({
                'id': submodule.id,
                'submodule_number': submodule.submodule_number,
                'title': submodule.title,
                'description': submodule.description,
                'estimated_minutes': submodule.estimated_minutes
            })
        
        return jsonify({
            'submodules': submodules_data
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting module submodules: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Marketing Email API Endpoints

@admin_bp.route('/api/marketing-recipients')
@admin_required
def get_marketing_recipients():
    """Get detailed recipient list for marketing email modal"""
    try:
        email_id = request.args.get('email_id')
        search = request.args.get('search', '').strip()
        subscription_filter = request.args.get('subscription', '')
        admin_filter = request.args.get('admin_filter', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if email_id:
            # Get recipients for specific email campaign
            email = MarketingEmail.query.get_or_404(email_id)
            recipients = MarketingEmailService.get_eligible_recipients(
                email.target_free_users,
                email.target_premium_users,
                email.target_pro_users,
                email.target_active_only
            )
        else:
            # Get all marketing-eligible recipients with basic targeting
            recipients = MarketingEmailService.get_eligible_recipients(
                target_free=True,
                target_premium=True,
                target_pro=True,
                target_active_only=False
            )
        
        # Apply additional filters
        filtered_recipients = []
        for user in recipients:
            # Search filter
            if search:
                search_match = (
                    search.lower() in (user.full_name or '').lower() or
                    search.lower() in user.email.lower()
                )
                if not search_match:
                    continue
            
            # Subscription filter
            if subscription_filter:
                user_subscription_tier = {
                    1: 'free',
                    2: 'premium',
                    3: 'pro'
                }.get(user.current_plan_id, 'free')
                
                if user_subscription_tier != subscription_filter:
                    continue
            
            # Admin filter
            if admin_filter:
                if admin_filter == 'admin' and not user.is_admin:
                    continue
                elif admin_filter == 'user' and user.is_admin:
                    continue
            
            filtered_recipients.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'subscription': {
                    1: 'free',
                    2: 'premium',
                    3: 'pro'
                }.get(user.current_plan_id, 'free'),
                'is_admin': user.is_admin
            })
        
        # If this is for the modal (no pagination requested), return all
        if 'page' not in request.args:
            return jsonify({
                'recipients': filtered_recipients,
                'count': len(filtered_recipients),
                'total_count': len(filtered_recipients)
            })
        
        # Pagination for API calls
        total_count = len(filtered_recipients)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_recipients = filtered_recipients[start_idx:end_idx]
        
        return jsonify({
            'recipients': paginated_recipients,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page,
                'has_next': end_idx < total_count,
                'has_prev': page > 1
            },
            'total_count': total_count
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in get_marketing_recipients: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/marketing-recipients/export')
@admin_required
def export_marketing_recipients():
    """Export marketing recipients as CSV or JSON"""
    try:
        email_id = request.args.get('email_id')
        format_type = request.args.get('format', 'csv').lower()
        search = request.args.get('search', '').strip()
        subscription_filter = request.args.get('subscription', '')
        admin_filter = request.args.get('admin_filter', '')
        
        if not email_id:
            return jsonify({'error': 'Email ID required'}), 400
        
        # Get recipients using the same logic as the modal
        email = MarketingEmail.query.get_or_404(email_id)
        recipients = MarketingEmailService.get_eligible_recipients(
            email.target_free_users,
            email.target_premium_users,
            email.target_pro_users,
            email.target_active_only
        )
        
        # Apply filters same as modal
        filtered_recipients = []
        for user in recipients:
            # Search filter
            if search:
                search_match = (
                    search.lower() in (user.full_name or '').lower() or
                    search.lower() in user.email.lower()
                )
                if not search_match:
                    continue
            
            # Subscription filter
            if subscription_filter and user.subscription_tier != subscription_filter:
                continue
            
            # Admin filter
            if admin_filter:
                if admin_filter == 'admin' and not user.is_admin:
                    continue
                elif admin_filter == 'user' and user.is_admin:
                    continue
            
            filtered_recipients.append({
                'full_name': user.full_name or 'N/A',
                'email': user.email,
                'subscription': user.subscription_tier or 'free',
                'account_type': 'Admin' if user.is_admin else 'User'
            })
        
        if format_type == 'csv':
            # Generate CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['full_name', 'email', 'subscription', 'account_type'])
            writer.writeheader()
            for recipient in filtered_recipients:
                writer.writerow(recipient)
            
            # Create response
            csv_data = output.getvalue()
            output.close()
            
            response = current_app.response_class(
                csv_data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=marketing_recipients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
            return response
            
        elif format_type == 'json':
            # Generate JSON
            json_data = {
                'export_date': datetime.now().isoformat(),
                'email_campaign_id': email_id,
                'total_recipients': len(filtered_recipients),
                'filters_applied': {
                    'search': search,
                    'subscription': subscription_filter,
                    'admin_filter': admin_filter
                },
                'recipients': filtered_recipients
            }
            
            response = current_app.response_class(
                json.dumps(json_data, indent=2),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=marketing_recipients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                }
            )
            return response
        
        else:
            return jsonify({'error': 'Invalid format. Use csv or json'}), 400
            
    except Exception as e:
        current_app.logger.error(f'Error in export_marketing_recipients: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/marketing-stats', methods=['GET'])
@admin_required
def api_marketing_stats():
    """API endpoint for marketing statistics"""
    try:
        stats = MarketingEmailService.get_marketing_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f'Error in api_marketing_stats: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/marketing-send', methods=['POST'])
@admin_required
def send_marketing_email():
    """Send marketing email campaign"""
    try:
        data = request.get_json()
        email_id = data.get('email_id')
        is_resend = data.get('resend', False)
        
        if not email_id:
            return jsonify({'success': False, 'error': 'Email ID required'}), 400
        
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
        
    except Exception as e:
        current_app.logger.error(f'Error in send_marketing_email: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/marketing-email/<int:email_id>/delete', methods=['DELETE'])
@admin_required
def delete_marketing_email(email_id):
    """Delete marketing email campaign"""
    try:
        email = MarketingEmail.query.get_or_404(email_id)
        
        # Store email info for logging
        email_title = email.title
        email_status = email.status
        
        # Check if email can be deleted
        if email.status == 'sending':
            return jsonify({
                'success': False, 
                'error': 'Cannot delete email that is currently being sent'
            }), 400
        
        # Delete related email logs first (foreign key constraint)
        MarketingEmailLog.query.filter_by(marketing_email_id=email_id).delete()
        
        # Delete the email
        db.session.delete(email)
        db.session.commit()
        
        # Log the deletion action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='marketing_email_delete',
            additional_info=json.dumps({
                'email_id': email_id,
                'email_title': email_title,
                'email_status': email_status
            })
        )
        
        return jsonify({
            'success': True, 
            'message': f'Marketing email "{email_title}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting marketing email {email_id}: {str(e)}')
        return jsonify({
            'success': False, 
            'error': 'Failed to delete marketing email'
        }), 500
# ========================================
# MARKETING AJAX API ENDPOINTS
# ========================================

@admin_bp.route('/api/marketing-emails', methods=['GET'])
@admin_required
def api_marketing_emails():
    """API endpoint for marketing emails with filtering, sorting, and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate per_page options
        if per_page not in [10, 20, 50, 100] and per_page != -1:
            per_page = 20
        
        # Build query
        query = MarketingEmail.query
        
        # Apply search filter
        if search:
            query = query.filter(
                MarketingEmail.title.contains(search) |
                MarketingEmail.subject.contains(search)
            )
        
        # Apply status filter
        if status:
            query = query.filter(MarketingEmail.status == status)
        
        # Apply sorting
        valid_sort_columns = ['id', 'title', 'subject', 'status', 'created_at', 'sent_at']
        if sort_by in valid_sort_columns:
            sort_column = getattr(MarketingEmail, sort_by)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(MarketingEmail.created_at.desc())
        
        # Get total count for stats
        total_count = query.count()
        
        # Apply pagination
        if per_page == -1:  # Show all
            emails = query.all()
            pages = 1
            has_prev = False
            has_next = False
            prev_num = None
            next_num = None
        else:
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            emails = paginated.items
            pages = paginated.pages
            has_prev = paginated.has_prev
            has_next = paginated.has_next
            prev_num = paginated.prev_num
            next_num = paginated.next_num
        
        # Format emails data
        emails_data = []
        for email in emails:
            emails_data.append({
                'id': email.id,
                'title': email.title,
                'subject': email.subject,
                'status': email.status,
                'recipients_count': email.recipients_count,
                'sent_count': email.sent_count,
                'failed_count': email.failed_count,
                'success_rate': (email.sent_count / email.recipients_count * 100) if email.recipients_count > 0 else 0,
                'created_at': email.created_at.strftime('%d.%m.%Y %H:%M') if email.created_at else '',
                'sent_at': email.sent_at.strftime('%d.%m.%Y %H:%M') if email.sent_at else None,
                'created_by': {
                    'id': email.created_by.id,
                    'username': email.created_by.username
                } if email.created_by else None
            })
        
        return jsonify({
            'success': True,
            'emails': emails_data,
            'pagination': {
                'page': page,
                'pages': pages,
                'per_page': per_page,
                'total': total_count,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_num': next_num,
                'prev_num': prev_num
            }
        })
        
    except Exception as e:
        logger.error(f'Error in api_marketing_emails: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/marketing-email/<int:email_id>', methods=['GET'])
@admin_required
def api_marketing_email_details(email_id):
    """Get detailed marketing email information"""
    try:
        email = MarketingEmail.query.get_or_404(email_id)
        
        return jsonify({
            'success': True,
            'email': {
                'id': email.id,
                'title': email.title,
                'subject': email.subject,
                'html_content': email.html_content,
                'status': email.status,
                'recipients_count': email.recipients_count,
                'sent_count': email.sent_count,
                'failed_count': email.failed_count,
                'target_free_users': email.target_free_users,
                'target_premium_users': email.target_premium_users,
                'target_pro_users': email.target_pro_users,
                'target_active_only': email.target_active_only,
                'created_at': email.created_at.isoformat() if email.created_at else None,
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'created_by': {
                    'id': email.created_by.id,
                    'username': email.created_by.username
                } if email.created_by else None
            }
        })
        
    except Exception as e:
        logger.error(f'Error in api_marketing_email_details: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/marketing-email/<int:email_id>/delete', methods=['DELETE'])
@admin_required
def api_delete_marketing_email(email_id):
    """Delete a marketing email campaign"""
    try:
        email = MarketingEmail.query.get_or_404(email_id)
        
        # Only allow deletion of drafts and failed campaigns
        if email.status not in ['draft', 'failed']:
            return jsonify({
                'success': False,
                'error': 'Only draft and failed campaigns can be deleted'
            }), 400
        
        # Delete associated logs first
        MarketingEmailLog.query.filter_by(marketing_email_id=email_id).delete()
        
        # Delete the email
        db.session.delete(email)
        db.session.commit()
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='marketing_email_delete',
            additional_info=json.dumps({
                'email_id': email_id,
                'title': email.title
            })
        )
        
        return jsonify({
            'success': True,
            'message': 'Marketing email deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in api_delete_marketing_email: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/reports/<int:report_id>')
@admin_required
def api_report_details(report_id):
    """Get detailed report information"""
    try:
        report = AdminReport.query.get_or_404(report_id)
        
        return jsonify({
            'report': {
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'report_type': report.report_type,
                'priority': report.priority,
                'status': report.status,
                'created_at': report.created_at.isoformat(),
                'additional_info': report.additional_info,
                'reported_by': {
                    'id': report.reported_by.id,
                    'username': report.reported_by.username
                } if report.reported_by else None,
                'assigned_to': {
                    'id': report.assigned_to.id,
                    'username': report.assigned_to.username
                } if report.assigned_to else None
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@admin_bp.route('/api/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def api_resolve_report(report_id):
    """Mark report as resolved"""
    try:
        report = AdminReport.query.get_or_404(report_id)
        report.status = 'resolved'
        
        db.session.commit()
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='report_resolve',
            target_user=None,
            additional_info=f'Report #{report_id}: {report.title}'
        )
        
        return jsonify({'success': True, 'message': 'Report resolved successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users')
@admin_required
def api_users():
    """API endpoint for users with filtering, sorting, and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        admin_status = request.args.get('admin_status', '')
        status = request.args.get('status', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = User.query
        
        # Apply filters
        if search:
            query = query.filter(
                User.username.contains(search) |
                User.email.contains(search) |
                User.full_name.contains(search)
            )
        
        if admin_status == 'admin':
            query = query.filter(User.is_admin == True)
        elif admin_status == 'user':
            query = query.filter(User.is_admin == False)
        
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Apply sorting
        if hasattr(User, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(User, sort_by).desc())
            else:
                query = query.order_by(getattr(User, sort_by))
        
        # Paginate
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        users_data = []
        for user in users.items:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_current_user': user.id == current_user.id
            })
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev,
                'next_num': users.next_num,
                'prev_num': users.prev_num
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/grant-admin', methods=['POST'])
@admin_required
def api_grant_admin(user_id):
    """Grant admin privileges to user"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot modify own privileges'}), 400
        
        if user.is_admin:
            return jsonify({'error': 'User already has admin privileges'}), 400
        
        user.is_admin = True
        db.session.commit()
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='grant_admin',
            additional_info=f'Admin privileges granted to {user.username}'
        )
        
        return jsonify({'success': True, 'message': f'Admin privileges granted to {user.username}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/revoke-admin', methods=['POST'])
@admin_required
def api_revoke_admin(user_id):
    """Revoke admin privileges from user"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot modify own privileges'}), 400
        
        if not user.is_admin:
            return jsonify({'error': 'User does not have admin privileges'}), 400
        
        user.is_admin = False
        db.session.commit()
        
        # Log the action
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='revoke_admin',
            additional_info=f'Admin privileges revoked from {user.username}'
        )
        
        return jsonify({'success': True, 'message': f'Admin privileges revoked from {user.username}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>')
@admin_required
def api_user_details(user_id):
    """API endpoint for getting detailed user information"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user progress if available
        user_progress = None
        try:
            from ..models import UserProgress
            user_progress = UserProgress.query.filter_by(user_id=user.id).first()
        except:
            pass
        
        # Format user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'total_xp': user.total_xp,
            'subscription_tier': user.subscription_tier,
            'current_plan_id': user.current_plan_id,
            'subscription_status': user.subscription_status,
            'profile_picture': user.profile_picture,
            'preferred_language': user.preferred_language,
            'is_current_user': user.id == current_user.id
        }
        
        # Add progress data if available
        if user_progress:
            user_data['progress'] = {
                'total_quizzes_taken': user_progress.total_quizzes_taken,
                'total_questions_answered': user_progress.total_questions_answered,
                'correct_answers': user_progress.correct_answers,
                'current_streak_days': user_progress.current_streak_days,
                'longest_streak_days': user_progress.longest_streak_days,
                'last_activity_date': user_progress.last_activity_date.isoformat() if user_progress.last_activity_date else None
            }
        
        return jsonify(user_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@admin_bp.route('/api/activity-logs')
@admin_required
def api_activity_logs():
    """API endpoint for activity logs with filtering, sorting, and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        search_column = request.args.get('search_column', 'all')
        action = request.args.get('action', '')
        time_range = request.args.get('time_range', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate per_page
        if per_page not in [20, 50, 100] and per_page != -1:
            per_page = 50
            
        # Build query
        query = AdminAuditLog.query
        
        # Apply search filters
        if search:
            search_filter = None
            if search_column == 'action':
                search_filter = AdminAuditLog.action.contains(search)
            elif search_column == 'target_user':
                query = query.join(User, AdminAuditLog.target_user_id == User.id, isouter=True)
                search_filter = User.username.contains(search)
            elif search_column == 'admin_user':
                query = query.join(User, AdminAuditLog.admin_user_id == User.id, isouter=True)
                search_filter = User.username.contains(search)
            elif search_column == 'ip_address':
                search_filter = AdminAuditLog.ip_address.contains(search)
            else:  # 'all'
                admin_user_alias = db.aliased(User)
                target_user_alias = db.aliased(User)
                query = query.join(admin_user_alias, AdminAuditLog.admin_user_id == admin_user_alias.id, isouter=True)
                query = query.join(target_user_alias, AdminAuditLog.target_user_id == target_user_alias.id, isouter=True)
                search_filter = (
                    AdminAuditLog.action.contains(search) |
                    AdminAuditLog.additional_info.contains(search) |
                    AdminAuditLog.ip_address.contains(search) |
                    admin_user_alias.username.contains(search) |
                    target_user_alias.username.contains(search)
                )
            
            if search_filter is not None:
                query = query.filter(search_filter)
        
        # Apply action filter
        if action:
            query = query.filter(AdminAuditLog.action == action)
        
        # Apply time range filter
        if time_range:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            if time_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(AdminAuditLog.created_at >= start_date)
            elif time_range == 'week':
                start_date = now - timedelta(days=7)
                query = query.filter(AdminAuditLog.created_at >= start_date)
            elif time_range == 'month':
                start_date = now - timedelta(days=30)
                query = query.filter(AdminAuditLog.created_at >= start_date)
        
        # Apply sorting
        if hasattr(AdminAuditLog, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(AdminAuditLog, sort_by).desc())
            else:
                query = query.order_by(getattr(AdminAuditLog, sort_by))
        
        # Handle "All" option for per_page
        if per_page == -1:
            logs = query.all()
            # Create a mock pagination object
            class MockPagination:
                def __init__(self, items):
                    self.items = items
                    self.page = 1
                    self.pages = 1
                    self.per_page = len(items)
                    self.total = len(items)
                    self.has_next = False
                    self.has_prev = False
                    self.next_num = None
                    self.prev_num = None
            
            logs = MockPagination(logs)
        else:
            # Paginate
            logs = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
        
        # Format response
        logs_data = []
        for log in logs.items:
            logs_data.append({
                'id': log.id,
                'action': log.action,
                'created_at': log.created_at.strftime('%d.%m.%Y %H:%M:%S') if log.created_at else '',
                'ip_address': log.ip_address or '-',
                'user_agent': log.user_agent or '',
                'additional_info': log.additional_info or '',
                'admin_user': {
                    'id': log.admin_user.id,
                    'username': log.admin_user.username
                } if log.admin_user else {'id': None, 'username': 'System'},
                'target_user': {
                    'id': log.target_user.id,
                    'username': log.target_user.username
                } if log.target_user else {'id': None, 'username': 'Unknown'}
            })
        
        return jsonify({
            'logs': logs_data,
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev,
                'next_num': logs.next_num,
                'prev_num': logs.prev_num
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in api_activity_logs: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/audit-logs')
@admin_required
def api_audit_logs():
    """API endpoint for audit logs with filtering, sorting, and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        action = request.args.get('action', '')
        ip = request.args.get('ip', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = AdminAuditLog.query
        
        # Apply filters
        if search:
            query = query.join(User, AdminAuditLog.admin_user_id == User.id, isouter=True)
            query = query.filter(
                AdminAuditLog.action.contains(search) |
                AdminAuditLog.additional_info.contains(search) |
                User.username.contains(search)
            )
        
        if action:
            query = query.filter(AdminAuditLog.action == action)
        
        if ip:
            query = query.filter(AdminAuditLog.ip_address.contains(ip))
        
        # Apply sorting
        if hasattr(AdminAuditLog, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(AdminAuditLog, sort_by).desc())
            else:
                query = query.order_by(getattr(AdminAuditLog, sort_by))
        
        # Paginate
        logs = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        logs_data = []
        for log in logs.items:
            logs_data.append({
                'id': log.id,
                'action': log.action,
                'created_at': log.created_at.isoformat(),
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'additional_info': log.additional_info,
                'admin_user': {
                    'id': log.admin_user.id,
                    'username': log.admin_user.username,
                    'is_current_user': log.admin_user.id == current_user.id
                } if log.admin_user else None,
                'target_user': {
                    'id': log.target_user.id,
                    'username': log.target_user.username
                } if log.target_user else None
            })
        
        return jsonify({
            'logs': logs_data,
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev,
                'next_num': logs.next_num,
                'prev_num': logs.prev_num
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== LEARNING MODULES ADMIN API ROUTES =====
# Add this section to the very end of app/admin/routes.py

@admin_bp.route('/api/learning-modules')
@admin_required
def admin_api_learning_modules():
    """Get all learning modules with statistics for admin interface"""
    try:
        modules = LearningModules.query.order_by(LearningModules.module_number).all()
        
        modules_data = []
        for module in modules:
            # Get submodule count
            submodule_count = LearningSubmodules.query.filter_by(
                module_id=module.id, is_active=True
            ).count()
            
            # Get video shorts count
            video_count = db.session.query(VideoShorts).join(
                LearningSubmodules, 
                VideoShorts.submodule_id == LearningSubmodules.submodule_number
            ).filter(
                LearningSubmodules.module_id == module.id,
                VideoShorts.is_active == True
            ).count()
            
            modules_data.append({
                'id': module.id,
                'module_number': module.module_number,
                'title': module.title,
                'description': module.description,
                'estimated_hours': module.estimated_hours,
                'submodule_count': submodule_count,
                'video_count': video_count,
                'completion_rate': module.completion_rate or 0,
                'is_active': module.is_active,
                'has_content_directory': bool(module.content_directory),
                'last_updated': module.last_content_update.isoformat() if module.last_content_update else None,
                'created_at': module.created_at.isoformat() if module.created_at else None
            })
        
        # Calculate statistics
        total_modules = len(modules_data)
        total_submodules = sum(m['submodule_count'] for m in modules_data)
        total_videos = sum(m['video_count'] for m in modules_data)
        avg_completion = sum(m['completion_rate'] for m in modules_data) / total_modules if total_modules > 0 else 0
        
        return jsonify({
            'modules': modules_data,
            'stats': {
                'total_modules': total_modules,
                'total_submodules': total_submodules,
                'total_videos': total_videos,
                'avg_completion_rate': avg_completion
            }
        })
        
    except Exception as e:
        logger.error(f'Error in admin_api_learning_modules: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules', methods=['POST'])
@admin_required
def admin_create_learning_module():
    """Create a new learning module"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get next module number if not provided
        module_number = data.get('module_number')
        if not module_number:
            last_module = LearningModules.query.order_by(LearningModules.module_number.desc()).first()
            module_number = (last_module.module_number if last_module else 0) + 1
        
        # Create module
        module = LearningModules(
            module_number=float(module_number),
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            estimated_hours=float(data.get('estimated_hours', 0)) if data.get('estimated_hours') else None,
            prerequisites=json.dumps(data.get('prerequisites', [])),
            learning_objectives=json.dumps(data.get('learning_objectives', [])),
            is_active=True,
            ai_generated=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(module)
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user, 'create_learning_module', 
            additional_info=f'Created module: {module.title}'
        )
        
        return jsonify({
            'success': True, 
            'module_id': module.id,
            'message': f'Module "{module.title}" created successfully'
        })
        
    except Exception as e:
        logger.error(f'Error creating learning module: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>')
@admin_required
def admin_get_learning_module(module_id):
    """Get a specific learning module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        
        return jsonify({
            'id': module.id,
            'module_number': module.module_number,
            'title': module.title,
            'description': module.description,
            'estimated_hours': module.estimated_hours,
            'prerequisites': module.get_prerequisites_list() if hasattr(module, 'get_prerequisites_list') else [],
            'learning_objectives': module.get_learning_objectives_list() if hasattr(module, 'get_learning_objectives_list') else [],
            'is_active': module.is_active,
            'content_directory': module.content_directory,
            'created_at': module.created_at.isoformat() if module.created_at else None,
            'updated_at': module.updated_at.isoformat() if module.updated_at else None
        })
        
    except Exception as e:
        logger.error(f'Error getting learning module {module_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['PUT'])
@admin_required
def admin_update_learning_module(module_id):
    """Update an existing learning module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data and data['title'].strip():
            module.title = data['title'].strip()
        if 'description' in data:
            module.description = data['description'].strip()
        if 'estimated_hours' in data:
            module.estimated_hours = float(data['estimated_hours']) if data['estimated_hours'] else None
        if 'module_number' in data:
            module.module_number = float(data['module_number'])
        if 'prerequisites' in data:
            module.prerequisites = json.dumps(data['prerequisites'])
        if 'learning_objectives' in data:
            module.learning_objectives = json.dumps(data['learning_objectives'])
        if 'is_active' in data:
            module.is_active = bool(data['is_active'])
        
        module.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user, 'update_learning_module',
            additional_info=f'Updated module: {module.title}'
        )
        
        return jsonify({
            'success': True,
            'message': f'Module "{module.title}" updated successfully'
        })
        
    except Exception as e:
        logger.error(f'Error updating learning module {module_id}: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>', methods=['DELETE'])
@admin_required
def admin_delete_learning_module(module_id):
    """Delete a learning module and its content"""
    try:
        from ..services.file_upload import FileUploadService
        
        module = LearningModules.query.get_or_404(module_id)
        module_title = module.title
        
        # Delete content files and directories
        FileUploadService.delete_content('module', module_id)
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user, 'delete_learning_module',
            additional_info=f'Deleted module: {module_title}'
        )
        
        return jsonify({
            'success': True,
            'message': f'Module "{module_title}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f'Error deleting learning module {module_id}: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-modules/<int:module_id>/submodules')
@admin_required
def admin_get_module_submodules(module_id):
    """Get all submodules for a specific module"""
    try:
        module = LearningModules.query.get_or_404(module_id)
        submodules = LearningSubmodules.query.filter_by(
            module_id=module_id
        ).order_by(LearningSubmodules.submodule_number).all()
        
        submodules_data = []
        for submodule in submodules:
            # Count video shorts for this submodule
            video_count = VideoShorts.query.filter_by(
                submodule_id=submodule.submodule_number,
                is_active=True
            ).count()
            
            submodules_data.append({
                'id': submodule.id,
                'submodule_number': submodule.submodule_number,
                'title': submodule.title,
                'description': submodule.description,
                'estimated_minutes': submodule.estimated_minutes,
                'difficulty_level': submodule.difficulty_level,
                'has_quiz': submodule.has_quiz,
                'has_video_shorts': submodule.has_video_shorts,
                'video_count': video_count,
                'is_active': submodule.is_active,
                'has_content': bool(submodule.content_file_path),
                'has_summary': bool(submodule.summary_file_path),
                'last_updated': submodule.last_content_update.isoformat() if submodule.last_content_update else None
            })
        
        return jsonify({
            'module': {
                'id': module.id,
                'title': module.title,
                'module_number': module.module_number
            },
            'submodules': submodules_data
        })
        
    except Exception as e:
        logger.error(f'Error getting submodules for module {module_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/upload-video', methods=['POST'])
@admin_required
def admin_upload_video():
    """Upload video file for learning modules"""
    try:
        from ..services.file_upload import FileUploadService
        
        if 'video_file' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data
        submodule_id = request.form.get('submodule_id')
        if not submodule_id:
            return jsonify({'error': 'Submodule ID is required'}), 400
        
        try:
            submodule_id = int(submodule_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid submodule ID'}), 400
        
        if not FileUploadService.allowed_file(video_file.filename, 'video'):
            return jsonify({'error': 'Invalid video format. Only MP4, MOV, AVI, MKV allowed.'}), 400
        
        if not FileUploadService.validate_file_size(video_file, 'video'):
            return jsonify({'error': 'Video file too large. Maximum size is 300MB.'}), 400
        
        # Get video metadata from form
        video_metadata = {
            'title': request.form.get('title', 'Untitled Video').strip(),
            'description': request.form.get('description', '').strip(),
            'duration_seconds': int(request.form.get('duration_seconds', 60)),
            'difficulty_level': int(request.form.get('difficulty_level', 1))
        }
        
        if not video_metadata['title']:
            return jsonify({'error': 'Video title is required'}), 400
        
        # Upload video
        video_id = FileUploadService.upload_video_short(submodule_id, video_file, video_metadata)
        
        # Log admin action
        submodule = LearningSubmodules.query.get(submodule_id)
        AdminSecurityService.log_admin_action(
            current_user, 'upload_learning_video',
            additional_info=f'Uploaded video "{video_metadata["title"]}" for submodule: {submodule.title if submodule else submodule_id}'
        )
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'message': 'Video uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f'Error uploading video: {str(e)}')
        return jsonify({'error': str(e)}), 500
    
# Add these routes to your app/admin/routes.py file

@admin_bp.route('/api/learning-modules/<int:module_id>/upload-yaml', methods=['POST'])
@admin_required
def upload_module_yaml(module_id):
    """Upload module.yaml file for a learning module"""
    try:
        # Check if YAML file is present
        if 'yaml_file' not in request.files:
            return jsonify({'error': 'No YAML file provided'}), 400
            
        yaml_file = request.files['yaml_file']
        if yaml_file.filename == '':
            return jsonify({'error': 'No YAML file selected'}), 400
        
        # Validate file type
        if not yaml_file.filename.lower().endswith(('.yaml', '.yml')):
            return jsonify({'error': 'Only YAML files (.yaml, .yml) are supported'}), 400
        
        # Verify module exists
        module = LearningModules.query.get_or_404(module_id)
        
        # Read and validate YAML content
        try:
            yaml_content = yaml_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'Invalid file encoding. Please use UTF-8'}), 400
        
        # Use FileUploadService to upload YAML
        from ..services.file_upload import FileUploadService
        FileUploadService.upload_module_yaml(module_id, yaml_content)
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Uploaded module.yaml for module: {module.title} (#{module.module_number})"
        )
        
        return jsonify({
            'success': True,
            'message': 'Module YAML uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading module YAML for module {module_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-submodules/<int:submodule_id>/upload-content', methods=['POST'])
@admin_required
def upload_submodule_content(submodule_id):
    """Upload long.md or short.md content for a submodule"""
    try:
        # Check if content file is present
        if 'content_file' not in request.files:
            return jsonify({'error': 'No content file provided'}), 400
            
        content_file = request.files['content_file']
        if content_file.filename == '':
            return jsonify({'error': 'No content file selected'}), 400
        
        # Get content type from form data
        content_type = request.form.get('content_type')
        if content_type not in ['long', 'short']:
            return jsonify({'error': 'Content type must be "long" or "short"'}), 400
        
        # Validate file type
        if not content_file.filename.lower().endswith('.md'):
            return jsonify({'error': 'Only Markdown files (.md) are supported'}), 400
        
        # Verify submodule exists
        submodule = LearningSubmodules.query.get_or_404(submodule_id)
        
        # Read markdown content
        try:
            markdown_content = content_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'Invalid file encoding. Please use UTF-8'}), 400
        
        # Use FileUploadService to upload markdown content
        from ..services.file_upload import FileUploadService
        FileUploadService.upload_markdown_content(submodule_id, content_type, markdown_content)
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Uploaded {content_type}.md for submodule: {submodule.title} (#{submodule.submodule_number})"
        )
        
        return jsonify({
            'success': True,
            'message': f'{content_type.capitalize()} content uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading content for submodule {submodule_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/learning-submodules/<int:submodule_id>/upload-metadata', methods=['POST'])
@admin_required
def upload_submodule_metadata(submodule_id):
    """Upload metadata.yaml file for a submodule"""
    try:
        # Check if metadata file is present
        if 'content_file' not in request.files:
            return jsonify({'error': 'No metadata file provided'}), 400
            
        metadata_file = request.files['content_file']
        if metadata_file.filename == '':
            return jsonify({'error': 'No metadata file selected'}), 400
        
        # Validate file type
        if not metadata_file.filename.lower().endswith(('.yaml', '.yml')):
            return jsonify({'error': 'Only YAML files (.yaml, .yml) are supported'}), 400
        
        # Verify submodule exists
        submodule = LearningSubmodules.query.get_or_404(submodule_id)
        
        # Read and validate YAML content
        try:
            metadata_content = metadata_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'Invalid file encoding. Please use UTF-8'}), 400
        
        # Use FileUploadService to upload metadata
        from ..services.file_upload import FileUploadService
        FileUploadService.upload_submodule_metadata(submodule_id, metadata_content)
        
        # Log admin action
        AdminSecurityService.log_admin_action(
            current_user,
            f"Uploaded metadata.yaml for submodule: {submodule.title} (#{submodule.submodule_number})"
        )
        
        return jsonify({
            'success': True,
            'message': 'Metadata uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading metadata for submodule {submodule_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/export-content', methods=['GET'])
@admin_required
def export_learning_content():
    """Export learning content in various formats"""
    try:
        # Get export parameters
        export_type = request.args.get('type', 'all')  # 'all' or 'module'
        export_format = request.args.get('format', 'zip')  # 'zip' or 'json'
        module_id = request.args.get('module_id')
        
        # Get include options
        include_videos = request.args.get('include_videos', 'false').lower() == 'true'
        include_markdown = request.args.get('include_markdown', 'false').lower() == 'true'
        include_yaml = request.args.get('include_yaml', 'false').lower() == 'true'
        include_progress = request.args.get('include_progress', 'false').lower() == 'true'
        
        # Validation
        if export_type == 'module' and not module_id:
            return jsonify({'error': 'Module ID required for module export'}), 400
        
        if export_type == 'module':
            module = LearningModules.query.get_or_404(module_id)
            modules = [module]
            export_name = f"module_{module.module_number}_{module.title}"
        else:
            modules = LearningModules.query.filter_by(is_active=True).all()
            export_name = "all_learning_content"
        
        # Sanitize export name for filename
        import re
        export_name = re.sub(r'[^\w\-_.]', '_', export_name)
        
        if export_format == 'json':
            # JSON Export - Database data only
            export_data = {
                'export_info': {
                    'exported_at': datetime.utcnow().isoformat(),
                    'exported_by': current_user.username,
                    'export_type': export_type,
                    'include_options': {
                        'videos': include_videos,
                        'markdown': include_markdown,
                        'yaml': include_yaml,
                        'progress': include_progress
                    }
                },
                'modules': []
            }
            
            for module in modules:
                module_data = {
                    'id': module.id,
                    'module_number': module.module_number,
                    'title': module.title,
                    'description': module.description,
                    'estimated_hours': module.estimated_hours,
                    'submodules': []
                }
                
                # Get submodules
                submodules = LearningSubmodules.query.filter_by(
                    module_id=module.id, 
                    is_active=True
                ).all()
                
                for submodule in submodules:
                    submodule_data = {
                        'id': submodule.id,
                        'submodule_number': submodule.submodule_number,
                        'title': submodule.title,
                        'description': submodule.description,
                        'estimated_minutes': submodule.estimated_minutes
                    }
                    
                    # Add video data if requested
                    if include_videos:
                        videos = VideoShorts.query.filter(
                            func.cast(VideoShorts.submodule_id, db.Float) == submodule.submodule_number,
                            VideoShorts.is_active == True
                        ).all()
                        submodule_data['videos'] = [{
                            'id': video.id,
                            'title': video.title,
                            'description': video.description,
                            'filename': video.filename,
                            'duration_seconds': video.duration_seconds,
                            'sequence_order': video.sequence_order
                        } for video in videos]
                    
                    module_data['submodules'].append(submodule_data)
                
                export_data['modules'].append(module_data)
            
            # Add user progress if requested
            if include_progress:
                progress_data = UserShortsProgress.query.all()
                export_data['user_progress'] = [{
                    'user_id': p.user_id,
                    'shorts_id': p.shorts_id,
                    'watch_status': p.watch_status,
                    'watch_percentage': p.watch_percentage,
                    'completed_at': p.completed_at.isoformat() if p.completed_at else None
                } for p in progress_data]
            
            # Create JSON response
            output = BytesIO()
            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            output.write(json_content.encode('utf-8'))
            output.seek(0)
            
            # Log export action
            AdminSecurityService.log_admin_action(
                current_user,
                f"Exported learning content (JSON): {export_type}"
            )
            
            return send_file(
                output,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'{export_name}.json'
            )
        
        else:
            # ZIP Export - Files and data
            import zipfile
            import tempfile
            
            # Create temporary file for ZIP
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                learning_base = os.path.join(current_app.root_path, '..', 'learning')
                
                for module in modules:
                    if not module.content_directory:
                        continue
                    
                    module_path = os.path.join(learning_base, module.content_directory)
                    if not os.path.exists(module_path):
                        continue
                    
                    # Add module files to ZIP
                    for root, dirs, files in os.walk(module_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            # Check include options
                            if file.endswith('.yaml') and not include_yaml:
                                continue
                            if file.endswith('.md') and not include_markdown:
                                continue
                            if file.endswith('.mp4') and not include_videos:
                                continue
                            
                            # Add file to ZIP with relative path
                            arcname = os.path.relpath(file_path, learning_base)
                            zipf.write(file_path, arcname)
                
                # Add database export as JSON
                if include_progress or any([include_videos, include_markdown, include_yaml]):
                    # Create simplified database export
                    db_export = {
                        'modules': [{
                            'id': m.id,
                            'module_number': m.module_number,
                            'title': m.title,
                            'description': m.description
                        } for m in modules]
                    }
                    
                    db_json = json.dumps(db_export, ensure_ascii=False, indent=2)
                    zipf.writestr('database_export.json', db_json.encode('utf-8'))
            
            # Log export action
            AdminSecurityService.log_admin_action(
                current_user,
                f"Exported learning content (ZIP): {export_type}"
            )
            
            # Send ZIP file
            return send_file(
                temp_zip.name,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'{export_name}.zip'
            )
        
    except Exception as e:
        logger.error(f"Error exporting learning content: {str(e)}")
        return jsonify({'error': str(e)}), 500