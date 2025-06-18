#!/usr/bin/env python3
"""
Initialize the ML system for adaptive learning.
Run this script after setting up the database to initialize ML features.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.ml.service import ml_service
from app.models import User, Question

def initialize_ml_system():
    """Initialize the ML system with basic configuration"""
    app = create_app()
    
    with app.app_context():
        print("🧠 Initializing ML-Powered Adaptive Learning System...")
        
        # Initialize ML service
        try:
            ml_service.initialize()
            print("✅ ML Service initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing ML service: {e}")
            return False
        
        # Check database connectivity
        try:
            user_count = User.query.count()
            question_count = Question.query.count()
            print(f"📊 Database Status:")
            print(f"   - Users: {user_count}")
            print(f"   - Questions: {question_count}")
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
        
        # Get ML status
        ml_status = ml_service.get_ml_status()
        print(f"🤖 ML System Status:")
        print(f"   - ML Enabled: {ml_status.get('ml_enabled', False)}")
        print(f"   - Algorithm Version: {ml_status.get('algorithm_version', 'Unknown')}")
        print(f"   - Skill Profiles: {ml_status.get('skill_profiles', 0)}")
        print(f"   - Question Profiles: {ml_status.get('question_profiles', 0)}")
        
        # List available features
        features = ml_status.get('features_available', [])
        if features:
            print(f"🚀 Available ML Features:")
            for feature in features:
                print(f"   - {feature.replace('_', ' ').title()}")
        
        print("\n🎯 ML System Ready!")
        print("\nNext Steps:")
        print("1. Users can now access AI-powered features at /ml/insights")
        print("2. Adaptive question selection will improve as users complete more quizzes")
        print("3. Check the admin panel for ML system monitoring")
        print("\nML Features:")
        print("- Adaptive Question Selection: Questions chosen based on user skill level")
        print("- Personalized Difficulty: Dynamic difficulty adjustment")
        print("- Learning Insights: AI-powered analysis of learning patterns")
        print("- Weak Area Detection: Automatic identification of topics needing practice")
        print("- Study Recommendations: Personalized study suggestions")
        
        return True

def check_dependencies():
    """Check if required ML dependencies are installed"""
    missing_deps = []
    
    try:
        import numpy
        print("✅ NumPy installed")
    except ImportError:
        missing_deps.append('numpy')
    
    try:
        import pandas
        print("✅ Pandas installed")
    except ImportError:
        missing_deps.append('pandas')
    
    try:
        import sklearn
        print("✅ Scikit-learn installed")
    except ImportError:
        missing_deps.append('scikit-learn')
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install " + ' '.join(missing_deps))
        return False
    
    return True

if __name__ == '__main__':
    print("🧠 ML System Initialization")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before continuing.")
        sys.exit(1)
    
    # Initialize ML system
    if initialize_ml_system():
        print("\n🎉 ML System initialization completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ ML System initialization failed.")
        sys.exit(1)
