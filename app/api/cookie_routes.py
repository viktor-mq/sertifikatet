# app/api/cookie_routes.py
from flask import request, jsonify, session, current_app
from datetime import datetime
import uuid
from . import api_bp
from .. import db
from ..notification_models import CookieConsent, UserNotificationPreferences
from flask_login import current_user
from sqlalchemy.orm.attributes import flag_modified


@api_bp.route('/cookie-consent', methods=['POST'])
def save_cookie_consent():
    """Save cookie consent preferences (GDPR compliance)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract consent preferences
        preferences = {
            'necessary': True,  # Always true, required for functionality
            'analytics': data.get('analytics', False),
            'marketing': data.get('marketing', False)
        }
        
        # Get user info for audit trail
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        version = current_app.config.get('COOKIE_POLICY_VERSION', '1.0')  # Get version from config
        
        if current_user.is_authenticated:
            # Logged-in user - save to notification preferences
            prefs = current_user.notification_preferences
            if not prefs:
                # Create notification preferences if they don't exist
                from ..notification_models import UserNotificationPreferences
                prefs = UserNotificationPreferences(user_id=current_user.id)
                db.session.add(prefs)
                db.session.flush()
            
            # Update cookie preferences
            prefs.cookie_preferences = preferences
            prefs.cookie_consent_date = datetime.utcnow()
            prefs.cookie_consent_version = version
            prefs.updated_at = datetime.utcnow()  # Explicitly update timestamp
            
            # Mark JSON field as modified to ensure SQLAlchemy detects the change
            flag_modified(prefs, 'cookie_preferences')
            
            # Sync marketing consent with email marketing preferences
            prefs.marketing_emails = preferences.get('marketing', False)
            prefs.partner_offers = preferences.get('marketing', False)
            
        else:
            # Anonymous user - save to cookie_consents table
            session_id = session.get('cookie_session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                session['cookie_session_id'] = session_id
            
            # Get or create consent record
            consent = CookieConsent.get_or_create_consent(session_id)
            consent.update_preferences(
                preferences=preferences,
                version=version,
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'preferences': preferences,
            'message': 'Cookie preferences saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to save preferences: {str(e)}'}), 500


@api_bp.route('/cookie-consent', methods=['GET'])
def get_cookie_consent():
    """Get current cookie consent preferences"""
    try:
        if current_user.is_authenticated:
            # Logged-in user
            prefs = current_user.notification_preferences
            if prefs and prefs.cookie_preferences:
                return jsonify({
                    'preferences': prefs.cookie_preferences,
                    'consent_date': prefs.cookie_consent_date.isoformat() if prefs.cookie_consent_date else None,
                    'version': prefs.cookie_consent_version
                })
        else:
            # Anonymous user
            session_id = session.get('cookie_session_id')
            if session_id:
                consent = CookieConsent.query.filter_by(session_id=session_id).first()
                if consent:
                    return jsonify({
                        'preferences': consent.preferences,
                        'consent_date': consent.consent_date.isoformat(),
                        'version': consent.version
                    })
        
        # No consent found
        return jsonify({
            'preferences': None,
            'consent_date': None,
            'version': None
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get preferences: {str(e)}'}), 500
