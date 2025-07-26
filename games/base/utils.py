# Base Game Utilities
"""
Shared utilities and helper functions for all games
"""

import math
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import current_app

class GameRegistry:
    """Registry for managing available games"""
    
    def __init__(self):
        self.registered_games = {}
        self.game_instances = {}
    
    def register_game(self, game_id: str, game_info: Dict):
        """Register a game in the system"""
        self.registered_games[game_id] = game_info
    
    def get_registered_games(self) -> Dict:
        """Get all registered games"""
        return self.registered_games
    
    def get_game_info(self, game_id: str) -> Optional[Dict]:
        """Get info for a specific game"""
        return self.registered_games.get(game_id)
    
    def is_game_available(self, game_id: str) -> bool:
        """Check if a game is available"""
        return game_id in self.registered_games
    
    def get_all_games(self) -> Dict:
        """Get all games with their info"""
        return self.registered_games

def calculate_xp_reward(base_xp: int, performance_multiplier: float = 1.0, 
                       time_bonus: float = 0.0, streak_multiplier: float = 1.0) -> int:
    """
    Calculate XP reward based on performance
    
    Args:
        base_xp: Base XP for the game
        performance_multiplier: Multiplier based on score/accuracy (0.0-2.0)
        time_bonus: Bonus for completing quickly (0.0-1.0)
        streak_multiplier: Multiplier for consecutive plays (1.0-3.0)
    
    Returns:
        Final XP amount
    """
    # Ensure multipliers are within reasonable bounds
    performance_multiplier = max(0.1, min(3.0, performance_multiplier))
    time_bonus = max(0.0, min(1.0, time_bonus))
    streak_multiplier = max(1.0, min(5.0, streak_multiplier))
    
    # Calculate final XP
    xp = base_xp * performance_multiplier * streak_multiplier + (base_xp * time_bonus)
    
    return int(math.ceil(xp))

def calculate_performance_multiplier(score: int, max_score: int, 
                                   accuracy: float, completion_time: float,
                                   target_time: float = 300.0) -> float:
    """
    Calculate performance multiplier based on various factors
    
    Args:
        score: Player's score
        max_score: Maximum possible score
        accuracy: Accuracy percentage (0-100)
        completion_time: Time taken in seconds
        target_time: Target completion time in seconds
    
    Returns:
        Performance multiplier (0.1-3.0)
    """
    # Score component (0.0-1.0)
    score_ratio = score / max_score if max_score > 0 else 0
    
    # Accuracy component (0.0-1.0)
    accuracy_ratio = accuracy / 100.0
    
    # Time component (0.5-1.5)
    time_ratio = min(1.5, max(0.5, target_time / completion_time))
    
    # Combine factors
    multiplier = (score_ratio * 0.4 + accuracy_ratio * 0.4 + (time_ratio - 0.5) * 0.2) * 2.0
    
    return max(0.1, min(3.0, multiplier))

def get_global_leaderboard(limit: int = 50, game_id: Optional[str] = None) -> List[Dict]:
    """
    Get global leaderboard across all games or for a specific game
    
    Args:
        limit: Maximum number of entries to return
        game_id: Optional game ID to filter by
    
    Returns:
        List of leaderboard entries
    """
    try:
        from app.models import User, GameSession
        from app import db
        
        query = db.session.query(
            User.id,
            User.username,
            User.profile_picture,
            db.func.sum(GameSession.score).label('total_score'),
            db.func.count(GameSession.id).label('games_played'),
            db.func.avg(GameSession.score).label('avg_score'),
            db.func.max(GameSession.score).label('best_score')
        ).join(GameSession).filter(GameSession.completed == True)
        
        if game_id:
            # Filter by specific game
            from app.models import GameScenario
            scenario = GameScenario.query.filter_by(scenario_type=game_id).first()
            if scenario:
                query = query.filter(GameSession.scenario_id == scenario.id)
        
        leaderboard = query.group_by(User.id).order_by(
            db.func.sum(GameSession.score).desc()
        ).limit(limit).all()
        
        return [
            {
                'rank': idx + 1,
                'user_id': entry.id,
                'username': entry.username,
                'profile_picture': entry.profile_picture,
                'total_score': entry.total_score or 0,
                'games_played': entry.games_played or 0,
                'avg_score': round(entry.avg_score or 0, 1),
                'best_score': entry.best_score or 0
            }
            for idx, entry in enumerate(leaderboard)
        ]
        
    except Exception as e:
        current_app.logger.error(f"Error getting global leaderboard: {e}")
        return []

def get_user_game_stats(user_id: int, game_id: Optional[str] = None) -> Dict:
    """
    Get comprehensive game statistics for a user
    
    Args:
        user_id: User ID
        game_id: Optional game ID to filter by
    
    Returns:
        Dictionary with user's game statistics
    """
    try:
        from app.models import User, GameSession, GameScenario
        from app import db
        
        query = GameSession.query.filter_by(user_id=user_id, completed=True)
        
        if game_id:
            scenario = GameScenario.query.filter_by(scenario_type=game_id).first()
            if scenario:
                query = query.filter_by(scenario_id=scenario.id)
        
        sessions = query.all()
        
        if not sessions:
            return {
                'total_games': 0,
                'total_score': 0,
                'avg_score': 0,
                'best_score': 0,
                'total_time_played': 0,
                'avg_completion_time': 0,
                'games_this_week': 0,
                'current_streak': 0
            }
        
        # Calculate statistics
        total_games = len(sessions)
        total_score = sum(s.score for s in sessions)
        avg_score = total_score / total_games
        best_score = max(s.score for s in sessions)
        
        # Time statistics (if available)
        completion_times = [s.completion_time for s in sessions if s.completion_time]
        total_time_played = sum(completion_times)
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        games_this_week = len([s for s in sessions if s.created_at >= week_ago])
        
        # Calculate current streak
        current_streak = calculate_user_streak(user_id, game_id)
        
        return {
            'total_games': total_games,
            'total_score': total_score,
            'avg_score': round(avg_score, 1),
            'best_score': best_score,
            'total_time_played': total_time_played,
            'avg_completion_time': round(avg_completion_time, 1),
            'games_this_week': games_this_week,
            'current_streak': current_streak
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting user game stats: {e}")
        return {}

def calculate_user_streak(user_id: int, game_id: Optional[str] = None) -> int:
    """
    Calculate user's current playing streak
    
    Args:
        user_id: User ID
        game_id: Optional game ID to filter by
    
    Returns:
        Current streak count
    """
    try:
        from app.models import GameSession, GameScenario
        from app import db
        
        # Get recent sessions ordered by date
        query = GameSession.query.filter_by(user_id=user_id, completed=True)
        
        if game_id:
            scenario = GameScenario.query.filter_by(scenario_type=game_id).first()
            if scenario:
                query = query.filter_by(scenario_id=scenario.id)
        
        sessions = query.order_by(GameSession.created_at.desc()).limit(30).all()
        
        if not sessions:
            return 0
        
        # Calculate streak (consecutive days with at least one game)
        streak = 0
        current_date = datetime.utcnow().date()
        
        # Group sessions by date
        session_dates = set()
        for session in sessions:
            session_dates.add(session.created_at.date())
        
        # Count consecutive days
        check_date = current_date
        while check_date in session_dates:
            streak += 1
            check_date -= timedelta(days=1)
        
        return streak
        
    except Exception as e:
        current_app.logger.error(f"Error calculating user streak: {e}")
        return 0

def format_game_time(seconds: float) -> str:
    """Format game time in a human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def validate_game_session(user_id: int, session_id: str, game_id: str) -> bool:
    """
    Validate that a game session belongs to the user and is active
    
    Args:
        user_id: User ID
        session_id: Session ID
        game_id: Game ID
    
    Returns:
        True if session is valid
    """
    try:
        from app.models import GameSession, GameScenario
        
        scenario = GameScenario.query.filter_by(scenario_type=game_id).first()
        if not scenario:
            return False
        
        session = GameSession.query.filter_by(
            id=session_id,
            user_id=user_id,
            scenario_id=scenario.id
        ).first()
        
        return session is not None
        
    except Exception as e:
        current_app.logger.error(f"Error validating game session: {e}")
        return False

# Game-specific utility functions
def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())

def sanitize_game_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize game data for storage"""
    # Remove any sensitive or unnecessary data
    sanitized = {}
    allowed_keys = [
        'score', 'answers', 'completion_time', 'difficulty',
        'questions_answered', 'correct_answers', 'hints_used'
    ]
    
    for key, value in data.items():
        if key in allowed_keys:
            sanitized[key] = value
    
    return sanitized