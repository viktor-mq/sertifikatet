# app/learning/services.py
from app import db
from app.learning.models import TheoryService
from datetime import datetime, date, timedelta
from sqlalchemy import func
import logging
import yaml
import os

logger = logging.getLogger(__name__)


class LearningService:
    """Service class for learning-related business logic"""
    
    @staticmethod
    def _get_submodule_count(module_id):
        """Get submodule count from module.yaml file"""
        try:
            module_dirs = [
                "1.basic_traffic_theory",
                "2.road_signs_and_markings", 
                "3.vehicles_and_technology",
                "4.human_factors_in_traffic",
                "5.practice_driving_and_final_test"
            ]
            
            if 1 <= module_id <= len(module_dirs):
                module_dir = module_dirs[module_id - 1]
                module_path = f"learning/{module_dir}/module.yaml"
                
                if os.path.exists(module_path):
                    with open(module_path, 'r', encoding='utf-8') as f:
                        module_data = yaml.safe_load(f)
                        return len(module_data.get('submodules', []))
            
            return 5  # Default fallback
        except Exception as e:
            logger.warning(f"Could not get submodule count for module {module_id}: {e}")
            return 5
    
    @staticmethod
    def enroll_user_in_module(user, module_id):
        """Enroll user in a module (create UserLearningModule record)"""
        try:
            from app.models import UserLearningModule
            
            # Check if already enrolled
            existing = UserLearningModule.query.filter_by(
                user_id=user.id,
                module_id=module_id
            ).first()
            
            if not existing:
                # Create new enrollment
                user_module = UserLearningModule(
                    user_id=user.id,
                    module_id=module_id,
                    progress_percentage=0,
                    started_at=datetime.utcnow()
                )
                db.session.add(user_module)
                db.session.commit()
                
                logger.info(f"User {user.id} enrolled in module {module_id}")
                return True
            
            return False  # Already enrolled
        except Exception as e:
            logger.error(f"Error enrolling user {user.id} in module {module_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_modules_progress(user):
        """Get all modules with user progress information from database"""
        try:
            # Import models from main models file
            from app.models import LearningModules, UserLearningModule, UserLearningProgress
            
            # Get all learning modules from database
            modules = LearningModules.query.filter_by(is_active=True).order_by(LearningModules.module_number).all()
            
            modules_data = []
            for module in modules:
                # Get user module enrollment
                user_module = UserLearningModule.query.filter_by(
                    user_id=user.id,
                    module_id=module.id
                ).first()
                
                # Calculate real progress from submodules
                total_submodules = len(module.submodules) if module.submodules else 0
                
                if total_submodules > 0:
                    # Count completed submodules
                    completed_submodules = UserLearningProgress.query.filter_by(
                        user_id=user.id,
                        module_id=module.id,
                        progress_type='content',
                        status='completed'
                    ).count()
                    
                    # Count in-progress submodules
                    in_progress_submodules = UserLearningProgress.query.filter_by(
                        user_id=user.id,
                        module_id=module.id,
                        progress_type='content',
                        status='in_progress'
                    ).count()
                    
                    # Calculate completion percentage
                    completion_percentage = int((completed_submodules / total_submodules) * 100)
                    
                    # Determine status
                    if completed_submodules == total_submodules:
                        status = 'completed'
                    elif completed_submodules > 0 or in_progress_submodules > 0:
                        status = 'in_progress'
                    else:
                        status = 'not_started'
                else:
                    # No submodules found - use fallback logic
                    completion_percentage = 0
                    status = 'not_started'
                    total_submodules = LearningService._get_submodule_count(module.id)
                
                # Check if user is enrolled
                is_enrolled = user_module is not None
                
                # Get last access time
                last_progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    module_id=module.id
                ).order_by(UserLearningProgress.last_accessed.desc()).first()
                
                last_accessed = last_progress.last_accessed if last_progress else None
                
                module_data = {
                    'id': module.id,
                    'title': module.title,
                    'description': module.description,
                    'estimated_hours': module.estimated_hours or 3,
                    'difficulty_level': 1,  # Default difficulty for modules
                    'is_recommended': module.id == 1,  # First module is recommended
                    'completion_percentage': completion_percentage,
                    'progress': completion_percentage,
                    'status': status,
                    'total_items': total_submodules,
                    'is_enrolled': is_enrolled,
                    'last_accessed': last_accessed,
                    'module_number': module.module_number
                }
                
                modules_data.append(module_data)
            
            # If no modules found in database, fall back to mock data
            if not modules_data:
                logger.warning("No modules found in database, using mock data")
                return LearningService._get_mock_modules_data(user)
            
            logger.info(f"Retrieved {len(modules_data)} modules with real progress data")
            return modules_data
            
        except Exception as e:
            logger.error(f"Error getting user modules progress: {str(e)}")
            # Return mock data as fallback
            return LearningService._get_mock_modules_data(user)
    
    @staticmethod
    def _get_mock_modules_data(user):
        """Fallback mock data if database fails"""
        # Check if user has any progress to show some realistic mock data
        try:
            from app.models import UserLearningProgress
            
            has_any_progress = UserLearningProgress.query.filter_by(user_id=user.id).first() is not None
            
            # Show some progress for first module if user has any activity
            first_module_progress = 25 if has_any_progress else 0
            first_module_status = 'in_progress' if has_any_progress else 'not_started'
            
        except Exception:
            first_module_progress = 0
            first_module_status = 'not_started'
        
        return [
            {
                'id': 1,
                'title': 'Grunnleggende Trafikklære',
                'description': 'Lær grunnleggende trafikkskilt og regler',
                'estimated_hours': 3,
                'difficulty_level': 1,
                'is_recommended': True,
                'completion_percentage': first_module_progress,
                'progress': first_module_progress,
                'status': first_module_status,
                'total_items': 5,
                'is_enrolled': has_any_progress,
                'last_accessed': None,
                'module_number': 1
            },
            {
                'id': 2,
                'title': 'Skilt og Oppmerking',
                'description': 'Gjenkjenn og forstå trafikkskilt',
                'estimated_hours': 3,
                'difficulty_level': 2,
                'is_recommended': False,
                'completion_percentage': 0,
                'progress': 0,
                'status': 'not_started',
                'total_items': 5,
                'is_enrolled': False,
                'last_accessed': None,
                'module_number': 2
            },
            {
                'id': 3,
                'title': 'Kjøretøy og Teknologi',
                'description': 'Forstå bremselengde, sikt og kjøretøyets tekniske aspekter',
                'estimated_hours': 2,
                'difficulty_level': 3,
                'is_recommended': False,
                'completion_percentage': 0,
                'progress': 0,
                'status': 'not_started',
                'total_items': 5,
                'is_enrolled': False,
                'last_accessed': None,
                'module_number': 3
            },
            {
                'id': 4,
                'title': 'Mennesket i Trafikken',
                'description': 'Lær om alkohol, rus, trøtthet og menneskelige faktorer',
                'estimated_hours': 2,
                'difficulty_level': 3,
                'is_recommended': False,
                'completion_percentage': 0,
                'progress': 0,
                'status': 'not_started',
                'total_items': 4,
                'is_enrolled': False,
                'last_accessed': None,
                'module_number': 4
            },
            {
                'id': 5,
                'title': 'Øvingskjøring og Avsluttende Test',
                'description': 'Øvingskjøring, eksamenstrening og forberedelse til teoriprøven',
                'estimated_hours': 2,
                'difficulty_level': 4,
                'is_recommended': False,
                'completion_percentage': 0,
                'progress': 0,
                'status': 'not_started',
                'total_items': 4,
                'is_enrolled': False,
                'last_accessed': None,
                'module_number': 5
            }
        ]
    
    @staticmethod
    def get_user_learning_stats(user):
        """Get comprehensive learning statistics for user from database"""
        try:
            from app.models import UserLearningProgress, UserLearningModule
            
            # Get modules completed
            modules_completed = UserLearningModule.query.filter_by(
                user_id=user.id
            ).filter(UserLearningModule.progress_percentage >= 100).count()
            
            # Get total time spent (sum of time_spent_minutes from all progress records)
            total_time_result = db.session.query(func.sum(UserLearningProgress.time_spent_minutes)).filter_by(
                user_id=user.id
            ).scalar()
            total_time_minutes = total_time_result if total_time_result else 0
            
            # Get shorts watched (sum of shorts_watched from all progress records)
            shorts_watched_result = db.session.query(func.sum(UserLearningProgress.shorts_watched)).filter_by(
                user_id=user.id
            ).scalar()
            shorts_watched = shorts_watched_result if shorts_watched_result else 0
            
            # Calculate current streak (simplified - based on recent activity)
            from datetime import datetime, timedelta
            recent_activity = UserLearningProgress.query.filter_by(
                user_id=user.id
            ).filter(
                UserLearningProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            current_streak = min(recent_activity, 7)  # Max 7 day streak
            
            # Calculate overall progress (percentage of all content completed)
            total_progress_records = UserLearningProgress.query.filter_by(
                user_id=user.id,
                progress_type='content'
            ).count()
            
            completed_progress_records = UserLearningProgress.query.filter_by(
                user_id=user.id,
                progress_type='content',
                status='completed'
            ).count()
            
            overall_progress = int((completed_progress_records / total_progress_records) * 100) if total_progress_records > 0 else 0
            
            stats = {
                'modules_completed': modules_completed,
                'total_time_minutes': total_time_minutes,
                'shorts_watched': shorts_watched,
                'current_streak': current_streak,
                'overall_progress': overall_progress,
                'total_content_accessed': total_progress_records,
                'content_completed': completed_progress_records
            }
            
            logger.info(f"Retrieved learning stats for user {user.id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user learning stats: {str(e)}")
            # Return basic stats on error
            return {
                'modules_completed': 0,
                'total_time_minutes': 0,
                'shorts_watched': 0,
                'current_streak': 0,
                'overall_progress': 0,
                'total_content_accessed': 0,
                'content_completed': 0
            }
    
    @staticmethod
    def get_recommendations(user):
        """Get recommended next steps for user based on progress"""
        try:
            from app.models import UserLearningProgress, LearningModules
            
            recommendations = []
            
            # Get user's current progress
            current_progress = UserLearningProgress.query.filter_by(
                user_id=user.id
            ).order_by(UserLearningProgress.last_accessed.desc()).first()
            
            if current_progress:
                # User has some progress - recommend next logical step
                if current_progress.status == 'in_progress':
                    # Continue current submodule
                    recommendations.append({
                        'type': 'continue',
                        'title': 'Fortsett der du slapp',
                        'description': 'Fullfør innholdet du startet på',
                        'priority': 'high',
                        'url': '/learning/continue',
                        'icon': 'fas fa-play'
                    })
                
                # Check if user has completed content but not shorts
                if current_progress.content_viewed and current_progress.shorts_watched == 0:
                    recommendations.append({
                        'type': 'shorts',
                        'title': 'Se videoleksjoner',
                        'description': 'Forstå innholdet bedre med korte videoer',
                        'priority': 'medium',
                        'url': f'/learning/shorts/{current_progress.submodule_id}',
                        'icon': 'fas fa-play-circle'
                    })
                
                # Recommend next module if current is completed
                completed_modules = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    progress_type='content',
                    status='completed'
                ).count()
                
                if completed_modules > 0:
                    next_module = LearningModules.query.filter(
                        LearningModules.module_number > completed_modules
                    ).order_by(LearningModules.module_number).first()
                    
                    if next_module:
                        recommendations.append({
                            'type': 'next_module',
                            'title': f'Start {next_module.title}',
                            'description': 'Neste modul i læringsveien',
                            'priority': 'medium',
                            'url': f'/learning/module/{next_module.id}',
                            'icon': 'fas fa-arrow-right'
                        })
            
            else:
                # New user - recommend starting with first module
                first_module = LearningModules.query.filter_by(
                    module_number=1,
                    is_active=True
                ).first()
                
                if first_module:
                    recommendations.append({
                        'type': 'start',
                        'title': 'Start med grunnleggende trafikk',
                        'description': 'Begynn læringsveien med det første modulet',
                        'priority': 'high',
                        'url': f'/learning/module/{first_module.id}',
                        'icon': 'fas fa-play'
                    })
            
            # Always recommend practice quiz
            recommendations.append({
                'type': 'quiz',
                'title': 'Øv med quiz',
                'description': 'Test kunnskapen din med øvingsspørsmål',
                'priority': 'low',
                'url': '/quiz',
                'icon': 'fas fa-question-circle'
            })
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user.id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            # Return basic recommendation on error
            return [{
                'type': 'start',
                'title': 'Start læringsveien',
                'description': 'Begynn med det første modulet',
                'priority': 'high',
                'url': '/learning/dashboard',
                'icon': 'fas fa-play'
            }]
    
    @staticmethod
    def get_module_details(module_id, user):
        """Get detailed module information with user progress from database"""
        try:
            from app.models import LearningModules, UserLearningModule, UserLearningProgress
            
            # Get module from database
            module = LearningModules.query.filter_by(
                id=module_id,
                is_active=True
            ).first()
            
            if not module:
                # Module not found in database, return None
                logger.warning(f"Module {module_id} not found in database")
                return None
            
            # Get user enrollment
            user_module = UserLearningModule.query.filter_by(
                user_id=user.id,
                module_id=module.id
            ).first()
            
            # Calculate progress from submodules
            total_submodules = len(module.submodules) if module.submodules else 0
            
            if total_submodules > 0:
                # Count completed submodules
                completed_submodules = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    module_id=module.id,
                    progress_type='content',
                    status='completed'
                ).count()
                
                # Calculate completion percentage
                completion_percentage = int((completed_submodules / total_submodules) * 100)
                
                # Determine status
                if completed_submodules == total_submodules:
                    status = 'completed'
                elif completed_submodules > 0:
                    status = 'in_progress'
                else:
                    status = 'not_started'
            else:
                # No submodules - use fallback
                completion_percentage = 0
                status = 'not_started'
                total_submodules = LearningService._get_submodule_count(module.id)
            
            # Get time spent
            total_time_result = db.session.query(func.sum(UserLearningProgress.time_spent_minutes)).filter_by(
                user_id=user.id,
                module_id=module.id
            ).scalar()
            time_spent = total_time_result if total_time_result else 0
            
            # Get last access time
            last_progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                module_id=module.id
            ).order_by(UserLearningProgress.last_accessed.desc()).first()
            
            last_accessed = last_progress.last_accessed if last_progress else None
            
            module_details = {
                'id': module.id,
                'module_number': module.module_number,
                'title': module.title,
                'description': module.description,
                'estimated_hours': module.estimated_hours or 3,
                'completion_percentage': completion_percentage,
                'status': status,
                'time_spent': time_spent,
                'total_submodules': total_submodules,
                'completed_submodules': completed_submodules if total_submodules > 0 else 0,
                'is_enrolled': user_module is not None,
                'last_accessed': last_accessed,
                'started_at': user_module.started_at if user_module else None,
                'completed_at': user_module.completed_at if user_module else None,
                'learning_objectives': module.get_learning_objectives_list(),
                'prerequisites': module.get_prerequisites_list()
            }
            
            logger.info(f"Retrieved module details for {module_id} with real progress data")
            return module_details
            
        except Exception as e:
            logger.error(f"Error getting module details for {module_id}: {str(e)}")
            # Return mock data as fallback
            return LearningService._get_mock_module_details(module_id)
    
    @staticmethod
    def _get_mock_module_details(module_id):
        """Fallback mock module details"""
        module_titles = {
            1: 'Grunnleggende Trafikklære',
            2: 'Skilt og Oppmerking',
            3: 'Kjøretøy og Teknologi',
            4: 'Mennesket i Trafikken',
            5: 'Øvingskjøring og Avsluttende Test'
        }
        
        module_descriptions = {
            1: 'Lær grunnleggende trafikkskilt og regler',
            2: 'Gjenkjenn og forstå trafikkskilt',
            3: 'Forstå bremselengde, sikt og kjøretøyets tekniske aspekter',
            4: 'Lær om alkohol, rus, trøtthet og menneskelige faktorer',
            5: 'Øvingskjøring, eksamenstrening og forberedelse til teoriprøven'
        }
        
        return {
            'id': module_id,
            'module_number': module_id,
            'title': module_titles.get(module_id, f'Modul {module_id}'),
            'description': module_descriptions.get(module_id, f'Beskrivelse for modul {module_id}'),
            'estimated_hours': 3,
            'completion_percentage': 0,
            'status': 'not_started',
            'time_spent': 0,
            'total_submodules': 5,
            'completed_submodules': 0,
            'is_enrolled': False,
            'last_accessed': None,
            'started_at': None,
            'completed_at': None,
            'learning_objectives': ['Læringsmål 1', 'Læringsmål 2', 'Læringsmål 3'],
            'prerequisites': []
        }
    
    @staticmethod
    def get_submodules_progress(module_id, user):
        """Get all submodules for a module with user progress from database"""
        try:
            from app.models import LearningSubmodules, UserLearningProgress
            
            # Get all submodules for this module from database
            submodules = LearningSubmodules.query.filter_by(
                module_id=module_id,
                is_active=True
            ).order_by(LearningSubmodules.submodule_number).all()
            
            submodules_data = []
            
            for submodule in submodules:
                # Get user progress for this submodule
                progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    submodule_id=submodule.id,
                    progress_type='content'
                ).first()
                
                # Calculate completion percentage and status
                completion_percentage = progress.completion_percentage if progress else 0
                status = progress.status if progress else 'not_started'
                
                # Get time spent
                time_spent = progress.time_spent_minutes if progress else 0
                
                # Check if user has viewed different content types
                content_viewed = progress.content_viewed if progress else False
                summary_viewed = progress.summary_viewed if progress else False
                
                # Check for shorts progress
                shorts_progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    submodule_id=submodule.id,
                    progress_type='shorts'
                ).first()
                
                shorts_watched = shorts_progress.shorts_watched if shorts_progress else 0
                
                submodule_data = {
                    'submodule_number': submodule.submodule_number,
                    'title': submodule.title,
                    'description': submodule.description,
                    'estimated_minutes': submodule.estimated_minutes or 30,
                    'difficulty_level': submodule.difficulty_level or 2,
                    'completion_percentage': completion_percentage,
                    'status': status,
                    'time_spent': time_spent,
                    'content_viewed': content_viewed,
                    'summary_viewed': summary_viewed,
                    'shorts_watched': shorts_watched,
                    'has_video_shorts': submodule.has_video_shorts or False,
                    'shorts_count': submodule.shorts_count or 0,
                    'has_quiz': submodule.has_quiz or False,
                    'quiz_question_count': submodule.quiz_question_count or 0,
                    'last_accessed': progress.last_accessed if progress else None,
                    'started_at': progress.started_at if progress else None,
                    'completed_at': progress.completed_at if progress else None
                }
                
                submodules_data.append(submodule_data)
            
            # If no submodules found in database, fall back to mock data for this module
            if not submodules_data:
                logger.warning(f"No submodules found for module {module_id}, using mock data")
                return LearningService._get_mock_submodules_data(module_id, user)
            
            logger.info(f"Retrieved {len(submodules_data)} submodules for module {module_id} with real progress")
            return submodules_data
            
        except Exception as e:
            logger.error(f"Error getting submodules progress for module {module_id}: {str(e)}")
            # Fall back to mock data on error
            return LearningService._get_mock_submodules_data(module_id, user)
    
    @staticmethod
    def _get_mock_submodules_data(module_id, user):
        """Fallback mock data if database query fails"""
        # Get basic progress for mock data
        try:
            from app.models import UserLearningProgress
            
            # Check if user has any progress for this module
            has_progress = UserLearningProgress.query.filter_by(
                user_id=user.id,
                module_id=module_id
            ).first() is not None
            
            # Set different mock progress based on module
            if module_id == 1 and has_progress:
                # Show some progress for module 1
                mock_progress = [
                    {'completion_percentage': 100, 'status': 'completed'},
                    {'completion_percentage': 65, 'status': 'in_progress'},
                    {'completion_percentage': 0, 'status': 'not_started'},
                    {'completion_percentage': 0, 'status': 'not_started'},
                    {'completion_percentage': 0, 'status': 'not_started'}
                ]
            else:
                # Show no progress for other modules
                mock_progress = [{'completion_percentage': 0, 'status': 'not_started'}] * 5
            
        except Exception:
            mock_progress = [{'completion_percentage': 0, 'status': 'not_started'}] * 5
        
        # Create mock submodule data with the progress
        module_titles = {
            1: ['Trafikkregler', 'Vikeplikt', 'Politi og trafikklys', 'Plassering og feltskifte', 'Kjøring i rundkjøring'],
            2: ['Fareskilt', 'Forbudsskilt', 'Påbudsskilt', 'Opplysningsskilt', 'Vegoppmerking'],
            3: ['Bremselengde', 'Sikt og lysbruk', 'Dekk og grep', 'Kontrollrutiner', 'Elbil og teknologi'],
            4: ['Alkohol og rus', 'Trøtthet', 'Risikoforståelse', 'Førstehjelp'],
            5: ['Øvingskjøring', 'Oppsummeringsquiz', 'Eksamenstrening', 'Teoriprøven']
        }
        
        titles = module_titles.get(module_id, ['Emne 1', 'Emne 2', 'Emne 3', 'Emne 4', 'Emne 5'])
        
        mock_data = []
        for i, title in enumerate(titles):
            progress_data = mock_progress[i] if i < len(mock_progress) else {'completion_percentage': 0, 'status': 'not_started'}
            
            mock_data.append({
                'submodule_number': float(f"{module_id}.{i+1}"),
                'title': title,
                'description': f'Beskrivelse for {title}',
                'estimated_minutes': 30,
                'difficulty_level': 2,
                'completion_percentage': progress_data['completion_percentage'],
                'status': progress_data['status'],
                'time_spent': 0,
                'content_viewed': progress_data['status'] != 'not_started',
                'summary_viewed': False,
                'shorts_watched': 0,
                'has_video_shorts': True,
                'shorts_count': 2,
                'has_quiz': True,
                'quiz_question_count': 10,
                'last_accessed': None,
                'started_at': None,
                'completed_at': None
            })
        
        return mock_data
    
    @staticmethod
    def get_submodule_content(submodule_id, user):
        """Get submodule content with progress tracking - simplified for now"""
        try:
            # For now, return None - this would load actual content from files
            return None
        except Exception as e:
            logger.error(f"Error getting submodule content for {submodule_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_submodule_shorts(submodule_id, user):
        """Get video shorts for submodule - mock or database based on config"""
        from flask import current_app
        
        if current_app.config.get('SHORT_VIDEOS_MOCK', False):
            return LearningService._get_mock_shorts(submodule_id, user)
        else:
            return LearningService._get_database_shorts(submodule_id, user)

    @staticmethod  
    def _get_database_shorts(submodule_id, user):
        """Real database video data for production"""
        try:
            from app.models import Video, VideoProgress
            
            # Get videos for this submodule
            shorts = Video.query.filter(
                Video.theory_module_ref == str(submodule_id),
                Video.is_active == True,
                Video.aspect_ratio == '9:16'
            ).order_by(Video.sequence_order).all()
            
            shorts_data = []
            for short in shorts:
                # Get user progress
                progress = VideoProgress.query.filter_by(
                    user_id=user.id,
                    video_id=short.id
                ).first()
                
                shorts_data.append({
                    'id': short.id,
                    'title': short.title,
                    'description': short.description,
                    'file_path': short.file_path,
                    'duration_seconds': short.duration_seconds,
                    'watch_percentage': progress.watch_percentage if progress else 0,
                    'is_completed': progress.completed if progress else False,
                    'sequence_order': short.sequence_order
                })
            
            return shorts_data
            
        except Exception as e:
            logger.error(f"Error getting database shorts: {e}")
            # Fallback to mock data on error
            return LearningService._get_mock_shorts(submodule_id, user)

    @staticmethod
    def get_all_shorts_for_session(user, starting_submodule=None):
        """Get ALL video shorts across modules for continuous playback"""
        from flask import current_app
        
        if current_app.config.get('SHORT_VIDEOS_MOCK', False):
            return LearningService._get_all_mock_shorts(user, starting_submodule)
        else:
            return LearningService._get_all_database_shorts(user, starting_submodule)

    @staticmethod
    def _get_all_mock_shorts(user, starting_submodule=None):
        """Generate mock videos for all submodules 1.1 through 5.4"""
        all_videos = []
        
        # Define submodule structure
        submodules = [
            '1.1', '1.2', '1.3', '1.4', '1.5',
            '2.1', '2.2', '2.3', '2.4', '2.5', 
            '3.1', '3.2', '3.3', '3.4', '3.5',
            '4.1', '4.2', '4.3', '4.4',
            '5.1', '5.2', '5.3', '5.4'
        ]
        
        mock_video_files = [
            'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4', 
            'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'
        ]
        
        video_counter = 0
        for submodule in submodules:
            # Parse submodule (e.g., "1.1" -> module=1, sub=1)
            module = int(float(submodule))  # 1.1 -> 1
            sub_decimal = float(submodule) % 1  # 1.1 -> 0.1
            sub = int(sub_decimal * 10) if sub_decimal > 0 else 1  # 0.1 -> 1
            
            # 2-3 videos per submodule
            videos_per_submodule = 2 if float(submodule) % 1 != 0.5 else 3
            
            for i in range(videos_per_submodule):
                video_counter += 1
                all_videos.append({
                    'id': 9000 + (module * 100) + (sub * 10) + (i + 1),  # 🎯 INTEGER ID!
                    'title': f'Modul {submodule} - Del {i+1}',
                    'description': f'Video {i+1} for submodule {submodule}',
                    'file_path': mock_video_files[video_counter % len(mock_video_files)],
                    'duration_seconds': 45 + (i * 7),  # Vary duration
                    'submodule_id': submodule,
                    'watch_percentage': 0,
                    'is_completed': False,
                    'sequence_order': i + 1
                })
        
        # If starting_submodule specified, reorder to start from there
        if starting_submodule:
            start_index = next((i for i, v in enumerate(all_videos) if v['submodule_id'] == str(starting_submodule)), 0)
            all_videos = all_videos[start_index:] + all_videos[:start_index]
        
        return all_videos

    @staticmethod
    def _get_all_database_shorts(user, starting_submodule=None):
        """Get all database shorts ordered for continuous playback"""
        try:
            from app.models import Video, VideoProgress
            
            # Get all short videos ordered by theory module reference
            query = Video.query.filter(
                Video.is_active == True,
                Video.aspect_ratio == '9:16',
                Video.theory_module_ref.isnot(None)
            ).order_by(Video.theory_module_ref, Video.sequence_order)
            
            if starting_submodule:
                # Start from specific submodule
                query = query.filter(Video.theory_module_ref >= str(starting_submodule))
            
            shorts = query.all()
            
            # Get all progress records for user efficiently
            progress_records = {p.video_id: p for p in VideoProgress.query.filter_by(user_id=user.id).all()}
            
            shorts_data = []
            for short in shorts:
                progress = progress_records.get(short.id)
                
                shorts_data.append({
                    'id': short.id,
                    'title': short.title,
                    'description': short.description,
                    'file_path': short.file_path,
                    'duration_seconds': short.duration_seconds,
                    'submodule_id': short.theory_module_ref,
                    'watch_percentage': progress.watch_percentage if progress else 0,
                    'is_completed': progress.completed if progress else False,
                    'sequence_order': short.sequence_order
                })
            
            return shorts_data
            
        except Exception as e:
            logger.error(f"Error getting all database shorts: {e}")
            # Fallback to mock data
            return LearningService._get_all_mock_shorts(user, starting_submodule)
    
    @staticmethod
    def track_content_access(user, submodule_id, content_type):
        """Track that user accessed content with database storage"""
        try:
            from app.models import UserLearningProgress
            
            # Extract module_id from submodule_id (e.g., 1.1 -> 1)
            module_id = int(float(submodule_id))
            
            # Get or create submodule_id for database lookup
            from app.models import LearningSubmodules
            submodule = LearningSubmodules.query.filter_by(submodule_number=float(submodule_id)).first()
            submodule_db_id = submodule.id if submodule else None
            
            # Track the access
            progress = UserLearningProgress.track_content_access(
                user_id=user.id,
                module_id=module_id,
                submodule_id=submodule_db_id,
                progress_type=content_type
            )
            
            logger.info(f"User {user.id} accessed {content_type} for submodule {submodule_id}")
            return progress
            
        except Exception as e:
            logger.error(f"Error tracking content access: {str(e)}")
            return None
    
    # Add missing methods that are called by routes
    @staticmethod
    def get_submodule_details(submodule_id, user):
        """Get submodule details with content from ContentManager"""
        try:
            from app.learning.content_manager import ContentManager
            
            logger.info(f"Getting submodule details for {submodule_id}")
            
            # Get completion status from database
            try:
                from app.models import UserLearningProgress, LearningSubmodules
                
                # Extract module_id from submodule_id (1.1 -> 1)
                module_id = int(float(submodule_id))
                
                # Get submodule_id for database lookup
                submodule_record = LearningSubmodules.query.filter_by(submodule_number=float(submodule_id)).first()
                submodule_db_id = submodule_record.id if submodule_record else None
                
                # Check if user has completed this content
                progress = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    module_id=module_id,
                    submodule_id=submodule_db_id,
                    progress_type='content'
                ).first()
                
                # Extract progress data
                if progress:
                    completion_status = progress.status
                    completion_percentage = progress.completion_percentage
                    time_spent = progress.time_spent_minutes or 0
                    is_completed = progress.status == 'completed'
                else:
                    completion_status = 'not_started'
                    completion_percentage = 0
                    time_spent = 0
                    is_completed = False
                    
                logger.info(f"User {user.id} progress for {submodule_id}: {completion_status} ({completion_percentage}%)")
                
            except Exception as db_error:
                logger.warning(f"Could not get completion status for {submodule_id}: {str(db_error)}")
                # Fallback to default values if database query fails
                completion_status = 'not_started'
                completion_percentage = 0
                time_spent = 0
                is_completed = False
            
            # Build submodule details with real progress data
            submodule_details = {
                'submodule_number': submodule_id,
                'title': f'Modul {submodule_id}',
                'description': f'Beskrivelse for modul {submodule_id}',
                'estimated_minutes': 30,
                'difficulty_level': 2,
                'has_video_shorts': True,
                'shorts_count': 2,
                'has_quiz': True,
                'content_available': {
                    'detailed': True,
                    'kort': True
                },
                'learning_objectives': [
                    'Læringsmål 1',
                    'Læringsmål 2',
                    'Læringsmål 3'
                ],
                'tags': ['tag1', 'tag2'],
                'progress': {
                    'status': completion_status,
                    'completion_percentage': completion_percentage,
                    'time_spent': time_spent
                },
                'module': {
                    'id': int(submodule_id),
                    'title': f'Modul {int(submodule_id)}',
                    'number': int(submodule_id)
                },
                # Add these new fields for template use
                'status': completion_status,
                'completion_percentage': completion_percentage,
                'is_completed': is_completed,
                'time_spent': time_spent
            }
            
            # Try to load actual content, but don't fail if it doesn't work
            try:
                content_data = ContentManager.get_submodule_content(submodule_id)
                if content_data and content_data.get('metadata'):
                    metadata = content_data['metadata']
                    submodule_details.update({
                        'title': metadata.get('title', submodule_details['title']),
                        'description': metadata.get('description', submodule_details['description']),
                        'estimated_minutes': metadata.get('estimated_minutes', submodule_details['estimated_minutes']),
                        'difficulty_level': metadata.get('difficulty_level', submodule_details['difficulty_level']),
                        'learning_objectives': metadata.get('learning_objectives', submodule_details['learning_objectives']),
                        'tags': metadata.get('tags', submodule_details['tags'])
                    })
                    logger.info(f"Successfully loaded metadata for {submodule_id}")
                else:
                    logger.warning(f"No content data found for {submodule_id}, using mock data")
            except Exception as content_error:
                logger.warning(f"Could not load content for {submodule_id}: {str(content_error)}")
            
            return submodule_details
            
        except Exception as e:
            logger.error(f"Error getting submodule details for {submodule_id}: {str(e)}")
            return None
    
    @staticmethod
    def start_submodule_content(user, submodule_id):
        """Start submodule content tracking - simplified for now"""
        pass
    
    @staticmethod
    def start_submodule_shorts(user, submodule_id):
        """Start submodule shorts tracking - simplified for now"""
        pass
    
    @staticmethod
    def get_comprehensive_progress(user):
        """Get comprehensive progress data - simplified for now"""
        return {}
    
    @staticmethod
    def update_progress(user, content_type, content_id, progress_data):
        """Update learning progress - simplified for now"""
        return {}
    
    @staticmethod
    def mark_content_complete(user, content_type, content_id, completion_data=None):
        """Mark content as completed with database storage"""
        try:
            from app.models import UserLearningProgress
            
            # Extract module_id from content_id (assuming it's submodule_id like 1.1)
            module_id = int(float(content_id))
            
            # Get submodule_id for database lookup
            from app.models import LearningSubmodules
            submodule = LearningSubmodules.query.filter_by(submodule_number=float(content_id)).first()
            submodule_db_id = submodule.id if submodule else None
            
            # Mark as complete
            progress = UserLearningProgress.mark_content_complete(
                user_id=user.id,
                module_id=module_id,
                submodule_id=submodule_db_id,
                progress_type=content_type,
                completion_data=completion_data
            )
            
            logger.info(f"User {user.id} completed {content_type} for content {content_id}")
            return {
                'success': True,
                'progress': progress,
                'completion_percentage': progress.completion_percentage if progress else 100
            }
            
        except Exception as e:
            logger.error(f"Error marking content complete: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def track_time_spent(user, content_type, content_id, time_seconds):
        """Track time spent on content - simplified for now"""
        return {}
    
    @staticmethod
    def get_user_last_position(user):
        """Get user's last learning position"""
        try:
            from app.models import UserLearningProgress, LearningSubmodules
            
            # Get user's last accessed content
            progress = UserLearningProgress.get_user_last_position(user.id)
            
            if progress:
                # Get submodule number for URL routing
                submodule_number = None
                if progress.submodule_id:
                    submodule = LearningSubmodules.query.get(progress.submodule_id)
                    if submodule:
                        submodule_number = submodule.submodule_number
                
                return {
                    'module_id': progress.module_id,
                    'submodule_id': progress.submodule_id,
                    'submodule_number': submodule_number,
                    'progress_type': progress.progress_type,
                    'last_accessed': progress.last_accessed,
                    'status': progress.status
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user last position: {str(e)}")
            return None
    
    @staticmethod
    def get_next_content_smart(user, current_submodule, current_content_type='content'):
        """Get next recommended content with smart logic"""
        try:
            # For now, implement simple sequential logic
            # This can be enhanced with ML recommendations later
            
            current_module = int(float(current_submodule))
            current_sub = float(current_submodule)
            
            # Define next content logic based on current content type
            if current_content_type == 'content':
                return LearningService.get_next_submodule(current_submodule)
            
            elif current_content_type == 'shorts':
                # After shorts, go to next submodule
                return LearningService.get_next_submodule(current_submodule)
            
            else:
                # Default to next submodule
                return LearningService.get_next_submodule(current_submodule)
                
        except Exception as e:
            logger.error(f"Error getting next content: {str(e)}")
            return None
    
    @staticmethod
    def get_next_submodule(current_submodule):
        """Get next submodule in sequence"""
        try:
            current_module = int(float(current_submodule))
            current_sub_num = float(current_submodule)
            
            # Simple increment logic (1.1 -> 1.2 -> 1.3 -> 2.1)
            next_sub = round(current_sub_num + 0.1, 1)
            
            # Check if next submodule exists in current module
            submodule_counts = [5, 5, 5, 4, 4]  # As defined in mock data
            max_subs = submodule_counts[current_module - 1] if current_module <= len(submodule_counts) else 5
            
            if (next_sub - current_module) <= (max_subs / 10):
                # Stay in current module
                return {
                    'submodule_id': next_sub,
                    'content_type': 'content',
                    'url': f'/learning/module/{next_sub}',
                    'title': f'Modul {next_sub}'
                }
            else:
                # Move to next module
                if current_module < 5:
                    next_module_sub = current_module + 1.1
                    return {
                        'submodule_id': next_module_sub,
                        'content_type': 'content',
                        'url': f'/learning/module/{next_module_sub}',
                        'title': f'Modul {next_module_sub}'
                    }
                else:
                    # End of content
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting next submodule: {str(e)}")
            return None
    
    @staticmethod
    def has_shorts(submodule_id):
        """Check if submodule has video shorts"""
        try:
            from app.models import Video
            
            # Check if shorts exist for this submodule
            shorts_exist = Video.query.filter(
                Video.theory_module_ref == str(submodule_id),
                Video.is_active == True,
                Video.aspect_ratio == '9:16'
            ).first() is not None
            
            return shorts_exist
            
        except Exception as e:
            logger.error(f"Error checking shorts availability: {str(e)}")
            return False  # Default to no shorts available
    
    @staticmethod
    def get_next_content(user, current_content_type, current_content_id):
        """Get next recommended content - wrapper for backward compatibility"""
        return LearningService.get_next_content_smart(user, current_content_id, current_content_type)
    
    @staticmethod
    def update_shorts_progress(user, shorts_id, watch_data):
        """Update user progress for watching a video short using extended VideoProgress model"""
        try:
            from app.models import Video, VideoProgress

            video = Video.query.get(shorts_id)
            
            # Find or create progress record
            progress = VideoProgress.query.filter_by(
                user_id=user.id,
                video_id=shorts_id
            ).first()
            
            if not progress:
                progress = VideoProgress(
                    user_id=user.id,
                    video_id=shorts_id,
                )
                db.session.add(progress)
            
            if 'watch_percentage' in watch_data and video and video.duration_seconds:
                # Convert percentage to seconds using actual video duration
                progress.last_position_seconds = int((watch_data['watch_percentage'] / 100) * video.duration_seconds)
            
            if 'watch_time_seconds' in watch_data:
                progress.last_position_seconds = watch_data['watch_time_seconds']
                
            # Mark as completed if >= 95% watched
            if progress.watch_percentage >= 95 and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.utcnow()
            
            progress.updated_at = datetime.utcnow()
            
            # Update video view count
            if video and not progress.started_at:  # First time watching
                video.view_count += 1
                progress.started_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'watch_percentage': progress.watch_percentage,
                'completed': progress.completed
            }
            
        except Exception as e:
            logger.error(f"Error updating video progress: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_video_progress(user, video_id, watch_data):
        """Generic method for updating video progress - wrapper for update_shorts_progress"""
        return LearningService.update_shorts_progress(user, video_id, watch_data)
    
    @staticmethod
    def toggle_shorts_like(user, video_id):
        """Toggle like status for a video short using extended VideoProgress model"""
        try:
            from app.models import Video, VideoProgress
            
            # Find or create progress record
            progress = VideoProgress.query.filter_by(
                user_id=user.id,
                video_id=video_id
            ).first()
            
            if not progress:
                progress = VideoProgress(
                    user_id=user.id,
                    video_id=video_id,
                )
                db.session.add(progress)
            
            # For now, use interaction_quality field to store like status
            # TODO: Add proper like tracking field in future migration
            old_liked = progress.interaction_quality > 0
            new_liked = not old_liked
            progress.interaction_quality = 1.0 if new_liked else 0.0
            
            db.session.commit()
            
            logger.info(f"Toggled like for user {user.id}, video {video_id}: {new_liked}")
            return {
                'success': True,
                'liked': new_liked
            }
            
        except Exception as e:
            logger.error(f"Error toggling video like: {str(e)}")
            db.session.rollback()
            return {'success': False, 'liked': False}
    
    @staticmethod
    def get_submodule_shorts(submodule_id, user):
        """Get video shorts for submodule - mock or database based on config"""
        from flask import current_app
        
        if current_app.config.get('SHORT_VIDEOS_MOCK', False):
            return LearningService._get_mock_shorts(submodule_id, user)
        else:
            return LearningService._get_database_shorts(submodule_id, user)
    
    @staticmethod
    def _get_mock_shorts(submodule_id, user):
        """Mock video data with integer IDs using 9XXX encoding"""
        # Parse submodule_id (e.g., "1.1" -> module=1, sub=1)
        module = int(float(submodule_id))  # 1.1 -> 1
        sub_decimal = float(submodule_id) % 1  # 1.1 -> 0.1
        sub = int(sub_decimal * 10) if sub_decimal > 0 else 1  # 0.1 -> 1, 0.2 -> 2
        
        mock_videos = [
            {
                'id': 9000 + (module * 100) + (sub * 10) + 1,  # e.g., 9111 for module 1.1 video 1
                'title': f'Modul {submodule_id} - Del 1',
                'description': f'Første video for modul {submodule_id}',
                'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'duration_seconds': 45,
                'watch_percentage': 0,
                'is_completed': False,
                'sequence_order': 1
            },
            {
                'id': 9000 + (module * 100) + (sub * 10) + 2,  # e.g., 9112 for module 1.1 video 2
                'title': f'Modul {submodule_id} - Del 2',
                'description': f'Andre video for modul {submodule_id}',
                'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
                'duration_seconds': 52,
                'watch_percentage': 0,
                'is_completed': False,
                'sequence_order': 2
            },
            {
                'id': 9000 + (module * 100) + (sub * 10) + 3,  # e.g., 9113 for module 1.1 video 3
                'title': f'Modul {submodule_id} - Del 3',
                'description': f'Tredje video for modul {submodule_id}',
                'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
                'duration_seconds': 38,
                'watch_percentage': 0,
                'is_completed': False,
                'sequence_order': 3
            }
        ]
        return mock_videos
    
    @staticmethod  
    def _get_database_shorts(submodule_id, user):
        """Real database video data for production"""
        try:
            from app.models import Video, VideoProgress
            
            # Get videos for this submodule
            shorts = Video.query.filter(
                Video.theory_module_ref == str(submodule_id),
                Video.is_active == True,
                Video.aspect_ratio == '9:16'
            ).order_by(Video.sequence_order).all()
            
            shorts_data = []
            for short in shorts:
                # Get user progress
                progress = VideoProgress.query.filter_by(
                    user_id=user.id,
                    video_id=short.id
                ).first()
                
                shorts_data.append({
                    'id': short.id,
                    'title': short.title,
                    'description': short.description,
                    'file_path': short.file_path,
                    'duration_seconds': short.duration_seconds,
                    'watch_percentage': progress.watch_percentage if progress else 0,
                    'is_completed': progress.completed if progress else False,
                    'sequence_order': short.sequence_order
                })
            
            return shorts_data
            
        except Exception as e:
            logger.error(f"Error getting database shorts: {e}")
            # Fallback to mock data on error
            return LearningService._get_mock_shorts(submodule_id, user)
    
    @staticmethod
    def get_all_shorts_for_session(user, starting_submodule=None):
        """Get ALL video shorts across modules for continuous playback"""
        from flask import current_app
        
        if current_app.config.get('SHORT_VIDEOS_MOCK', False):
            return LearningService._get_all_mock_shorts(user, starting_submodule)
        else:
            return LearningService._get_all_database_shorts(user, starting_submodule)
    
    @staticmethod
    def _get_all_database_shorts(user, starting_submodule=None):
        """Get all database shorts ordered for continuous playback"""
        try:
            from app.models import Video, VideoProgress
            
            # Get all short videos ordered by theory module reference
            query = Video.query.filter(
                Video.is_active == True,
                Video.aspect_ratio == '9:16',
                Video.theory_module_ref.isnot(None)
            ).order_by(Video.theory_module_ref, Video.sequence_order)
            
            if starting_submodule:
                # Start from specific submodule
                query = query.filter(Video.theory_module_ref >= str(starting_submodule))
            
            shorts = query.all()
            
            # Get all progress records for user efficiently
            progress_records = {p.video_id: p for p in VideoProgress.query.filter_by(user_id=user.id).all()}
            
            shorts_data = []
            for short in shorts:
                progress = progress_records.get(short.id)
                
                shorts_data.append({
                    'id': short.id,
                    'title': short.title,
                    'description': short.description,
                    'file_path': short.file_path,
                    'duration_seconds': short.duration_seconds,
                    'submodule_id': short.theory_module_ref,
                    'watch_percentage': progress.watch_percentage if progress else 0,
                    'is_completed': progress.completed if progress else False,
                    'sequence_order': short.sequence_order
                })
            
            return shorts_data
            
        except Exception as e:
            logger.error(f"Error getting all database shorts: {e}")
            # Fallback to mock data
            return LearningService._get_all_mock_shorts(user, starting_submodule)
