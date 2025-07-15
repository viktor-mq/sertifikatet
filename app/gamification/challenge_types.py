# app/gamification/challenge_types.py
"""
Challenge type definitions and configurations for ML-generated daily challenges.
"""
from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass


class ChallengeType(Enum):
    """Enumeration of available challenge types"""
    QUIZ = "quiz"
    PERFECT_SCORE = "perfect_score"
    CATEGORY_FOCUS = "category_focus"
    STREAK = "streak"
    SPEED_CHALLENGE = "speed_challenge"
    ACCURACY_CHALLENGE = "accuracy_challenge"


@dataclass
class ChallengeTypeConfig:
    """Configuration for a challenge type"""
    name: str
    description: str
    base_xp: int
    scaling_factor: int
    requirement_range: Tuple[int, int]
    difficulty_scaling: bool = True
    category_specific: bool = False
    ml_weight: float = 1.0  # How likely ML is to select this type


class ChallengeTypeRegistry:
    """Registry of all available challenge types and their configurations"""
    
    CONFIGS = {
        ChallengeType.QUIZ: ChallengeTypeConfig(
            name="Quiz Challenge",
            description="Complete a specified number of quiz questions",
            base_xp=50,
            scaling_factor=10,
            requirement_range=(3, 15),
            difficulty_scaling=True,
            category_specific=False,
            ml_weight=1.0
        ),
        
        ChallengeType.PERFECT_SCORE: ChallengeTypeConfig(
            name="Perfect Score Challenge",
            description="Achieve perfect scores on quiz attempts",
            base_xp=100,
            scaling_factor=25,
            requirement_range=(1, 5),
            difficulty_scaling=True,
            category_specific=False,
            ml_weight=0.7  # Less likely for beginners
        ),
        
        ChallengeType.CATEGORY_FOCUS: ChallengeTypeConfig(
            name="Category Focus Challenge",
            description="Practice questions in a specific category",
            base_xp=75,
            scaling_factor=15,
            requirement_range=(5, 20),
            difficulty_scaling=True,
            category_specific=True,
            ml_weight=1.2  # More likely for targeted practice
        ),
        
        ChallengeType.STREAK: ChallengeTypeConfig(
            name="Learning Streak Challenge",
            description="Maintain consistent daily practice",
            base_xp=40,
            scaling_factor=10,
            requirement_range=(2, 7),
            difficulty_scaling=False,
            category_specific=False,
            ml_weight=0.8
        ),
        
        ChallengeType.SPEED_CHALLENGE: ChallengeTypeConfig(
            name="Speed Challenge",
            description="Complete questions within time limits",
            base_xp=80,
            scaling_factor=20,
            requirement_range=(5, 10),
            difficulty_scaling=True,
            category_specific=False,
            ml_weight=0.6  # For advanced users
        ),
        
        ChallengeType.ACCURACY_CHALLENGE: ChallengeTypeConfig(
            name="Accuracy Challenge",
            description="Achieve high accuracy rates",
            base_xp=70,
            scaling_factor=15,
            requirement_range=(10, 25),
            difficulty_scaling=True,
            category_specific=True,
            ml_weight=0.9
        )
    }
    
    @classmethod
    def get_config(cls, challenge_type: ChallengeType) -> ChallengeTypeConfig:
        """Get configuration for a challenge type"""
        return cls.CONFIGS.get(challenge_type)
    
    @classmethod
    def get_suitable_types_for_user(cls, skill_level: float, confidence: float, 
                                   total_questions: int) -> List[ChallengeType]:
        """Get challenge types suitable for a user's skill level"""
        suitable_types = []
        
        # Always include basic quiz challenges
        suitable_types.append(ChallengeType.QUIZ)
        
        # Category focus for targeted practice
        suitable_types.append(ChallengeType.CATEGORY_FOCUS)
        
        # Streak challenges for habit building
        if total_questions > 10:
            suitable_types.append(ChallengeType.STREAK)
        
        # Perfect score challenges for intermediate+ users
        if skill_level > 0.5 and confidence > 0.5:
            suitable_types.append(ChallengeType.PERFECT_SCORE)
        
        # Accuracy challenges for developing users
        if skill_level > 0.3 and total_questions > 20:
            suitable_types.append(ChallengeType.ACCURACY_CHALLENGE)
        
        # Speed challenges for advanced users
        if skill_level > 0.7 and confidence > 0.7:
            suitable_types.append(ChallengeType.SPEED_CHALLENGE)
        
        return suitable_types
    
    @classmethod
    def select_optimal_type(cls, user_skill_assessment: Dict, weak_areas: List[str]) -> ChallengeType:
        """Select the optimal challenge type based on ML analysis"""
        skill_level = user_skill_assessment.get('overall_skill_level', 0.5)
        confidence = user_skill_assessment.get('confidence_level', 0.5)
        total_questions = user_skill_assessment.get('total_practice_questions', 0)
        
        suitable_types = cls.get_suitable_types_for_user(skill_level, confidence, total_questions)
        
        # Weight selection based on user needs
        if weak_areas:
            # Focus on category-specific challenges for weak areas
            if ChallengeType.CATEGORY_FOCUS in suitable_types:
                return ChallengeType.CATEGORY_FOCUS
        
        if skill_level < 0.4:
            # New users: basic quiz practice
            return ChallengeType.QUIZ
        
        if confidence < 0.5 and skill_level > 0.4:
            # Low confidence: accuracy challenges to build confidence
            if ChallengeType.ACCURACY_CHALLENGE in suitable_types:
                return ChallengeType.ACCURACY_CHALLENGE
        
        if skill_level > 0.7:
            # Advanced users: perfect score or speed challenges
            if ChallengeType.PERFECT_SCORE in suitable_types:
                return ChallengeType.PERFECT_SCORE
        
        # Default to quiz challenge
        return ChallengeType.QUIZ


class CategoryRegistry:
    """Registry of learning categories with Norwegian translations"""
    
    CATEGORIES = {
        'traffic_signs': {
            'name': 'Trafikkskilt',
            'description': 'Gjenkjenne og forstå trafikkskilt',
            'difficulty_weight': 1.0
        },
        'traffic_rules': {
            'name': 'Trafikkregler', 
            'description': 'Grunnleggende trafikkregler og bestemmelser',
            'difficulty_weight': 0.8
        },
        'dangerous_situations': {
            'name': 'Farlige situasjoner',
            'description': 'Håndtering av farlige kjøresituasjoner',
            'difficulty_weight': 1.3
        },
        'vehicle_technology': {
            'name': 'Kjøretøy og teknologi',
            'description': 'Bilteknologi og vedlikehold',
            'difficulty_weight': 0.9
        },
        'road_markings': {
            'name': 'Vegoppmerking',
            'description': 'Forstå veglinjer og oppmerking',
            'difficulty_weight': 0.7
        },
        'priority_rules': {
            'name': 'Vikepliktregler',
            'description': 'Vikeplikt og prioriteringsregler',
            'difficulty_weight': 1.1
        },
        'parking_rules': {
            'name': 'Parkeringsregler',
            'description': 'Regler for parkering og stopping',
            'difficulty_weight': 0.6
        },
        'environment_driving': {
            'name': 'Miljøvennlig kjøring',
            'description': 'Økonomisk og miljøvennlig kjøring',
            'difficulty_weight': 0.5
        }
    }
    
    @classmethod
    def get_category_name(cls, category_key: str) -> str:
        """Get Norwegian name for category"""
        return cls.CATEGORIES.get(category_key, {}).get('name', category_key)
    
    @classmethod
    def get_category_description(cls, category_key: str) -> str:
        """Get description for category"""
        return cls.CATEGORIES.get(category_key, {}).get('description', '')
    
    @classmethod
    def get_difficulty_weight(cls, category_key: str) -> float:
        """Get difficulty weight for category (affects XP rewards)"""
        return cls.CATEGORIES.get(category_key, {}).get('difficulty_weight', 1.0)
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get list of all category keys"""
        return list(cls.CATEGORIES.keys())


class DifficultyScaler:
    """Handles difficulty scaling for challenges"""
    
    @staticmethod
    def scale_requirement(base_requirement: int, difficulty: float, 
                         challenge_type: ChallengeType) -> int:
        """Scale requirement value based on difficulty"""
        config = ChallengeTypeRegistry.get_config(challenge_type)
        min_req, max_req = config.requirement_range
        
        if difficulty < 0.3:
            # Easy
            return max(min_req, int(base_requirement * 0.7))
        elif difficulty > 0.7:
            # Hard
            return min(max_req, int(base_requirement * 1.4))
        else:
            # Medium
            return base_requirement
    
    @staticmethod
    def scale_xp_reward(base_xp: int, difficulty: float, category: str = None) -> int:
        """Scale XP reward based on difficulty and category"""
        # Base scaling
        if difficulty < 0.3:
            xp = int(base_xp * 0.8)
        elif difficulty > 0.7:
            xp = int(base_xp * 1.3)
        else:
            xp = base_xp
        
        # Category difficulty adjustment
        if category:
            category_weight = CategoryRegistry.get_difficulty_weight(category)
            xp = int(xp * category_weight)
        
        return max(10, xp)  # Minimum 10 XP
    
    @staticmethod
    def calculate_bonus_xp(base_xp: int, difficulty: float, challenge_type: ChallengeType) -> int:
        """Calculate bonus XP for completing difficult challenges"""
        if difficulty < 0.5:
            return 0
        
        bonus_percentage = (difficulty - 0.5) * 0.6  # 0-30% bonus
        
        # Perfect score challenges get higher bonuses
        if challenge_type == ChallengeType.PERFECT_SCORE:
            bonus_percentage *= 1.5
        
        return int(base_xp * bonus_percentage)
