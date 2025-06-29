"""
Server-side Analytics API for GTM Integration
Handles analytics events that need server-side processing
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from datetime import datetime
import json
import logging

# Create blueprint
analytics_api_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

@analytics_api_bp.route('/session-end', methods=['POST'])
def track_session_end():
    """
    Track session end events sent via sendBeacon
    This ensures reliable tracking even when users close the page
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Log session end for server-side analytics
        session_info = {
            'event': 'session_end_server',
            'session_duration': data.get('session_duration', 0),
            'pages_viewed': data.get('pages_viewed', 0),
            'events_tracked': data.get('events_tracked', 0),
            'engagement_score': data.get('engagement_score', 0),
            'exit_page': data.get('exit_page', ''),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
        }
        
        # Log to application logger for analysis
        current_app.logger.info(f"Session End: {json.dumps(session_info)}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Session end tracking error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_api_bp.route('/conversion', methods=['POST'])
def track_conversion():
    """
    Track high-value conversion events server-side
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('conversion_type'):
            return jsonify({'error': 'Invalid conversion data'}), 400
        
        conversion_info = {
            'event': 'server_side_conversion',
            'conversion_type': data.get('conversion_type'),
            'conversion_value': data.get('conversion_value', 0),
            'transaction_id': data.get('transaction_id'),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'user_tier': current_user.get_subscription_tier() if current_user.is_authenticated else 'anonymous',
            'timestamp': datetime.utcnow().isoformat(),
            'source': data.get('source', 'website'),
            'campaign': data.get('utm_campaign'),
            'medium': data.get('utm_medium'),
            'content': data.get('utm_content'),
        }
        
        # Log conversion for server-side analysis
        current_app.logger.info(f"Conversion: {json.dumps(conversion_info)}")
        
        return jsonify({'status': 'success', 'conversion_id': conversion_info['timestamp']}), 200
        
    except Exception as e:
        current_app.logger.error(f"Conversion tracking error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_api_bp.route('/custom-event', methods=['POST'])
def track_custom_event():
    """
    Track custom analytics events from client-side
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('event_name'):
            return jsonify({'error': 'Event name required'}), 400
        
        event_info = {
            'event': 'server_side_custom',
            'event_name': data.get('event_name'),
            'event_category': data.get('event_category', 'general'),
            'event_value': data.get('event_value'),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'session_id': data.get('session_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'page_url': data.get('page_url', ''),
            'referrer': data.get('referrer', ''),
            'custom_parameters': data.get('custom_parameters', {})
        }
        
        # Log custom event
        current_app.logger.info(f"Custom Event: {json.dumps(event_info)}")
        
        return jsonify({'status': 'success', 'event_id': event_info['timestamp']}), 200
        
    except Exception as e:
        current_app.logger.error(f"Custom event tracking error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_api_bp.route('/user-journey', methods=['POST'])
def track_user_journey():
    """
    Track detailed user journey events for funnel analysis
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('journey_step'):
            return jsonify({'error': 'Journey step required'}), 400
        
        journey_info = {
            'event': 'user_journey_step',
            'journey_step': data.get('journey_step'),
            'journey_stage': data.get('journey_stage', 'unknown'),
            'step_value': data.get('step_value', 0),
            'time_in_step': data.get('time_in_step', 0),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'user_tier': current_user.get_subscription_tier() if current_user.is_authenticated else 'anonymous',
            'session_id': data.get('session_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'previous_step': data.get('previous_step'),
            'funnel_id': data.get('funnel_id', 'default'),
            'conversion_probability': data.get('conversion_probability', 0)
        }
        
        # Log journey step
        current_app.logger.info(f"User Journey: {json.dumps(journey_info)}")
        
        return jsonify({'status': 'success', 'journey_id': journey_info['timestamp']}), 200
        
    except Exception as e:
        current_app.logger.error(f"User journey tracking error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_api_bp.route('/health', methods=['GET'])
def analytics_health():
    """
    Health check endpoint for analytics API
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'gtm_container': current_app.config.get('GOOGLE_TAG_MANAGER_ID'),
        'ga_measurement': current_app.config.get('GOOGLE_ANALYTICS_ID')
    }), 200
