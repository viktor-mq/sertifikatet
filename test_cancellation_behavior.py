#!/usr/bin/env python3
"""
Test Subscription Cancellation Behavior
Verify that cancellation works correctly with grace period
"""

import sys
import os
from datetime import datetime, timedelta

# Ensure we're in the right directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

def test_cancellation_behavior():
    """Test that subscription cancellation gives users grace period"""
    print("🚫 Testing Subscription Cancellation")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.models import User
        from app.payment_models import SubscriptionPlan, UserSubscription
        from app.services.payment_service import SubscriptionService
        
        app = create_app()
        
        with app.app_context():
            # Create a test premium user with active subscription
            print("\\n1. Setting up test scenario...")
            
            premium_plan = SubscriptionPlan.query.filter_by(name='premium').first()
            if not premium_plan:
                print("   ❌ Premium plan not found!")
                return False
            
            # Create test user
            test_user = User.query.filter_by(email='test_cancel@test.com').first()
            if not test_user:
                test_user = User(
                    username='test_cancel',
                    email='test_cancel@test.com',
                    password_hash='dummy',
                    full_name='Test Cancel User',
                    current_plan_id=premium_plan.id,
                    subscription_status='active',
                    is_active=True
                )
                db.session.add(test_user)
                db.session.flush()
            
            # Create active subscription that expires in 15 days
            future_expiry = datetime.utcnow() + timedelta(days=15)
            
            test_subscription = UserSubscription.query.filter_by(
                user_id=test_user.id,
                status='active'
            ).first()
            
            if not test_subscription:
                test_subscription = UserSubscription(
                    user_id=test_user.id,
                    plan_id=premium_plan.id,
                    status='active',
                    started_at=datetime.utcnow() - timedelta(days=15),  # Started 15 days ago
                    expires_at=future_expiry,  # Expires in 15 days
                    next_billing_date=future_expiry,
                    auto_renew=True,
                    is_trial=False
                )
                db.session.add(test_subscription)
            else:
                test_subscription.expires_at = future_expiry
                test_subscription.status = 'active'
                test_subscription.auto_renew = True
            
            db.session.commit()
            print(f"   ✅ Created test user with Premium subscription")
            print(f"   📅 Subscription expires: {future_expiry.strftime('%Y-%m-%d %H:%M')}")
            
            # Test 2: Check current access BEFORE cancellation
            print("\\n2. Testing access BEFORE cancellation...")
            
            user_plan = SubscriptionService.get_user_plan(test_user.id)
            can_watch_video, _ = SubscriptionService.can_user_watch_video(test_user.id)
            shows_ads = SubscriptionService.should_show_ads(test_user.id)
            subscription_stats = SubscriptionService.get_subscription_stats(test_user.id)
            
            print(f"   📊 User plan: {user_plan}")
            print(f"   📹 Can watch videos: {can_watch_video}")
            print(f"   📺 Shows ads: {shows_ads}")
            print(f"   📋 Subscription status: {subscription_stats['status']}")
            print(f"   🔄 Auto renew: {subscription_stats['auto_renew']}")
            
            if user_plan != 'premium' or not can_watch_video or shows_ads:
                print("   ❌ User doesn't have proper Premium access before cancellation!")
                return False
            
            # Test 3: Cancel the subscription
            print("\\n3. Cancelling subscription...")
            
            success = SubscriptionService.cancel_subscription(test_user.id, 'Testing cancellation behavior')
            
            if not success:
                print("   ❌ Cancellation failed!")
                return False
            
            print(f"   ✅ Subscription cancelled successfully")
            
            # Test 4: Check access AFTER cancellation (should still have access!)
            print("\\n4. Testing access AFTER cancellation...")
            
            user_plan_after = SubscriptionService.get_user_plan(test_user.id)
            can_watch_after, video_msg = SubscriptionService.can_user_watch_video(test_user.id)
            shows_ads_after = SubscriptionService.should_show_ads(test_user.id)
            subscription_stats_after = SubscriptionService.get_subscription_stats(test_user.id)
            
            print(f"   📊 User plan: {user_plan_after}")
            print(f"   📹 Can watch videos: {can_watch_after}")
            print(f"   📺 Shows ads: {shows_ads_after}")
            print(f"   📋 Subscription status: {subscription_stats_after['status']}")
            print(f"   🔄 Auto renew: {subscription_stats_after['auto_renew']}")
            print(f"   📅 Expires at: {subscription_stats_after['expires_at']}")
            print(f"   🚫 Cancelled at: {subscription_stats_after['cancelled_at']}")
            
            # Verify correct behavior
            expected_behavior = True
            issues = []
            
            # User should STILL have Premium access
            if user_plan_after != 'premium':
                issues.append(f\"User plan changed to {user_plan_after} (should stay premium until expiry)\")
                expected_behavior = False
            
            # User should STILL be able to watch videos
            if not can_watch_after:
                issues.append(f\"User lost video access immediately (should keep until expiry)\")
                expected_behavior = False
            
            # User should STILL not see ads
            if shows_ads_after:
                issues.append(f\"User sees ads immediately (should not see ads until expiry)\")
                expected_behavior = False
            
            # Subscription should be marked as cancelled
            if subscription_stats_after['status'] != 'cancelled':
                issues.append(f\"Subscription status is {subscription_stats_after['status']} (should be 'cancelled')\")
                expected_behavior = False
            
            # Auto renew should be disabled
            if subscription_stats_after['auto_renew']:
                issues.append(f\"Auto renew is still enabled (should be disabled)\")
                expected_behavior = False
            
            # Should have cancellation date
            if not subscription_stats_after['cancelled_at']:
                issues.append(f\"No cancellation date recorded\")
                expected_behavior = False
            
            # Test 5: Results
            print(\"\\n5. Cancellation Behavior Results...\")
            
            if expected_behavior:
                print(\"   ✅ PERFECT! Cancellation behavior is user-friendly:\")
                print(\"      - User keeps Premium access until expiry date\")
                print(\"      - Subscription marked as cancelled\")
                print(\"      - Auto-renew disabled\")
                print(\"      - User gets full value for money paid\")
                return True
            else:
                print(\"   ❌ Issues with cancellation behavior:\")
                for issue in issues:
                    print(f\"      - {issue}\")
                return False
                
    except Exception as e:
        print(f\"   ❌ Error during testing: {e}\")
        import traceback
        traceback.print_exc()
        return False

def main():
    \"\"\"Main test function\"\"\"
    success = test_cancellation_behavior()
    
    print(\"\\n\" + \"=\" * 40)
    if success:
        print(\"✅ SUBSCRIPTION CANCELLATION: EXCELLENT\")
        print(\"Users get full value and keep access until expiry!\")
    else:
        print(\"❌ SUBSCRIPTION CANCELLATION: NEEDS FIXING\") 
        print(\"Users are losing access immediately - this will anger customers!\")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
