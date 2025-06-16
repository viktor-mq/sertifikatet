#!/usr/bin/env python3
"""
Test script to verify the game scenario model fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import GameScenario

def test_game_scenarios():
    """Test that GameScenario queries work without template_name column."""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to query all scenarios (this was failing before)
            scenarios = GameScenario.query.filter_by(is_active=True).order_by(GameScenario.order_index).all()
            print(f"✓ Successfully queried {len(scenarios)} game scenarios")
            
            # Test the template_name property
            if scenarios:
                for scenario in scenarios:
                    print(f"  - {scenario.name}: type='{scenario.scenario_type}' -> template='{scenario.template_name}'")
            else:
                print("  No scenarios found in database")
                
                # Let's try to create a test scenario to verify the model works
                test_scenario = GameScenario(
                    name="Test Traffic Signs",
                    description="Test scenario",
                    scenario_type="traffic_signs",
                    difficulty_level=1,
                    max_score=100,
                    is_active=True,
                    order_index=1
                )
                
                db.session.add(test_scenario)
                db.session.commit()
                
                print(f"✓ Created test scenario: {test_scenario.name}")
                print(f"  Template name: {test_scenario.template_name}")
                
                # Clean up
                db.session.delete(test_scenario)
                db.session.commit()
                print("✓ Cleaned up test scenario")
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
            
        return True

if __name__ == '__main__':
    success = test_game_scenarios()
    if success:
        print("\n✓ Game scenario fix appears to be working!")
        print("You should now be able to access /game without the template_name error.")
    else:
        print("\n✗ There are still issues with the game scenarios.")
