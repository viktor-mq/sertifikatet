# app/video/routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Video, VideoCheckpoint, Question
from app.video_models import VideoCategory, VideoPlaylist, PlaylistItem
from app.video.services import VideoService
from app.video.utils import allowed_video_file, save_video_file, generate_thumbnail
from app.gamification.services import GamificationService
from app.utils.decorators import admin_required
from app.utils.subscription_decorators import video_access_required, subscription_required
import os

video_bp = Blueprint('video', __name__, url_prefix='/video')


@video_bp.route('/')
@login_required
@video_access_required
def index():
    """Video library main page"""
    # Get categories
    categories = VideoCategory.query.order_by(VideoCategory.order_index).all()
    
    # Get featured/popular videos
    featured_videos = Video.query.filter_by(is_active=True).order_by(
        Video.created_at.desc()
    ).limit(6).all()
    
    # Get user's recent videos
    recent_videos = []
    if current_user.is_authenticated:
        from app.models import VideoProgress
        recent_progress = VideoProgress.query.filter_by(
            user_id=current_user.id
        ).order_by(VideoProgress.updated_at.desc()).limit(6).all()
        recent_videos = [p.video for p in recent_progress]
    
    # Get official playlists
    playlists = VideoPlaylist.query.filter_by(is_official=True).all()
    
    return render_template('video/index.html',
                         categories=categories,
                         featured_videos=featured_videos,
                         recent_videos=recent_videos,
                         playlists=playlists)


@video_bp.route('/category/<int:category_id>')
@login_required
@video_access_required
def category(category_id):
    """Videos in a specific category"""
    category = VideoCategory.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    
    videos = Video.query.filter_by(
        category_id=category_id,
        is_active=True
    ).order_by(Video.order_index, Video.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('video/category.html',
                         category=category,
                         videos=videos)


@video_bp.route('/watch/<int:video_id>')
@login_required
@video_access_required
def watch(video_id):
    """Watch video page"""
    video_data = VideoService.get_video_details(video_id, current_user)
    
    # Start or get progress
    progress = VideoService.start_video(current_user, video_id)
    
    # Get checkpoints
    checkpoints = VideoCheckpoint.query.filter_by(
        video_id=video_id
    ).order_by(VideoCheckpoint.timestamp_seconds).all()
    
    # Get playlist info if video is in a playlist
    playlist_item = PlaylistItem.query.filter_by(video_id=video_id).first()
    playlist = None
    next_video = None
    
    if playlist_item:
        playlist = playlist_item.playlist
        next_video = VideoService.get_next_video_in_playlist(
            playlist.id, video_id
        )
    
    # Get related videos
    related_videos = Video.query.filter(
        Video.category_id == video_data['video'].category_id,
        Video.id != video_id,
        Video.is_active == True
    ).order_by(db.func.random()).limit(6).all()
    
    return render_template('video/watch.html',
                         **video_data,
                         progress=progress,
                         checkpoints=checkpoints,
                         playlist=playlist,
                         next_video=next_video,
                         related_videos=related_videos)


@video_bp.route('/update-progress', methods=['POST'])
@login_required
@video_access_required
def update_progress():
    """Update video progress (AJAX)"""
    data = request.get_json()
    video_id = data.get('video_id')
    position = data.get('position', 0)
    total_duration = data.get('total_duration', 0)
    
    progress = VideoService.update_progress(current_user, video_id, position)
    
    # Check if video was just completed
    was_completed = False
    if progress and progress.completed:
        was_completed = True
    
    response_data = {
        'success': True,
        'completed': progress.completed if progress else False
    }
    
    # Add analytics data if video was completed
    if was_completed:
        video = Video.query.get(video_id)
        response_data['analytics_data'] = {
            'user_id': current_user.id,
            'video_id': video_id,
            'video_title': video.title if video else '',
            'category': video.category if video else '',
            'completion_percentage': 100,
            'watch_time_seconds': total_duration,
            'total_duration_seconds': total_duration,
            'checkpoints_passed': progress.checkpoints_passed if progress else 0
        }
    
    return jsonify(response_data)


@video_bp.route('/checkpoint/<int:checkpoint_id>/answer', methods=['POST'])
@login_required
def answer_checkpoint(checkpoint_id):
    """Answer checkpoint question (AJAX)"""
    data = request.get_json()
    answer = data.get('answer')
    video_id = data.get('video_id')
    
    result = VideoService.pass_checkpoint(
        current_user, video_id, checkpoint_id, answer
    )
    
    return jsonify(result)


@video_bp.route('/note', methods=['POST'])
@login_required
def add_note():
    """Add note to video (AJAX)"""
    data = request.get_json()
    video_id = data.get('video_id')
    timestamp = data.get('timestamp', 0)
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'success': False, 'message': 'Note text is required'})
    
    note = VideoService.add_note(current_user, video_id, timestamp, text)
    
    return jsonify({
        'success': True,
        'note': {
            'id': note.id,
            'timestamp': note.timestamp_seconds,
            'text': note.note_text,
            'created_at': note.created_at.isoformat()
        }
    })


@video_bp.route('/note/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    """Update note (AJAX)"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'success': False, 'message': 'Note text is required'})
    
    note = VideoService.update_note(current_user, note_id, text)
    
    if note:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Note not found'}), 404


@video_bp.route('/note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """Delete note (AJAX)"""
    success = VideoService.delete_note(current_user, note_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Note not found'}), 404


@video_bp.route('/rate', methods=['POST'])
@login_required
def rate_video():
    """Rate video (AJAX)"""
    data = request.get_json()
    video_id = data.get('video_id')
    rating = data.get('rating')
    
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid rating'}), 400
    
    VideoService.rate_video(current_user, video_id, rating)
    
    # Get updated average rating
    video_data = VideoService.get_video_details(video_id)
    
    return jsonify({
        'success': True,
        'avg_rating': video_data['avg_rating'],
        'total_ratings': video_data['total_ratings']
    })


@video_bp.route('/bookmark/<int:video_id>', methods=['POST'])
@login_required
def toggle_bookmark(video_id):
    """Toggle video bookmark (AJAX)"""
    bookmarked = VideoService.toggle_bookmark(current_user, video_id)
    
    return jsonify({
        'success': True,
        'bookmarked': bookmarked
    })


@video_bp.route('/bookmarks')
@login_required
def bookmarks():
    """User's bookmarked videos"""
    videos = VideoService.get_user_bookmarks(current_user)
    
    return render_template('video/bookmarks.html', videos=videos)


@video_bp.route('/playlists')
@login_required
def playlists():
    """Browse playlists"""
    official_playlists = VideoPlaylist.query.filter_by(is_official=True).all()
    
    user_playlists = []
    if current_user.is_authenticated:
        user_playlists = VideoPlaylist.query.filter_by(
            created_by=current_user.id
        ).all()
    
    return render_template('video/playlists.html',
                         official_playlists=official_playlists,
                         user_playlists=user_playlists)


@video_bp.route('/playlist/<int:playlist_id>')
@login_required
def playlist(playlist_id):
    """View playlist"""
    playlist = VideoPlaylist.query.get_or_404(playlist_id)
    
    # Check access for private playlists
    if not playlist.is_official and playlist.created_by != current_user.id:
        flash('Du har ikke tilgang til denne spillelisten', 'warning')
        return redirect(url_for('video.playlists'))
    
    return render_template('video/playlist.html', playlist=playlist)


@video_bp.route('/playlist/create', methods=['GET', 'POST'])
@login_required
@subscription_required('premium')
def create_playlist():
    """Create user playlist"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Spillelistenavn er påkrevd', 'error')
            return redirect(url_for('video.create_playlist'))
        
        playlist = VideoService.create_playlist(
            name, description, current_user, is_official=False
        )
        
        flash('Spilleliste opprettet!', 'success')
        return redirect(url_for('video.playlist', playlist_id=playlist.id))
    
    return render_template('video/create_playlist.html')


@video_bp.route('/playlist/<int:playlist_id>/add/<int:video_id>', methods=['POST'])
@login_required
def add_to_playlist(playlist_id, video_id):
    """Add video to playlist (AJAX)"""
    item = VideoService.add_to_playlist(playlist_id, video_id, current_user)
    
    if item:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Kunne ikke legge til video'}), 400


@video_bp.route('/search')
@login_required
@video_access_required
def search():
    """Search videos"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('video.index'))
    
    # Search in title and description
    videos = Video.query.filter(
        db.or_(
            Video.title.ilike(f'%{query}%'),
            Video.description.ilike(f'%{query}%')
        ),
        Video.is_active == True
    ).paginate(page=page, per_page=12, error_out=False)
    
    return render_template('video/search.html',
                         query=query,
                         videos=videos)


@video_bp.route('/recommended')
@login_required
@video_access_required
def recommended():
    """Personalized recommendations"""
    recommendations = VideoService.get_video_recommendations(current_user, limit=12)
    
    return render_template('video/recommended.html',
                         videos=recommendations)


# Admin routes for uploading videos
@video_bp.route('/admin/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_upload():
    """Admin video upload"""
    from app.utils.decorators import admin_required
    
    @admin_required
    def upload():
        if request.method == 'POST':
            # Handle video upload
            title = request.form.get('title')
            description = request.form.get('description')
            category_id = request.form.get('category_id', type=int)
            youtube_url = request.form.get('youtube_url')
            video_file = request.files.get('video_file')
            
            if not title:
                flash('Tittel er påkrevd', 'error')
                return redirect(url_for('video.admin_upload'))
            
            video = Video(
                title=title,
                description=description,
                category_id=category_id
            )
            
            # Handle YouTube URL
            if youtube_url:
                youtube_id = VideoService.extract_youtube_id(youtube_url)
                if youtube_id:
                    video.youtube_url = f'https://www.youtube.com/embed/{youtube_id}'
                else:
                    flash('Ugyldig YouTube URL', 'error')
                    return redirect(url_for('video.admin_upload'))
            
            # Handle file upload
            elif video_file and allowed_video_file(video_file.filename):
                filename = save_video_file(video_file)
                video.filename = filename
                
                # Generate thumbnail
                thumbnail = generate_thumbnail(filename)
                if thumbnail:
                    video.thumbnail_filename = thumbnail
            else:
                flash('Vennligst oppgi enten YouTube URL eller last opp en videofil', 'error')
                return redirect(url_for('video.admin_upload'))
            
            db.session.add(video)
            db.session.commit()
            
            flash('Video lastet opp!', 'success')
            return redirect(url_for('video.watch', video_id=video.id))
        
        categories = VideoCategory.query.order_by(VideoCategory.name).all()
        return render_template('video/admin_upload.html', categories=categories)
    
    return upload()
