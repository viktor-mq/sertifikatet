from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_class=None):
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Load configuration first
    if config_class is not None:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Set up error handling (NEW)
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    # Set up rate limiting and security (NEW) - temporarily commented out
    # from .security.rate_limiter import limiter, rate_limit_handler
    # from .security.middleware import SecurityMiddleware
    # from .security.csrf_protection import setup_csrf_protection
    
    # limiter.init_app(app)
    # app.register_error_handler(429, rate_limit_handler)
    # SecurityMiddleware(app)
    # setup_csrf_protection(app)
    
    # Set up performance monitoring (NEW) - temporarily commented out
    # from .utils.performance_monitor import PerformanceMonitor
    # app.before_request(PerformanceMonitor.before_request)
    # app.after_request(PerformanceMonitor.after_request)
    
    # Set up session optimization (NEW) - temporarily commented out
    # from .utils.session_optimization import SessionOptimizer
    # SessionOptimizer.configure_session(app)
    
    # Register blueprints
    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from .main.routes import main_bp
    app.register_blueprint(main_bp)
    
    from .quiz.routes import quiz_bp
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from .learning import learning_bp
    app.register_blueprint(learning_bp, url_prefix='/learning')
    
    from .gamification import gamification_bp
    app.register_blueprint(gamification_bp, url_prefix='/gamification')
    
    # Register video blueprints
    from .video import video_bp, video_api_bp, register_filters
    app.register_blueprint(video_bp)
    app.register_blueprint(video_api_bp)
    register_filters(app)  # Register video-specific Jinja2 filters
    
    # Register custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if parsed else []
            except (json.JSONDecodeError, TypeError) as e:
                print(f"JSON decode error for value: {value[:100]}... Error: {e}")
                return []
        return value or []
    
    # Register game blueprint
    from .game import game_bp
    app.register_blueprint(game_bp)
    
    # Register subscription blueprint
    from .subscription import subscription_bp
    app.register_blueprint(subscription_bp)
    
    # Register ML blueprint
    from .ml import ml_bp
    app.register_blueprint(ml_bp, url_prefix='/ml')
    
    # Register health check blueprint (NEW) - temporarily commented out
    # from .utils.health_check import health_bp
    # app.register_blueprint(health_bp)
    
    # Apply developer authentication (for development protection)
    from .middleware import apply_dev_auth_to_app
    apply_dev_auth_to_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        # Import all models to ensure they're registered
        from . import models, gamification_models, video_models, payment_models, notification_models, marketing_models
        from .ml import models as ml_models
        db.create_all()
        
        # Create database indexes for performance (NEW) - temporarily commented out
        # from .utils.database_optimization import DatabaseOptimizer
        # DatabaseOptimizer.create_indexes()
        
        # Initialize cache service (NEW) - temporarily commented out
        # from .services.cache_service import cache
        # cache.connect()
    
    # Set up background tasks if Celery is available (NEW) - temporarily commented out
    # try:
    #     from .utils.async_tasks import make_celery
    #     celery = make_celery(app)
    #     app.celery = celery
    # except ImportError:
    #     app.logger.info("Celery not available, background tasks disabled")
    
    return app
