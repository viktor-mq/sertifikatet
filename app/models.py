# app/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func  
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255))
    preferred_language = db.Column(db.String(10), default='no')
    total_xp = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    subscription_tier = db.Column(db.String(20), default='free')  # 'free', 'premium', 'pro' - DEPRECATED
    current_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=True)
    subscription_status = db.Column(db.Enum('active', 'cancelled', 'expired', 'trial'), default='active')
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    current_plan = db.relationship('SubscriptionPlan', foreign_keys=[current_plan_id], backref='users')
    progress = db.relationship('UserProgress', backref='user', uselist=False, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', cascade='all, delete-orphan')
    quiz_sessions = db.relationship('QuizSession', backref='user', cascade='all, delete-orphan')
    game_sessions = db.relationship('GameSession', backref='user', cascade='all, delete-orphan')
    video_progress = db.relationship('VideoProgress', backref='user', cascade='all, delete-orphan')
    learning_modules = db.relationship('UserLearningModule', 
                                primaryjoin='User.id == UserLearningModule.user_id',
                                backref='user', 
                                cascade='all, delete-orphan')
    # shorts_progress relationship removed - using extended VideoProgress model instead
    leaderboard_entries = db.relationship('LeaderboardEntry', backref='user', cascade='all, delete-orphan')
    feedback = db.relationship('UserFeedback', backref='user', cascade='all, delete-orphan')
    
    def get_subscription_tier(self):
        """Get user's current subscription tier name"""
        if self.current_plan:
            return self.current_plan.name
        return 'free'
    
    def get_level(self):
        """Calculate user level based on total XP"""
        # Level calculation: Level = sqrt(XP / 100)
        # Level 1: 0-199 XP, Level 2: 200-499 XP, Level 3: 500-899 XP, etc.
        if self.total_xp < 100:
            return 1
        return int((self.total_xp / 100) ** 0.5) + 1
    
    def get_current_plan_name(self):
        """Get current subscription plan display name"""
        if self.current_plan:
            return self.current_plan.display_name
        return 'Gratis Plan'
    
    def is_premium_user(self):
        """Check if user has premium or pro subscription"""
        if self.current_plan:
            return self.current_plan.name in ['premium', 'pro']
        return False
    
    def get_analytics_data(self):
        """Get user data for analytics tracking"""
        return {
            'user_id': str(self.id),
            'subscription_tier': self.get_subscription_tier(),
            'user_level': self.get_level(),
            'is_verified': self.is_verified,
            'total_xp': self.total_xp,
            'registration_date': self.created_at.isoformat() if self.created_at else None,
            'is_premium': self.is_premium_user()
        }


class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_quizzes_taken = db.Column(db.Integer, default=0)
    total_questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_game_sessions = db.Column(db.Integer, default=0)
    total_game_score = db.Column(db.Integer, default=0)
    total_videos_watched = db.Column(db.Integer, default=0)
    videos_completed = db.Column(db.Integer, default=0)
    current_streak_days = db.Column(db.Integer, default=0)
    longest_streak_days = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)


class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon_filename = db.Column(db.String(255))
    points = db.Column(db.Integer, default=10)
    category = db.Column(db.String(50))
    requirement_type = db.Column(db.String(50))
    requirement_value = db.Column(db.Integer)
    
    # Relationships
    user_achievements = db.relationship('UserAchievement', backref='achievement', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert achievement to a serializable dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon_filename,
            'points': self.points,
            'category': self.category
        }


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    shown_at = db.Column(db.DateTime, nullable=True)  # Timestamp when notification was shown
    
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='_user_achv_uc'),)


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))
    difficulty_level = db.Column(db.Integer, default=1)
    explanation = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    question_type = db.Column(db.String(50), default='multiple_choice')
    
    # Relationships
    options = db.relationship('Option', backref='question', cascade='all, delete-orphan')
    quiz_responses = db.relationship('QuizResponse', backref='question', cascade='all, delete-orphan')
    video_checkpoints = db.relationship('VideoCheckpoint', backref='question')


class Option(db.Model):
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_letter = db.Column(db.String(1), nullable=False)  # 'a', 'b', 'c', 'd'
    option_text = db.Column(db.Text, nullable=False)


class TrafficSign(db.Model):
    __tablename__ = 'traffic_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    sign_code = db.Column(db.String(50), unique=True, nullable=False)
    explanation = db.Column(db.Text)
    category = db.Column(db.String(100))
    filename = db.Column(db.String(255))
    description = db.Column(db.Text)


class QuizSession(db.Model):
    __tablename__ = 'quiz_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_type = db.Column(db.String(50))
    category = db.Column(db.String(100))
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    time_spent_seconds = db.Column(db.Integer)
    score = db.Column(db.Numeric(5, 2))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    challenge_id = db.Column(db.Integer, db.ForeignKey('daily_challenges.id'), nullable=True)  # For daily challenges
    
    # Relationships
    responses = db.relationship('QuizResponse', backref='session', cascade='all, delete-orphan')


class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    category = db.Column(db.String(100))  # Track actual question category
    subcategory = db.Column(db.String(100))  # Track specific subcategory for granular analytics
    user_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)
    time_spent_seconds = db.Column(db.Integer)


class GameScenario(db.Model):
    __tablename__ = 'game_scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    scenario_type = db.Column(db.String(50))  # 'traffic_signs', 'driving_sim', 'memory', 'puzzle', 'time_challenge', 'multiplayer'
    difficulty_level = db.Column(db.Integer, default=1)
    max_score = db.Column(db.Integer)
    time_limit_seconds = db.Column(db.Integer)
    config_json = db.Column(db.Text)  # JSON configuration for the scenario
    template_name = db.Column(db.String(100))  # Template file name for the game
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    min_level_required = db.Column(db.Integer, default=1)  # Minimum user level to play
    is_premium = db.Column(db.Boolean, default=False)  # Premium-only game
    
    # Relationships
    game_sessions = db.relationship('GameSession', backref='scenario')


class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey('game_scenarios.id'), nullable=False)
    score = db.Column(db.Integer)
    time_played_seconds = db.Column(db.Integer)
    mistakes_count = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


# Video model definition moved to end of file to avoid conflicts


class VideoCheckpoint(db.Model):
    __tablename__ = 'video_checkpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    timestamp_seconds = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    is_mandatory = db.Column(db.Boolean, default=False)


# VideoProgress model definition moved to end of file to avoid conflicts

class LearningModuleItem(db.Model):
    __tablename__ = 'learning_module_items'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    item_type = db.Column(db.String(50))  # 'quiz', 'video', 'game'
    item_id = db.Column(db.Integer)  # ID of the quiz/video/game
    order_index = db.Column(db.Integer)
    is_mandatory = db.Column(db.Boolean, default=True)


class UserLearningModule(db.Model):
    __tablename__ = 'user_learning_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    progress_percentage = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'module_id', name='_user_module_uc'),)


class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leaderboard_type = db.Column(db.String(50))  # 'weekly', 'monthly', 'all-time'
    category = db.Column(db.String(100))
    score = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feedback_type = db.Column(db.String(50))  # 'bug', 'feature', 'general'
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='new')  # 'new', 'in-progress', 'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminReport(db.Model):
    """Store all types of admin reports for security monitoring"""
    __tablename__ = 'admin_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(50), nullable=False)  # 'user_feedback', 'system_error', 'security_alert', 'admin_change', 'suspicious_activity'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    status = db.Column(db.String(20), default='new')  # 'new', 'in_progress', 'resolved', 'archived'
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # User related
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    affected_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Technical details
    ip_address = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(db.Text)
    url = db.Column(db.Text)  # URL where issue occurred
    error_message = db.Column(db.Text)  # For system errors
    stack_trace = db.Column(db.Text)  # For technical errors
    
    # Additional data
    metadata_json = db.Column(db.Text)  # JSON string with extra details
    screenshot_filename = db.Column(db.String(255))  # If user uploaded screenshot
    
    # Handling
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    reported_by = db.relationship('User', foreign_keys=[reported_by_user_id], backref='reports_created')
    affected_user = db.relationship('User', foreign_keys=[affected_user_id], backref='reports_affecting')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='reports_assigned')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id], backref='reports_resolved')


class AdminAuditLog(db.Model):
    """Track admin privilege changes for security auditing"""
    __tablename__ = 'admin_audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who made the change
    action = db.Column(db.String(50), nullable=False)  # 'grant_admin', 'revoke_admin', 'login_attempt'
    ip_address = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(db.Text)
    additional_info = db.Column(db.Text)  # JSON string with extra details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='admin_logs_target')
    admin_user = db.relationship('User', foreign_keys=[admin_user_id], backref='admin_logs_performed')

    def to_dict(self):
        return {
            'id': self.id,
            'target_user_id': self.target_user_id,
            'admin_user_id': self.admin_user_id,
            'action': self.action,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'additional_info': self.additional_info,
            'created_at': self.created_at.isoformat(),
            'target_user': self.target_user.username if self.target_user else None,
            'admin_user': self.admin_user.username if self.admin_user else None
        }


# Legacy table for image management (keeping for compatibility)
class QuizImage(db.Model):
    __tablename__ = 'quiz_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    folder = db.Column(db.String(100))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)


class SystemSettings(db.Model):
    """Store system-wide configuration settings for features like ML, notifications, etc."""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(db.String(20), default='string', nullable=False)  # 'boolean', 'integer', 'float', 'string', 'json'
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general', nullable=False, index=True)  # 'ml', 'quiz', 'general', 'security', etc.
    is_public = db.Column(db.Boolean, default=False, nullable=False)  # Can non-admins see this setting?
    is_editable = db.Column(db.Boolean, default=True, nullable=False)  # Can this setting be changed via UI?
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    updated_by_user = db.relationship('User', foreign_keys=[updated_by], backref='settings_updated')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_setting_category_key', 'category', 'setting_key'),
        db.Index('idx_setting_public', 'is_public'),
    )
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}={self.setting_value}>'
    
    def get_typed_value(self):
        """Return the setting value converted to its proper Python type"""
        try:
            if self.setting_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == 'integer':
                return int(self.setting_value)
            elif self.setting_type == 'float':
                return float(self.setting_value)
            elif self.setting_type == 'json':
                import json
                return json.loads(self.setting_value)
            else:  # string
                return self.setting_value
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            # If conversion fails, return the raw string value
            return self.setting_value
    
    def set_typed_value(self, value):
        """Set the setting value from a Python type, converting to string for storage"""
        if self.setting_type == 'boolean':
            self.setting_value = 'true' if value else 'false'
        elif self.setting_type == 'json':
            import json
            self.setting_value = json.dumps(value)
        else:
            self.setting_value = str(value)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.get_typed_value(),
            'setting_type': self.setting_type,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'is_editable': self.is_editable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by_user.username if self.updated_by_user else None
        }
    
    @classmethod
    def get_setting(cls, key, default=None, setting_type=None):
        """Get a setting value by key, with optional type conversion"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            return setting.get_typed_value()
        return default
    
    @classmethod
    def set_setting(cls, key, value, description=None, category='general', setting_type='string', 
                   is_public=False, is_editable=True, updated_by=None):
        """Set a setting value, creating or updating as needed"""
        setting = cls.query.filter_by(setting_key=key).first()
        
        if setting:
            # Update existing setting
            setting.set_typed_value(value)
            setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            # Create new setting
            setting = cls(
                setting_key=key,
                setting_type=setting_type,
                description=description,
                category=category,
                is_public=is_public,
                is_editable=is_editable,
                updated_by=updated_by
            )
            setting.set_typed_value(value)
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_category_settings(cls, category):
        """Get all settings for a specific category"""
        return cls.query.filter_by(category=category).all()
    
    @classmethod
    def get_public_settings(cls):
        """Get all public settings (viewable by non-admins)"""
        return cls.query.filter_by(is_public=True).all()


# VideoShorts model removed - using extended Video model instead per implementation plan


class UserLearningProgress(db.Model):
    """User progress tracking for learning modules and submodules"""
    __tablename__ = 'user_learning_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    submodule_id = db.Column(db.Integer, db.ForeignKey('learning_submodules.id'), nullable=True)
    progress_type = db.Column(db.Enum('module','submodule','content','summary','shorts'), nullable=False)
    status = db.Column(db.Enum('not_started','in_progress','completed','skipped'), default='not_started')
    completion_percentage = db.Column(db.Integer, default=0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    content_viewed = db.Column(db.Boolean, default=False)
    summary_viewed = db.Column(db.Boolean, default=False)
    shorts_watched = db.Column(db.Integer, default=0)
    quiz_attempts = db.Column(db.Integer, default=0)
    quiz_best_score = db.Column(db.Float, default=0.0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='learning_progress')
    learning_module = db.relationship('LearningModules', backref='user_progress')
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_id', 'submodule_id', 'progress_type'),
    )
    
    def __repr__(self):
        return f'<UserLearningProgress user:{self.user_id} module:{self.module_id} submodule:{self.submodule_id} type:{self.progress_type}>'

    def to_dict(self):
        """Serialize the progress record to primitives JSON can handle."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'module_id': self.module_id,
            'submodule_id': self.submodule_id,
            'progress_type': str(self.progress_type),
            'status': str(self.status),
            'completion_percentage': self.completion_percentage,
            'time_spent_minutes': self.time_spent_minutes,
            'content_viewed': self.content_viewed,
            'summary_viewed': self.summary_viewed,
            'shorts_watched': self.shorts_watched,
            'quiz_attempts': self.quiz_attempts,
            'quiz_best_score': self.quiz_best_score,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_last_position(cls, user_id):
        """Get user's last learning position"""
        return cls.query.filter_by(user_id=user_id)\
            .order_by(cls.last_accessed.desc()).first()
    
    @classmethod
    def track_content_access(cls, user_id, module_id, submodule_id, progress_type):
        """Track content access with UPSERT operation"""
        try:
            # Find existing or create new
            progress = cls.query.filter_by(
                user_id=user_id,
                module_id=module_id,
                submodule_id=submodule_id,
                progress_type=progress_type
            ).first()
            
            if not progress:
                progress = cls(
                    user_id=user_id,
                    module_id=module_id,
                    submodule_id=submodule_id,
                    progress_type=progress_type,
                    time_spent_minutes=0
                )
                db.session.add(progress)
            
            progress.last_accessed = datetime.utcnow()
            if progress.status != 'completed':
                progress.status = 'in_progress'
            
            if progress_type == 'content':
                progress.content_viewed = True
            elif progress_type == 'summary':
                progress.summary_viewed = True
            elif progress_type == 'shorts':
                progress.shorts_watched = (progress.shorts_watched or 0) + 1
                
            try:
                db.session.commit()
                return progress
            except Exception as commit_error:
                db.session.rollback()
                # Handle duplicate key error - fetch existing record instead
                if "Duplicate entry" in str(commit_error) or "IntegrityError" in str(commit_error):
                    progress = cls.query.filter_by(
                        user_id=user_id,
                        module_id=module_id, 
                        submodule_id=submodule_id,
                        progress_type=progress_type
                    ).first()
                    
                    if progress:
                        # Update the existing record
                        progress.last_accessed = datetime.utcnow()
                        if progress.status != 'completed':
                            progress.status = 'in_progress'
                        
                        if progress_type == 'shorts':
                            progress.shorts_watched = (progress.shorts_watched or 0) + 1
                        
                        db.session.commit()
                        return progress
                
                # Re-raise if not a duplicate key error
                raise commit_error
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def mark_content_complete(cls, user_id, module_id, submodule_id, progress_type, completion_data=None):
        """Mark content as completed"""
        try:
             # Add debug logging
            #print(f"DEBUG: Marking complete with params:")
            #print(f"  user_id: {user_id}")
            #print(f"  module_id: {module_id}")
            #print(f"  submodule_id: {submodule_id} (type: {type(submodule_id)})")
            #print(f"  progress_type: {progress_type}")
            progress = cls.query.filter_by(
                user_id=user_id,
                module_id=module_id,
                submodule_id=submodule_id,
                progress_type=progress_type
            ).first()
            
            if not progress:
                progress = cls(
                    user_id=user_id,
                    module_id=module_id,
                    submodule_id=submodule_id,
                    progress_type=progress_type,
                    time_spent_minutes=0  # Explicitly initialize to prevent None issues
                )
                db.session.add(progress)
            
            progress.status = 'completed'
            progress.completion_percentage = 100
            progress.completed_at = datetime.utcnow()
            progress.last_accessed = datetime.utcnow()
            
            if completion_data:
                if 'time_spent' in completion_data:
                    # Ensure time_spent_minutes is not None before adding
                    if progress.time_spent_minutes is None:
                        progress.time_spent_minutes = 0
                    progress.time_spent_minutes += completion_data['time_spent']
                if 'quiz_score' in completion_data:
                    # Ensure quiz_best_score is not None before comparison
                    if progress.quiz_best_score is None:
                        progress.quiz_best_score = 0.0
                    progress.quiz_best_score = max(progress.quiz_best_score, completion_data['quiz_score'])
                    if progress.quiz_attempts is None:
                        progress.quiz_attempts = 0
                    progress.quiz_attempts += 1
            
            db.session.commit()
            return progress
            
        except Exception as e:
            db.session.rollback()
            raise e


# UserShortsProgress model removed - using extended VideoProgress model instead per implementation plan

class LearningSubmodules(db.Model):
    __tablename__ = 'learning_submodules'
    
    id = db.Column(db.Integer, primary_key=True)
    # Change this line:
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    submodule_number = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_file_path = db.Column(db.String(500))
    summary_file_path = db.Column(db.String(500))
    shorts_directory = db.Column(db.String(500))
    estimated_minutes = db.Column(db.Integer)
    difficulty_level = db.Column(db.Integer)
    has_quiz = db.Column(db.Boolean)
    quiz_question_count = db.Column(db.Integer)
    has_video_shorts = db.Column(db.Boolean)
    shorts_count = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    ai_generated_content = db.Column(db.Boolean, default=False)
    ai_generated_summary = db.Column(db.Boolean, default=False)
    content_version = db.Column(db.String(50))
    last_content_update = db.Column(db.DateTime)
    engagement_score = db.Column(db.Float)
    completion_rate = db.Column(db.Float)
    average_study_time = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Remove the old Learninmodule relationship
    # The 'module' backref will be created by LearningModules.submodules relationship
    # video_shorts relationship removed - using extended Video model instead
    
class LearningModules(db.Model):
    """
    Comprehensive learning modules table - replaces learning_modules with advanced features
    Designed for AI content generation, analytics, and professional learning management
    """
    __tablename__ = 'learning_modules'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    module_number = db.Column(db.Float, nullable=False, unique=True)  # 1, 2, 3, 4, 5
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    estimated_hours = db.Column(db.Integer)
    
    # Learning structure
    prerequisites = db.Column(db.Text)  # JSON array of prerequisite module numbers
    learning_objectives = db.Column(db.Text)  # JSON array of learning objectives
    content_directory = db.Column(db.String(500))  # Module to content files
    
    # Status and management
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    last_content_update = db.Column(db.DateTime)
    
    # Analytics and performance
    completion_rate = db.Column(db.Float, default=0.0)  # Percentage of users who complete
    average_time_spent = db.Column(db.Integer, default=0)  # Average minutes spent
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    submodules = db.relationship('LearningSubmodules', backref='module', cascade='all, delete-orphan')
    user_modules = db.relationship('UserLearningModule', 
                               primaryjoin='LearningModules.id == UserLearningModule.module_id',
                               backref='learning_module')
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_module_number', 'module_number'),
        db.Index('idx_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<LearningModule {self.module_number}: {self.title}>'
    
    def get_prerequisites_list(self):
        """Parse prerequisites JSON string to list"""
        if self.prerequisites:
            try:
                import json
                return json.loads(self.prerequisites)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_prerequisites_list(self, prerequisites_list):
        """Set prerequisites from list"""
        import json
        self.prerequisites = json.dumps(prerequisites_list) if prerequisites_list else None
    
    def get_learning_objectives_list(self):
        """Parse learning objectives JSON string to list"""
        if self.learning_objectives:
            try:
                import json
                return json.loads(self.learning_objectives)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_learning_objectives_list(self, objectives_list):
        """Set learning objectives from list"""
        import json
        self.learning_objectives = json.dumps(objectives_list) if objectives_list else None
    
    def get_submodule_count(self):
        """Get count of active submodules"""
        return len([sub for sub in self.submodules if sub.is_active])
    
    def get_completion_stats(self):
        """Get completion statistics for this module"""
        total_enrolled = UserLearningModule.query.filter_by(module_id=self.id).count()
        completed = UserLearningModule.query.filter_by(
            module_id=self.id
        ).filter(UserLearningModule.progress_percentage >= 100).count()
        
        return {
            'total_enrolled': total_enrolled,
            'completed': completed,
            'completion_rate': (completed / total_enrolled * 100) if total_enrolled > 0 else 0
        }
    
    def update_analytics(self):
        """Update completion rate and average time spent from user data"""
        stats = self.get_completion_stats()
        self.completion_rate = stats['completion_rate']
        
        # Calculate average time spent (simplified - could be enhanced)
        # This is a placeholder - you'd implement based on your time tracking
        self.average_time_spent = (self.estimated_hours or 0) * 60
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'module_number': self.module_number,
            'title': self.title,
            'description': self.description,
            'estimated_hours': self.estimated_hours,
            'prerequisites': self.get_prerequisites_list(),
            'learning_objectives': self.get_learning_objectives_list(),
            'content_directory': self.content_directory,
            'is_active': self.is_active,
            'ai_generated': self.ai_generated,
            'last_content_update': self.last_content_update.isoformat() if self.last_content_update else None,
            'completion_rate': self.completion_rate,
            'average_time_spent': self.average_time_spent,
            'submodule_count': self.get_submodule_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active_modules(cls):
        """Get all active learning modules ordered by module number"""
        return cls.query.filter_by(is_active=True).order_by(cls.module_number).all()
    
    @classmethod
    def get_module_by_number(cls, module_number):
        """Get module by number (e.g., 1, 2, 3)"""
        return cls.query.filter_by(module_number=module_number, is_active=True).first()
    
    @classmethod
    def get_modules_for_user(cls, user):
        """Get all modules with user progress information"""
        modules = cls.get_active_modules()
        
        # Add user progress information
        for module in modules:
            user_progress = UserLearningModule.query.filter_by(
                user_id=user.id,
                module_id=module.id
            ).first()
            
            # Add progress attributes
            module.user_enrolled = user_progress is not None
            module.user_progress_percentage = user_progress.progress_percentage if user_progress else 0
            module.user_started_at = user_progress.started_at if user_progress else None
            module.user_completed_at = user_progress.completed_at if user_progress else None
            
            # Determine status
            if not user_progress:
                module.user_status = 'not_started'
            elif user_progress.progress_percentage >= 100:
                module.user_status = 'completed'
            elif user_progress.progress_percentage > 0:
                module.user_status = 'in_progress'
            else:
                module.user_status = 'enrolled'
        
        return modules


class Video(db.Model):
    """Extended Video model for TikTok-style short videos and regular content"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    youtube_url = db.Column(db.String(500))
    duration_seconds = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('video_categories.id'))
    difficulty_level = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    thumbnail_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Extended fields for short videos (from migration)
    aspect_ratio = db.Column(db.String(10))  # '9:16' for TikTok-style
    content_type = db.Column(db.String(20), default='video')
    theory_module_ref = db.Column(db.String(10))  # '1.1', '1.2', etc.
    sequence_order = db.Column(db.Integer, default=0)
    
    # Relationships
    progress_records = db.relationship('VideoProgress', backref='video', cascade='all, delete-orphan')
    
    @property
    def is_short_video(self):
        """Check if this is a TikTok-style short video"""
        return self.aspect_ratio == '9:16' or self.content_type == 'short'
    
    @property 
    def file_path(self):
        """Get the file path for this video"""
        if self.youtube_url:
            return self.youtube_url
        return f"/static/videos/{self.filename}" if self.filename else None
    
    def get_user_progress(self, user_id):
        """Get progress for specific user"""
        return VideoProgress.query.filter_by(
            user_id=user_id,
            video_id=self.id
        ).first()
    
    def to_dict(self, user_id=None):
        """Convert to dictionary for API responses"""
        progress = self.get_user_progress(user_id) if user_id else None
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'duration_seconds': self.duration_seconds,
            'submodule_id': self.theory_module_ref,
            'watch_percentage': progress.watch_percentage if progress else 0,
            'is_completed': progress.completed if progress else False,
            'sequence_order': self.sequence_order,
            'aspect_ratio': self.aspect_ratio,
            'content_type': self.content_type,
            'view_count': self.view_count
        }
    
    @classmethod
    def get_shorts_for_submodule(cls, submodule_id):
        """Get all short videos for a specific submodule"""
        return cls.query.filter(
            cls.theory_module_ref == str(submodule_id),
            cls.is_active == True,
            cls.aspect_ratio == '9:16'
        ).order_by(cls.sequence_order).all()
    
    @classmethod
    def get_all_shorts_ordered(cls):
        """Get all short videos ordered by theory module reference and sequence"""
        return cls.query.filter(
            cls.is_active == True,
            cls.aspect_ratio == '9:16',
            cls.theory_module_ref.isnot(None)
        ).order_by(cls.theory_module_ref, cls.sequence_order).all()


class VideoProgress(db.Model):
    """Extended VideoProgress model for tracking video watch progress including shorts"""
    __tablename__ = 'video_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    last_position_seconds = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    checkpoints_passed = db.Column(db.Integer, default=0)
    total_checkpoints = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate progress records
    __table_args__ = (db.UniqueConstraint('user_id', 'video_id', name='_user_video_uc'),)

    @property
    def watch_percentage(self):
        """Calculate watch percentage from position and video duration"""
        if self.video and self.video.duration_seconds > 0:
            return min(100.0, (self.last_position_seconds / self.video.duration_seconds) * 100)
        return 0.0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'watch_percentage': self.watch_percentage,
            'completed': self.completed,
            'last_position_seconds': self.last_position_seconds,
            'interaction_quality': self.interaction_quality,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }