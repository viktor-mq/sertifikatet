# app/gamification/services.py
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Achievement, UserAchievement, QuizSession
from app.gamification_models import (
    UserLevel, XPTransaction, DailyChallenge, UserDailyChallenge,
    WeeklyTournament, TournamentParticipant, StreakReward, XPReward
)
from app.utils.email import send_badge_notification, send_streak_lost_email
import math


class GamificationService:
    """Service for handling all gamification logic"""
    
    # Fallback XP rewards (if database is unavailable)
    FALLBACK_XP_REWARDS = {
        'quiz_complete': 10,
        'quiz_perfect': 50,
        'question_correct': 2,
        'question_streak_5': 10,
        'question_streak_10': 25,
        'daily_login': 5,
        'daily_challenge': 50,
        'achievement_unlock': 0,
        'tournament_participation': 20,
        'tournament_top3': 100,
        'tournament_win': 250,
        'friend_challenge_win': 30,
        'video_complete': 15,
        'learning_path_complete': 100,
    }
    
    @classmethod
    def get_xp_reward(cls, reward_type, **kwargs):
        """Get XP reward from database with optional scaling"""
        try:
            xp_reward = XPReward.query.filter_by(reward_type=reward_type).first()
            if not xp_reward:
                # Fallback to hardcoded values
                return cls.FALLBACK_XP_REWARDS.get(reward_type, 0)
            
            base_xp = xp_reward.base_value
            
            # Apply scaling based on reward type
            if reward_type == 'quiz_complete':
                question_count = kwargs.get('question_count', 1)
                scaled_xp = base_xp + (question_count * float(xp_reward.scaling_factor))
            
            elif reward_type == 'quiz_perfect':
                question_count = kwargs.get('question_count', 1)
                scaled_xp = question_count * float(xp_reward.scaling_factor)
            
            elif reward_type == 'video_complete':
                duration_minutes = kwargs.get('duration_minutes', 1)
                scaled_xp = duration_minutes * float(xp_reward.scaling_factor)
            
            else:
                # No scaling, use base value
                scaled_xp = base_xp
            
            # Apply max value limit if set
            if xp_reward.max_value and scaled_xp > xp_reward.max_value:
                scaled_xp = xp_reward.max_value
            
            return int(scaled_xp)
            
        except Exception as e:
            print(f"Error getting XP reward for {reward_type}: {e}")
            return cls.FALLBACK_XP_REWARDS.get(reward_type, 0)
    
    @classmethod
    def calculate_quiz_xp(cls, correct_answers, total_questions, score):
        """Calculate total XP for a quiz completion (for preview/testing)"""
        total_xp = 0
        breakdown = {}
        
        # Correct answers XP
        correct_xp = correct_answers * cls.get_xp_reward('question_correct')
        total_xp += correct_xp
        breakdown['correct_answers'] = correct_xp
        
        # Completion XP
        completion_xp = cls.get_xp_reward('quiz_complete', question_count=total_questions)
        total_xp += completion_xp
        breakdown['completion'] = completion_xp
        
        # Perfect score bonus
        if score == 100:
            perfect_xp = cls.get_xp_reward('quiz_perfect', question_count=total_questions)
            total_xp += perfect_xp
            breakdown['perfect_bonus'] = perfect_xp
        
        return {
            'total_xp': total_xp,
            'breakdown': breakdown
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
    
    @staticmethod
    def calculate_total_xp_for_level(level):
        """Calculate total cumulative XP needed to reach a specific level"""
        if level <= 1:
            return 0
        
        total_xp = 0
        for lvl in range(2, level + 1):
            total_xp += GamificationService.calculate_xp_for_level(lvl)
        
        return total_xp
    
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
        # Update total XP
        user_level.total_xp += amount

        # Recalculate level and progress from total XP
        old_level = user_level.current_level
        new_level = cls.calculate_level_from_xp(user_level.total_xp)

        # Calculate XP progress within current level
        xp_for_current_level = cls.calculate_total_xp_for_level(new_level)
        xp_for_next_level = cls.calculate_total_xp_for_level(new_level + 1)
        user_level.current_xp = user_level.total_xp - xp_for_current_level
        user_level.next_level_xp = xp_for_next_level - xp_for_current_level

        # Update level and check for level ups
        level_ups = []
        if new_level > old_level:
            user_level.current_level = new_level
            user_level.last_level_up = datetime.utcnow()
            
            # Record all level ups
            for level in range(old_level + 1, new_level + 1):
                level_ups.append(level)
                # Check for level-based achievements
                cls.check_level_achievements(user, level)
                
        db.session.commit()
        return level_ups
    
    @classmethod
    def sync_user_level(cls, user):
        """Manually sync user level with their total XP - fixes corrupted progress data"""
        # Get or create user level
        user_level = UserLevel.query.filter_by(user_id=user.id).first()
        if not user_level:
            user_level = UserLevel(user_id=user.id)
            db.session.add(user_level)
        
        # Recalculate everything from user.total_xp
        total_xp = user.total_xp or 0
        new_level = cls.calculate_level_from_xp(total_xp)
        
        # Calculate XP progress within current level
        xp_for_current_level = cls.calculate_total_xp_for_level(new_level)
        xp_for_next_level = cls.calculate_total_xp_for_level(new_level + 1)
        
        # Update user level data
        user_level.current_level = new_level
        user_level.total_xp = total_xp
        user_level.current_xp = total_xp - xp_for_current_level
        user_level.next_level_xp = xp_for_next_level - xp_for_current_level
        
        db.session.commit()
        
        print(f"✅ Synced user {user.username}: Level {new_level}, {user_level.current_xp}/{user_level.next_level_xp} XP")
        return user_level
    
    @classmethod
    def update_daily_challenge_progress(cls, user, challenge_type, progress_amount, category=None):
        """Update progress on daily challenges"""
        completed_challenges = []
        today = date.today()
        
        # Get active daily challenges of the specified type
        active_challenges = DailyChallenge.query.filter_by(
            challenge_type=challenge_type,
            is_active=True,
            date=today
        ).all()
        
        if category:
            # Filter by category if specified
            active_challenges = [c for c in active_challenges if category in (c.category or '')]
        
        for challenge in active_challenges:
            # Get or create user challenge progress
            user_challenge = UserDailyChallenge.query.filter_by(
                user_id=user.id,
                challenge_id=challenge.id
            ).first()
            
            if not user_challenge:
                user_challenge = UserDailyChallenge(
                    user_id=user.id,
                    challenge_id=challenge.id,
                    progress=0,
                    completed=False
                )
                db.session.add(user_challenge)
            
            # Update progress
            if not user_challenge.completed:
                user_challenge.progress += progress_amount
                
                # Check if challenge is completed
                if user_challenge.progress >= challenge.requirement_value:
                    user_challenge.completed = True
                    user_challenge.completed_at = datetime.utcnow()
                    user_challenge.xp_earned = challenge.xp_reward
                    
                    # Award XP
                    cls.award_xp(
                        user,
                        challenge.xp_reward,
                        'daily_challenge',
                        f"Fullførte: {challenge.title}",
                        challenge.id
                    )
                    
                    completed_challenges.append({
                        'title': challenge.title,
                        'description': challenge.description,
                        'xp_reward': challenge.xp_reward
                    })
        
        db.session.commit()
        return completed_challenges
    
    @classmethod
    def check_and_update_streak(cls, user):
        """Check and update user's activity streak"""
        from app.models import UserProgress
        
        # Get or create user progress
        progress = UserProgress.query.filter_by(user_id=user.id).first()
        if not progress:
            progress = UserProgress(user_id=user.id)
            db.session.add(progress)
        
        today = date.today()
        last_activity = progress.last_activity_date
        
        if not last_activity:
            # First activity
            progress.current_streak_days = 1
            progress.longest_streak_days = 1
            progress.last_activity_date = today
            db.session.commit()
            return True
        
        days_since_last = (today - last_activity).days
        
        if days_since_last == 0:
            # Already active today
            return True
        elif days_since_last == 1:
            # Consecutive day - extend streak
            progress.current_streak_days += 1
            progress.last_activity_date = today
            
            # Update longest streak if needed
            if progress.current_streak_days > progress.longest_streak_days:
                progress.longest_streak_days = progress.current_streak_days
            
            # Check for streak rewards
            cls.check_streak_rewards(user, progress.current_streak_days)
            
            db.session.commit()
            return True
        else:
            # Streak broken
            lost_streak = progress.current_streak_days
            progress.current_streak_days = 1
            progress.last_activity_date = today
            
            # Send streak lost notification for significant streaks
            if lost_streak >= 3:
                try:
                    send_streak_lost_email(user, lost_streak)
                except Exception as e:
                    print(f"Failed to send streak lost email: {e}")
            
            db.session.commit()
            return False
    
    @classmethod
    def check_level_achievements(cls, user, level):
        """Check for level-based achievements"""
        level_milestones = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
        
        if level in level_milestones:
            # Check if achievement exists for this level
            achievement = Achievement.query.filter_by(
                requirement_type='user_level',
                requirement_value=level
            ).first()
            
            if achievement:
                # Check if user already has this achievement
                existing = UserAchievement.query.filter_by(
                    user_id=user.id,
                    achievement_id=achievement.id
                ).first()
                
                if not existing:
                    # Award achievement
                    user_achievement = UserAchievement(
                        user_id=user.id,
                        achievement_id=achievement.id
                    )
                    db.session.add(user_achievement)
                    
                    # Award achievement XP
                    if achievement.points > 0:
                        cls.award_xp(
                            user,
                            achievement.points,
                            'achievement_unlock',
                            f"Låst opp: {achievement.name}",
                            achievement.id
                        )
    
    @classmethod
    def _check_achievement_criteria(cls, user, achievement, context=None):
        """Check if user meets criteria for a specific achievement"""
        # Implementation depends on achievement requirements
        # This is a simplified version - you may need to expand based on your achievement types
        
        if achievement.requirement_type == 'quiz_perfect_score':
            if context and context.get('score') == 100:
                return True
        
        elif achievement.requirement_type == 'quiz_speed':
            if context and context.get('quiz_time', 0) <= achievement.requirement_value:
                return True
        
        elif achievement.requirement_type == 'quiz_count':
            # Count user's completed quizzes
            quiz_count = QuizSession.query.filter_by(
                user_id=user.id,
                completed_at=db.not_(None)
            ).count()
            return quiz_count >= achievement.requirement_value
        
        elif achievement.requirement_type == 'user_level':
            user_level = UserLevel.query.filter_by(user_id=user.id).first()
            if user_level and user_level.current_level >= achievement.requirement_value:
                return True
        
        return False
    
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
        """Get today's daily challenges for a user, including ML-generated ones"""
        today = date.today()
        
        # Get today's challenges
        challenges = DailyChallenge.query.filter_by(
            user_id = user.id,
            date=today,
            is_active=True
        ).all()
        
        # If no challenges exist for today, try to generate ML challenges
        if not challenges:
            try:
                from .ml_challenge_service import ml_challenge_service
                # Generate challenges for all users (including this user)
                generation_results = ml_challenge_service.generate_daily_challenges_for_all_users(today)
                print(f"Generated daily challenges: {generation_results}")
                
                # Refresh challenges query
                challenges = DailyChallenge.query.filter_by(
                    user_id = user.id,
                    date=today,
                    is_active=True
                ).all()
            except Exception as e:
                print(f"Error generating ML challenges: {e}")
                # Continue with empty challenges list
        
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
            cls.get_xp_reward('tournament_participation'),
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

    # Add this method to your GamificationService class in services.py

    @classmethod
    def sync_user_level(cls, user):
        """Manually sync user level with their total XP - one-time fix"""
        # Get or create user level
        user_level = UserLevel.query.filter_by(user_id=user.id).first()
        if not user_level:
            user_level = UserLevel(user_id=user.id)
            db.session.add(user_level)
        
        # Recalculate everything from user.total_xp
        total_xp = user.total_xp or 0
        new_level = cls.calculate_level_from_xp(total_xp)
        
        # Calculate XP progress within current level
        xp_for_current_level = cls.calculate_total_xp_for_level(new_level)
        xp_for_next_level = cls.calculate_total_xp_for_level(new_level + 1)
        
        # Update user level data
        user_level.current_level = new_level
        user_level.total_xp = total_xp
        user_level.current_xp = total_xp - xp_for_current_level
        user_level.next_level_xp = xp_for_next_level - xp_for_current_level
        
        db.session.commit()
        
        print(f"✅ Synced user {user.username}:")
        print(f"   Level: {new_level}")
        print(f"   Progress: {user_level.current_xp}/{user_level.next_level_xp} XP")
        print(f"   Total XP: {total_xp}")
        return user_level

    # Run this in Flask shell to fix your user:
    # from app.gamification.services import GamificationService
    # from app.models import User
    # user = User.query.filter_by(username='Administrator').first()  # or your username
    # GamificationService.sync_user_level(user)
