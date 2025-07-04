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
from ..ml.service import ml_service
from ..models import User

# Setup logger
logger = logging.getLogger(__name__)

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
    """Saves the ML configuration settings."""
    try:
        config_data = request.get_json()
        result = ml_service.save_ml_configuration(config_data)
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"[ML_API] Error saving ML config: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


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
    """Resets all ML models and their learned data."""
    try:
        result = ml_service.reset_ml_models()
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"[ML_API] Error resetting ML models: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


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

