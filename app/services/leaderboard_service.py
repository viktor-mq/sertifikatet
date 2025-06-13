# app/services/leaderboard_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, func, desc
from .. import db
from ..models import User, UserProgress, LeaderboardEntry, UserAchievement

class LeaderboardService:
    """Service for managing leaderboards and rankings"""
    
    LEADERBOARD_TYPES = ['daily', 'weekly', 'monthly', 'all_time']
    LEADERBOARD_CATEGORIES = ['overall', 'quiz_score', 'achievements', 'streak']
    
    def update_leaderboards(self, user_id: int):
        """Update all leaderboards for a user"""
        user = User.query.get(user_id)
        if not user or not user.progress:
            return
        
        progress = user.progress
        
        # Calculate scores for different categories
        scores = self._calculate_user_scores(user_id, progress)
        
        # Update each leaderboard type
        for lb_type in self.LEADERBOARD_TYPES:
            period_start, period_end = self._get_period_dates(lb_type)
            
            for category, score in scores.items():
                self._update_leaderboard_entry(
                    user_id=user_id,
                    leaderboard_type=lb_type,
                    category=category,
                    score=score,
                    period_start=period_start,
                    period_end=period_end
                )
        
        # Update rankings
        self._update_rankings()
    
    def _calculate_user_scores(self, user_id: int, progress: UserProgress) -> Dict[str, int]:
        """Calculate scores for different leaderboard categories"""
        scores = {}
        
        # Overall score (combination of all factors)
        quiz_score = 0
        if progress.total_questions_answered > 0:
            accuracy = (progress.correct_answers / progress.total_questions_answered) * 100
            quiz_score = int(accuracy * progress.total_quizzes_taken)
        
        # Achievement score (total achievement points)
        achievement_score = db.session.query(
            func.sum(Achievement.points)
        ).join(
            UserAchievement, Achievement.id == UserAchievement.achievement_id
        ).filter(
            UserAchievement.user_id == user_id
        ).scalar() or 0
        
        # Streak score
        streak_score = progress.longest_streak_days * 10
        
        # Calculate overall score
        overall_score = quiz_score + achievement_score + streak_score
        
        scores['overall'] = overall_score
        scores['quiz_score'] = quiz_score
        scores['achievements'] = achievement_score
        scores['streak'] = streak_score
        
        return scores
    
    def _get_period_dates(self, leaderboard_type: str) -> tuple:
        """Get start and end dates for a leaderboard period"""
        now = datetime.utcnow()
        
        if leaderboard_type == 'daily':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif leaderboard_type == 'weekly':
            # Start from Monday
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(days=7)
        elif leaderboard_type == 'monthly':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get first day of next month
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        else:  # all_time
            start = datetime(2000, 1, 1)  # Arbitrary old date
            end = datetime(2100, 1, 1)  # Arbitrary future date
        
        return start, end
    
    def _update_leaderboard_entry(self, user_id: int, leaderboard_type: str, 
                                 category: str, score: int, 
                                 period_start: datetime, period_end: datetime):
        """Update or create a leaderboard entry"""
        # Find existing entry
        entry = LeaderboardEntry.query.filter_by(
            user_id=user_id,
            leaderboard_type=leaderboard_type,
            category=category,
            period_start=period_start,
            period_end=period_end
        ).first()
        
        if entry:
            entry.score = score
            entry.created_at = datetime.utcnow()
        else:
            entry = LeaderboardEntry(
                user_id=user_id,
                leaderboard_type=leaderboard_type,
                category=category,
                score=score,
                period_start=period_start,
                period_end=period_end,
                created_at=datetime.utcnow()
            )
            db.session.add(entry)
        
        db.session.commit()
    
    def _update_rankings(self):
        """Update rankings for all leaderboard entries"""
        for lb_type in self.LEADERBOARD_TYPES:
            period_start, period_end = self._get_period_dates(lb_type)
            
            for category in self.LEADERBOARD_CATEGORIES:
                # Get all entries for this period and category, ordered by score
                entries = LeaderboardEntry.query.filter(
                    and_(
                        LeaderboardEntry.leaderboard_type == lb_type,
                        LeaderboardEntry.category == category,
                        LeaderboardEntry.period_start == period_start,
                        LeaderboardEntry.period_end == period_end
                    )
                ).order_by(desc(LeaderboardEntry.score)).all()
                
                # Update ranks
                for rank, entry in enumerate(entries, 1):
                    entry.rank = rank
        
        db.session.commit()
    
    def get_leaderboard(self, leaderboard_type: str = 'weekly', 
                       category: str = 'overall', limit: int = 10) -> List[Dict]:
        """Get leaderboard entries with user information"""
        period_start, period_end = self._get_period_dates(leaderboard_type)
        
        # Query leaderboard with user info
        results = db.session.query(
            LeaderboardEntry, User
        ).join(
            User, LeaderboardEntry.user_id == User.id
        ).filter(
            and_(
                LeaderboardEntry.leaderboard_type == leaderboard_type,
                LeaderboardEntry.category == category,
                LeaderboardEntry.period_start == period_start,
                LeaderboardEntry.period_end == period_end
            )
        ).order_by(
            LeaderboardEntry.rank
        ).limit(limit).all()
        
        leaderboard = []
        for entry, user in results:
            leaderboard.append({
                'rank': entry.rank,
                'user_id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'score': entry.score,
                'avatar': user.full_name[0].upper() if user.full_name else user.username[0].upper()
            })
        
        return leaderboard
    
    def get_user_rank(self, user_id: int, leaderboard_type: str = 'weekly',
                     category: str = 'overall') -> Optional[Dict]:
        """Get a specific user's rank in a leaderboard"""
        period_start, period_end = self._get_period_dates(leaderboard_type)
        
        entry = LeaderboardEntry.query.filter_by(
            user_id=user_id,
            leaderboard_type=leaderboard_type,
            category=category,
            period_start=period_start,
            period_end=period_end
        ).first()
        
        if entry:
            return {
                'rank': entry.rank,
                'score': entry.score,
                'total_players': LeaderboardEntry.query.filter_by(
                    leaderboard_type=leaderboard_type,
                    category=category,
                    period_start=period_start,
                    period_end=period_end
                ).count()
            }
        
        return None
