# app/notification_models.py
from datetime import datetime
from . import db
from sqlalchemy.orm.attributes import flag_modified

class UserNotificationPreferences(db.Model):
    """User notification preferences for email notifications"""
    __tablename__ = 'user_notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Email notification settings
    daily_reminders = db.Column(db.Boolean, default=True)
    weekly_summary = db.Column(db.Boolean, default=True)
    achievement_notifications = db.Column(db.Boolean, default=True)
    streak_lost_reminders = db.Column(db.Boolean, default=True)
    study_tips = db.Column(db.Boolean, default=True)
    new_features = db.Column(db.Boolean, default=True)
    
    # Progress notifications
    progress_milestones = db.Column(db.Boolean, default=True)
    quiz_reminder_frequency = db.Column(db.String(20), default='daily')  # 'never', 'daily', 'weekly'
    
    # Communication preferences
    marketing_emails = db.Column(db.Boolean, default=False)
    partner_offers = db.Column(db.Boolean, default=False)
    
    # Timing preferences
    reminder_time = db.Column(db.Time, default=datetime.strptime('18:00', '%H:%M').time())  # Default 6 PM
    timezone = db.Column(db.String(50), default='Europe/Oslo')
    
    # Cookie consent tracking (GDPR compliance)
    cookie_preferences = db.Column(db.JSON)  # Stores cookie consent choices
    cookie_consent_date = db.Column(db.DateTime)  # When consent was given
    cookie_consent_version = db.Column(db.String(10))  # Version of cookie policy
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<UserNotificationPreferences {self.user_id}>'
    
    def update_cookie_preferences(self, preferences, version=None):
        """Update cookie preferences with timestamp"""
        from flask import current_app
        
        if version is None:
            version = current_app.config.get('COOKIE_POLICY_VERSION', '1.0')
            
        self.cookie_preferences = preferences
        self.cookie_consent_date = datetime.utcnow()
        self.cookie_consent_version = version
        self.updated_at = datetime.utcnow()  # Explicitly update timestamp
        
        # Mark JSON field as modified to ensure SQLAlchemy detects the change
        flag_modified(self, 'cookie_preferences')
        
        # Mark the instance as dirty to ensure SQLAlchemy detects the change
        db.session.add(self)
        db.session.commit()
    
    def get_cookie_preferences(self):
        """Get current cookie preferences with defaults"""
        if self.cookie_preferences:
            return self.cookie_preferences
        return {
            'necessary': True,
            'analytics': True,   # Default to opted-in
            'marketing': True    # Default to opted-in
        }


class CookieConsent(db.Model):
    """Cookie consent tracking for anonymous users (GDPR compliance)"""
    __tablename__ = 'cookie_consents'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)  # Browser session ID
    
    # Consent data
    preferences = db.Column(db.JSON, nullable=False)  # Cookie consent choices
    consent_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    version = db.Column(db.String(10), nullable=False)  # Cookie policy version
    
    # Audit trail (for compliance)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    user_agent = db.Column(db.Text)  # Browser info
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CookieConsent {self.session_id}>'
    
    @classmethod
    def get_or_create_consent(cls, session_id):
        """Get existing consent or create new record"""
        from flask import current_app
        
        consent = cls.query.filter_by(session_id=session_id).first()
        if not consent:
            default_version = current_app.config.get('COOKIE_POLICY_VERSION', '1.0')
            consent = cls(session_id=session_id, preferences={}, version=default_version)
            db.session.add(consent)
        return consent
    
    def update_preferences(self, preferences, version=None, ip_address=None, user_agent=None):
        """Update cookie preferences with audit trail"""
        from flask import current_app
        
        if version is None:
            version = current_app.config.get('COOKIE_POLICY_VERSION', '1.0')
            
        self.preferences = preferences
        self.consent_date = datetime.utcnow()
        self.version = version
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        db.session.commit()
