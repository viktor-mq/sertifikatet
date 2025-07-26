# app/services/achievement_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, func
from .. import db
from ..models import Achievement, UserAchievement, QuizSession, User, UserProgress, GameSession

class AchievementService:
    """Service for managing achievements and checking conditions"""
    
    def __init__(self):
        # No more hardcoded definitions - everything comes from database
        pass
    
    def get_all_achievements(self):
        """Get all achievements from database"""
        return Achievement.query.all()
    
    def check_achievements(self, user_id: int) -> List[Achievement]:
        """Check all achievements for a user and award new ones"""
        new_achievements = []
        
        # Get already earned achievements
        earned_ids = db.session.query(UserAchievement.achievement_id).filter_by(
            user_id=user_id
        ).all()
        earned_ids = {id[0] for id in earned_ids}
        
        # Get all achievements from database
        all_achievements = self.get_all_achievements()
        
        # Check each achievement
        for achievement in all_achievements:
            if achievement.id not in earned_ids:
                if self._check_achievement_condition(user_id, achievement):
                    # Award achievement
                    awarded = self._award_achievement(user_id, achievement)
                    if awarded:
                        new_achievements.append(achievement)
        
        return new_achievements
    
    def _check_achievement_condition(self, user_id: int, achievement: Achievement) -> bool:
        """Check if user meets achievement condition based on database requirement_type"""
        requirement_type = achievement.requirement_type
        requirement_value = achievement.requirement_value
        
        if requirement_type == 'quiz_count':
            count = QuizSession.query.filter(
                QuizSession.user_id == user_id,
                QuizSession.completed_at.isnot(None)
            ).count()
            return count >= requirement_value
        
        elif requirement_type == 'perfect_score':
            count = QuizSession.query.filter_by(
                user_id=user_id,
                score=100.0
            ).count()
            return count >= requirement_value
        
        elif requirement_type == 'questions_answered':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            return progress and progress.total_questions_answered >= requirement_value
        
        elif requirement_type == 'streak_days':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            return progress and progress.longest_streak_days >= requirement_value
        
        elif requirement_type == 'accuracy_rate':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if progress and progress.total_questions_answered >= 50:  # Min 50 questions
                accuracy = (progress.correct_answers / progress.total_questions_answered) * 100
                return accuracy >= requirement_value
            return False
        
        elif requirement_type == 'videos_watched':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            return progress and progress.total_videos_watched >= requirement_value
        
        elif requirement_type == 'games_played':
            count = GameSession.query.filter_by(user_id=user_id).count()
            return count >= requirement_value
        
        elif requirement_type == 'category_complete':
            # Check category mastery using target_category and min_accuracy from database
            target_category = getattr(achievement, 'target_category', None)
            min_accuracy = getattr(achievement, 'min_accuracy', 85.0)
            min_sessions = getattr(achievement, 'min_sessions', 5)
            
            # Handle NULL values from database
            if not target_category or target_category == 'NULL':
                return False
            if min_accuracy == 'NULL':
                min_accuracy = 85.0
            if min_sessions == 'NULL':
                min_sessions = 5
                
            result = db.session.query(
                func.count(QuizSession.id).label('sessions'),
                func.avg(QuizSession.score).label('avg_score')
            ).filter(
                QuizSession.user_id == user_id,
                QuizSession.category == target_category,
                QuizSession.completed_at.isnot(None)
            ).first()
            
            if result and result.sessions >= min_sessions:
                return result.avg_score >= min_accuracy
            return False
        
        elif requirement_type == 'exam_passed':
            # Check for exam mode quizzes with passing score (38/45 = 84.44%)
            count = QuizSession.query.filter(
                QuizSession.user_id == user_id,
                QuizSession.quiz_type == 'exam',
                QuizSession.total_questions == 45,
                QuizSession.score >= 84.44
            ).count()
            return count >= requirement_value
        
        return False
    
    def _award_achievement(self, user_id: int, achievement: Achievement) -> Optional[Achievement]:
        """Award an achievement to a user"""
        try:
            # Create user achievement record
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                earned_at=datetime.utcnow()
            )
            db.session.add(user_achievement)
            
            # Update user's total points
            user = User.query.get(user_id)
            if user:
                current_xp = getattr(user, 'total_xp', 0)
                user.total_xp = current_xp + achievement.points
            
            db.session.commit()
            return achievement
            
        except Exception as e:
            db.session.rollback()
            print(f"Error awarding achievement: {e}")
            return None
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get all achievements for a user with their status and progress"""
        all_achievements = []
        
        # Get all achievements from database
        achievements = Achievement.query.all()
        
        # Get earned achievements for this user
        earned_achievements = db.session.query(
            Achievement, UserAchievement.earned_at
        ).join(
            UserAchievement, Achievement.id == UserAchievement.achievement_id
        ).filter(
            UserAchievement.user_id == user_id
        ).all()
        
        earned_ids = {ach.id for ach, _ in earned_achievements}
        
        # Add earned achievements
        for achievement, earned_at in earned_achievements:
            all_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon_filename,
                'points': achievement.points,
                'category': achievement.category,
                'earned': True,
                'earned_at': earned_at,
                'progress_text': None,  # No progress needed for earned achievements
                'progress_percentage': 100
            })
        
        # Add unearned achievements with progress
        for achievement in achievements:
            if achievement.id not in earned_ids:
                progress_data = self._get_achievement_progress(user_id, achievement)
                all_achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'icon': achievement.icon_filename,
                    'points': achievement.points,
                    'category': achievement.category,
                    'earned': False,
                    'earned_at': None,
                    'progress_text': progress_data['text'],
                    'progress_percentage': progress_data['percentage']
                })
        
        return sorted(all_achievements, key=lambda x: (not x['earned'], x['category'], x['points']))
    
    def _get_achievement_progress(self, user_id: int, achievement: Achievement) -> Dict:
        """Get progress information for an unearned achievement"""
        requirement_type = achievement.requirement_type
        requirement_value = achievement.requirement_value
        
        if requirement_type == 'quiz_count':
            current = QuizSession.query.filter(
                QuizSession.user_id == user_id,
                QuizSession.completed_at.isnot(None)
            ).count()
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Ta {remaining} quizer til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'perfect_score':
            current = QuizSession.query.filter_by(
                user_id=user_id,
                score=100.0
            ).count()
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Få {remaining} perfekte scorer til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'questions_answered':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            current = progress.total_questions_answered if progress else 0
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Svar på {remaining} spørsmål til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'streak_days':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            current = progress.longest_streak_days if progress else 0
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Hold {remaining} dager streak til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'accuracy_rate':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if progress and progress.total_questions_answered >= 50:
                current_accuracy = (progress.correct_answers / progress.total_questions_answered) * 100
                percentage = min(100, (current_accuracy / requirement_value) * 100)
                if current_accuracy >= requirement_value:
                    return {'text': 'Klar!', 'percentage': 100}
                else:
                    return {
                        'text': f'Oppnå {requirement_value}% nøyaktighet (nå: {current_accuracy:.1f}%)',
                        'percentage': percentage
                    }
            else:
                questions_needed = 50 - (progress.total_questions_answered if progress else 0)
                return {
                    'text': f'Svar på {questions_needed} spørsmål til for å låse opp',
                    'percentage': 0
                }
        
        elif requirement_type == 'videos_watched':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            current = progress.total_videos_watched if progress else 0
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Se {remaining} videoer til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'games_played':
            current = GameSession.query.filter_by(user_id=user_id).count()
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Spill {remaining} spill til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        elif requirement_type == 'category_complete':
            target_category = getattr(achievement, 'target_category', None)
            min_accuracy = getattr(achievement, 'min_accuracy', 85.0)
            min_sessions = getattr(achievement, 'min_sessions', 5)
            
            if not target_category:
                return {'text': 'Ikke konfigurert', 'percentage': 0}
                
            result = db.session.query(
                func.count(QuizSession.id).label('sessions'),
                func.avg(QuizSession.score).label('avg_score')
            ).filter(
                QuizSession.user_id == user_id,
                QuizSession.category == target_category,
                QuizSession.completed_at.isnot(None)
            ).first()
            
            current_sessions = result.sessions if result else 0
            current_accuracy = result.avg_score if result else 0
            
            if current_sessions < min_sessions:
                remaining_sessions = min_sessions - current_sessions
                return {
                    'text': f'Ta {remaining_sessions} {target_category} quizer til',
                    'percentage': (current_sessions / min_sessions) * 50  # 50% for sessions
                }
            elif current_accuracy < min_accuracy:
                return {
                    'text': f'Oppnå {min_accuracy}% i {target_category} (nå: {current_accuracy:.1f}%)',
                    'percentage': 50 + (current_accuracy / min_accuracy) * 50  # 50% + accuracy progress
                }
            else:
                return {'text': 'Klar!', 'percentage': 100}
        
        elif requirement_type == 'exam_passed':
            current = QuizSession.query.filter(
                QuizSession.user_id == user_id,
                QuizSession.quiz_type == 'exam',
                QuizSession.total_questions == 45,
                QuizSession.score >= 84.44
            ).count()
            remaining = max(0, requirement_value - current)
            percentage = min(100, (current / requirement_value) * 100)
            return {
                'text': f'Bestå {remaining} prøveeksamen til' if remaining > 0 else 'Klar!',
                'percentage': percentage
            }
        
        # Default fallback
        return {'text': getattr(achievement, 'progress_hint', 'Låst'), 'percentage': 0}
    
    def mark_achievements_as_shown(self, user_id: int, achievement_ids: list) -> None:
        """Mark achievements as shown to prevent re-displaying"""
        from datetime import datetime
        
        db.session.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id.in_(achievement_ids),
            UserAchievement.shown_at.is_(None)
        ).update(
            {UserAchievement.shown_at: datetime.utcnow()},
            synchronize_session=False
        )
        db.session.commit()
    
    def get_unshown_achievements(self, user_id: int) -> list:
        """Get achievements that haven't been shown to the user yet"""
        unshown = db.session.query(UserAchievement, Achievement).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.shown_at.is_(None)
        ).all()
        
        return [
            {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'points': achievement.points,
                'icon': achievement.icon_filename,
                'earned_at': user_achievement.earned_at.isoformat() if user_achievement.earned_at else None
            }
            for user_achievement, achievement in unshown
        ]
