"""
Email service for admin notifications and security alerts
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Handle email notifications for admin security events"""
    
    @staticmethod
    def send_admin_creation_alert(new_admin_user, granting_admin_user=None, ip_address=None):
        """Send email alert when a new admin user is created"""
        
        if not current_app.config.get('ADMIN_EMAIL_NOTIFICATIONS', True):
            logger.info("Admin email notifications are disabled")
            return True
            
        # Get all current admin users to notify
        from ..models import User
        admin_users = User.query.filter_by(is_admin=True).filter(User.id != new_admin_user.id).all()
        
        if not admin_users:
            logger.warning("No existing admin users found to notify")
            return True
            
        # Get super admin email if configured
        super_admin_email = current_app.config.get('SUPER_ADMIN_EMAIL')
        
        # Prepare recipient list
        recipients = []
        for admin in admin_users:
            if admin.email:
                recipients.append(admin.email)
        
        if super_admin_email and super_admin_email not in recipients:
            recipients.append(super_admin_email)
            
        if not recipients:
            logger.warning("No admin email addresses found for notification")
            return True
            
        # Create email content
        subject = f"🚨 SECURITY ALERT: New Admin User Created - {current_app.config.get('SITE_NAME', 'Sertifikatet')}"
        
        # Email template
        email_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .alert { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .danger { background: #f8d7da; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; }
        .header { background: #dc3545; color: white; padding: 15px; border-radius: 5px; text-align: center; }
        .details { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
        h1, h2 { margin-top: 0; }
        .timestamp { font-family: monospace; background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 SECURITY ALERT</h1>
            <p>New Administrator Account Created</p>
        </div>
        
        <div class="alert danger">
            <h2>⚠️ Admin Privilege Granted</h2>
            <p>A new user has been granted administrator privileges in {{ site_name }}.</p>
        </div>
        
        <div class="details">
            <h3>📋 New Admin Details:</h3>
            <ul>
                <li><strong>Username:</strong> {{ new_admin.username }}</li>
                <li><strong>Email:</strong> {{ new_admin.email }}</li>
                <li><strong>Full Name:</strong> {{ new_admin.full_name or 'Not provided' }}</li>
                <li><strong>User ID:</strong> {{ new_admin.id }}</li>
                <li><strong>Account Created:</strong> {{ new_admin.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') }}</li>
            </ul>
        </div>
        
        {% if granting_admin %}
        <div class="details">
            <h3>👤 Granted By:</h3>
            <ul>
                <li><strong>Admin Username:</strong> {{ granting_admin.username }}</li>
                <li><strong>Admin Email:</strong> {{ granting_admin.email }}</li>
                <li><strong>Admin ID:</strong> {{ granting_admin.id }}</li>
            </ul>
        </div>
        {% endif %}
        
        <div class="details">
            <h3>🌐 Additional Information:</h3>
            <ul>
                <li><strong>Timestamp:</strong> <span class="timestamp">{{ timestamp }}</span></li>
                {% if ip_address %}
                <li><strong>IP Address:</strong> <span class="timestamp">{{ ip_address }}</span></li>
                {% endif %}
                <li><strong>Total Admin Users:</strong> {{ total_admins }}</li>
            </ul>
        </div>
        
        <div class="alert info">
            <h3>🔒 Security Recommendations:</h3>
            <ul>
                <li>Verify this admin creation was authorized</li>
                <li>Review admin user permissions immediately</li>
                <li>Check recent login logs for suspicious activity</li>
                <li>Contact the granting admin if this was unexpected</li>
            </ul>
        </div>
        
        <div class="alert">
            <p><strong>⚡ Quick Actions:</strong></p>
            <ul>
                <li>Review admin users: <a href="{{ admin_url }}">Admin Panel</a></li>
                <li>Check audit logs for recent changes</li>
                <li>Revoke access immediately if unauthorized</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>This is an automated security notification from {{ site_name }}.</p>
            <p>If you believe this notification was sent in error or if you notice any suspicious activity, please investigate immediately.</p>
            <p><strong>Do not ignore this alert.</strong> Admin privilege escalation can be a sign of a security breach.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Render email template
        from ..models import User
        total_admins = User.query.filter_by(is_admin=True).count()
        
        # Ensure we have valid values for template rendering
        server_name = current_app.config.get('SERVER_NAME', 'localhost:5000')
        if not server_name.startswith(('http://', 'https://')):
            admin_url = f"http://{server_name}/admin"
        else:
            admin_url = f"{server_name}/admin"
        
        html_content = render_template_string(email_template,
            site_name=current_app.config.get('SITE_NAME', 'Sertifikatet'),
            new_admin=new_admin_user,
            granting_admin=granting_admin_user,
            ip_address=ip_address or 'Unknown',
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            total_admins=total_admins,
            admin_url=admin_url
        )
        
        # Send email to all admin recipients
        try:
            return EmailService._send_email(recipients, subject, html_content)
        except Exception as e:
            logger.error(f"Failed to send admin creation alert: {e}")
            return False
    
    @staticmethod
    def send_admin_revocation_alert(revoked_admin_user, revoking_admin_user=None, ip_address=None):
        """Send email alert when admin privileges are revoked"""
        
        if not current_app.config.get('ADMIN_EMAIL_NOTIFICATIONS', True):
            return True
            
        # Get remaining admin users
        from ..models import User
        admin_users = User.query.filter_by(is_admin=True).all()
        
        recipients = []
        for admin in admin_users:
            if admin.email:
                recipients.append(admin.email)
        
        # Also notify the super admin and the revoked user
        super_admin_email = current_app.config.get('SUPER_ADMIN_EMAIL')
        if super_admin_email and super_admin_email not in recipients:
            recipients.append(super_admin_email)
            
        if revoked_admin_user.email and revoked_admin_user.email not in recipients:
            recipients.append(revoked_admin_user.email)
            
        if not recipients:
            return True
            
        subject = f"⚠️ Admin Privileges Revoked - {current_app.config.get('SITE_NAME', 'Sertifikatet')}"
        
        # Simple text content for revocation
        content = f"""
Admin Privileges Revoked

The following user's administrator privileges have been revoked:

Username: {revoked_admin_user.username}
Email: {revoked_admin_user.email}
User ID: {revoked_admin_user.id}

Revoked by: {revoking_admin_user.username if revoking_admin_user else 'System'}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
IP Address: {ip_address or 'Unknown'}

This is an automated security notification.
        """
        
        try:
            return EmailService._send_email(recipients, subject, content, is_html=False)
        except Exception as e:
            logger.error(f"Failed to send admin revocation alert: {e}")
            return False
    
    @staticmethod
    def _send_email(recipients, subject, content, is_html=True):
        """Internal method to send email via SMTP using admin email configuration"""
        
        if not current_app.config.get('ADMIN_MAIL_USERNAME') or not current_app.config.get('ADMIN_MAIL_PASSWORD'):
            logger.warning("Admin email credentials not configured, skipping email send")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config.get('ADMIN_MAIL_DEFAULT_SENDER')
            msg['To'] = ', '.join(recipients)
            
            # Add content
            if is_html:
                msg.attach(MIMEText(content, 'html'))
            else:
                msg.attach(MIMEText(content, 'plain'))
            
            # Send email using admin SMTP configuration
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
            
            logger.info(f"Admin security email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin email: {e}")
            return False
