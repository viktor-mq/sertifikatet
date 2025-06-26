# tests/test_auth_validation.py - Test auth validation logic
import pytest
from app.models import User


class TestAuthValidation:
    """Test authentication validation logic"""
    
    def test_registration_validation_missing_terms(self, client, init_database):
        """Test that registration validation properly rejects missing terms"""
        initial_user_count = User.query.count()
        
        response = client.post('/auth/register', data={
            'username': 'testuser_no_terms',
            'email': 'test_no_terms@example.com',
            'password': 'ValidPassword123',
            'full_name': 'Test User No Terms'
            # Missing 'terms' and 'privacy' checkboxes
        }, follow_redirects=False)
        
        # Should redirect (not create user and show success page)
        assert response.status_code == 302
        assert '/auth/register' in response.location
        
        # User should not be created
        final_user_count = User.query.count()
        assert final_user_count == initial_user_count
        
        # Specific user should not exist
        user = User.query.filter_by(username='testuser_no_terms').first()
        assert user is None
    
    def test_registration_validation_missing_privacy(self, client, init_database):
        """Test that registration validation properly rejects missing privacy consent"""
        initial_user_count = User.query.count()
        
        response = client.post('/auth/register', data={
            'username': 'testuser_no_privacy',
            'email': 'test_no_privacy@example.com',
            'password': 'ValidPassword123',
            'full_name': 'Test User No Privacy',
            'terms': 'on'  # Terms accepted but privacy missing
            # Missing 'privacy' checkbox
        }, follow_redirects=False)
        
        # Should redirect (not create user)
        assert response.status_code == 302
        assert '/auth/register' in response.location
        
        # User should not be created
        final_user_count = User.query.count()
        assert final_user_count == initial_user_count
        
        # Specific user should not exist
        user = User.query.filter_by(username='testuser_no_privacy').first()
        assert user is None
    
    def test_registration_validation_both_consents_given(self, client, init_database):
        """Test that registration succeeds when both consents are given"""
        initial_user_count = User.query.count()
        
        response = client.post('/auth/register', data={
            'username': 'testuser_valid',
            'email': 'test_valid@example.com',
            'password': 'ValidPassword123',
            'full_name': 'Test User Valid',
            'terms': 'on',      # Terms accepted
            'privacy': 'on'     # Privacy accepted
        }, follow_redirects=False)
        
        # Should redirect to success page or verification page
        assert response.status_code == 302
        # Should NOT redirect back to register page
        assert '/auth/register' not in response.location
        
        # User should be created
        final_user_count = User.query.count()
        assert final_user_count == initial_user_count + 1
        
        # Specific user should exist
        user = User.query.filter_by(username='testuser_valid').first()
        assert user is not None
        assert user.email == 'test_valid@example.com'
        assert not user.is_verified  # Should require email verification
