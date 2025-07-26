# Games Module - Central Registry and Integration Point
"""
Sertifikatet Mini-Games System
Modular game architecture with shared interfaces and connection points
"""

import importlib
from flask import Blueprint
from typing import Dict, List, Optional

# Game Registry - Add new games here
AVAILABLE_GAMES = {
    'traffic_signs': {
        'module': 'games.traffic_signs',
        'name': 'Trafikkskiltgjenkjenning',
        'description': 'Gjenkjenn norske trafikkskilt',
        'icon': 'fas fa-road',
        'difficulty': 'Lett',
        'estimated_time': '5-10 min',
        'status': 'active',
        'priority': 1
    },
    'rule_puzzle': {
        'module': 'games.rule_puzzle',
        'name': 'Trafikk Scenario Puslespill',
        'description': 'Løs trafikksituasjoner ved å plassere kjøretøy riktig',
        'icon': 'fas fa-puzzle-piece',
        'difficulty': 'Middels',
        'estimated_time': '5-10 min',
        'status': 'active',
        'priority': 2
    },
    'violation_spotter': {
        'module': 'games.violation_spotter',
        'name': 'Feilfinner',
        'description': 'Finn regelbrudd i animerte trafikksituasjoner',
        'icon': 'fas fa-search',
        'difficulty': 'Middels',
        'estimated_time': '3-5 min',
        'status': 'development',
        'priority': 3
    },
    'driving_simulator': {
        'module': 'games.driving_simulator',
        'name': 'Kjøresimulator',
        'description': 'Øv på trafikksituasjoner',
        'icon': 'fas fa-car',
        'difficulty': 'Vanskelig',
        'estimated_time': '5-10 min',
        'status': 'planned',
        'priority': 5
    },
    'multiplayer': {
        'module': 'games.multiplayer',
        'name': 'Flerspiller',
        'description': 'Konkurrer mot andre',
        'icon': 'fas fa-users',
        'difficulty': 'Variabel',
        'estimated_time': '3-15 min',
        'status': 'planned',
        'priority': 6
    }
}

def get_available_games(status_filter: Optional[str] = None) -> Dict:
    """Get available games, optionally filtered by status"""
    if status_filter:
        return {k: v for k, v in AVAILABLE_GAMES.items() if v['status'] == status_filter}
    return AVAILABLE_GAMES

def get_active_games() -> Dict:
    """Get only active/ready games"""
    return get_available_games('active')

def get_game_info(game_id: str) -> Optional[Dict]:
    """Get information about a specific game"""
    return AVAILABLE_GAMES.get(game_id)

def register_all_games(app):
    """Register all available games with the Flask app"""
    from games.base.utils import GameRegistry
    
    registry = GameRegistry()
    
    for game_id, game_info in AVAILABLE_GAMES.items():
        try:
            # Only register active games
            if game_info['status'] == 'active':
                module_path = game_info['module']
                game_module = importlib.import_module(f"{module_path}.routes")
                
                # Register the blueprint
                blueprint = getattr(game_module, 'bp', None)
                if blueprint:
                    app.register_blueprint(blueprint, url_prefix=f'/games/{game_id}')
                    registry.register_game(game_id, game_info)
                    print(f"✅ Registered game: {game_info['name']} at /games/{game_id}")
                else:
                    print(f"⚠️  No blueprint found for game: {game_id}")
            else:
                print(f"⏸️  Skipped {game_id} (status: {game_info['status']})")
                
        except ImportError as e:
            print(f"❌ Failed to import game {game_id}: {e}")
        except Exception as e:
            print(f"❌ Error registering game {game_id}: {e}")
    
    # Store registry in app context
    app.game_registry = registry
    print(f"🎮 Games system initialized with {len(registry.get_registered_games())} active games")

def create_games_blueprint():
    """Create main games blueprint for shared routes"""
    games_bp = Blueprint('games', __name__, url_prefix='/games',
                        template_folder='../templates')
    
    @games_bp.route('/')
    def index():
        """Games overview page"""
        from flask import render_template, current_app
        
        # Get game registry from app context
        registry = getattr(current_app, 'game_registry', None)
        if not registry:
            games = get_available_games()
        else:
            games = registry.get_all_games()
            
        return render_template('games/index.html', games=games)
    
    @games_bp.route('/leaderboard')
    def global_leaderboard():
        """Global leaderboard across all games"""
        from flask import render_template
        from games.base.utils import get_global_leaderboard
        
        leaderboard = get_global_leaderboard()
        return render_template('games/global_leaderboard.html', leaderboard=leaderboard)
    
    return games_bp

# Export main components
__all__ = [
    'AVAILABLE_GAMES',
    'get_available_games',
    'get_active_games', 
    'get_game_info',
    'register_all_games',
    'create_games_blueprint'
]