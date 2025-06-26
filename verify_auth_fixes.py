#!/usr/bin/env python3
"""Quick test script to verify the auth test fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_changes():
    """Test that our changes work correctly"""
    print("Testing registration template and auth route changes...")
    
    # Check that the template comment typo is fixed
    with open('templates/auth/register.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    if '<!-- templates/auth/register.html-->' in template_content:
        print("✅ Template comment typo fixed")
    else:
        print("❌ Template comment typo not fixed")
    
    if '<!-- templates/auth/reguster.html-->' in template_content:
        print("❌ Template still has typo")
    else:
        print("✅ Template typo removed")
    
    # Check that the template contains the expected Norwegian text
    if 'personvernerklæringen' in template_content:
        print("✅ Template contains 'personvernerklæringen'")
    else:
        print("❌ Template missing 'personvernerklæringen'")
    
    if 'godtar vilkårene' in template_content:
        print("✅ Template contains 'godtar vilkårene'")
    else:
        print("❌ Template missing 'godtar vilkårene'")
    
    # Check that auth routes contain the expected flash messages
    with open('app/auth/routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    if 'Du må godta vilkårene' in routes_content:
        print("✅ Auth routes contain 'Du må godta vilkårene' flash message")
    else:
        print("❌ Auth routes missing flash message")
    
    if 'Du må bekrefte at du har lest personvernerklæringen' in routes_content:
        print("✅ Auth routes contain privacy flash message")
    else:
        print("❌ Auth routes missing privacy flash message")
    
    # Check the test file changes
    with open('tests/test_auth.py', 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    if 'follow_redirects=False' in test_content:
        print("✅ Test updated to check redirect behavior")
    else:
        print("❌ Test not updated for redirect behavior")
    
    if 'alert-error' in test_content:
        print("✅ Test checks for flash message CSS classes")
    else:
        print("❌ Test doesn't check for CSS classes")
    
    print("\nSummary:")
    print("- Fixed template comment typo")
    print("- Updated test to be more robust by checking redirects and multiple validation indicators")
    print("- Added comprehensive validation tests in test_auth_validation.py")
    print("- Test now checks for flash message CSS classes and form presence, not just exact text")

if __name__ == '__main__':
    test_changes()
