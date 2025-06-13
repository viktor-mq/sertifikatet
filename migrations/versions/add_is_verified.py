"""add is_verified to users table

Revision ID: add_is_verified
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_verified'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add is_verified column to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove is_verified column from users table
    op.drop_column('users', 'is_verified')
