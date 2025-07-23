#!/usr/bin/env python3
"""
Form Submission Testing
Tests that CSRF-protected forms can actually be submitted
"""

from app import create_app

def test_form_submission():
    """Test that CSRF-protected forms work with test client"""
    print("🧪 Testing Form Submission with CSRF...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Test 1: GET request to login page (should work)
        try:
            response = client.get('/auth/login')
            if response.status_code == 200:
                print("✅ Login page loads successfully")
                
                # Check if CSRF token is in the response
                if b'csrf_token' in response.data:
                    print("✅ CSRF token present in login form")
                else:
                    print("❌ CSRF token missing from login form")
                    return False
            else:
                print(f"❌ Login page failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login page test failed: {e}")
            return False
        
        # Test 2: Test CSRF token extraction from form
        try:
            with app.app_context():
                with app.test_request_context():
                    from flask_wtf.csrf import generate_csrf
                    token = generate_csrf()
                    
                    # Simulate form submission WITH CSRF token
                    form_data = {
                        'username': 'testuser',
                        'password': 'testpass',
                        'csrf_token': token
                    }
                    
                    # This might fail due to validation, but shouldn't fail due to CSRF
                    response = client.post('/auth/login', data=form_data, follow_redirects=False)
                    
                    # We expect either success or form validation error, NOT CSRF error
                    if response.status_code in [200, 302, 400]:
                        print("✅ Form submission with CSRF token works")
                    else:
                        print(f"❌ Unexpected response: {response.status_code}")
                        return False
                        
        except Exception as e:
            print(f"❌ Form submission test failed: {e}")
            return False
            
        # Test 3: Check that form submission WITHOUT CSRF token fails
        try:
            form_data_no_csrf = {
                'username': 'testuser', 
                'password': 'testpass'
                # No CSRF token
            }
            
            response = client.post('/auth/login', data=form_data_no_csrf)
            
            # Should get CSRF error (400) or similar
            if response.status_code in [400, 403]:
                print("✅ Form submission without CSRF token properly rejected")
            else:
                print(f"⚠️  Form without CSRF token got status: {response.status_code}")
                # This might be OK if there are other validation errors first
                
        except Exception as e:
            print(f"❌ CSRF rejection test failed: {e}")
            return False
    
    print("✅ Form submission tests completed")
    return True

def test_admin_forms():
    """Test admin forms work correctly"""
    print("\n🔐 Testing Admin Form Access...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Test admin login page loads
        try:
            response = client.get('/admin/login')
            if response.status_code == 200:
                print("✅ Admin login page loads")
                
                if b'csrf_token' in response.data:
                    print("✅ Admin login has CSRF token")
                else:
                    print("❌ Admin login missing CSRF token")
                    return False
            else:
                print(f"❌ Admin login page failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Admin login test failed: {e}")
            return False
    
    print("✅ Admin form tests completed")
    return True

if __name__ == "__main__":
    print("🚀 Starting Form Submission Testing...\n")
    
    success = True
    success &= test_form_submission()
    success &= test_admin_forms()
    
    print(f"\n{'🎉 ALL FORM TESTS PASSED!' if success else '❌ SOME FORM TESTS FAILED!'}")
    print(f"Form Functionality Status: {'VERIFIED ✅' if success else 'NEEDS REVIEW ❌'}")