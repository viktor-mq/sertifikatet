# app/services/learning_service.py
from datetime import datetime
from sqlalchemy import func
from .. import db
from ..models import (
    LearningModules, LearningModuleItem, UserLearningModule,
    Question, QuizSession, VideoProgress, GameSession, QuizResponse
)


class LearningService:
    """Service for managing learning module and progression."""
    
    @staticmethod
    def create_default_learning_modules():
        """Create initial learning modules for the platform."""
        modules_data = [
            {
                'name': 'Grunnleggende Trafikkregler',
                'description': 'Start din reise mot førerkortet med de mest grunnleggende trafikkreglene. Perfekt for nybegynnere!',
                'estimated_hours': 10,
                'difficulty_level': 1,
                'is_recommended': True,
                'items': [
                    {'type': 'quiz', 'category': 'Trafikkregler', 'order': 1, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Vikeplikt', 'order': 2, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Fartsgrenser', 'order': 3, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Forbikjøring', 'order': 4, 'mandatory': False},
                ]
            },
            {
                'name': 'Trafikkskilt Mestring',
                'description': 'Lær alle trafikkskiltene grundig med progressive øvelser og tester.',
                'estimated_hours': 8,
                'difficulty_level': 2,
                'is_recommended': True,
                'items': [
                    {'type': 'quiz', 'category': 'Fareskilt', 'order': 1, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Forbudsskilt', 'order': 2, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Påbudsskilt', 'order': 3, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Opplysningsskilt', 'order': 4, 'mandatory': False},
                    {'type': 'quiz', 'category': 'Vegvisningsskilt', 'order': 5, 'mandatory': False},
                ]
            },
            {
                'name': 'Sikker Kjøring',
                'description': 'Fokus på sikkerhet, risikovurdering og defensive kjøreteknikker.',
                'estimated_hours': 12,
                'difficulty_level': 2,
                'is_recommended': False,
                'items': [
                    {'type': 'quiz', 'category': 'Sikkerhet', 'order': 1, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Førstehjelp', 'order': 2, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Risikovurdering', 'order': 3, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Kjøreteknikk', 'order': 4, 'mandatory': False},
                ]
            },
            {
                'name': 'Eksamensforberedelse',
                'description': 'Intensivt program for deg som skal opp til teoriprøven snart. Dekker alle temaer!',
                'estimated_hours': 20,
                'difficulty_level': 3,
                'is_recommended': True,
                'items': [
                    {'type': 'quiz', 'category': 'Trafikkregler', 'order': 1, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Trafikkskilt', 'order': 2, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Sikkerhet', 'order': 3, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Miljø', 'order': 4, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Teknisk', 'order': 5, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Blandede spørsmål', 'order': 6, 'mandatory': False},
                ]
            },
            {
                'name': 'Miljøvennlig Kjøring',
                'description': 'Lær hvordan du kan kjøre mer miljøvennlig og spare drivstoff.',
                'estimated_hours': 5,
                'difficulty_level': 1,
                'is_recommended': False,
                'items': [
                    {'type': 'quiz', 'category': 'Miljø', 'order': 1, 'mandatory': True},
                    {'type': 'quiz', 'category': 'Økonomi', 'order': 2, 'mandatory': False},
                ]
            }
        ]
        
        created_modules = []
        
        for module_data in module_data:
            # Check if module already exists
            existing = LearningModules.query.filter_by(name=module_data['name']).first()
            if existing:
                continue
                
            # Create learning module
            module = LearningModules(
                name=module_data['name'],
                description=module_data['description'],
                estimated_hours=module_data['estimated_hours'],
                difficulty_level=module_data['difficulty_level'],
                is_recommended=module_data['is_recommended']
            )
            db.session.add(module)
            db.session.flush()  # Get the ID
            
            # Create module items
            for item_data in module_data['items']:
                item = LearningModuleItem(
                    module_id=module.id,
                    item_type=item_data['type'],
                    item_id=item_data['category'],  # Using category as identifier
                    order_index=item_data['order'],
                    is_mandatory=item_data['mandatory']
                )
                db.session.add(item)
            
            created_modules.append(module)
        
        db.session.commit()
        return created_modules
    
    @staticmethod
    def calculate_module_progress(user_id, model_id):
        """Calculate user's progress in a learning module."""
        module = LearningModules.query.get(model_id)
        if not module:
            return 0
            
        total_items = len(module.items)
        if total_items == 0:
            return 0
            
        completed_items = 0
        
        for item in module.items:
            if LearningService.is_item_completed(user_id, item):
                completed_items += 1
        
        return int((completed_items / total_items) * 100)
    
    @staticmethod
    def is_item_completed(user_id, item):
        """Check if a learning module item is completed by the user."""
        if item.item_type == 'quiz':
            # Check if user has passed quiz in this category
            passed_quiz = QuizSession.query.filter_by(
                user_id=user_id,
                category=item.item_id
            ).filter(
                QuizSession.score >= 80,  # 80% pass rate
                QuizSession.quiz_type == 'learning_module'
            ).first()
            return passed_quiz is not None
            
        elif item.item_type == 'video':
            # Check if user has completed the video
            video_progress = VideoProgress.query.filter_by(
                user_id=user_id,
                video_id=item.item_id,
                completed=True
            ).first()
            return video_progress is not None
            
        elif item.item_type == 'game':
            # Check if user has completed the game scenario
            game_session = GameSession.query.filter_by(
                user_id=user_id,
                scenario_id=item.item_id,
                completed=True
            ).first()
            return game_session is not None
            
        return False
    
    @staticmethod
    def get_next_item(user_id, model_id):
        """Get the next item to complete in a learning module."""
        module = LearningModules.query.get(model_id)
        if not module:
            return None
            
        for item in module.items:
            if not LearningService.is_item_completed(user_id, item):
                # Check if prerequisites are met
                if LearningService.are_prerequisites_met(user_id, module, item):
                    return item
        
        return None  # All items completed
    
    @staticmethod
    def are_prerequisites_met(user_id, module, item):
        """Check if all mandatory prerequisite items are completed."""
        for prereq_item in module.items:
            if prereq_item.order_index >= item.order_index:
                break
            if prereq_item.is_mandatory and not LearningService.is_item_completed(user_id, prereq_item):
                return False
        return True
    
    @staticmethod
    def update_module_progress(user_id, model_id):
        """Update user's progress in a learning module."""
        user_module = UserLearningModule.query.filter_by(
            user_id=user_id,
            model_id=model_id
        ).first()
        
        if not user_module:
            return None
            
        # Calculate new progress
        progress = LearningService.calculate_module_progress(user_id, model_id)
        user_module.progress_percentage = progress
        
        # Check if completed
        if progress >= 100 and not user_module.completed_at:
            user_module.completed_at = datetime.utcnow()
        
        db.session.commit()
        return user_module
    
    @staticmethod
    def get_recommended_modules(user_id, limit=3):
        """Get recommended learning modules for a user based on their performance."""
        # Get user's weak areas
        weak_categories = db.session.query(
            Question.category,
            func.avg(QuizResponse.is_correct).label('accuracy')
        ).join(
            QuizResponse, Question.id == QuizResponse.question_id
        ).join(
            QuizSession, QuizResponse.session_id == QuizSession.id
        ).filter(
            QuizSession.user_id == user_id
        ).group_by(Question.category).having(
            func.avg(QuizResponse.is_correct) < 0.7
        ).all()
        
        if not weak_categories:
            # Return beginner-friendly modules
            return LearningModules.query.filter_by(
                difficulty_level=1,
                is_recommended=True
            ).limit(limit).all()
        
        # Find modules that cover weak categories
        weak_category_names = [cat[0] for cat in weak_categories]
        
        recommended_modules = []
        all_modules = LearningModules.query.all()
        
        for module in all_modules:
            module_categories = [item.item_id for item in module.items if item.item_type == 'quiz']
            overlap = set(module_categories).intersection(weak_category_names)
            
            if overlap:
                recommended_modules.append((module, len(overlap)))
        
        # Sort by coverage and return top modules
        recommended_modules.sort(key=lambda x: x[1], reverse=True)
        return [module for module, _ in recommended_modules[:limit]]
