# app/video/services.py
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import Video, VideoProgress, VideoCheckpoint, User
from app.video_models import (
    VideoCategory, VideoPlaylist, PlaylistItem, VideoNote,
    VideoSubtitle, VideoRating, VideoBookmark
)
from app.gamification.services import GamificationService
import re


class VideoService:
    """Service for handling video-related operations"""
    
    @staticmethod
    def get_video_details(video_id, user=None):
        """Get video details including user progress if applicable"""
        video = Video.query.get_or_404(video_id)
        
        # Get average rating
        avg_rating = db.session.query(func.avg(VideoRating.rating)).filter_by(
            video_id=video_id
        ).scalar() or 0
        
        total_ratings = VideoRating.query.filter_by(video_id=video_id).count()
        
        # Get user-specific data if user is provided
        user_data = {
            'progress': None,
            'rating': None,
            'bookmarked': False,
            'notes': []
        }
        
        if user:
            # Get user progress
            progress = VideoProgress.query.filter_by(
                user_id=user.id,
                video_id=video_id
            ).first()
            user_data['progress'] = progress
            
            # Get user rating
            rating = VideoRating.query.filter_by(
                user_id=user.id,
                video_id=video_id
            ).first()
            user_data['rating'] = rating.rating if rating else None
            
            # Check if bookmarked
            bookmark = VideoBookmark.query.filter_by(
                user_id=user.id,
                video_id=video_id
            ).first()
            user_data['bookmarked'] = bookmark is not None
            
            # Get user notes
            notes = VideoNote.query.filter_by(
                user_id=user.id,
                video_id=video_id
            ).order_by(VideoNote.timestamp_seconds).all()
            user_data['notes'] = notes
        
        return {
            'video': video,
            'avg_rating': round(avg_rating, 1),
            'total_ratings': total_ratings,
            'user_data': user_data
        }
    
    @staticmethod
    def start_video(user, video_id):
        """Start or resume video for user"""
        # Get or create video progress
        progress = VideoProgress.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if not progress:
            # First time watching
            progress = VideoProgress(
                user_id=user.id,
                video_id=video_id,
                total_checkpoints=VideoCheckpoint.query.filter_by(video_id=video_id).count()
            )
            db.session.add(progress)
            db.session.commit()
            
            # Update daily challenges
            GamificationService.update_daily_challenge_progress(user, 'video', 1)
        
        return progress
    
    @staticmethod
    def update_progress(user, video_id, position_seconds):
        """Update video progress"""
        progress = VideoProgress.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if progress:
            progress.last_position_seconds = position_seconds
            
            # Check if video is completed (within last 10 seconds)
            video = Video.query.get(video_id)
            if video and video.duration_seconds:
                if position_seconds >= video.duration_seconds - 10 and not progress.completed:
                    VideoService.complete_video(user, video_id)
            
            db.session.commit()
        
        return progress
    
    @staticmethod
    def complete_video(user, video_id):
        """Mark video as completed and award XP"""
        progress = VideoProgress.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if progress and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            
            # Award XP
            GamificationService.award_xp(
                user,
                GamificationService.XP_REWARDS['video_complete'],
                'video_complete',
                f'Fullførte video: {progress.video.title}',
                video_id
            )
            
            # Update user progress stats
            if user.progress:
                user.progress.total_videos_watched += 1
                user.progress.videos_completed += 1
            
            # Check achievements
            GamificationService.check_achievements(user, {'video_completed': True})
            
            db.session.commit()
            
            return True
        
        return False
    
    @staticmethod
    def pass_checkpoint(user, video_id, checkpoint_id, answer):
        """Process checkpoint answer"""
        checkpoint = VideoCheckpoint.query.get_or_404(checkpoint_id)
        progress = VideoProgress.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if not progress:
            return {'success': False, 'message': 'Video progress not found'}
        
        # Check answer if it's a question checkpoint
        is_correct = True
        if checkpoint.question_id:
            question = checkpoint.question
            is_correct = answer == question.correct_option
        
        if is_correct or not checkpoint.is_mandatory:
            progress.checkpoints_passed += 1
            db.session.commit()
            
            # Award bonus XP for checkpoint
            if is_correct and checkpoint.question_id:
                GamificationService.award_xp(
                    user,
                    5,  # Bonus XP for checkpoint
                    'video_checkpoint',
                    'Passerte video checkpoint',
                    checkpoint_id
                )
        
        return {
            'success': is_correct or not checkpoint.is_mandatory,
            'is_correct': is_correct,
            'message': 'Riktig!' if is_correct else 'Feil svar, men du kan fortsette.' if not checkpoint.is_mandatory else 'Feil svar. Prøv igjen!'
        }
    
    @staticmethod
    def add_note(user, video_id, timestamp_seconds, note_text):
        """Add a note to video"""
        note = VideoNote(
            user_id=user.id,
            video_id=video_id,
            timestamp_seconds=timestamp_seconds,
            note_text=note_text
        )
        db.session.add(note)
        db.session.commit()
        return note
    
    @staticmethod
    def update_note(user, note_id, note_text):
        """Update an existing note"""
        note = VideoNote.query.filter_by(
            id=note_id,
            user_id=user.id
        ).first()
        
        if note:
            note.note_text = note_text
            note.updated_at = datetime.utcnow()
            db.session.commit()
            return note
        
        return None
    
    @staticmethod
    def delete_note(user, note_id):
        """Delete a note"""
        note = VideoNote.query.filter_by(
            id=note_id,
            user_id=user.id
        ).first()
        
        if note:
            db.session.delete(note)
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def rate_video(user, video_id, rating):
        """Rate a video"""
        if not 1 <= rating <= 5:
            return None
        
        video_rating = VideoRating.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if video_rating:
            video_rating.rating = rating
        else:
            video_rating = VideoRating(
                user_id=user.id,
                video_id=video_id,
                rating=rating
            )
            db.session.add(video_rating)
        
        db.session.commit()
        return video_rating
    
    @staticmethod
    def toggle_bookmark(user, video_id):
        """Toggle video bookmark"""
        bookmark = VideoBookmark.query.filter_by(
            user_id=user.id,
            video_id=video_id
        ).first()
        
        if bookmark:
            db.session.delete(bookmark)
            db.session.commit()
            return False
        else:
            bookmark = VideoBookmark(
                user_id=user.id,
                video_id=video_id
            )
            db.session.add(bookmark)
            db.session.commit()
            return True
    
    @staticmethod
    def get_user_bookmarks(user):
        """Get user's bookmarked videos"""
        bookmarks = VideoBookmark.query.filter_by(
            user_id=user.id
        ).join(Video).order_by(VideoBookmark.created_at.desc()).all()
        
        return [bookmark.video for bookmark in bookmarks]
    
    @staticmethod
    def get_video_recommendations(user, limit=6):
        """Get personalized video recommendations"""
        # Get user's completed videos
        completed_video_ids = db.session.query(VideoProgress.video_id).filter_by(
            user_id=user.id,
            completed=True
        ).scalar_subquery()
        
        # Get videos in same categories as watched videos
        watched_categories = db.session.query(Video.category_id).filter(
            Video.id.in_(db.session.query(VideoProgress.video_id).filter_by(
                user_id=user.id,
                completed=True
            ).scalar_subquery())
        ).distinct().all()
        watched_categories = [cat[0] for cat in watched_categories if cat[0]]
        
        # Recommend unwatched videos from same categories
        recommendations = Video.query.filter(
            ~Video.id.in_(db.session.query(VideoProgress.video_id).filter_by(
                user_id=user.id,
                completed=True
            ).scalar_subquery()),
            Video.category_id.in_(watched_categories) if watched_categories else True,
            Video.is_active == True
        ).order_by(func.random()).limit(limit).all()
        
        # If not enough recommendations, add popular videos
        if len(recommendations) < limit:
            recommendation_ids = [v.id for v in recommendations]
            popular_videos = Video.query.filter(
                ~Video.id.in_(db.session.query(VideoProgress.video_id).filter_by(
                    user_id=user.id,
                    completed=True
                ).scalar_subquery()),
                ~Video.id.in_(recommendation_ids) if recommendation_ids else True,
                Video.is_active == True
            ).join(VideoRating, isouter=True).group_by(Video.id).order_by(
                func.coalesce(func.avg(VideoRating.rating), 0).desc()
            ).limit(limit - len(recommendations)).all()
            
            recommendations.extend(popular_videos)
        
        return recommendations
    
    @staticmethod
    def create_playlist(name, description, user=None, is_official=False):
        """Create a new playlist"""
        playlist = VideoPlaylist(
            name=name,
            description=description,
            created_by=user.id if user else None,
            is_official=is_official
        )
        db.session.add(playlist)
        db.session.commit()
        return playlist
    
    @staticmethod
    def add_to_playlist(playlist_id, video_id, user=None):
        """Add video to playlist"""
        playlist = VideoPlaylist.query.get_or_404(playlist_id)
        
        # Check permissions if user playlist
        if not playlist.is_official and user and playlist.created_by != user.id:
            return None
        
        # Check if already in playlist
        existing = PlaylistItem.query.filter_by(
            playlist_id=playlist_id,
            video_id=video_id
        ).first()
        
        if existing:
            return existing
        
        # Get next order index
        max_order = db.session.query(func.max(PlaylistItem.order_index)).filter_by(
            playlist_id=playlist_id
        ).scalar() or -1
        
        item = PlaylistItem(
            playlist_id=playlist_id,
            video_id=video_id,
            order_index=max_order + 1
        )
        db.session.add(item)
        db.session.commit()
        return item
    
    @staticmethod
    def get_next_video_in_playlist(playlist_id, current_video_id):
        """Get next video in playlist"""
        current_item = PlaylistItem.query.filter_by(
            playlist_id=playlist_id,
            video_id=current_video_id
        ).first()
        
        if not current_item:
            return None
        
        next_item = PlaylistItem.query.filter_by(
            playlist_id=playlist_id
        ).filter(
            PlaylistItem.order_index > current_item.order_index
        ).order_by(PlaylistItem.order_index).first()
        
        return next_item.video if next_item else None
    
    @staticmethod
    def extract_youtube_id(url):
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to readable format"""
        if not seconds:
            return "0:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
