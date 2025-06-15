"""add video system fields

Revision ID: add_video_fields
Revises: 
Create Date: 2025-06-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_video_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add fields to users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('subscription_tier', sa.String(20), nullable=True, server_default='free'))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='0'))
    
    # Add fields to videos table
    with op.batch_alter_table('videos') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'))
        batch_op.add_column(sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'))
        batch_op.create_foreign_key('fk_videos_category_id', 'video_categories', ['category_id'], ['id'])
    
    # Add updated_at to video_progress table
    with op.batch_alter_table('video_progress') as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove fields from video_progress table
    with op.batch_alter_table('video_progress') as batch_op:
        batch_op.drop_column('updated_at')
    
    # Remove fields from videos table
    with op.batch_alter_table('videos') as batch_op:
        batch_op.drop_constraint('fk_videos_category_id', type_='foreignkey')
        batch_op.drop_column('view_count')
        batch_op.drop_column('is_active')
        batch_op.drop_column('category_id')
    
    # Remove fields from users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_admin')
        batch_op.drop_column('subscription_tier')
