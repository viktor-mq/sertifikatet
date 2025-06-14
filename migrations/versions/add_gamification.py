"""add gamification tables

Revision ID: add_gamification
Revises: add_is_verified
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_gamification'
down_revision = 'add_is_verified'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_levels table
    op.create_table('user_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_level', sa.Integer(), default=1),
        sa.Column('current_xp', sa.Integer(), default=0),
        sa.Column('total_xp', sa.Integer(), default=0),
        sa.Column('next_level_xp', sa.Integer(), default=100),
        sa.Column('last_level_up', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create daily_challenges table
    op.create_table('daily_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('challenge_type', sa.String(50)),
        sa.Column('requirement_value', sa.Integer()),
        sa.Column('xp_reward', sa.Integer(), default=50),
        sa.Column('bonus_reward', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('date', sa.Date(), default=sa.func.current_date()),
        sa.Column('category', sa.String(100)),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_daily_challenges table
    op.create_table('user_daily_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('completed', sa.Boolean(), default=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('xp_earned', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['challenge_id'], ['daily_challenges.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'challenge_id', name='_user_daily_challenge_uc')
    )
    
    # Create weekly_tournaments table
    op.create_table('weekly_tournaments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('tournament_type', sa.String(50)),
        sa.Column('category', sa.String(100)),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('entry_fee_xp', sa.Integer(), default=0),
        sa.Column('prize_pool_xp', sa.Integer(), default=1000),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tournament_participants table
    op.create_table('tournament_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), default=0),
        sa.Column('rank', sa.Integer()),
        sa.Column('joined_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('last_participation', sa.DateTime()),
        sa.Column('prize_earned', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tournament_id'], ['weekly_tournaments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tournament_id', name='_user_tournament_uc')
    )
    
    # Create streak_rewards table
    op.create_table('streak_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('streak_days', sa.Integer(), nullable=False),
        sa.Column('reward_name', sa.String(100), nullable=False),
        sa.Column('xp_bonus', sa.Integer(), default=0),
        sa.Column('badge_id', sa.Integer()),
        sa.Column('description', sa.Text()),
        sa.ForeignKeyConstraint(['badge_id'], ['achievements.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('streak_days')
    )
    
    # Create xp_transactions table
    op.create_table('xp_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50)),
        sa.Column('description', sa.String(255)),
        sa.Column('reference_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create power_ups table
    op.create_table('power_ups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('icon', sa.String(100)),
        sa.Column('cost_xp', sa.Integer(), nullable=False),
        sa.Column('effect_type', sa.String(50)),
        sa.Column('effect_duration', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_power_ups table
    op.create_table('user_power_ups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('power_up_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('purchased_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('used_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['power_up_id'], ['power_ups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create friend_challenges table
    op.create_table('friend_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenger_id', sa.Integer(), nullable=False),
        sa.Column('challenged_id', sa.Integer(), nullable=False),
        sa.Column('challenge_type', sa.String(50)),
        sa.Column('category', sa.String(100)),
        sa.Column('wager_xp', sa.Integer(), default=0),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('winner_id', sa.Integer()),
        sa.Column('challenger_score', sa.Integer()),
        sa.Column('challenged_score', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['challenger_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['challenged_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create badge_categories table
    op.create_table('badge_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('icon', sa.String(100)),
        sa.Column('order_index', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_xp_transactions_user_date', 'xp_transactions', ['user_id', 'created_at'])
    op.create_index('idx_daily_challenges_date', 'daily_challenges', ['date', 'is_active'])
    op.create_index('idx_tournament_participants_score', 'tournament_participants', ['tournament_id', 'score'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_tournament_participants_score', table_name='tournament_participants')
    op.drop_index('idx_daily_challenges_date', table_name='daily_challenges')
    op.drop_index('idx_xp_transactions_user_date', table_name='xp_transactions')
    
    # Drop tables in reverse order
    op.drop_table('badge_categories')
    op.drop_table('friend_challenges')
    op.drop_table('user_power_ups')
    op.drop_table('power_ups')
    op.drop_table('xp_transactions')
    op.drop_table('streak_rewards')
    op.drop_table('tournament_participants')
    op.drop_table('weekly_tournaments')
    op.drop_table('user_daily_challenges')
    op.drop_table('daily_challenges')
    op.drop_table('user_levels')
