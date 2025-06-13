# app/services/achievement_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, func
from .. import db
from ..models import Achievement, UserAchievement, QuizSession, User, UserProgress

class AchievementRule:
    """Base class for achievement rules"""
    def __init__(self, achievement_id: int, name: str, description: str, 
                 points: int, category: str, icon: str):
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.points = points
        self.category = category
        self.icon = icon
    
    def check_condition(self, user_id: int) -> bool:
        """Override this method to implement specific achievement logic"""
        raise NotImplementedError

class QuizAchievementRule(AchievementRule):
    """Rules for quiz-based achievements"""
    def __init__(self, achievement_id: int, name: str, description: str,
                 points: int, icon: str, requirement_type: str, requirement_value: int):
        super().__init__(achievement_id, name, description, points, 'quiz', icon)
        self.requirement_type = requirement_type
        self.requirement_value = requirement_value
    
    def check_condition(self, user_id: int) -> bool:
        if self.requirement_type == 'quizzes_completed':
            count = QuizSession.query.filter_by(
                user_id=user_id,
                completed_at__isnot=None
            ).count()
            return count >= self.requirement_value
        
        elif self.requirement_type == 'perfect_score':
            count = QuizSession.query.filter_by(
                user_id=user_id,
                score=100.0
            ).count()
            return count >= self.requirement_value
        
        elif self.requirement_type == 'questions_answered':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            return progress and progress.total_questions_answered >= self.requirement_value
        
        elif self.requirement_type == 'accuracy_rate':
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if progress and progress.total_questions_answered >= 50:  # Min 50 questions
                accuracy = (progress.correct_answers / progress.total_questions_answered) * 100
                return accuracy >= self.requirement_value
        
        elif self.requirement_type == 'exam_passed':
            # Check for exam mode quizzes with passing score (38/45 = 84.44%)
            count = QuizSession.query.filter(
                QuizSession.user_id == user_id,
                QuizSession.quiz_type == 'exam',
                QuizSession.total_questions == 45,
                QuizSession.score >= 84.44
            ).count()
            return count >= self.requirement_value
        
        return False

class StreakAchievementRule(AchievementRule):
    """Rules for consistency/streak achievements"""
    def __init__(self, achievement_id: int, name: str, description: str,
                 points: int, icon: str, streak_days: int):
        super().__init__(achievement_id, name, description, points, 'consistency', icon)
        self.streak_days = streak_days
    
    def check_condition(self, user_id: int) -> bool:
        progress = UserProgress.query.filter_by(user_id=user_id).first()
        return progress and progress.longest_streak_days >= self.streak_days

class CategoryMasteryRule(AchievementRule):
    """Rules for mastering specific categories"""
    def __init__(self, achievement_id: int, name: str, description: str,
                 points: int, icon: str, category: str, min_accuracy: float):
        super().__init__(achievement_id, name, description, points, 'mastery', icon)
        self.target_category = category
        self.min_accuracy = min_accuracy
    
    def check_condition(self, user_id: int) -> bool:
        # Get category performance
        result = db.session.query(
            func.count(QuizSession.id).label('sessions'),
            func.avg(QuizSession.score).label('avg_score')
        ).filter(
            QuizSession.user_id == user_id,
            QuizSession.category == self.target_category,
            QuizSession.completed_at.isnot(None)
        ).first()
        
        if result and result.sessions >= 5:  # Min 5 sessions in category
            return result.avg_score >= self.min_accuracy
        return False

class AchievementService:
    """Service for managing achievements and checking conditions"""
    
    # Define all achievements with their rules
    ACHIEVEMENT_DEFINITIONS = [
        # Quiz milestones
        {'id': 1, 'rule': QuizAchievementRule, 'params': {
            'name': 'Første Steg', 'description': 'Fullfør din første quiz',
            'points': 10, 'icon': 'fa-flag-checkered',
            'requirement_type': 'quizzes_completed', 'requirement_value': 1
        }},
        {'id': 2, 'rule': QuizAchievementRule, 'params': {
            'name': 'Quiz Entusiast', 'description': 'Fullfør 10 quizer',
            'points': 50, 'icon': 'fa-brain',
            'requirement_type': 'quizzes_completed', 'requirement_value': 10
        }},
        {'id': 3, 'rule': QuizAchievementRule, 'params': {
            'name': 'Quiz Mester', 'description': 'Fullfør 50 quizer',
            'points': 200, 'icon': 'fa-graduation-cap',
            'requirement_type': 'quizzes_completed', 'requirement_value': 50
        }},
        
        # Perfect scores
        {'id': 4, 'rule': QuizAchievementRule, 'params': {
            'name': 'Perfeksjonist', 'description': 'Få 100% på en quiz',
            'points': 25, 'icon': 'fa-star',
            'requirement_type': 'perfect_score', 'requirement_value': 1
        }},
        {'id': 5, 'rule': QuizAchievementRule, 'params': {
            'name': 'Konsistent Perfekt', 'description': 'Få 100% på 5 quizer',
            'points': 100, 'icon': 'fa-medal',
            'requirement_type': 'perfect_score', 'requirement_value': 5
        }},
        
        # Question milestones
        {'id': 6, 'rule': QuizAchievementRule, 'params': {
            'name': 'Kunnskapssøker', 'description': 'Svar på 100 spørsmål',
            'points': 30, 'icon': 'fa-book',
            'requirement_type': 'questions_answered', 'requirement_value': 100
        }},
        {'id': 7, 'rule': QuizAchievementRule, 'params': {
            'name': 'Læremester', 'description': 'Svar på 1000 spørsmål',
            'points': 150, 'icon': 'fa-book-reader',
            'requirement_type': 'questions_answered', 'requirement_value': 1000
        }},
        
        # Accuracy achievements
        {'id': 8, 'rule': QuizAchievementRule, 'params': {
            'name': 'Skarpskytter', 'description': 'Oppretthold 90% nøyaktighet',
            'points': 75, 'icon': 'fa-bullseye',
            'requirement_type': 'accuracy_rate', 'requirement_value': 90
        }},
        
        # Streak achievements
        {'id': 9, 'rule': StreakAchievementRule, 'params': {
            'name': 'Konsistent', 'description': '3 dagers streak',
            'points': 20, 'icon': 'fa-fire',
            'streak_days': 3
        }},
        {'id': 10, 'rule': StreakAchievementRule, 'params': {
            'name': 'Dedikert', 'description': '7 dagers streak',
            'points': 50, 'icon': 'fa-fire-alt',
            'streak_days': 7
        }},
        {'id': 11, 'rule': StreakAchievementRule, 'params': {
            'name': 'Ustoppelig', 'description': '30 dagers streak',
            'points': 200, 'icon': 'fa-rocket',
            'streak_days': 30
        }},
        
        # Exam achievements
        {'id': 12, 'rule': QuizAchievementRule, 'params': {
            'name': 'Eksamensklar', 'description': 'Bestå en prøveeksamen (maks 7 feil)',
            'points': 100, 'icon': 'fa-graduation-cap',
            'requirement_type': 'exam_passed', 'requirement_value': 1
        }},
        
        # Category mastery
        {'id': 13, 'rule': CategoryMasteryRule, 'params': {
            'name': 'Fareskilt Ekspert', 'description': 'Mestre fareskilt kategorien',
            'points': 100, 'icon': 'fa-exclamation-triangle',
            'category': 'Fareskilt', 'min_accuracy': 85
        }},
        {'id': 14, 'rule': CategoryMasteryRule, 'params': {
            'name': 'Trafikkregel Guru', 'description': 'Mestre trafikkregler',
            'points': 100, 'icon': 'fa-traffic-light',
            'category': 'Trafikkregler', 'min_accuracy': 85
        }},
    ]
    
    def __init__(self):
        self.rules = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize achievement rules from definitions"""
        for definition in self.ACHIEVEMENT_DEFINITIONS:
            rule_class = definition['rule']
            params = definition['params']
            rule = rule_class(achievement_id=definition['id'], **params)
            self.rules.append(rule)
    
    def check_achievements(self, user_id: int) -> List[Achievement]:
        """Check all achievements for a user and award new ones"""
        new_achievements = []
        
        # Get already earned achievements
        earned_ids = db.session.query(UserAchievement.achievement_id).filter_by(
            user_id=user_id
        ).all()
        earned_ids = {id[0] for id in earned_ids}
        
        # Check each rule
        for rule in self.rules:
            if rule.achievement_id not in earned_ids:
                if rule.check_condition(user_id):
                    # Award achievement
                    achievement = self._award_achievement(user_id, rule)
                    if achievement:
                        new_achievements.append(achievement)
        
        return new_achievements
    
    def _award_achievement(self, user_id: int, rule: AchievementRule) -> Optional[Achievement]:
        """Award an achievement to a user"""
        try:
            # Get or create achievement record
            achievement = Achievement.query.get(rule.achievement_id)
            if not achievement:
                achievement = Achievement(
                    id=rule.achievement_id,
                    name=rule.name,
                    description=rule.description,
                    icon_filename=rule.icon,
                    points=rule.points,
                    category=rule.category,
                    requirement_type=getattr(rule, 'requirement_type', None),
                    requirement_value=getattr(rule, 'requirement_value', None)
                )
                db.session.add(achievement)
            
            # Create user achievement record
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=rule.achievement_id,
                earned_at=datetime.utcnow()
            )
            db.session.add(user_achievement)
            
            # Update user's total points
            user = User.query.get(user_id)
            if user:
                # Add XP points to user (we'll add this field to User model)
                current_xp = getattr(user, 'total_xp', 0)
                user.total_xp = current_xp + rule.points
            
            db.session.commit()
            return achievement
            
        except Exception as e:
            db.session.rollback()
            print(f"Error awarding achievement: {e}")
            return None
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get all achievements for a user with their status"""
        all_achievements = []
        
        # Get earned achievements
        earned = db.session.query(
            Achievement, UserAchievement.earned_at
        ).join(
            UserAchievement, Achievement.id == UserAchievement.achievement_id
        ).filter(
            UserAchievement.user_id == user_id
        ).all()
        
        earned_ids = {ach.id for ach, _ in earned}
        
        # Add earned achievements
        for achievement, earned_at in earned:
            all_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon_filename,
                'points': achievement.points,
                'category': achievement.category,
                'earned': True,
                'earned_at': earned_at
            })
        
        # Add unearned achievements
        for rule in self.rules:
            if rule.achievement_id not in earned_ids:
                all_achievements.append({
                    'id': rule.achievement_id,
                    'name': rule.name,
                    'description': rule.description,
                    'icon': rule.icon,
                    'points': rule.points,
                    'category': rule.category,
                    'earned': False,
                    'earned_at': None
                })
        
        return sorted(all_achievements, key=lambda x: (not x['earned'], x['category'], x['points']))
