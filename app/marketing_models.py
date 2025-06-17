# app/marketing_models.py
from datetime import datetime
from . import db

class MarketingEmail(db.Model):
    """Marketing email campaigns created by admins"""
    __tablename__ = 'marketing_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    
    # Targeting options
    target_all_opted_in = db.Column(db.Boolean, default=True)
    target_free_users = db.Column(db.Boolean, default=True)
    target_premium_users = db.Column(db.Boolean, default=True)
    target_pro_users = db.Column(db.Boolean, default=True)
    target_active_only = db.Column(db.Boolean, default=False)  # Active in last 30 days
    
    # Sending status
    status = db.Column(db.String(20), default='draft')  # 'draft', 'scheduled', 'sending', 'sent', 'failed'
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    
    # Statistics
    recipients_count = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='marketing_emails_created')
    send_logs = db.relationship('MarketingEmailLog', backref='email_campaign', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MarketingEmail {self.title}>'


class MarketingEmailLog(db.Model):
    """Log of marketing emails sent to specific users"""
    __tablename__ = 'marketing_email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    marketing_email_id = db.Column(db.Integer, db.ForeignKey('marketing_emails.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)  # Store email at time of sending
    
    # Send status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'sent', 'failed', 'bounced'
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    provider_response = db.Column(db.Text)  # Store email provider response
    
    # Email tracking (for future implementation)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    unsubscribed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='marketing_email_logs')
    
    __table_args__ = (db.UniqueConstraint('marketing_email_id', 'user_id', name='_marketing_email_user_uc'),)
    
    def __repr__(self):
        return f'<MarketingEmailLog {self.marketing_email_id}-{self.user_id}>'


class MarketingTemplate(db.Model):
    """Reusable marketing email templates"""
    __tablename__ = 'marketing_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    html_content = db.Column(db.Text, nullable=False)
    
    # Template metadata
    category = db.Column(db.String(100))  # 'newsletter', 'promotion', 'announcement', 'seasonal'
    is_active = db.Column(db.Boolean, default=True)
    
    # Usage tracking
    times_used = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime)
    
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='marketing_templates_created')
    
    def __repr__(self):
        return f'<MarketingTemplate {self.name}>'
