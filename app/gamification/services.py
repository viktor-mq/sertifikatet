# app/gamification/services.py
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Achievement, UserAchievement, QuizSession
from app.gamification_models import (
    UserLevel, XPTransaction, DailyChallenge, UserDailyChallenge,
    WeeklyTournament, TournamentParticipant, StreakReward
)
from app.utils.email import send_badge_notification, send_streak_lost_email
import math


class GamificationService:
    """Service for handling all gamification logic"""
    
    # XP rewards configuration
    XP_REWARDS = {
        'quiz_complete': 10,
        'quiz_perfect': 50,
        'question_correct': 2,
        'question_streak_5': 10,
        'question_streak_10': 25,
        'daily_login': 5,
        'daily_challenge': 50,
        'achievement_unlock': 0,  # Variable based on achievement
        'tournament_participation': 20,
        'tournament_top3': 100,
        'tournament_win': 250,
        'friend_challenge_win': 30,
        'video_complete': 15,
        'learning_path_complete': 100,
    }
    
    # Level progression formula
    @staticmethod
    def calculate_xp_for_level(level):
        """Calculate XP required for a specific level"""
        # Exponential growth: 100, 150, 225, 340, 510...
        return int(100 * math.pow(1.5, level - 1))
    
    @staticmethod
    def calculate_level_from_xp(total_xp):
        """Calculate level based on total XP"""
        if total_xp < 100:
            return 1
            
        level = 1
        xp_accumulated = 0
        
        while True:
            xp_for_next_level = GamificationService.calculate_xp_for_level(level + 1)
            if xp_accumulated + xp_for_next_level > total_xp:
                break
            xp_accumulated += xp_for_next_level
            level += 1
            
            # Safety check to prevent infinite loops
            if level > 100:
                break
        
        return level
    
    @classmethod
    def award_xp(cls, user, amount, transaction_type, description=None, reference_id=None):
        """Award XP to a user and handle level progression"""
        # Create XP transaction record
        transaction = XPTransaction(
            user_id=user.id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id
        )
        db.session.add(transaction)
        
        # Update user's total XP
        user.total_xp = (user.total_xp or 0) + amount
        
        # Get or create user level info
        user_level = UserLevel.query.filter_by(user_id=user.id).first()
        if not user_level:
            user_level = UserLevel(user_id=user.id)
            db.session.add(user_level)
        
        # Update current XP and check for level up
        user_level.current_xp += amount
        user_level.total_xp += amount
        
        level_ups = []
        while user_level.current_xp >= user_level.next_level_xp:
            # Level up!
            user_level.current_xp -= user_level.next_level_xp
            user_level.current_level += 1
            user_level.next_level_xp = cls.calculate_xp_for_level(user_level.current_level + 1)
            user_level.last_level_up = datetime.utcnow()
            level_ups.append(user_level.current_level)
            
            # Check for level-based achievements
            cls.check_level_achievements(user, user_level.current_level)
        
        db.session.commit()
        return level_ups
    
    @classmethod
    def check_achievements(cls, user, context=None):
        """Check and award achievements based on user progress"""
        achievements_earned = []
        
        # Get user's current achievements
        earned_achievement_ids = [ua.achievement_id for ua in user.achievements]
        
        # Get all available achievements
        all_achievements = Achievement.query.filter(
            ~Achievement.id.in_(earned_achievement_ids) if earned_achievement_ids else True
        ).all()
        
        for achievement in all_achievements:
            if cls._check_achievement_criteria(user, achievement, context):
                # Award achievement
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
                db.session.add(user_achievement)
                
                # Award XP for achievement
                if achievement.points > 0:
                    cls.award_xp(
                        user, 
                        achievement.points, 
                        'achievement_unlock',
                        f"Låst opp: {achievement.name}",
                        achievement.id
                    )
                
                achievements_earned.append(achievement)
                
                # Send notification email
                try:
                    send_badge_notification(user, achievement.name)
                except Exception as e:
                    print(f"Failed to send achievement email: {e}")
        
        if achievements_earned:
            db.session.commit()
        
        return achievements_earned
    
    @classmethod
    def get_achievement_analytics_data(cls, achievements_earned, user):
        """Get analytics data for earned achievements"""
        analytics_data = []
        
        for achievement in achievements_earned:
            analytics_data.append({
                'user_id': user.id,
                'achievement_id': achievement.id,
                'achievement_name': achievement.name,
                'category': achievement.category,
                'points_earned': achievement.points,
                'user_level': user.get_level()
            })
        
        return analytics_data
    
    @classmethod
    def _check_achievement_criteria(cls, user, achievement, context=None):
        """Check if user meets criteria for specific achievement"""
        progress = user.progress
        
        if achievement.requirement_type == 'quiz_count':
            return progress and progress.total_quizzes_taken >= achievement.requirement_value
        
        elif achievement.requirement_type == 'perfect_quiz':
            # Check for perfect score quizzes
            perfect_quizzes = QuizSession.query.filter_by(
                user_id=user.id,
                score=100
            ).count()
            return perfect_quizzes >= achievement.requirement_value
        
        elif achievement.requirement_type == 'streak_days':
            return progress and progress.current_streak_days >= achievement.requirement_value
        
        elif achievement.requirement_type == 'total_questions':
            return progress and progress.total_questions_answered >= achievement.requirement_value
        
        elif achievement.requirement_type == 'accuracy':
            if progress and progress.total_questions_answered >= 50:  # Min 50 questions
                accuracy = (progress.correct_answers / progress.total_questions_answered) * 100
                return accuracy >= achievement.requirement_value
        
        elif achievement.requirement_type == 'category_master':
            # Check if user has high accuracy in specific category
            if context and context.get('category'):
                category_sessions = QuizSession.query.filter_by(
                    user_id=user.id,
                    category=context['category']
                ).filter(QuizSession.score >= 90).count()
                return category_sessions >= achievement.requirement_value
        
        elif achievement.requirement_type == 'speed_demon':
            # Check for fast quiz completion
            if context and context.get('quiz_time'):
                return context['quiz_time'] <= achievement.requirement_value
        
        elif achievement.requirement_type == 'level':
            user_level = UserLevel.query.filter_by(user_id=user.id).first()
            return user_level and user_level.current_level >= achievement.requirement_value
        
        return False
    
    @classmethod
    def check_level_achievements(cls, user, new_level):
        """Check for level-based achievements"""
        level_achievements = Achievement.query.filter_by(
            requirement_type='level',
            requirement_value=new_level
        ).all()
        
        for achievement in level_achievements:
            if not any(ua.achievement_id == achievement.id for ua in user.achievements):
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
                db.session.add(user_achievement)
                
                # Send notification
                try:
                    send_badge_notification(user, achievement.name)
                except Exception as e:
                    print(f"Failed to send achievement email: {e}")
    
    @classmethod
    def get_daily_challenges(cls, user):
        """Get today's daily challenges for a user"""
        today = date.today()
        
        # Get today's challenges
        challenges = DailyChallenge.query.filter_by(
            date=today,
            is_active=True
        ).all()
        
        # Get user's progress on these challenges
        user_challenges = []
        for challenge in challenges:
            user_challenge = UserDailyChallenge.query.filter_by(
                user_id=user.id,
                challenge_id=challenge.id
            ).first()
            
            if not user_challenge:
                user_challenge = UserDailyChallenge(
                    user_id=user.id,
                    challenge_id=challenge.id
                )
                db.session.add(user_challenge)
            
            user_challenges.append(user_challenge)
        
        db.session.commit()
        return user_challenges
    
    @classmethod
    def update_daily_challenge_progress(cls, user, challenge_type, increment=1, category=None):
        """Update progress on daily challenges"""
        today = date.today()
        
        # Find matching challenges
        query = DailyChallenge.query.filter_by(
            date=today,
            challenge_type=challenge_type,
            is_active=True
        )
        
        if category:
            query = query.filter_by(category=category)
        
        challenges = query.all()
        
        completed_challenges = []
        for challenge in challenges:
            user_challenge = UserDailyChallenge.query.filter_by(
                user_id=user.id,
                challenge_id=challenge.id
            ).first()
            
            if user_challenge and not user_challenge.completed:
                user_challenge.progress += increment
                
                # Check if completed
                if user_challenge.progress >= challenge.requirement_value:
                    user_challenge.completed = True
                    user_challenge.completed_at = datetime.utcnow()
                    user_challenge.xp_earned = challenge.xp_reward
                    
                    # Award XP
                    cls.award_xp(
                        user,
                        challenge.xp_reward,
                        'daily_challenge',
                        f"Fullført: {challenge.title}",
                        challenge.id
                    )
                    
                    completed_challenges.append(challenge)
        
        db.session.commit()
        return completed_challenges
    
    @classmethod
    def check_and_update_streak(cls, user):
        """Check and update user's streak"""
        progress = user.progress
        if not progress:
            return False
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # If last activity was yesterday, increment streak
        if progress.last_activity_date == yesterday:
            progress.current_streak_days += 1
            progress.last_activity_date = today
            
            # Update longest streak if needed
            if progress.current_streak_days > progress.longest_streak_days:
                progress.longest_streak_days = progress.current_streak_days
            
            # Check for streak rewards
            cls.check_streak_rewards(user, progress.current_streak_days)
            
            db.session.commit()
            return True
        
        # If last activity was today, no change
        elif progress.last_activity_date == today:
            return True
        
        # Otherwise, streak is broken
        else:
            lost_streak = progress.current_streak_days
            if lost_streak > 0:
                progress.current_streak_days = 1
                progress.last_activity_date = today
                db.session.commit()
                
                # Send streak lost notification
                if lost_streak >= 3:  # Only notify for streaks of 3+ days
                    try:
                        send_streak_lost_email(user, lost_streak)
                    except Exception as e:
                        print(f"Failed to send streak lost email: {e}")
            else:
                progress.current_streak_days = 1
                progress.last_activity_date = today
                db.session.commit()
            
            return False
    
    @classmethod
    def check_streak_rewards(cls, user, streak_days):
        """Check and award streak milestone rewards"""
        streak_rewards = StreakReward.query.filter(
            StreakReward.streak_days <= streak_days
        ).all()
        
        for reward in streak_rewards:
            # Check if already awarded
            if reward.badge_id:
                existing = UserAchievement.query.filter_by(
                    user_id=user.id,
                    achievement_id=reward.badge_id
                ).first()
                
                if not existing:
                    # Award achievement
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=reward.badge_id
                    )
                    db.session.add(user_achievement)
            
            # Award XP bonus for reaching exact milestone
            if reward.streak_days == streak_days and reward.xp_bonus > 0:
                cls.award_xp(
                    user,
                    reward.xp_bonus,
                    'streak',
                    f"Streak milestone: {streak_days} dager",
                    reward.id
                )
    
    @classmethod
    def get_user_ranking(cls, user, period='all-time'):
        """Get user's ranking in leaderboard"""
        if period == 'weekly':
            start_date = date.today() - timedelta(days=date.today().weekday())
            query = db.session.query(
                User.id,
                User.username,
                func.sum(XPTransaction.amount).label('xp_earned')
            ).join(XPTransaction).filter(
                XPTransaction.created_at >= start_date,
                XPTransaction.amount > 0
            ).group_by(User.id).order_by(func.sum(XPTransaction.amount).desc())
        
        elif period == 'monthly':
            start_date = date.today().replace(day=1)
            query = db.session.query(
                User.id,
                User.username,
                func.sum(XPTransaction.amount).label('xp_earned')
            ).join(XPTransaction).filter(
                XPTransaction.created_at >= start_date,
                XPTransaction.amount > 0
            ).group_by(User.id).order_by(func.sum(XPTransaction.amount).desc())
        
        else:  # all-time
            query = db.session.query(
                User.id,
                User.username,
                User.total_xp.label('xp_earned')
            ).order_by(User.total_xp.desc())
        
        rankings = query.limit(100).all()
        
        # Find user's rank
        user_rank = None
        for i, ranking in enumerate(rankings, 1):
            if ranking.id == user.id:
                user_rank = i
                break
        
        # If user not in top 100, calculate their rank
        if not user_rank:
            if period == 'all-time':
                user_rank = User.query.filter(User.total_xp > user.total_xp).count() + 1
            else:
                # Complex query for period-based ranking
                user_xp = db.session.query(
                    func.sum(XPTransaction.amount)
                ).filter(
                    XPTransaction.user_id == user.id,
                    XPTransaction.created_at >= start_date,
                    XPTransaction.amount > 0
                ).scalar() or 0
                
                user_rank = db.session.query(
                    func.count(func.distinct(User.id))
                ).join(XPTransaction).filter(
                    XPTransaction.created_at >= start_date,
                    XPTransaction.amount > 0
                ).group_by(User.id).having(
                    func.sum(XPTransaction.amount) > user_xp
                ).count() + 1
        
        return {
            'rankings': rankings[:10],  # Top 10
            'user_rank': user_rank,
            'total_players': User.query.filter(User.is_active == True).count()
        }
    
    @classmethod
    def join_tournament(cls, user, tournament_id):
        """Join a weekly tournament"""
        tournament = WeeklyTournament.query.get(tournament_id)
        if not tournament or not tournament.is_active:
            return False, "Turneringen er ikke tilgjengelig"
        
        # Check if already joined
        existing = TournamentParticipant.query.filter_by(
            user_id=user.id,
            tournament_id=tournament_id
        ).first()
        
        if existing:
            return False, "Du har allerede meldt deg på denne turneringen"
        
        # Check entry fee
        if tournament.entry_fee_xp > 0:
            if user.total_xp < tournament.entry_fee_xp:
                return False, f"Du trenger {tournament.entry_fee_xp} XP for å delta"
            
            # Deduct entry fee
            cls.award_xp(
                user,
                -tournament.entry_fee_xp,
                'tournament_entry',
                f"Påmelding: {tournament.name}",
                tournament.id
            )
        
        # Create participant entry
        participant = TournamentParticipant(
            user_id=user.id,
            tournament_id=tournament_id
        )
        db.session.add(participant)
        
        # Award participation XP
        cls.award_xp(
            user,
            cls.XP_REWARDS['tournament_participation'],
            'tournament_participation',
            f"Deltok i: {tournament.name}",
            tournament.id
        )
        
        db.session.commit()
        return True, "Påmelding vellykket!"
    
    @classmethod
    def update_tournament_score(cls, user, tournament_id, score_increment):
        """Update user's tournament score"""
        participant = TournamentParticipant.query.filter_by(
            user_id=user.id,
            tournament_id=tournament_id
        ).first()
        
        if participant:
            participant.score += score_increment
            participant.last_participation = datetime.utcnow()
            db.session.commit()
            
            # Update rankings
            cls._update_tournament_rankings(tournament_id)
    
    @classmethod
    def _update_tournament_rankings(cls, tournament_id):
        """Update tournament rankings"""
        participants = TournamentParticipant.query.filter_by(
            tournament_id=tournament_id
        ).order_by(TournamentParticipant.score.desc()).all()
        
        for i, participant in enumerate(participants, 1):
            participant.rank = i
        
        db.session.commit()
