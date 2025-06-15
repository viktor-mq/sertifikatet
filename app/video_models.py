# app/video_models.py
from datetime import datetime
from app import db


class VideoCategory(db.Model):
    """Categories for organizing videos"""
    __tablename__ = 'video_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    order_index = db.Column(db.Integer, default=0)
    
    # Relationships
    videos = db.relationship('Video', backref='video_category', lazy='dynamic')


class VideoPlaylist(db.Model):
    """Playlists for organizing videos"""
    __tablename__ = 'video_playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(500))
    is_official = db.Column(db.Boolean, default=True)  # Official vs user-created
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_playlists')
    items = db.relationship('PlaylistItem', backref='playlist', cascade='all, delete-orphan', order_by='PlaylistItem.order_index')


class PlaylistItem(db.Model):
    """Videos in playlists"""
    __tablename__ = 'playlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('video_playlists.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    video = db.relationship('Video', backref='playlist_items')
    
    __table_args__ = (db.UniqueConstraint('playlist_id', 'video_id', name='_playlist_video_uc'),)


class VideoNote(db.Model):
    """User notes on videos"""
    __tablename__ = 'video_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    timestamp_seconds = db.Column(db.Integer, nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='video_notes')
    video = db.relationship('Video', backref='notes')


class VideoSubtitle(db.Model):
    """Subtitles for videos"""
    __tablename__ = 'video_subtitles'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    language_code = db.Column(db.String(10), nullable=False)  # 'no', 'en', etc.
    subtitle_file = db.Column(db.String(255))  # VTT or SRT file path
    is_auto_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    video = db.relationship('Video', backref='subtitles')
    
    __table_args__ = (db.UniqueConstraint('video_id', 'language_code', name='_video_language_uc'),)


class VideoRating(db.Model):
    """User ratings for videos"""
    __tablename__ = 'video_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='video_ratings')
    video = db.relationship('Video', backref='ratings')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='_user_video_rating_uc'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='_rating_range_check')
    )


class VideoBookmark(db.Model):
    """User bookmarks for videos"""
    __tablename__ = 'video_bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='video_bookmarks')
    video = db.relationship('Video', backref='bookmarks')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'video_id', name='_user_video_bookmark_uc'),)


# Update Video model to include category relationship
# This extends the existing Video model from models.py
def update_video_model():
    """Add category_id to Video model if not exists"""
    from app.models import Video
    if not hasattr(Video, 'category_id'):
        Video.category_id = db.Column(db.Integer, db.ForeignKey('video_categories.id'))
