import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max file size
    
    # Site settings
    SITE_NAME = 'Sertifikatet'
    
    # Environment configuration
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development' if DEBUG else 'production')
    
    # Email configuration for admin notifications and security alerts
    ADMIN_MAIL_SERVER = os.getenv('ADMIN_MAIL_SERVER', os.getenv('MAIL_SERVER', 'smtp.gmail.com'))
    ADMIN_MAIL_PORT = int(os.getenv('ADMIN_MAIL_PORT', os.getenv('MAIL_PORT', '587')))
    ADMIN_MAIL_USE_TLS = os.getenv('ADMIN_MAIL_USE_TLS', os.getenv('MAIL_USE_TLS', 'True')).lower() in ('true', '1', 'yes')
    ADMIN_MAIL_USE_SSL = os.getenv('ADMIN_MAIL_USE_SSL', os.getenv('MAIL_USE_SSL', 'False')).lower() in ('true', '1', 'yes')
    ADMIN_MAIL_USERNAME = os.getenv('ADMIN_MAIL_USERNAME', os.getenv('MAIL_USERNAME'))
    ADMIN_MAIL_PASSWORD = os.getenv('ADMIN_MAIL_PASSWORD', os.getenv('MAIL_PASSWORD'))
    ADMIN_MAIL_DEFAULT_SENDER = os.getenv('ADMIN_MAIL_DEFAULT_SENDER', os.getenv('MAIL_DEFAULT_SENDER'))
    
    # Admin security settings
    ADMIN_EMAIL_NOTIFICATIONS = os.getenv('ADMIN_EMAIL_NOTIFICATIONS', 'True').lower() in ('true', '1', 'yes')
    SUPER_ADMIN_EMAIL = os.getenv('SUPER_ADMIN_EMAIL')  # Primary admin email
    
    # Stripe payment configuration
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Google Analytics configuration
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')
    GOOGLE_TAG_MANAGER_ID = os.getenv('GOOGLE_TAG_MANAGER_ID')
    
    # SEO & Search Engine Verification (Optional - for meta tag verification)
    # Note: Google Search Console verified via Cloudflare DNS (more robust)
    GOOGLE_SEARCH_CONSOLE_VERIFICATION = os.getenv('GOOGLE_SEARCH_CONSOLE_VERIFICATION')
    BING_WEBMASTER_VERIFICATION = os.getenv('BING_WEBMASTER_VERIFICATION')
    
    # Cookie policy version (GDPR compliance)
    COOKIE_POLICY_VERSION = os.getenv('COOKIE_POLICY_VERSION', '1.0')
    
    # Feature toggles
    REGULAR_VIDEOS_ENABLED = os.getenv('REGULAR_VIDEOS_ENABLED', 'True').lower() in ('true', '1', 'yes')