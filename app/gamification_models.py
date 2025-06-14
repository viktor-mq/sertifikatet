# app/gamification_models.py
from datetime import datetime
from app import db


class UserLevel(db.Model):
    """Track user's level progression"""
    __tablename__ = 'user_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    current_level = db.Column(db.Integer, default=1)
    current_xp = db.Column(db.Integer, default=0)
    total_xp = db.Column(db.Integer, default=0)
    next_level_xp = db.Column(db.Integer, default=100)
    last_level_up = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('level_info', uselist=False))


class DailyChallenge(db.Model):
    """Daily challenges for users"""
    __tablename__ = 'daily_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    challenge_type = db.Column(db.String(50))  # 'quiz', 'streak', 'perfect_score', 'category_focus'
    requirement_value = db.Column(db.Integer)  # e.g., 3 quizzes, 5 perfect scores
    xp_reward = db.Column(db.Integer, default=50)
    bonus_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    category = db.Column(db.String(100))  # Optional category focus
    
    # Relationships
    user_challenges = db.relationship('UserDailyChallenge', backref='challenge', cascade='all, delete-orphan')


class UserDailyChallenge(db.Model):
    """Track user's daily challenge progress"""
    __tablename__ = 'user_daily_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('daily_challenges.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    xp_earned = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='daily_challenges')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='_user_daily_challenge_uc'),)


class WeeklyTournament(db.Model):
    """Weekly tournaments"""
    __tablename__ = 'weekly_tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    tournament_type = db.Column(db.String(50))  # 'speed', 'accuracy', 'marathon', 'category'
    category = db.Column(db.String(100))  # Optional category focus
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    entry_fee_xp = db.Column(db.Integer, default=0)  # Optional XP entry fee
    prize_pool_xp = db.Column(db.Integer, default=1000)
    
    # Relationships
    participants = db.relationship('TournamentParticipant', backref='tournament', cascade='all, delete-orphan')


class TournamentParticipant(db.Model):
    """Track tournament participants and scores"""
    __tablename__ = 'tournament_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('weekly_tournaments.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_participation = db.Column(db.DateTime)
    prize_earned = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='tournament_participations')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'tournament_id', name='_user_tournament_uc'),)


class StreakReward(db.Model):
    """Streak milestone rewards"""
    __tablename__ = 'streak_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    streak_days = db.Column(db.Integer, unique=True, nullable=False)
    reward_name = db.Column(db.String(100), nullable=False)
    xp_bonus = db.Column(db.Integer, default=0)
    badge_id = db.Column(db.Integer, db.ForeignKey('achievements.id'))
    description = db.Column(db.Text)


class XPTransaction(db.Model):
    """Track all XP transactions for audit"""
    __tablename__ = 'xp_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Positive for earned, negative for spent
    transaction_type = db.Column(db.String(50))  # 'quiz', 'achievement', 'daily_challenge', 'tournament', 'streak'
    description = db.Column(db.String(255))
    reference_id = db.Column(db.Integer)  # ID of related entity (quiz_session_id, achievement_id, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='xp_transactions')


class PowerUp(db.Model):
    """Power-ups that can be purchased with XP"""
    __tablename__ = 'power_ups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    cost_xp = db.Column(db.Integer, nullable=False)
    effect_type = db.Column(db.String(50))  # 'double_xp', 'streak_freeze', 'hint', 'time_extend'
    effect_duration = db.Column(db.Integer)  # Duration in minutes, 0 for instant
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user_powerups = db.relationship('UserPowerUp', backref='powerup', cascade='all, delete-orphan')


class UserPowerUp(db.Model):
    """Track user's owned power-ups"""
    __tablename__ = 'user_power_ups'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    power_up_id = db.Column(db.Integer, db.ForeignKey('power_ups.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='power_ups')


class FriendChallenge(db.Model):
    """Friend challenges"""
    __tablename__ = 'friend_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenged_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_type = db.Column(db.String(50))  # 'quiz_duel', 'score_beat', 'category_master'
    category = db.Column(db.String(100))
    wager_xp = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'completed', 'declined'
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    challenger_score = db.Column(db.Integer)
    challenged_score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    challenger = db.relationship('User', foreign_keys=[challenger_id], backref='challenges_sent')
    challenged = db.relationship('User', foreign_keys=[challenged_id], backref='challenges_received')
    winner = db.relationship('User', foreign_keys=[winner_id], backref='challenges_won')


class BadgeCategory(db.Model):
    """Categories for badges/achievements"""
    __tablename__ = 'badge_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    order_index = db.Column(db.Integer, default=0)
