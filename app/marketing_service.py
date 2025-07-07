# app/marketing_service.py
from datetime import datetime, timedelta
from flask import render_template, url_for
from . import db
from .models import User
from .marketing_models import MarketingEmail, MarketingEmailLog
from .notification_models import UserNotificationPreferences
from .utils.email import send_email, get_notification_settings_url
from threading import Thread
import logging

logger = logging.getLogger(__name__)

class MarketingEmailService:
    """Service for handling marketing email campaigns"""
    
    @staticmethod
    def get_eligible_recipients(target_free=True, target_premium=True, target_pro=True, target_active_only=False):
        """
        Get users eligible for marketing emails based on targeting criteria.
        
        Args:
            target_free (bool): Include free users
            target_premium (bool): Include premium users  
            target_pro (bool): Include pro users
            target_active_only (bool): Only include users active in last 30 days
        
        Returns:
            List of User objects
        """
        # Base query - users who opted in to marketing emails
        query = db.session.query(User).join(
            UserNotificationPreferences, 
            User.id == UserNotificationPreferences.user_id
        ).filter(
            User.is_active == True,
            User.is_verified == True,
            UserNotificationPreferences.marketing_emails == True
        )
        
        # Filter by subscription tiers using current_plan_id
        plan_filters = []
        if target_free:
            plan_filters.append(User.current_plan_id == 1)  # Free plan
        if target_premium:
            plan_filters.append(User.current_plan_id == 2)  # Premium plan
        if target_pro:
            plan_filters.append(User.current_plan_id == 3)  # Pro plan
        
        if plan_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*plan_filters))
        else:
            # If no tiers selected, return empty list
            return []
        
        # Filter by activity if requested
        if target_active_only:
            from .models import UserProgress
            thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
            query = query.join(UserProgress).filter(
                UserProgress.last_activity_date >= thirty_days_ago
            )
        
        return query.all()
    
    @staticmethod
    def create_marketing_email(title, subject, html_content, created_by_user_id, 
                             target_free=True, target_premium=True, target_pro=True, 
                             target_active_only=False):
        """
        Create a new marketing email campaign.
        
        Returns:
            MarketingEmail object
        """
        email = MarketingEmail(
            title=title,
            subject=subject,
            html_content=html_content,
            created_by_user_id=created_by_user_id,
            target_free_users=target_free,
            target_premium_users=target_premium,
            target_pro_users=target_pro,
            target_active_only=target_active_only
        )
        
        # Calculate recipient count
        recipients = MarketingEmailService.get_eligible_recipients(
            target_free, target_premium, target_pro, target_active_only
        )
        email.recipients_count = len(recipients)
        
        db.session.add(email)
        db.session.commit()
        
        return email
    
    @staticmethod
    def send_marketing_email(email_id):
        """
        Send a marketing email campaign to all eligible recipients.
        
        Args:
            email_id (int): ID of the marketing email to send
            
        Returns:
            dict: Status and results
        """
        email = MarketingEmail.query.get(email_id)
        if not email:
            return {'success': False, 'error': 'Email campaign not found'}
        
        if email.status != 'draft':
            return {'success': False, 'error': 'Email campaign is not in draft status'}
        
        # Get eligible recipients
        recipients = MarketingEmailService.get_eligible_recipients(
            email.target_free_users,
            email.target_premium_users, 
            email.target_pro_users,
            email.target_active_only
        )
        
        # Update email status
        email.status = 'sending'
        email.recipients_count = len(recipients)
        db.session.commit()
        
        # Send emails in background thread with app context
        from flask import current_app
        Thread(
            target=MarketingEmailService._send_emails_async,
            args=(current_app._get_current_object(), email_id, [r.id for r in recipients])
        ).start()
        
        return {
            'success': True, 
            'message': f'Started sending to {len(recipients)} recipients',
            'recipient_count': len(recipients)
        }
    
    @staticmethod
    def _send_emails_async(app, email_id, recipient_user_ids):
        """
        Send emails asynchronously in background thread with app context.
        """
        with app.app_context():
            # Re-fetch the email and recipients within the app context
            email = MarketingEmail.query.get(email_id)
            if not email:
                logger.error(f"Email campaign {email_id} not found in async thread")
                return
            
            recipients = User.query.filter(User.id.in_(recipient_user_ids)).all()
            
            sent_count = 0
            failed_count = 0
            
            # Add static marketing footer
            footer = MarketingEmailService._get_marketing_footer()
            full_content = email.html_content + footer
            
            for user in recipients:
                try:
                    # Create log entry
                    log_entry = MarketingEmailLog(
                        marketing_email_id=email.id,
                        user_id=user.id,
                        recipient_email=user.email,
                        status='pending'
                    )
                    db.session.add(log_entry)
                    db.session.flush()
                    
                    # Personalize content
                    personalized_content = MarketingEmailService._personalize_content(
                        full_content, user
                    )
                    
                    # Send email
                    success = send_email(
                        subject=email.subject,
                        recipients=[user.email],
                        html_body=personalized_content
                    )
                    
                    if success:
                        log_entry.status = 'sent'
                        log_entry.sent_at = datetime.utcnow()
                        sent_count += 1
                    else:
                        log_entry.status = 'failed'
                        log_entry.error_message = 'Failed to send email'
                        failed_count += 1
                        
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to send marketing email to {user.email}: {str(e)}")
                    try:
                        log_entry.status = 'failed'
                        log_entry.error_message = str(e)
                        failed_count += 1
                        db.session.commit()
                    except:
                        # If we can't even save the error, just log it
                        logger.error(f"Failed to save error log for {user.email}")
            
            # Update email campaign status
            try:
                email.status = 'sent' if failed_count == 0 else ('partially_sent' if sent_count > 0 else 'failed')
                email.sent_count = sent_count
                email.failed_count = failed_count
                email.sent_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Marketing email '{email.title}' sent to {sent_count}/{len(recipients)} recipients")
            except Exception as e:
                logger.error(f"Failed to update email campaign status: {str(e)}")
    
    @staticmethod
    def _get_marketing_footer():
        """
        Get the static marketing footer as requested.
        """
        notification_settings_url = get_notification_settings_url()
        
        return f"""
        <div style="background: #f8f9fa; padding: 20px; margin-top: 30px; border-top: 1px solid #ddd; text-align: center; font-size: 12px; color: #666;">
            <p>&copy; {datetime.now().year} Sertifikatet.no. Alle rettigheter forbeholdt.</p>
            <p>
                <a href="{notification_settings_url}" style="color: #007bff;">Endre varslingsinnstillinger</a> | 
                <a href="{notification_settings_url}" style="color: #007bff;">Avmeld markedsføring</a>
            </p>
            <p><small>Du mottar denne e-posten fordi du har aktivert markedsføring i dine innstillinger.</small></p>
        </div>
        """
    
    @staticmethod
    def _personalize_content(html_content, user):
        """
        Personalize email content with user-specific information.
        
        Args:
            html_content (str): HTML content with placeholders
            user (User): User object
            
        Returns:
            str: Personalized HTML content
        """
        # Generate URLs using the same method as the footer
        notification_settings_url = get_notification_settings_url()
        
        # Replace user variables
        personalized = html_content.replace(
            '{{user.full_name or user.username}}', 
            user.full_name or user.username
        )
        personalized = personalized.replace(
            '{{user.username}}', 
            user.username
        )
        personalized = personalized.replace(
            '{{user.full_name}}', 
            user.full_name or user.username
        )
        
        # Replace URL variables using the same URL generation as footer
        personalized = personalized.replace(
            '{{settings_url}}', 
            notification_settings_url
        )
        personalized = personalized.replace(
            '{{unsubscribe_url}}', 
            notification_settings_url  # Same URL as footer - points to notification settings
        )
        
        return personalized
    
    @staticmethod
    def get_marketing_statistics():
        """
        Get marketing email statistics for dashboard.
        
        Returns:
            dict: Statistics data
        """
        total_campaigns = MarketingEmail.query.count()
        
        # Count users who opted in to marketing
        opted_in_users = db.session.query(User).join(
            UserNotificationPreferences
        ).filter(
            UserNotificationPreferences.marketing_emails == True,
            User.is_active == True,
            User.is_verified == True
        ).count()
        
        # Count emails sent this month
        this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        sent_this_month = MarketingEmail.query.filter(
            MarketingEmail.sent_at >= this_month,
            MarketingEmail.status.in_(['sent', 'partially_sent'])
        ).count()
        
        # Calculate success rate
        total_sent = db.session.query(
            db.func.sum(MarketingEmail.sent_count)
        ).scalar() or 0
        
        total_attempted = db.session.query(
            db.func.sum(MarketingEmail.recipients_count)
        ).filter(
            MarketingEmail.status.in_(['sent', 'partially_sent', 'failed'])
        ).scalar() or 0
        
        success_rate = (total_sent / total_attempted * 100) if total_attempted > 0 else 0
        
        return {
            'total_campaigns': total_campaigns,
            'opted_in_users': opted_in_users,
            'sent_this_month': sent_this_month,
            'success_rate': success_rate
        }
