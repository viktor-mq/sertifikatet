# app/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
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
    learning_paths = db.relationship('UserLearningPath', backref='user', cascade='all, delete-orphan')
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


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    quiz_responses = db.relationship('QuizResponse', backref='question')
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
    
    # Relationships
    responses = db.relationship('QuizResponse', backref='session', cascade='all, delete-orphan')


class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
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


class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255))
    youtube_url = db.Column(db.String(255))
    duration_seconds = db.Column(db.Integer)
    category = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('video_categories.id'))
    difficulty_level = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer)
    thumbnail_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    checkpoints = db.relationship('VideoCheckpoint', backref='video', cascade='all, delete-orphan')
    progress = db.relationship('VideoProgress', backref='video')


class VideoCheckpoint(db.Model):
    __tablename__ = 'video_checkpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    timestamp_seconds = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    is_mandatory = db.Column(db.Boolean, default=False)


class VideoProgress(db.Model):
    __tablename__ = 'video_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    last_position_seconds = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    checkpoints_passed = db.Column(db.Integer, default=0)
    total_checkpoints = db.Column(db.Integer)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'video_id', name='_user_video_uc'),)


class LearningPath(db.Model):
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    estimated_hours = db.Column(db.Integer)
    difficulty_level = db.Column(db.Integer, default=1)
    icon_filename = db.Column(db.String(255))
    is_recommended = db.Column(db.Boolean, default=False)
    
    # Relationships
    items = db.relationship('LearningPathItem', backref='path', cascade='all, delete-orphan')
    user_paths = db.relationship('UserLearningPath', backref='path')


class LearningPathItem(db.Model):
    __tablename__ = 'learning_path_items'
    
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'), nullable=False)
    item_type = db.Column(db.String(50))  # 'quiz', 'video', 'game'
    item_id = db.Column(db.Integer)  # ID of the quiz/video/game
    order_index = db.Column(db.Integer)
    is_mandatory = db.Column(db.Boolean, default=True)


class UserLearningPath(db.Model):
    __tablename__ = 'user_learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'), nullable=False)
    progress_percentage = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'path_id', name='_user_path_uc'),)


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


# Legacy table for image management (keeping for compatibility)
class QuizImage(db.Model):
    __tablename__ = 'quiz_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    folder = db.Column(db.String(100))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
