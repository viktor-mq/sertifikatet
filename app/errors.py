# app/errors.py - Centralized Error Handling
from flask import render_template, request, jsonify, current_app
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime
from . import db
from .models import AdminReport


class ErrorHandler:
    """Centralized error handling and reporting"""
    
    @staticmethod
    def log_error(error, error_type="system_error", user_id=None, ip_address=None, url=None, send_email=True):
        """Log error to database and file, optionally send email notification"""
        try:
            # Log to file
            current_app.logger.error(f"Error: {str(error)}")
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create admin report for tracking
            report = AdminReport(
                report_type=error_type,
                priority='high' if error_type in ['database_error', 'payment_error'] else 'medium',
                title=f"Application Error: {error.__class__.__name__}",
                description=str(error),
                affected_user_id=user_id,
                ip_address=ip_address or (request.remote_addr if request else None),
                url=url or (request.url if request else None),
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                user_agent=request.headers.get('User-Agent') if request else None
            )
            
            db.session.add(report)
            db.session.commit()
            
            # Send email notification for critical errors
            if send_email and error_type in ['server_error', 'unexpected_error', 'database_error', 'payment_error']:
                try:
                    ErrorHandler._send_error_notification_email(error, error_type, report)
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send error notification email: {email_error}")
            
        except Exception as db_error:
            # Fallback logging if database fails
            current_app.logger.critical(f"Failed to log error to database: {db_error}")
            current_app.logger.critical(f"Original error: {error}")
            
            # Try to send email even if database logging failed
            if send_email:
                try:
                    ErrorHandler._send_error_notification_email(error, error_type, None)
                except Exception as email_error:
                    current_app.logger.critical(f"Failed to send error notification email after DB failure: {email_error}")
    
    @staticmethod
    def _send_error_notification_email(error, error_type, report=None):
        """Send email notification to admins about the error"""
        try:
            from .security.email_service import EmailService
            
            # Get admin emails
            admin_emails = []
            
            # Get super admin email
            super_admin_email = current_app.config.get('SUPER_ADMIN_EMAIL')
            if super_admin_email:
                admin_emails.append(super_admin_email)
            
            # Get other admin emails from config
            other_admin_emails = current_app.config.get('ADMIN_EMAILS', '')
            if other_admin_emails:
                for email in other_admin_emails.split(','):
                    email = email.strip()
                    if email and email not in admin_emails:
                        admin_emails.append(email)
            
            # Get admin users from database
            try:
                from .models import User
                admin_users = User.query.filter_by(is_admin=True).all()
                for admin in admin_users:
                    if admin.email and admin.email not in admin_emails:
                        admin_emails.append(admin.email)
            except Exception:
                pass  # Database might be down
            
            if not admin_emails:
                current_app.logger.warning("No admin emails configured for error notifications")
                return False
            
            # Prepare email content
            subject = f"🚨 {error_type.replace('_', ' ').title()} - {current_app.config.get('SITE_NAME', 'Sertifikatet')}"
            
            # Get request info safely
            url = 'N/A'
            ip_address = 'N/A'
            user_agent = 'N/A'
            
            if request:
                url = request.url
                ip_address = request.remote_addr or 'N/A'
                user_agent = request.headers.get('User-Agent', 'N/A')
            
            # Create email body
            email_body = f"""
🚨 ERROR ALERT - {current_app.config.get('SITE_NAME', 'Sertifikatet')}

=== ERROR DETAILS ===
Error Type: {error_type}
Error Message: {str(error)}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

=== REQUEST DETAILS ===
URL: {url}
IP Address: {ip_address}
User Agent: {user_agent}

=== STACK TRACE ===
{traceback.format_exc()}

=== ADDITIONAL INFO ===
{f'Report ID: {report.id}' if report else 'Report not saved to database'}
Priority: {report.priority if report else 'high'}

Please investigate this error immediately.

Admin Panel: {current_app.config.get('SERVER_NAME', 'localhost')}/admin

---
This is an automated error notification from {current_app.config.get('SITE_NAME', 'Sertifikatet')}.
            """
            
            # Send email using internal method (simpler than the complex admin service)
            return ErrorHandler._send_simple_email(admin_emails, subject, email_body)
            
        except Exception as e:
            current_app.logger.error(f"Failed to send error notification email: {e}")
            return False
    
    @staticmethod
    def _send_simple_email(recipients, subject, content):
        """Send simple text email using admin SMTP config"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if not current_app.config.get('ADMIN_MAIL_USERNAME') or not current_app.config.get('ADMIN_MAIL_PASSWORD'):
                current_app.logger.warning("Admin email credentials not configured")
                return False
            
            # Create message
            msg = MIMEText(content, 'plain')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('ADMIN_MAIL_DEFAULT_SENDER', 'noreply@sertifikatet.no')
            msg['To'] = ', '.join(recipients)
            
            # Send via SMTP
            server = smtplib.SMTP(
                current_app.config.get('ADMIN_MAIL_SERVER'),
                current_app.config.get('ADMIN_MAIL_PORT')
            )
            
            if current_app.config.get('ADMIN_MAIL_USE_TLS'):
                server.starttls()
            
            server.login(
                current_app.config.get('ADMIN_MAIL_USERNAME'),
                current_app.config.get('ADMIN_MAIL_PASSWORD')
            )
            
            server.send_message(msg)
            server.quit()
            
            current_app.logger.info(f"Error notification email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send simple email: {e}")
            return False


def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.',
                'status_code': 404
            }), 404
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        ErrorHandler.log_error(error, "access_denied")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource.',
                'status_code': 403
            }), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server errors"""
        ErrorHandler.log_error(error, "server_error", send_email=True)
        db.session.rollback()
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'status_code': 500
            }), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle all unexpected errors"""
        if isinstance(error, HTTPException):
            return error
        
        ErrorHandler.log_error(error, "unexpected_error", send_email=True)
        db.session.rollback()
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unexpected Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'status_code': 500
            }), 500
        
        return render_template('errors/500.html'), 500


# Custom Exceptions for Business Logic
class SertifikatetException(Exception):
    """Base exception for Sertifikatet application"""
    def __init__(self, message, status_code=500, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class SubscriptionException(SertifikatetException):
    """Subscription-related errors"""
    def __init__(self, message, status_code=400):
        super().__init__(message, status_code, "SUBSCRIPTION_ERROR")


class QuotaExceededException(SertifikatetException):
    """User has exceeded their usage quota"""
    def __init__(self, message="Daily quiz limit exceeded", status_code=429):
        super().__init__(message, status_code, "QUOTA_EXCEEDED")
