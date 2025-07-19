# app/learning/models.py (Simplified - using existing tables)
from datetime import datetime
from app import db
from app.models import User

# We'll use existing models with some extensions
from sqlalchemy.ext.hybrid import hybrid_property

class TheoryLearningPath(db.Model):
    """
    Extends existing learning_paths table for theory modules
    Uses existing table structure with new path_type='theory'
    """
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    estimated_hours = db.Column(db.Integer)
    difficulty_level = db.Column(db.Integer, default=1)
    icon_filename = db.Column(db.String(255))
    is_recommended = db.Column(db.Boolean, default=False)
    
    # New theory-specific fields (added in migration)
    path_type = db.Column(db.String(20), default='traditional')  # 'theory' for theory modules
    module_number = db.Column(db.Float)  # 1.1, 1.2, etc.
    content_file_path = db.Column(db.String(500))
    summary_file_path = db.Column(db.String(500))
    
    # Relationships
    path_items = db.relationship('LearningPathItem', backref='learning_path', lazy='dynamic')
    user_paths = db.relationship('UserLearningPath', backref='learning_path', lazy='dynamic')
    
    def __repr__(self):
        return f'<TheoryLearningPath {self.module_number}: {self.name}>'
    
    @classmethod
    def get_theory_modules(cls):
        """Get all theory learning paths"""
        return cls.query.filter_by(path_type='theory').order_by(cls.module_number).all()
    
    @classmethod
    def get_module_by_number(cls, module_number):
        """Get theory module by number (e.g., 1.1)"""
        return cls.query.filter_by(path_type='theory', module_number=module_number).first()


class TheoryVideo(db.Model):
    """
    Extends existing videos table for TikTok-style shorts
    Uses existing table structure with new content_type='theory_short'
    """
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
    
    # New theory-specific fields (added in migration)
    aspect_ratio = db.Column(db.String(10))  # '9:16' for TikTok-style
    content_type = db.Column(db.String(20), default='video')  # 'theory_short' for theory videos
    theory_module_ref = db.Column(db.String(10))  # '1.1', '1.2', etc.
    sequence_order = db.Column(db.Integer, default=0)
    
    # Relationships
    progress_records = db.relationship('TheoryVideoProgress', backref='video', lazy='dynamic')
    
    def __repr__(self):
        return f'<TheoryVideo {self.theory_module_ref}-{self.sequence_order}: {self.title}>'
    
    @classmethod
    def get_theory_shorts(cls, module_number):
        """Get all theory shorts for a module"""
        return cls.query.filter_by(
            content_type='theory_short',
            theory_module_ref=str(module_number)
        ).order_by(cls.sequence_order).all()


class TheoryUserProgress(db.Model):
    """
    Extends existing user_learning_paths table for theory progress
    Uses existing table structure with new fields
    """
    __tablename__ = 'user_learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'), nullable=False)
    progress_percentage = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # New theory-specific fields (added in migration)
    content_viewed = db.Column(db.Boolean, default=False)
    summary_viewed = db.Column(db.Boolean, default=False)
    videos_watched = db.Column(db.Integer, default=0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='theory_progress')
    
    def __repr__(self):
        return f'<TheoryUserProgress User:{self.user_id} Path:{self.path_id}>'
    
    def mark_content_viewed(self):
        """Mark content as viewed"""
        self.content_viewed = True
        self.update_progress()
    
    def mark_summary_viewed(self):
        """Mark summary as viewed"""
        self.summary_viewed = True
        self.update_progress()
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_items = 2  # content + summary
        completed_items = 0
        
        if self.content_viewed:
            completed_items += 1
        if self.summary_viewed:
            completed_items += 1
            
        # Add video progress
        if self.videos_watched > 0:
            completed_items += min(self.videos_watched / 3, 1)  # Assuming 3 videos per module
            
        self.progress_percentage = min(int((completed_items / total_items) * 100), 100)
        
        if self.progress_percentage >= 100 and not self.completed_at:
            self.completed_at = datetime.utcnow()


class TheoryVideoProgress(db.Model):
    """
    Extends existing video_progress table for theory video tracking
    Uses existing table structure with new fields
    """
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
    
    # New theory-specific fields (added in migration)
    content_type = db.Column(db.String(20), default='video')
    watch_percentage = db.Column(db.Float, default=0.0)
    interaction_quality = db.Column(db.Float, default=0.0)
    
    # Relationships
    user = db.relationship('User', backref='theory_video_progress')
    
    def __repr__(self):
        return f'<TheoryVideoProgress User:{self.user_id} Video:{self.video_id}>'
    
    def mark_watched(self, percentage=1.0):
        """Mark video as watched with percentage"""
        self.watch_percentage = percentage
        self.last_position_seconds = int(self.video.duration_seconds * percentage) if self.video.duration_seconds else 0
        
        if percentage >= 0.9:  # 90% or more considered completed
            self.completed = True
            self.completed_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()


# Existing models we'll use as-is:
# - User (from app.models)
# - LearningPathItem (existing)
# - Questions (existing - for theory quizzes)
# - QuizSessions (existing - for theory quizzes)
