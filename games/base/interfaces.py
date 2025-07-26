# Base Game Interfaces
"""
Abstract base classes and interfaces that all games must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GameResult:
    """Standardized game result structure"""
    score: int
    max_score: int
    completion_time: float  # seconds
    correct_answers: int
    total_questions: int
    xp_earned: int
    achievements_unlocked: List[str]
    performance_data: Dict[str, Any]
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100

class BaseGame(ABC):
    """Abstract base class that all games must inherit from"""
    
    def __init__(self, user_id: int, game_id: str):
        self.user_id = user_id
        self.game_id = game_id
        self.session_id = None
        self.start_time = None
        self.current_score = 0
        self.session_data = {}
    
    @abstractmethod
    def start_session(self) -> Dict[str, Any]:
        """
        Initialize a new game session
        Returns: Initial game state data
        """
        pass
    
    @abstractmethod
    def process_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a game action (answer, move, etc.)
        Args:
            action_type: Type of action ('answer', 'move', 'pause', etc.)
            action_data: Action-specific data
        Returns: Updated game state and feedback
        """
        pass
    
    @abstractmethod
    def calculate_final_score(self) -> int:
        """
        Calculate the final score for the session
        Returns: Final score value
        """
        pass
    
    @abstractmethod
    def complete_session(self) -> GameResult:
        """
        Complete the game session and return results
        Returns: GameResult object with all session data
        """
        pass
    
    @abstractmethod
    def get_game_config(self) -> Dict[str, Any]:
        """
        Get game-specific configuration
        Returns: Configuration dictionary
        """
        pass
    
    # Optional methods with default implementations
    
    def pause_session(self) -> bool:
        """Pause the current session"""
        return True
    
    def resume_session(self) -> bool:
        """Resume a paused session"""
        return True
    
    def get_hint(self) -> Optional[str]:
        """Get a hint for the current question/situation"""
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information"""
        return {
            'score': self.current_score,
            'session_id': self.session_id,
            'elapsed_time': self._get_elapsed_time()
        }
    
    def validate_action(self, action_type: str, action_data: Dict[str, Any]) -> bool:
        """Validate if an action is allowed in current state"""
        return True
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time since session start"""
        if not self.start_time:
            return 0.0
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def _award_xp(self, base_xp: int, performance_multiplier: float = 1.0) -> int:
        """Calculate and award XP based on performance"""
        from games.base.utils import calculate_xp_reward
        return calculate_xp_reward(base_xp, performance_multiplier)
    
    def _trigger_achievements(self, result: GameResult) -> List[str]:
        """Check and trigger any achievements"""
        achievements = []
        
        # Example achievement checks (games can override this)
        if result.accuracy >= 100:
            achievements.append('perfect_score')
        if result.accuracy >= 90:
            achievements.append('high_accuracy')
        if result.completion_time < 60:
            achievements.append('speed_demon')
            
        return achievements

class GameEventHandler(ABC):
    """Interface for handling game events (achievements, XP, etc.)"""
    
    @abstractmethod
    def on_game_start(self, user_id: int, game_id: str, session_id: str):
        """Called when a game session starts"""
        pass
    
    @abstractmethod
    def on_game_complete(self, user_id: int, game_id: str, result: GameResult):
        """Called when a game session completes"""
        pass
    
    @abstractmethod
    def on_achievement_unlock(self, user_id: int, achievement_id: str, game_id: str):
        """Called when an achievement is unlocked"""
        pass
    
    @abstractmethod
    def on_xp_earned(self, user_id: int, xp_amount: int, source: str):
        """Called when XP is earned"""
        pass

class GameAnalytics(ABC):
    """Interface for game analytics tracking"""
    
    @abstractmethod
    def track_game_start(self, user_id: int, game_id: str, session_id: str):
        """Track game session start"""
        pass
    
    @abstractmethod
    def track_game_action(self, user_id: int, game_id: str, action_type: str, action_data: Dict):
        """Track individual game actions"""
        pass
    
    @abstractmethod
    def track_game_complete(self, user_id: int, game_id: str, result: GameResult):
        """Track game completion"""
        pass
    
    @abstractmethod
    def get_game_stats(self, game_id: str, user_id: Optional[int] = None) -> Dict:
        """Get game statistics"""
        pass