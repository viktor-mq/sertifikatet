# app/auth/routes.py
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Query
from . import auth_bp
from .. import db
from ..models import User, UserProgress, QuizSession
from flask_login import login_user, logout_user, login_required, current_user
from ..utils.email import (send_verification_email, send_password_reset_email, 
                          verify_email_token, verify_reset_token, send_welcome_email)
from .utils import validate_password


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Check if email is verified
            if not user.is_verified:
                flash('Du må bekrefte e-postadressen din før du kan logge inn. Sjekk innboksen din.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash(f'Velkommen tilbake, {user.full_name or user.username}!', 'success')
            # Redirect to dashboard or intended page
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Ugyldig brukernavn eller passord', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        # Get additional form data
        terms_accepted = request.form.get('terms')
        privacy_accepted = request.form.get('privacy')
        marketing_consent = request.form.get('marketing')
        
        # Validate inputs
        if not all([username, email, password]):
            flash('Alle felt må fylles ut', 'error')
            return redirect(url_for('auth.register'))
        
        # Validate required legal agreements (GDPR compliance)
        if not terms_accepted:
            flash('Du må godta vilkårene for bruk for å opprette en konto', 'error')
            return redirect(url_for('auth.register'))
            
        if not privacy_accepted:
            flash('Du må bekrefte at du har lest personvernerklæringen', 'error')
            return redirect(url_for('auth.register'))
        
        # Validate password requirements
        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return redirect(url_for('auth.register'))
            
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Brukernavnet er allerede tatt', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('E-postadressen er allerede registrert', 'error')
            return redirect(url_for('auth.register'))
        
        # Get default free subscription plan
        from ..payment_models import SubscriptionPlan

        free_plan = SubscriptionPlan.query.filter_by(name='free').first()
        if not free_plan:
            flash('Registreringsfeil: Gratis plan ikke funnet. Kontakt support.', 'error')
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            subscription_tier='free',  # Legacy field
            current_plan_id=free_plan.id  # Correct field
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create user progress record
        user_progress = UserProgress(user_id=user.id)
        db.session.add(user_progress)
        
        # Create notification preferences with marketing consent
        from ..notification_models import UserNotificationPreferences
        notification_prefs = UserNotificationPreferences(
            user_id=user.id,
            marketing_emails=bool(marketing_consent),  # Explicit consent for marketing
            partner_offers=bool(marketing_consent)     # Same consent applies to partner offers
        )
        db.session.add(notification_prefs)
        
        db.session.commit()
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registrering vellykket! Vi har sendt en bekreftelse til din e-postadresse. '
              'Vennligst sjekk innboksen din for å aktivere kontoen.', 'success')
        
        # Track user registration event for analytics
        return render_template('auth/registration_success.html', 
                             user_data={
                                 'user_id': user.id,
                                 'username': user.username,
                                 'marketing_consent': bool(marketing_consent)
                             })
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Du har blitt logget ut. Vi sees!', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = current_user
    
    # Get user progress and statistics
    progress = user.progress
    recent_sessions = (
        QuizSession.query
        .filter_by(user_id=current_user.id)
        .order_by(QuizSession.completed_at.desc())
        .limit(5)
        .all()
    )
    achievements = user.achievements
    
    # Get subscription information
    from ..services.payment_service import SubscriptionService, UsageLimitService
    subscription_stats = SubscriptionService.get_subscription_stats(current_user.id)
    usage_stats = UsageLimitService.get_usage_stats(current_user.id)
    
    # Calculate statistics
    total_score = 0
    if progress and progress.total_questions_answered > 0:
        total_score = (progress.correct_answers / progress.total_questions_answered) * 100
    
    return render_template('auth/profile.html', 
                         user=user, 
                         progress=progress,
                         recent_sessions=recent_sessions,
                         achievements=achievements,
                         subscription_stats=subscription_stats,
                         usage_stats=usage_stats,
                         total_score=total_score)


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify email address with token"""
    email = verify_email_token(token)
    
    if not email:
        flash('Bekreftelseslenken er ugyldig eller utløpt.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Ingen bruker funnet med denne e-postadressen.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('E-postadressen din er allerede bekreftet.', 'info')
        return redirect(url_for('auth.login'))
    
    # Verify the user
    user.is_verified = True
    db.session.commit()
    
    # Send welcome email
    send_welcome_email(user)
    
    flash('E-postadressen din er nå bekreftet! Du kan logge inn.', 'success')
    
    # Track email verification completion for analytics
    return render_template('auth/verification_success.html', 
                         user_data={
                             'user_id': user.id,
                             'username': user.username
                         })


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    # If user is already logged in, redirect them
    if current_user.is_authenticated:
        flash('Du er allerede innlogget. Bruk endre passord-funksjonen i profilen din.', 'info')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        # Always show success message to prevent email enumeration
        flash('Hvis denne e-postadressen er registrert, vil du motta en e-post '
              'med instruksjoner for å tilbakestille passordet.', 'info')
        
        if user:
            send_password_reset_email(user)
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # If user is already logged in, redirect them
    if current_user.is_authenticated:
        flash('Du er allerede innlogget. Bruk endre passord-funksjonen i profilen din.', 'info')
        return redirect(url_for('auth.profile'))
    
    email = verify_reset_token(token)
    
    if not email:
        flash('Tilbakestillingslenken er ugyldig eller utløpt.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Ingen bruker funnet.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate password requirements
        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passordene er ikke like.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        flash('Passordet ditt har blitt oppdatert! Du kan nå logge inn.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/resend-verification')
def resend_verification():
    """Resend verification email"""
    if current_user.is_authenticated:
        if current_user.is_verified:
            flash('E-postadressen din er allerede bekreftet.', 'info')
        else:
            send_verification_email(current_user)
            flash('En ny bekreftelsese-post har blitt sendt.', 'success')
    else:
        flash('Du må logge inn før du kan be om ny bekreftelse.', 'error')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Nåværende passord er feil.', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        password_errors = validate_password(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Passordene er ikke like.', 'error')
            return render_template('auth/change_password.html')
        
        if current_password == new_password:
            flash('Nytt passord kan ikke være det samme som det gamle.', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Passordet ditt har blitt oppdatert!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')


@auth_bp.route('/notification-settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Manage user notification preferences"""
    from ..notification_models import UserNotificationPreferences
    
    # Get or create user preferences
    preferences = UserNotificationPreferences.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Create preferences if they don't exist
        if not preferences:
            preferences = UserNotificationPreferences(user_id=current_user.id)
            db.session.add(preferences)
        
        # Update preferences from form data
        preferences.daily_reminders = bool(request.form.get('daily_reminders'))
        preferences.weekly_summary = bool(request.form.get('weekly_summary'))
        preferences.achievement_notifications = bool(request.form.get('achievement_notifications'))
        preferences.streak_lost_reminders = bool(request.form.get('streak_lost_reminders'))
        preferences.study_tips = bool(request.form.get('study_tips'))
        preferences.new_features = bool(request.form.get('new_features'))
        preferences.progress_milestones = bool(request.form.get('progress_milestones'))
        preferences.marketing_emails = bool(request.form.get('marketing_emails'))
        preferences.partner_offers = bool(request.form.get('partner_offers'))
        
        # Update frequency and timing
        preferences.quiz_reminder_frequency = request.form.get('quiz_reminder_frequency', 'daily')
        preferences.timezone = request.form.get('timezone', 'Europe/Oslo')
        
        # Handle time input
        reminder_time_str = request.form.get('reminder_time')
        if reminder_time_str:
            try:
                preferences.reminder_time = datetime.strptime(reminder_time_str, '%H:%M').time()
            except ValueError:
                flash('Ugyldig tidsformat. Bruker standard tid 18:00.', 'warning')
                preferences.reminder_time = datetime.strptime('18:00', '%H:%M').time()
        
        db.session.commit()
        flash('Varslingsinnstillinger er oppdatert!', 'success')
        return redirect(url_for('auth.notification_settings'))
    
    return render_template('auth/notification_settings.html', preferences=preferences)


@auth_bp.route('/download-data')
@login_required
def download_data():
    """Download user data as JSON or CSV"""
    import json
    import csv
    from io import StringIO, BytesIO
    from flask import Response
    
    format_type = request.args.get('format', 'json')
    
    # Gather user data
    user_data = {
        'user_info': {
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'member_since': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
            'total_xp': current_user.total_xp,
            'preferred_language': current_user.preferred_language
        },
        'progress': {},
        'quiz_history': [],
        'achievements': []
    }
    
    # Add progress data
    if current_user.progress:
        progress = current_user.progress
        user_data['progress'] = {
            'total_quizzes_taken': progress.total_quizzes_taken,
            'total_questions_answered': progress.total_questions_answered,
            'correct_answers': progress.correct_answers,
            'accuracy_percentage': round((progress.correct_answers / progress.total_questions_answered * 100) if progress.total_questions_answered > 0 else 0, 2),
            'current_streak_days': progress.current_streak_days,
            'longest_streak_days': progress.longest_streak_days,
            'last_activity_date': progress.last_activity_date.isoformat() if progress.last_activity_date else None
        }
    
    # Add quiz history
    for session in current_user.quiz_sessions:
        user_data['quiz_history'].append({
            'date': session.completed_at.isoformat() if session.completed_at else session.started_at.isoformat(),
            'quiz_type': session.quiz_type,
            'category': session.category,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'score': float(session.score) if session.score else 0,
            'time_spent_seconds': session.time_spent_seconds
        })
    
    # Add achievements
    for achievement in current_user.achievements:
        user_data['achievements'].append({
            'name': achievement.achievement.name,
            'description': achievement.achievement.description,
            'earned_at': achievement.earned_at.isoformat(),
            'points': achievement.achievement.points
        })
    
    if format_type == 'csv':
        # Create CSV format
        output = StringIO()
        
        # Write user info
        writer = csv.writer(output)
        writer.writerow(['User Information'])
        writer.writerow(['Field', 'Value'])
        for key, value in user_data['user_info'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        
        writer.writerow([])
        writer.writerow(['Progress Statistics'])
        writer.writerow(['Metric', 'Value'])
        for key, value in user_data['progress'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        
        writer.writerow([])
        writer.writerow(['Quiz History'])
        if user_data['quiz_history']:
            writer.writerow(['Date', 'Type', 'Category', 'Questions', 'Correct', 'Score', 'Time (seconds)'])
            for quiz in user_data['quiz_history']:
                writer.writerow([
                    quiz['date'],
                    quiz['quiz_type'] or 'Standard',
                    quiz['category'] or 'Mixed',
                    quiz['total_questions'],
                    quiz['correct_answers'],
                    quiz['score'],
                    quiz['time_spent_seconds']
                ])
        
        writer.writerow([])
        writer.writerow(['Achievements'])
        if user_data['achievements']:
            writer.writerow(['Name', 'Description', 'Earned Date', 'Points'])
            for ach in user_data['achievements']:
                writer.writerow([ach['name'], ach['description'], ach['earned_at'], ach['points']])
        
        # Create response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=sertifikatet_data_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    else:
        # Return JSON format
        return Response(
            json.dumps(user_data, indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=sertifikatet_data_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.json'
            }
        )
