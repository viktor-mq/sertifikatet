# Base Game Models
"""
Shared database models and data structures for games
Note: These extend the existing models in app/models.py
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class GameSessionData:
    """Data structure for game session information"""
    session_id: str
    user_id: int
    game_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    score: int = 0
    max_score: int = 0
    completed: bool = False
    session_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSessionData':
        """Create from dictionary"""
        # Convert ISO format back to datetime
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)

@dataclass
class GameScore:
    """Data structure for game scoring"""
    base_score: int
    bonus_score: int = 0
    time_bonus: int = 0
    accuracy_bonus: int = 0
    streak_bonus: int = 0
    penalty: int = 0
    
    @property
    def total_score(self) -> int:
        """Calculate total score"""
        return max(0, self.base_score + self.bonus_score + self.time_bonus + 
                  self.accuracy_bonus + self.streak_bonus - self.penalty)
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary"""
        return {
            'base_score': self.base_score,
            'bonus_score': self.bonus_score,
            'time_bonus': self.time_bonus,
            'accuracy_bonus': self.accuracy_bonus,
            'streak_bonus': self.streak_bonus,
            'penalty': self.penalty,
            'total_score': self.total_score
        }

@dataclass
class GameQuestion:
    """Data structure for game questions"""
    question_id: str
    question_text: str
    question_type: str  # 'multiple_choice', 'true_false', 'image_recognition', etc.
    options: list = None
    correct_answer: Any = None
    explanation: str = ""
    difficulty: str = "medium"  # 'easy', 'medium', 'hard'
    category: str = ""
    image_url: str = ""
    time_limit: int = 30  # seconds
    points: int = 10
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameQuestion':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class GameAnswer:
    """Data structure for game answers"""
    question_id: str
    user_answer: Any
    correct_answer: Any
    is_correct: bool
    time_taken: float  # seconds
    points_earned: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data

class GameSessionManager:
    """Manager for game session operations"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def create_session(self, user_id: int, game_id: str) -> GameSessionData:
        """Create a new game session"""
        from games.base.utils import generate_session_id
        
        session_id = generate_session_id()
        session = GameSessionData(
            session_id=session_id,
            user_id=user_id,
            game_id=game_id,
            start_time=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[GameSessionData]:
        """Get an active session"""
        return self.active_sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session data"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        return True
    
    def complete_session(self, session_id: str, final_score: int) -> Optional[GameSessionData]:
        """Complete a session and remove from active sessions"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        session.completed = True
        session.end_time = datetime.utcnow()
        session.score = final_score
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return session
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session.start_time < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        return len(expired_sessions)

class GameDataSerializer:
    """Utility class for serializing/deserializing game data"""
    
    @staticmethod
    def serialize_session_data(data: Dict[str, Any]) -> str:
        """Serialize session data to JSON string"""
        try:
            return json.dumps(data, default=str)
        except Exception:
            return "{}"
    
    @staticmethod
    def deserialize_session_data(data_str: str) -> Dict[str, Any]:
        """Deserialize session data from JSON string"""
        try:
            return json.loads(data_str) if data_str else {}
        except Exception:
            return {}
    
    @staticmethod
    def serialize_questions(questions: list) -> str:
        """Serialize list of GameQuestion objects"""
        try:
            question_dicts = [q.to_dict() if hasattr(q, 'to_dict') else q for q in questions]
            return json.dumps(question_dicts, default=str)
        except Exception:
            return "[]"
    
    @staticmethod
    def deserialize_questions(data_str: str) -> list:
        """Deserialize list of GameQuestion objects"""
        try:
            question_dicts = json.loads(data_str) if data_str else []
            return [GameQuestion.from_dict(q) for q in question_dicts]
        except Exception:
            return []

# Database model extensions (these would extend existing models)
def extend_existing_models():
    """
    This function would extend existing models in app/models.py
    with game-specific fields and methods
    """
    pass

# Example of how to extend existing GameSession model
class GameSessionExtensions:
    """
    Methods that could be added to the existing GameSession model
    """
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get parsed session data"""
        if hasattr(self, 'session_data') and self.session_data:
            return GameDataSerializer.deserialize_session_data(self.session_data)
        return {}
    
    def set_session_data(self, data: Dict[str, Any]):
        """Set session data as JSON string"""
        self.session_data = GameDataSerializer.serialize_session_data(data)
    
    def add_answer(self, answer: GameAnswer):
        """Add an answer to the session"""
        session_data = self.get_session_data()
        if 'answers' not in session_data:
            session_data['answers'] = []
        
        session_data['answers'].append(answer.to_dict())
        self.set_session_data(session_data)
    
    def get_answers(self) -> list:
        """Get all answers for this session"""
        session_data = self.get_session_data()
        answers_data = session_data.get('answers', [])
        return [GameAnswer(**answer) for answer in answers_data]
    
    def calculate_accuracy(self) -> float:
        """Calculate accuracy percentage for this session"""
        answers = self.get_answers()
        if not answers:
            return 0.0
        
        correct_count = sum(1 for answer in answers if answer.is_correct)
        return (correct_count / len(answers)) * 100
    
    def get_completion_time(self) -> float:
        """Get completion time in seconds"""
        if self.created_at and self.updated_at:
            return (self.updated_at - self.created_at).total_seconds()
        return 0.0