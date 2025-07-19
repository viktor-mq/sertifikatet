"""Simplified TikTok-style learning system integration using existing tables

Revision ID: add_learning_system
Revises: ml_adaptive_learning
Create Date: 2025-01-08 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_learning_system'
down_revision = 'ml_adaptive_learning'
branch_labels = None
depends_on = None


def upgrade():
    # Add theory-specific fields to existing videos table for TikTok-style content
    op.add_column('videos', sa.Column('aspect_ratio', sa.String(10), nullable=True))
    op.add_column('videos', sa.Column('content_type', sa.String(20), nullable=True, default='video'))
    op.add_column('videos', sa.Column('theory_module_ref', sa.String(10), nullable=True))  # e.g., "1.1", "2.3"
    op.add_column('videos', sa.Column('sequence_order', sa.Integer, nullable=True, default=0))
    
    # Add theory content tracking to existing learning paths
    op.add_column('learning_paths', sa.Column('path_type', sa.String(20), nullable=True, default='traditional'))
    op.add_column('learning_paths', sa.Column('module_number', sa.Float, nullable=True))  # For theory modules like 1.1, 1.2
    op.add_column('learning_paths', sa.Column('content_file_path', sa.String(500), nullable=True))
    op.add_column('learning_paths', sa.Column('summary_file_path', sa.String(500), nullable=True))
    
    # Add theory-specific progress tracking to existing user_learning_paths
    op.add_column('user_learning_paths', sa.Column('content_viewed', sa.Boolean, nullable=True, default=False))
    op.add_column('user_learning_paths', sa.Column('summary_viewed', sa.Boolean, nullable=True, default=False))
    op.add_column('user_learning_paths', sa.Column('videos_watched', sa.Integer, nullable=True, default=0))
    op.add_column('user_learning_paths', sa.Column('time_spent_minutes', sa.Integer, nullable=True, default=0))
    
    # Add theory content type to existing video_progress for better tracking
    op.add_column('video_progress', sa.Column('content_type', sa.String(20), nullable=True, default='video'))
    op.add_column('video_progress', sa.Column('watch_percentage', sa.Float, nullable=True, default=0.0))
    op.add_column('video_progress', sa.Column('interaction_quality', sa.Float, nullable=True, default=0.0))


def downgrade():
    # Remove added columns in reverse order
    op.drop_column('video_progress', 'interaction_quality')
    op.drop_column('video_progress', 'watch_percentage')
    op.drop_column('video_progress', 'content_type')
    
    op.drop_column('user_learning_paths', 'time_spent_minutes')
    op.drop_column('user_learning_paths', 'videos_watched')
    op.drop_column('user_learning_paths', 'summary_viewed')
    op.drop_column('user_learning_paths', 'content_viewed')
    
    op.drop_column('learning_paths', 'summary_file_path')
    op.drop_column('learning_paths', 'content_file_path')
    op.drop_column('learning_paths', 'module_number')
    op.drop_column('learning_paths', 'path_type')
    
    op.drop_column('videos', 'sequence_order')
    op.drop_column('videos', 'theory_module_ref')
    op.drop_column('videos', 'content_type')
    op.drop_column('videos', 'aspect_ratio')
