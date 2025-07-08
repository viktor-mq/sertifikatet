"""Add SystemSettings table for ML activation controls

Revision ID: add_system_settings
Revises: ml_adaptive_learning
Create Date: 2025-01-04 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'add_system_settings'
down_revision = 'ml_adaptive_learning'
branch_labels = None
depends_on = None

def upgrade():
    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_key', sa.String(length=100), nullable=False),
        sa.Column('setting_value', sa.Text(), nullable=False),
        sa.Column('setting_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_editable', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.UniqueConstraint('setting_key')
    )
    
    # Create indexes for performance
    op.create_index('idx_setting_category_key', 'system_settings', ['category', 'setting_key'])
    op.create_index('idx_setting_public', 'system_settings', ['is_public'])
    op.create_index('ix_system_settings_setting_key', 'system_settings', ['setting_key'])
    op.create_index('ix_system_settings_category', 'system_settings', ['category'])
    
    # Insert default ML settings
    settings_table = sa.table('system_settings',
        sa.column('setting_key', sa.String),
        sa.column('setting_value', sa.String),
        sa.column('setting_type', sa.String),
        sa.column('description', sa.String),
        sa.column('category', sa.String),
        sa.column('is_public', sa.Boolean),
        sa.column('is_editable', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
        sa.column('updated_by', sa.Integer)
    )
    
    current_time = datetime.utcnow()
    
    # ML Settings defaults
    ml_settings = [
        {
            'setting_key': 'ml_system_enabled',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Master switch for all machine learning features',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_adaptive_learning',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Enable adaptive question selection based on user skill',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_skill_tracking',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Track and analyze user skill development over time',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_difficulty_prediction',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Predict question difficulty using machine learning',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_data_collection',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Collect response times and behavioral data for ML training',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_model_retraining',
            'setting_value': 'true',
            'setting_type': 'boolean',
            'description': 'Automatically retrain ML models with new data',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_fallback_mode',
            'setting_value': 'random',
            'setting_type': 'string',
            'description': 'Fallback question selection when ML is disabled: random, difficulty, category, legacy',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_learning_rate',
            'setting_value': '0.05',
            'setting_type': 'float',
            'description': 'Learning rate for ML algorithms (0.01-0.1)',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        },
        {
            'setting_key': 'ml_adaptation_strength',
            'setting_value': '0.5',
            'setting_type': 'float',
            'description': 'How aggressively to adapt difficulty (0.1-1.0)',
            'category': 'ml',
            'is_public': False,
            'is_editable': True,
            'created_at': current_time,
            'updated_at': current_time,
            'updated_by': None
        }
    ]
    
    # Insert all ML settings
    op.bulk_insert(settings_table, ml_settings)


def downgrade():
    # Remove indexes
    op.drop_index('ix_system_settings_category', table_name='system_settings')
    op.drop_index('ix_system_settings_setting_key', table_name='system_settings')
    op.drop_index('idx_setting_public', table_name='system_settings')
    op.drop_index('idx_setting_category_key', table_name='system_settings')
    
    # Drop the table
    op.drop_table('system_settings')
