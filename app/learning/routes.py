# app/learning/routes.py
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.learning import learning_bp
from app.learning.services import LearningService
from app.learning.content_manager import ContentManager
from app import db
import logging
from app.models import UserLearningProgress

logger = logging.getLogger(__name__)


@learning_bp.route('/')
@login_required
def index():
    """Main learning index route - redirects to dashboard"""
    return redirect(url_for('learning.theory_dashboard'))

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
    """Submodule content page - shows theory content with reading/video toggle"""
    try:
        # Get content type from URL parameter (default to reading)
        content_type = request.args.get('type', 'reading')  # 'reading' or 'video'
        
        # Get submodule details with BOTH reading and video progress
        submodule_data = LearningService.get_submodule_details(submodule_id, current_user)
        
        if not submodule_data:
            flash('Undermodulen ble ikke funnet', 'error')
            return redirect(url_for('learning.theory_dashboard'))
        
        # Load reading content from files (EXISTING LOGIC - UNCHANGED)
        content_data = ContentManager.get_submodule_content(submodule_id)
        if not content_data:
            content_data = {
                'detailed': {'html_content': '<p>Detaljert innhold kommer snart...</p>'},
                'kort': {'html_content': '<p>Kort sammendrag kommer snart...</p>'},
                'shorts_available': False,
                'shorts_count': 0
            }
        
        # Get video data for video mode
        video_data = None
        if content_type == 'video' or submodule_data.get('has_video_shorts', False):
            video_data = LearningService.get_submodule_shorts(submodule_id, current_user)
        
        # Track content access based on mode
        if content_type == 'reading':
            LearningService.track_content_access(current_user, submodule_id, 'content')
        elif content_type == 'video':
            LearningService.track_video_access(current_user, submodule_id)
        
        return render_template('learning/submodule_content.html',
                             submodule=submodule_data,
                             content=content_data,
                             video_data=video_data,
                             content_type=content_type)
                             
    except Exception as e:
        logger.error(f"Error loading submodule {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av innholdet', 'error')
        return redirect(url_for('learning.theory_dashboard'))


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
        
        # Check for specific video to start from (continue functionality)
        start_video_id = request.args.get('start_video', type=int)
        start_video_index = 0  # Default to first video
        
        if start_video_id:
            # Find the index of the video to start from
            for i, video in enumerate(shorts_data):
                if video.get('id') == start_video_id:
                    start_video_index = i
                    logger.info(f"Starting shorts player from video {start_video_id} at index {i}")
                    break
            else:
                logger.warning(f"Start video {start_video_id} not found in submodule {submodule_id}, starting from beginning")
        
        # Track shorts access for progress tracking
        LearningService.track_content_access(current_user, submodule_id, 'shorts')
        
        return render_template('learning/shorts_player.html',
                             submodule=submodule_data,
                             shorts=shorts_data,
                             start_video_index=start_video_index)
    except Exception as e:
        logger.error(f"Error loading shorts for submodule {submodule_id}: {str(e)}")
        flash('Det oppstod en feil ved lasting av videoene', 'error')
        return redirect(url_for('learning.submodule_content', submodule_id=submodule_id))


@learning_bp.route('/continue')
@login_required
def continue_learning():
    """Continue where user left off"""
    try:
        # Get user's last learning position
        last_position = LearningService.get_user_last_position(current_user)
        
        if last_position and last_position['submodule_number']:
            # Redirect based on progress type
            if last_position['progress_type'] == 'shorts':
                # For video progress, include the specific video ID to resume from
                shorts_url = url_for('learning.shorts_player', 
                                    submodule_id=last_position['submodule_number'])
                
                # Add video ID parameter if we have specific video position
                if last_position.get('last_video_id'):
                    shorts_url += f"?start_video={last_position['last_video_id']}"
                
                return redirect(shorts_url)
            else:
                return redirect(url_for('learning.submodule_content', 
                                      submodule_id=last_position['submodule_number']))
        elif last_position and last_position['module_id']:
            # Redirect to module overview if no specific submodule
            return redirect(url_for('learning.module_overview', 
                                  module_id=last_position['module_id']))
        else:
            # First time user - redirect to dashboard
            flash('Velkommen! Start med å utforske læringsmodulene.', 'info')
            return redirect(url_for('learning.dashboard'))
            
    except Exception as e:
        logger.error(f"Error getting continue position: {str(e)}")
        flash('Kunne ikke finne din siste posisjon. Starter fra begynnelsen.', 'warning')
        return redirect(url_for('learning.dashboard'))


# Also add a route name fix for the shorts player
@learning_bp.route('/theory/shorts/<float:submodule_id>')
@login_required
def theory_shorts_player(submodule_id):
    """Redirect to shorts player (for backward compatibility)"""
    return redirect(url_for('learning.shorts_player', submodule_id=submodule_id))


@learning_bp.route('/api/get-next', methods=['POST'])
@login_required
def get_next_content_api():
    """API endpoint for getting next content recommendation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Ingen data mottatt'}), 400
        
        current_submodule = data.get('submodule_id')
        current_content_type = data.get('content_type', 'content')
        
        if not current_submodule:
            return jsonify({'success': False, 'error': 'Mangler submodule_id'}), 400
        
        # Get next content recommendation
        next_content = LearningService.get_next_content_smart(
            current_user, current_submodule, current_content_type
        )
        
        if next_content:
            return jsonify({
                'success': True,
                'next_content': next_content,
                'has_next': True
            })
        else:
            return jsonify({
                'success': True,
                'next_content': None,
                'has_next': False,
                'message': 'Du har fullført alt tilgjengelig innhold!'
            })
            
    except Exception as e:
        logger.error(f"Error getting next content: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke hente neste innhold'
        }), 500


@learning_bp.route('/api/complete-content', methods=['POST'])
@login_required
def complete_content_api():
    """API endpoint for marking content as complete"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Ingen data mottatt'}), 400
        
        content_type = data.get('content_type', 'content')
        content_id = data.get('content_id')
        completion_data = data.get('completion_data', {})
        
        if not content_id:
            return jsonify({'success': False, 'error': 'Mangler content_id'}), 400
        
        # Mark content as complete
        result = LearningService.mark_content_complete(
            current_user, content_type, content_id, completion_data
        )
        # Ensure progress is JSON‑serialisable
        progress_obj = result.get('progress')
        if hasattr(progress_obj, 'to_dict'):
            result['progress'] = progress_obj.to_dict()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Innhold markert som fullført',
                'progress': result.get('progress', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Kunne ikke markere som fullført')
            }), 500
            
    except Exception as e:
        logger.error(f"Error marking content complete: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Kunne ikke markere innhold som fullført'
        }), 500


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
        # Ensure returned progress is JSON‑friendly
        if hasattr(result, 'to_dict'):
            result = result.to_dict()
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


# ============================================================================
# NEW VIDEO PROGRESS API ROUTES (Phase 2 Implementation)
# ============================================================================

@learning_bp.route('/api/video-progress/<float:submodule_id>')
@login_required
def get_video_progress_api(submodule_id):
    """API endpoint to get current video progress for submodule"""
    try:
        video_progress = LearningService.get_submodule_video_progress(current_user, submodule_id)
        
        return jsonify({
            'success': True,
            'submodule_id': submodule_id,
            'progress': video_progress
        })
        
    except Exception as e:
        logger.error(f"Error getting video progress API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not load video progress'
        }), 500


@learning_bp.route('/api/mark-videos-complete/<float:submodule_id>', methods=['POST'])
@login_required  
def mark_videos_complete_api(submodule_id):
    """API endpoint to mark all videos in submodule as complete"""
    try:
        result = LearningService.mark_submodule_videos_complete(current_user, submodule_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Markerte {result['videos_completed']} videoer som fullført",
                'videos_completed': result['videos_completed'],
                'completion_percentage': result['completion_percentage']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
            
    except Exception as e:
        logger.error(f"Error marking videos complete API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not mark videos as complete'
        }), 500


@learning_bp.route('/api/cross-complete/<float:submodule_id>', methods=['POST'])
@login_required
def cross_complete_api(submodule_id):
    """API endpoint for cross-completion (mark other format as complete)"""
    try:
        data = request.get_json()
        format_type = data.get('format')  # 'reading' or 'video'
        
        if format_type == 'video':
            # User completed reading, mark videos as complete
            result = LearningService.mark_submodule_videos_complete(current_user, submodule_id)
            action = "videoer som fullført"
        elif format_type == 'reading':
            # User completed videos, mark reading as complete  
            result = LearningService.mark_content_complete(current_user, 'content', submodule_id)
            action = "lesing som fullført"
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid format specified'
            }), 400
        
        if result.get('success', True):  # mark_content_complete might not return success field
            return jsonify({
                'success': True,
                'message': f"Markerte {action}",
                'format': format_type
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in cross-completion API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not complete cross-completion'
        }), 500


@learning_bp.route('/api/progress-summary/<float:submodule_id>')
@login_required
def progress_summary_api(submodule_id):
    """API endpoint to get complete progress summary for both formats"""
    try:
        submodule_data = LearningService.get_submodule_details(submodule_id, current_user)
        
        if not submodule_data:
            return jsonify({
                'success': False,
                'error': 'Submodule not found'
            }), 404
        
        return jsonify({
            'success': True,
            'submodule_id': submodule_id,
            'reading_progress': submodule_data['reading_progress'],
            'video_progress': submodule_data['video_progress'],
            'overall_progress': submodule_data.get('overall_progress', {
                'status': 'not_started',
                'completion_percentage': 0
            })
        })
        
    except Exception as e:
        logger.error(f"Error getting progress summary API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Could not load progress summary'
        }), 500





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
        # Get content type from URL parameter
        content_type = request.args.get('type', 'reading')  # 'reading' or 'video'
        
        if content_type == 'video':
            # Get video progress for all modules
            modules_data = LearningService.get_dashboard_video_progress(current_user)
        else:
            # Get reading progress (existing functionality)
            modules_data = LearningService.get_user_modules_progress(current_user)
        
        # Get user learning stats
        learning_stats = LearningService.get_user_learning_stats(current_user)
        
        # Get recommended next steps
        recommendations = LearningService.get_recommendations(current_user)
        
        # Pass content_type to template
        return render_template('learning/theory_dashboard.html',
                             modules=modules_data,
                             stats=learning_stats,
                             recommendations=recommendations,
                             content_type=content_type)
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
@learning_bp.route('/api/shorts/mock/progress', methods=['POST'])
@login_required  
def update_mock_shorts_progress_api():
    """Handle progress updates for mock videos - saves to database in development mode"""
    try:
        data = request.get_json()
        
        # In development mode, save mock progress to database for testing
        from flask import current_app
        if current_app.config.get('ENVIRONMENT') == 'development':
            video_id = data.get('video_id') or data.get('shorts_id')
            if video_id:
                # Use the real progress tracking service
                # Filter to only allowed fields to match the real endpoint
                allowed_fields = ['watch_percentage', 'watch_time_seconds', 'watch_status']
                filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                
                if filtered_data:
                    result = LearningService.update_shorts_progress(
                        current_user, video_id, filtered_data
                    )
                    return jsonify(result)
        
        # Fallback to mock response for production or missing data
        return jsonify({
            'success': True,
            'message': 'Mock progress tracked',
            'watch_percentage': data.get('watch_percentage', 0)
        })
    except Exception as e:
        logger.error(f"Error in mock progress tracking: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Mock progress tracking failed'
        }), 400

@learning_bp.route('/api/shorts/mock/like', methods=['POST'])
@login_required  
def toggle_mock_shorts_like():
    """Handle like toggle for mock videos - saves to database in development mode"""
    try:
        data = request.get_json()
        
        # In development mode, save mock likes to database for testing
        from flask import current_app
        if current_app.config.get('ENVIRONMENT') == 'development':
            video_id = data.get('video_id') or data.get('shorts_id')
            if video_id:
                # Use the real like toggle service
                result = LearningService.toggle_shorts_like(
                    current_user, video_id
                )
                return jsonify(result)
        
        # Fallback to mock response for production or missing data
        return jsonify({
            'success': True,
            'liked': True,  # Always return liked for mock
            'message': 'Mock like tracked'
        })
    except Exception as e:
        logger.error(f"Error in mock like tracking: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Mock like tracking failed'
        }), 400

@learning_bp.route('/api/shorts/all-session', methods=['GET'])
@login_required
def get_session_shorts_api():
    """Get all shorts for cross-module session with continuation support"""
    try:
        starting_submodule = request.args.get('start')
        starting_video_id = request.args.get('start_video', type=int)
        
        videos = LearningService.get_all_shorts_for_session(
            current_user, 
            starting_submodule, 
            starting_video_id=starting_video_id
        )
        
        return jsonify({
            'success': True,
            'videos': videos,
            'count': len(videos)
        })
    except Exception as e:
        logger.error(f"Error getting session shorts: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not load session videos'
        }), 500

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
        from app.models import Video, VideoProgress
        
        # Get video short
        video_short = Video.query.get_or_404(shorts_id)
        
        # Get user progress
        progress = VideoProgress.query.filter_by(
            user_id=current_user.id,
            video_id=shorts_id
        ).first()
        
        analytics_data = {
            'total_views': video_short.view_count,
            'total_likes': 0,  # TODO: Add like tracking field in future
            'completion_rate': 0,  # TODO: Calculate from VideoProgress records
            'average_watch_time': video_short.duration_seconds,
            'user_progress': {
                'watch_status': 'completed' if progress and progress.completed else 'not_watched',
                'watch_percentage': progress.watch_percentage if progress else 0,
                'liked': progress.interaction_quality > 0 if progress else False,
                'watch_time': progress.last_position_seconds if progress else 0
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


# NEW API ROUTES FOR VIDEO SHORTS USING VIDEO/VIDEOPROGRESS MODELS

# Duplicate route removed - using get_session_shorts_api above


@learning_bp.route('/api/shorts/mock/progress', methods=['POST'])
@login_required  
def update_mock_shorts_progress():
    """Handle progress updates for mock videos - saves to database in development mode"""
    try:
        data = request.get_json()
        
        # In development mode, save mock progress to database for testing
        from flask import current_app
        if current_app.config.get('ENVIRONMENT') == 'development':
            video_id = data.get('video_id') or data.get('shorts_id')
            if video_id:
                # Use the real progress tracking service
                # Filter to only allowed fields to match the real endpoint
                allowed_fields = ['watch_percentage', 'watch_time_seconds', 'watch_status']
                filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                
                if filtered_data:
                    result = LearningService.update_shorts_progress(
                        current_user, video_id, filtered_data
                    )
                    return jsonify(result)
        
        # Fallback to mock response for production or missing data
        return jsonify({
            'success': True,
            'message': 'Mock progress tracked',
            'watch_percentage': data.get('watch_percentage', 0)
        })
    except Exception as e:
        logger.error(f"Error in mock progress tracking: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Mock progress tracking failed'
        }), 400
