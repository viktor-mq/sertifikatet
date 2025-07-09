# app/learning/models.py (Simplified - using existing models via services)
from datetime import datetime
from app import db

# We'll use existing models and query them with filters rather than creating new model classes
# This avoids table conflicts while providing the theory learning functionality

class TheoryService:
    """Service class for theory learning using existing models"""
    
    @staticmethod
    def get_theory_modules():
        """Get all theory learning modules"""
        # Import here to avoid circular imports
        from app.models import LearningModules
        
        return LearningModules.query.order_by(LearningModules.id).all()
    
    @staticmethod
    def get_module_by_number(module_number):
        """Get theory module by number (e.g., 1.1)"""
        from app.models import LearningModules
        
        return LearningModules.query.filter_by(id=int(module_number)).first()
    
    @staticmethod
    def get_theory_shorts(module_number):
        """Get all theory shorts for a module"""
        from app.models import Video
        
        return Video.query.filter_by(
            category=f'theory_module_{module_number}'
        ).order_by(Video.order_index).all()
    
    @staticmethod
    def get_user_progress(user_id, module_number):
        """Get user progress for a theory module"""
        from app.models import UserLearningModule
        
        module = TheoryService.get_module_by_number(module_number)
        if not module:
            return None
            
        return UserLearningModule.query.filter_by(
            user_id=user_id,
            model_id=module.id
        ).first()
    
    @staticmethod
    def get_video_progress(user_id, video_id):
        """Get user progress for a theory video"""
        from app.models import VideoProgress
        
        return VideoProgress.query.filter_by(
            user_id=user_id,
            video_id=video_id
        ).first()
