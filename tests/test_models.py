# tests/test_models.py - Test database models safely
import pytest
from app.models import User, UserProgress, Question, Option
from datetime import datetime


class TestUserModel:
    """Test User model with isolated test database"""
    
    def test_user_creation(self, clean_db):
        """Test creating a user in test database"""
        from werkzeug.security import generate_password_hash
        import uuid
        
        # Use unique username to avoid any potential collisions
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        
        # First, try to create a subscription plan (required for User)
        try:
            from app.payment_models import SubscriptionPlan
            # Check if a plan with ID 1 already exists
            existing_plan = SubscriptionPlan.query.get(1)
            if not existing_plan:
                plan = SubscriptionPlan(
                    id=1,
                    name='free',
                    display_name='Free Plan',
                    price_nok=0.00,
                    billing_cycle='monthly',
                    description='Free test plan',
                    has_ads=True,
                    is_active=True
                )
                clean_db.session.add(plan)
                clean_db.session.flush()
        except ImportError:
            # If payment models don't exist, skip this part
            pass
        
        user = User(
            username=unique_username,
            email=unique_email,
            password_hash=generate_password_hash('password123'),
            full_name='New User',
            current_plan_id=1  # Reference the plan we created
        )
        clean_db.session.add(user)
        clean_db.session.commit()
        
        # Verify user was created
        created_user = User.query.filter_by(username=unique_username).first()
        assert created_user is not None
        assert created_user.username == unique_username
        assert created_user.email == unique_email
        assert created_user.is_active is True
        assert created_user.is_verified is False
        assert created_user.total_xp == 0


class TestQuestionModel:
    """Test Question model with isolated test database"""
    
    def test_question_creation(self, clean_db):
        """Test creating a question in test database"""
        question = Question(
            question='Test question?',
            correct_option='b',
            category='Test',
            difficulty_level=2,
            explanation='Test explanation',
            is_active=True
        )
        clean_db.session.add(question)
        clean_db.session.commit()
        
        # Verify question was created
        created_question = Question.query.filter_by(question='Test question?').first()
        assert created_question is not None
        assert created_question.correct_option == 'b'
        assert created_question.category == 'Test'
        assert created_question.difficulty_level == 2
        assert created_question.is_active is True
        assert created_question.created_at is not None


class TestWithTestData:
    """Test with pre-created test data"""
    
    def test_test_data_exists(self, init_database):
        """Test that our test data is created properly"""
        # Check test user exists
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.is_verified is True
        
        # Check test question exists
        question = Question.query.filter_by(category='Fareskilt').first()
        assert question is not None
        assert len(question.options) == 4
        
        # Check user progress exists
        assert user.progress is not None
