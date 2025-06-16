#!/usr/bin/env python3
"""
Script to initialize game scenarios in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models import GameScenario

def create_test_scenarios():
    """Create some test game scenarios."""
    app = create_app()
    
    with app.app_context():
        # Check if scenarios already exist
        existing_count = GameScenario.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} game scenarios. Skipping creation.")
            return
        
        scenarios = [
            {
                'name': 'Traffic Sign Recognition',
                'description': 'Test your knowledge of Norwegian traffic signs',
                'scenario_type': 'traffic_signs',
                'difficulty_level': 1,
                'max_score': 100,
                'time_limit_seconds': 300,
                'config_json': '{"signs_count": 20, "time_per_sign": 15}',
                'is_active': True,
                'order_index': 1,
                'min_level_required': 1,
                'is_premium': False
            },
            {
                'name': 'Driving Simulator',
                'description': 'Practice driving scenarios in a virtual environment',
                'scenario_type': 'driving_sim',
                'difficulty_level': 2,
                'max_score': 200,
                'time_limit_seconds': 600,
                'config_json': '{"scenarios": ["city_driving", "highway", "parking"]}',
                'is_active': True,
                'order_index': 2,
                'min_level_required': 3,
                'is_premium': False
            },
            {
                'name': 'Memory Game',
                'description': 'Match traffic signs and rules to improve your memory',
                'scenario_type': 'memory',
                'difficulty_level': 1,
                'max_score': 150,
                'time_limit_seconds': 240,
                'config_json': '{"pairs_count": 12, "reveal_time": 2}',
                'is_active': True,
                'order_index': 3,
                'min_level_required': 1,
                'is_premium': False
            },
            {
                'name': 'Rule Puzzle',
                'description': 'Solve traffic rule puzzles and scenarios',
                'scenario_type': 'puzzle',
                'difficulty_level': 3,
                'max_score': 180,
                'time_limit_seconds': 450,
                'config_json': '{"puzzle_count": 15, "difficulty": "medium"}',
                'is_active': True,
                'order_index': 4,
                'min_level_required': 5,
                'is_premium': False
            },
            {
                'name': 'Time Challenge',
                'description': 'Answer as many questions as possible in limited time',
                'scenario_type': 'time_challenge',
                'difficulty_level': 2,
                'max_score': 250,
                'time_limit_seconds': 180,
                'config_json': '{"question_count": 50, "time_pressure": true}',
                'is_active': True,
                'order_index': 5,
                'min_level_required': 2,
                'is_premium': False
            }
        ]
        
        for scenario_data in scenarios:
            scenario = GameScenario(**scenario_data)
            db.session.add(scenario)
        
        try:
            db.session.commit()
            print(f"Successfully created {len(scenarios)} game scenarios!")
            
            # List created scenarios
            print("\nCreated scenarios:")
            for scenario in GameScenario.query.all():
                print(f"- {scenario.name} ({scenario.scenario_type}) - Template: {scenario.template_name}")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating scenarios: {e}")

if __name__ == '__main__':
    create_test_scenarios()
