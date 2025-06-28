"""
Advertising Services for Sertifikatet
Business logic for ad tracking and upgrade prompt management
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.ad_models import AdInteraction, UpgradePrompt
import json


class AdTrackingService:
    """Service for tracking ad interactions"""
    
    @staticmethod
    def track_interaction(user_id, session_id, ad_type, ad_placement, action, page_section, **kwargs):
        """Create and save ad interaction record"""
        try:
            interaction = AdInteraction(
                user_id=user_id,
                session_id=session_id,
                ad_type=ad_type,
                ad_placement=ad_placement,
                action=action,
                page_section=page_section,
                ad_provider=kwargs.get('ad_provider', 'google_adsense'),
                revenue_cpm=kwargs.get('revenue_cpm'),
                user_tier=kwargs.get('user_tier', 'free'),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                referrer_url=kwargs.get('referrer_url')
            )
            
            db.session.add(interaction)
            db.session.commit()
            
            current_app.logger.info(f"Ad interaction tracked: {action} on {ad_placement} for user {user_id}")
            return interaction
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error tracking ad interaction: {str(e)}")
            raise
    
    @staticmethod
    def get_session_ad_count(session_id, user_id=None):
        """Get number of ads shown in current session"""
        query = AdInteraction.query.filter(
            AdInteraction.session_id == session_id,
            AdInteraction.action == 'impression'
        )
        
        if user_id:
            query = query.filter(AdInteraction.user_id == user_id)
        
        return query.count()
    
    @staticmethod
    def get_recent_ad_interactions(user_id, minutes=30):
        """Get recent ad interactions for a user"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return AdInteraction.query.filter(
            AdInteraction.user_id == user_id,
            AdInteraction.timestamp >= cutoff_time
        ).all()
    
    @staticmethod
    def has_ad_blocker(session_id):
        """Check if session has ad blocker based on detection events"""
        blocker_detection = AdInteraction.query.filter(
            AdInteraction.session_id == session_id,
            AdInteraction.action == 'block_detected'
        ).first()
        
        return blocker_detection is not None


class UpgradePromptService:
    """Service for managing upgrade prompts and conversions"""
    
    # Configuration for prompt triggers
    PROMPT_CONFIG = {
        'high_ad_exposure': {
            'min_ads_per_session': 5,
            'min_ads_per_hour': 8,
            'cooldown_hours': 2
        },
        'high_engagement': {
            'min_activities': 3,
            'min_time_minutes': 10,
            'engagement_threshold': 0.7,
            'cooldown_hours': 4
        },
        'adblock_detected': {
            'immediate_trigger': True,
            'cooldown_hours': 24
        },
        'repeated_usage': {
            'min_sessions': 3,
            'timeframe_days': 7,
            'cooldown_hours': 48
        }
    }
    
    @staticmethod
    def should_show_prompt(user_id, session_id, trigger_context='general'):
        """Determine if upgrade prompt should be shown"""
        try:
            # Check recent prompts to avoid spam
            recent_prompt = UpgradePromptService._get_recent_prompt(user_id)
            if recent_prompt:
                return False, 'recent_prompt_shown'
            
            # Check different trigger conditions
            for trigger_type, config in UpgradePromptService.PROMPT_CONFIG.items():
                should_trigger, reason = UpgradePromptService._check_trigger_condition(
                    user_id, session_id, trigger_type, config, trigger_context
                )
                
                if should_trigger:
                    return True, trigger_type
            
            return False, 'no_trigger_conditions_met'
            
        except Exception as e:
            current_app.logger.error(f"Error checking upgrade prompt conditions: {str(e)}")
            return False, 'error'
    
    @staticmethod
    def _get_recent_prompt(user_id):
        """Check for recent upgrade prompts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour cooldown minimum
        
        return UpgradePrompt.query.filter(
            UpgradePrompt.user_id == user_id,
            UpgradePrompt.timestamp >= cutoff_time,
            UpgradePrompt.action == 'shown'
        ).first()
    
    @staticmethod
    def _check_trigger_condition(user_id, session_id, trigger_type, config, context):
        """Check specific trigger condition"""
        if trigger_type == 'high_ad_exposure':
            return UpgradePromptService._check_ad_exposure(user_id, session_id, config)
        elif trigger_type == 'high_engagement':
            return UpgradePromptService._check_engagement(user_id, session_id, config)
        elif trigger_type == 'adblock_detected':
            return UpgradePromptService._check_adblock(session_id, config)
        elif trigger_type == 'repeated_usage':
            return UpgradePromptService._check_repeated_usage(user_id, config)
        
        return False, 'unknown_trigger'
    
    @staticmethod
    def _check_ad_exposure(user_id, session_id, config):
        """Check if user has seen too many ads"""
        # Session ad count
        session_ads = AdTrackingService.get_session_ad_count(session_id, user_id)
        if session_ads >= config['min_ads_per_session']:
            return True, f'session_ads_{session_ads}'
        
        # Hourly ad count
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        hourly_ads = AdInteraction.query.filter(
            AdInteraction.user_id == user_id,
            AdInteraction.action == 'impression',
            AdInteraction.timestamp >= hour_ago
        ).count()
        
        if hourly_ads >= config['min_ads_per_hour']:
            return True, f'hourly_ads_{hourly_ads}'
        
        return False, 'ad_exposure_below_threshold'
    
    @staticmethod
    def _check_engagement(user_id, session_id, config):
        """Check if user shows high engagement"""
        # This would integrate with existing analytics
        # For now, simplified version based on ad interactions
        recent_interactions = AdTrackingService.get_recent_ad_interactions(user_id, 60)
        
        if len(recent_interactions) >= config['min_activities']:
            return True, f'high_activity_{len(recent_interactions)}'
        
        return False, 'engagement_below_threshold'
    
    @staticmethod
    def _check_adblock(session_id, config):
        """Check if ad blocker was detected"""
        if config.get('immediate_trigger') and AdTrackingService.has_ad_blocker(session_id):
            return True, 'adblock_detected'
        
        return False, 'no_adblock_detected'
    
    @staticmethod
    def _check_repeated_usage(user_id, config):
        """Check for repeated usage pattern"""
        days_ago = datetime.utcnow() - timedelta(days=config['timeframe_days'])
        
        # Count unique sessions in timeframe
        unique_sessions = db.session.query(
            db.func.count(db.func.distinct(AdInteraction.session_id))
        ).filter(
            AdInteraction.user_id == user_id,
            AdInteraction.timestamp >= days_ago
        ).scalar()
        
        if unique_sessions >= config['min_sessions']:
            return True, f'repeated_usage_{unique_sessions}_sessions'
        
        return False, 'usage_below_threshold'
    
    @staticmethod
    def track_prompt(user_id, session_id, trigger_reason, prompt_type, action, **kwargs):
        """Track upgrade prompt interaction"""
        try:
            prompt = UpgradePrompt(
                user_id=user_id,
                session_id=session_id,
                trigger_reason=trigger_reason,
                prompt_type=prompt_type,
                action=action,
                ad_count_session=kwargs.get('ad_count_session', 0),
                engagement_score=kwargs.get('engagement_score'),
                time_on_site_minutes=kwargs.get('time_on_site_minutes'),
                activities_completed=kwargs.get('activities_completed', 0),
                personalization_data=kwargs.get('personalization_data'),
                conversion_value=kwargs.get('conversion_value')
            )
            
            db.session.add(prompt)
            db.session.commit()
            
            current_app.logger.info(
                f"Upgrade prompt tracked: {action} for user {user_id} - {trigger_reason}"
            )
            return prompt
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error tracking upgrade prompt: {str(e)}")
            raise
    
    @staticmethod
    def get_personalized_prompt(user_id, trigger_reason):
        """Get personalized prompt content based on trigger reason"""
        prompt_messages = {
            'high_ad_exposure': {
                'title': 'Liker du Sertifikatet? 🚗',
                'message': 'Vi ser at du bruker plattformen mye! Oppgrader til Premium for en reklamefri opplevelse.',
                'cta': 'Fjern annonser - 149 NOK/måned',
                'highlight': 'Ingen annonser, ubegrenset tilgang!'
            },
            'high_engagement': {
                'title': 'Du lærer raskt! 🚀',
                'message': 'Imponerende fremgang! Få tilgang til alle funksjoner og fjern annonser med Premium.',
                'cta': 'Lås opp alt - 149 NOK/måned',
                'highlight': 'AI-tilpasset læring + ingen annonser'
            },
            'adblock_detected': {
                'title': 'Vi merker du bruker ad-blocker 🛡️',
                'message': 'Støtt gratis utdanning ved å oppgradere til Premium. Ingen annonser, bare læring!',
                'cta': 'Støtt plattformen - 149 NOK/måned',
                'highlight': 'Støtt gratis utdanning for alle'
            },
            'repeated_usage': {
                'title': 'Velkommen tilbake! 👋',
                'message': 'Du er en troffast bruker! Få den beste opplevelsen med Premium.',
                'cta': 'Oppgrader nå - 149 NOK/måned',
                'highlight': 'Trofaste brukere fortjener det beste'
            }
        }
        
        return prompt_messages.get(trigger_reason, prompt_messages['high_ad_exposure'])
    
    @staticmethod
    def get_conversion_stats(user_id=None, days=30):
        """Get conversion statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = UpgradePrompt.query.filter(UpgradePrompt.timestamp >= cutoff_date)
        
        if user_id:
            query = query.filter(UpgradePrompt.user_id == user_id)
        
        stats = query.with_entities(
            db.func.count(UpgradePrompt.id).label('total_prompts'),
            db.func.sum(db.case([(UpgradePrompt.action == 'shown', 1)], else_=0)).label('prompts_shown'),
            db.func.sum(db.case([(UpgradePrompt.action == 'clicked', 1)], else_=0)).label('prompts_clicked'),
            db.func.sum(db.case([(UpgradePrompt.action == 'converted', 1)], else_=0)).label('conversions'),
            db.func.sum(UpgradePrompt.conversion_value).label('total_revenue')
        ).first()
        
        prompts_shown = stats.prompts_shown or 0
        conversions = stats.conversions or 0
        
        return {
            'total_prompts': stats.total_prompts or 0,
            'prompts_shown': prompts_shown,
            'prompts_clicked': stats.prompts_clicked or 0,
            'conversions': conversions,
            'total_revenue': float(stats.total_revenue or 0),
            'conversion_rate': (conversions / prompts_shown * 100) if prompts_shown > 0 else 0,
            'average_conversion_value': float(stats.total_revenue or 0) / conversions if conversions > 0 else 0
        }
