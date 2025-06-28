"""
Advertising Analytics Service for Sertifikatet
Revenue analytics, reporting, and performance tracking
"""

from datetime import datetime, timedelta, date
from flask import current_app
from sqlalchemy import func, and_, or_
from app import db
from app.ad_models import (
    AdInteraction, UpgradePrompt, AdRevenueAnalytics, 
    AdPlacementPerformance
)
from .services import AdTrackingService, UpgradePromptService
import random


class AdAnalyticsService:
    """Service for ad revenue analytics and reporting"""
    
    @staticmethod
    def update_daily_analytics(target_date=None):
        """Update daily analytics summary"""
        if target_date is None:
            target_date = datetime.utcnow().date()
        
        # Get or create daily summary
        summary = AdRevenueAnalytics.query.filter_by(date=target_date).first()
        if not summary:
            summary = AdRevenueAnalytics(date=target_date)
            db.session.add(summary)
        
        # Calculate date range for the day
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        # Ad interaction metrics
        ad_metrics = db.session.query(
            func.count(AdInteraction.id).label('total_interactions'),
            func.sum(db.case([(AdInteraction.action == 'impression', 1)], else_=0)).label('impressions'),
            func.sum(db.case([(AdInteraction.action == 'click', 1)], else_=0)).label('clicks'),
            func.sum(db.case([(AdInteraction.action == 'block_detected', 1)], else_=0)).label('blocks'),
            func.count(func.distinct(AdInteraction.user_id)).label('unique_users')
        ).filter(
            AdInteraction.timestamp >= start_datetime,
            AdInteraction.timestamp < end_datetime
        ).first()
        
        # Upgrade prompt metrics
        upgrade_metrics = db.session.query(
            func.sum(db.case([(UpgradePrompt.action == 'shown', 1)], else_=0)).label('prompts_shown'),
            func.sum(db.case([(UpgradePrompt.action == 'converted', 1)], else_=0)).label('conversions'),
            func.sum(UpgradePrompt.conversion_value).label('upgrade_revenue')
        ).filter(
            UpgradePrompt.timestamp >= start_datetime,
            UpgradePrompt.timestamp < end_datetime
        ).first()
        
        # Update summary
        summary.total_impressions = ad_metrics.impressions or 0
        summary.total_clicks = ad_metrics.clicks or 0
        summary.unique_users_served = ad_metrics.unique_users or 0
        summary.ad_block_detections = ad_metrics.blocks or 0
        summary.upgrade_prompts_shown = upgrade_metrics.prompts_shown or 0
        summary.upgrade_conversions = upgrade_metrics.conversions or 0
        summary.upgrade_revenue_nok = upgrade_metrics.upgrade_revenue or 0
        
        # Calculate ad revenue (estimated)
        if summary.total_impressions > 0:
            # Estimate based on Norwegian educational content CPM
            estimated_cpm = 20.0  # NOK
            summary.total_revenue_nok = (summary.total_impressions / 1000) * estimated_cpm
            summary.avg_cpm = estimated_cpm
            
            # Calculate CTR
            summary.avg_ctr = (summary.total_clicks / summary.total_impressions)
        
        # Combined revenue
        summary.combined_revenue_nok = summary.total_revenue_nok + summary.upgrade_revenue_nok
        
        # Conversion rate
        if summary.upgrade_prompts_shown > 0:
            summary.premium_conversion_rate = (summary.upgrade_conversions / summary.upgrade_prompts_shown)
        
        # Revenue per user
        if summary.unique_users_served > 0:
            summary.revenue_per_free_user = (summary.combined_revenue_nok / summary.unique_users_served)
        
        # Count of free users (approximate)
        summary.free_user_count = summary.unique_users_served  # Simplified
        
        db.session.commit()
        current_app.logger.info(f"Daily analytics updated for {target_date}")
        
        return summary
    
    @staticmethod
    def get_revenue_summary(start_date=None, end_date=None):
        """Get comprehensive revenue analytics for date range"""
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Get daily summaries
        daily_summaries = AdRevenueAnalytics.query.filter(
            AdRevenueAnalytics.date >= start_date,
            AdRevenueAnalytics.date <= end_date
        ).order_by(AdRevenueAnalytics.date).all()
        
        if not daily_summaries:
            return {
                'message': 'No data available for the specified date range',
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_count': 0
                }
            }
        
        # Calculate totals
        total_stats = {
            'total_impressions': sum(s.total_impressions for s in daily_summaries),
            'total_clicks': sum(s.total_clicks for s in daily_summaries),
            'total_ad_revenue': sum(s.total_revenue_nok for s in daily_summaries),
            'total_upgrade_revenue': sum(s.upgrade_revenue_nok for s in daily_summaries),
            'total_combined_revenue': sum(s.combined_revenue_nok for s in daily_summaries),
            'total_upgrade_prompts': sum(s.upgrade_prompts_shown for s in daily_summaries),
            'total_conversions': sum(s.upgrade_conversions for s in daily_summaries),
            'total_ad_blocks': sum(s.ad_block_detections for s in daily_summaries),
            'unique_users_served': max((s.unique_users_served for s in daily_summaries), default=0)
        }
        
        # Calculate averages
        days_count = len(daily_summaries) or 1
        avg_stats = {
            'avg_daily_impressions': total_stats['total_impressions'] / days_count,
            'avg_daily_revenue': total_stats['total_combined_revenue'] / days_count,
            'avg_ctr': (total_stats['total_clicks'] / total_stats['total_impressions'] * 100) if total_stats['total_impressions'] > 0 else 0,
            'avg_conversion_rate': (total_stats['total_conversions'] / total_stats['total_upgrade_prompts'] * 100) if total_stats['total_upgrade_prompts'] > 0 else 0,
            'avg_revenue_per_user': total_stats['total_combined_revenue'] / total_stats['unique_users_served'] if total_stats['unique_users_served'] > 0 else 0
        }
        
        # Revenue projections
        if days_count >= 7:  # Need at least a week of data
            daily_avg = total_stats['total_combined_revenue'] / days_count
            projections = {
                'monthly_projection': daily_avg * 30,
                'yearly_projection': daily_avg * 365,
                'confidence': 'medium' if days_count >= 14 else 'low'
            }
        else:
            projections = {
                'monthly_projection': 0,
                'yearly_projection': 0,
                'confidence': 'insufficient_data'
            }
        
        return {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days_count': days_count
            },
            'totals': total_stats,
            'averages': avg_stats,
            'projections': projections,
            'daily_data': [s.to_dict() for s in daily_summaries],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_placement_performance(days=30, placement_id=None):
        """Get ad placement performance analytics"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = AdPlacementPerformance.query.filter(
            AdPlacementPerformance.date >= start_date,
            AdPlacementPerformance.date <= end_date
        )
        
        if placement_id:
            query = query.filter(AdPlacementPerformance.placement_id == placement_id)
        
        placements = query.all()
        
        # Group by placement_id
        placement_stats = {}
        for p in placements:
            if p.placement_id not in placement_stats:
                placement_stats[p.placement_id] = {
                    'placement_id': p.placement_id,
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_revenue': 0,
                    'total_conversions': 0,
                    'avg_ctr': 0,
                    'avg_cpm': 0,
                    'daily_data': []
                }
            
            stats = placement_stats[p.placement_id]
            stats['total_impressions'] += p.impressions
            stats['total_clicks'] += p.clicks
            stats['total_revenue'] += float(p.revenue_nok)
            stats['total_conversions'] += p.conversion_attribution
            stats['daily_data'].append(p.to_dict())
        
        # Calculate averages
        for placement_id, stats in placement_stats.items():
            if stats['total_impressions'] > 0:
                stats['avg_ctr'] = (stats['total_clicks'] / stats['total_impressions']) * 100
                stats['avg_cpm'] = (stats['total_revenue'] / stats['total_impressions']) * 1000
        
        return {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days_count': days
            },
            'placements': list(placement_stats.values()),
            'total_placements': len(placement_stats),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_user_statistics(user_id, days=30):
        """Get detailed statistics for a specific user"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Ad interactions
        ad_stats = db.session.query(
            func.count(AdInteraction.id).label('total_interactions'),
            func.sum(db.case([(AdInteraction.action == 'impression', 1)], else_=0)).label('impressions'),
            func.sum(db.case([(AdInteraction.action == 'click', 1)], else_=0)).label('clicks'),
            func.sum(db.case([(AdInteraction.action == 'dismiss', 1)], else_=0)).label('dismissals'),
            func.sum(db.case([(AdInteraction.action == 'block_detected', 1)], else_=0)).label('ad_blocks'),
            func.count(func.distinct(AdInteraction.session_id)).label('unique_sessions')
        ).filter(
            AdInteraction.user_id == user_id,
            AdInteraction.timestamp >= start_date
        ).first()
        
        # Upgrade prompts
        upgrade_stats = db.session.query(
            func.count(UpgradePrompt.id).label('total_prompts'),
            func.sum(db.case([(UpgradePrompt.action == 'shown', 1)], else_=0)).label('prompts_shown'),
            func.sum(db.case([(UpgradePrompt.action == 'clicked', 1)], else_=0)).label('prompts_clicked'),
            func.sum(db.case([(UpgradePrompt.action == 'dismissed', 1)], else_=0)).label('prompts_dismissed'),
            func.sum(db.case([(UpgradePrompt.action == 'converted', 1)], else_=0)).label('conversions')
        ).filter(
            UpgradePrompt.user_id == user_id,
            UpgradePrompt.timestamp >= start_date
        ).first()
        
        # Calculate derived metrics
        impressions = ad_stats.impressions or 0
        clicks = ad_stats.clicks or 0
        prompts_shown = upgrade_stats.prompts_shown or 0
        conversions = upgrade_stats.conversions or 0
        
        return {
            'user_id': user_id,
            'period_days': days,
            'ad_interactions': {
                'total_interactions': ad_stats.total_interactions or 0,
                'impressions': impressions,
                'clicks': clicks,
                'dismissals': ad_stats.dismissals or 0,
                'ad_blocks_detected': ad_stats.ad_blocks or 0,
                'unique_sessions': ad_stats.unique_sessions or 0,
                'ctr_percentage': (clicks / impressions * 100) if impressions > 0 else 0
            },
            'upgrade_prompts': {
                'total_prompts': upgrade_stats.total_prompts or 0,
                'prompts_shown': prompts_shown,
                'prompts_clicked': upgrade_stats.prompts_clicked or 0,
                'prompts_dismissed': upgrade_stats.prompts_dismissed or 0,
                'conversions': conversions,
                'conversion_rate': (conversions / prompts_shown * 100) if prompts_shown > 0 else 0
            },
            'engagement_metrics': {
                'avg_interactions_per_session': (ad_stats.total_interactions or 0) / (ad_stats.unique_sessions or 1),
                'prompt_to_ad_ratio': (prompts_shown / impressions * 100) if impressions > 0 else 0
            },
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def generate_sample_data(days=7):
        """Generate sample ad data for testing (development only)"""
        if not current_app.debug:
            raise Exception("Sample data generation only available in debug mode")
        
        sample_sessions = []
        placements = ['quiz_sidebar', 'video_preroll', 'homepage_banner', 'quiz_interstitial']
        
        for day in range(days):
            target_date = datetime.utcnow().date() - timedelta(days=day)
            
            # Generate 20-50 interactions per day
            daily_interactions = random.randint(20, 50)
            
            for i in range(daily_interactions):
                session_id = f"sample_session_{target_date}_{i}"
                placement = random.choice(placements)
                
                # Create impression
                AdTrackingService.track_interaction(
                    user_id=1,  # Assuming user 1 exists
                    session_id=session_id,
                    ad_type='banner',
                    ad_placement=placement,
                    action='impression',
                    page_section=placement.split('_')[0]
                )
                
                # Sometimes add clicks
                if random.random() < 0.025:  # 2.5% CTR
                    AdTrackingService.track_interaction(
                        user_id=1,
                        session_id=session_id,
                        ad_type='banner',
                        ad_placement=placement,
                        action='click',
                        page_section=placement.split('_')[0]
                    )
            
            # Generate some upgrade prompts
            if random.random() < 0.3:  # 30% of days have upgrade prompts
                UpgradePromptService.track_prompt(
                    user_id=1,
                    session_id=f"sample_session_{target_date}_upgrade",
                    trigger_reason='high_ad_exposure',
                    prompt_type='smart_popup',
                    action='shown',
                    ad_count_session=random.randint(3, 8)
                )
            
            # Update daily analytics
            AdAnalyticsService.update_daily_analytics(target_date)
            
            sample_sessions.append({
                'date': target_date.isoformat(),
                'interactions': daily_interactions
            })
        
        return {
            'message': f'Generated {days} days of sample data',
            'sessions': sample_sessions
        }
