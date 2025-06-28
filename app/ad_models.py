"""
Ad Revenue and Tracking Models for Sertifikatet
Handles ad interactions, upgrade prompts, and revenue analytics
"""

from app import db
from datetime import datetime
from sqlalchemy import Index
import json


class AdInteraction(db.Model):
    """Track all ad interactions for revenue and optimization"""
    __tablename__ = 'ad_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL for anonymous
    session_id = db.Column(db.String(100), nullable=False, index=True)
    ad_type = db.Column(db.String(50), nullable=False)  # 'banner', 'interstitial', 'video', 'native'
    ad_placement = db.Column(db.String(50), nullable=False)  # 'quiz_sidebar', 'video_preroll', etc.
    action = db.Column(db.String(50), nullable=False)  # 'impression', 'click', 'dismiss', 'block_detected'
    page_section = db.Column(db.String(50), nullable=False)  # 'quiz', 'video', 'general'
    ad_provider = db.Column(db.String(50), nullable=False, default='google_adsense')
    revenue_cpm = db.Column(db.Numeric(10, 4), nullable=True)  # Revenue per thousand impressions
    user_tier = db.Column(db.String(20), nullable=False, default='free')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # For fraud detection
    user_agent = db.Column(db.Text, nullable=True)
    referrer_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ad_interactions')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ad_interactions_user_date', 'user_id', 'timestamp'),
        Index('idx_ad_interactions_session', 'session_id', 'timestamp'),
        Index('idx_ad_interactions_placement_date', 'ad_placement', 'timestamp'),
        Index('idx_ad_interactions_action_date', 'action', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<AdInteraction {self.action} on {self.ad_placement} by user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ad_type': self.ad_type,
            'ad_placement': self.ad_placement,
            'action': self.action,
            'page_section': self.page_section,
            'ad_provider': self.ad_provider,
            'revenue_cpm': float(self.revenue_cpm) if self.revenue_cpm else None,
            'user_tier': self.user_tier,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class UpgradePrompt(db.Model):
    """Track upgrade prompts and their effectiveness"""
    __tablename__ = 'upgrade_prompts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    trigger_reason = db.Column(db.String(100), nullable=False)  # 'high_ad_exposure', 'high_engagement', etc.
    prompt_type = db.Column(db.String(50), nullable=False)  # 'smart_popup', 'banner', 'interstitial'
    action = db.Column(db.String(50), nullable=False)  # 'shown', 'clicked', 'dismissed', 'converted'
    ad_count_session = db.Column(db.Integer, nullable=False, default=0)
    engagement_score = db.Column(db.Float, nullable=True)  # 0.0-1.0
    time_on_site_minutes = db.Column(db.Integer, nullable=True)
    activities_completed = db.Column(db.Integer, nullable=False, default=0)
    personalization_data = db.Column(db.JSON, nullable=True)
    conversion_value = db.Column(db.Numeric(10, 2), nullable=True)  # 149.00 for premium
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='upgrade_prompts')
    
    # Indexes
    __table_args__ = (
        Index('idx_upgrade_prompts_user_date', 'user_id', 'timestamp'),
        Index('idx_upgrade_prompts_trigger', 'trigger_reason', 'action'),
        Index('idx_upgrade_prompts_conversion', 'action', 'conversion_value'),
    )
    
    def __repr__(self):
        return f'<UpgradePrompt {self.action} for user {self.user_id} - {self.trigger_reason}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'trigger_reason': self.trigger_reason,
            'prompt_type': self.prompt_type,
            'action': self.action,
            'ad_count_session': self.ad_count_session,
            'engagement_score': self.engagement_score,
            'time_on_site_minutes': self.time_on_site_minutes,
            'activities_completed': self.activities_completed,
            'personalization_data': self.personalization_data,
            'conversion_value': float(self.conversion_value) if self.conversion_value else None,
            'timestamp': self.timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class AdRevenueAnalytics(db.Model):
    """Daily aggregated ad revenue and performance analytics"""
    __tablename__ = 'ad_revenue_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    total_impressions = db.Column(db.Integer, nullable=False, default=0)
    total_clicks = db.Column(db.Integer, nullable=False, default=0)
    total_revenue_nok = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    avg_cpm = db.Column(db.Numeric(10, 4), nullable=True)
    avg_ctr = db.Column(db.Numeric(5, 4), nullable=True)  # Click-through rate
    unique_users_served = db.Column(db.Integer, nullable=False, default=0)
    upgrade_prompts_shown = db.Column(db.Integer, nullable=False, default=0)
    upgrade_conversions = db.Column(db.Integer, nullable=False, default=0)
    upgrade_revenue_nok = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    combined_revenue_nok = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    ad_block_detections = db.Column(db.Integer, nullable=False, default=0)
    free_user_count = db.Column(db.Integer, nullable=False, default=0)
    premium_conversion_rate = db.Column(db.Numeric(5, 4), nullable=True)
    revenue_per_free_user = db.Column(db.Numeric(10, 4), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdRevenueAnalytics {self.date} - {self.combined_revenue_nok} NOK>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_impressions': self.total_impressions,
            'total_clicks': self.total_clicks,
            'total_revenue_nok': float(self.total_revenue_nok),
            'avg_cpm': float(self.avg_cpm) if self.avg_cpm else None,
            'avg_ctr': float(self.avg_ctr) if self.avg_ctr else None,
            'unique_users_served': self.unique_users_served,
            'upgrade_prompts_shown': self.upgrade_prompts_shown,
            'upgrade_conversions': self.upgrade_conversions,
            'upgrade_revenue_nok': float(self.upgrade_revenue_nok),
            'combined_revenue_nok': float(self.combined_revenue_nok),
            'ad_block_detections': self.ad_block_detections,
            'free_user_count': self.free_user_count,
            'premium_conversion_rate': float(self.premium_conversion_rate) if self.premium_conversion_rate else None,
            'revenue_per_free_user': float(self.revenue_per_free_user) if self.revenue_per_free_user else None,
            'created_at': self.created_at.isoformat()
        }


class AdPlacementPerformance(db.Model):
    """Track performance of specific ad placements"""
    __tablename__ = 'ad_placement_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    placement_id = db.Column(db.String(50), nullable=False)  # 'quiz_sidebar', 'video_preroll', etc.
    date = db.Column(db.Date, nullable=False, index=True)
    impressions = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    revenue_nok = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    ctr = db.Column(db.Numeric(5, 4), nullable=True)  # Click-through rate
    cpm = db.Column(db.Numeric(10, 4), nullable=True)  # Cost per mille
    conversion_attribution = db.Column(db.Integer, nullable=False, default=0)  # Upgrades attributed
    user_satisfaction_score = db.Column(db.Numeric(3, 2), nullable=True)  # 1-5 rating
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_placement_performance_date', 'placement_id', 'date'),
        Index('idx_placement_performance_revenue', 'date', 'revenue_nok'),
    )
    
    def __repr__(self):
        return f'<AdPlacementPerformance {self.placement_id} {self.date} - {self.revenue_nok} NOK>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'placement_id': self.placement_id,
            'date': self.date.isoformat(),
            'impressions': self.impressions,
            'clicks': self.clicks,
            'revenue_nok': float(self.revenue_nok),
            'ctr': float(self.ctr) if self.ctr else None,
            'cpm': float(self.cpm) if self.cpm else None,
            'conversion_attribution': self.conversion_attribution,
            'user_satisfaction_score': float(self.user_satisfaction_score) if self.user_satisfaction_score else None,
            'created_at': self.created_at.isoformat()
        }
