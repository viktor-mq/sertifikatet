import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max file size
    
    # Site settings
    SITE_NAME = 'Sertifikatet'
    
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