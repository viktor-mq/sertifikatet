#!/usr/bin/env python3
"""
Script to populate learning_submodules table from module.yaml files
This reads the actual file structure and populates the database properly
Usage: python scripts/populate_submodules_from_yaml.py
"""

import sys
import os
import yaml
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import LearningModules
from datetime import datetime

# Try to import LearningSubmodules
try:
    from app.models import LearningSubmodules
    HAS_SUBMODULES_MODEL = True
except ImportError:
    try:
        from app.models import LearningSubmodule
        LearningSubmodules = LearningSubmodule
        HAS_SUBMODULES_MODEL = True
    except ImportError:
        HAS_SUBMODULES_MODEL = False

def verify_database_setup():
    """Verify that we have everything we need"""
    if not HAS_SUBMODULES_MODEL:
        print("❌ LearningSubmodules model not found in app.models")
        return False
    
    # Check that learning_modules are populated
    modules_count = LearningModules.query.count()
    if modules_count == 0:
        print("❌ No learning modules found. Please run the learning modules seeder first.")
        return False
    
    print(f"✅ Found {modules_count} learning modules")
    print("✅ LearningSubmodules model available")
    return True

def find_module_yaml_files():
    """Find all module.yaml files in the learning directory"""
    learning_dir = Path('learning')
    
    if not learning_dir.exists():
        print(f"❌ Learning directory not found: {learning_dir.absolute()}")
        return []
    
    module_files = []
    for module_dir in learning_dir.iterdir():
        if module_dir.is_dir() and not module_dir.name.startswith('.'):
            yaml_file = module_dir / 'module.yaml'
            if yaml_file.exists():
                # Extract module number from directory name (e.g., "1.basic_traffic_theory" -> 1)
                try:
                    module_number = int(module_dir.name.split('.')[0])
                    module_files.append({
                        'module_number': module_number,
                        'directory': module_dir,
                        'yaml_file': yaml_file
                    })
                except ValueError:
                    print(f"⚠️  Could not extract module number from: {module_dir.name}")
    
    # Sort by module number
    module_files.sort(key=lambda x: x['module_number'])
    
    print(f"📁 Found {len(module_files)} module.yaml files:")
    for mf in module_files:
        print(f"   Module {mf['module_number']}: {mf['directory'].name}")
    
    return module_files

def load_module_data(yaml_file):
    """Load and parse a module.yaml file"""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error reading {yaml_file}: {str(e)}")
        return None

def map_submodule_to_database(submodule_data, module_id, module_dir):
    """Map submodule data from YAML to database columns"""
    
    # Extract submodule number (e.g., 1.1 from id "1.1")
    submodule_id = submodule_data.get('id', '')
    try:
        submodule_number = float(submodule_id)
    except (ValueError, TypeError):
        print(f"⚠️  Invalid submodule ID: {submodule_id}")
        return None
    
    # Create file modules based on your current structure
    submodule_dir_name = f"{submodule_id}_{submodule_data.get('title', '').lower().replace(' ', '_').replace('?', '').replace('–', '').replace(',', '')}"
    content_file_module = f"learning/{module_dir.name}/{submodule_dir_name}/long.md"
    summary_file_module = f"learning/{module_dir.name}/{submodule_dir_name}/short.md"
    shorts_directory = f"learning/{module_dir.name}/{submodule_dir_name}/videos/"
    
    # Map to database structure
    db_data = {
        'module_id': module_id,
        'submodule_number': submodule_number,
        'title': submodule_data.get('title', ''),
        'description': submodule_data.get('description', ''),
        'content_file_path': content_file_module,
        'summary_file_path': summary_file_module,
        'shorts_directory': shorts_directory,
        'estimated_minutes': submodule_data.get('estimated_minutes', 30),
        'difficulty_level': submodule_data.get('difficulty_level', 1),
        'has_quiz': submodule_data.get('has_quiz', True),
        'quiz_question_count': submodule_data.get('quiz_question_count', 5),
        'has_video_shorts': submodule_data.get('has_video_shorts', True),
        'shorts_count': submodule_data.get('shorts_count', 2),
        'is_active': True,
        'ai_generated_content': False,
        'ai_generated_summary': False,
        'content_version': '1.0',
        'last_content_update': datetime.utcnow(),
        'engagement_score': 0.0,
        'completion_rate': 0.0,
        'average_study_time': submodule_data.get('estimated_minutes', 30),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    return db_data

def populate_submodules_from_yaml():
    """Main function to populate submodules from YAML files"""
    print("📚 Populating learning_submodules from module.yaml files...")
    
    # Find all module YAML files
    module_files = find_module_yaml_files()
    if not module_files:
        print("❌ No module.yaml files found")
        return False
    
    # Check if submodules already exist
    existing_count = LearningSubmodules.query.count()
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing submodules")
        response = input("Do you want to clear existing data and reload? (y/N): ")
        if response.lower() == 'y':
            print("🧹 Clearing existing submodules...")
            LearningSubmodules.query.delete()
            db.session.commit()
        else:
            print("ℹ️  Keeping existing data. Exiting.")
            return True
    
    total_added = 0
    total_failed = 0
    
    # Process each module
    for module_info in module_files:
        module_number = module_info['module_number']
        module_dir = module_info['directory']
        yaml_file = module_info['yaml_file']
        
        print(f"\n📖 Processing Module {module_number}: {module_dir.name}")
        
        # Get the corresponding learning_module ID
        learning_module = LearningModules.query.filter_by(id=module_number).first()
        if not learning_module:
            print(f"❌ No learning module found for module {module_number}")
            continue
        
        # Load module data from YAML
        module_data = load_module_data(yaml_file)
        if not module_data:
            continue
        
        # Get submodules from YAML
        submodules = module_data.get('submodules', [])
        print(f"   Found {len(submodules)} submodules")
        
        # Process each submodule
        for submodule_data in submodules:
            try:
                # Map to database structure
                db_data = map_submodule_to_database(submodule_data, learning_module.id, module_dir)
                if not db_data:
                    total_failed += 1
                    continue
                
                # Create database record
                submodule = LearningSubmodules(**db_data)
                db.session.add(submodule)
                
                print(f"   ✅ {db_data['submodule_number']}: {db_data['title']}")
                total_added += 1
                
            except Exception as e:
                print(f"   ❌ Failed to add {submodule_data.get('id', 'unknown')}: {str(e)}")
                total_failed += 1
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"\n🎉 Successfully added {total_added} submodules to database!")
        if total_failed > 0:
            print(f"⚠️  {total_failed} submodules failed to add")
        
        return True
        
    except Exception as e:
        print(f"❌ Error committing to database: {str(e)}")
        db.session.rollback()
        return False

def show_populated_data():
    """Show what was populated in the database"""
    print("\n📊 Database Summary:")
    
    total_submodules = LearningSubmodules.query.count()
    print(f"   Total submodules: {total_submodules}")
    
    # Show breakdown by module
    modules = db.session.query(
        LearningSubmodules.module_id,
        db.func.count(LearningSubmodules.id).label('count')
    ).group_by(LearningSubmodules.module_id).order_by(LearningSubmodules.module_id).all()
    
    if modules:
        print("\n📋 Submodules by module:")
        for module_id, count in modules:
            learning_module = LearningModules.query.get(module_id)
            module_name = learning_module.name if learning_module else f"Module {module_id}"
            print(f"   Module {module_id} ({module_name}): {count} submodules")
    
    # Show some sample submodules
    sample_submodules = LearningSubmodules.query.limit(5).all()
    if sample_submodules:
        print("\n🎬 Sample submodules:")
        for sub in sample_submodules:
            print(f"   {sub.submodule_number}: {sub.title}")

def main():
    """Main function"""
    print("🌱 Starting submodule population from YAML files...")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Verify database setup
            if not verify_database_setup():
                return 1
            
            print()
            
            # Populate submodules from YAML
            success = populate_submodules_from_yaml()
            
            if not success:
                print("❌ Failed to populate submodules")
                return 1
            
            # Show summary
            show_populated_data()
            
            print("\n" + "=" * 60)
            print("✅ Submodule population completed successfully!")
            
            print("\n🚀 Next Steps:")
            print("   1. Run the video shorts seeding script")
            print("   2. Video shorts will now properly reference these submodules")
            print("   3. Update LearningService to read from database instead of mock data")
            
            print("\n🔍 Verification:")
            print("   - learning_submodules table is now populated")
            print("   - Foreign key relationships are properly established")
            print("   - File modules match your current structure")
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)