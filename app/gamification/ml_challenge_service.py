# app/gamification/ml_challenge_service.py
"""
ML-powered daily challenge generation service.
Analyzes user learning patterns and creates personalized daily challenges.
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import random
from dataclasses import dataclass

from .. import db
from ..models import User
from ..gamification_models import DailyChallenge, UserDailyChallenge, XPReward
from ..ml.service import MLService
from .challenge_types import (
    ChallengeType, ChallengeTypeRegistry, CategoryRegistry, DifficultyScaler
)
from .challenge_templates import challenge_template_engine

logger = logging.getLogger(__name__)


@dataclass
class ChallengeConfig:
    """Configuration for generating a challenge"""
    title: str
    description: str
    challenge_type: str
    requirement_value: int
    xp_reward: int
    bonus_reward: int
    category: Optional[str] = None
    difficulty_level: float = 0.5


class MLChallengeService:
    """Service for generating ML-driven personalized daily challenges"""
    
    def __init__(self):
        self.ml_service = MLService()
        
        # Initialize challenge type registry
        self.challenge_registry = ChallengeTypeRegistry()
        self.category_registry = CategoryRegistry()
        self.difficulty_scaler = DifficultyScaler()
        self.template_engine = challenge_template_engine
    
    def generate_daily_challenges_for_all_users(self, target_date: date = None) -> Dict:
        """
        Generate personalized daily challenges for all active users.
        This is typically called by a daily cron job.
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Starting ML challenge generation for {target_date}")
        
        # Get all active users
        active_users = User.query.filter_by(is_active=True).all()
        
        results = {
            'generated': 0,
            'ml_generated': 0,
            'fallback_generated': 0,
            'errors': 0,
            'target_date': target_date.isoformat()
        }
        
        for user in active_users:
            try:
                challenge_config = self.generate_personalized_challenge(user.id, target_date)
                if challenge_config:
                    # Create the challenge in database
                    challenge = self._create_challenge_from_config(challenge_config, target_date)
                    if challenge:
                        results['generated'] += 1
                        if challenge_config.title.startswith('[ML]'):
                            results['ml_generated'] += 1
                        else:
                            results['fallback_generated'] += 1
                    else:
                        results['errors'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error generating challenge for user {user.id}: {e}")
                results['errors'] += 1
        
        logger.info(f"Challenge generation complete: {results}")
        return results
    
    def generate_personalized_challenge(self, user_id: int, target_date: date = None) -> Optional[ChallengeConfig]:
        """
        Generate a personalized challenge for a specific user based on ML analysis.
        """
        if target_date is None:
            target_date = date.today()
        
        # Check if user already has a challenge for this date
        existing_challenge = self._get_existing_challenge(user_id, target_date)
        if existing_challenge:
            logger.info(f"User {user_id} already has challenge for {target_date}")
            return None
        
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            
            # Try ML-based generation first
            if self.ml_service.is_ml_enabled():
                ml_challenge = self._generate_ml_challenge(user)
                if ml_challenge:
                    logger.info(f"Generated ML challenge for user {user_id}")
                    return ml_challenge
            
            # Fallback to smart challenge generation
            fallback_challenge = self._generate_fallback_challenge(user)
            logger.info(f"Generated fallback challenge for user {user_id}")
            return fallback_challenge
            
        except Exception as e:
            logger.error(f"Error generating personalized challenge for user {user_id}: {e}")
            return None
    
    def _generate_ml_challenge(self, user: User) -> Optional[ChallengeConfig]:
        """
        Generate challenge using ML analysis of user's learning patterns.
        """
        try:
            # Get user's weak areas
            weak_areas = self.ml_service.get_weak_areas(user.id)
            
            # Get skill assessment
            skill_assessment = self.ml_service.get_skill_assessment(user.id)
            
            if not weak_areas and skill_assessment.get('total_practice_questions', 0) < 10:
                # Not enough data for ML, use fallback
                return None
            
            # Select challenge type based on user patterns
            challenge_type = self._select_ml_challenge_type(user, skill_assessment)
            
            # Select target category (weakest area)
            target_category = None
            if weak_areas:
                target_category = weak_areas[0]  # Focus on weakest area
            
            # Calculate difficulty and requirements
            difficulty = self._calculate_challenge_difficulty(user, skill_assessment)
            requirement_value = self._calculate_requirement_value(challenge_type, difficulty)
            
            # Generate challenge configuration
            challenge_config = self._build_ml_challenge_config(
                challenge_type, target_category, requirement_value, difficulty, user
            )
            
            return challenge_config
            
        except Exception as e:
            logger.error(f"Error in ML challenge generation for user {user.id}: {e}")
            return None
    
    def _generate_fallback_challenge(self, user: User) -> ChallengeConfig:
        """
        Generate a smart fallback challenge for users without sufficient ML data.
        """
        # Get user's basic statistics
        progress = user.progress
        total_questions = progress.total_questions_answered if progress else 0
        
        # Determine user experience level
        if total_questions < 50:
            # New user - start with basics
            challenge_type = ChallengeType.QUIZ
            requirement_value = 3
            difficulty = 0.3
            category = None
        elif total_questions < 200:
            # Developing user - mixed challenges
            challenge_type = random.choice([ChallengeType.QUIZ, ChallengeType.CATEGORY_FOCUS])
            requirement_value = random.randint(4, 7)
            difficulty = 0.5
            category = random.choice(CategoryRegistry.get_all_categories())
        else:
            # Experienced user - challenging tasks
            challenge_type = random.choice([ChallengeType.PERFECT_SCORE, ChallengeType.CATEGORY_FOCUS, ChallengeType.QUIZ])
            requirement_value = random.randint(6, 10) if challenge_type == ChallengeType.QUIZ else random.randint(2, 4)
            difficulty = 0.7
            category = random.choice(CategoryRegistry.get_all_categories())
        
        return self._build_fallback_challenge_config(
            challenge_type, category, requirement_value, difficulty, user
        )
    
    def _select_ml_challenge_type(self, user: User, skill_assessment: Dict) -> ChallengeType:
        """
        Select the most appropriate challenge type based on ML analysis.
        """
        return ChallengeTypeRegistry.select_optimal_type(skill_assessment, self.ml_service.get_weak_areas(user.id))
    
    def _calculate_challenge_difficulty(self, user: User, skill_assessment: Dict) -> float:
        """
        Calculate appropriate challenge difficulty based on user skill.
        """
        overall_skill = skill_assessment.get('overall_skill_level', 0.5)
        confidence = skill_assessment.get('confidence_level', 0.5)
        
        # Start with user's skill level
        difficulty = overall_skill
        
        # Adjust based on confidence
        if confidence < 0.5:
            difficulty = max(0.2, difficulty - 0.2)  # Easier for low confidence
        elif confidence > 0.8:
            difficulty = min(0.9, difficulty + 0.1)  # Slightly harder for confident users
        
        # Ensure reasonable bounds
        return max(0.2, min(0.9, difficulty))
    
    def _calculate_requirement_value(self, challenge_type: ChallengeType, difficulty: float) -> int:
        """
        Calculate challenge requirement value based on type and difficulty.
        """
        config = ChallengeTypeRegistry.get_config(challenge_type)
        min_req, max_req = config.requirement_range
        
        # Calculate base requirement
        base_requirement = int((min_req + max_req) / 2)
        
        # Scale based on difficulty
        return DifficultyScaler.scale_requirement(base_requirement, difficulty, challenge_type)
    
    def _build_ml_challenge_config(self, challenge_type: ChallengeType, category: str, 
                                  requirement_value: int, difficulty: float, user: User) -> ChallengeConfig:
        """
        Build challenge configuration for ML-generated challenges.
        """
        # Generate text using template engine
        challenge_text = self.template_engine.generate_challenge_text(
            challenge_type=challenge_type,
            requirement_value=requirement_value,
            category=category,
            difficulty=difficulty,
            is_ml_generated=True
        )
        
        # Calculate XP rewards using difficulty scaler
        config = ChallengeTypeRegistry.get_config(challenge_type)
        base_xp = config.base_xp
        xp_reward = DifficultyScaler.scale_xp_reward(base_xp, difficulty, category)
        bonus_reward = DifficultyScaler.calculate_bonus_xp(base_xp, difficulty, challenge_type)
        
        return ChallengeConfig(
            title=challenge_text['title'],
            description=challenge_text['description'],
            challenge_type=challenge_type.value,
            requirement_value=requirement_value,
            xp_reward=xp_reward,
            bonus_reward=bonus_reward,
            category=category,
            difficulty_level=difficulty
        )
    
    def _build_fallback_challenge_config(self, challenge_type: ChallengeType, category: str,
                                       requirement_value: int, difficulty: float, user: User) -> ChallengeConfig:
        """
        Build challenge configuration for fallback challenges.
        """
        # Generate text using template engine (non-ML)
        challenge_text = self.template_engine.generate_challenge_text(
            challenge_type=challenge_type,
            requirement_value=requirement_value,
            category=category,
            difficulty=difficulty,
            is_ml_generated=False
        )
        
        # Calculate XP rewards
        config = ChallengeTypeRegistry.get_config(challenge_type)
        base_xp = config.base_xp
        xp_reward = DifficultyScaler.scale_xp_reward(base_xp, difficulty, category)
        bonus_reward = DifficultyScaler.calculate_bonus_xp(base_xp, difficulty, challenge_type)
        
        return ChallengeConfig(
            title=challenge_text['title'],
            description=challenge_text['description'], 
            challenge_type=challenge_type.value,
            requirement_value=requirement_value,
            xp_reward=xp_reward,
            bonus_reward=bonus_reward,
            category=category,
            difficulty_level=difficulty
        )
    
    def _create_challenge_from_config(self, config: ChallengeConfig, target_date: date) -> Optional[DailyChallenge]:
        """
        Create a DailyChallenge database record from a ChallengeConfig.
        """
        try:
            challenge = DailyChallenge(
                title=config.title,
                description=config.description,
                challenge_type=config.challenge_type,
                requirement_value=config.requirement_value,
                xp_reward=config.xp_reward,
                bonus_reward=config.bonus_reward,
                is_active=True,
                date=target_date,
                category=config.category
            )
            
            db.session.add(challenge)
            db.session.commit()
            
            logger.info(f"Created challenge: {config.title} for {target_date}")
            return challenge
            
        except Exception as e:
            logger.error(f"Error creating challenge from config: {e}")
            db.session.rollback()
            return None
    
    def _get_existing_challenge(self, user_id: int, target_date: date) -> Optional[DailyChallenge]:
        """
        Check if user already has a challenge for the target date.
        """
        try:
            # Check for existing challenges on this date
            existing = DailyChallenge.query.filter_by(
                date=target_date,
                is_active=True
            ).first()
            
            return existing
            
        except Exception as e:
            logger.error(f"Error checking existing challenge: {e}")
            return None
    
    def get_challenge_performance_stats(self, days: int = 30) -> Dict:
        """
        Get performance statistics for ML-generated challenges.
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            # Get all challenges in period
            challenges = DailyChallenge.query.filter(
                DailyChallenge.date >= start_date,
                DailyChallenge.is_active == True
            ).all()
            
            # Categorize by type
            ml_challenges = [c for c in challenges if c.title.startswith('[ML]')]
            fallback_challenges = [c for c in challenges if not c.title.startswith('[ML]')]
            
            # Calculate completion rates
            ml_completion_rate = self._calculate_completion_rate(ml_challenges)
            fallback_completion_rate = self._calculate_completion_rate(fallback_challenges)
            
            return {
                'period_days': days,
                'total_challenges': len(challenges),
                'ml_challenges': len(ml_challenges),
                'fallback_challenges': len(fallback_challenges),
                'ml_completion_rate': ml_completion_rate,
                'fallback_completion_rate': fallback_completion_rate,
                'ml_enabled': self.ml_service.is_ml_enabled()
            }
            
        except Exception as e:
            logger.error(f"Error getting challenge performance stats: {e}")
            return {}
    
    def _calculate_completion_rate(self, challenges: List[DailyChallenge]) -> float:
        """
        Calculate completion rate for a list of challenges.
        """
        if not challenges:
            return 0.0
        
        try:
            total_assignments = 0
            completed_assignments = 0
            
            for challenge in challenges:
                user_challenges = UserDailyChallenge.query.filter_by(
                    challenge_id=challenge.id
                ).all()
                
                total_assignments += len(user_challenges)
                completed_assignments += len([uc for uc in user_challenges if uc.completed])
            
            if total_assignments == 0:
                return 0.0
            
            return completed_assignments / total_assignments
            
        except Exception as e:
            logger.error(f"Error calculating completion rate: {e}")
            return 0.0


# Global instance
ml_challenge_service = MLChallengeService()
