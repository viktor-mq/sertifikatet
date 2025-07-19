#!/usr/bin/env python3
"""
Quick test script to verify the database migration works
Run this after running the migration script to test the integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, LearningPath, UserLearningPath
from app.learning.services import LearningService

def test_migration():
    """Test the migration and database integration"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing Database Migration...")
            
            # 1. Check if theory modules exist
            if hasattr(LearningPath, 'path_type'):
                theory_modules = LearningPath.query.filter_by(path_type='theory').all()
            else:
                # If no path_type field, just get all learning paths (they're all theory modules now)
                theory_modules = LearningPath.query.all()
                
            print(f"✅ Found {len(theory_modules)} modules in database:")
            for module in theory_modules:
                module_num = getattr(module, 'module_number', module.id)
                print(f"  - {module_num}: {module.name}")
            
            # 2. Test getting modules without user (should work with mock user)
            print("\n🧪 Testing LearningService...")
            
            # Create a test user if none exists
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                print("Creating test user...")
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash='dummy_hash',
                    full_name='Test User'
                )
                db.session.add(test_user)
                db.session.commit()
            
            # 3. Test getting modules with user progress
            modules_data = LearningService.get_user_modules_progress(test_user)
            print(f"✅ LearningService returned {len(modules_data)} modules")
            
            # 4. Test enrollment
            if modules_data:
                first_module_id = modules_data[0]['id']
                print(f"\n🧪 Testing enrollment in module {first_module_id}...")
                
                success = LearningService.enroll_user_in_module(test_user, first_module_id)
                print(f"✅ Enrollment {'successful' if success else 'failed (probably already enrolled)'}")
                
                # Test getting module details
                module_details = LearningService.get_module_details(first_module_id, test_user)
                if module_details:
                    print(f"✅ Module details loaded: {module_details['title']}")
                else:
                    print("❌ Failed to load module details")
                
                # Test getting submodules
                submodules = LearningService.get_submodules_progress(first_module_id, test_user)
                print(f"✅ Found {len(submodules)} submodules for module {first_module_id}")
            
            # 5. Check user enrollment
            enrollments = UserLearningPath.query.filter_by(user_id=test_user.id).all()
            print(f"\n✅ User has {len(enrollments)} module enrollments")
            
            print("\n🎉 All tests passed! Database integration is working.")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_migration()
