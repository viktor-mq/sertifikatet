"""
Payment and Subscription Services
Phase 11: Payment & Subscriptions
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import json
import logging
from flask import current_app
from sqlalchemy import and_, or_
from ..models import User
from ..payment_models import (
    SubscriptionPlan, UserSubscription, Payment, UsageLimit, 
    DiscountCode, DiscountUsage, RefundRequest, BillingAddress
)
from .. import db

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing user subscriptions"""
    
    # Plan configurations
    PLAN_CONFIGS = {
        'free': {
            'max_daily_quizzes': 10,
            'max_weekly_exams': 2,
            'has_ads': True,
            'has_detailed_stats': False,
            'has_ai_adaptive': False,
            'has_offline_mode': False,
            'has_personal_tutor': False,
            'has_video_access': False,
            'priority_support': False
        },
        'premium': {
            'max_daily_quizzes': None,  # Unlimited
            'max_weekly_exams': None,   # Unlimited
            'has_ads': False,
            'has_detailed_stats': True,
            'has_ai_adaptive': True,
            'has_offline_mode': False,
            'has_personal_tutor': False,
            'has_video_access': True,
            'priority_support': True
        },
        'pro': {
            'max_daily_quizzes': None,  # Unlimited
            'max_weekly_exams': None,   # Unlimited
            'has_ads': False,
            'has_detailed_stats': True,
            'has_ai_adaptive': True,
            'has_offline_mode': True,
            'has_personal_tutor': True,
            'has_video_access': True,
            'priority_support': True
        }
    }
    
    @staticmethod
    def get_user_subscription(user_id: int) -> Optional[UserSubscription]:
        """Get user's current active subscription"""
        return UserSubscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).filter(
            or_(
                UserSubscription.expires_at.is_(None),
                UserSubscription.expires_at > datetime.utcnow()
            )
        ).first()
    
    @staticmethod
    def get_user_plan(user_id: int) -> str:
        """Get user's current plan name using FK relationship"""
        user = User.query.get(user_id)
        if user and user.current_plan:
            return user.current_plan.name
        return 'free'
    
    @staticmethod
    def get_plan_features(plan_name: str) -> Dict:
        """Get features for a specific plan"""
        return SubscriptionService.PLAN_CONFIGS.get(plan_name, SubscriptionService.PLAN_CONFIGS['free'])
    
    @staticmethod
    def user_has_feature(user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        plan_name = SubscriptionService.get_user_plan(user_id)
        features = SubscriptionService.get_plan_features(plan_name)
        return features.get(feature, False)
    
    @staticmethod
    def can_user_take_quiz(user_id: int, quiz_type: str = 'practice') -> Tuple[bool, str]:
        """Check if user can take a quiz based on their plan and usage"""
        plan_name = SubscriptionService.get_user_plan(user_id)
        
        # Premium/Pro users have unlimited access
        if plan_name in ['premium', 'pro']:
            return True, ""
        
        # Free users have limits
        usage_service = UsageLimitService()
        
        if quiz_type == 'exam':
            can_take, count, limit = usage_service.can_take_weekly_exam(user_id)
            if not can_take:
                return False, f"Du har nådd ukesgrensen på {limit} prøveeksamener. Oppgrader til Premium for ubegrenset tilgang."
        else:
            can_take, count, limit = usage_service.can_take_daily_quiz(user_id)
            if not can_take:
                return False, f"Du har nådd dagens grense på {limit} quiz. Oppgrader til Premium for ubegrenset tilgang."
        
        return True, ""
    
    @staticmethod
    def can_user_watch_video(user_id: int) -> Tuple[bool, str]:
        """Check if user can watch videos"""
        if SubscriptionService.user_has_feature(user_id, 'has_video_access'):
            return True, ""
        return False, "Videoer er kun tilgjengelig for Premium og Pro brukere. Oppgrader for full tilgang."
    
    @staticmethod
    def should_show_ads(user_id: int) -> bool:
        """Check if ads should be shown to user"""
        return SubscriptionService.user_has_feature(user_id, 'has_ads')
    
    @staticmethod
    def get_subscription_stats(user_id: int) -> Dict:
        """Get comprehensive subscription statistics for user"""
        subscription = SubscriptionService.get_user_subscription(user_id)
        plan_name = SubscriptionService.get_user_plan(user_id)
        features = SubscriptionService.get_plan_features(plan_name)
        
        # Get subscription details
        subscription_info = {
            'plan_name': plan_name,
            'plan_display_name': plan_name.title(),
            'is_premium': plan_name != 'free',
            'features': features
        }
        
        if subscription:
            subscription_info.update({
                'status': subscription.status,
                'started_at': subscription.started_at.isoformat() if subscription.started_at else None,
                'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
                'auto_renew': subscription.auto_renew,
                'is_trial': subscription.is_trial,
                'trial_ends_at': subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                'cancelled_at': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
                'cancelled_reason': subscription.cancelled_reason,
                'payment_method_id': subscription.payment_method_id,
                'stripe_subscription_id': subscription.stripe_subscription_id
            })
        else:
            # Free plan defaults
            subscription_info.update({
                'status': 'active',
                'started_at': None,
                'expires_at': None,
                'next_billing_date': None,
                'auto_renew': False,
                'is_trial': False,
                'trial_ends_at': None,
                'cancelled_at': None,
                'cancelled_reason': None,
                'payment_method_id': None,
                'stripe_subscription_id': None
            })
        
        return subscription_info
    
    @staticmethod
    def cancel_subscription(user_id: int, reason: str = 'User requested cancellation') -> bool:
        """Cancel user's active subscription"""
        try:
            subscription = SubscriptionService.get_user_subscription(user_id)
            if not subscription:
                return False  # No active subscription to cancel
            
            subscription.status = 'cancelled'
            subscription.cancelled_at = datetime.utcnow()
            subscription.cancelled_reason = reason
            subscription.auto_renew = False
            
            # Update user's current plan to free
            user = User.query.get(user_id)
            if user:
                free_plan = SubscriptionService.get_plan_by_name('free')
                if free_plan:
                    user.current_plan_id = free_plan.id
                    user.subscription_status = 'cancelled'
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling subscription for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_plan_by_name(plan_name: str) -> Optional['SubscriptionPlan']:
        """Get subscription plan by name"""
        from ..payment_models import SubscriptionPlan
        return SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    
    @staticmethod
    def update_user_plan(user_id: int, plan_name: str, status: str = 'active') -> bool:
        """Update user's current plan via FK relationship"""
        try:
            user = User.query.get(user_id)
            plan = SubscriptionService.get_plan_by_name(plan_name)
            
            if user and plan:
                user.current_plan_id = plan.id
                user.subscription_status = status
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user plan: {str(e)}")
            return False


class UsageLimitService:
    """Service for tracking and enforcing usage limits"""
    
    @staticmethod
    def get_or_create_usage_limit(user_id: int) -> UsageLimit:
        """Get or create usage limit record for user"""
        today = datetime.utcnow().date()
        usage = UsageLimit.query.filter_by(user_id=user_id).first()
        
        if not usage:
            # Create new usage record
            usage = UsageLimit(
                user_id=user_id,
                daily_limit_date=today,
                weekly_limit_start=UsageLimitService._get_week_start(today)
            )
            db.session.add(usage)
            db.session.commit()
        else:
            # Reset counters if needed
            if usage.daily_limit_date != today:
                usage.daily_quizzes_taken = 0
                usage.daily_limit_date = today
                usage.last_daily_reset = datetime.utcnow()
            
            current_week_start = UsageLimitService._get_week_start(today)
            if usage.weekly_limit_start != current_week_start:
                usage.weekly_exams_taken = 0
                usage.weekly_limit_start = current_week_start
                usage.last_weekly_reset = datetime.utcnow()
            
            db.session.commit()
        
        return usage
    
    @staticmethod
    def _get_week_start(date) -> datetime.date:
        """Get the start of the week (Monday) for a given date"""
        days_since_monday = date.weekday()
        return date - timedelta(days=days_since_monday)
    
    @staticmethod
    def can_take_daily_quiz(user_id: int) -> Tuple[bool, int, int]:
        """Check if user can take another daily quiz"""
        usage = UsageLimitService.get_or_create_usage_limit(user_id)
        max_daily = SubscriptionService.PLAN_CONFIGS['free']['max_daily_quizzes']
        
        can_take = usage.daily_quizzes_taken < max_daily
        return can_take, usage.daily_quizzes_taken, max_daily
    
    @staticmethod
    def can_take_weekly_exam(user_id: int) -> Tuple[bool, int, int]:
        """Check if user can take another weekly exam"""
        usage = UsageLimitService.get_or_create_usage_limit(user_id)
        max_weekly = SubscriptionService.PLAN_CONFIGS['free']['max_weekly_exams']
        
        can_take = usage.weekly_exams_taken < max_weekly
        return can_take, usage.weekly_exams_taken, max_weekly
    
    @staticmethod
    def record_quiz_taken(user_id: int, quiz_type: str = 'practice'):
        """Record that user has taken a quiz"""
        usage = UsageLimitService.get_or_create_usage_limit(user_id)
        
        if quiz_type == 'exam':
            usage.weekly_exams_taken += 1
        else:
            usage.daily_quizzes_taken += 1
        
        usage.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_usage_stats(user_id: int) -> Dict:
        """Get usage statistics for user"""
        usage = UsageLimitService.get_or_create_usage_limit(user_id)
        max_daily = SubscriptionService.PLAN_CONFIGS['free']['max_daily_quizzes']
        max_weekly = SubscriptionService.PLAN_CONFIGS['free']['max_weekly_exams']
        
        return {
            'daily_quizzes': {
                'taken': usage.daily_quizzes_taken,
                'limit': max_daily,
                'remaining': max_daily - usage.daily_quizzes_taken,
                'resets_at': (usage.daily_limit_date + timedelta(days=1)).isoformat()
            },
            'weekly_exams': {
                'taken': usage.weekly_exams_taken,
                'limit': max_weekly,
                'remaining': max_weekly - usage.weekly_exams_taken,
                'resets_at': (usage.weekly_limit_start + timedelta(days=7)).isoformat()
            }
        }


class PaymentService:
    """Service for handling payments and billing"""
    
    @staticmethod
    def create_payment_intent(user_id: int, plan_name: str, discount_code: str = None) -> Dict:
        """Create a payment intent for subscription"""
        plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
        if not plan:
            raise ValueError(f"Plan '{plan_name}' not found")
        
        amount = plan.price_nok
        
        # Create payment record
        payment = Payment(
            user_id=user_id,
            plan_id=plan.id,
            amount_nok=amount,
            status='pending',
            description=f"{plan.display_name} subscription",
            created_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        # Generate invoice number
        payment.invoice_number = f"SERT-{datetime.utcnow().year}-{payment.id:06d}"
        
        db.session.commit()
        
        return {
            'payment_id': payment.id,
            'amount': float(amount),
            'currency': 'NOK',
            'description': payment.description,
            'invoice_number': payment.invoice_number
        }
    
    @staticmethod
    def complete_payment(payment_id: int, external_payment_id: str, payment_method: str) -> bool:
        """Complete a payment and activate subscription"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return False
            
            # Update payment status
            payment.status = 'completed'
            payment.external_payment_id = external_payment_id
            payment.payment_method = payment_method
            payment.completed_at = datetime.utcnow()
            
            # Update user's current plan via FK relationship
            plan = payment.plan
            if plan:
                SubscriptionService.update_user_plan(payment.user_id, plan.name, 'active')
            
            # Create or update subscription record for tracking
            existing_subscription = SubscriptionService.get_user_subscription(payment.user_id)
            
            if existing_subscription:
                # Update existing subscription
                existing_subscription.plan_id = payment.plan_id
                existing_subscription.status = 'active'
                existing_subscription.auto_renew = True
                existing_subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
                existing_subscription.updated_at = datetime.utcnow()
            else:
                # Create new subscription
                subscription = UserSubscription(
                    user_id=payment.user_id,
                    plan_id=payment.plan_id,
                    status='active',
                    started_at=datetime.utcnow(),
                    next_billing_date=datetime.utcnow() + timedelta(days=30),
                    auto_renew=True,
                    is_trial=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(subscription)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error completing payment {payment_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_user_payment_history(user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's payment history"""
        payments = Payment.query.filter_by(user_id=user_id)\
                                .order_by(Payment.created_at.desc())\
                                .limit(limit)\
                                .all()
        
        payment_history = []
        for payment in payments:
            payment_data = {
                'id': payment.id,
                'amount': float(payment.amount_nok),
                'currency': 'NOK',
                'status': payment.status,
                'description': payment.description,
                'invoice_number': payment.invoice_number,
                'payment_method': payment.payment_method,
                'created_at': payment.created_at.isoformat() if payment.created_at else None,
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'plan_name': payment.plan.name if payment.plan else None,
                'plan_display_name': payment.plan.display_name if payment.plan else None
            }
            payment_history.append(payment_data)
        
        return payment_history
