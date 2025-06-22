#!/usr/bin/env python3
"""
Test error email notification system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.errors import ErrorHandler

def test_error_email():
    """Test sending error notification email"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 TESTING ERROR EMAIL NOTIFICATION")
        print("=" * 50)
        
        # Check email configuration
        print("\n📧 Email Configuration:")
        print(f"ADMIN_MAIL_SERVER: {app.config.get('ADMIN_MAIL_SERVER')}")
        print(f"ADMIN_MAIL_USERNAME: {app.config.get('ADMIN_MAIL_USERNAME')}")
        print(f"ADMIN_MAIL_PASSWORD: {'*' * len(app.config.get('ADMIN_MAIL_PASSWORD', '')) if app.config.get('ADMIN_MAIL_PASSWORD') else 'NOT SET'}")
        print(f"SUPER_ADMIN_EMAIL: {app.config.get('SUPER_ADMIN_EMAIL')}")
        print(f"ADMIN_EMAILS: {app.config.get('ADMIN_EMAILS')}")
        
        # Create a test error
        print("\n🎯 Creating test error...")
        try:
            # Simulate an error
            test_error = Exception("This is a test error for email notification system")
            
            # Test the error notification
            print("📤 Attempting to send error notification email...")
            result = ErrorHandler._send_error_notification_email(
                error=test_error,
                error_type="test_error",
                report=None
            )
            
            if result:
                print("✅ Error notification email sent successfully!")
                print("📧 Check your email for the notification.")
            else:
                print("❌ Failed to send error notification email.")
                print("💡 Check the logs above for specific error details.")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("🏁 Test completed!")

if __name__ == '__main__':
    test_error_email()
