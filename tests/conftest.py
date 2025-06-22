# tests/conftest.py - pytest configuration and fixtures
import pytest
import sys
import os
from datetime import datetime, date

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, UserProgress, Question, Option, QuizSession, Achievement
from config import Config


class TestConfig(Config):
    """Test configuration - ISOLATED from production"""
    TESTING = True
    # Use in-memory SQLite for tests - completely isolated
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    ADMIN_EMAIL_NOTIFICATIONS = False
    STRIPE_PUBLISHABLE_KEY = 'pk_test_fake'
    STRIPE_SECRET_KEY = 'sk_test_fake'
    # Use fake Redis URL for tests (won't connect to real Redis)
    REDIS_URL = 'redis://localhost:6379/15'  # Different Redis DB for tests


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Override database to ensure we're using test database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # Create all tables in the in-memory test database
        db.create_all()
        yield app
        # Clean up - this only affects the in-memory database
        try:
            db.drop_all()
        except:
            pass  # Ignore errors during cleanup


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function') 
def clean_db(app):
    """Provide a clean database for each test"""
    with app.app_context():
        # Create fresh tables for each test
        db.create_all()
        yield db
        # Clean up after test
        try:
            # Truncate all tables instead of deleting with foreign keys
            db.session.execute('PRAGMA foreign_keys=OFF;')
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
            db.session.execute('PRAGMA foreign_keys=ON;')
        except:
            db.session.rollback()


@pytest.fixture(scope='function')
def init_database(clean_db):
    """Initialize database with test data"""
    # Create test data in the clean test database
    create_test_data()
    yield clean_db
    # Cleanup is handled by clean_db fixture


def create_test_data():
    """Create test data for testing"""
    # Create test user with proper password hash
    from werkzeug.security import generate_password_hash
    
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpassword'),
        full_name='Test User',
        is_verified=True,
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.flush()
    
    # Create user progress
    progress = UserProgress(user_id=user.id)
    db.session.add(progress)
    
    # Create test questions
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
