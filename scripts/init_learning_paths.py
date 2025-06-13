# scripts/init_learning_paths.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.services.learning_service import LearningService

def init_learning_paths():
    """Initialize default learning paths in the database."""
    app = create_app()
    
    with app.app_context():
        print("Creating default learning paths...")
        created_paths = LearningService.create_default_learning_paths()
        
        if created_paths:
            print(f"Successfully created {len(created_paths)} learning paths:")
            for path in created_paths:
                print(f"  - {path.name} (Level {path.difficulty_level})")
        else:
            print("Learning paths already exist or no new paths created.")
        
        print("\nDone!")

if __name__ == "__main__":
    init_learning_paths()
