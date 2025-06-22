# tests/conftest.py - pytest configuration and fixtures
import pytest
import sys
import os
from datetime import datetime, date

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, UserProgress, Question, Option, QuizSession, Achievement


class TestConfig:
    """Test configuration - COMPLETELY ISOLATED from production"""
    TESTING = True
    # Force SQLite in-memory database - completely isolated
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-that-is-long-enough-for-security'
    DEBUG = False
    ADMIN_EMAIL_NOTIFICATIONS = False
    STRIPE_PUBLISHABLE_KEY = 'pk_test_fake'
    STRIPE_SECRET_KEY = 'sk_test_fake'
    REDIS_URL = 'redis://localhost:6379/15'  # Different Redis DB for tests
    
    # Override any other settings that might interfere
    UPLOAD_FOLDER = '/tmp/test_uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB for tests
    SITE_NAME = 'Test Sertifikatet'


@pytest.fixture(scope='session')
def app():
    """Create application for testing with complete database isolation"""
    
    # Store original environment variables
    original_env = {}
    env_vars_to_override = ['DATABASE_URL', 'TESTING', 'FLASK_ENV']
    
    for var in env_vars_to_override:
        original_env[var] = os.environ.get(var)
    
    try:
        # Force test environment variables
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['TESTING'] = '1'
        os.environ['FLASK_ENV'] = 'testing'
        
        # Create Flask app with test configuration
        app = create_app(TestConfig)
        
        # Triple check the database URI is correct
        final_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if 'mysql' in final_uri.lower() or 'sertifikatet' in final_uri:
            raise RuntimeError(f"CRITICAL: Test using production database! URI: {final_uri}")
        
        print(f"✅ Test using database: {final_uri}")
        
        with app.app_context():
            # Database is already initialized by create_app(), just verify and create tables
            
            # Verify we're using SQLite
            engine_url = str(db.engine.url)
            print(f"✅ Database engine: {engine_url}")
            
            if 'sqlite' not in engine_url:
                raise RuntimeError(f"CRITICAL: Not using SQLite! Engine: {engine_url}")
            
            # Create all tables
            db.create_all()
            
            yield app
            
            # Comprehensive cleanup
            try:
                # Close all database sessions
                db.session.remove()
                # Drop all tables
                db.drop_all()
                # Dispose of the engine completely
                if hasattr(db, 'engine') and db.engine is not None:
                    db.engine.dispose()
                print("✅ Database cleanup completed")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
                pass
                
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function') 
def clean_db(app):
    """Provide a clean database for each test"""
    with app.app_context():
        # Verify we're still using the test database
        engine_url = str(db.engine.url)
        if 'sqlite' not in engine_url:
            raise RuntimeError(f"Database switched! Now using: {engine_url}")
            
        print(f"✅ Clean DB using: {engine_url}")
        
        # Drop and recreate all tables for complete isolation
        db.drop_all()
        db.create_all()
        
        yield db
        
        # Cleanup after test
        try:
            db.session.remove()
            db.drop_all()
        except Exception as e:
            print(f"Cleanup error: {e}")
            try:
                db.session.rollback()
            except:
                pass


@pytest.fixture(scope='function')
def init_database(clean_db):
    """Initialize database with test data"""
    create_test_data()
    yield clean_db


def create_test_data():
    """Create minimal test data for testing"""
    from werkzeug.security import generate_password_hash
    from app.payment_models import SubscriptionPlan
    
    # Create a minimal subscription plan first (required for User)
    try:
        # Check if free plan already exists
        free_plan = SubscriptionPlan.query.filter_by(name='free').first()
        if not free_plan:
            plan = SubscriptionPlan(
                id=1,
                name='free',  # This is critical - registration looks for name='free'
                display_name='Free Plan',
                price_nok=0.00,
                billing_cycle='monthly',
                description='Free test plan',
                has_ads=True,
                is_active=True
            )
            db.session.add(plan)
            db.session.flush()
    except Exception as e:
        print(f"Note: Could not create subscription plan: {e}")
        # Continue without plan if the model doesn't exist
        pass
    
    # Create test user
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpassword'),
        full_name='Test User',
        is_verified=True,
        created_at=datetime.utcnow(),
        current_plan_id=1
    )
    db.session.add(user)
    db.session.flush()
    
    # Create user progress
    progress = UserProgress(user_id=user.id)
    db.session.add(progress)
    
    # Create test question
    question = Question(
        question='Hva betyr dette skiltet?',
        correct_option='a',
        category='Fareskilt',
        difficulty_level=1,
        explanation='Dette er et fareskilt som varsler om fare.',
        is_active=True
    )
    db.session.add(question)
    db.session.flush()
    
    # Add options
    options = [
        Option(question_id=question.id, option_letter='a', option_text='Fareskilt'),
        Option(question_id=question.id, option_letter='b', option_text='Påbudsskilt'),
        Option(question_id=question.id, option_letter='c', option_text='Forbudsskilt'),
        Option(question_id=question.id, option_letter='d', option_text='Opplysningsskilt')
    ]
    for option in options:
        db.session.add(option)
    
    db.session.commit()
