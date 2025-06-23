#!/usr/bin/env python3
"""
Email Configuration Diagnostic Script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def check_email_config():
    """Check email configuration in detail"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 EMAIL CONFIGURATION DIAGNOSTIC")
        print("=" * 50)
        
        # Check user email config (noreply)
        print("\n📨 USER EMAIL CONFIG (noreply@):")
        print("-" * 30)
        
        mail_server = os.environ.get('MAIL_SERVER')
        mail_port = os.environ.get('MAIL_PORT')
        mail_username = os.environ.get('MAIL_USERNAME')
        mail_password = os.environ.get('MAIL_PASSWORD')
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER')
        
        print(f"MAIL_SERVER: {mail_server}")
        print(f"MAIL_PORT: {mail_port}")
        print(f"MAIL_USERNAME: {mail_username}")
        print(f"MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else 'NOT SET'}")
        print(f"MAIL_DEFAULT_SENDER: {mail_sender}")
        
        user_config_ok = all([mail_server, mail_port, mail_username, mail_password])
        print(f"✅ User email config complete: {user_config_ok}")
        
        # Check admin email config (info)
        print("\n👨‍💼 ADMIN EMAIL CONFIG (info@):")
        print("-" * 30)
        
        admin_mail_server = os.environ.get('ADMIN_MAIL_SERVER', mail_server)
        admin_mail_port = os.environ.get('ADMIN_MAIL_PORT', mail_port)
        admin_mail_username = os.environ.get('ADMIN_MAIL_USERNAME', mail_username)
        admin_mail_password = os.environ.get('ADMIN_MAIL_PASSWORD', mail_password)
        admin_mail_sender = os.environ.get('ADMIN_MAIL_DEFAULT_SENDER', mail_sender)
        
        print(f"ADMIN_MAIL_SERVER: {admin_mail_server}")
        print(f"ADMIN_MAIL_PORT: {admin_mail_port}")
        print(f"ADMIN_MAIL_USERNAME: {admin_mail_username}")
        print(f"ADMIN_MAIL_PASSWORD: {'*' * len(admin_mail_password) if admin_mail_password else 'NOT SET'}")
        print(f"ADMIN_MAIL_DEFAULT_SENDER: {admin_mail_sender}")
        
        admin_config_ok = all([admin_mail_server, admin_mail_port, admin_mail_username, admin_mail_password])
        print(f"✅ Admin email config complete: {admin_config_ok}")
        
        # Check Flask app config
        print("\n⚙️ FLASK APP EMAIL CONFIG:")
        print("-" * 30)
        
        app_admin_server = app.config.get('ADMIN_MAIL_SERVER')
        app_admin_username = app.config.get('ADMIN_MAIL_USERNAME') 
        app_admin_password = app.config.get('ADMIN_MAIL_PASSWORD')
        
        print(f"App ADMIN_MAIL_SERVER: {app_admin_server}")
        print(f"App ADMIN_MAIL_USERNAME: {app_admin_username}")
        print(f"App ADMIN_MAIL_PASSWORD: {'*' * len(app_admin_password) if app_admin_password else 'NOT SET'}")
        
        # Test basic SMTP connection
        print("\n🔌 TESTING SMTP CONNECTION:")
        print("-" * 30)
        
        try:
            import smtplib
            
            # Test user email SMTP
            if user_config_ok:
                try:
                    server = smtplib.SMTP(mail_server, int(mail_port))
                    server.starttls()
                    server.login(mail_username, mail_password)
                    server.quit()
                    print("✅ User email SMTP connection: SUCCESS")
                except Exception as e:
                    print(f"❌ User email SMTP connection: FAILED - {e}")
            else:
                print("⚠️ User email SMTP: SKIPPED (config incomplete)")
            
            # Test admin email SMTP
            if admin_config_ok:
                try:
                    server = smtplib.SMTP(admin_mail_server, int(admin_mail_port))
                    server.starttls()
                    server.login(admin_mail_username, admin_mail_password)
                    server.quit()
                    print("✅ Admin email SMTP connection: SUCCESS")
                except Exception as e:
                    print(f"❌ Admin email SMTP connection: FAILED - {e}")
            else:
                print("⚠️ Admin email SMTP: SKIPPED (config incomplete)")
                
        except Exception as e:
            print(f"❌ SMTP test failed: {e}")
        
        print("\n" + "=" * 50)
        print("📋 SUMMARY:")
        print("=" * 50)
        
        if user_config_ok:
            print("✅ User email configuration looks good")
        else:
            print("❌ User email configuration incomplete")
            print("   Check MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD in .env")
        
        if admin_config_ok:
            print("✅ Admin email configuration looks good")
        else:
            print("❌ Admin email configuration incomplete")
            print("   Check ADMIN_MAIL_* variables in .env")
        
        print("\n🔧 NEXT STEPS:")
        if not user_config_ok or not admin_config_ok:
            print("1. Fix missing email configuration in .env file")
            print("2. Restart your application")
            print("3. Run the email test again")
        else:
            print("1. Configuration looks good!")
            print("2. Run: python test_all_emails.py")
            print("3. Check for other potential issues (firewall, etc.)")

if __name__ == '__main__':
    check_email_config()
