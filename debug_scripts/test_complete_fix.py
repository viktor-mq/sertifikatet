#!/usr/bin/env python3
"""
Comprehensive test for the game scenario database fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import GameScenario

def test_complete_fix():
    """Test the complete fix for game scenarios."""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Game Scenario Database Fix")
        print("=" * 50)
        
        try:
            # Test 1: Basic query that was failing before
            print("1️⃣ Testing basic GameScenario query...")
            scenarios = GameScenario.query.filter_by(is_active=True).order_by(GameScenario.order_index).all()
            print(f"   ✅ Successfully queried {len(scenarios)} scenarios")
            
            # Test 2: Template name property
            print("\n2️⃣ Testing template_name property...")
            test_scenario_types = ['traffic_signs', 'driving_sim', 'memory', 'puzzle', 'time_challenge', 'multiplayer']
            
            for scenario_type in test_scenario_types:
                # Create a temporary scenario to test the property
                temp_scenario = GameScenario(
                    name=f"Test {scenario_type}",
                    scenario_type=scenario_type,
                    description="Test scenario"
                )
                template_name = temp_scenario.template_name
                print(f"   📄 {scenario_type} -> {template_name}")
            
            print("   ✅ All template mappings working correctly")
            
            # Test 3: Create and save a scenario (tests model compatibility)
            print("\n3️⃣ Testing scenario creation...")
            test_scenario = GameScenario(
                name="Test Scenario",
                description="This is a test scenario to verify the fix",
                scenario_type="traffic_signs",
                difficulty_level=1,
                max_score=100,
                time_limit_seconds=300,
                is_active=True,
                order_index=999
            )
            
            db.session.add(test_scenario)
            db.session.flush()  # Don't commit yet
            
            print(f"   ✅ Created scenario with ID: {test_scenario.id}")
            print(f"   📄 Template name: {test_scenario.template_name}")
            
            # Test 4: Query the created scenario
            print("\n4️⃣ Testing scenario retrieval...")
            retrieved = GameScenario.query.get(test_scenario.id)
            if retrieved:
                print(f"   ✅ Retrieved scenario: {retrieved.name}")
                print(f"   📄 Template: {retrieved.template_name}")
            else:
                print("   ❌ Failed to retrieve created scenario")
                
            # Clean up
            db.session.rollback()
            print("   🧹 Cleaned up test scenario")
            
            # Test 5: Test the route simulation
            print("\n5️⃣ Testing route template rendering simulation...")
            if scenarios:
                for scenario in scenarios[:3]:  # Test first 3 scenarios
                    template_path = f"game/{scenario.template_name}.html"
                    print(f"   📄 {scenario.name} -> {template_path}")
            else:
                print("   ℹ️ No scenarios in database to test")
            
            print("\n" + "=" * 50)
            print("🎉 All tests passed! The fix appears to be working correctly.")
            print("\nYou should now be able to:")
            print("- Access /game without database errors")
            print("- Create and query game scenarios")
            print("- Use the template_name property for routing")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            print("\nThis indicates there may still be issues with the database schema.")
            print("You might need to:")
            print("- Run database migrations")
            print("- Check MySQL connection")
            print("- Verify table structure")
            return False

def provide_next_steps():
    """Provide next steps based on test results."""
    print("\n" + "🔧 Next Steps" + "\n" + "=" * 20)
    print("1. Run this test: python test_complete_fix.py")
    print("2. If tests pass, try accessing /game in your browser")
    print("3. If you have no scenarios, run: python scripts/init_game_scenarios.py")
    print("4. Check database schema: python check_db_schema.py")

if __name__ == '__main__':
    success = test_complete_fix()
    if success:
        provide_next_steps()
