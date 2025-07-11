#!/usr/bin/env python3
"""
Quick test to verify route conflicts are resolved
"""
import sys
import os

# Change to the project directory
os.chdir('/Users/viktorigesund/Documents/teoritest')
sys.path.insert(0, '.')

try:
    print("🔧 Testing route conflict resolution...")
    
    # Test importing the app
    from app import create_app
    app = create_app()
    
    print("✅ App created successfully - no route conflicts!")
    
    # Test admin routes are available
    with app.app_context():
        learning_routes = []
        for rule in app.url_map.iter_rules():
            if 'learning' in str(rule):
                learning_routes.append(str(rule))
        
        print(f"✅ Found {len(learning_routes)} learning routes:")
        for route in learning_routes:
            print(f"   {route}")
    
    print("\n🎉 SUCCESS: All route conflicts resolved!")
    print("\n📋 Next steps:")
    print("   1. Start the development server: python run.py")
    print("   2. Go to: http://localhost:5000/admin/dashboard")
    print("   3. Click on '🎓 Læringsmoduler' tab")
    print("   4. Test the file upload functionality")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
