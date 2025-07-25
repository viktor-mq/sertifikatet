# Base Game Components
"""
Shared components and interfaces for all mini-games
"""

from .interfaces import BaseGame, GameResult
from .models import GameSession, GameScore
from .utils import GameRegistry, calculate_xp_reward, get_global_leaderboard

__all__ = [
    'BaseGame',
    'GameResult', 
    'GameSession',
    'GameScore',
    'GameRegistry',
    'calculate_xp_reward',
    'get_global_leaderboard'
]