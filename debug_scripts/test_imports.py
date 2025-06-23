# Test script to check for import errors
import sys
sys.path.insert(0, '/Users/viktorigesund/Documents/teoritest')

try:
    from app import create_app
    print("✓ App import successful")
    
    app = create_app()
    print("✓ App created successfully")
    
    with app.app_context():
        from app import db
        # This will create tables and add missing columns
        db.create_all()
        print("✓ Database tables created/updated")
        
        # Update Viktor to admin
        from app.models import User
        viktor = User.query.filter_by(username='Viktor').first()
        if viktor:
            viktor.is_admin = True
            viktor.subscription_tier = 'pro'
            db.session.commit()
            print("✓ Viktor updated to admin")
    
    print("\n✓ All imports and setup successful! You can now run the server.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
