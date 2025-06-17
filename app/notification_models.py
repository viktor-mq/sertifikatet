# app/notification_models.py
from datetime import datetime
from . import db

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
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<UserNotificationPreferences {self.user_id}>'
