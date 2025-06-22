# tests/test_auth.py - Test authentication functionality
import pytest
from app.models import User


class TestAuthentication:
    """Test authentication functionality"""
    
    def test_user_registration(self, client, init_database):
        """Test user registration"""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPassword123',
            'full_name': 'New User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert not user.is_verified  # Should require email verification
    
    def test_user_login_success(self, client, init_database):
        """Test successful login"""
        # Create test user directly in database
        from werkzeug.security import generate_password_hash
        from app import db
        
        user = User(
            username='testlogin',
            email='testlogin@example.com',
            password_hash=generate_password_hash('TestPassword123'),
            full_name='Test Login',
            is_verified=True,
            current_plan_id=1  # Required field
        )
        db.session.add(user)
        db.session.commit()
        
        # Test login
        response = client.post('/auth/login', data={
            'username': 'testlogin',
            'password': 'TestPassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Check for success indicators
        assert b'Velkommen tilbake' in response.data or b'dashboard' in response.data
    
    def test_user_login_invalid(self, client, init_database):
        """Test login with invalid credentials"""
        response = client.post('/auth/login', data={
            'username': 'invalid',
            'password': 'invalid'
        })
        
        assert response.status_code == 200
        assert b'Ugyldig brukernavn eller passord' in response.data
