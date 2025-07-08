"""Add TikTok-style learning system tables

Revision ID: add_learning_system
Revises: ml_adaptive_learning
Create Date: 2025-01-08 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_learning_system'
down_revision = 'ml_adaptive_learning'
branch_labels = None
depends_on = None


def upgrade():
    # Create learning_modules table
    op.create_table('learning_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('prerequisites', mysql.JSON(), nullable=True),
        sa.Column('learning_objectives', mysql.JSON(), nullable=True),
        sa.Column('content_directory', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('last_content_update', sa.DateTime(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('average_time_spent', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_number')
    )
    
    # Create learning_submodules table
    op.create_table('learning_submodules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('submodule_number', sa.Float(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_file_path', sa.String(length=500), nullable=True),
        sa.Column('summary_file_path', sa.String(length=500), nullable=True),
        sa.Column('shorts_directory', sa.String(length=500), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('has_quiz', sa.Boolean(), nullable=True),
        sa.Column('quiz_question_count', sa.Integer(), nullable=True),
        sa.Column('has_video_shorts', sa.Boolean(), nullable=True),
        sa.Column('shorts_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ai_generated_content', sa.Boolean(), nullable=True),
        sa.Column('ai_generated_summary', sa.Boolean(), nullable=True),
        sa.Column('content_version', sa.String(length=50), nullable=True),
        sa.Column('last_content_update', sa.DateTime(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('average_study_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['learning_modules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'submodule_number', name='_module_submodule_uc')
    )
    
    # Create video_shorts table
    op.create_table('video_shorts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submodule_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=10), nullable=True),
        sa.Column('resolution', sa.String(length=20), nullable=True),
        sa.Column('file_size_mb', sa.Float(), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('has_captions', sa.Boolean(), nullable=True),
        sa.Column('caption_file_path', sa.String(length=500), nullable=True),
        sa.Column('topic_tags', mysql.JSON(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('average_watch_time', sa.Float(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['submodule_id'], ['learning_submodules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_learning_progress table
    op.create_table('user_learning_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('submodule_id', sa.Integer(), nullable=True),
        sa.Column('progress_type', sa.Enum('module', 'submodule', 'content', 'summary', 'shorts', name='progress_type'), nullable=False),
        sa.Column('status', sa.Enum('not_started', 'in_progress', 'completed', 'skipped', name='progress_status'), nullable=True),
        sa.Column('completion_percentage', sa.Float(), nullable=True),
        sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
        sa.Column('content_viewed', sa.Boolean(), nullable=True),
        sa.Column('summary_viewed', sa.Boolean(), nullable=True),
        sa.Column('shorts_watched', sa.Integer(), nullable=True),
        sa.Column('quiz_attempts', sa.Integer(), nullable=True),
        sa.Column('quiz_best_score', sa.Float(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['learning_modules.id'], ),
        sa.ForeignKeyConstraint(['submodule_id'], ['learning_submodules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_shorts_progress table
    op.create_table('user_shorts_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shorts_id', sa.Integer(), nullable=False),
        sa.Column('watch_status', sa.Enum('not_watched', 'started', 'completed', 'skipped', name='watch_status'), nullable=True),
        sa.Column('watch_percentage', sa.Float(), nullable=True),
        sa.Column('watch_time_seconds', sa.Float(), nullable=True),
        sa.Column('replay_count', sa.Integer(), nullable=True),
        sa.Column('liked', sa.Boolean(), nullable=True),
        sa.Column('swipe_direction', sa.Enum('up', 'down', 'left', 'right', name='swipe_direction'), nullable=True),
        sa.Column('interaction_quality', sa.Float(), nullable=True),
        sa.Column('first_watched_at', sa.DateTime(), nullable=True),
        sa.Column('last_watched_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shorts_id'], ['video_shorts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'shorts_id', name='_user_shorts_uc')
    )
    
    # Create content_analytics table
    op.create_table('content_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.Enum('module', 'submodule', 'content', 'summary', 'shorts', name='content_type'), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.Enum('view', 'completion', 'engagement', 'time_spent', name='metric_type'), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('user_count', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('content_analytics')
    op.drop_table('user_shorts_progress')
    op.drop_table('user_learning_progress')
    op.drop_table('video_shorts')
    op.drop_table('learning_submodules')
    op.drop_table('learning_modules')
