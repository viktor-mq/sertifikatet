# app/services/progress_service.py
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import func, desc, case
from .. import db
from ..models import User, UserProgress, QuizSession, QuizResponse, Question

class ProgressService:
    """Service for tracking and analyzing user progress"""
    
    def get_user_dashboard_data(self, user_id: int) -> Dict:
        """Get comprehensive dashboard data for a user"""
        user = db.session.get(User, user_id)
        if not user:
            return {}
        
        progress = user.progress or self._initialize_user_progress(user_id)
        
        # Get basic stats
        stats = self._calculate_basic_stats(user_id, progress)
        
        # Get category performance
        category_performance = self._calculate_category_performance(user_id)
        
        # Get recent activity (last 30 days)
        activity_timeline = self._get_activity_timeline(user_id, days=30)
        
        # Get weak areas
        weak_areas = self._identify_weak_areas(user_id)
        
        # Get mastery levels
        mastery_levels = self._calculate_mastery_levels(user_id)
        
        return {
            'basic_stats': stats,
            'category_performance': category_performance,
            'activity_timeline': activity_timeline,
            'weak_areas': weak_areas,
            'mastery_levels': mastery_levels,
            'streak_info': {
                'current_streak': progress.current_streak_days,
                'longest_streak': progress.longest_streak_days,
                'last_activity': progress.last_activity_date
            }
        }
    
    def _initialize_user_progress(self, user_id: int) -> UserProgress:
        """Initialize user progress if it doesn't exist"""
        progress = UserProgress(user_id=user_id)
        db.session.add(progress)
        db.session.commit()
        return progress
    
    def _calculate_basic_stats(self, user_id: int, progress: UserProgress) -> Dict:
        """Calculate basic user statistics"""
        # Calculate accuracy rate
        accuracy_rate = 0
        if progress.total_questions_answered > 0:
            accuracy_rate = (progress.correct_answers / progress.total_questions_answered) * 100
        
        # Get recent quiz performance (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = QuizSession.query.filter(
            QuizSession.user_id == user_id,
            QuizSession.completed_at >= seven_days_ago
        ).all()
        
        recent_quizzes = len(recent_sessions)
        recent_avg_score = 0
        if recent_sessions:
            recent_avg_score = sum(session.score or 0 for session in recent_sessions) / len(recent_sessions)
        
        # Get improvement trend (compare last 7 days vs previous 7 days)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
        previous_sessions = QuizSession.query.filter(
            QuizSession.user_id == user_id,
            QuizSession.completed_at >= fourteen_days_ago,
            QuizSession.completed_at < seven_days_ago
        ).all()
        
        improvement_trend = 0
        if previous_sessions:
            previous_avg = sum(session.score or 0 for session in previous_sessions) / len(previous_sessions)
            if previous_avg > 0:
                improvement_trend = ((recent_avg_score - previous_avg) / previous_avg) * 100
        
        return {
            'total_quizzes': progress.total_quizzes_taken,
            'total_questions': progress.total_questions_answered,
            'accuracy_rate': round(accuracy_rate, 1),
            'recent_quizzes_7_days': recent_quizzes,
            'recent_avg_score': round(recent_avg_score, 1),
            'improvement_trend': round(improvement_trend, 1),
            'total_game_sessions': progress.total_game_sessions,
            'total_videos_watched': progress.total_videos_watched,
            'videos_completed': progress.videos_completed
        }
    
    def _calculate_category_performance(self, user_id: int) -> List[Dict]:
        """Calculate performance by category using quiz responses"""
        # Use quiz_responses to get accurate category performance
        results = db.session.query(
            QuizResponse.category,
            func.count(func.distinct(QuizResponse.session_id)).label('sessions'),
            func.count(QuizResponse.id).label('total_questions'),
            func.sum(func.cast(QuizResponse.is_correct, db.Integer)).label('correct_answers')
        ).join(
            QuizSession, QuizResponse.session_id == QuizSession.id
        ).filter(
            QuizSession.user_id == user_id,
            QuizSession.completed_at.isnot(None),
            QuizResponse.category.isnot(None)
        ).group_by(QuizResponse.category).all()
        
        category_performance = []
        for result in results:
            accuracy = 0
            avg_score = 0
            if result.total_questions and result.correct_answers:
                accuracy = (result.correct_answers / result.total_questions) * 100
                avg_score = accuracy  # Since we're calculating from individual responses
            
            mastery_level = self._calculate_mastery_level(
                result.sessions, avg_score, accuracy
            )
            
            category_performance.append({
                'category': str(result.category),
                'sessions': int(result.sessions),
                'avg_score': round(float(avg_score), 1),
                'accuracy': round(float(accuracy), 1),
                'mastery_level': str(mastery_level),
                'total_questions': int(result.total_questions or 0)
            })
        
        return sorted(category_performance, key=lambda x: x['avg_score'], reverse=True)
    
    def _calculate_mastery_level(self, sessions: int, avg_score: float, accuracy: float) -> str:
        """Calculate mastery level based on performance metrics"""
        # Require minimum sessions to assess mastery
        if sessions < 3:
            return 'Beginner'
        
        # Define mastery thresholds
        if avg_score >= 90 and accuracy >= 90 and sessions >= 10:
            return 'Expert'
        elif avg_score >= 80 and accuracy >= 80 and sessions >= 5:
            return 'Advanced'
        elif avg_score >= 70 and accuracy >= 70:
            return 'Intermediate'
        elif avg_score >= 60 and accuracy >= 60:
            return 'Developing'
        else:
            return 'Beginner'
    
    def _get_activity_timeline(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get daily activity for the last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get quiz sessions grouped by date
        results = db.session.query(
            func.date(QuizSession.completed_at).label('date'),
            func.count(QuizSession.id).label('quizzes'),
            func.avg(QuizSession.score).label('avg_score'),
            func.sum(QuizSession.total_questions).label('questions')
        ).filter(
            QuizSession.user_id == user_id,
            QuizSession.completed_at >= start_date,
            QuizSession.completed_at.isnot(None)
        ).group_by(func.date(QuizSession.completed_at)).all()
        
        # Create timeline with all dates (limit to avoid infinite loops)
        timeline = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        # Convert results to dict for easy lookup
        activity_by_date = {result.date: result for result in results}
        
        # Safety limit to prevent infinite loops
        max_days = 30
        day_count = 0
        
        while current_date <= end_date and day_count < max_days:
            activity = activity_by_date.get(current_date)
            if activity:
                timeline.append({
                    'date': current_date.isoformat(),
                    'quizzes': int(activity.quizzes),
                    'avg_score': round(float(activity.avg_score or 0), 1),
                    'questions': int(activity.questions or 0)
                })
            else:
                timeline.append({
                    'date': current_date.isoformat(),
                    'quizzes': 0,
                    'avg_score': 0,
                    'questions': 0
                })
            current_date += timedelta(days=1)
            day_count += 1
        
        return timeline
    
    def _identify_weak_areas(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Identify areas where user needs improvement"""
        # Get questions answered incorrectly multiple times
        weak_questions = db.session.query(
            Question.id,
            Question.question,
            Question.category,
            Question.subcategory,
            func.count(QuizResponse.id).label('attempts'),
            func.sum(case((QuizResponse.is_correct == False, 1), else_=0)).label('incorrect_count')
        ).join(
            QuizResponse, Question.id == QuizResponse.question_id
        ).join(
            QuizSession, QuizResponse.session_id == QuizSession.id
        ).filter(
            QuizSession.user_id == user_id
        ).group_by(
            Question.id, Question.question, Question.category, Question.subcategory
        ).having(
            func.count(QuizResponse.id) >= 2  # At least 2 attempts
        ).order_by(
            desc(func.sum(case((QuizResponse.is_correct == False, 1), else_=0)))
        ).limit(limit).all()
        
        weak_areas = []
        for result in weak_questions:
            error_rate = (result.incorrect_count / result.attempts) * 100
            weak_areas.append({
                'question_id': result.id,
                'question_text': result.question[:100] + '...' if len(result.question) > 100 else result.question,
                'category': result.category,
                'subcategory': result.subcategory,
                'attempts': result.attempts,
                'error_rate': round(error_rate, 1)
            })
        
        return weak_areas
    
    def _calculate_mastery_levels(self, user_id: int) -> Dict:
        """Calculate overall mastery levels"""
        category_performance = self._calculate_category_performance(user_id)
        
        if not category_performance:
            return {
                'overall_level': 'Beginner',
                'categories': {},
                'progress_to_next': 0
            }
        
        # Calculate overall mastery
        avg_score = sum(cat['avg_score'] for cat in category_performance) / len(category_performance)
        total_sessions = sum(cat['sessions'] for cat in category_performance)
        
        overall_level = self._calculate_mastery_level(total_sessions, avg_score, avg_score)
        
        # Calculate progress to next level
        progress_to_next = self._calculate_progress_to_next_level(total_sessions, avg_score)
        
        categories = {cat['category']: cat['mastery_level'] for cat in category_performance}
        
        return {
            'overall_level': overall_level,
            'categories': categories,
            'progress_to_next': progress_to_next
        }
    
    def _calculate_progress_to_next_level(self, sessions: int, avg_score: float) -> int:
        """Calculate percentage progress to next mastery level"""
        if avg_score >= 90 and sessions >= 10:
            return 100  # Already at Expert level
        elif avg_score >= 80 and sessions >= 5:
            # Progress to Expert
            score_progress = min((avg_score - 80) / 10 * 50, 50)
            session_progress = min((sessions - 5) / 5 * 50, 50)
            return min(int(score_progress + session_progress), 99)
        elif avg_score >= 70:
            # Progress to Advanced
            score_progress = min((avg_score - 70) / 10 * 60, 60)
            session_progress = min(sessions / 5 * 40, 40)
            return min(int(score_progress + session_progress), 99)
        elif avg_score >= 60:
            # Progress to Intermediate
            return min(int((avg_score - 60) / 10 * 100), 99)
        else:
            # Progress to Developing
            return min(int(avg_score / 60 * 100), 99)
    
    def update_user_progress(self, user_id: int, quiz_session: QuizSession):
        """Update user progress after completing a quiz"""
        progress = UserProgress.query.filter_by(user_id=user_id).first()
        if not progress:
            progress = self._initialize_user_progress(user_id)
        
        # Update basic counts
        progress.total_quizzes_taken += 1
        progress.total_questions_answered += quiz_session.total_questions or 0
        progress.correct_answers += quiz_session.correct_answers or 0
        
        # Update streak
        today = datetime.utcnow().date()
        if progress.last_activity_date:
            days_diff = (today - progress.last_activity_date).days
            if days_diff == 1:
                # Consecutive day
                progress.current_streak_days += 1
                progress.longest_streak_days = max(
                    progress.longest_streak_days, 
                    progress.current_streak_days
                )
            elif days_diff > 1:
                # Streak broken
                progress.current_streak_days = 1
        else:
            # First activity
            progress.current_streak_days = 1
            progress.longest_streak_days = 1
        
        progress.last_activity_date = today
        
        db.session.commit()