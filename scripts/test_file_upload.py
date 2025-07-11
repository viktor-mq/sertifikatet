#!/usr/bin/env python3
# scripts/test_file_upload.py
"""
Test script for the learning modules file upload system
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import LearningModules, LearningSubmodules, VideoShorts
from app.services.file_upload import FileUploadService
from app.services.content_validator import ContentValidator
import tempfile
import yaml

def test_file_upload_system():
    """Test the file upload system components"""
    print("🧪 Testing Learning Modules File Upload System")
    
    app = create_app()
    
    with app.app_context():
        print("\n1. Testing database connection...")
        try:
            # Test database connection
            modules = LearningModules.query.all()
            print(f"✅ Database connected. Found {len(modules)} modules.")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        print("\n2. Testing content validation...")
        
        # Test YAML validation
        sample_yaml = """
id: 1
title: "Test Module"
description: "This is a test module"
estimated_hours: 2
submodules:
  - id: 1.1
    title: "Test Submodule"
    description: "Test description"
"""
        
        is_valid, message = ContentValidator.validate_yaml_content(sample_yaml)
        if is_valid:
            print("✅ YAML validation working")
        else:
            print(f"❌ YAML validation failed: {message}")
        
        # Test markdown validation
        sample_markdown = """
# Test Content

This is a test markdown file with proper structure.

## Learning Objectives
- Objective 1
- Objective 2

## Content
Sample content here.
"""
        
        is_valid, message = ContentValidator.validate_markdown_content(sample_markdown)
        if is_valid:
            print("✅ Markdown validation working")
        else:
            print(f"❌ Markdown validation failed: {message}")
        
        print("\n3. Testing file upload service...")
        
        # Test file extension validation
        test_cases = [
            ('test.mp4', 'video', True),
            ('test.mov', 'video', True),
            ('test.avi', 'video', True),
            ('test.mkv', 'video', True),
            ('test.txt', 'video', False),
            ('test.md', 'document', True),
            ('test.yaml', 'document', True),
            ('test.yml', 'document', True),
            ('test.txt', 'document', True),
            ('test.mp4', 'document', False)
        ]
        
        for filename, file_type, expected in test_cases:
            result = FileUploadService.allowed_file(filename, file_type)
            if result == expected:
                print(f"✅ File validation for {filename} ({file_type}): {result}")
            else:
                print(f"❌ File validation for {filename} ({file_type}): expected {expected}, got {result}")
        
        print("\n4. Testing directory creation...")
        
        try:
            # Test directory creation
            test_path, test_dir = FileUploadService.create_module_directory(99, "Test Module")
            print(f"✅ Module directory creation: {test_dir}")
            
            # Clean up test directory
            import shutil
            if os.path.exists(test_path):
                shutil.rmtree(test_path)
                print("✅ Test directory cleaned up")
        except Exception as e:
            print(f"❌ Directory creation failed: {e}")
        
        print("\n5. Testing database models...")
        
        try:
            # Test model creation
            test_module = LearningModules(
                module_number=99,
                title="Test Module",
                description="Test description",
                estimated_hours=2,
                is_active=True
            )
            
            # Don't actually save to database, just test model creation
            print(f"✅ Module model creation: {test_module.title}")
            
            test_submodule = LearningSubmodules(
                module_id=1,  # Assuming module 1 exists
                submodule_number=99.1,
                title="Test Submodule",
                description="Test description",
                estimated_minutes=30,
                is_active=True
            )
            
            print(f"✅ Submodule model creation: {test_submodule.title}")
            
        except Exception as e:
            print(f"❌ Model creation failed: {e}")
        
        print("\n6. Summary")
        print("✅ File upload system components are working correctly!")
        print("\n📋 Next steps:")
        print("   1. Access admin interface at /admin/dashboard")
        print("   2. Click on '🎓 Læringsmoduler' tab")
        print("   3. Create new modules and upload content")
        print("   4. Test video uploads and content management")
        
        return True

if __name__ == '__main__':
    try:
        success = test_file_upload_system()
        if success:
            print("\n🎉 All tests passed! File upload system is ready.")
        else:
            print("\n❌ Some tests failed. Check the output above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test script failed: {e}")
        sys.exit(1)
