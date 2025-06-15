#!/usr/bin/env python
"""Quick migration script to add video fields"""

from app import create_app, db
from app.models import User, Video, VideoProgress

app = create_app()

with app.app_context():
    # Add new columns if they don't exist
    try:
        # Check if columns exist by querying
        user = User.query.first()
        if user and not hasattr(user, 'subscription_tier'):
            db.engine.execute('ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(20) DEFAULT "free"')
            print("Added subscription_tier to users table")
        
        if user and not hasattr(user, 'is_admin'):
            db.engine.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
            print("Added is_admin to users table")
            
    except Exception as e:
        print(f"Error updating users table: {e}")
    
    try:
        # Update videos table
        video = Video.query.first()
        if video is not None:
            if not hasattr(video, 'is_active'):
                db.engine.execute('ALTER TABLE videos ADD COLUMN is_active BOOLEAN DEFAULT 1')
                print("Added is_active to videos table")
            
            if not hasattr(video, 'view_count'):
                db.engine.execute('ALTER TABLE videos ADD COLUMN view_count INTEGER DEFAULT 0')
                print("Added view_count to videos table")
                
            if not hasattr(video, 'category_id'):
                db.engine.execute('ALTER TABLE videos ADD COLUMN category_id INTEGER')
                print("Added category_id to videos table")
        
    except Exception as e:
        print(f"Error updating videos table: {e}")
    
    try:
        # Update video_progress table
        progress = VideoProgress.query.first()
        if progress is not None and not hasattr(progress, 'updated_at'):
            db.engine.execute('ALTER TABLE video_progress ADD COLUMN updated_at DATETIME')
            print("Added updated_at to video_progress table")
            
    except Exception as e:
        print(f"Error updating video_progress table: {e}")
    
    # Make Viktor an admin
    try:
        viktor = User.query.filter_by(username='Viktor').first()
        if viktor:
            viktor.is_admin = True
            viktor.subscription_tier = 'pro'
            db.session.commit()
            print("Updated Viktor to admin with pro subscription")
    except Exception as e:
        print(f"Error updating Viktor: {e}")
    
    print("Migration completed!")
