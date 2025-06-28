"""
Advertising Routes for Sertifikatet
API endpoints for ad tracking and revenue management
"""

from flask import request, jsonify, current_app
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import uuid

from . import advertising
from .services import AdTrackingService, UpgradePromptService
from .analytics import AdAnalyticsService
from app.ad_models import AdInteraction, UpgradePrompt, AdRevenueAnalytics
from app import db


@advertising.route('/track/ad-interaction', methods=['POST'])
def track_ad_interaction():
    """Track ad interactions (impressions, clicks, dismissals)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['session_id', 'ad_type', 'ad_placement', 'action', 'page_section']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get user info
        user_id = current_user.id if current_user.is_authenticated else None
        user_tier = current_user.get_subscription_tier() if current_user.is_authenticated else 'free'
        
        # Create ad interaction record
        interaction = AdTrackingService.track_interaction(
            user_id=user_id,
            session_id=data['session_id'],
            ad_type=data['ad_type'],
            ad_placement=data['ad_placement'],
            action=data['action'],
            page_section=data['page_section'],
            ad_provider=data.get('ad_provider', 'google_adsense'),
            user_tier=user_tier,
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            referrer_url=request.headers.get('Referer')
        )
        
        # Check if we should show upgrade prompt
        should_prompt = False
        prompt_reason = None
        
        if user_id and user_tier == 'free':
            should_prompt, prompt_reason = UpgradePromptService.should_show_prompt(
                user_id, data['session_id'], data['action']
            )
        
        response_data = {
            'success': True,
            'interaction_id': interaction.id,
            'should_show_upgrade_prompt': should_prompt,
            'prompt_reason': prompt_reason
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error tracking ad interaction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/track/upgrade-prompt', methods=['POST'])
@login_required
def track_upgrade_prompt():
    """Track upgrade prompt interactions"""
    try:
        data = request.get_json()
        
        required_fields = ['session_id', 'trigger_reason', 'prompt_type', 'action']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Only track for free users
        if current_user.get_subscription_tier() != 'free':
            return jsonify({'error': 'Not applicable for premium users'}), 400
        
        prompt = UpgradePromptService.track_prompt(
            user_id=current_user.id,
            session_id=data['session_id'],
            trigger_reason=data['trigger_reason'],
            prompt_type=data['prompt_type'],
            action=data['action'],
            ad_count_session=data.get('ad_count_session', 0),
            engagement_score=data.get('engagement_score'),
            time_on_site_minutes=data.get('time_on_site_minutes'),
            activities_completed=data.get('activities_completed', 0),
            personalization_data=data.get('personalization_data'),
            conversion_value=149.0 if data['action'] == 'converted' else None
        )
        
        return jsonify({
            'success': True,
            'prompt_id': prompt.id,
            'message': 'Upgrade prompt tracked successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error tracking upgrade prompt: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/upgrade-prompt/check', methods=['POST'])
@login_required
def check_upgrade_prompt():
    """Check if upgrade prompt should be shown to user"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        trigger_context = data.get('trigger_context', 'general')
        
        if not session_id:
            return jsonify({'error': 'Missing session_id'}), 400
        
        # Only for free users
        if current_user.get_subscription_tier() != 'free':
            return jsonify({
                'should_show_prompt': False,
                'reason': 'premium_user'
            }), 200
        
        should_show, reason = UpgradePromptService.should_show_prompt(
            current_user.id, session_id, trigger_context
        )
        
        prompt_data = None
        if should_show:
            prompt_data = UpgradePromptService.get_personalized_prompt(
                current_user.id, reason
            )
        
        return jsonify({
            'should_show_prompt': should_show,
            'reason': reason,
            'prompt_data': prompt_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error checking upgrade prompt: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/analytics/revenue', methods=['GET'])
@login_required
def get_revenue_analytics():
    """Get revenue analytics (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = AdAnalyticsService.get_revenue_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(analytics), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting revenue analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/analytics/placements', methods=['GET'])
@login_required
def get_placement_analytics():
    """Get ad placement performance analytics (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        placement_id = request.args.get('placement_id')
        
        analytics = AdAnalyticsService.get_placement_performance(
            days=days,
            placement_id=placement_id
        )
        
        return jsonify(analytics), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting placement analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/analytics/user-stats', methods=['GET'])
@login_required
def get_user_ad_stats():
    """Get current user's ad interaction statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        stats = AdAnalyticsService.get_user_statistics(
            current_user.id, days=days
        )
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user ad stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/ad-block/detected', methods=['POST'])
def track_ad_block_detection():
    """Track when ad blocker is detected"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        user_id = current_user.id if current_user.is_authenticated else None
        user_tier = current_user.get_subscription_tier() if current_user.is_authenticated else 'free'
        
        # Track ad block detection
        AdTrackingService.track_interaction(
            user_id=user_id,
            session_id=session_id,
            ad_type='detection',
            ad_placement='general',
            action='block_detected',
            page_section=data.get('page_section', 'unknown'),
            user_tier=user_tier,
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            user_agent=request.headers.get('User-Agent')
        )
        
        # Check if we should show upgrade prompt for ad block users
        should_prompt = False
        if user_id and user_tier == 'free':
            should_prompt, _ = UpgradePromptService.should_show_prompt(
                user_id, session_id, 'adblock_detected'
            )
        
        return jsonify({
            'success': True,
            'message': 'Ad block detection tracked',
            'should_show_upgrade_prompt': should_prompt
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error tracking ad block detection: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@advertising.route('/revenue/update-daily', methods=['POST'])
@login_required
def update_daily_revenue():
    """Manually trigger daily revenue analytics update (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        date_str = request.json.get('date') if request.json else None
        target_date = None
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        summary = AdAnalyticsService.update_daily_analytics(target_date)
        
        return jsonify({
            'success': True,
            'message': 'Daily revenue analytics updated',
            'summary': summary.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating daily revenue: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
