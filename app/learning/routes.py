# app/learning/routes.py
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.learning import learning_bp
from app.learning.services import LearningService
from app.learning.content_manager import ContentManager
from app import db
import logging

logger = logging.getLogger(__name__)


@learning_bp.route('/')
@login_required
def index():
    """Main learning index route - redirects to dashboard"""
    return redirect(url_for('learning.dashboard'))


@learning_bp.route('/dashboard')
@login_required
def dashboard():
    """Main learning dashboard - shows all modules with progress"""
    try:
        # Get all modules with user progress
        modules_data = LearningService.get_user_modules_progress(current_user)
        
        # Get user learning stats
        learning_stats = LearningService.get_user_learning_stats(current_user)
        
        # Get recommended next steps
        recommendations = LearningService.get_recommendations(current_user)
        
        return render_template('learning/index.html',
                             modules=modules_data,
                             stats=learning_stats,
                             recommendations=recommendations)
    except Exception as e:
        logger.error(f"Error loading learning dashboard: {str(e)}")
        flash('Det oppstod en feil ved lasting av læringsoversikten', 'error')
        return redirect(url_for('main.index'))


@learning_bp.route('/module/<int:module_id>/enroll', methods=['POST'])
@login_required
def enroll_in_module(module_id):
    """Enroll user in a module"""
    try:
        success = LearningService.enroll_user_in_module(current_user, module_id)
        if success:
            flash('Du er nå påmeldt modulen!', 'success')
        else:
            flash('Du er allerede påmeldt denne modulen', 'info')
        return redirect(url_for('learning.module_overview', module_id=module_id))
    except Exception as e:
        logger.error(f"Error enrolling in module {module_id}: {str(e)}")
        flash('Det oppstod en feil ved påmelding', 'error')
        return redirect(url_for('learning.dashboard'))


@learning_bp.route('/module/<int:module_id>')
@login_required
def module_overview(module_id):
    """Module overview page - shows submodules with progress"""
    try:
        # Get module details with user progress
        module_data = LearningService.get_module_details(module_id, current_user)
        
        if not module_data:
            flash('Modulen ble ikke funnet', 'error')
            return redirect(url_for('learning.dashboard'))
        
        # Get submodules with progress
        submodules_data = LearningService.get_submodules_progress(module_id, current_user)
        
        return render_template('learning/module_overview.html',
                             module=module_data,
                             submodules=submodules_data)
    except Exception as e:
        logger.error(f"Error loading module {module_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av modulen', 'error')
        return redirect(url_for('learning.dashboard'))


@learning_bp.route('/module/<float:submodule_id>')
@login_required
def submodule_content(submodule_id):
    """Submodule content page - shows detailed theory content with toggle"""
    try:
        # Get submodule details with content
        submodule_data = LearningService.get_submodule_details(submodule_id, current_user)
        
        if not submodule_data:
            flash('Undermodulen ble ikke funnet', 'error')
            return redirect(url_for('learning.dashboard'))
        
        # Load content from files
        content_data = ContentManager.get_submodule_content(submodule_id)
        if not content_data:
            content_data = {
                'detailed': {'html_content': '<p>Detaljert innhold kommer snart...</p>'},
                'kort': {'html_content': '<p>Kort sammendrag kommer snart...</p>'},
                'shorts_available': False,
                'shorts_count': 0
            }
        
        # Start or update progress
        LearningService.start_submodule_content(current_user, submodule_id)
        
        return render_template('learning/submodule_content.html',
                             submodule=submodule_data,
                             content=content_data)
    except Exception as e:
        logger.error(f"Error loading submodule {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av innholdet', 'error')
        return redirect(url_for('learning.dashboard'))


@learning_bp.route('/shorts/<float:submodule_id>')
@login_required
def shorts_player(submodule_id):
    """TikTok-style shorts player for submodule videos"""
    try:
        # Get submodule details
        submodule_data = LearningService.get_submodule_details(submodule_id, current_user)
        
        if not submodule_data:
            flash('Undermodulen ble ikke funnet', 'error')
            return redirect(url_for('learning.dashboard'))
        
        # Get video shorts for this submodule
        shorts_data = LearningService.get_submodule_shorts(submodule_id, current_user)
        
        if not shorts_data:
            flash('Ingen videoer funnet for denne undermodulen ennå', 'info')
            return redirect(url_for('learning.submodule_content', submodule_id=submodule_id))
        
        # Start shorts progress tracking
        LearningService.start_submodule_shorts(current_user, submodule_id)
        
        return render_template('learning/shorts_player.html',
                             submodule=submodule_data,
                             shorts=shorts_data)
    except Exception as e:
        logger.error(f"Error loading shorts for submodule {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av videoene', 'error')
        return redirect(url_for('learning.submodule_content', submodule_id=submodule_id))


@learning_bp.route('/progress')
@login_required
def progress_tracker():
    """Detailed progress tracking page"""
    try:
        # Get comprehensive progress data
        progress_data = LearningService.get_comprehensive_progress(current_user)
        
        return render_template('learning/progress_tracker.html',
                             progress=progress_data)
    except Exception as e:
        logger.error(f"Error loading progress tracker: {str(e)}")
        flash('Det oppstod en feil ved lasting av fremgangsdata', 'error')
        return redirect(url_for('learning.dashboard'))


# API routes for progress tracking and interactions
@learning_bp.route('/api/progress', methods=['POST'])
@login_required
def api_update_progress():
    """Update learning progress (AJAX)"""
    try:
        data = request.get_json()
        
        result = LearningService.update_progress(
            user=current_user,
            content_type=data.get('content_type'),
            content_id=data.get('content_id'),
            progress_data=data.get('progress_data', {})
        )
        
        return jsonify({
            'success': True,
            'progress': result
        })
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke oppdatere fremgang'
        }), 400


@learning_bp.route('/api/complete-content', methods=['POST'])
@login_required
def api_complete_content():
    """Mark content as completed (AJAX)"""
    try:
        data = request.get_json()
        
        result = LearningService.mark_content_complete(
            user=current_user,
            content_type=data.get('content_type'),
            content_id=data.get('content_id'),
            completion_data=data.get('completion_data', {})
        )
        
        return jsonify({
            'success': True,
            'completion': result
        })
    except Exception as e:
        logger.error(f"Error marking content complete: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke markere innhold som fullført'
        }), 400


@learning_bp.route('/api/track-time', methods=['POST'])
@login_required
def api_track_time():
    """Track time spent on content (AJAX)"""
    try:
        data = request.get_json()
        
        result = LearningService.track_time_spent(
            user=current_user,
            content_type=data.get('content_type'),
            content_id=data.get('content_id'),
            time_seconds=data.get('time_seconds', 0)
        )
        
        return jsonify({
            'success': True,
            'time_tracked': result
        })
    except Exception as e:
        logger.error(f"Error tracking time: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke spore tid'
        }), 400


@learning_bp.route('/api/get-next', methods=['GET'])
@login_required
def api_get_next():
    """Get next recommended content (AJAX)"""
    try:
        current_content_type = request.args.get('content_type')
        current_content_id = request.args.get('content_id')
        
        next_content = LearningService.get_next_content(
            user=current_user,
            current_content_type=current_content_type,
            current_content_id=current_content_id
        )
        
        return jsonify({
            'success': True,
            'next_content': next_content
        })
    except Exception as e:
        logger.error(f"Error getting next content: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke hente neste innhold'
        }), 400


# Video shorts specific API endpoints
@learning_bp.route('/api/shorts/watch', methods=['POST'])
@login_required
def api_shorts_watch():
    """Update shorts watch progress (AJAX)"""
    try:
        data = request.get_json()
        
        result = LearningService.update_shorts_progress(
            user=current_user,
            shorts_id=data.get('shorts_id'),
            watch_data={
                'watch_percentage': data.get('watch_percentage', 0),
                'watch_time_seconds': data.get('watch_time_seconds', 0),
                'swipe_direction': data.get('swipe_direction')
            }
        )
        
        return jsonify({
            'success': True,
            'watch_progress': result
        })
    except Exception as e:
        logger.error(f"Error updating shorts watch progress: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke oppdatere video fremgang'
        }), 400


@learning_bp.route('/api/shorts/like', methods=['POST'])
@login_required
def api_shorts_like():
    """Toggle like on shorts video (AJAX)"""
    try:
        data = request.get_json()
        
        result = LearningService.toggle_shorts_like(
            user=current_user,
            shorts_id=data.get('shorts_id')
        )
        
        return jsonify({
            'success': True,
            'liked': result
        })
    except Exception as e:
        logger.error(f"Error toggling shorts like: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke like video'
        }), 400


# ===== THEORY MODE ROUTES (TikTok Learning System Integration) =====

@learning_bp.route('/theory')
@login_required
def theory_dashboard():
    """Theory mode dashboard - shows learning modules with progress"""
    try:
        # Get all modules with user progress
        modules_data = LearningService.get_user_modules_progress(current_user)
        
        # Get user learning stats
        learning_stats = LearningService.get_user_learning_stats(current_user)
        
        # Get recommended next steps
        recommendations = LearningService.get_recommendations(current_user)
        
        return render_template('learning/theory_dashboard.html',
                             modules=modules_data,
                             stats=learning_stats,
                             recommendations=recommendations)
    except Exception as e:
        logger.error(f"Error loading theory dashboard: {str(e)}")
        flash('Det oppstod en feil ved lasting av teorioversikten', 'error')
        return redirect(url_for('learning.index'))


@learning_bp.route('/theory/module/<int:module_id>')
@login_required
def theory_module_overview(module_id):
    """Theory module overview page - shows submodules with progress"""
    try:
        # Get module details with user progress
        module_data = LearningService.get_module_details(module_id, current_user)
        
        if not module_data:
            flash('Modulen ble ikke funnet', 'error')
            return redirect(url_for('learning.theory_dashboard'))
        
        # Get submodules with progress
        submodules_data = LearningService.get_submodules_progress(module_id, current_user)
        
        return render_template('learning/module_overview.html',
                             module=module_data,
                             submodules=submodules_data)
    except Exception as e:
        logger.error(f"Error loading theory module {module_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av modulen', 'error')
        return redirect(url_for('learning.theory_dashboard'))


@learning_bp.route('/theory/module/<float:submodule_id>')
@login_required
def theory_submodule_content(submodule_id):
    """Theory submodule content page - shows content and summary"""
    try:
        # Get submodule details with content
        submodule_data = LearningService.get_submodule_details(submodule_id, current_user)
        
        if not submodule_data:
            flash('Delmodulen ble ikke funnet', 'error')
            return redirect(url_for('learning.theory_dashboard'))
        
        # Load content from files
        content_data = ContentManager.get_submodule_content(submodule_id)
        if not content_data:
            content_data = {
                'detailed': {'html_content': '<p>Detaljert innhold kommer snart...</p>'},
                'kort': {'html_content': '<p>Kort sammendrag kommer snart...</p>'},
                'shorts_available': False,
                'shorts_count': 0
            }
        
        # Track that user accessed this content
        LearningService.track_content_access(
            user=current_user,
            submodule_id=int(submodule_id * 10) // 10,  # Convert 1.1 to 1
            content_type='content'
        )
        
        return render_template('learning/submodule_content.html',
                             submodule=submodule_data,
                             content=content_data)
    except Exception as e:
        logger.error(f"Error loading theory submodule {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av innholdet', 'error')
        return redirect(url_for('learning.theory_dashboard'))


@learning_bp.route('/theory/shorts/<float:submodule_id>')
@login_required
def theory_shorts_player(submodule_id):
    """Theory shorts player - TikTok-style video player"""
    try:
        # Get shorts for this submodule
        shorts_data = LearningService.get_submodule_shorts(submodule_id, current_user)
        
        if not shorts_data:
            flash('Ingen videoer funnet for denne delen', 'error')
            return redirect(url_for('learning.theory_submodule_content', submodule_id=submodule_id))
        
        return render_template('learning/shorts_player.html',
                             shorts=shorts_data,
                             submodule_id=submodule_id)
    except Exception as e:
        logger.error(f"Error loading theory shorts for {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av videoene', 'error')
        return redirect(url_for('learning.theory_dashboard'))


# Additional routes required by the template
@learning_bp.route('/module/<int:module_id>>')
@login_required
def view_module(module_id):
    """View a specific learning module"""
    try:
        # For now, redirect to module overview
        return redirect(url_for('learning.module_overview', module_id=module_id))
    except Exception as e:
        logger.error(f"Error viewing module {module_id}: {str(e)}")
        flash('Læringsveien ble ikke funnet', 'error')
        return redirect(url_for('learning.index'))


@learning_bp.route('/my-modules')
@login_required
def my_modules():
    """Show user's enrolled learning modules"""
    try:
        # For now, show empty state
        return render_template('learning/my_modules.html', modules=[])
    except Exception as e:
        logger.error(f"Error loading my modules: {str(e)}")
        flash('Kunne ikke laste dine læringsveier', 'error')
        return redirect(url_for('learning.index'))


@learning_bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """Get personalized recommendations (AJAX)"""
    try:
        recommendations = LearningService.get_recommendations(current_user)
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke hente anbefalinger'
        }), 400


# Video Shorts API Endpoints
@learning_bp.route('/api/shorts/<int:shorts_id>/progress', methods=['POST'])
@login_required
def update_shorts_progress(shorts_id):
    """Update user progress for watching a video short"""
    try:
        watch_data = request.get_json()
        if not watch_data:
            return jsonify({
                'success': False,
                'error': 'Ingen data mottatt'
            }), 400
        
        # Validate watch data
        allowed_fields = ['watch_percentage', 'watch_time_seconds', 'watch_status']
        filtered_data = {k: v for k, v in watch_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return jsonify({
                'success': False,
                'error': 'Ugyldig data format'
            }), 400
        
        # Update progress using service
        result = LearningService.update_shorts_progress(current_user, shorts_id, filtered_data)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating shorts progress for {shorts_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke oppdatere fremgang'
        }), 500


@learning_bp.route('/api/shorts/<int:shorts_id>/like', methods=['POST'])
@login_required
def toggle_shorts_like(shorts_id):
    """Toggle like status for a video short"""
    try:
        result = LearningService.toggle_shorts_like(current_user, shorts_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error toggling shorts like for {shorts_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke oppdatere like-status'
        }), 500


@learning_bp.route('/api/shorts/<int:shorts_id>/analytics', methods=['GET'])
@login_required
def get_shorts_analytics(shorts_id):
    """Get analytics data for a video short"""
    try:
        from app.models import VideoShorts, UserShortsProgress
        
        # Get video short
        video_short = VideoShorts.query.get_or_404(shorts_id)
        
        # Get user progress
        progress = UserShortsProgress.query.filter_by(
            user_id=current_user.id,
            shorts_id=shorts_id
        ).first()
        
        analytics_data = {
            'total_views': video_short.view_count,
            'total_likes': video_short.like_count,
            'completion_rate': video_short.completion_rate,
            'average_watch_time': video_short.average_watch_time,
            'user_progress': {
                'watch_status': progress.watch_status if progress else 'not_watched',
                'watch_percentage': progress.watch_percentage if progress else 0,
                'liked': progress.liked if progress else False,
                'watch_time': progress.watch_time_seconds if progress else 0
            }
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data
        })
        
    except Exception as e:
        logger.error(f"Error getting shorts analytics for {shorts_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke hente analytics'
        }), 500
