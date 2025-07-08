# app/learning/services.py
from app import db
from app.learning.models import (
    LearningModule, LearningSubmodule, VideoShorts, 
    UserLearningProgress, UserShortsProgress, ContentAnalytics
)
from datetime import datetime, date, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class LearningService:
    """Service class for learning-related business logic"""
    
    @staticmethod
    def get_user_modules_progress(user):
        """Get all modules with user progress information"""
        try:
            modules = LearningModule.query.filter_by(is_active=True).order_by(LearningModule.module_number).all()
            modules_data = []
            
            for module in modules:
                # Get user progress for this module
                progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    module_id=module.id,
                    progress_type='module'
                ).first()
                
                # Calculate completion percentage
                completion_rate = module.get_completion_rate_for_user(user.id)
                
                modules_data.append({
                    'module': module,
                    'progress': progress,
                    'completion_rate': completion_rate,
                    'is_locked': LearningService._is_module_locked(module, user),
                    'next_submodule': LearningService._get_next_submodule(module, user)
                })
            
            return modules_data
        except Exception as e:
            logger.error(f"Error getting user modules progress: {str(e)}")
            return []
    
    @staticmethod
    def get_user_learning_stats(user):
        """Get comprehensive learning statistics for user"""
        try:
            stats = {}
            
            # Total time spent learning
            total_time = db.session.query(func.sum(UserLearningProgress.time_spent_minutes)).filter_by(
                user_id=user.id
            ).scalar() or 0
            
            # Modules completed
            modules_completed = UserLearningProgress.query.filter_by(
                user_id=user.id,
                progress_type='module',
                status='completed'
            ).count()
            
            # Submodules completed
            submodules_completed = UserLearningProgress.query.filter_by(
                user_id=user.id,
                progress_type='submodule',
                status='completed'
            ).count()
            
            # Videos watched
            videos_watched = UserShortsProgress.query.filter_by(
                user_id=user.id,
                watch_status='completed'
            ).count()
            
            # Current streak (days of consecutive learning)
            current_streak = LearningService._calculate_learning_streak(user)
            
            stats = {
                'total_time_minutes': total_time,
                'modules_completed': modules_completed,
                'submodules_completed': submodules_completed,
                'videos_watched': videos_watched,
                'current_streak_days': current_streak,
                'total_modules': LearningModule.query.filter_by(is_active=True).count()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user learning stats: {str(e)}")
            return {}
    
    @staticmethod
    def _calculate_learning_streak(user):
        """Calculate consecutive days of learning"""
        # This is a simplified version - could be more sophisticated
        recent_dates = db.session.query(func.date(UserLearningProgress.last_accessed)).filter_by(
            user_id=user.id
        ).filter(
            UserLearningProgress.last_accessed >= datetime.now() - timedelta(days=30)
        ).distinct().order_by(func.date(UserLearningProgress.last_accessed).desc()).all()
        
        if not recent_dates:
            return 0
        
        streak = 0
        expected_date = date.today()
        
        for (activity_date,) in recent_dates:
            if activity_date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break
        
        return streak
    
    @staticmethod
    def _is_module_locked(module, user):
        """Check if module is locked based on prerequisites"""
        if not module.prerequisites:
            return False
        
        # Check if all prerequisite modules are completed
        for prereq_id in module.prerequisites:
            completed = UserLearningProgress.query.filter_by(
                user_id=user.id,
                module_id=prereq_id,
                progress_type='module',
                status='completed'
            ).first()
            
            if not completed:
                return True
        
        return False
    
    @staticmethod
    def _get_next_submodule(module, user):
        """Get the next submodule user should study in this module"""
        submodules = LearningSubmodule.query.filter_by(
            module_id=module.id,
            is_active=True
        ).order_by(LearningSubmodule.submodule_number).all()
        
        for submodule in submodules:
            progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                submodule_id=submodule.id,
                progress_type='submodule'
            ).first()
            
            if not progress or progress.status != 'completed':
                return submodule
        
        return None  # All submodules completed
    
    # ===== THEORY MODE SPECIFIC METHODS =====
    
    @staticmethod
    def get_module_details(module_id, user):
        """Get detailed module information with user progress"""
        try:
            module = LearningModule.query.filter_by(id=module_id, is_active=True).first()
            if not module:
                return None
            
            # Get user progress for this module
            progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                module_id=module.id,
                progress_type='module'
            ).first()
            
            # Get completion rate
            completion_rate = module.get_completion_rate_for_user(user.id)
            
            return {
                'id': module.id,
                'module_number': module.module_number,
                'title': module.title,
                'description': module.description,
                'estimated_hours': module.estimated_hours,
                'learning_objectives': module.learning_objectives,
                'completion_percentage': completion_rate,
                'status': progress.status if progress else 'not_started',
                'time_spent': progress.time_spent_minutes if progress else 0
            }
        except Exception as e:
            logger.error(f"Error getting module details for {module_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_submodules_progress(module_id, user):
        """Get all submodules for a module with user progress"""
        try:
            submodules = LearningSubmodule.query.filter_by(
                module_id=module_id,
                is_active=True
            ).order_by(LearningSubmodule.submodule_number).all()
            
            submodules_data = []
            for submodule in submodules:
                # Get user progress
                progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    submodule_id=submodule.id,
                    progress_type='submodule'
                ).first()
                
                submodules_data.append({
                    'id': submodule.id,
                    'submodule_number': submodule.submodule_number,
                    'title': submodule.title,
                    'description': submodule.description,
                    'estimated_minutes': submodule.estimated_minutes,
                    'difficulty_level': submodule.difficulty_level,
                    'has_quiz': submodule.has_quiz,
                    'has_video_shorts': submodule.has_video_shorts,
                    'shorts_count': submodule.shorts_count,
                    'status': progress.status if progress else 'not_started',
                    'completion_percentage': progress.completion_percentage if progress else 0.0,
                    'time_spent': progress.time_spent_minutes if progress else 0
                })
            
            return submodules_data
        except Exception as e:
            logger.error(f"Error getting submodules progress for module {module_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_submodule_content(submodule_id, user):
        """Get submodule content with progress tracking"""
        try:
            from app.learning.content_manager import ContentManager
            
            # Find submodule by number (e.g., 1.1)
            submodule = LearningSubmodule.query.filter_by(
                submodule_number=submodule_id,
                is_active=True
            ).first()
            
            if not submodule:
                return None
            
            # Get content from files
            content_data = ContentManager.get_submodule_content(submodule_id)
            
            # Get user progress
            progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                submodule_id=submodule.id,
                progress_type='submodule'
            ).first()
            
            return {
                'submodule': submodule,
                'content': content_data.get('content', ''),
                'summary': content_data.get('summary', ''),
                'metadata': content_data.get('metadata', {}),
                'progress': progress,
                'module': submodule.module
            }
        except Exception as e:
            logger.error(f"Error getting submodule content for {submodule_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_submodule_shorts(submodule_id, user):
        """Get video shorts for a submodule with user progress"""
        try:
            # Find submodule by number (e.g., 1.1)
            submodule = LearningSubmodule.query.filter_by(
                submodule_number=submodule_id,
                is_active=True
            ).first()
            
            if not submodule:
                return None
            
            # Get shorts for this submodule
            shorts = VideoShorts.query.filter_by(
                submodule_id=submodule.id,
                is_active=True
            ).order_by(VideoShorts.sequence_order).all()
            
            shorts_data = []
            for short in shorts:
                # Get user progress for this short
                progress = UserShortsProgress.query.filter_by(
                    user_id=user.id,
                    shorts_id=short.id
                ).first()
                
                shorts_data.append({
                    'short': short,
                    'progress': progress
                })
            
            return {
                'submodule': submodule,
                'shorts': shorts_data,
                'total_count': len(shorts)
            }
        except Exception as e:
            logger.error(f"Error getting submodule shorts for {submodule_id}: {str(e)}")
            return None
    
    @staticmethod
    def track_content_access(user, submodule_id, content_type):
        """Track that user accessed content"""
        try:
            # Find the actual submodule by module_id and calculate submodule_id
            # This is a simplified approach - in production you'd want better ID handling
            module_id = int(submodule_id)
            submodule = LearningSubmodule.query.filter_by(
                module_id=module_id,
                is_active=True
            ).first()
            
            if not submodule:
                return
            
            # Get or create progress record
            progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                submodule_id=submodule.id,
                progress_type='submodule'
            ).first()
            
            if not progress:
                progress = UserLearningProgress(
                    user_id=user.id,
                    module_id=submodule.module_id,
                    submodule_id=submodule.id,
                    progress_type='submodule',
                    status='in_progress',
                    started_at=datetime.utcnow()
                )
                db.session.add(progress)
            
            # Mark content as viewed
            if content_type == 'content':
                progress.content_viewed = True
            elif content_type == 'summary':
                progress.summary_viewed = True
            
            progress.last_accessed = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error tracking content access: {str(e)}")
            db.session.rollback()
