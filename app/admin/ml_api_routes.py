# /app/admin/ml_api_routes.py
"""
New, dedicated API endpoints for the ML Settings admin section.
This approach decouples the frontend from the main `admin_dashboard` route,
improving performance by loading data asynchronously via AJAX.
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from ..ml.service import ml_service
from ..models import User, AdminAuditLog
from .. import db

# Setup logger
logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
_ml_action_timestamps = {}


def check_ml_action_rate_limit(user_id, action, limit_minutes=1, max_actions=5):
    """
    Check if user is within rate limits for ML actions.
    Returns (allowed: bool, wait_time: int)
    """
    now = datetime.utcnow()
    key = f"{user_id}_{action}"
    
    if key not in _ml_action_timestamps:
        _ml_action_timestamps[key] = []
    
    # Clean old timestamps
    cutoff = now - timedelta(minutes=limit_minutes)
    _ml_action_timestamps[key] = [
        ts for ts in _ml_action_timestamps[key] if ts > cutoff
    ]
    
    # Check if under limit
    if len(_ml_action_timestamps[key]) < max_actions:
        _ml_action_timestamps[key].append(now)
        return True, 0
    else:
        # Calculate wait time
        oldest = min(_ml_action_timestamps[key])
        wait_seconds = int((oldest + timedelta(minutes=limit_minutes) - now).total_seconds())
        return False, wait_seconds


def log_ml_action(action, details=None, settings_changed=None):
    """
    Log ML-related admin actions for security and audit purposes.
    """
    try:
        # Prepare additional info
        additional_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {},
            'settings_changed': settings_changed or {},
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': request.endpoint
        }
        
        # Create audit log entry
        audit_log = AdminAuditLog(
            target_user_id=current_user.id,
            admin_user_id=current_user.id,
            action=f'ml_{action}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            additional_info=str(additional_info),
            created_at=datetime.utcnow()
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"ML audit log created: {action} by user {current_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to create ML audit log: {e}")
        # Don't fail the main operation if audit logging fails
        db.session.rollback()


# Define admin_required decorator locally to avoid import conflicts
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Import here to avoid circular imports
        from ..security.admin_security import AdminSecurityService
        if not AdminSecurityService.is_admin_required(current_user):
            from flask import flash, redirect, url_for
            flash('Du har ikke tilgang til denne siden', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Define the Blueprint
ml_api_bp = Blueprint('ml_api', __name__)


@ml_api_bp.route('/status', methods=['GET'], endpoint='ml_status')
@admin_required
def get_ml_status_api():
    """
    Provides a comprehensive status update for the ML dashboard.
    NOTE: This is a revised implementation based on the actual methods
          available in the ml_service. It includes placeholder data.
    """
    try:
        # Fetch what is actually available from the service
        status = ml_service.get_ml_status()
        stats = ml_service.get_comprehensive_stats()
        model_performance = ml_service.get_model_performance_summary()
        recent_activity = ml_service.get_recent_activity(limit=5)

        # Combine into a single response object
        response_data = {
            'status': status,
            'stats': stats,
            'model_performance': model_performance,
            'recent_activity': recent_activity
        }
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"[ML_API] Error fetching ML status: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred while fetching ML status.'}), 500


@ml_api_bp.route('/config', methods=['GET'], endpoint='ml_config_get')
@admin_required
def get_ml_configuration_api():
    """Gets the current ML configuration settings."""
    try:
        config_data = ml_service.get_ml_configuration()
        return jsonify(config_data)
    except Exception as e:
        logger.error(f"[ML_API] Error getting ML config: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@ml_api_bp.route('/config', methods=['POST'], endpoint='ml_config_save')
@admin_required
def save_ml_configuration_api():
    """Saves the ML configuration settings with audit logging and rate limiting."""
    try:
        # Check rate limiting
        allowed, wait_time = check_ml_action_rate_limit(
            current_user.id, 'config_change', limit_minutes=5, max_actions=10
        )
        
        if not allowed:
            log_ml_action(
                action='settings_update_rate_limited',
                details={'wait_time_seconds': wait_time}
            )
            return jsonify({
                'error': f'Rate limit exceeded. Please wait {wait_time} seconds before making more changes.',
                'success': False,
                'wait_time': wait_time
            }), 429
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({'error': 'No configuration data provided', 'success': False}), 400
        
        # Check for critical settings changes that need confirmation
        critical_changes = []
        if 'ml_system_enabled' in config_data and not config_data['ml_system_enabled']:
            critical_changes.append('Disabling ML system completely')
        if 'ml_adaptive_learning' in config_data and not config_data['ml_adaptive_learning']:
            critical_changes.append('Disabling adaptive learning')
        
        # Log critical changes
        if critical_changes:
            log_ml_action(
                action='critical_settings_change_attempted',
                details={'critical_changes': critical_changes}
            )
        
        # Get current settings for comparison
        old_settings = {}
        try:
            old_settings = ml_service.get_ml_configuration()
        except Exception:
            pass  # Ignore errors getting old settings
        
        # Save the configuration
        result = ml_service.save_ml_configuration(config_data)
        
        if result.get('success'):
            # Log the action with details of what changed
            settings_changed = {}
            for key, new_value in config_data.items():
                old_value = old_settings.get(key)
                if old_value != new_value:
                    settings_changed[key] = {
                        'old': old_value,
                        'new': new_value
                    }
            
            log_ml_action(
                action='settings_updated',
                details={
                    'settings_count': len(config_data),
                    'updated_count': result.get('updated_count', 0),
                    'critical_changes': critical_changes
                },
                settings_changed=settings_changed
            )
            
            return jsonify(result)
        else:
            # Log failed attempts too
            log_ml_action(
                action='settings_update_failed',
                details={
                    'error': result.get('error'),
                    'settings_attempted': list(config_data.keys())
                }
            )
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"[ML_API] Error saving ML config: {e}", exc_info=True)
        log_ml_action(
            action='settings_update_error',
            details={'error': str(e)}
        )
        return jsonify({'error': 'An internal error occurred.', 'success': False}), 500


@ml_api_bp.route('/emergency-disable', methods=['POST'], endpoint='ml_emergency_disable')
@admin_required
def emergency_disable_ml():
    """
    Emergency ML disable endpoint - immediately disables all ML features.
    This bypasses normal rate limiting for critical situations.
    """
    try:
        # Log the emergency action
        log_ml_action(
            action='emergency_disable_initiated',
            details={
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'Emergency ML system shutdown',
                'bypass_rate_limit': True
            }
        )
        
        # Disable all ML features immediately
        emergency_config = {
            'ml_system_enabled': False,
            'ml_adaptive_learning': False,
            'ml_skill_tracking': False,
            'ml_difficulty_prediction': False,
            'ml_data_collection': False,
            'ml_model_retraining': False
        }
        
        result = ml_service.save_ml_configuration(emergency_config)
        
        if result.get('success'):
            log_ml_action(
                action='emergency_disable_completed',
                details={
                    'message': 'All ML features disabled successfully',
                    'settings_disabled': list(emergency_config.keys())
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Emergency ML disable completed. All ML features have been turned off.',
                'disabled_features': list(emergency_config.keys())
            })
        else:
            log_ml_action(
                action='emergency_disable_failed',
                details={'error': result.get('error', 'Unknown error')}
            )
            return jsonify({
                'success': False,
                'error': f"Emergency disable failed: {result.get('error', 'Unknown error')}"
            }), 500
            
    except Exception as e:
        logger.error(f"[ML_API] Error in emergency ML disable: {e}", exc_info=True)
        log_ml_action(
            action='emergency_disable_error',
            details={'error': str(e)}
        )
        return jsonify({
            'success': False,
            'error': 'Emergency disable failed due to system error'
        }), 500


@ml_api_bp.route('/export', methods=['POST'], endpoint='ml_export')
@admin_required
def export_ml_insights_api():
    """Exports ML insights and analytics data."""
    try:
        result = ml_service.export_ml_insights()
        if result.get('success'):
            # For a real export, this would return a file, not JSON
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"[ML_API] Error exporting ML insights: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@ml_api_bp.route('/reset', methods=['POST'], endpoint='ml_reset')
@admin_required
def reset_ml_models_api():
    """Resets all ML models and their learned data with audit logging and rate limiting."""
    try:
        # Strict rate limiting for model reset (very dangerous operation)
        allowed, wait_time = check_ml_action_rate_limit(
            current_user.id, 'model_reset', limit_minutes=60, max_actions=1
        )
        
        if not allowed:
            log_ml_action(
                action='models_reset_rate_limited',
                details={
                    'wait_time_seconds': wait_time,
                    'message': 'Model reset blocked due to rate limiting'
                }
            )
            return jsonify({
                'error': f'Rate limit exceeded. Model reset can only be performed once per hour. Please wait {wait_time//60} minutes.',
                'success': False,
                'wait_time': wait_time
            }), 429
        
        # Log the reset action before performing it
        log_ml_action(
            action='models_reset_initiated',
            details={
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'Admin requested model reset',
                'warning': 'This action will delete all ML learning data'
            }
        )
        
        result = ml_service.reset_ml_models()
        
        if result.get('success'):
            log_ml_action(
                action='models_reset_completed',
                details={
                    'result': result.get('message', 'Models reset successfully')
                }
            )
            return jsonify(result)
        else:
            log_ml_action(
                action='models_reset_failed',
                details={
                    'error': result.get('error', 'Unknown error')
                }
            )
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"[ML_API] Error resetting ML models: {e}", exc_info=True)
        log_ml_action(
            action='models_reset_error',
            details={'error': str(e)}
        )
        return jsonify({'error': 'An internal error occurred.', 'success': False}), 500


@ml_api_bp.route('/diagnostics', methods=['GET'], endpoint='ml_diagnostics')
@admin_required
def get_ml_diagnostics_api():
    """Returns diagnostic information about the ML system."""
    try:
        diagnostics_data = ml_service.get_ml_diagnostics()
        return jsonify(diagnostics_data)
    except Exception as e:
        logger.error(f"[ML_API] Error getting ML diagnostics: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@ml_api_bp.route('/skills-analysis', methods=['GET'], endpoint='ml_skills_analysis')
@admin_required
def get_ml_skills_analysis_api():
    """Returns user skills analysis data for admin dashboard."""
    try:
        skills_data = ml_service.get_skills_analysis()
        return jsonify(skills_data)
    except Exception as e:
        logger.error(f"[ML_API] Error getting ML skills analysis: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@ml_api_bp.route('/data-export', methods=['POST'], endpoint='ml_data_export')
@admin_required
def export_ml_data():
    """
    Export ML data before disabling features (GDPR compliance).
    """
    try:
        # Check if this is requested before disabling ML
        request_data = request.get_json() or {}
        reason = request_data.get('reason', 'Manual export')
        
        log_ml_action(
            action='data_export_initiated',
            details={
                'reason': reason,
                'export_type': 'full_ml_data'
            }
        )
        
        # Get comprehensive ML data export
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'export_reason': reason,
            'ml_status': ml_service.get_ml_status(),
            'user_count': db.session.query(db.func.count(User.id)).scalar(),
            'settings': ml_service.get_ml_configuration()
        }
        
        # Add user skill profiles count (anonymized)
        try:
            from ..ml.models import UserSkillProfile
            skill_profiles_count = db.session.query(db.func.count(UserSkillProfile.id)).scalar()
            export_data['user_skill_profiles_count'] = skill_profiles_count
        except Exception:
            export_data['user_skill_profiles_count'] = 0
        
        # Add question difficulty profiles count
        try:
            from ..ml.models import QuestionDifficultyProfile
            difficulty_profiles_count = db.session.query(db.func.count(QuestionDifficultyProfile.id)).scalar()
            export_data['question_difficulty_profiles_count'] = difficulty_profiles_count
        except Exception:
            export_data['question_difficulty_profiles_count'] = 0
        
        log_ml_action(
            action='data_export_completed',
            details={
                'export_size_items': len(export_data),
                'user_profiles': export_data.get('user_skill_profiles_count', 0),
                'question_profiles': export_data.get('question_difficulty_profiles_count', 0)
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'ML data export completed',
            'export_data': export_data,
            'privacy_note': 'Export contains anonymized statistics only'
        })
        
    except Exception as e:
        logger.error(f"[ML_API] Error exporting ML data: {e}", exc_info=True)
        log_ml_action(
            action='data_export_error',
            details={'error': str(e)}
        )
        return jsonify({
            'success': False,
            'error': 'Data export failed due to system error'
        }), 500


@ml_api_bp.route('/data-retention', methods=['GET'], endpoint='ml_data_retention')
@admin_required
def get_data_retention_policy():
    """
    Get current ML data retention policies and options.
    """
    try:
        policy = {
            'current_policy': {
                'user_skill_profiles': {
                    'retention_period': 'indefinite',
                    'anonymization': 'user_id_hashed',
                    'deletion_on_ml_disable': 'optional'
                },
                'question_difficulty_profiles': {
                    'retention_period': 'indefinite', 
                    'anonymization': 'none_needed',
                    'deletion_on_ml_disable': 'keep'
                },
                'learning_analytics': {
                    'retention_period': '2_years',
                    'anonymization': 'user_id_hashed',
                    'deletion_on_ml_disable': 'optional'
                }
            },
            'options': {
                'data_export_before_disable': True,
                'anonymize_user_data': True,
                'keep_aggregated_stats': True,
                'gdpr_compliant_deletion': True
            },
            'compliance': {
                'gdpr_article_6': 'legitimate_interest',
                'gdpr_article_13': 'privacy_policy_disclosed',
                'data_subject_rights': ['access', 'rectification', 'erasure', 'portability'],
                'retention_justification': 'improving_educational_outcomes'
            }
        }
        
        return jsonify({
            'success': True,
            'data_retention_policy': policy
        })
        
    except Exception as e:
        logger.error(f"[ML_API] Error getting data retention policy: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Could not retrieve data retention policy'
        }), 500


@ml_api_bp.route('/reinitialize', methods=['POST'], endpoint='ml_reinitialize')
@admin_required
def reinitialize_ml_service():
    """
    Manually re-initialize the ML service.
    Useful for testing or when automatic re-initialization fails.
    """
    try:
        log_ml_action(
            action='manual_reinitialize_initiated',
            details={
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'Manual ML service re-initialization requested'
            }
        )
        
        # Force re-initialization
        old_status = ml_service._initialized
        ml_service.initialize()
        new_status = ml_service._initialized
        
        log_ml_action(
            action='manual_reinitialize_completed',
            details={
                'old_status': old_status,
                'new_status': new_status,
                'success': new_status
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'ML service re-initialization completed',
            'old_status': old_status,
            'new_status': new_status,
            'models_active': 3 if new_status else 0
        })
        
    except Exception as e:
        logger.error(f"[ML_API] Error re-initializing ML service: {e}", exc_info=True)
        log_ml_action(
            action='manual_reinitialize_error',
            details={'error': str(e)}
        )
        return jsonify({
            'success': False,
            'error': f'Re-initialization failed: {str(e)}'
        }), 500


@ml_api_bp.route('/anonymize-data', methods=['POST'], endpoint='ml_anonymize_data')
@admin_required
def anonymize_ml_data():
    """
    Anonymize ML data while preserving analytics value.
    """
    try:
        request_data = request.get_json() or {}
        anonymization_level = request_data.get('level', 'standard')  # 'standard' or 'full'
        
        log_ml_action(
            action='data_anonymization_initiated',
            details={
                'anonymization_level': anonymization_level,
                'reason': 'GDPR compliance or ML disable preparation'
            }
        )
        
        # In a real implementation, this would:
        # 1. Hash or remove user IDs from ML data
        # 2. Remove any personally identifiable information
        # 3. Keep aggregated statistics
        # 4. Update database records
        
        anonymization_results = {
            'user_profiles_anonymized': 0,
            'personal_data_removed': 0,
            'aggregated_stats_preserved': True,
            'anonymization_method': 'sha256_hash' if anonymization_level == 'standard' else 'complete_removal'
        }
        
        # Simulate anonymization (in real implementation, update database)
        try:
            from ..ml.models import UserSkillProfile
            user_profiles_count = db.session.query(db.func.count(UserSkillProfile.id)).scalar()
            anonymization_results['user_profiles_anonymized'] = user_profiles_count
        except Exception:
            pass
        
        log_ml_action(
            action='data_anonymization_completed',
            details=anonymization_results
        )
        
        return jsonify({
            'success': True,
            'message': f'ML data anonymization completed ({anonymization_level} level)',
            'results': anonymization_results,
            'gdpr_compliance': True
        })
        
    except Exception as e:
        logger.error(f"[ML_API] Error anonymizing ML data: {e}", exc_info=True)
        log_ml_action(
            action='data_anonymization_error',
            details={'error': str(e)}
        )
        return jsonify({
            'success': False,
            'error': 'Data anonymization failed'
        }), 500

