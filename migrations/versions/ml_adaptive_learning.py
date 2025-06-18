"""Add ML models for adaptive learning

Revision ID: ml_adaptive_learning
Revises: subscription_models
Create Date: 2025-06-18 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'ml_adaptive_learning'
down_revision = 'subscription_models'
branch_labels = None
depends_on = None

def upgrade():
    # Create user_skill_profiles table
    op.create_table('user_skill_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('difficulty_preference', sa.Float(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('response_time_variance', sa.Float(), nullable=True),
        sa.Column('questions_attempted', sa.Integer(), nullable=True),
        sa.Column('questions_correct', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'category', 'subcategory', name='_user_skill_uc')
    )
    op.create_index('idx_user_skill_category', 'user_skill_profiles', ['user_id', 'category'], unique=False)

    # Create question_difficulty_profiles table
    op.create_table('question_difficulty_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('computed_difficulty', sa.Float(), nullable=True),
        sa.Column('discrimination_power', sa.Float(), nullable=True),
        sa.Column('guess_factor', sa.Float(), nullable=True),
        sa.Column('total_attempts', sa.Integer(), nullable=True),
        sa.Column('correct_attempts', sa.Integer(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('response_time_variance', sa.Float(), nullable=True),
        sa.Column('skill_threshold', sa.Float(), nullable=True),
        sa.Column('learning_value', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_question_difficulty', 'question_difficulty_profiles', ['computed_difficulty'], unique=False)
    op.create_index('idx_question_discrimination', 'question_difficulty_profiles', ['discrimination_power'], unique=False)

    # Create adaptive_quiz_sessions table
    op.create_table('adaptive_quiz_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quiz_session_id', sa.Integer(), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), nullable=True),
        sa.Column('target_difficulty', sa.Float(), nullable=True),
        sa.Column('adaptation_strength', sa.Float(), nullable=True),
        sa.Column('initial_skill_estimate', sa.Float(), nullable=True),
        sa.Column('final_skill_estimate', sa.Float(), nullable=True),
        sa.Column('skill_improvement', sa.Float(), nullable=True),
        sa.Column('questions_above_skill', sa.Integer(), nullable=True),
        sa.Column('questions_below_skill', sa.Integer(), nullable=True),
        sa.Column('questions_optimal', sa.Integer(), nullable=True),
        sa.Column('average_engagement_score', sa.Float(), nullable=True),
        sa.Column('frustration_indicators', sa.Integer(), nullable=True),
        sa.Column('confidence_trend', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_session_id'], ['quiz_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create learning_analytics table
    op.create_table('learning_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_study_time_minutes', sa.Integer(), nullable=True),
        sa.Column('questions_attempted', sa.Integer(), nullable=True),
        sa.Column('questions_correct', sa.Integer(), nullable=True),
        sa.Column('average_difficulty_attempted', sa.Float(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('response_time_consistency', sa.Float(), nullable=True),
        sa.Column('mistakes_per_session', sa.Float(), nullable=True),
        sa.Column('learning_velocity', sa.Float(), nullable=True),
        sa.Column('knowledge_retention', sa.Float(), nullable=True),
        sa.Column('concept_mastery_score', sa.Float(), nullable=True),
        sa.Column('preferred_study_duration', sa.Integer(), nullable=True),
        sa.Column('optimal_question_difficulty', sa.Float(), nullable=True),
        sa.Column('learning_style_indicators', sa.Text(), nullable=True),
        sa.Column('weakest_categories', sa.Text(), nullable=True),
        sa.Column('strength_categories', sa.Text(), nullable=True),
        sa.Column('recommended_study_time', sa.Integer(), nullable=True),
        sa.Column('recommended_difficulty', sa.Float(), nullable=True),
        sa.Column('priority_topics', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='_user_date_analytics_uc')
    )
    op.create_index('idx_analytics_date', 'learning_analytics', ['date'], unique=False)
    op.create_index('idx_analytics_user_date', 'learning_analytics', ['user_id', 'date'], unique=False)

    # Create ml_models table
    op.create_table('ml_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall_score', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('hyperparameters', sa.Text(), nullable=True),
        sa.Column('feature_importance', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('total_predictions', sa.Integer(), nullable=True),
        sa.Column('last_retrained', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='_model_version_uc')
    )

    # Create enhanced_quiz_responses table
    op.create_table('enhanced_quiz_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_response_id', sa.Integer(), nullable=False),
        sa.Column('user_confidence_level', sa.Float(), nullable=True),
        sa.Column('difficulty_perception', sa.Float(), nullable=True),
        sa.Column('cognitive_load_score', sa.Float(), nullable=True),
        sa.Column('time_to_first_answer', sa.Float(), nullable=True),
        sa.Column('answer_change_count', sa.Integer(), nullable=True),
        sa.Column('hesitation_score', sa.Float(), nullable=True),
        sa.Column('question_order_in_session', sa.Integer(), nullable=True),
        sa.Column('user_fatigue_score', sa.Float(), nullable=True),
        sa.Column('predicted_difficulty', sa.Float(), nullable=True),
        sa.Column('actual_difficulty', sa.Float(), nullable=True),
        sa.Column('knowledge_gain_estimate', sa.Float(), nullable=True),
        sa.Column('skill_level_before', sa.Float(), nullable=True),
        sa.Column('skill_level_after', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_response_id'], ['quiz_responses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('enhanced_quiz_responses')
    op.drop_table('ml_models')
    op.drop_index('idx_analytics_user_date', table_name='learning_analytics')
    op.drop_index('idx_analytics_date', table_name='learning_analytics')
    op.drop_table('learning_analytics')
    op.drop_table('adaptive_quiz_sessions')
    op.drop_index('idx_question_discrimination', table_name='question_difficulty_profiles')
    op.drop_index('idx_question_difficulty', table_name='question_difficulty_profiles')
    op.drop_table('question_difficulty_profiles')
    op.drop_index('idx_user_skill_category', table_name='user_skill_profiles')
    op.drop_table('user_skill_profiles')
