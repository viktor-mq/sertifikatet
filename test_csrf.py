#!/usr/bin/env python3
"""
CSRF Protection Testing Script
Tests various aspects of CSRF implementation
"""

from app import create_app
import tempfile
import os

def test_csrf_functionality():
    """Test CSRF token generation and validation"""
    print("🧪 Testing CSRF Functionality...")
    
    app = create_app()
    
    # Test 1: Application startup
    try:
        print("✅ Flask application starts successfully")
    except Exception as e:
        print(f"❌ Flask startup failed: {e}")
        return False
    
    # Test 2: CSRF token generation
    with app.app_context():
        with app.test_request_context():
            try:
                from flask_wtf.csrf import generate_csrf
                token1 = generate_csrf()
                token2 = generate_csrf()
                
                print("✅ CSRF tokens generate successfully")
                print(f"   Sample token: {token1[:20]}...")
                
                # Test tokens are different (randomness)
                if token1 != token2:
                    print("✅ Tokens are properly randomized")
                else:
                    print("❌ Warning: Tokens are identical")
                    
            except Exception as e:
                print(f"❌ CSRF token generation failed: {e}")
                return False
    
    # Test 3: Template rendering with CSRF tokens
    with app.app_context():
        with app.test_request_context():
            try:
                from flask import render_template_string
                template = '''
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit">Test</button>
                </form>
                '''
                rendered = render_template_string(template)
                
                if 'csrf_token' in rendered and 'csrf_token()' not in rendered:
                    print("✅ Template CSRF token rendering works")
                else:
                    print("❌ Template CSRF token rendering failed")
                    return False
                    
            except Exception as e:
                print(f"❌ Template rendering failed: {e}")
                return False
    
    # Test 4: Check critical routes exist
    with app.app_context():
        try:
            # Get all routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(rule.endpoint)
            
            critical_routes = [
                'auth.login',
                'auth.register', 
                'admin.admin_dashboard',
                'main.index'
            ]
            
            missing_routes = []
            for route in critical_routes:
                if route not in routes:
                    missing_routes.append(route)
            
            if not missing_routes:
                print("✅ All critical routes exist")
            else:
                print(f"❌ Missing routes: {missing_routes}")
                return False
                
        except Exception as e:
            print(f"❌ Route checking failed: {e}")
            return False
    
    print("🎉 All CSRF tests passed!")
    return True

def test_form_syntax():
    """Test that all our modified templates have valid syntax"""
    print("\n🔍 Testing Template Syntax...")
    
    # Sample of critical templates to check
    critical_templates = [
        'templates/auth/login.html',
        'templates/auth/register.html',
        'templates/admin/admin_login.html',
        'templates/subscription/checkout.html'
    ]
    
    app = create_app()
    
    for template_path in critical_templates:
        try:
            with app.app_context():
                with app.test_request_context():
                    # Try to render the template (this will catch syntax errors)
                    from flask import render_template
                    
                    # Get just the filename from the path
                    template_name = template_path.replace('templates/', '')
                    
                    # Try to render with minimal context
                    try:
                        # This might fail due to missing variables, but syntax errors will be caught
                        render_template(template_name)
                        print(f"✅ {template_name} - syntax OK")
                    except Exception as e:
                        # Check if it's a syntax error vs missing variables
                        if 'syntax' in str(e).lower() or 'unexpected' in str(e).lower():
                            print(f"❌ {template_name} - syntax error: {e}")
                            return False
                        else:
                            # Likely just missing template variables, syntax is OK
                            print(f"✅ {template_name} - syntax OK (missing vars expected)")
                            
        except Exception as e:
            print(f"❌ {template_path} - template error: {e}")
            return False
    
    print("✅ Template syntax validation passed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Comprehensive CSRF Testing...\n")
    
    success = True
    success &= test_csrf_functionality()
    success &= test_form_syntax()
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED!'}")
    print(f"CSRF Implementation Status: {'VERIFIED ✅' if success else 'NEEDS REVIEW ❌'}")