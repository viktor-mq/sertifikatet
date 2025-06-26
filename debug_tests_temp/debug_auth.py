#!/usr/bin/env python3
"""Debug script to test the auth registration functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from tests.conftest import TestConfig, create_test_data

def debug_registration_test():
    """Debug the registration test to see what's happening"""
    app = create_app(TestConfig)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        create_test_data()
        
        # Create test client
        client = app.test_client()
        
        print("=== Testing registration without terms ===")
        
        # First, test without following redirects
        response = client.post('/auth/register', data={
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'TestPassword123',
            'full_name': 'New User 2'
            # Missing terms and privacy checkboxes
        }, follow_redirects=False)
        
        print(f"Response status (no redirect): {response.status_code}")
        print(f"Response location: {response.location}")
        
        # Now test with following redirects
        response = client.post('/auth/register', data={
            'username': 'newuser2',
            'email': 'newuser2@example.com', 
            'password': 'TestPassword123',
            'full_name': 'New User 2'
            # Missing terms and privacy checkboxes
        }, follow_redirects=True)
        
        print(f"Response status (with redirect): {response.status_code}")
        print(f"Response size: {len(response.data)} bytes")
        
        # Check what's in the response
        response_text = response.data.decode('utf-8')
        
        print("\n=== Checking for expected text ===")
        print(f"Contains 'godta vilkårene': {'godta vilk' in response_text}")
        print(f"Contains 'godtar vilkårene': {'godtar vilk' in response_text}")
        print(f"Contains 'personvernerklæringen': {'personvernerkl' in response_text}")
        
        # Check for flash message areas
        print(f"Contains flash message div: {'alert alert-' in response_text}")
        print(f"Contains 'Du må godta': {'Du må godta' in response_text}")
        print(f"Contains 'Du må bekrefte': {'Du må bekrefte' in response_text}")
        
        # Look for the template comment
        if 'templates/auth/register.html' in response_text:
            print("✅ Correct template loaded")
        elif 'templates/auth/reguster.html' in response_text:
            print("❌ Template has typo in comment")
        else:
            print("? Template comment not found")
        
        # Check if user was created (should not be)
        user = User.query.filter_by(username='newuser2').first()
        print(f"User created: {user is not None}")
        
        print("\n=== Response excerpt ===")
        # Show first 1000 chars of response
        print(response_text[:1000])
        print("...")
        
        # Cleanup
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    debug_registration_test()
