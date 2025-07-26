# Rule Puzzle Game Routes
"""
Flask routes for the traffic scenario puzzle game
"""

from flask import Blueprint, request, jsonify, render_template, session
from flask_login import login_required, current_user
from .game_logic import RulePuzzleGame
from .config import GAME_CONFIG
from games.base.utils import GameRegistry
import logging
import json

logger = logging.getLogger(__name__)

# Create blueprint with template folder
bp = Blueprint('rule_puzzle', __name__, 
               template_folder='templates',
               static_folder='static')

# Store active game sessions
active_sessions = {}


@bp.route('/play')
@login_required
def play():
    """Main game page"""
    try:
        # Get vehicle types and scenarios from database
        from app.models import GameScenario
        from .config import VEHICLE_TYPES  # Keep vehicle types in config for now
        
        scenarios = GameScenario.query.filter_by(
            scenario_type='rule_puzzle',
            is_active=True
        ).all()
        
        scenarios_data = []
        for scenario in scenarios:
            try:
                config = json.loads(scenario.config_json) if scenario.config_json else {}
            except:
                config = {}
            
            scenarios_data.append({
                'id': scenario.id,
                'name': scenario.name,
                'description': scenario.description,
                'difficulty': scenario.difficulty_level,
                'max_score': scenario.max_score,
                'time_limit': scenario.time_limit_seconds,
                'config': config
            })
        
        return render_template('game.html',
                             game_config=GAME_CONFIG,
                             scenarios=scenarios_data,
                             vehicles=VEHICLE_TYPES)
    except Exception as e:
        logger.error(f"Error loading rule puzzle game: {e}")
        return jsonify({'error': 'Failed to load game'}), 500


@bp.route('/api/start', methods=['POST'])
@login_required
def start_game():
    """Start a new game session"""
    try:
        data = request.get_json() or {}
        difficulty = data.get('difficulty', 'medium')
        
        # Create new game instance
        game = RulePuzzleGame(current_user.id)
        game.difficulty = difficulty
        
        # Start session
        session_data = game.start_session()
        
        # Store in active sessions
        active_sessions[session_data['session_id']] = game
        
        logger.info(f"Started rule puzzle session {session_data['session_id']} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'session_data': session_data
        })
        
    except Exception as e:
        logger.error(f"Error starting rule puzzle game: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/action', methods=['POST'])
@login_required
def process_action():
    """Process game actions"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        action_type = data.get('action_type')
        action_data = data.get('action_data', {})
        
        if not session_id or not action_type:
            return jsonify({'success': False, 'error': 'Missing session_id or action_type'}), 400
        
        # Get game session
        game = active_sessions.get(session_id)
        if not game:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Validate user ownership
        if game.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Validate action
        if not game.validate_action(action_type, action_data):
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        # Process action
        result = game.process_action(action_type, action_data)
        
        logger.debug(f"Processed action {action_type} for session {session_id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing rule puzzle action: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/complete', methods=['POST'])
@login_required
def complete_game():
    """Complete game session and get results"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Missing session_id'}), 400
        
        # Get game session
        game = active_sessions.get(session_id)
        if not game:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Validate user ownership
        if game.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Complete session
        result = game.complete_session()
        
        # Save to database
        try:
            _save_game_session(game, result)
        except Exception as e:
            logger.error(f"Error saving game session: {e}")
            # Continue even if saving fails
        
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        logger.info(f"Completed rule puzzle session {session_id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'result': {
                'score': result.score,
                'max_score': result.max_score,
                'completion_time': result.completion_time,
                'accuracy': result.accuracy,
                'xp_earned': result.xp_earned,
                'achievements_unlocked': result.achievements_unlocked,
                'performance_data': result.performance_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error completing rule puzzle game: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/abandon', methods=['POST'])
@login_required
def abandon_game():
    """Abandon current game session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Missing session_id'}), 400
        
        # Remove session
        if session_id in active_sessions:
            game = active_sessions[session_id]
            if game.user_id == current_user.id:
                del active_sessions[session_id]
                logger.info(f"Abandoned rule puzzle session {session_id} for user {current_user.id}")
            else:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error abandoning rule puzzle game: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/leaderboard')
@login_required
def leaderboard():
    """Game-specific leaderboard"""
    try:
        from games.base.utils import get_global_leaderboard
        
        leaderboard_data = get_global_leaderboard(limit=20, game_id='rule_puzzle')
        
        return render_template('leaderboard.html',
                             leaderboard=leaderboard_data,
                             game_name="Trafikk Scenario Puslespill")
    except Exception as e:
        logger.error(f"Error loading rule puzzle leaderboard: {e}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500


@bp.route('/api/stats')
@login_required
def get_stats():
    """Get user statistics for this game"""
    try:
        from games.base.utils import get_user_game_stats
        
        stats = get_user_game_stats(current_user.id, 'rule_puzzle')
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting rule puzzle stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _save_game_session(game: RulePuzzleGame, result) -> None:
    """Save game session to database"""
    try:
        from app import db
        from app.models import GameSession, GameScenario
        
        # Get or create game scenario
        scenario = GameScenario.query.filter_by(scenario_type='rule_puzzle').first()
        if not scenario:
            scenario = GameScenario(
                name='Trafikk Scenario Puslespill',
                description='Interaktive trafikk scenario puzzles',
                scenario_type='rule_puzzle',
                difficulty_level=1 if game.difficulty == 'easy' else 2 if game.difficulty == 'medium' else 3,
                max_score=GAME_CONFIG['max_score'],
                time_limit_seconds=GAME_CONFIG['time_limit'],
                config_json='{}',
                template_name='rule_puzzle',
                is_active=True
            )
            db.session.add(scenario)
            db.session.flush()
        
        # Create game session record
        session_record = GameSession(
            user_id=game.user_id,
            scenario_id=scenario.id,
            score=result.score,
            time_played_seconds=int(result.completion_time),
            mistakes_count=getattr(result, 'mistakes_count', 0),
            completed=True,
            started_at=game.start_time,
            completed_at=game.start_time  # Will be updated by the model
        )
        
        db.session.add(session_record)
        db.session.commit()
        
        logger.info(f"Saved rule puzzle session to database for user {game.user_id}")
        
    except Exception as e:
        logger.error(f"Error saving rule puzzle session to database: {e}")
        db.session.rollback()
        raise


# Health check endpoint
@bp.route('/health')
def health_check():
    """Health check for the rule puzzle game"""
    return jsonify({
        'status': 'healthy',
        'game': 'rule_puzzle',
        'active_sessions': len(active_sessions)
    })


# Game configuration endpoint
@bp.route('/api/config')
def get_config():
    """Get game configuration"""
    return jsonify({
        'success': True,
        'config': GAME_CONFIG,
        'scenarios': SCENARIO_TYPES,
        'vehicles': VEHICLE_TYPES
    })