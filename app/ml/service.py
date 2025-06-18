# app/ml/service.py
"""
Machine Learning service layer that integrates with the existing quiz system.
Provides high-level ML functionality for the application.
"""
from typing import List, Dict, Optional
from flask import current_app
import logging

from ..models import User, Question, QuizSession
from .adaptive_engine import AdaptiveLearningEngine
from .models import UserSkillProfile, QuestionDifficultyProfile

logger = logging.getLogger(__name__)


class MLService:
    """
    High-level service for machine learning features.
    Acts as the interface between the ML engine and the rest of the application.
    """
    
    def __init__(self):
        self.engine = AdaptiveLearningEngine()
        self._initialized = False
    
    def initialize(self):
        """Initialize the ML service"""
        try:
            self.engine.initialize_models()
            self._initialized = True
            logger.info("ML Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML Service: {e}")
            self._initialized = False
    
    def get_adaptive_questions(self, user_id: int, category: str = None, 
                             num_questions: int = 10, session_id: int = None) -> List[Question]:
        """
        Get adaptively selected questions for a user.
        This is the main entry point for personalized question selection.
        """
        if not self._initialized:
            self.initialize()
        
        try:
            return self.engine.select_adaptive_questions(
                user_id=user_id,
                category=category,
                num_questions=num_questions,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error getting adaptive questions: {e}")
            # Fallback to basic question selection
            return self._get_fallback_questions(category, num_questions)
    
    def get_user_learning_insights(self, user_id: int) -> Dict:
        """Get comprehensive learning insights for a user"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.engine.get_learning_insights(user_id)
        except Exception as e:
            logger.error(f"Error getting learning insights for user {user_id}: {e}")
            return self._get_basic_insights(user_id)
    
    def update_learning_progress(self, user_id: int, session_id: int, responses: List[Dict]):
        """Update user's learning progress based on quiz responses"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.engine.update_user_performance(user_id, session_id, responses)
        except Exception as e:
            logger.error(f"Error updating learning progress: {e}")
    
    def get_personalized_difficulty(self, user_id: int, category: str = None) -> float:
        """Get recommended difficulty level for a user"""
        if not self._initialized:
            self.initialize()
        
        try:
            skill_profile = self.engine.get_user_skill_profile(user_id, category)
            return self.engine._suggest_next_difficulty(skill_profile)
        except Exception as e:
            logger.error(f"Error getting personalized difficulty: {e}")
            return 0.5  # Default difficulty
    
    def get_weak_areas(self, user_id: int) -> List[str]:
        """Get user's weak areas that need practice"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.engine._identify_weak_areas(user_id)
        except Exception as e:
            logger.error(f"Error identifying weak areas: {e}")
            return []
    
    def get_study_recommendations(self, user_id: int) -> List[str]:
        """Get personalized study recommendations"""
        if not self._initialized:
            self.initialize()
        
        try:
            skill_profile = self.engine.get_user_skill_profile(user_id)
            return self.engine._generate_study_recommendations(user_id, skill_profile)
        except Exception as e:
            logger.error(f"Error getting study recommendations: {e}")
            return [
                "Continue regular practice",
                "Focus on areas where you struggle most",
                "Take regular breaks to avoid fatigue"
            ]
    
    def get_skill_assessment(self, user_id: int) -> Dict:
        """Get current skill assessment for a user"""
        if not self._initialized:
            self.initialize()
        
        try:
            skill_profile = self.engine.get_user_skill_profile(user_id)
            
            return {
                'overall_skill_level': skill_profile['overall_accuracy'],
                'confidence_level': skill_profile['confidence'],
                'learning_progress': skill_profile['learning_rate'],
                'total_practice_questions': skill_profile['total_questions'],
                'category_breakdown': skill_profile['categories'],
                'skill_description': self._get_skill_description(skill_profile['overall_accuracy'])
            }
        except Exception as e:
            logger.error(f"Error getting skill assessment: {e}")
            return self._get_basic_skill_assessment(user_id)
    
    def get_next_session_config(self, user_id: int, category: str = None) -> Dict:
        """Get recommended configuration for the user's next study session"""
        if not self._initialized:
            self.initialize()
        
        try:
            skill_profile = self.engine.get_user_skill_profile(user_id, category)
            weak_areas = self.engine._identify_weak_areas(user_id)
            
            config = {
                'recommended_difficulty': self.engine._suggest_next_difficulty(skill_profile),
                'suggested_question_count': self._suggest_question_count(skill_profile),
                'focus_areas': weak_areas[:3] if weak_areas else [category] if category else [],
                'session_duration_minutes': self._suggest_session_duration(skill_profile),
                'question_types': self._suggest_question_types(skill_profile),
                'breaks_recommended': skill_profile['total_questions'] > 50
            }
            
            return config
        except Exception as e:
            logger.error(f"Error getting session config: {e}")
            return self._get_default_session_config()
    
    def is_ml_enabled(self) -> bool:
        """Check if ML features are enabled and working"""
        return self._initialized
    
    def get_ml_status(self) -> Dict:
        """Get status information about ML system"""
        try:
            # Count ML data points
            skill_profiles_count = UserSkillProfile.query.count()
            difficulty_profiles_count = QuestionDifficultyProfile.query.count()
            
            return {
                'ml_enabled': self._initialized,
                'skill_profiles': skill_profiles_count,
                'question_profiles': difficulty_profiles_count,
                'algorithm_version': 'v1.0',
                'features_available': [
                    'adaptive_question_selection',
                    'personalized_difficulty',
                    'learning_insights',
                    'weak_area_detection',
                    'study_recommendations'
                ]
            }
        except Exception as e:
            logger.error(f"Error getting ML status: {e}")
            return {'ml_enabled': False, 'error': str(e)}
    
    # Helper methods
    def _get_fallback_questions(self, category: str = None, num_questions: int = 10) -> List[Question]:
        """Fallback question selection when ML fails"""
        try:
            query = Question.query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)
            
            return query.order_by(Question.id).limit(num_questions).all()
        except Exception as e:
            logger.error(f"Error in fallback question selection: {e}")
            return []
    
    def _get_basic_insights(self, user_id: int) -> Dict:
        """Basic insights when ML is not available"""
        try:
            # Get basic statistics from quiz sessions
            user = User.query.get(user_id)
            if not user:
                return {}
            
            recent_sessions = QuizSession.query.filter_by(user_id=user_id)\
                .order_by(QuizSession.completed_at.desc()).limit(10).all()
            
            if not recent_sessions:
                return {
                    'skill_level': 0.5,
                    'confidence': 0.5,
                    'weak_areas': [],
                    'strong_areas': [],
                    'study_recommendations': ['Start with basic practice questions'],
                    'next_difficulty_level': 0.5
                }
            
            # Calculate basic metrics
            total_questions = sum(s.total_questions or 0 for s in recent_sessions)
            total_correct = sum(s.correct_answers or 0 for s in recent_sessions)
            accuracy = total_correct / total_questions if total_questions > 0 else 0.5
            
            return {
                'skill_level': accuracy,
                'confidence': min(0.8, accuracy + 0.1),
                'weak_areas': [],
                'strong_areas': [],
                'study_recommendations': self._get_basic_recommendations(accuracy),
                'next_difficulty_level': min(0.8, accuracy + 0.1)
            }
        except Exception as e:
            logger.error(f"Error getting basic insights: {e}")
            return {}
    
    def _get_basic_skill_assessment(self, user_id: int) -> Dict:
        """Basic skill assessment when ML is not available"""
        try:
            user = User.query.get(user_id)
            if not user or not user.progress:
                return {
                    'overall_skill_level': 0.5,
                    'confidence_level': 0.5,
                    'learning_progress': 0.5,
                    'total_practice_questions': 0,
                    'category_breakdown': {},
                    'skill_description': 'Beginner'
                }
            
            progress = user.progress
            accuracy = (progress.correct_answers / progress.total_questions_answered 
                       if progress.total_questions_answered > 0 else 0.5)
            
            return {
                'overall_skill_level': accuracy,
                'confidence_level': min(0.8, accuracy + 0.1),
                'learning_progress': 0.5,
                'total_practice_questions': progress.total_questions_answered,
                'category_breakdown': {},
                'skill_description': self._get_skill_description(accuracy)
            }
        except Exception as e:
            logger.error(f"Error getting basic skill assessment: {e}")
            return {}
    
    def _get_skill_description(self, accuracy: float) -> str:
        """Get human-readable skill description"""
        if accuracy < 0.4:
            return "Beginner - Focus on fundamentals"
        elif accuracy < 0.6:
            return "Developing - Building core knowledge"
        elif accuracy < 0.75:
            return "Intermediate - Good progress"
        elif accuracy < 0.85:
            return "Advanced - Strong understanding"
        else:
            return "Expert - Excellent mastery"
    
    def _suggest_question_count(self, skill_profile: Dict) -> int:
        """Suggest optimal number of questions for next session"""
        accuracy = skill_profile['overall_accuracy']
        total_questions = skill_profile['total_questions']
        
        # Beginners: shorter sessions
        if accuracy < 0.5 or total_questions < 50:
            return 10
        # Intermediate: moderate sessions
        elif accuracy < 0.75:
            return 15
        # Advanced: longer sessions
        else:
            return 20
    
    def _suggest_session_duration(self, skill_profile: Dict) -> int:
        """Suggest optimal session duration in minutes"""
        accuracy = skill_profile['overall_accuracy']
        response_time = skill_profile['avg_response_time']
        
        # Base duration on skill level and response speed
        if accuracy < 0.5:
            base_duration = 15  # Shorter for beginners
        elif accuracy < 0.75:
            base_duration = 25
        else:
            base_duration = 35
        
        # Adjust for response time
        if response_time > 20:
            base_duration += 10  # More time for slower responders
        
        return min(45, max(10, base_duration))
    
    def _suggest_question_types(self, skill_profile: Dict) -> List[str]:
        """Suggest types of questions to focus on"""
        accuracy = skill_profile['overall_accuracy']
        
        if accuracy < 0.5:
            return ['multiple_choice', 'basic_concepts']
        elif accuracy < 0.75:
            return ['multiple_choice', 'scenario_based', 'application']
        else:
            return ['challenging', 'scenario_based', 'exam_simulation']
    
    def _get_basic_recommendations(self, accuracy: float) -> List[str]:
        """Get basic study recommendations based on accuracy"""
        if accuracy < 0.5:
            return [
                "Start with fundamental concepts",
                "Take your time with each question",
                "Review explanations carefully",
                "Practice regularly in short sessions"
            ]
        elif accuracy < 0.75:
            return [
                "Mix easy and challenging questions",
                "Focus on understanding concepts, not memorizing",
                "Practice exam-style questions",
                "Review mistakes to learn from them"
            ]
        else:
            return [
                "Challenge yourself with harder questions",
                "Focus on exam simulation",
                "Work on speed and accuracy",
                "Help others to reinforce your knowledge"
            ]
    
    def _get_default_session_config(self) -> Dict:
        """Default session configuration when ML is not available"""
        return {
            'recommended_difficulty': 0.5,
            'suggested_question_count': 15,
            'focus_areas': [],
            'session_duration_minutes': 25,
            'question_types': ['multiple_choice'],
            'breaks_recommended': False
        }


# Global ML service instance
ml_service = MLService()
