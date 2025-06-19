#!/usr/bin/env python3
"""
Debug subscription enforcement 
Check if a free user actually has restrictions
"""

import sys
import os

# Ensure we're in the right directory
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

def debug_user_access():
    """Debug why free user might have access to everything"""
    print("🔍 DEBUGGING USER ACCESS")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.models import User
        from app.services.payment_service import SubscriptionService
        
        app = create_app()
        
        with app.app_context():
            # Find the test user
            test_user = User.query.filter_by(email__like='%test%').first()
            if not test_user:
                test_user = User.query.first()
            
            if not test_user:
                print("   ❌ No users found!")
                return False
            
            print(f"\\n1. User Details:")
            print(f"   👤 Email: {test_user.email}")
            print(f"   🆔 ID: {test_user.id}")
            print(f"   👑 Is Admin: {test_user.is_admin}")
            print(f"   🔗 Current Plan ID: {test_user.current_plan_id}")
            print(f"   📊 Subscription Status: {test_user.subscription_status}")
            
            # Check detected plan
            detected_plan = SubscriptionService.get_user_plan(test_user.id)
            print(f"   📋 Detected Plan: {detected_plan}")
            
            # Check if user is admin (this might be the issue!)
            if test_user.is_admin:
                print(f"   🚨 FOUND THE ISSUE! User is ADMIN - admins get Pro access to everything!")
                print(f"   💡 Admins bypass all subscription restrictions")
                return "admin"
            
            # Check specific features
            print(f"\\n2. Feature Access Check:")
            features = [
                ('has_video_access', 'Videos'),
                ('has_detailed_stats', 'Detailed Stats'),
                ('has_ai_adaptive', 'AI Adaptive'),
                ('has_ads', 'Shows Ads (should be True for free)')
            ]
            
            for feature, name in features:
                has_access = SubscriptionService.user_has_feature(test_user.id, feature)
                expected = True if feature == 'has_ads' and detected_plan == 'free' else False
                status = "✅" if (has_access == expected or detected_plan != 'free') else "❌"
                print(f"   {status} {name}: {has_access}")
            
            # Check quiz limits
            print(f"\\n3. Quiz Limits Check:")
            can_practice, practice_msg = SubscriptionService.can_user_take_quiz(test_user.id, 'practice')
            can_exam, exam_msg = SubscriptionService.can_user_take_quiz(test_user.id, 'exam')
            
            print(f"   📝 Can take practice quiz: {can_practice}")
            if practice_msg:
                print(f"      Message: {practice_msg}")
            print(f"   📋 Can take exam: {can_exam}")
            if exam_msg:
                print(f"      Message: {exam_msg}")
            
            # Check video access
            print(f"\\n4. Video Access Check:")
            can_watch, video_msg = SubscriptionService.can_user_watch_video(test_user.id)
            print(f"   📹 Can watch videos: {can_watch}")
            if video_msg:
                print(f"      Message: {video_msg}")
            
            # Determine if restrictions are working
            if detected_plan == 'free' and not test_user.is_admin:
                # Free user should have restrictions
                if can_watch or not SubscriptionService.user_has_feature(test_user.id, 'has_ads'):
                    print(f"\\n   ❌ FREE USER HAS UNRESTRICTED ACCESS - SECURITY ISSUE!")
                    return False
                else:
                    print(f"\\n   ✅ Free user properly restricted")
                    return True
            else:
                print(f"\\n   ℹ️  User has premium access (plan: {detected_plan}, admin: {test_user.is_admin})")
                return True
                
    except Exception as e:
        print(f"   ❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_real_free_user():
    """Create a non-admin free user for testing"""
    print("\\n🆕 Creating Real Free User for Testing")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.models import User
        from app.payment_models import SubscriptionPlan
        
        app = create_app()
        
        with app.app_context():
            # Get free plan
            free_plan = SubscriptionPlan.query.filter_by(name='free').first()
            if not free_plan:
                print("   ❌ Free plan not found!")
                return False
            
            # Check if free test user already exists
            free_user = User.query.filter_by(email='free_test@test.com').first()
            if free_user:
                print(f"   ℹ️  Free test user already exists: {free_user.email}")
                return free_user
            
            # Create new free user
            free_user = User(
                username='free_test_user',
                email='free_test@test.com',
                password_hash='dummy_hash',
                full_name='Free Test User',
                current_plan_id=free_plan.id,
                subscription_status='active',
                is_admin=False,  # IMPORTANT: Not admin!
                is_active=True
            )
            
            db.session.add(free_user)
            db.session.commit()
            
            print(f"   ✅ Created free test user: {free_user.email}")
            print(f"   📊 Plan ID: {free_user.current_plan_id}")
            print(f"   👑 Is Admin: {free_user.is_admin}")
            
            return free_user
            
    except Exception as e:
        print(f"   ❌ Error creating free user: {e}")
        return False

def main():
    """Main debug function"""
    result = debug_user_access()
    
    if result == "admin":
        print("\\n" + "=" * 40)
        print("🚨 ISSUE FOUND: Your test user is an ADMIN!")
        print("Admins automatically get Pro access to everything.")
        print("\\nSolutions:")
        print("1. Test with a non-admin user")
        print("2. Create a real free user for testing")
        print("\\nCreating a real free user now...")
        
        free_user = create_real_free_user()
        if free_user:
            print("\\n✅ Now test the restrictions with this free user!")
            print(f"   Login as: {free_user.email}")
            print(f"   This user should have restrictions.")
    elif result:
        print("\\n" + "=" * 40)
        print("✅ ACCESS CONTROL WORKING CORRECTLY")
    else:
        print("\\n" + "=" * 40) 
        print("❌ ACCESS CONTROL NOT WORKING - SECURITY ISSUE!")
        print("Free users can access premium features!")
    
    return result

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
