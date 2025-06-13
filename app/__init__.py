from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
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
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app
