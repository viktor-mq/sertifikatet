# app/video/api.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Video, VideoCheckpoint, Question
from app.video_models import VideoCategory, VideoPlaylist
from app.video.services import VideoService

video_api_bp = Blueprint('video_api', __name__, url_prefix='/api/video')


@video_api_bp.route('/checkpoint/<int:checkpoint_id>')
@login_required
def get_checkpoint(checkpoint_id):
    """Get checkpoint question data"""
    checkpoint = VideoCheckpoint.query.get_or_404(checkpoint_id)
    
    if checkpoint.question_id:
        question = checkpoint.question
        return jsonify({
            'checkpoint_id': checkpoint.id,
            'timestamp': checkpoint.timestamp_seconds,
            'is_mandatory': checkpoint.is_mandatory,
            'question': question.question,
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d,
            'image': question.image_filename
        })
    else:
        # No question, just a checkpoint
        return jsonify({
            'checkpoint_id': checkpoint.id,
            'timestamp': checkpoint.timestamp_seconds,
            'is_mandatory': checkpoint.is_mandatory,
            'question': None
        })


@video_api_bp.route('/videos')
@login_required
def get_videos():
    """Get videos with filters"""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    query = Video.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            db.or_(
                Video.title.ilike(f'%{search}%'),
                Video.description.ilike(f'%{search}%')
            )
        )
    
    videos = query.order_by(Video.order_index, Video.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'videos': [{
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'thumbnail': v.thumbnail_filename,
            'duration': v.duration_seconds,
            'category': v.category,
            'youtube_url': v.youtube_url
        } for v in videos.items],
        'total': videos.total,
        'pages': videos.pages,
        'current_page': videos.page
    })


@video_api_bp.route('/categories')
@login_required
def get_categories():
    """Get all video categories"""
    categories = VideoCategory.query.order_by(VideoCategory.order_index).all()
    
    return jsonify({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'icon': c.icon,
            'video_count': c.videos.count()
        } for c in categories]
    })


@video_api_bp.route('/playlists')
@login_required
def get_playlists():
    """Get playlists"""
    playlist_type = request.args.get('type', 'all')
    
    if playlist_type == 'official':
        playlists = VideoPlaylist.query.filter_by(is_official=True).all()
    elif playlist_type == 'user':
        playlists = VideoPlaylist.query.filter_by(created_by=current_user.id).all()
    else:
        # Get both official and user's playlists
        playlists = VideoPlaylist.query.filter(
            db.or_(
                VideoPlaylist.is_official == True,
                VideoPlaylist.created_by == current_user.id
            )
        ).all()
    
    return jsonify({
        'playlists': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'thumbnail_url': p.thumbnail_url,
            'is_official': p.is_official,
            'video_count': len(p.items),
            'created_at': p.created_at.isoformat()
        } for p in playlists]
    })


@video_api_bp.route('/video/<int:video_id>/progress')
@login_required
def get_video_progress(video_id):
    """Get user's progress for a specific video"""
    from app.models import VideoProgress
    
    progress = VideoProgress.query.filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()
    
    if progress:
        return jsonify({
            'last_position': progress.last_position_seconds,
            'completed': progress.completed,
            'checkpoints_passed': progress.checkpoints_passed,
            'total_checkpoints': progress.total_checkpoints
        })
    else:
        return jsonify({
            'last_position': 0,
            'completed': False,
            'checkpoints_passed': 0,
            'total_checkpoints': VideoCheckpoint.query.filter_by(video_id=video_id).count()
        })


@video_api_bp.route('/stats')
@login_required
def get_video_stats():
    """Get user's video learning statistics"""
    from app.models import VideoProgress
    
    # Total videos watched
    total_watched = VideoProgress.query.filter_by(user_id=current_user.id).count()
    
    # Completed videos
    completed = VideoProgress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()
    
    # Total watch time
    total_time = db.session.query(
        db.func.sum(VideoProgress.last_position_seconds)
    ).filter_by(user_id=current_user.id).scalar() or 0
    
    # Videos by category
    from sqlalchemy import func
    category_stats = db.session.query(
        Video.category,
        func.count(VideoProgress.id).label('count')
    ).join(
        VideoProgress, Video.id == VideoProgress.video_id
    ).filter(
        VideoProgress.user_id == current_user.id,
        VideoProgress.completed == True
    ).group_by(Video.category).all()
    
    return jsonify({
        'total_watched': total_watched,
        'completed': completed,
        'total_time_seconds': total_time,
        'completion_rate': (completed / total_watched * 100) if total_watched > 0 else 0,
        'categories': {
            cat: count for cat, count in category_stats
        }
    })


@video_api_bp.route('/recommendations')
@login_required
def get_recommendations():
    """Get personalized video recommendations"""
    limit = request.args.get('limit', 6, type=int)
    recommendations = VideoService.get_video_recommendations(current_user, limit=limit)
    
    return jsonify({
        'recommendations': [{
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'thumbnail': v.thumbnail_filename,
            'duration': v.duration_seconds,
            'category': v.category
        } for v in recommendations]
    })
