# app/utils/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def should_send_notification(user, notification_type):
    """
    Check if user wants to receive a specific type of notification.
    
    Args:
        user: User model instance
        notification_type (str): Type of notification to check
        
    Returns:
        bool: True if user wants this notification, False otherwise
    """
    from app.notification_models import UserNotificationPreferences
    
    # Get user preferences
    preferences = UserNotificationPreferences.query.filter_by(user_id=user.id).first()
    
    # If no preferences found, assume user wants notifications (default behavior)
    if not preferences:
        return True
    
    # Map notification types to preference fields
    preference_map = {
        'daily_reminders': preferences.daily_reminders,
        'weekly_summary': preferences.weekly_summary,
        'achievement_notifications': preferences.achievement_notifications,
        'streak_lost_reminders': preferences.streak_lost_reminders,
        'study_tips': preferences.study_tips,
        'new_features': preferences.new_features,
        'progress_milestones': preferences.progress_milestones,
        'marketing_emails': preferences.marketing_emails,
        'partner_offers': preferences.partner_offers
    }
    
    return preference_map.get(notification_type, True)


def get_notification_settings_url():
    """
    Get the URL for notification settings page.
    
    Returns:
        str: Full URL to notification settings
    """
    try:
        return url_for('auth.notification_settings', _external=True)
    except:
        # Fallback if url_for fails
        return 'https://sertifikatet.no/auth/notification-settings'


def get_token_serializer():
    """Get the token serializer for generating secure tokens."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def send_async_email(app, msg, mail_server, mail_port, mail_username, mail_password, mail_use_tls):
    """Send email asynchronously in a separate thread."""
    with app.app_context():
        try:
            with smtplib.SMTP(mail_server, mail_port) as server:
                if mail_use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to send email to {msg['To']}: {str(e)}")


def send_email(subject, recipients, html_body, sender=None, use_info_sender=False):
    """
    Send an email to the specified recipients.
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        html_body (str): HTML content of the email
        sender (str): Optional sender email (defaults to MAIL_DEFAULT_SENDER)
        use_info_sender (bool): Use info@sertifikatet.no instead of noreply@
    """
    # Get mail configuration from environment
    mail_server = os.environ.get('MAIL_SERVER', 'mail.sertifikatet.no')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    
    if use_info_sender:
        mail_username = os.environ.get('ADMIN_MAIL_USERNAME', 'info@sertifikatet.no')
        mail_password = os.environ.get('ADMIN_MAIL_PASSWORD', '')  # Must be set in environment
        mail_default_sender = os.environ.get('ADMIN_MAIL_DEFAULT_SENDER', 'Sertifikatet.no Support <info@sertifikatet.no>')
        
        if not mail_password:
            logger.error("ADMIN_MAIL_PASSWORD not configured for info sender")
            return False
    else:
        mail_username = os.environ.get('MAIL_USERNAME', 'noreply@sertifikatet.no')
        mail_password = os.environ.get('MAIL_PASSWORD')
        mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER', 'Sertifikatet.no <noreply@sertifikatet.no>')
    
    if not mail_password:
        logger.error("MAIL_PASSWORD not configured")
        return False
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender or mail_default_sender
    msg['To'] = ', '.join(recipients) if isinstance(recipients, list) else recipients
    
    # Create plain text version from HTML (basic conversion)
    import re
    text_body = re.sub('<[^<]+?>', '', html_body)
    
    # Attach parts
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email in a separate thread
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg, mail_server, mail_port, 
              mail_username, mail_password, mail_use_tls)
    ).start()
    
    return True


def send_verification_email(user):
    """
    Send email verification link to new user.
    
    Args:
        user: User model instance
    """
    token_serializer = get_token_serializer()
    token = token_serializer.dumps(user.email, salt='email-verification')
    
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    html_body = render_template('emails/verify_email.html',
                               user=user,
                               verify_url=verify_url,
                               current_year=datetime.now().year)
    
    send_email(
        subject='Bekreft din e-postadresse - Sertifikatet.no',
        recipients=[user.email],
        html_body=html_body
    )


def send_password_reset_email(user):
    """
    Send password reset link to user.
    
    Args:
        user: User model instance
    """
    token_serializer = get_token_serializer()
    token = token_serializer.dumps(user.email, salt='password-reset')
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    html_body = render_template('emails/reset_password.html',
                               user=user,
                               reset_url=reset_url,
                               current_year=datetime.now().year)
    
    send_email(
        subject='Tilbakestill passord - Sertifikatet.no',
        recipients=[user.email],
        html_body=html_body
    )


def send_learning_reminder_email(user):
    """
    Send daily learning reminder to user.
    
    Args:
        user: User model instance
    """
    # Check if user wants daily reminders
    if not should_send_notification(user, 'daily_reminders'):
        return False
    
    # Get user's progress info
    progress = user.progress
    streak_days = progress.current_streak_days if progress else 0
    
    html_body = render_template('emails/daily_reminder.html',
                               user=user,
                               streak_days=streak_days,
                               login_url=url_for('auth.login', _external=True),
                               notification_settings_url=get_notification_settings_url(),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'Din daglige påminnelse - {streak_days} dager i strekk! 🔥',
        recipients=[user.email],
        html_body=html_body
    )
    return True


def send_badge_notification(user, badge_name):
    """
    Send notification when user earns a new badge/achievement.
    
    Args:
        user: User model instance
        badge_name (str): Name of the earned badge
    """
    # Check if user wants achievement notifications
    if not should_send_notification(user, 'achievement_notifications'):
        return False
    
    html_body = render_template('emails/badge_earned.html',
                               user=user,
                               badge_name=badge_name,
                               profile_url=url_for('auth.profile', _external=True),
                               notification_settings_url=get_notification_settings_url(),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'Gratulerer! Du har låst opp "{badge_name}" 🏆',
        recipients=[user.email],
        html_body=html_body
    )
    return True


def get_admin_emails():
    """Get all admin user emails from the database dynamically"""
    try:
        from app.models import User
        admin_users = User.query.filter_by(is_admin=True, is_active=True, is_verified=True).all()
        admin_emails = [user.email for user in admin_users if user.email]
        
        # Fallback to environment variable if no admin users found
        if not admin_emails:
            env_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
            admin_emails = [email.strip() for email in env_emails if email.strip()]
        
        return admin_emails
    except Exception as e:
        logger.error(f"Error getting admin emails: {e}")
        # Fallback to environment variable
        env_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
        return [email.strip() for email in env_emails if email.strip()]


def send_admin_alert(subject, message):
    """Send alert email to admin(s) - dynamically gets all admin users from database"""
    admin_emails = get_admin_emails()
    
    if not admin_emails:
        logger.warning("No admin emails found (neither in database nor environment)")
        return
    
    html_body = render_template('emails/admin_alert.html',
                               subject=subject,
                               message=message,
                               timestamp=datetime.now(),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'[Admin Alert] {subject}',
        recipients=admin_emails,
        html_body=html_body,
        use_info_sender=True
    )


def send_batch_reminders():
    """
    Send learning reminders to all eligible users.
    This function should be called by a scheduled task (e.g., Celery).
    """
    from app.models import User, UserProgress
    from app import db
    from datetime import date, timedelta
    
    # Find users who haven't been active today
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Query users with active streaks who haven't been active today
    eligible_users = db.session.query(User).join(UserProgress).filter(
        User.is_active == True,
        UserProgress.last_activity_date == yesterday,
        UserProgress.current_streak_days > 0
    ).all()
    
    sent_count = 0
    for user in eligible_users:
        try:
            if send_learning_reminder_email(user):  # Function now returns True/False
                sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send reminder to {user.email}: {str(e)}")
    
    logger.info(f"Sent {sent_count} reminder emails out of {len(eligible_users)} eligible users")


def verify_email_token(token, max_age=3600):
    """
    Verify email verification token.
    
    Args:
        token (str): Token to verify
        max_age (int): Maximum age of token in seconds (default: 1 hour)
        
    Returns:
        str: Email address if valid, None if invalid
    """
    token_serializer = get_token_serializer()
    try:
        email = token_serializer.loads(token, salt='email-verification', max_age=max_age)
        return email
    except Exception:
        return None


def verify_reset_token(token, max_age=3600):
    """
    Verify password reset token.
    
    Args:
        token (str): Token to verify
        max_age (int): Maximum age of token in seconds (default: 1 hour)
        
    Returns:
        str: Email address if valid, None if invalid
    """
    token_serializer = get_token_serializer()
    try:
        email = token_serializer.loads(token, salt='password-reset', max_age=max_age)
        return email
    except Exception:
        return None


def send_welcome_email(user):
    """
    Send welcome email after successful verification.
    
    Args:
        user: User model instance
    """
    html_body = render_template('emails/welcome_email.html',
                               user=user,
                               dashboard_url=url_for('main.dashboard', _external=True),
                               quiz_url=url_for('main.quiz', _external=True),
                               current_year=datetime.now().year)
    
    send_email(
        subject='Velkommen til Sertifikatet.no! 🎉',
        recipients=[user.email],
        html_body=html_body
    )


def send_streak_lost_email(user, lost_streak_days):
    """
    Send notification when user loses their streak.
    
    Args:
        user: User model instance
        lost_streak_days (int): Number of days the streak lasted
    """
    # Check if user wants streak lost reminders
    if not should_send_notification(user, 'streak_lost_reminders'):
        return False
    
    html_body = render_template('emails/streak_lost.html',
                               user=user,
                               lost_streak_days=lost_streak_days,
                               login_url=url_for('auth.login', _external=True),
                               notification_settings_url=get_notification_settings_url(),
                               current_year=datetime.now().year)
    
    send_email(
        subject='Din streak er brutt - men ikke gi opp! 💪',
        recipients=[user.email],
        html_body=html_body
    )
    return True


def send_weekly_summary_email(user, stats):
    """
    Send weekly progress summary.
    
    Args:
        user: User model instance
        stats (dict): Weekly statistics including XP, quizzes, etc.
    """
    # Check if user wants weekly summaries
    if not should_send_notification(user, 'weekly_summary'):
        return False
    
    html_body = render_template('emails/weekly_summary.html',
                               user=user,
                               stats=stats,
                               dashboard_url=url_for('main.dashboard', _external=True),
                               notification_settings_url=get_notification_settings_url(),
                               current_year=datetime.now().year)
    
    send_email(
        subject='Din ukentlige oppsummering 📊 - Sertifikatet.no',
        recipients=[user.email],
        html_body=html_body
    )
    return True


def send_study_tip_email(user, tip_data):
    """
    Send AI-driven study tip based on user's performance.
    
    Args:
        user: User model instance
        tip_data (dict): Contains area of improvement and tips
    """
    # Check if user wants study tips
    if not should_send_notification(user, 'study_tips'):
        return False
    
    html_body = render_template('emails/study_tip.html',
                               user=user,
                               tip_data=tip_data,
                               quiz_url=url_for('main.quiz', _external=True),
                               notification_settings_url=get_notification_settings_url(),
                               current_year=datetime.now().year)
    
    send_email(
        subject='Personlig studietips for deg 🎯',
        recipients=[user.email],
        html_body=html_body
    )
    return True


def send_user_report_alert(user, report_data):
    """
    Send alert to admin when user submits a report/feedback.
    Also creates an AdminReport for tracking.
    
    Args:
        user: User model instance
        report_data (dict): Report details
    """
    # Create AdminReport for tracking
    from app.models import AdminReport
    import json
    
    priority_map = {
        'bug': 'high',
        'security': 'critical',
        'feature': 'low',
        'High': 'high',
        'Medium': 'medium',
        'Low': 'low'
    }
    
    report = AdminReport(
        report_type='user_feedback',
        priority=priority_map.get(report_data.get('priority', 'medium'), 'medium'),
        title=f"User Report: {report_data.get('type', 'General')}",
        description=report_data.get('message', ''),
        reported_by_user_id=user.id,
        metadata_json=json.dumps(report_data)
    )
    
    from app import db
    db.session.add(report)
    db.session.commit()
    
    admin_emails = get_admin_emails()
    if not admin_emails:
        logger.warning("No admin emails found")
        return
    
    html_body = render_template('emails/user_report_alert.html',
                               user=user,
                               report_data=report_data,
                               timestamp=datetime.now(),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'[Brukerrapport] {report_data.get("type", "Generell")} - {user.username}',
        recipients=admin_emails,
        html_body=html_body,
        use_info_sender=True
    )


def send_manual_review_alert(review_type, details):
    """
    Send alert to admin for manual review requirements.
    
    Args:
        review_type (str): Type of review needed
        details (dict): Review details
    """
    admin_emails = get_admin_emails()
    if not admin_emails:
        logger.warning("No admin emails found")
        return
    
    html_body = render_template('emails/manual_review_alert.html',
                               review_type=review_type,
                               details=details,
                               timestamp=datetime.now(),
                               admin_url=url_for('admin.admin_dashboard', _external=True),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'[Manuell gjennomgang påkrevd] {review_type}',
        recipients=admin_emails,
        html_body=html_body,
        use_info_sender=True
    )
