# tests/test_basic.py - Basic tests that don't require complex database operations
import pytest


class TestBasicFunctionality:
    """Test basic functionality without complex database operations"""
    
    def test_app_creation(self, app):
        """Test that the app is created successfully"""
        assert app is not None
        assert app.config['TESTING'] is True
        assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']
    
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_register_page(self, client):
        """Test register page loads"""
        response = client.get('/auth/register')
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'Side ikke funnet' in response.data or b'404' in response.data
    
    def test_api_404_error(self, client):
        """Test 404 error for API endpoints returns JSON"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        # Should return JSON for API endpoints
        assert response.content_type == 'application/json'


class TestQuizPages:
    """Test quiz-related pages"""
    
    def test_quiz_page(self, client, init_database):
        """Test quiz page redirects to login when not authenticated"""
        response = client.get('/quiz')
        assert response.status_code == 302
    
    def test_quiz_categories_page(self, client, init_database):
        """Test quiz categories page redirects to login when not authenticated"""
        response = client.get('/quiz/categories')
        assert response.status_code == 302
