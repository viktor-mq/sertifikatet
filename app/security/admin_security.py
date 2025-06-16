"""
Admin Security Service - Enhanced security measures for admin privilege management
"""
import json
import logging
from datetime import datetime, timedelta
from flask import request, current_app
from sqlalchemy import and_
from ..models import User, AdminAuditLog, AdminReport, db
from .email_service import EmailService

logger = logging.getLogger(__name__)

class AdminSecurityService:
    """Comprehensive admin security management"""
    
    @staticmethod
    def grant_admin_privileges(target_user, granting_admin=None):
        """
        Safely grant admin privileges with comprehensive logging and notifications
        
        Args:
            target_user: User object to grant admin privileges to
            granting_admin: User object of the admin granting privileges (None for system)
            
        Returns:
            dict: {success: bool, message: str, warnings: list}
        """
        
        if target_user.is_admin:
            return {
                'success': False,
                'message': f'User {target_user.username} already has admin privileges',
                'warnings': []
            }
        
        warnings = []
        
        # Security checks
        if not AdminSecurityService._validate_admin_creation(target_user, granting_admin):
            return {
                'success': False,
                'message': 'Admin creation validation failed - potential security risk',
                'warnings': ['Security validation failed']
            }
        
        # Check for suspicious patterns
        suspicious_flags = AdminSecurityService._check_suspicious_activity(target_user)
        if suspicious_flags:
            warnings.extend(suspicious_flags)
            logger.warning(f"Suspicious flags detected for admin grant to {target_user.username}: {suspicious_flags}")
        
        try:
            # Grant admin privileges
            target_user.is_admin = True
            
            # Log the action
            AdminSecurityService._log_admin_action(
                action='grant_admin',
                target_user=target_user,
                admin_user=granting_admin,
                additional_info={'warnings': warnings}
            )
            
            db.session.commit()
            
            # Create security report
            AdminSecurityService._create_security_report(
                report_type='admin_change',
                priority='high',
                title=f'Admin Privileges Granted to {target_user.username}',
                description=f'Admin privileges were granted to user {target_user.username} (ID: {target_user.id}) by {granting_admin.username if granting_admin else "system"}.',
                affected_user=target_user,
                reported_by=granting_admin,
                metadata={'action': 'grant_admin', 'warnings': warnings}
            )
            
            # Send email notifications to all existing admins
            try:
                email_success = EmailService.send_admin_creation_alert(
                    new_admin_user=target_user,
                    granting_admin_user=granting_admin,
                    ip_address=AdminSecurityService._get_client_ip()
                )
                if not email_success:
                    warnings.append('Failed to send email notifications to admin users')
            except Exception as e:
                logger.error(f"Failed to send admin creation email: {e}")
                warnings.append('Email notification failed')
            
            logger.info(f"Admin privileges granted to user {target_user.username} by {granting_admin.username if granting_admin else 'system'}")
            
            return {
                'success': True,
                'message': f'Admin privileges successfully granted to {target_user.username}',
                'warnings': warnings
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to grant admin privileges: {e}")
            return {
                'success': False,
                'message': f'Failed to grant admin privileges: {str(e)}',
                'warnings': warnings
            }
    
    @staticmethod
    def revoke_admin_privileges(target_user, revoking_admin=None):
        """
        Safely revoke admin privileges with logging and notifications
        
        Args:
            target_user: User object to revoke admin privileges from
            revoking_admin: User object of the admin revoking privileges
            
        Returns:
            dict: {success: bool, message: str, warnings: list}
        """
        
        if not target_user.is_admin:
            return {
                'success': False,
                'message': f'User {target_user.username} does not have admin privileges',
                'warnings': []
            }
        
        warnings = []
        
        # Check if this would leave no admins
        remaining_admins = User.query.filter(
            and_(User.is_admin == True, User.id != target_user.id)
        ).count()
        
        if remaining_admins == 0:
            return {
                'success': False,
                'message': 'Cannot revoke admin privileges - this would leave no administrators',
                'warnings': ['Last admin protection']
            }
        
        try:
            # Revoke admin privileges
            target_user.is_admin = False
            
            # Log the action
            AdminSecurityService._log_admin_action(
                action='revoke_admin',
                target_user=target_user,
                admin_user=revoking_admin,
                additional_info={'remaining_admins': remaining_admins}
            )
            
            db.session.commit()
            
            # Create security report
            AdminSecurityService._create_security_report(
                report_type='admin_change',
                priority='high',
                title=f'Admin Privileges Revoked from {target_user.username}',
                description=f'Admin privileges were revoked from user {target_user.username} (ID: {target_user.id}) by {revoking_admin.username if revoking_admin else "system"}. Remaining admins: {remaining_admins}',
                affected_user=target_user,
                reported_by=revoking_admin,
                metadata={'action': 'revoke_admin', 'remaining_admins': remaining_admins}
            )
            
            # Send email notifications
            try:
                EmailService.send_admin_revocation_alert(
                    revoked_admin_user=target_user,
                    revoking_admin_user=revoking_admin,
                    ip_address=AdminSecurityService._get_client_ip()
                )
            except Exception as e:
                logger.error(f"Failed to send admin revocation email: {e}")
                warnings.append('Email notification failed')
            
            logger.info(f"Admin privileges revoked from user {target_user.username} by {revoking_admin.username if revoking_admin else 'system'}")
            
            return {
                'success': True,
                'message': f'Admin privileges successfully revoked from {target_user.username}',
                'warnings': warnings
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to revoke admin privileges: {e}")
            return {
                'success': False,
                'message': f'Failed to revoke admin privileges: {str(e)}',
                'warnings': warnings
            }
    
    @staticmethod
    def get_admin_audit_log(limit=100):
        """Get recent admin audit log entries"""
        return AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def is_admin_required(user):
        """Enhanced admin check with proper security"""
        if not user or not user.is_authenticated:
            return False
        return user.is_admin
    
    @staticmethod
    def _validate_admin_creation(target_user, granting_admin):
        """Validate admin creation request for security"""
        
        # Check if target user exists and is active
        if not target_user or not target_user.is_active:
            logger.warning(f"Attempted to grant admin to inactive or non-existent user: {target_user}")
            return False
        
        # Check if granting admin has privileges (None means system operation)
        if granting_admin and not granting_admin.is_admin:
            logger.warning(f"Non-admin user {granting_admin.username} attempted to grant admin privileges")
            return False
        
        # Check for recent suspicious activity
        recent_failed_attempts = AdminAuditLog.query.filter(
            and_(
                AdminAuditLog.target_user_id == target_user.id,
                AdminAuditLog.action == 'login_attempt',
                AdminAuditLog.created_at > datetime.utcnow() - timedelta(hours=24)
            )
        ).count()
        
        if recent_failed_attempts > 10:
            logger.warning(f"High number of recent login attempts for user {target_user.username}")
            return False
        
        return True
    
    @staticmethod
    def _check_suspicious_activity(target_user):
        """Check for suspicious patterns that might indicate security risk"""
        flags = []
        
        # Check account age
        if target_user.created_at > datetime.utcnow() - timedelta(days=1):
            flags.append('Account created within last 24 hours')
        
        # Check if user has unusual activity patterns
        if not target_user.email or '@' not in target_user.email:
            flags.append('Invalid or missing email address')
        
        # Check if user has completed normal user activities
        if hasattr(target_user, 'progress') and target_user.progress:
            if target_user.progress.total_quizzes_taken == 0:
                flags.append('User has never taken a quiz')
        
        # Check for multiple recent admin grants
        recent_admin_grants = AdminAuditLog.query.filter(
            and_(
                AdminAuditLog.action == 'grant_admin',
                AdminAuditLog.created_at > datetime.utcnow() - timedelta(hours=1)
            )
        ).count()
        
        if recent_admin_grants > 3:
            flags.append('Multiple admin grants in last hour')
        
        return flags
    
    @staticmethod
    def _log_admin_action(action, target_user, admin_user=None, additional_info=None):
        """Log admin privilege changes for audit trail"""
        
        audit_log = AdminAuditLog(
            target_user_id=target_user.id,
            admin_user_id=admin_user.id if admin_user else None,
            action=action,
            ip_address=AdminSecurityService._get_client_ip(),
            user_agent=request.headers.get('User-Agent', '') if request else '',
            additional_info=json.dumps(additional_info) if additional_info else None
        )
        
        db.session.add(audit_log)
        # Note: commit is handled by the calling function
    
    @staticmethod
    def _get_client_ip():
        """Get client IP address safely"""
        if not request:
            return None
            
        # Check for forwarded headers (proxy/load balancer)
        if 'X-Forwarded-For' in request.headers:
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif 'X-Real-IP' in request.headers:
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr
    
    @staticmethod
    def log_admin_login_attempt(user, success=True):
        """Log admin login attempts for security monitoring"""
        try:
            AdminSecurityService._log_admin_action(
                action='admin_login_success' if success else 'admin_login_failure',
                target_user=user,
                additional_info={'success': success}
            )
            
            # Create security report for failed admin login attempts
            if not success:
                AdminSecurityService._create_security_report(
                    report_type='security_alert',
                    priority='medium',
                    title=f'Failed Admin Login Attempt - {user.username}',
                    description=f'Failed admin login attempt for user {user.username} from IP {AdminSecurityService._get_client_ip()}',
                    affected_user=user,
                    metadata={'ip_address': AdminSecurityService._get_client_ip()}
                )
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log admin login attempt: {e}")
    
    @staticmethod
    def _create_security_report(report_type, priority, title, description, affected_user=None, reported_by=None, metadata=None):
        """Create an AdminReport for security tracking"""
        try:
            report = AdminReport(
                report_type=report_type,
                priority=priority,
                title=title,
                description=description,
                affected_user_id=affected_user.id if affected_user else None,
                reported_by_user_id=reported_by.id if reported_by else None,
                ip_address=AdminSecurityService._get_client_ip(),
                user_agent=request.headers.get('User-Agent', '') if request else '',
                metadata_json=json.dumps(metadata) if metadata else None
            )
            db.session.add(report)
            # Note: commit is handled by the calling function
        except Exception as e:
            logger.error(f"Failed to create security report: {e}")
    
    @staticmethod
    def log_admin_action(admin_user, action, target_user_id=None, additional_info=None):
        """Public method to log admin actions with report creation"""
        try:
            # Get target user if ID provided
            target_user = None
            if target_user_id:
                target_user = User.query.get(target_user_id)
            
            # Log the action
            AdminSecurityService._log_admin_action(
                action=action,
                target_user=target_user or admin_user,
                admin_user=admin_user,
                additional_info=additional_info
            )
            
            # Create report for certain actions
            if action.startswith('report_'):
                # This is a report action, no need to create another report
                pass
            elif action in ['suspicious_activity', 'security_violation']:
                AdminSecurityService._create_security_report(
                    report_type='security_alert',
                    priority='high',
                    title=f'Security Alert: {action}',
                    description=f'Security action logged: {action}',
                    affected_user=target_user,
                    reported_by=admin_user,
                    metadata=additional_info
                )
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
