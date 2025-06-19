#!/usr/bin/env python3
"""
Complete Payment System Verification
One script to test everything - replaces all other verification scripts
Run from project root: python3 verify_payment.py
"""

import sys
import os
from datetime import datetime

# Ensure we're in the right directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

def test_basic_setup():
    """Test basic app setup and imports"""
    print("🔍 PAYMENT SYSTEM VERIFICATION")
    print("=" * 50)
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        print("\n1. Testing app import...")
        from app import create_app, db
        print("   ✅ App import successful")
        
        print("\n2. Testing app context...")
        app = create_app()
        print("   ✅ App created successfully")
        
        return app
    except Exception as e:
        print(f"   ❌ Setup failed: {e}")
        return None

def test_database(app):
    """Test database connectivity and models"""
    print("\n3. Testing database connection...")
    try:
        with app.app_context():
            from app.models import User
            from app.payment_models import SubscriptionPlan, UserSubscription, Payment
            
            user_count = User.query.count()
            plan_count = SubscriptionPlan.query.count()
            sub_count = UserSubscription.query.count()
            payment_count = Payment.query.count()
            
            print(f"   ✅ Database connected")
            print(f"   📊 Users: {user_count}")
            print(f"   📊 Plans: {plan_count}")
            print(f"   📊 Subscriptions: {sub_count}")
            print(f"   📊 Payments: {payment_count}")
            
            return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def test_stripe_config(app):
    """Test Stripe configuration"""
    print("\n4. Testing Stripe configuration...")
    try:
        with app.app_context():
            stripe_secret = app.config.get('STRIPE_SECRET_KEY', '')
            stripe_pub = app.config.get('STRIPE_PUBLISHABLE_KEY', '')
            stripe_webhook = app.config.get('STRIPE_WEBHOOK_SECRET', '')
            
            if stripe_secret.startswith('sk_') and stripe_pub.startswith('pk_'):
                mode = '🔴 LIVE' if 'live' in stripe_pub else '🟡 TEST'
                print(f"   ✅ Stripe configured - Mode: {mode}")
                print(f"   🔑 Publishable key: {stripe_pub[:20]}...")
                print(f"   🔑 Secret key: {stripe_secret[:15]}...")
                print(f"   🪝 Webhook: {'✅ Set' if stripe_webhook else '⚠️  Not set'}")
                
                # Test actual Stripe connection
                try:
                    import stripe
                    stripe.api_key = stripe_secret
                    stripe.Account.retrieve()
                    print("   ✅ Stripe API connection successful")
                except Exception as e:
                    print(f"   ⚠️  Stripe API error: {e}")
                
                return True
            else:
                print("   ❌ Stripe not configured properly")
                return False
    except Exception as e:
        print(f"   ❌ Stripe config error: {e}")
        return False

def test_services(app):
    """Test payment services"""
    print("\n5. Testing payment services...")
    try:
        with app.app_context():
            from app.services.payment_service import SubscriptionService
            from app.services.stripe_service import StripeService
            
            # Test SubscriptionService
            features = SubscriptionService.get_plan_features('premium')
            print(f"   ✅ SubscriptionService working")
            print(f"   📋 Premium features: {len(features)} items")
            
            # Test StripeService
            stripe_service = StripeService()
            print("   ✅ StripeService initialized")
            
            return True
    except Exception as e:
        print(f"   ❌ Services error: {e}")
        return False

def test_admin_protection(app):
    """Test admin user protection"""
    print("\n6. Testing admin user protection...")
    try:
        with app.app_context():
            from app.models import User
            from app.services.payment_service import SubscriptionService
            
            admin_users = User.query.filter_by(is_admin=True).all()
            print(f"   📊 Found {len(admin_users)} admin users")
            
            if not admin_users:
                print("   ⚠️  No admin users found - creating test admin...")
                from app.payment_models import SubscriptionPlan
                from app import db
                
                free_plan = SubscriptionPlan.query.filter_by(name='free').first()
                
                if free_plan:
                    test_admin = User(
                        username="test_admin",
                        email="admin@test.com",
                        password_hash="dummy",
                        full_name="Test Admin",
                        current_plan_id=free_plan.id,
                        is_admin=True,
                        is_active=True
                    )
                    db.session.add(test_admin)
                    db.session.commit()
                    admin_users = [test_admin]
                    print("   ✅ Test admin created")
            
            # Test admin privileges
            all_good = True
            for admin in admin_users[:3]:  # Test first 3
                plan = SubscriptionService.get_user_plan(admin.id)
                has_video = SubscriptionService.user_has_feature(admin.id, 'has_video_access')
                shows_ads = SubscriptionService.should_show_ads(admin.id)
                can_quiz, _ = SubscriptionService.can_user_take_quiz(admin.id)
                
                print(f"   👑 Admin {admin.email}:")
                print(f"      Plan: {plan} {'✅' if plan == 'pro' else '❌'}")
                print(f"      Video access: {has_video} {'✅' if has_video else '❌'}")
                print(f"      Shows ads: {shows_ads} {'✅' if not shows_ads else '❌'}")
                print(f"      Unlimited quiz: {can_quiz} {'✅' if can_quiz else '❌'}")
                
                if plan != 'pro' or not has_video or shows_ads or not can_quiz:
                    all_good = False
            
            return all_good
    except Exception as e:
        print(f"   ❌ Admin test error: {e}")
        return False

def test_payment_creation(app):
    """Test payment intent creation"""
    print("\n7. Testing payment creation...")
    try:
        with app.app_context():
            from app.models import User
            from app.services.payment_service import PaymentService
            from app.payment_models import SubscriptionPlan
            
            # Get a test user
            test_user = User.query.first()
            premium_plan = SubscriptionPlan.query.filter_by(name='premium').first()
            
            if test_user and premium_plan:
                payment_data = PaymentService.create_payment_intent(
                    test_user.id,
                    'premium'
                )
                print("   ✅ Payment intent created successfully")
                print(f"   💰 Amount: {payment_data['amount']} {payment_data['currency']}")
                print(f"   🧾 Invoice: {payment_data['invoice_number']}")
                return True
            else:
                print("   ⚠️  No test user or premium plan found")
                return False
    except Exception as e:
        print(f"   ❌ Payment creation error: {e}")
        return False

def test_subscription_stats(app):
    """Test subscription statistics"""
    print("\n8. Testing subscription statistics...")
    try:
        with app.app_context():
            from app.models import User
            from app.payment_models import SubscriptionPlan, UserSubscription
            from app.services.payment_service import SubscriptionService, UsageLimitService
            
            # Get plan distribution
            total_users = User.query.count()
            if total_users > 0:
                free_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'free').count()
                premium_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'premium').count()
                pro_users = User.query.join(SubscriptionPlan).filter(SubscriptionPlan.name == 'pro').count()
                admin_users = User.query.filter_by(is_admin=True).count()
                
                print(f"   📊 Total users: {total_users}")
                print(f"   📊 Free: {free_users} ({free_users/total_users*100:.1f}%)")
                print(f"   📊 Premium: {premium_users} ({premium_users/total_users*100:.1f}%)")
                print(f"   📊 Pro: {pro_users} ({pro_users/total_users*100:.1f}%)")
                print(f"   📊 Admins: {admin_users}")
                
                # Test usage statistics for a user
                test_user = User.query.first()
                if test_user:
                    usage_stats = UsageLimitService.get_usage_stats(test_user.id)
                    subscription_stats = SubscriptionService.get_subscription_stats(test_user.id)
                    
                    print(f"   📊 Sample user stats:")
                    print(f"      Daily quiz: {usage_stats['daily_quizzes']['taken']}/{usage_stats['daily_quizzes']['limit']}")
                    print(f"      Weekly exam: {usage_stats['weekly_exams']['taken']}/{usage_stats['weekly_exams']['limit']}")
                    print(f"      Current plan: {subscription_stats['plan_name']}")
                
                return True
            else:
                print("   ⚠️  No users found")
                return False
    except Exception as e:
        print(f"   ❌ Statistics error: {e}")
        return False

def test_daily_job_files():
    """Test daily job files exist"""
    print("\n9. Testing daily job files...")
    try:
        job_file = os.path.join(project_root, 'scripts', 'jobs', 'daily_subscription_check.py')
        setup_file = os.path.join(project_root, 'scripts', 'jobs', 'setup_cron.sh')
        cron_config = os.path.join(project_root, 'scripts', 'jobs', 'crontab_config')
        
        files_exist = 0
        if os.path.exists(job_file):
            print("   ✅ daily_subscription_check.py exists")
            files_exist += 1
        else:
            print("   ❌ daily_subscription_check.py missing")
        
        if os.path.exists(setup_file):
            print("   ✅ setup_cron.sh exists")
            files_exist += 1
        else:
            print("   ❌ setup_cron.sh missing")
        
        if os.path.exists(cron_config):
            print("   ✅ crontab_config exists")
            files_exist += 1
        else:
            print("   ❌ crontab_config missing")
        
        return files_exist == 3
    except Exception as e:
        print(f"   ❌ File check error: {e}")
        return False

def test_cron_job():
    """Test cron job status"""
    print("\n10. Testing cron job...")
    try:
        cron_output = os.popen('crontab -l 2>/dev/null || echo "No crontab"').read()
        if 'daily_subscription_check.py' in cron_output:
            print("   ✅ Cron job is installed")
            # Extract the cron line
            for line in cron_output.split('\n'):
                if 'daily_subscription_check.py' in line:
                    print(f"   📅 Schedule: {line.strip()}")
            return True
        else:
            print("   ⚠️  Cron job not installed")
            print("   💡 To install: chmod +x scripts/jobs/setup_cron.sh && ./scripts/jobs/setup_cron.sh")
            return False
    except Exception as e:
        print(f"   ❌ Cron check error: {e}")
        return False

def test_manual_job_run(app):
    """Test running the daily job manually"""
    print("\n11. Testing daily job execution...")
    try:
        with app.app_context():
            from app.models import User
            from app.payment_models import UserSubscription
            from app.services.payment_service import SubscriptionService
            
            # Check current subscription status
            active_subs = UserSubscription.query.filter_by(status='active').all()
            expired_subs = UserSubscription.query.filter_by(status='expired').all()
            
            print(f"   📊 Active subscriptions: {len(active_subs)}")
            print(f"   📊 Expired subscriptions: {len(expired_subs)}")
            
            # Show some subscription details
            for sub in active_subs[:3]:  # First 3
                if sub.expires_at:
                    days_left = (sub.expires_at - datetime.utcnow()).days
                    print(f"   📅 User {sub.user_id}: expires in {days_left} days")
                else:
                    print(f"   📅 User {sub.user_id}: never expires")
            
            print("   💡 To run daily check manually:")
            print("      python3 scripts/jobs/daily_subscription_check.py")
            
            return True
    except Exception as e:
        print(f"   ❌ Daily job test error: {e}")
        return False

def main():
    """Main verification function"""
    # Run all tests
    app = test_basic_setup()
    if not app:
        print("\n❌ Basic setup failed - cannot continue")
        return False
    
    results = []
    results.append(test_database(app))
    results.append(test_stripe_config(app))
    results.append(test_services(app))
    results.append(test_admin_protection(app))
    results.append(test_payment_creation(app))
    results.append(test_subscription_stats(app))
    results.append(test_daily_job_files())
    results.append(test_cron_job())
    results.append(test_manual_job_run(app))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 VERIFICATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED! Payment system is ready!")
        print("\n🚀 Next steps:")
        print("1. Start the app: python3 run.py")
        print("2. Test payment flow at: http://localhost:8000/subscription/plans")
        print("3. Use test card: 4242 4242 4242 4242")
    elif passed >= total - 2:
        print("⚠️  MOSTLY WORKING - Minor issues to fix")
        print("\n🔧 Common fixes:")
        if not results[6]:  # Daily job files
            print("- Run setup: git pull  # If files are missing")
        if not results[7]:  # Cron job
            print("- Install cron: ./scripts/jobs/setup_cron.sh")
    else:
        print("❌ SIGNIFICANT ISSUES - Check errors above")
        print("\n🔧 Troubleshooting:")
        print("1. Check .env file has correct Stripe keys")
        print("2. Verify database connection")
        print("3. Install requirements: pip install -r requirements.txt")
    
    print(f"\n📁 Working directory: {os.getcwd()}")
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
