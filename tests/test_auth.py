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
            'full_name': 'New User',
            'terms': 'on',  # Required checkbox
            'privacy': 'on'  # Required checkbox
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
    
    def test_registration_without_terms_fails(self, client, init_database):
        """Test that registration fails without accepting terms"""
        # First test without following redirects to see the immediate response
        response = client.post('/auth/register', data={
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'TestPassword123',
            'full_name': 'New User 2'
            # Missing terms and privacy checkboxes
        }, follow_redirects=False)
        
        # Should get a redirect response
        assert response.status_code == 302
        assert '/auth/register' in response.location
        
        # Now follow the redirect to see the flash messages
        response = client.get('/auth/register')
        assert response.status_code == 200
        
        response_text = response.data.decode('utf-8')
        
        # Check for validation failure indicators
        validation_failed = (
            # Flash message about terms
            'godta vilkårene' in response_text or
            'Du må godta' in response_text or
            # Flash message about privacy
            'personvernerklæringen' in response_text or
            'Du må bekrefte' in response_text or
            # Error message styling
            'alert-error' in response_text or
            'bg-red-600' in response_text
        )
        
        assert validation_failed, f"Expected validation failure indicators not found. Response contains: {response_text[:1000]}..."
        
        # Most important: user should not be created
        user = User.query.filter_by(username='newuser2').first()
        assert user is None, "User should not be created when terms are not accepted"
