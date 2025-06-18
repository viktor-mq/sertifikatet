# app/ml/models.py
"""
Machine Learning models for enhanced personalization.
These extend the existing database schema with ML-specific data.
"""
from datetime import datetime
from .. import db

class UserSkillProfile(db.Model):
    """Track user skill levels across different categories and concepts"""
    __tablename__ = 'user_skill_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # e.g., 'traffic_signs', 'road_rules'
    subcategory = db.Column(db.String(100))  # More specific areas
    
    # ML-computed skill metrics (0.0 to 1.0)
    accuracy_score = db.Column(db.Float, default=0.5)  # Historical accuracy in this area
    confidence_score = db.Column(db.Float, default=0.5)  # How confident the user is
    learning_rate = db.Column(db.Float, default=0.5)  # How quickly user improves
    difficulty_preference = db.Column(db.Float, default=0.5)  # Preferred difficulty level
    
    # Response time metrics (in seconds)
    avg_response_time = db.Column(db.Float, default=10.0)
    response_time_variance = db.Column(db.Float, default=5.0)
    
    # Learning patterns
    questions_attempted = db.Column(db.Integer, default=0)
    questions_correct = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='skill_profiles')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'subcategory', name='_user_skill_uc'),
        db.Index('idx_user_skill_category', 'user_id', 'category'),
    )


class QuestionDifficultyProfile(db.Model):
    """ML-computed difficulty metrics for each question"""
    __tablename__ = 'question_difficulty_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # ML-computed difficulty metrics (0.0 to 1.0)
    computed_difficulty = db.Column(db.Float, default=0.5)  # Overall difficulty
    discrimination_power = db.Column(db.Float, default=0.5)  # How well it separates skill levels
    guess_factor = db.Column(db.Float, default=0.25)  # Probability of guessing correctly
    
    # Statistics from user responses
    total_attempts = db.Column(db.Integer, default=0)
    correct_attempts = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float, default=10.0)
    response_time_variance = db.Column(db.Float, default=5.0)
    
    # Advanced metrics
    skill_threshold = db.Column(db.Float, default=0.5)  # Min skill needed for >50% chance
    learning_value = db.Column(db.Float, default=0.5)  # How much this question teaches
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', backref='difficulty_profile')
    
    __table_args__ = (
        db.Index('idx_question_difficulty', 'computed_difficulty'),
        db.Index('idx_question_discrimination', 'discrimination_power'),
    )


class AdaptiveQuizSession(db.Model):
    """Extended quiz session with ML-specific tracking"""
    __tablename__ = 'adaptive_quiz_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_session_id = db.Column(db.Integer, db.ForeignKey('quiz_sessions.id'), nullable=False)
    
    # ML algorithm settings used
    algorithm_version = db.Column(db.String(50), default='v1.0')
    target_difficulty = db.Column(db.Float, default=0.5)  # Target difficulty level (0.0-1.0)
    adaptation_strength = db.Column(db.Float, default=0.3)  # How aggressively to adapt
    
    # Session performance metrics
    initial_skill_estimate = db.Column(db.Float)  # Estimated skill at start
    final_skill_estimate = db.Column(db.Float)    # Estimated skill at end
    skill_improvement = db.Column(db.Float)       # Measured improvement
    
    # Question selection metrics
    questions_above_skill = db.Column(db.Integer, default=0)  # Too hard
    questions_below_skill = db.Column(db.Integer, default=0)  # Too easy
    questions_optimal = db.Column(db.Integer, default=0)      # Just right
    
    # Engagement metrics
    average_engagement_score = db.Column(db.Float)  # Based on response times and patterns
    frustration_indicators = db.Column(db.Integer, default=0)  # Count of frustration signs
    confidence_trend = db.Column(db.String(20))  # 'improving', 'declining', 'stable'
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='adaptive_sessions')
    quiz_session = db.relationship('QuizSession', backref='adaptive_data', uselist=False)


class LearningAnalytics(db.Model):
    """Store aggregated learning analytics for ML insights"""
    __tablename__ = 'learning_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Time-based aggregations
    date = db.Column(db.Date, nullable=False)  # Analytics for specific date
    
    # Learning metrics
    total_study_time_minutes = db.Column(db.Integer, default=0)
    questions_attempted = db.Column(db.Integer, default=0)
    questions_correct = db.Column(db.Integer, default=0)
    average_difficulty_attempted = db.Column(db.Float, default=0.5)
    
    # Cognitive load indicators
    avg_response_time = db.Column(db.Float)
    response_time_consistency = db.Column(db.Float)  # Lower = more consistent
    mistakes_per_session = db.Column(db.Float)
    
    # Learning patterns
    learning_velocity = db.Column(db.Float)  # Rate of skill improvement
    knowledge_retention = db.Column(db.Float)  # How well knowledge is retained
    concept_mastery_score = db.Column(db.Float)  # Overall concept understanding
    
    # Behavioral patterns
    preferred_study_duration = db.Column(db.Integer)  # Minutes per session
    optimal_question_difficulty = db.Column(db.Float)  # User's sweet spot
    learning_style_indicators = db.Column(db.Text)  # JSON with learning style data
    
    # Weak areas identification
    weakest_categories = db.Column(db.Text)  # JSON array of categories needing work
    strength_categories = db.Column(db.Text)  # JSON array of strong categories
    
    # Recommendations
    recommended_study_time = db.Column(db.Integer)  # Suggested minutes for next session
    recommended_difficulty = db.Column(db.Float)   # Suggested difficulty level
    priority_topics = db.Column(db.Text)  # JSON array of topics to focus on
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='learning_analytics')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='_user_date_analytics_uc'),
        db.Index('idx_analytics_date', 'date'),
        db.Index('idx_analytics_user_date', 'user_id', 'date'),
    )


class MLModel(db.Model):
    """Track ML model versions and performance"""
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., 'difficulty_predictor', 'skill_estimator'
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # Model performance metrics
    accuracy_score = db.Column(db.Float)
    precision_score = db.Column(db.Float)
    recall_score = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    
    # Model configuration
    hyperparameters = db.Column(db.Text)  # JSON with model settings
    feature_importance = db.Column(db.Text)  # JSON with feature weights
    
    # Usage tracking
    is_active = db.Column(db.Boolean, default=False)
    total_predictions = db.Column(db.Integer, default=0)
    last_retrained = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    __table_args__ = (
        db.UniqueConstraint('name', 'version', name='_model_version_uc'),
    )


# Add new columns to existing QuizResponse model via migration
# We'll extend the existing model by adding fields for ML tracking
class EnhancedQuizResponse(db.Model):
    """Enhanced quiz response tracking for ML analysis"""
    __tablename__ = 'enhanced_quiz_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_response_id = db.Column(db.Integer, db.ForeignKey('quiz_responses.id'), nullable=False)
    
    # ML-specific tracking
    user_confidence_level = db.Column(db.Float)  # Self-reported or inferred confidence
    difficulty_perception = db.Column(db.Float)  # How hard user thought it was
    cognitive_load_score = db.Column(db.Float)   # Estimated mental effort required
    
    # Timing analysis
    time_to_first_answer = db.Column(db.Float)   # Time before first option selected
    answer_change_count = db.Column(db.Integer, default=0)  # How many times changed answer
    hesitation_score = db.Column(db.Float)       # Measure of uncertainty
    
    # Context
    question_order_in_session = db.Column(db.Integer)  # Position in quiz
    user_fatigue_score = db.Column(db.Float)     # Estimated tiredness level
    predicted_difficulty = db.Column(db.Float)   # ML prediction before answer
    actual_difficulty = db.Column(db.Float)      # Calculated after answer
    
    # Learning indicators
    knowledge_gain_estimate = db.Column(db.Float)  # How much user learned from this question
    skill_level_before = db.Column(db.Float)       # Estimated skill before question
    skill_level_after = db.Column(db.Float)        # Estimated skill after question
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_response = db.relationship('QuizResponse', backref='enhanced_data', uselist=False)
