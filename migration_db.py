#!/usr/bin/env python3
"""
Migration script: learning_paths → learning_modules
This script migrates data from learning_paths to learning_modules table
and updates all relationships to use the new comprehensive structure.

Usage: python scripts/migrate_to_learning_modules.py
"""

import sys
import os
import yaml
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import LearningModules, UserLearningModule
from datetime import datetime

# Try to import learning modules
try:
    from app.models import LearningModules
    HAS_MODULES_MODEL = True
except ImportError:
    try:
        from app.models import LearningModules
        LearningModules = LearningModules
        HAS_MODULES_MODEL = True
    except ImportError:
        HAS_MODULES_MODEL = False

def verify_migration_setup():
    """Verify that we have everything needed for migration"""
    print("🔍 Verifying migration setup...")
    
    if not HAS_MODULES_MODEL:
        print("❌ LearningModules model not found in app.models")
        print("   Please add the LearningModules model to your models.py first")
        return False
    
    # Check source data
    module_count = LearningModules.query.count()
    if module_count == 0:
        print("❌ No learning models found to migrate")
        return False
    
    # Check target table
    modules_count = LearningModules.query.count()
    if modules_count > 0:
        print(f"⚠️  Found {modules_count} existing learning modules")
        response = input("Do you want to clear existing modules and migrate fresh? (y/N): ")
        if response.lower() != 'y':
            print("ℹ️  Migration cancelled")
            return False
    
    print(f"✅ Found {modules_count} learning modules to migrate")
    print("✅ LearningModules model available")
    return True

def load_module_yaml_data():
    """Load additional data from module.yaml files"""
    print("📁 Loading module.yaml data for enhanced migration...")
    
    learning_dir = Path('learning')
    yaml_data = {}
    
    if not learning_dir.exists():
        print("⚠️  Learning directory not found - using basic migration")
        return yaml_data
    
    for module_dir in learning_dir.iterdir():
        if module_dir.is_dir() and not module_dir.name.startswith('.'):
            yaml_file = module_dir / 'module.yaml'
            if yaml_file.exists():
                try:
                    module_number = int(module_dir.name.split('.')[0])
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        yaml_content = yaml.safe_load(f)
                        yaml_data[module_number] = {
                            'yaml_content': yaml_content,
                            'directory': module_dir.name,
                            'content_directory': f"learning/{module_dir.name}"
                        }
                except Exception as e:
                    print(f"⚠️  Error loading {yaml_file}: {str(e)}")
    
    print(f"📊 Loaded YAML data for {len(yaml_data)} modules")
    return yaml_data

def migrate_learning_paths_to_modules():
    """Migrate data from learning_paths to learning_modules"""
    print("🚀 Starting migration from learning_paths to learning_modules...")
    
    # Load YAML data for enhancement
    yaml_data = load_module_yaml_data()
    
    # Clear existing modules if requested
    existing_count = LearningModules.query.count()
    if existing_count > 0:
        print("🧹 Clearing existing learning modules...")
        LearningModules.query.delete()
        db.session.commit()
    
    # Get all learning modules
    learning_modules = LearningModules.query.order_by(LearningModules.id).all()
    
    migrated_count = 0
    migration_mapping = {}  # old_id -> new_id
    
    for module in learning_modules:
        try:
            print(f"📖 Migrating: {module.name}")
            
            # Get enhanced data from YAML if available
            yaml_info = yaml_data.get(module.id, {})
            yaml_content = yaml_info.get('yaml_content', {})
            
            # Create learning module with comprehensive data
            module_data = {
                # Basic data from learning_path
                'module_number': module.id,
                'title': module.name,
                'description': module.description,
                'estimated_hours': module.estimated_hours,
                'difficulty_level': module.difficulty_level,
                
                # Enhanced data from YAML
                'prerequisites': yaml_content.get('prerequisites', []),
                'learning_objectives': yaml_content.get('learning_objectives', []),
                'content_directory': yaml_info.get('content_directory'),
                
                # Default values for new fields
                'is_active': True,
                'ai_generated': False,
                'last_content_update': datetime.utcnow(),
                'completion_rate': 0.0,
                'average_time_spent': (module.estimated_hours or 0) * 60,  # Convert to minutes
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Handle JSON fields (prerequisites and learning_objectives)
            if isinstance(module_data['prerequisites'], list):
                import json
                module_data['prerequisites'] = json.dumps(module_data['prerequisites'])
            
            if isinstance(module_data['learning_objectives'], list):
                import json
                module_data['learning_objectives'] = json.dumps(module_data['learning_objectives'])
            
            # Create new learning module
            learning_module = LearningModules(**module_data)
            db.session.add(learning_module)
            db.session.flush()  # Get the ID
            
            # Store mapping for relationship updates
            migration_mapping[module.id] = learning_module.id
            
            print(f"   ✅ Migrated to module ID {learning_module.id}")
            migrated_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to migrate {module.name}: {str(e)}")
            db.session.rollback()
            return False, {}
    
    try:
        db.session.commit()
        print(f"🎉 Successfully migrated {migrated_count} learning paths to modules!")
        return True, migration_mapping
        
    except Exception as e:
        print(f"❌ Error committing migration: {str(e)}")
        db.session.rollback()
        return False, {}

def update_user_learning_modules(migration_mapping):
    """Update user_learning_modules to reference new learning_modules"""
    print("👥 Updating user learning modules references...")
    
    try:
        updated_count = 0
        user_modules = UserLearningModule.query.all()
        
        for user_module in user_modules:
            old_module_id = user_modules.module_id
            new_module_id = migration_mapping.get(old_module_id)
            
            if new_module_id:
                user_module.module_id = new_module_id
                updated_count += 1
            else:
                print(f"⚠️  No mapping found for user module {user_module.id} -> learning_module {old_module_id}")
        
        db.session.commit()
        print(f"✅ Updated {updated_count} user learning module references")
        return True
        
    except Exception as e:
        print(f"❌ Error updating user learning modules: {str(e)}")
        db.session.rollback()
        return False

def update_foreign_key_constraint():
    """Update the database constraint to point to learning_modules"""
    print("🔧 Updating foreign key constraints...")
    
    try:
        # Update learning_submodules constraint
        db.engine.execute("ALTER TABLE learning_submodules DROP FOREIGN KEY learning_submodules_ibfk_1")
        db.engine.execute("ALTER TABLE learning_submodules ADD CONSTRAINT learning_submodules_ibfk_1 FOREIGN KEY (module_id) REFERENCES learning_modules(id)")
        
        print("✅ Updated learning_submodules foreign key constraint")
        return True
        
    except Exception as e:
        print(f"❌ Error updating foreign key constraint: {str(e)}")
        print("   You may need to run this SQL manually:")
        print("   ALTER TABLE learning_submodules DROP FOREIGN KEY learning_submodules_ibfk_1;")
        print("   ALTER TABLE learning_submodules ADD CONSTRAINT learning_submodules_ibfk_1 FOREIGN KEY (module_id) REFERENCES learning_modules(id);")
        return False

def verify_migration_results():
    """Verify that the migration completed successfully"""
    print("🔍 Verifying migration results...")
    
    modules_count = LearningModules.query.count()
    user_modules_count = UserLearningModule.query.count()
    
    print(f"📊 Migration Results:")
    print(f"   Learning modules: {modules_count}")
    print(f"   Learning paths (original): {paths_count}")
    print(f"   User learning paths: {user_paths_count}")
    
    # Show sample migrated data
    sample_modules = LearningModules.query.limit(3).all()
    if sample_modules:
        print(f"\n📋 Sample migrated modules:")
        for module in sample_modules:
            print(f"   Module {module.module_number}: {module.title}")
    
    return True

def show_next_steps():
    """Show what to do after migration"""
    print("\n" + "="*60)
    print("✅ Migration completed successfully!")
    
    print("\n📝 Next Steps:")
    print("   1. Update your LearningService to use LearningModules instead of LearningPath")
    print("   2. Update model relationships to reference learning_modules")
    print("   3. Run the submodule population script (should work now)")
    print("   4. Test that user progress still works correctly")
    print("   5. Consider deprecating learning_paths table in future")
    
    print("\n🔧 Model Updates Needed:")
    print("   - Update foreign key in LearningSubmodules model:")
    print("     module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'))")
    print("   - Update LearningService imports and queries")
    
    print("\n⚠️  Backup Recommendation:")
    print("   - Keep learning_paths table as backup until fully tested")
    print("   - Test all functionality before removing old references")

def main():
    """Main migration function"""
    print("🔄 Learning Paths → Learning Modules Migration")
    print("="*60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Verify setup
            if not verify_migration_setup():
                return 1
            
            print()
            
            # Perform migration
            success, mapping = migrate_learning_paths_to_modules()
            if not success:
                print("❌ Migration failed")
                return 1
            
            print()
            
            # Update user relationships
            if not update_user_learning_paths(mapping):
                print("❌ Failed to update user learning paths")
                return 1
            
            print()
            
            # Update foreign key constraints
            update_foreign_key_constraint()  # Non-critical if fails
            
            print()
            
            # Verify results
            verify_migration_results()
            
            # Show next steps
            show_next_steps()
            
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)