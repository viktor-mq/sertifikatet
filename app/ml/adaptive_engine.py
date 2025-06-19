# app/ml/adaptive_engine.py
"""
Core adaptive learning engine that powers personalized question selection.
Uses local machine learning with scikit-learn for privacy-friendly AI.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Optional
import json
import logging
from datetime import datetime, timedelta

from .. import db
from ..models import User, Question, QuizResponse, QuizSession
from .models import (
    UserSkillProfile, QuestionDifficultyProfile, AdaptiveQuizSession,
    LearningAnalytics, EnhancedQuizResponse
)

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """Main engine for adaptive question selection and difficulty adjustment."""
    
    def __init__(self):
        self.skill_estimator = None
        self.difficulty_predictor = None
        self.scaler = StandardScaler()
        self.is_initialized = False
        
        # Algorithm parameters
        self.default_skill = 0.5
        self.adaptation_rate = 0.1
        self.confidence_threshold = 0.7
        
    def initialize_models(self):
        """Initialize ML models and register them in the database"""
        try:
            from .models import MLModel
            
            # Initialize ML algorithms
            self.skill_estimator = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42
            )
            self.difficulty_predictor = RandomForestRegressor(
                n_estimators=50, max_depth=8, random_state=42
            )
            self.is_initialized = True
            
            # Register or update ML models in database
            self._register_ml_models()
            
            logger.info("Adaptive learning engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            self.is_initialized = False
    
    def _register_ml_models(self):
        """Register ML models in the database for tracking"""
        try:
            from .models import MLModel
            
            # First, clean up any old models to ensure clean state
            try:
                MLModel.query.delete()
                db.session.commit()
                logger.info("Cleaned up existing ML model records")
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up old models: {cleanup_error}")
                db.session.rollback()
            
            # Register Skill Estimator
            skill_model = MLModel(
                name='skill_estimator',
                version='v1.0',
                description='Gradient Boosting model for estimating user skill levels',
                hyperparameters=json.dumps({
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 6,
                    'random_state': 42
                }),
                created_by=1,  # System user
                is_active=True,
                accuracy_score=None,  # Will be calculated during retraining
                precision_score=None,
                recall_score=None,
                f1_score=None,
                total_predictions=0
            )
            db.session.add(skill_model)
            
            # Register Difficulty Predictor
            diff_model = MLModel(
                name='difficulty_predictor',
                version='v1.0',
                description='Random Forest model for predicting question difficulty',
                hyperparameters=json.dumps({
                    'n_estimators': 50,
                    'max_depth': 8,
                    'random_state': 42
                }),
                created_by=1,  # System user
                is_active=True,
                accuracy_score=None,  # Will be calculated during retraining
                precision_score=None,
                recall_score=None,
                f1_score=None,
                total_predictions=0
            )
            db.session.add(diff_model)
            
            db.session.commit()
            logger.info("Successfully registered 2 ML models in database")
            
        except Exception as e:
            logger.error(f"Error registering ML models: {e}")
            db.session.rollback()
            raise e
    
    def get_user_skill_profile(self, user_id: int, category: str = None) -> Dict:
        """Get comprehensive skill profile for a user"""
        try:
            if category:
                profiles = UserSkillProfile.query.filter_by(
                    user_id=user_id, category=category
                ).all()
            else:
                profiles = UserSkillProfile.query.filter_by(user_id=user_id).all()
            
            if not profiles:
                return self._create_initial_skill_profile(user_id, category)
            
            skill_data = {
                'overall_accuracy': np.mean([p.accuracy_score for p in profiles]),
                'confidence': np.mean([p.confidence_score for p in profiles]),
                'learning_rate': np.mean([p.learning_rate for p in profiles]),
                'preferred_difficulty': np.mean([p.difficulty_preference for p in profiles]),
                'avg_response_time': np.mean([p.avg_response_time for p in profiles]),
                'total_questions': sum([p.questions_attempted for p in profiles]),
                'categories': {p.category: {
                    'accuracy': p.accuracy_score,
                    'confidence': p.confidence_score,
                    'questions_attempted': p.questions_attempted
                } for p in profiles}
            }
            
            return skill_data
            
        except Exception as e:
            logger.error(f"Error getting skill profile for user {user_id}: {e}")
            return self._create_initial_skill_profile(user_id, category)
    
    def select_adaptive_questions(self, user_id: int, category: str = None, 
                                num_questions: int = 10, session_id: int = None) -> List[Question]:
        """Core algorithm for personalized question selection"""
        try:
            if not self.is_initialized:
                self.initialize_models()
            
            skill_profile = self.get_user_skill_profile(user_id, category)
            
            query = Question.query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)
            
            available_questions = query.all()
            
            if not available_questions:
                logger.warning(f"No questions available for category: {category}")
                return []
            
            # Calculate question scores
            question_scores = []
            for question in available_questions:
                difficulty_score = self._calculate_question_difficulty(question, skill_profile)
                relevance_score = self._calculate_question_relevance(question, user_id, skill_profile)
                learning_value = self._calculate_learning_value(question, skill_profile)
                
                total_score = (
                    0.4 * difficulty_score +
                    0.3 * relevance_score +
                    0.3 * learning_value
                )
                
                question_scores.append((question, total_score))
            
            question_scores.sort(key=lambda x: x[1], reverse=True)
            selected_questions = self._apply_diversity_selection(question_scores, num_questions)
            
            if session_id:
                self._create_adaptive_session_tracking(user_id, session_id, skill_profile)
            
            return [q[0] for q in selected_questions[:num_questions]]
            
        except Exception as e:
            logger.error(f"Error in adaptive question selection: {e}")
            return self._fallback_question_selection(category, num_questions)
    
    def get_learning_insights(self, user_id: int) -> Dict:
        """Generate comprehensive learning insights for a user"""
        try:
            skill_profile = self.get_user_skill_profile(user_id)
            
            insights = {
                'skill_level': skill_profile['overall_accuracy'],
                'confidence': skill_profile['confidence'],
                'weak_areas': self._identify_weak_areas(user_id),
                'strong_areas': self._identify_strong_areas(user_id),
                'study_recommendations': self._generate_study_recommendations(user_id, skill_profile),
                'next_difficulty_level': self._suggest_next_difficulty(skill_profile)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return {}

    # Helper methods
    def _create_initial_skill_profile(self, user_id: int, category: str = None) -> Dict:
        """Create initial skill profile for new users"""
        return {
            'overall_accuracy': 0.5,
            'confidence': 0.5,
            'learning_rate': 0.5,
            'preferred_difficulty': 0.5,
            'avg_response_time': 15.0,
            'total_questions': 0,
            'categories': {}
        }
    
    def _calculate_question_difficulty(self, question: Question, skill_profile: Dict) -> float:
        """Calculate how appropriate this question's difficulty is for the user"""
        difficulty_profile = QuestionDifficultyProfile.query.filter_by(
            question_id=question.id
        ).first()
        
        if difficulty_profile:
            question_difficulty = difficulty_profile.computed_difficulty
        else:
            question_difficulty = self._estimate_question_difficulty(question)
        
        user_skill = skill_profile['overall_accuracy']
        difficulty_match = 1.0 - abs(question_difficulty - user_skill)
        
        if question_difficulty > user_skill:
            growth_bonus = min(0.1, (question_difficulty - user_skill) * 0.5)
            difficulty_match += growth_bonus
        
        return max(0.0, min(1.0, difficulty_match))
    
    def _calculate_question_relevance(self, question: Question, user_id: int, skill_profile: Dict) -> float:
        """Calculate how relevant this question is to user's learning needs"""
        weak_areas = self._identify_weak_areas(user_id)
        relevance_score = 0.5
        
        if question.category in weak_areas:
            relevance_score += 0.3
        
        if question.subcategory in weak_areas:
            relevance_score += 0.2
        
        return min(1.0, relevance_score)
    
    def _calculate_learning_value(self, question: Question, skill_profile: Dict) -> float:
        """Calculate how much the user can learn from this question"""
        difficulty_profile = QuestionDifficultyProfile.query.filter_by(
            question_id=question.id
        ).first()
        
        if difficulty_profile:
            discrimination = difficulty_profile.discrimination_power
            learning_value = difficulty_profile.learning_value or 0.5
        else:
            discrimination = 0.5
            learning_value = 0.5
        
        return discrimination * learning_value
    
    def _identify_weak_areas(self, user_id: int) -> List[str]:
        """Identify user's weak areas based on recent performance"""
        try:
            recent_responses = db.session.query(QuizResponse, Question)\
                .join(Question, QuizResponse.question_id == Question.id)\
                .join(QuizSession, QuizResponse.session_id == QuizSession.id)\
                .filter(QuizSession.user_id == user_id)\
                .filter(QuizSession.completed_at >= datetime.now() - timedelta(days=30))\
                .all()
            
            if not recent_responses:
                return []
            
            category_stats = {}
            for response, question in recent_responses:
                category = question.category
                if category not in category_stats:
                    category_stats[category] = {'correct': 0, 'total': 0}
                
                category_stats[category]['total'] += 1
                if response.is_correct:
                    category_stats[category]['correct'] += 1
            
            weak_areas = []
            for category, stats in category_stats.items():
                if stats['total'] >= 3:
                    accuracy = stats['correct'] / stats['total']
                    if accuracy < 0.7:
                        weak_areas.append(category)
            
            return weak_areas
            
        except Exception as e:
            logger.error(f"Error identifying weak areas for user {user_id}: {e}")
            return []
    
    def _identify_strong_areas(self, user_id: int) -> List[str]:
        """Identify user's strong areas"""
        try:
            skill_profiles = UserSkillProfile.query.filter_by(user_id=user_id).all()
            
            strong_areas = []
            for profile in skill_profiles:
                if (profile.questions_attempted >= 5 and 
                    profile.accuracy_score > 0.8):
                    strong_areas.append(profile.category)
            
            return strong_areas
            
        except Exception as e:
            logger.error(f"Error identifying strong areas: {e}")
            return []
    
    def _estimate_question_difficulty(self, question: Question) -> float:
        """Estimate question difficulty when no historical data is available"""
        try:
            base_difficulty = (question.difficulty_level - 1) / 4
            difficulty_modifiers = 0.0
            
            if question.image_filename:
                difficulty_modifiers -= 0.1
            
            if len(question.question) > 200:
                difficulty_modifiers += 0.1
            
            category_difficulty_map = {
                'traffic_signs': 0.4,
                'road_rules': 0.6,
                'safety': 0.5,
                'parking': 0.7,
                'alcohol_drugs': 0.3
            }
            
            category_base = category_difficulty_map.get(question.category, 0.5)
            
            estimated_difficulty = (base_difficulty * 0.5 + 
                                  category_base * 0.3 + 
                                  (0.5 + difficulty_modifiers) * 0.2)
            
            return max(0.1, min(0.9, estimated_difficulty))
            
        except Exception as e:
            logger.error(f"Error estimating difficulty for question {question.id}: {e}")
            return 0.5
    
    def _apply_diversity_selection(self, scored_questions: List, num_questions: int) -> List:
        """Apply diversity to question selection to avoid topic clustering"""
        if len(scored_questions) <= num_questions:
            return scored_questions
        
        selected = []
        category_counts = {}
        
        for question, score in scored_questions:
            if len(selected) >= num_questions:
                break
            
            category = question.category
            max_per_category = max(2, num_questions // 3)
            category_count = category_counts.get(category, 0)
            
            if category_count < max_per_category or score > 0.9:
                selected.append((question, score))
                category_counts[category] = category_count + 1
        
        return selected
    
    def _create_adaptive_session_tracking(self, user_id: int, session_id: int, skill_profile: Dict):
        """Create tracking record for adaptive session"""
        try:
            adaptive_session = AdaptiveQuizSession(
                user_id=user_id,
                quiz_session_id=session_id,
                algorithm_version='v1.0',
                target_difficulty=skill_profile['preferred_difficulty'],
                initial_skill_estimate=skill_profile['overall_accuracy']
            )
            db.session.add(adaptive_session)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating adaptive session tracking: {e}")
            db.session.rollback()
    
    def _fallback_question_selection(self, category: str = None, num_questions: int = 10) -> List[Question]:
        """Fallback to simple random selection when ML fails"""
        try:
            query = Question.query.filter_by(is_active=True)
            if category:
                query = query.filter_by(category=category)
            
            return query.order_by(db.func.random()).limit(num_questions).all()
            
        except Exception as e:
            logger.error(f"Error in fallback question selection: {e}")
            return []
    
    def _generate_study_recommendations(self, user_id: int, skill_profile: Dict) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        try:
            weak_areas = self._identify_weak_areas(user_id)
            overall_accuracy = skill_profile['overall_accuracy']
            
            if overall_accuracy < 0.6:
                recommendations.append("Focus on fundamentals with easier questions")
                recommendations.append("Take shorter study sessions (10-15 minutes)")
            elif overall_accuracy < 0.8:
                recommendations.append("Practice mixed difficulty levels")
                recommendations.append("Focus on weak areas while maintaining strengths")
            else:
                recommendations.append("Challenge yourself with harder questions")
                recommendations.append("Focus on exam simulation mode")
            
            if weak_areas:
                recommendations.append(f"Priority practice needed: {', '.join(weak_areas[:3])}")
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Continue regular practice", "Focus on weak areas"]
    
    def _suggest_next_difficulty(self, skill_profile: Dict) -> float:
        """Suggest optimal difficulty level for next session"""
        current_skill = skill_profile['overall_accuracy']
        confidence = skill_profile['confidence']
        
        if confidence > 0.7:
            target_difficulty = min(0.9, current_skill + 0.15)
        elif confidence < 0.4:
            target_difficulty = max(0.2, current_skill - 0.1)
        else:
            target_difficulty = min(0.8, current_skill + 0.1)
        
        return round(target_difficulty, 2)
    
    def update_user_performance(self, user_id: int, session_id: int, responses: List[Dict]):
        """Update user skill profile based on quiz performance"""
        try:
            if not responses:
                return
            
            total_questions = len(responses)
            correct_answers = sum(1 for r in responses if r.get('is_correct', False))
            accuracy = correct_answers / total_questions
            
            for response in responses:
                question_id = response.get('question_id')
                question = Question.query.get(question_id)
                if not question:
                    continue
                
                self._update_category_skill_profile(
                    user_id, question.category, response, accuracy
                )
                
                self._update_question_difficulty_profile(question_id, response)
            
            self._finalize_adaptive_session(session_id, accuracy, responses)
            
        except Exception as e:
            logger.error(f"Error updating user performance: {e}")
    
    def _update_category_skill_profile(self, user_id: int, category: str, 
                                     response: Dict, session_accuracy: float):
        """Update user's skill profile for specific category"""
        try:
            profile = UserSkillProfile.query.filter_by(
                user_id=user_id, category=category
            ).first()
            
            if not profile:
                profile = UserSkillProfile(
                    user_id=user_id,
                    category=category,
                    accuracy_score=self.default_skill,
                    confidence_score=self.default_skill,
                    learning_rate=0.5,
                    difficulty_preference=self.default_skill
                )
                db.session.add(profile)
            
            profile.questions_attempted += 1
            if response.get('is_correct', False):
                profile.questions_correct += 1
            
            new_accuracy = profile.questions_correct / profile.questions_attempted
            profile.accuracy_score = (0.8 * profile.accuracy_score + 0.2 * new_accuracy)
            
            response_time = response.get('time_spent', 10)
            if profile.avg_response_time > 0:
                profile.avg_response_time = (0.8 * profile.avg_response_time + 0.2 * response_time)
            else:
                profile.avg_response_time = response_time
            
            if session_accuracy > 0.8:
                profile.confidence_score = min(1.0, profile.confidence_score + 0.05)
            elif session_accuracy < 0.5:
                profile.confidence_score = max(0.2, profile.confidence_score - 0.05)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating category skill profile: {e}")
            db.session.rollback()
    
    def _update_question_difficulty_profile(self, question_id: int, response: Dict):
        """Update difficulty profile for a question based on user response"""
        try:
            profile = QuestionDifficultyProfile.query.filter_by(
                question_id=question_id
            ).first()
            
            if not profile:
                profile = QuestionDifficultyProfile(
                    question_id=question_id,
                    computed_difficulty=0.5,
                    discrimination_power=0.5,
                    total_attempts=0,
                    correct_attempts=0
                )
                db.session.add(profile)
            
            profile.total_attempts += 1
            if response.get('is_correct', False):
                profile.correct_attempts += 1
            
            success_rate = profile.correct_attempts / profile.total_attempts
            profile.computed_difficulty = 1.0 - success_rate
            
            response_time = response.get('time_spent', 10)
            if profile.avg_response_time > 0:
                profile.avg_response_time = (0.9 * profile.avg_response_time + 0.1 * response_time)
            else:
                profile.avg_response_time = response_time
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating question difficulty profile: {e}")
            db.session.rollback()
    
    def rebuild_all_profiles(self) -> Dict:
        """Rebuild all user skill profiles from historical data"""
        try:
            updated_profiles = 0
            users = User.query.all()
            
            for user in users:
                # Get user's quiz history
                quiz_sessions = QuizSession.query.filter_by(user_id=user.id).all()
                
                if not quiz_sessions:
                    continue
                
                # Clear existing profiles
                UserSkillProfile.query.filter_by(user_id=user.id).delete()
                
                # Rebuild from historical data
                category_data = {}
                
                for session in quiz_sessions:
                    responses = QuizResponse.query.filter_by(session_id=session.id).all()
                    
                    for response in responses:
                        question = Question.query.get(response.question_id)
                        if not question:
                            continue
                        
                        category = question.category
                        if category not in category_data:
                            category_data[category] = {
                                'total': 0, 'correct': 0, 'response_times': []
                            }
                        
                        category_data[category]['total'] += 1
                        if response.is_correct:
                            category_data[category]['correct'] += 1
                        
                        if response.time_spent_seconds:
                            category_data[category]['response_times'].append(response.time_spent_seconds)
                
                # Create new skill profiles
                for category, data in category_data.items():
                    if data['total'] < 3:  # Skip categories with too few attempts
                        continue
                    
                    accuracy = data['correct'] / data['total']
                    avg_time = np.mean(data['response_times']) if data['response_times'] else 15.0
                    
                    profile = UserSkillProfile(
                        user_id=user.id,
                        category=category,
                        accuracy_score=accuracy,
                        confidence_score=min(0.9, accuracy + 0.1),
                        learning_rate=0.5,
                        difficulty_preference=accuracy,
                        avg_response_time=avg_time,
                        questions_attempted=data['total'],
                        questions_correct=data['correct']
                    )
                    db.session.add(profile)
                    updated_profiles += 1
            
            db.session.commit()
            return {
                'success': True,
                'updated_profiles': updated_profiles,
                'message': f'Successfully rebuilt {updated_profiles} skill profiles'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error rebuilding profiles: {e}')
            return {
                'success': False,
                'error': str(e),
                'updated_profiles': 0
            }
    
    def retrain_models(self) -> Dict:
        """Retrain ML models with latest data and calculate real accuracy"""
        try:
            from .models import MLModel
            
            # Retrain question difficulty models
            questions_updated = 0
            questions = Question.query.filter_by(is_active=True).all()
            
            difficulty_predictions = []  # Store predictions for accuracy calculation
            
            for question in questions:
                # Get response data for this question
                responses = db.session.query(QuizResponse).filter_by(
                    question_id=question.id
                ).all()
                
                if len(responses) < 5:  # Need minimum data
                    continue
                
                # Calculate statistics
                total_attempts = len(responses)
                correct_attempts = sum(1 for r in responses if r.is_correct)
                success_rate = correct_attempts / total_attempts
                actual_difficulty = 1.0 - success_rate
                
                # Get existing difficulty prediction (if any)
                existing_profile = QuestionDifficultyProfile.query.filter_by(
                    question_id=question.id
                ).first()
                
                if existing_profile and existing_profile.computed_difficulty:
                    predicted_difficulty = existing_profile.computed_difficulty
                else:
                    # Use our estimation method for new questions
                    predicted_difficulty = self._estimate_question_difficulty(question)
                
                # Store for accuracy calculation
                difficulty_predictions.append({
                    'predicted': predicted_difficulty,
                    'actual': actual_difficulty,
                    'question_id': question.id
                })
                
                response_times = [r.time_spent_seconds for r in responses if r.time_spent_seconds]
                avg_time = np.mean(response_times) if response_times else 15.0
                time_variance = np.var(response_times) if len(response_times) > 1 else 5.0
                
                # Update or create difficulty profile
                profile = QuestionDifficultyProfile.query.filter_by(
                    question_id=question.id
                ).first()
                
                if not profile:
                    profile = QuestionDifficultyProfile(question_id=question.id)
                    db.session.add(profile)
                
                profile.computed_difficulty = actual_difficulty
                profile.total_attempts = total_attempts
                profile.correct_attempts = correct_attempts
                profile.avg_response_time = avg_time
                profile.response_time_variance = time_variance
                profile.discrimination_power = min(1.0, time_variance / avg_time)
                profile.learning_value = 0.5 + (0.3 * profile.discrimination_power)
                
                questions_updated += 1
            
            # Calculate model accuracies
            skill_accuracy = self._calculate_skill_estimator_accuracy()
            difficulty_accuracy = self._calculate_difficulty_predictor_accuracy(difficulty_predictions)
            
            # Re-initialize models
            self.initialize_models()
            
            # Update model tracking with real accuracy scores
            skill_model = MLModel.query.filter_by(name='skill_estimator', is_active=True).first()
            if skill_model:
                skill_model.accuracy_score = skill_accuracy['accuracy'] if skill_accuracy else None
                skill_model.precision_score = skill_accuracy['precision'] if skill_accuracy else None
                skill_model.recall_score = skill_accuracy['recall'] if skill_accuracy else None
                skill_model.f1_score = skill_accuracy['f1'] if skill_accuracy else None
                skill_model.last_retrained = datetime.now()
                skill_model.total_predictions = (skill_model.total_predictions or 0) + len(difficulty_predictions)
            
            diff_model = MLModel.query.filter_by(name='difficulty_predictor', is_active=True).first()
            if diff_model:
                diff_model.accuracy_score = difficulty_accuracy['accuracy'] if difficulty_accuracy else None
                diff_model.precision_score = difficulty_accuracy['precision'] if difficulty_accuracy else None
                diff_model.recall_score = difficulty_accuracy['recall'] if difficulty_accuracy else None
                diff_model.f1_score = difficulty_accuracy['f1'] if difficulty_accuracy else None
                diff_model.last_retrained = datetime.now()
                diff_model.total_predictions = (diff_model.total_predictions or 0) + len(difficulty_predictions)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Retrained models with {questions_updated} question profiles. Accuracy calculated from real data.',
                'questions_updated': questions_updated,
                'skill_accuracy': skill_accuracy['accuracy'] if skill_accuracy else 'No data',
                'difficulty_accuracy': difficulty_accuracy['accuracy'] if difficulty_accuracy else 'No data'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error retraining models: {e}')
            return {
                'success': False,
                'error': str(e),
                'questions_updated': 0
            }
    
    def _calculate_skill_estimator_accuracy(self) -> Dict:
        """Calculate accuracy of skill estimation based on prediction vs actual performance"""
        try:
            # Get users with enough data for validation
            users_with_data = db.session.query(User).join(
                QuizSession, User.id == QuizSession.user_id
            ).group_by(User.id).having(
                db.func.count(QuizSession.id) >= 3
            ).all()
            
            if len(users_with_data) < 10:  # Need minimum users for reliable accuracy
                return None
            
            predictions = []
            actuals = []
            
            for user in users_with_data:
                # Get user's historical skill estimate
                skill_profile = self.get_user_skill_profile(user.id)
                predicted_skill = skill_profile['overall_accuracy']
                
                # Get actual recent performance
                recent_sessions = QuizSession.query.filter_by(
                    user_id=user.id
                ).order_by(QuizSession.completed_at.desc()).limit(5).all()
                
                if recent_sessions:
                    total_questions = sum(s.total_questions or 0 for s in recent_sessions)
                    total_correct = sum(s.correct_answers or 0 for s in recent_sessions)
                    actual_skill = total_correct / total_questions if total_questions > 0 else 0
                    
                    predictions.append(predicted_skill)
                    actuals.append(actual_skill)
            
            if len(predictions) < 5:
                return None
                
            # Calculate metrics
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            # Mean Absolute Error converted to accuracy
            mae = np.mean(np.abs(predictions - actuals))
            accuracy = max(0, 1 - mae)  # Convert MAE to accuracy (1 = perfect, 0 = worst)
            
            # Convert to classification for precision/recall (>0.7 = high skill)
            pred_high = (predictions > 0.7).astype(int)
            actual_high = (actuals > 0.7).astype(int)
            
            from sklearn.metrics import precision_score, recall_score, f1_score
            
            # Handle edge cases
            if len(np.unique(actual_high)) == 1:
                precision = recall = f1 = accuracy
            else:
                precision = precision_score(actual_high, pred_high, zero_division=0)
                recall = recall_score(actual_high, pred_high, zero_division=0)
                f1 = f1_score(actual_high, pred_high, zero_division=0)
            
            return {
                'accuracy': round(accuracy, 3),
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1': round(f1, 3)
            }
            
        except Exception as e:
            logger.error(f'Error calculating skill estimator accuracy: {e}')
            return None
    
    def _calculate_difficulty_predictor_accuracy(self, predictions_data: List[Dict]) -> Dict:
        """Calculate accuracy of difficulty prediction based on predicted vs actual difficulty"""
        try:
            if len(predictions_data) < 10:  # Need minimum questions for reliable accuracy
                return None
            
            predictions = []
            actuals = []
            
            for item in predictions_data:
                predictions.append(item['predicted'])
                actuals.append(item['actual'])
            
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            # Calculate Mean Absolute Error and convert to accuracy
            mae = np.mean(np.abs(predictions - actuals))
            accuracy = max(0, 1 - mae)
            
            # Convert to classification (>0.6 = difficult)
            pred_difficult = (predictions > 0.6).astype(int)
            actual_difficult = (actuals > 0.6).astype(int)
            
            from sklearn.metrics import precision_score, recall_score, f1_score
            
            # Handle edge cases
            if len(np.unique(actual_difficult)) == 1:
                precision = recall = f1 = accuracy
            else:
                precision = precision_score(actual_difficult, pred_difficult, zero_division=0)
                recall = recall_score(actual_difficult, pred_difficult, zero_division=0)
                f1 = f1_score(actual_difficult, pred_difficult, zero_division=0)
            
            return {
                'accuracy': round(accuracy, 3),
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1': round(f1, 3)
            }
            
        except Exception as e:
            logger.error(f'Error calculating difficulty predictor accuracy: {e}')
            return None
    
    def _finalize_adaptive_session(self, session_id: int, final_accuracy: float, responses: List[Dict]):
        """Update adaptive session with final results"""
        try:
            adaptive_session = AdaptiveQuizSession.query.filter_by(
                quiz_session_id=session_id
            ).first()
            
            if not adaptive_session:
                return
            
            adaptive_session.final_skill_estimate = final_accuracy
            adaptive_session.skill_improvement = (
                final_accuracy - (adaptive_session.initial_skill_estimate or 0.5)
            )
            
            for response in responses:
                predicted_difficulty = response.get('predicted_difficulty', 0.5)
                user_skill = response.get('skill_before', 0.5)
                
                if predicted_difficulty > user_skill + 0.2:
                    adaptive_session.questions_above_skill += 1
                elif predicted_difficulty < user_skill - 0.2:
                    adaptive_session.questions_below_skill += 1
                else:
                    adaptive_session.questions_optimal += 1
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error finalizing adaptive session: {e}")
            db.session.rollback()
