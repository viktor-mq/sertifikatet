"""
Initialize game scenarios
"""
from app import create_app, db
from app.models import GameScenario
import json

def init_game_scenarios():
    """Initialize game scenarios in the database."""
    app = create_app()
    
    with app.app_context():
        # Check if scenarios already exist
        if GameScenario.query.count() > 0:
            print("Game scenarios already exist. Skipping initialization.")
            return
        
        # Define game scenarios
        scenarios = [
            {
                'name': 'Trafikkskiltgjenkjenning',
                'description': 'Test dine kunnskaper om norske trafikkskilt',
                'scenario_type': 'traffic_signs',
                'difficulty_level': 1,
                'max_score': 100,
                'time_limit_seconds': 300,  # 5 minutes
                'template_name': 'traffic_signs',
                'is_active': True,
                'order_index': 1,
                'min_level_required': 1,
                'is_premium': False,
                'config_json': json.dumps({
                    'questions_per_game': 10,
                    'points_per_correct': 10,
                    'time_bonus': True
                })
            },
            {
                'name': 'Hukommelsesspill',
                'description': 'Match trafikkskilt-par og tren hukommelsen din',
                'scenario_type': 'memory',
                'difficulty_level': 2,
                'max_score': 200,
                'time_limit_seconds': 600,  # 10 minutes
                'template_name': 'memory_game',
                'is_active': True,
                'order_index': 2,
                'min_level_required': 1,
                'is_premium': False,
                'config_json': json.dumps({
                    'pairs': 8,
                    'points_per_match': 25,
                    'time_penalty': True
                })
            },
            {
                'name': 'Kjøresimulator',
                'description': 'Øv på trafikksituasjoner i en trygg simulering',
                'scenario_type': 'driving_sim',
                'difficulty_level': 3,
                'max_score': 300,
                'time_limit_seconds': 900,  # 15 minutes
                'template_name': 'driving_simulator',
                'is_active': True,
                'order_index': 3,
                'min_level_required': 5,
                'is_premium': False,
                'config_json': json.dumps({
                    'scenarios': 5,
                    'points_per_scenario': 60,
                    'decision_time_limit': 30
                })
            },
            {
                'name': 'Regelpuslespill',
                'description': 'Løs trafikkrelaterte gåter og lær reglene',
                'scenario_type': 'puzzle',
                'difficulty_level': 2,
                'max_score': 150,
                'time_limit_seconds': 600,  # 10 minutes
                'template_name': 'rule_puzzle',
                'is_active': True,
                'order_index': 4,
                'min_level_required': 3,
                'is_premium': False,
                'config_json': json.dumps({
                    'puzzles_per_game': 10,
                    'points_per_puzzle': 15,
                    'hint_penalty': 5
                })
            },
            {
                'name': 'Tidsutfordring',
                'description': 'Svar på flest mulig spørsmål på kortest tid',
                'scenario_type': 'time_challenge',
                'difficulty_level': 3,
                'max_score': 500,
                'time_limit_seconds': 120,  # 2 minutes
                'template_name': 'time_challenge',
                'is_active': True,
                'order_index': 5,
                'min_level_required': 10,
                'is_premium': False,
                'config_json': json.dumps({
                    'questions': 20,
                    'points_per_correct': 10,
                    'time_bonus_per_second': 1
                })
            },
            {
                'name': 'Flerspiller Duell',
                'description': 'Konkurrer mot andre spillere i sanntid',
                'scenario_type': 'multiplayer',
                'difficulty_level': 2,
                'max_score': 1000,
                'time_limit_seconds': 300,  # 5 minutes
                'template_name': 'multiplayer_lobby',
                'is_active': True,
                'order_index': 6,
                'min_level_required': 5,
                'is_premium': True,
                'config_json': json.dumps({
                    'max_players': 2,
                    'questions_per_round': 10,
                    'points_multiplier': 1.5
                })
            }
        ]
        
        # Add scenarios to database
        for scenario_data in scenarios:
            scenario = GameScenario(**scenario_data)
            db.session.add(scenario)
        
        try:
            db.session.commit()
            print(f"Successfully added {len(scenarios)} game scenarios.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding game scenarios: {e}")

if __name__ == "__main__":
    init_game_scenarios()
