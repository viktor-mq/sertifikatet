#!/usr/bin/env python3
"""
Email Testing Script - Test all email functions in the Sertifikatet project
Run this to verify that all email configurations are working correctly.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, AdminReport
from app.utils.email import (
    send_verification_email, send_password_reset_email, send_welcome_email,
    send_learning_reminder_email, send_badge_notification, send_streak_lost_email,
    send_weekly_summary_email, send_study_tip_email, send_admin_alert,
    send_user_report_alert, send_manual_review_alert
)
from app.security import AdminSecurityService, EmailService
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_test_user():
    """Create a test user for email testing"""
    test_user = User(
        username='testuser',
        email='viktorandreas@hotmail.com',  # Your email for testing
        full_name='Test User',
        is_active=True,
        is_verified=True,
        created_at=datetime.now()  # Add created_at for email templates
    )
    return test_user

def test_all_emails():
    """Test all email functions in the system"""
    
    app = create_app()
    
    # Configure Flask app for URL generation
    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', 'localhost:8000')
    app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
    
    with app.app_context():
        print("🧪 SERTIFIKATET EMAIL TESTING")
        print("=" * 50)
        print(f"📧 All test emails will be sent to: viktorandreas@hotmail.com")
        print("=" * 50)
        
        # Create test user
        test_user = create_test_user()
        
        # Test counter
        test_count = 0
        success_count = 0
        
        print("\n📋 TESTING USER EMAILS (noreply@sertifikatet.no):")
        print("-" * 50)
        
        # 1. Email Verification
        test_count += 1
        try:
            print(f"{test_count}. Testing email verification...")
            send_verification_email(test_user)
            print("   ✅ Email verification sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 2. Password Reset
        test_count += 1
        try:
            print(f"{test_count}. Testing password reset...")
            send_password_reset_email(test_user)
            print("   ✅ Password reset sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 3. Welcome Email
        test_count += 1
        try:
            print(f"{test_count}. Testing welcome email...")
            send_welcome_email(test_user)
            print("   ✅ Welcome email sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 4. Learning Reminder
        test_count += 1
        try:
            print(f"{test_count}. Testing learning reminder...")
            send_learning_reminder_email(test_user)
            print("   ✅ Learning reminder sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 5. Badge Notification
        test_count += 1
        try:
            print(f"{test_count}. Testing badge notification...")
            send_badge_notification(test_user, "Test Badge 🏆")
            print("   ✅ Badge notification sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 6. Streak Lost
        test_count += 1
        try:
            print(f"{test_count}. Testing streak lost notification...")
            send_streak_lost_email(test_user, 7)
            print("   ✅ Streak lost notification sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 7. Weekly Summary
        test_count += 1
        try:
            print(f"{test_count}. Testing weekly summary...")
            test_stats = {
                'xp_earned': 150,
                'quizzes_taken': 5,
                'correct_percentage': 85,
                'streak_days': 7
            }
            send_weekly_summary_email(test_user, test_stats)
            print("   ✅ Weekly summary sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 8. Study Tip
        test_count += 1
        try:
            print(f"{test_count}. Testing study tip...")
            tip_data = {
                'area': 'Trafikkskilt',
                'tips': ['Øv mer på vikeplikt-skilt', 'Fokuser på fareskilt']
            }
            send_study_tip_email(test_user, tip_data)
            print("   ✅ Study tip sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print("\n📋 TESTING ADMIN EMAILS (info@sertifikatet.no):")
        print("-" * 50)
        
        # 9. Admin Alert
        test_count += 1
        try:
            print(f"{test_count}. Testing admin alert...")
            send_admin_alert("Test Alert", "This is a test admin alert message.")
            print("   ✅ Admin alert sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 10. User Report Alert
        test_count += 1
        try:
            print(f"{test_count}. Testing user report alert...")
            report_data = {
                'type': 'Bug Report',
                'message': 'Test bug report message',
                'priority': 'Medium',
                'created_at': datetime.now()  # Add timestamp to fix strftime error
            }
            
            # Count AdminReports before
            reports_before = AdminReport.query.count()
            
            send_user_report_alert(test_user, report_data)
            
            # Check if AdminReport was created
            reports_after = AdminReport.query.count()
            if reports_after > reports_before:
                print("   ✅ User report alert sent and AdminReport created!")
            else:
                print("   ✅ User report alert sent! (Note: AdminReport might have failed)")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 11. Manual Review Alert
        test_count += 1
        try:
            print(f"{test_count}. Testing manual review alert...")
            details = {
                'review_type': 'Content Review',
                'description': 'Test content needs manual review',
                'urgency': 'Low'
            }
            send_manual_review_alert("Test Review", details)
            print("   ✅ Manual review alert sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print("\n📋 TESTING NEW ADMIN SECURITY EMAILS (info@sertifikatet.no):")
        print("-" * 50)
        
        # 12. Admin Creation Alert
        test_count += 1
        try:
            print(f"{test_count}. Testing admin creation alert...")
            
            # Create a fake admin user for testing
            new_admin = User(
                username='testadmin',
                email='testadmin@example.com',
                full_name='Test Admin User',
                is_admin=True,
                is_active=True,
                created_at=datetime.now()  # Add created_at timestamp
            )
            
            granting_admin = User(
                username='Viktor',
                email='viktorandreas@hotmail.com',
                full_name='Viktor Andreas',
                is_admin=True,
                created_at=datetime.now()  # Add created_at timestamp
            )
            
            EmailService.send_admin_creation_alert(
                new_admin_user=new_admin,
                granting_admin_user=granting_admin,
                ip_address='127.0.0.1'
            )
            print("   ✅ Admin creation alert sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # 13. Admin Revocation Alert
        test_count += 1
        try:
            print(f"{test_count}. Testing admin revocation alert...")
            
            EmailService.send_admin_revocation_alert(
                revoked_admin_user=new_admin,
                revoking_admin_user=granting_admin,
                ip_address='127.0.0.1'
            )
            print("   ✅ Admin revocation alert sent!")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print("\n" + "=" * 50)
        print("📊 EMAIL TEST RESULTS:")
        print("=" * 50)
        print(f"✅ Successful: {success_count}/{test_count}")
        print(f"❌ Failed: {test_count - success_count}/{test_count}")
        
        # Check AdminReport creation
        print("\n🔍 ADMIN REPORT VERIFICATION:")
        recent_reports = AdminReport.query.filter(
            AdminReport.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
        print(f"📋 Admin reports created today: {recent_reports}")
        
        if success_count == test_count:
            print("\n🎉 ALL EMAILS SENT SUCCESSFULLY!")
            print("📧 Check viktorandreas@hotmail.com for all test emails")
            print("🛡️ Check /admin/reports to see the created reports")
        else:
            print(f"\n⚠️  {test_count - success_count} email(s) failed to send")
            print("Check your .env email configuration")
        
        print("\n📋 EMAIL BREAKDOWN:")
        print(f"📨 User emails (noreply@): Tests 1-8")
        print(f"👨‍💼 Admin emails (info@): Tests 9-13") 
        print(f"📧 All emails sent to: viktorandreas@hotmail.com")
        
        print("\n🔍 WHAT TO CHECK:")
        print("- Check your inbox for all 13 test emails")
        print("- Verify emails come from correct senders:")
        print("  • noreply@sertifikatet.no (tests 1-8)")
        print("  • info@sertifikatet.no (tests 9-13)")
        print("- Check that HTML formatting looks good")
        print("- Verify all links work correctly")

if __name__ == '__main__':
    print("🚀 Starting email tests...")
    print("⚠️  Make sure your .env file is configured correctly!")
    
    # Ask for confirmation
    response = input("\nSend test emails to viktorandreas@hotmail.com? (y/N): ")
    if response.lower() in ['y', 'yes']:
        test_all_emails()
    else:
        print("❌ Test cancelled")
