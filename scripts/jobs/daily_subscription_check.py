#!/usr/bin/env python3
"""
Daily Subscription Check Job
Runs after midnight to check subscription statuses and expire subscriptions
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models import User
from app.payment_models import UserSubscription, SubscriptionPlan
from app.services.payment_service import SubscriptionService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sertifikatet/subscription_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_and_expire_subscriptions():
    """Check all subscriptions and expire those that should be expired"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Starting daily subscription check...")
            
            # Get current timestamp
            now = datetime.utcnow()
            
            # Find all subscriptions that should be expired (both active and cancelled)
            expired_subscriptions = UserSubscription.query.filter(
                or_(
                    UserSubscription.status == 'active',
                    UserSubscription.status == 'cancelled'
                ),
                UserSubscription.expires_at <= now,
                UserSubscription.expires_at.isnot(None)
            ).all()
            
            logger.info(f"Found {len(expired_subscriptions)} subscriptions to expire")
            
            # Get free plan for downgrading users
            free_plan = SubscriptionPlan.query.filter_by(name='free', is_active=True).first()
            if not free_plan:
                logger.error("❌ Free plan not found! Cannot downgrade users.")
                return False
            
            expired_count = 0
            for subscription in expired_subscriptions:
                try:
                    # Update subscription status
                    subscription.status = 'expired'
                    subscription.updated_at = now
                    
                    # Downgrade user to free plan
                    user = User.query.get(subscription.user_id)
                    if user:
                        user.current_plan_id = free_plan.id
                        user.subscription_status = 'expired'
                        
                        logger.info(f"✅ Expired subscription for user {user.email} (ID: {user.id}) - was {subscription.status}")
                        expired_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error expiring subscription {subscription.id}: {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            # Check for subscriptions expiring soon (within 3 days)
            warning_date = now + timedelta(days=3)
            warning_subscriptions = UserSubscription.query.filter(
                UserSubscription.status == 'active',
                UserSubscription.expires_at <= warning_date,
                UserSubscription.expires_at > now,
                UserSubscription.expires_at.isnot(None)
            ).all()
            
            logger.info(f"Found {len(warning_subscriptions)} subscriptions expiring within 3 days")
            
            # TODO: Send email notifications for expiring subscriptions
            # This would integrate with your email service
            
            logger.info(f"✅ Daily subscription check completed. Expired {expired_count} subscriptions.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in daily subscription check: {str(e)}")
            db.session.rollback()
            return False


def check_admin_users():
    """Ensure admin users always have Pro plan access"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔑 Checking admin user access...")
            
            # Get Pro plan
            pro_plan = SubscriptionPlan.query.filter_by(name='pro', is_active=True).first()
            if not pro_plan:
                logger.error("❌ Pro plan not found! Cannot upgrade admin users.")
                return False
            
            # Find all admin users
            admin_users = User.query.filter_by(is_admin=True).all()
            
            updated_count = 0
            for admin in admin_users:
                try:
                    # Ensure admin has Pro plan
                    if admin.current_plan_id != pro_plan.id:
                        admin.current_plan_id = pro_plan.id
                        admin.subscription_status = 'active'
                        
                        # Check if they have an active subscription record
                        active_subscription = UserSubscription.query.filter_by(
                            user_id=admin.id,
                            status='active'
                        ).first()
                        
                        if not active_subscription:
                            # Create a permanent Pro subscription for admin
                            admin_subscription = UserSubscription(
                                user_id=admin.id,
                                plan_id=pro_plan.id,
                                status='active',
                                started_at=datetime.utcnow(),
                                expires_at=None,  # Never expires for admins
                                auto_renew=False,
                                is_trial=False,
                                notes='Admin user - permanent Pro access',
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            db.session.add(admin_subscription)
                        
                        logger.info(f"✅ Ensured admin access for {admin.email} (ID: {admin.id})")
                        updated_count += 1
                
                except Exception as e:
                    logger.error(f"❌ Error updating admin user {admin.id}: {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"✅ Admin access check completed. Updated {updated_count} admin users.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in admin access check: {str(e)}")
            db.session.rollback()
            return False


def generate_daily_report():
    """Generate a daily subscription report"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("📊 Generating daily subscription report...")
            
            # Get subscription statistics
            total_users = User.query.count()
            free_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'free').count()
            premium_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'premium').count()
            pro_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'pro').count()
            admin_users = User.query.filter_by(is_admin=True).count()
            
            # Active subscriptions
            active_subscriptions = UserSubscription.query.filter_by(status='active').count()
            expired_subscriptions = UserSubscription.query.filter_by(status='expired').count()
            cancelled_subscriptions = UserSubscription.query.filter_by(status='cancelled').count()
            
            # Subscriptions expiring soon
            now = datetime.utcnow()
            expiring_soon = UserSubscription.query.filter(
                UserSubscription.status == 'active',
                UserSubscription.expires_at <= now + timedelta(days=7),
                UserSubscription.expires_at > now,
                UserSubscription.expires_at.isnot(None)
            ).count()
            
            report = f"""
📊 DAILY SUBSCRIPTION REPORT - {now.strftime('%Y-%m-%d %H:%M:%S')}
================================================================

👥 USER STATISTICS:
   Total Users: {total_users}
   Free Users: {free_users}
   Premium Users: {premium_users}
   Pro Users: {pro_users}
   Admin Users: {admin_users}

📋 SUBSCRIPTION STATUS:
   Active Subscriptions: {active_subscriptions}
   Expired Subscriptions: {expired_subscriptions}
   Cancelled Subscriptions: {cancelled_subscriptions}
   Expiring Within 7 Days: {expiring_soon}

💰 PLAN DISTRIBUTION:
   Free Plan: {(free_users/total_users*100):.1f}%
   Premium Plan: {(premium_users/total_users*100):.1f}%
   Pro Plan: {(pro_users/total_users*100):.1f}%
   Admin Users: {(admin_users/total_users*100):.1f}%

================================================================
            """
            
            logger.info(report)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating daily report: {str(e)}")
            return False


def main():
    """Main function to run all daily checks"""
    logger.info("🚀 Starting daily subscription maintenance job...")
    
    success = True
    
    # 1. Check and expire subscriptions
    if not check_and_expire_subscriptions():
        success = False
    
    # 2. Ensure admin users have Pro access
    if not check_admin_users():
        success = False
    
    # 3. Generate daily report
    if not generate_daily_report():
        success = False
    
    if success:
        logger.info("✅ Daily subscription maintenance completed successfully!")
    else:
        logger.error("❌ Daily subscription maintenance completed with errors!")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
