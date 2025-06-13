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


def send_email(subject, recipients, html_body, sender=None):
    """
    Send an email to the specified recipients.
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        html_body (str): HTML content of the email
        sender (str): Optional sender email (defaults to MAIL_DEFAULT_SENDER)
    """
    # Get mail configuration from environment
    mail_server = os.environ.get('MAIL_SERVER', 'mail.sertifikatet.no')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
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
    # Get user's progress info
    progress = user.progress
    streak_days = progress.current_streak_days if progress else 0
    
    html_body = render_template('emails/daily_reminder.html',
                               user=user,
                               streak_days=streak_days,
                               login_url=url_for('auth.login', _external=True),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'Din daglige påminnelse - {streak_days} dager i strekk! 🔥',
        recipients=[user.email],
        html_body=html_body
    )


def send_badge_notification(user, badge_name):
    """
    Send notification when user earns a new badge/achievement.
    
    Args:
        user: User model instance
        badge_name (str): Name of the earned badge
    """
    html_body = render_template('emails/badge_earned.html',
                               user=user,
                               badge_name=badge_name,
                               profile_url=url_for('main.profile', _external=True),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'Gratulerer! Du har låst opp "{badge_name}" 🏆',
        recipients=[user.email],
        html_body=html_body
    )


def send_admin_alert(subject, message):
    """
    Send alert email to admin(s).
    
    Args:
        subject (str): Alert subject
        message (str): Alert message
    """
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    if not admin_emails or not admin_emails[0]:
        logger.warning("No admin emails configured")
        return
    
    html_body = render_template('emails/admin_alert.html',
                               subject=subject,
                               message=message,
                               timestamp=datetime.now(),
                               current_year=datetime.now().year)
    
    send_email(
        subject=f'[Admin Alert] {subject}',
        recipients=admin_emails,
        html_body=html_body
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
    
    for user in eligible_users:
        try:
            send_learning_reminder_email(user)
        except Exception as e:
            logger.error(f"Failed to send reminder to {user.email}: {str(e)}")
    
    logger.info(f"Sent {len(eligible_users)} reminder emails")


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
