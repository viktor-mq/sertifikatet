"""
Enhanced upgrade service for Premium → Pro and other upgrades
Handles plan upgrades with proper billing and expiration logic
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
import logging
from ..payment_models import SubscriptionPlan, UserSubscription, Payment
from ..models import User
from .. import db

logger = logging.getLogger(__name__)


class UpgradeService:
    """Service for handling subscription plan upgrades"""
    
    @staticmethod
    def calculate_upgrade_cost(user_id: int, target_plan_name: str) -> Dict:
        """Calculate prorated cost for upgrading to a higher plan"""
        from .payment_service import SubscriptionService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        current_plan = SubscriptionService.get_user_plan(user_id)
        current_subscription = SubscriptionService.get_user_subscription(user_id)
        target_plan = SubscriptionPlan.query.filter_by(name=target_plan_name, is_active=True).first()
        
        if not target_plan:
            raise ValueError(f"Target plan '{target_plan_name}' not found")
        
        current_plan_obj = SubscriptionService.get_plan_by_name(current_plan)
        
        # Check if this is actually an upgrade
        if not current_plan_obj or target_plan.price_nok <= current_plan_obj.price_nok:
            if current_plan == target_plan_name:
                raise ValueError("User already has this plan")
            else:
                raise ValueError("This is not an upgrade (target plan is not more expensive)")
        
        upgrade_info = {
            'current_plan': current_plan,
            'current_plan_display': current_plan_obj.display_name,
            'current_price': float(current_plan_obj.price_nok),
            'target_plan': target_plan_name,
            'target_plan_display': target_plan.display_name,
            'target_price': float(target_plan.price_nok),
            'is_upgrade': True
        }
        
        if current_subscription and current_subscription.expires_at:
            # Calculate prorated refund for remaining time
            now = datetime.utcnow()
            expires_at = current_subscription.expires_at
            
            if expires_at > now:
                # Calculate remaining days
                remaining_days = (expires_at - now).days
                total_days = 30  # Assuming monthly billing
                
                # Convert to Decimal for precise calculations
                remaining_days_decimal = Decimal(str(remaining_days))
                total_days_decimal = Decimal(str(total_days))
                
                # Calculate prorated amounts using Decimal arithmetic
                remaining_value = (remaining_days_decimal / total_days_decimal) * current_plan_obj.price_nok
                upgrade_cost = target_plan.price_nok - remaining_value
                
                # Ensure minimum charge (e.g., at least 10 NOK)
                upgrade_cost = max(upgrade_cost, Decimal('10.00'))
                
                upgrade_info.update({
                    'remaining_days': remaining_days,
                    'remaining_value': float(remaining_value),
                    'upgrade_cost': float(upgrade_cost),
                    'proration_applied': True,
                    'expires_at': expires_at,
                    'new_expires_at': now + timedelta(days=30)  # Full month from upgrade
                })
            else:
                # Subscription already expired or expires today
                upgrade_info.update({
                    'remaining_days': 0,
                    'remaining_value': 0.0,
                    'upgrade_cost': float(target_plan.price_nok),
                    'proration_applied': False,
                    'new_expires_at': now + timedelta(days=30)
                })
        else:
            # No active subscription or Free plan
            upgrade_info.update({
                'remaining_days': 0,
                'remaining_value': 0.0,
                'upgrade_cost': float(target_plan.price_nok),
                'proration_applied': False,
                'new_expires_at': datetime.utcnow() + timedelta(days=30)
            })
        
        return upgrade_info
    
    @staticmethod
    def process_upgrade(user_id: int, target_plan_name: str, payment_id: int) -> bool:
        """Process plan upgrade after successful payment"""
        try:
            from .payment_service import SubscriptionService
            
            payment = Payment.query.get(payment_id)
            if not payment or payment.user_id != user_id:
                logger.error(f"Payment {payment_id} not found or doesn't belong to user {user_id}")
                return False
            
            # Get current subscription
            current_subscription = SubscriptionService.get_user_subscription(user_id)
            target_plan = SubscriptionService.get_plan_by_name(target_plan_name)
            
            if not target_plan:
                logger.error(f"Target plan {target_plan_name} not found")
                return False
            
            # Update payment record
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            # Update user's plan immediately
            SubscriptionService.update_user_plan(user_id, target_plan_name, 'active')
            
            if current_subscription:
                # Update existing subscription
                current_subscription.plan_id = target_plan.id
                current_subscription.status = 'active'
                current_subscription.auto_renew = True
                current_subscription.started_at = datetime.utcnow()
                current_subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # Fresh 30 days
                current_subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
                current_subscription.updated_at = datetime.utcnow()
                
                # Clear any cancellation info since this is a new upgrade
                current_subscription.cancelled_at = None
                current_subscription.cancelled_reason = None
                
                logger.info(f"Upgraded user {user_id} to {target_plan_name} - subscription updated")
            else:
                # Create new subscription
                new_subscription = UserSubscription(
                    user_id=user_id,
                    plan_id=target_plan.id,
                    status='active',
                    started_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30),
                    next_billing_date=datetime.utcnow() + timedelta(days=30),
                    auto_renew=True,
                    is_trial=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_subscription)
                logger.info(f"Upgraded user {user_id} to {target_plan_name} - new subscription created")
            
            # Link payment to subscription
            if current_subscription:
                payment.subscription_id = current_subscription.id
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing upgrade for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def can_upgrade_to(user_id: int, target_plan_name: str) -> Tuple[bool, str]:
        """Check if user can upgrade to target plan"""
        from .payment_service import SubscriptionService
        
        current_plan = SubscriptionService.get_user_plan(user_id)
        target_plan = SubscriptionService.get_plan_by_name(target_plan_name)
        current_plan_obj = SubscriptionService.get_plan_by_name(current_plan)
        
        if not target_plan:
            return False, f"Plan '{target_plan_name}' not found"
        
        if current_plan == target_plan_name:
            return False, "You already have this plan"
        
        # Check if it's actually an upgrade (more expensive)
        if current_plan_obj and target_plan.price_nok <= current_plan_obj.price_nok:
            return False, "This would be a downgrade, not an upgrade"
        
        # Admins can always upgrade (though they already have Pro access)
        user = User.query.get(user_id)
        if user and user.is_admin:
            return True, ""
        
        # Check plan hierarchy: free → premium → pro
        plan_hierarchy = {'free': 0, 'premium': 1, 'pro': 2}
        current_level = plan_hierarchy.get(current_plan, 0)
        target_level = plan_hierarchy.get(target_plan_name, 0)
        
        if target_level <= current_level:
            return False, "You can only upgrade to a higher plan"
        
        return True, ""
    
    @staticmethod
    def get_upgrade_options(user_id: int) -> List[Dict]:
        """Get available upgrade options for user"""
        from .payment_service import SubscriptionService
        
        current_plan = SubscriptionService.get_user_plan(user_id)
        all_plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_nok).all()
        current_plan_obj = SubscriptionService.get_plan_by_name(current_plan)
        
        upgrade_options = []
        
        for plan in all_plans:
            # Only show plans that are more expensive (upgrades)
            if current_plan_obj and plan.price_nok > current_plan_obj.price_nok:
                can_upgrade, message = UpgradeService.can_upgrade_to(user_id, plan.name)
                
                if can_upgrade:
                    try:
                        upgrade_info = UpgradeService.calculate_upgrade_cost(user_id, plan.name)
                        upgrade_options.append({
                            'plan': plan,
                            'upgrade_info': upgrade_info
                        })
                    except ValueError as e:
                        # Skip plans that can't be calculated
                        continue
        
        return upgrade_options
