from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import game_bp
from ..models import db, GameScenario, GameSession, TrafficSign, User, UserProgress
from ..gamification_models import XPTransaction, UserDailyChallenge, DailyChallenge
from datetime import datetime
import json
import random

@game_bp.route('/')
@login_required
def index():
    """Show the main games page with all available games."""
    # Get user's game statistics
    user_progress = current_user.progress
    
    # Get available game scenarios
    scenarios = GameScenario.query.filter_by(is_active=True).order_by(GameScenario.order_index).all()
    
    # Get user's recent game sessions
    recent_sessions = GameSession.query.filter_by(user_id=current_user.id)\
        .order_by(GameSession.started_at.desc()).limit(5).all()
    
    # Calculate user's game stats
    total_games = GameSession.query.filter_by(user_id=current_user.id).count()
    games_won = GameSession.query.filter_by(user_id=current_user.id, completed=True).count()
    
    return render_template('game/index.html',
                         user_progress=user_progress,
                         scenarios=scenarios,
                         recent_sessions=recent_sessions,
                         total_games=total_games,
                         games_won=games_won)

@game_bp.route('/traffic-signs')
@login_required
def traffic_signs():
    """Traffic sign recognition game."""
    return render_template('game/traffic_signs.html')

@game_bp.route('/driving-simulator')
@login_required
def driving_simulator():
    """Driving simulation game."""
    return render_template('game/driving_simulator.html')

@game_bp.route('/memory-game')
@login_required
def memory_game():
    """Memory matching game with traffic signs."""
    return render_template('game/memory_game.html')

@game_bp.route('/rule-puzzle')
@login_required
def rule_puzzle():
    """Rule-based puzzle game - redirect to new modular system."""
    return redirect(url_for('rule_puzzle.play'))

@game_bp.route('/time-challenge')
@login_required
def time_challenge():
    """Time-based challenge game."""
    return render_template('game/time_challenge.html')

@game_bp.route('/multiplayer-lobby')
@login_required
def multiplayer_lobby():
    """Multiplayer game lobby."""
    # Check if user has premium subscription for multiplayer
    if current_user.subscription_tier == 'free':
        flash('Flerspiller er kun tilgjengelig for premium-brukere.', 'warning')
        return redirect(url_for('game.index'))
    
    return render_template('game/multiplayer_lobby.html')

@game_bp.route('/play/<int:scenario_id>')
@login_required
def play(scenario_id):
    """Play a specific game scenario."""
    scenario = GameScenario.query.get_or_404(scenario_id)
    
    # Create a new game session
    game_session = GameSession(
        user_id=current_user.id,
        scenario_id=scenario_id,
        started_at=datetime.utcnow()
    )
    db.session.add(game_session)
    db.session.commit()
    
    return render_template(f'game/{scenario.template_name}.html',
                         scenario=scenario,
                         session_id=game_session.id)

@game_bp.route('/complete/<int:session_id>', methods=['POST'])
@login_required
def complete_game(session_id):
    """Complete a game session and save results."""
    game_session = GameSession.query.get_or_404(session_id)
    
    if game_session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get game data from request
    data = request.get_json()
    score = data.get('score', 0)
    mistakes = data.get('mistakes', 0)
    time_played = data.get('time_played', 0)
    
    # Update game session
    game_session.score = score
    game_session.mistakes_count = mistakes
    game_session.time_played_seconds = time_played
    game_session.completed = True
    game_session.completed_at = datetime.utcnow()
    
    # Update user progress
    user_progress = current_user.progress
    user_progress.total_game_sessions += 1
    user_progress.total_game_score += score
    
    # Award XP based on performance
    xp_earned = calculate_game_xp(score, mistakes, time_played, game_session.scenario)
    if xp_earned > 0:
        current_user.total_xp += xp_earned
        xp_transaction = XPTransaction(
            user_id=current_user.id,
            amount=xp_earned,
            transaction_type='game',
            description=f'Fullført {game_session.scenario.name}'
        )
        db.session.add(xp_transaction)
    
    # Check for daily challenges
    check_game_challenges(current_user, game_session)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'xp_earned': xp_earned,
        'total_xp': current_user.total_xp,
        'score': score
    })

def calculate_game_xp(score, mistakes, time_played, scenario):
    """Calculate XP earned from a game session."""
    base_xp = 50  # Base XP for completing a game
    
    # Bonus for high score
    if score >= scenario.max_score * 0.9:
        base_xp += 30
    elif score >= scenario.max_score * 0.7:
        base_xp += 20
    elif score >= scenario.max_score * 0.5:
        base_xp += 10
    
    # Bonus for no mistakes
    if mistakes == 0:
        base_xp += 25
    
    # Time bonus (if completed under time limit)
    if scenario.time_limit_seconds and time_played < scenario.time_limit_seconds:
        time_bonus = int((scenario.time_limit_seconds - time_played) / scenario.time_limit_seconds * 20)
        base_xp += time_bonus
    
    return base_xp

def check_game_challenges(user, game_session):
    """Check if user completed any game-related challenges."""
    # Get active daily challenges for the user
    from datetime import date
    today = date.today()
    
    active_challenges = UserDailyChallenge.query.join(DailyChallenge).filter(
        UserDailyChallenge.user_id == user.id,
        UserDailyChallenge.completed == False,
        DailyChallenge.date == today,
        DailyChallenge.challenge_type.in_(['quiz', 'streak', 'perfect_score'])
    ).all()
    
    for user_challenge in active_challenges:
        challenge = user_challenge.challenge
        
        # Check different challenge types
        if challenge.challenge_type == 'perfect_score' and game_session.mistakes_count == 0:
            user_challenge.progress += 1
            if user_challenge.progress >= challenge.requirement_value:
                user_challenge.completed = True
                user_challenge.completed_at = datetime.utcnow()
                user_challenge.xp_earned = challenge.xp_reward
                
                # Award XP
                user.total_xp += challenge.xp_reward
                xp_transaction = XPTransaction(
                    user_id=user.id,
                    amount=challenge.xp_reward,
                    transaction_type='daily_challenge',
                    description=f'Fullført utfordring: {challenge.title}'
                )
                db.session.add(xp_transaction)
        
        elif challenge.challenge_type == 'quiz' and challenge.category == 'game':
            # For game-related quiz challenges, increment progress
            user_challenge.progress += 1
            if user_challenge.progress >= challenge.requirement_value:
                user_challenge.completed = True
                user_challenge.completed_at = datetime.utcnow()
                user_challenge.xp_earned = challenge.xp_reward
                
                # Award XP
                user.total_xp += challenge.xp_reward
                xp_transaction = XPTransaction(
                    user_id=user.id,
                    amount=challenge.xp_reward,
                    transaction_type='daily_challenge',
                    description=f'Fullført utfordring: {challenge.title}'
                )
                db.session.add(xp_transaction)

@game_bp.route('/leaderboard/<game_type>')
@login_required
def game_leaderboard(game_type):
    """Show leaderboard for a specific game type."""
    # Get top players for this game type
    scenario = GameScenario.query.filter_by(scenario_type=game_type).first_or_404()
    
    top_scores = db.session.query(
        User.username,
        User.profile_picture,
        db.func.max(GameSession.score).label('high_score'),
        db.func.count(GameSession.id).label('games_played')
    ).join(GameSession).filter(
        GameSession.scenario_id == scenario.id,
        GameSession.completed == True
    ).group_by(User.id).order_by(db.func.max(GameSession.score).desc()).limit(20).all()
    
    # Get current user's rank
    user_score = GameSession.query.filter_by(
        user_id=current_user.id,
        scenario_id=scenario.id,
        completed=True
    ).order_by(GameSession.score.desc()).first()
    
    return render_template('game/leaderboard.html',
                         scenario=scenario,
                         top_scores=top_scores,
                         user_score=user_score)
