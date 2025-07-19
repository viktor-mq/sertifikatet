#!/usr/bin/env python3
"""
Migration script to populate existing learning_paths table with module data
Reads from your learning/ directory and populates database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from datetime import datetime
from app import create_app, db

def load_module_data():
    """Load module data from your existing learning/ directory structure"""
    modules = []
    
    # Your actual directory structure
    module_mapping = {
        1: "1.basic_traffic_theory",
        2: "2.road_signs_and_markings", 
        3: "3.vehicles_and_technology",
        4: "4.human_factors_in_traffic",
        5: "5.practice_driving_and_final_test"
    }
    
    for module_id, module_dir in module_mapping.items():
        module_path = f"learning/{module_dir}/module.yaml"
        
        print(f"Reading {module_path}...")
        
        if not os.path.exists(module_path):
            print(f"⚠️  File not found: {module_path}")
            continue
            
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                module_data = yaml.safe_load(f)
            
            # Transform to fit existing learning_paths table
            module_info = {
                'id': module_id,
                'name': module_data['title'],
                'description': module_data['description'],
                'estimated_hours': module_data['estimated_hours'],
                'difficulty_level': module_id,  # Use module number as difficulty
                'icon_filename': f'module-{module_id}.png',
                'is_recommended': (module_id == 1),  # First module recommended
                # Use existing fields for theory content tracking
                'path_type': 'theory',  # Mark as theory content
                'module_number': float(module_id),  # Store module number
                'content_file_path': module_path,  # Reference to yaml file
                'submodule_count': len(module_data.get('submodules', []))
            }
            
            modules.append(module_info)
            print(f"✅ Loaded: {module_data['title']} ({len(module_data.get('submodules', []))} submodules)")
            
        except Exception as e:
            print(f"❌ Error loading {module_path}: {e}")
    
    return modules

def populate_database():
    """Populate learning_paths table with module data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Import your models
            from app.models import LearningPath, LearningPathItem
            
            print("🚀 Starting database population...")
            
            # Load module data from files
            modules = load_module_data()
            
            if not modules:
                print("❌ No modules found to migrate!")
                return False
            
            print(f"\n📊 Found {len(modules)} modules to migrate")
            
            for module in modules:
                print(f"\n🔄 Processing: {module['name']}")
                
                # Check if module already exists
                existing = LearningPath.query.filter_by(id=module['id']).first()
                
                if existing:
                    print(f"   Updating existing module...")
                    # Update existing
                    existing.name = module['name']
                    existing.description = module['description']
                    existing.estimated_hours = module['estimated_hours']
                    existing.difficulty_level = module['difficulty_level']
                    existing.icon_filename = module['icon_filename']
                    existing.is_recommended = module['is_recommended']
                    
                    # Add new fields if they exist
                    if hasattr(existing, 'path_type'):
                        existing.path_type = module['path_type']
                    if hasattr(existing, 'module_number'):
                        existing.module_number = module['module_number']
                    if hasattr(existing, 'content_file_path'):
                        existing.content_file_path = module['content_file_path']
                        
                else:
                    print(f"   Creating new module...")
                    # Create new learning path with only the basic fields that exist
                    learning_path = LearningPath(
                        id=module['id'],
                        name=module['name'],
                        description=module['description'],
                        estimated_hours=module['estimated_hours'],
                        difficulty_level=module['difficulty_level'],
                        icon_filename=module['icon_filename'],
                        is_recommended=module['is_recommended']
                    )
                    
                    # Add optional fields if they exist in the model
                    if hasattr(LearningPath, 'path_type'):
                        learning_path.path_type = module['path_type']
                        print("   Added path_type field")
                    if hasattr(LearningPath, 'module_number'):
                        learning_path.module_number = module['module_number']
                        print("   Added module_number field")
                    if hasattr(LearningPath, 'content_file_path'):
                        learning_path.content_file_path = module['content_file_path']
                        print("   Added content_file_path field")
                    db.session.add(learning_path)
                
                # Create a learning path item to track that this has submodules
                # Clear existing items for this path first
                LearningPathItem.query.filter_by(path_id=module['id']).delete()
                
                # Add an item to indicate this path has theory content
                path_item = LearningPathItem(
                    path_id=module['id'],
                    item_type='theory_module',  # Custom type to mark theory modules
                    item_id=module['submodule_count'],  # Store submodule count
                    order_index=1,
                    is_mandatory=True
                )
                db.session.add(path_item)
                
                print(f"   ✅ Configured with {module['submodule_count']} submodules")
            
            # Commit all changes
            db.session.commit()
            print("\n🎉 Database population completed successfully!")
            
            # Verify the migration
            if hasattr(LearningPath, 'path_type'):
                theory_paths = LearningPath.query.filter_by(path_type='theory').order_by(LearningPath.id).all()
            else:
                # If no path_type field, just get all paths (they're all theory modules now)
                theory_paths = LearningPath.query.order_by(LearningPath.id).all()
            
            print(f"\n📊 Verification: Found {len(theory_paths)} modules in database:")
            for path in theory_paths:
                module_num = getattr(path, 'module_number', path.id)
                print(f"  - Module {module_num}: {path.name}")
                
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def verify_setup():
    """Verify that the setup is ready for migration"""
    print("🔍 Verifying setup...")
    
    # Check if learning directory exists
    if not os.path.exists('learning'):
        print("❌ learning/ directory not found")
        return False
    
    # Check if module files exist
    required_modules = [
        'learning/1.basic_traffic_theory/module.yaml',
        'learning/2.road_signs_and_markings/module.yaml',
        'learning/3.vehicles_and_technology/module.yaml',
        'learning/4.human_factors_in_traffic/module.yaml',
        'learning/5.practice_driving_and_final_test/module.yaml'
    ]
    
    missing_files = []
    for module_file in required_modules:
        if not os.path.exists(module_file):
            missing_files.append(module_file)
    
    if missing_files:
        print("❌ Missing module files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All module files found")
    return True

if __name__ == "__main__":
    print("📚 Learning Content Migration Script")
    print("=" * 50)
    
    if not verify_setup():
        print("\n❌ Setup verification failed. Please check your file structure.")
        sys.exit(1)
    
    if populate_database():
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test the integration: python scripts/test_migration.py")
        print("2. Visit /learning/dashboard to see your modules")
        print("3. Your learning system is now database-driven!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
