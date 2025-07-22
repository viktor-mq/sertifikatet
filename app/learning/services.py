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
    def track_video_access(user, submodule_id):
        """Track that user started watching videos for this submodule (mirrors track_content_access)"""
        try:
            # Get the first video for this submodule to track access
            videos = LearningService.get_submodule_shorts(submodule_id, user)
            
            if not videos:
                logger.warning(f"No videos found for submodule {submodule_id}")
                return None
            
            first_video = videos[0]
            
            # Create or update progress for first video to mark access
            from app.models import VideoProgress
            
            progress = VideoProgress.query.filter_by(
                user_id=user.id,
                video_id=first_video['id']
            ).first()
            
            if not progress:
                progress = VideoProgress(
                    user_id=user.id,
                    video_id=first_video['id'],
                    started_at=datetime.utcnow()
                )
                db.session.add(progress)
            
            progress.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User {user.id} accessed videos for submodule {submodule_id}")
            return progress
            
        except Exception as e:
            logger.error(f"Error tracking video access: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def mark_submodule_videos_complete(user, submodule_id):
        """Mark all videos in submodule as 100% complete (mirrors mark_content_complete)"""
        try:
            # Get all videos for this submodule
            videos = LearningService.get_submodule_shorts(submodule_id, user)
            
            if not videos:
                logger.warning(f"No videos found for submodule {submodule_id}")
                return {'success': False, 'error': 'No videos found'}
            
            from app.models import VideoProgress, Video
            
            completed_count = 0
            
            for video in videos:
                video_id = video['id']
                
                # Find or create progress record
                progress = VideoProgress.query.filter_by(
                    user_id=user.id,
                    video_id=video_id
                ).first()
                
                if not progress:
                    progress = VideoProgress(
                        user_id=user.id,
                        video_id=video_id,
                        started_at=datetime.utcnow()
                    )
                    db.session.add(progress)
                
                # Mark as completed
                progress.completed = True
                progress.completed_at = datetime.utcnow()
                progress.updated_at = datetime.utcnow()
                
                # Set to 100% watch percentage
                video_obj = Video.query.get(video_id)
                if video_obj and video_obj.duration_seconds:
                    progress.last_position_seconds = video_obj.duration_seconds
                
                completed_count += 1
            
            db.session.commit()
            
            logger.info(f"User {user.id} marked {completed_count} videos complete in submodule {submodule_id}")
            return {
                'success': True,
                'videos_completed': completed_count,
                'completion_percentage': 100
            }
            
        except Exception as e:
            logger.error(f"Error marking submodule videos complete: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_submodule_video_progress(user, submodule_id):
        """Get aggregated video progress for a submodule (mirrors reading progress structure)"""
        try:
            # Get all videos for this submodule
            videos = LearningService.get_submodule_shorts(submodule_id, user)
            
            if not videos:
                return {
                    'status': 'not_started',
                    'completion_percentage': 0,
                    'videos_completed': 0,
                    'total_videos': 0,
                    'last_accessed': None,
                    'time_spent': 0
                }
            
            # Calculate aggregate progress
            total_videos = len(videos)
            completed_videos = sum(1 for v in videos if v.get('is_completed', False))
            total_watch_percentage = sum(v.get('watch_percentage', 0) for v in videos)
            
            # Overall completion = average of all video watch percentages
            completion_percentage = int(total_watch_percentage / total_videos) if total_videos > 0 else 0
            
            # Determine status
            if completion_percentage >= 95:
                status = 'completed'
            elif completion_percentage > 0:
                status = 'in_progress'
            else:
                status = 'not_started'
            
            # Get last accessed time from VideoProgress table
            try:
                from app.models import VideoProgress, Video
                
                # Get video IDs for this submodule
                video_ids = [v['id'] for v in videos]
                
                # Get most recent access time
                last_progress = VideoProgress.query.filter(
                    VideoProgress.user_id == user.id,
                    VideoProgress.video_id.in_(video_ids)
                ).order_by(VideoProgress.updated_at.desc()).first()
                
                last_accessed = last_progress.updated_at if last_progress else None
                
            except Exception as e:
                logger.warning(f"Could not get video last accessed time: {e}")
                last_accessed = None
            
            result = {
                'status': status,
                'completion_percentage': completion_percentage,
                'videos_completed': completed_videos,
                'total_videos': total_videos,
                'last_accessed': last_accessed,
                'time_spent': 0  # Could be calculated from video durations if needed
            }
            
            logger.info(f"Video progress for submodule {submodule_id}: {completion_percentage}% ({completed_videos}/{total_videos})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting submodule video progress: {str(e)}")
            return {
                'status': 'not_started',
                'completion_percentage': 0,
                'videos_completed': 0,
                'total_videos': 0,
                'last_accessed': None,
                'time_spent': 0
            }
    
    
    @staticmethod
    def get_submodule_details(submodule_id, user):
        """Get submodule details with BOTH reading and video progress"""
        try:
            from app.learning.content_manager import ContentManager
            
            logger.info(f"Getting submodule details for {submodule_id}")
            
            # Get reading completion status from database (EXISTING LOGIC - UNCHANGED)
            try:
                from app.models import UserLearningProgress, LearningSubmodules
                
                # Extract module_id from submodule_id (1.1 -> 1)
                module_id = int(float(submodule_id))
                
                # Get submodule_id for database lookup
                submodule_record = LearningSubmodules.query.filter_by(submodule_number=float(submodule_id)).first()
                submodule_db_id = submodule_record.id if submodule_record else None
                
                # Check if user has completed reading content
                reading_progress_record = UserLearningProgress.query.filter_by(
                    user_id=user.id,
                    module_id=module_id,
                    submodule_id=submodule_db_id,
                    progress_type='content'
                ).first()
                
                # Extract reading progress data
                if reading_progress_record:
                    reading_progress = {
                        'status': reading_progress_record.status,
                        'completion_percentage': reading_progress_record.completion_percentage,
                        'time_spent': reading_progress_record.time_spent_minutes or 0,
                        'last_accessed': reading_progress_record.last_accessed,
                        'is_completed': reading_progress_record.status == 'completed'
                    }
                else:
                    reading_progress = {
                        'status': 'not_started',
                        'completion_percentage': 0,
                        'time_spent': 0,
                        'last_accessed': None,
                        'is_completed': False
                    }
                    
                logger.info(f"Reading progress for {submodule_id}: {reading_progress['status']} ({reading_progress['completion_percentage']}%)")
                
            except Exception as db_error:
                logger.warning(f"Could not get reading progress for {submodule_id}: {str(db_error)}")
                # Fallback to default values if database query fails
                reading_progress = {
                    'status': 'not_started',
                    'completion_percentage': 0,
                    'time_spent': 0,
                    'last_accessed': None,
                    'is_completed': False
                }
            
            # Get video progress using new method (NEW FUNCTIONALITY)
            video_progress = LearningService.get_submodule_video_progress(user, submodule_id)
            
            # Build submodule details with BOTH reading and video progress
            submodule_details = {
                'submodule_number': submodule_id,
                'title': f'Modul {submodule_id}',
                'description': f'Beskrivelse for modul {submodule_id}',
                'estimated_minutes': 30,
                'difficulty_level': 2,
                'has_video_shorts': True,
                'shorts_count': video_progress.get('total_videos', 0),
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
                
                # SEPARATE PROGRESS FOR READING AND VIDEO
                'reading_progress': reading_progress,
                'video_progress': video_progress,
                
                # OVERALL SUBMODULE STATUS (based on both formats)
                'overall_progress': LearningService._calculate_overall_progress(reading_progress, video_progress),
                
                'module': {
                    'id': int(submodule_id),
                    'title': f'Modul {int(submodule_id)}',
                    'number': int(submodule_id)
                },
                
                # BACKWARD COMPATIBILITY (keep existing fields for templates that expect them)
                'status': reading_progress['status'],  # Default to reading status for compatibility
                'completion_percentage': reading_progress['completion_percentage'],
                'is_completed': reading_progress['is_completed'],
                'time_spent': reading_progress['time_spent']
            }
            
            # Try to load actual content metadata, but don't fail if it doesn't work
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
    def _calculate_overall_progress(reading_progress, video_progress):
        """Calculate overall progress considering both reading and video"""
        reading_completion = reading_progress.get('completion_percentage', 0)
        video_completion = video_progress.get('completion_percentage', 0)
        
        # Overall progress = average of both formats
        overall_percentage = (reading_completion + video_completion) / 2
        
        # Determine overall status
        if overall_percentage >= 95:
            overall_status = 'completed'
        elif overall_percentage > 0:
            overall_status = 'in_progress' 
        else:
            overall_status = 'not_started'
            
        return {
            'status': overall_status,
            'completion_percentage': int(overall_percentage),
            'reading_percentage': reading_completion,
            'video_percentage': video_completion
        }
    
    @staticmethod
    def _get_all_mock_shorts(user, starting_submodule=None, starting_video_id=None):
        """Get all mock videos from database (ID 9000+ series) for cross-module sessions"""
        try:
            from app.models import Video, VideoProgress
            
            # Get all mock videos from database (ID >= 9000)
            all_shorts = Video.query.filter(
                Video.is_active == True,
                Video.aspect_ratio == '9:16',
                Video.id >= 9000  # Mock video identifier
            ).order_by(Video.theory_module_ref, Video.sequence_order).all()
            
            if not all_shorts:
                logger.warning("No mock videos found in database for cross-module session")
                return []
            
            # Format video data with user progress
            formatted_videos = []
            for video in all_shorts:
                # Get user progress for this video
                progress = VideoProgress.query.filter_by(
                    user_id=user.id,
                    video_id=video.id
                ).first()
                
                # Calculate progress data
                watch_percentage = 0
                is_completed = False
                if progress:
                    watch_percentage = progress.watch_percentage or 0
                    is_completed = progress.completed or False
                
                formatted_videos.append({
                    'id': video.id,
                    'title': video.title,
                    'description': video.description,
                    'file_path': video.youtube_url or video.filename,  # Use youtube_url or filename
                    'duration_seconds': video.duration_seconds,
                    'submodule_id': video.theory_module_ref,  # e.g., '1.1', '1.2'
                    'watch_percentage': watch_percentage,
                    'is_completed': is_completed,
                    'sequence_order': video.sequence_order
                })
            
            # Determine the starting index
            start_index = 0
            if starting_video_id:
                # Find specific video ID in the array
                start_index = next((i for i, v in enumerate(formatted_videos) if v['id'] == starting_video_id), 0)
                logger.info(f"Found starting video {starting_video_id} at index {start_index} (mock shorts)")
            elif starting_submodule:
                # Fallback to submodule if specific video ID is not provided
                start_index = next(
                    (i for i, v in enumerate(formatted_videos) 
                     if v['submodule_id'] == str(starting_submodule)), 0
                )
                logger.info(f"Found starting submodule {starting_submodule} at index {start_index} (mock shorts)")
            
            # Reorder the playlist to start from the correct video
            if start_index > 0:
                formatted_videos = formatted_videos[start_index:] + formatted_videos[:start_index]
                logger.info(f"Reordered mock playlist to start from index {start_index}")
            
            return formatted_videos
            
        except Exception as e:
            logger.error(f"Error getting all mock shorts from database: {str(e)}")
            # Fallback to empty list if database query fails
            return []

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
        """Get user's last learning position including specific video position"""
        try:
            from app.models import UserLearningProgress, LearningSubmodules, VideoProgress, Video
            
            # Check both content progress and video progress to find the true last position
            content_progress = UserLearningProgress.get_user_last_position(user.id)
            
            # Get most recent video progress
            video_progress = VideoProgress.query.filter_by(
                user_id=user.id
            ).order_by(VideoProgress.updated_at.desc()).first()
            
            # Determine which is more recent
            last_position = None
            use_video_progress = False
            
            if video_progress and content_progress:
                # Compare timestamps to find the most recent activity
                video_time = video_progress.updated_at or video_progress.started_at
                content_time = content_progress.last_accessed
                
                if video_time and content_time:
                    use_video_progress = video_time > content_time
                elif video_time:
                    use_video_progress = True
            elif video_progress:
                use_video_progress = True
            
            if use_video_progress and video_progress:
                # Get video details to determine submodule
                video = Video.query.get(video_progress.video_id)
                if video and video.theory_module_ref:
                    return {
                        'module_id': int(float(video.theory_module_ref)),  # 1.3 -> 1
                        'submodule_id': None,  # Not needed for video continuation
                        'submodule_number': video.theory_module_ref,  # e.g., '1.3'
                        'progress_type': 'shorts',
                        'last_accessed': video_progress.updated_at or video_progress.started_at,
                        'status': 'completed' if video_progress.completed else 'in_progress',
                        # Enhanced fields for video-specific continuation
                        'last_video_id': video_progress.video_id,
                        'video_position_seconds': video_progress.last_position_seconds or 0,
                        'video_submodule_ref': video.theory_module_ref
                    }
            
            # Fallback to content progress
            if content_progress:
                # Get submodule number for URL routing
                submodule_number = None
                if content_progress.submodule_id:
                    submodule = LearningSubmodules.query.get(content_progress.submodule_id)
                    if submodule:
                        submodule_number = submodule.submodule_number
                
                return {
                    'module_id': content_progress.module_id,
                    'submodule_id': content_progress.submodule_id,
                    'submodule_number': submodule_number,
                    'progress_type': content_progress.progress_type,
                    'last_accessed': content_progress.last_accessed,
                    'status': content_progress.status,
                    # No video-specific fields for content progress
                    'last_video_id': None,
                    'video_position_seconds': 0,
                    'video_submodule_ref': None
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
                
            # Mark as completed if >= 95% watched (use request data directly)
            request_percentage = watch_data.get('watch_percentage', 0)
            if request_percentage >= 95 and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.utcnow()
            
            progress.updated_at = datetime.utcnow()
            
            # Update video view count
            if video and not progress.started_at:  # First time watching
                video.view_count += 1
                progress.started_at = datetime.utcnow()
            
            db.session.commit()
            
            # Calculate watch percentage from stored position and video duration
            calculated_watch_percentage = 0
            if video and video.duration_seconds > 0 and progress.last_position_seconds:
                calculated_watch_percentage = (progress.last_position_seconds / video.duration_seconds) * 100
                # Cap at 100% to avoid display issues
                calculated_watch_percentage = min(calculated_watch_percentage, 100)
            
            return {
                'success': True,
                'watch_percentage': calculated_watch_percentage,
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
    def _get_mock_shorts(submodule_id, user):
        """Mock video data from database (ID 9000+ series)"""
        try:
            from app.models import Video, VideoProgress
            
            # Get mock videos for this submodule (ID >= 9000)
            shorts = Video.query.filter(
                Video.theory_module_ref == str(submodule_id),
                Video.is_active == True,
                Video.aspect_ratio == '9:16',
                Video.id >= 9000  # Mock video identifier
            ).order_by(Video.sequence_order).all()
            
            if not shorts:
                logger.warning(f"No mock videos found for submodule {submodule_id}")
                return []
            
            # Format video data with user progress
            formatted_shorts = []
            for video in shorts:
                # Get user progress for this video
                progress = VideoProgress.query.filter_by(
                    user_id=user.id,
                    video_id=video.id
                ).first()
                
                # Calculate progress data
                watch_percentage = 0
                is_completed = False
                if progress:
                    watch_percentage = progress.watch_percentage or 0
                    is_completed = progress.completed or False
                
                formatted_shorts.append({
                    'id': video.id,
                    'title': video.title,
                    'description': video.description,
                    'file_path': video.youtube_url or video.filename,  # Use youtube_url or filename
                    'duration_seconds': video.duration_seconds,
                    'watch_percentage': watch_percentage,
                    'is_completed': is_completed,
                    'sequence_order': video.sequence_order
                })
            
            return formatted_shorts
            
        except Exception as e:
            logger.error(f"Error getting mock shorts from database: {str(e)}")
            # Fallback to empty list if database query fails
            return []
    
    @staticmethod
    def get_all_shorts_for_session(user, starting_submodule=None, starting_video_id=None):
        """Get ALL video shorts across modules for continuous playback"""
        from flask import current_app
        
        if current_app.config.get('SHORT_VIDEOS_MOCK', False):
            return LearningService._get_all_mock_shorts(user, starting_submodule, starting_video_id)
        else:
            return LearningService._get_all_database_shorts(user, starting_submodule, starting_video_id)
    
    @staticmethod
    def _get_all_database_shorts(user, starting_submodule=None, starting_video_id=None):
        """Get all database shorts ordered for continuous playbook"""
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
            
            # Determine the starting index
            start_index = 0
            if starting_video_id:
                # Find specific video ID in the array
                start_index = next((i for i, v in enumerate(shorts_data) if v['id'] == starting_video_id), 0)
                logger.info(f"Found starting video {starting_video_id} at index {start_index}")
            elif starting_submodule:
                # Fallback to submodule if specific video ID is not provided
                start_index = next((i for i, v in enumerate(shorts_data) if v['submodule_id'] == str(starting_submodule)), 0)
                logger.info(f"Found starting submodule {starting_submodule} at index {start_index}")
            
            # Reorder the playlist to start from the correct video
            if start_index > 0:
                shorts_data = shorts_data[start_index:] + shorts_data[:start_index]
                logger.info(f"Reordered playlist to start from index {start_index}")
            
            return shorts_data
            
        except Exception as e:
            logger.error(f"Error getting all database shorts: {e}")
            # Fallback to mock data, passing along the starting parameters
            return LearningService._get_all_mock_shorts(user, starting_submodule, starting_video_id)
    
    @staticmethod
    def get_dashboard_video_progress(user):
        """Get video progress for all modules for dashboard display with smart video navigation"""
        try:
            # Get all modules for user
            modules = LearningService.get_user_modules_progress(user)
            
            # Add video progress to each module
            for module in modules:
                # Get all submodules for this module (1.1, 1.2, etc.)
                module_id = module['id']
                total_videos = 0
                completed_videos = 0
                next_video_submodule = f"{module_id}.1"  # Default to first submodule
                
                # Calculate submodules based on module structure
                submodule_counts = [5, 5, 5, 4, 4]  # As defined in mock data
                num_submodules = submodule_counts[module_id - 1] if module_id <= len(submodule_counts) else 5
                
                # Track submodule progress for smart navigation
                submodule_progress_list = []
                
                for sub_num in range(1, num_submodules + 1):
                    submodule_id = f"{module_id}.{sub_num}"
                    
                    # Get video progress for this submodule
                    video_progress = LearningService.get_submodule_video_progress(user, submodule_id)
                    total_videos += video_progress.get('total_videos', 0)
                    completed_videos += video_progress.get('videos_completed', 0)
                    
                    # Store submodule progress for navigation logic
                    submodule_progress_list.append({
                        'submodule_id': submodule_id,
                        'completion_percentage': video_progress.get('completion_percentage', 0),
                        'status': video_progress.get('status', 'not_started'),
                        'videos_completed': video_progress.get('videos_completed', 0),
                        'total_videos': video_progress.get('total_videos', 0)
                    })
                
                # Calculate module video completion percentage
                if total_videos > 0:
                    module['completion_percentage'] = int((completed_videos / total_videos) * 100)
                    module['progress'] = module['completion_percentage']
                    
                    if completed_videos == total_videos:
                        module['status'] = 'completed'
                    elif completed_videos > 0:
                        module['status'] = 'in_progress'
                    else:
                        module['status'] = 'not_started'
                else:
                    module['completion_percentage'] = 0
                    module['progress'] = 0
                    module['status'] = 'not_started'
                
                # Get last video position specifically for THIS module
                last_video_in_module = LearningService.get_last_video_position_for_module(user, module_id)
                
                if last_video_in_module:
                    # User has video progress in this specific module
                    next_video_submodule = last_video_in_module['submodule_id']
                    next_video_id = last_video_in_module['video_id']
                    logger.info(f"Dashboard: Module {module_id} will continue from video {next_video_id} in submodule {next_video_submodule}")
                else:
                    # No video progress in this module - start from first incomplete submodule
                    next_video_submodule = LearningService._determine_next_video_submodule(
                        module_id, submodule_progress_list
                    )
                    next_video_id = None  # Will start from first video
                    logger.info(f"Dashboard: Module {module_id} will start from submodule {next_video_submodule} (no video progress)")
                
                # Add video-specific navigation data
                module['next_video_submodule'] = next_video_submodule
                module['next_video_id'] = next_video_id
                module['video_button_text'] = LearningService._get_video_button_text(module['status'])
                    
            return modules
            
        except Exception as e:
            logger.error(f"Error getting dashboard video progress: {str(e)}")
            return []
    
    @staticmethod
    def _determine_next_video_submodule(module_id, submodule_progress_list):
        """Determine which submodule video to show next based on progress"""
        try:
            # Sort by submodule_id to ensure proper order
            sorted_submodules = sorted(submodule_progress_list, key=lambda x: float(x['submodule_id']))
            
            # Find first incomplete submodule
            for submodule in sorted_submodules:
                if submodule['status'] in ['not_started', 'in_progress']:
                    return submodule['submodule_id']
            
            # If all completed, return first submodule for review
            if sorted_submodules:
                return sorted_submodules[0]['submodule_id']
            
            # Fallback to first submodule
            return f"{module_id}.1"
            
        except Exception as e:
            logger.error(f"Error determining next video submodule: {str(e)}")
            return f"{module_id}.1"
    
    @staticmethod
    def get_last_video_position_for_module(user, module_id):
        """Smart video continuation: next unwatched, then incomplete, then next submodule"""
        try:
            from app.models import VideoProgress, Video
            from sqlalchemy import and_, or_
            
            # Step 1: Find the last completed video in this module (highest sequence)
            last_completed = db.session.query(VideoProgress)\
                .join(Video, VideoProgress.video_id == Video.id)\
                .filter(
                    VideoProgress.user_id == user.id,
                    Video.theory_module_ref.like(f"{module_id}.%"),
                    VideoProgress.completed == True
                )\
                .order_by(Video.theory_module_ref, Video.sequence_order.desc())\
                .first()
            
            if last_completed:
                # Step 2: Find next video after the last completed one in the same submodule
                next_video = Video.query.filter(
                    Video.theory_module_ref == last_completed.video.theory_module_ref,  # Same submodule
                    Video.sequence_order > last_completed.video.sequence_order,
                    Video.is_active == True
                ).order_by(Video.sequence_order).first()
                
                if next_video:
                    logger.info(f"Module {module_id}: Next video {next_video.id} after completed video {last_completed.video_id}")
                    return {
                        'video_id': next_video.id,
                        'submodule_id': next_video.theory_module_ref,
                        'last_position_seconds': 0,
                        'continuation_type': 'next_in_sequence'
                    }
            
            # Step 3: No next video in sequence - find any incomplete video in this module
            incomplete_video = db.session.query(Video)\
                .outerjoin(VideoProgress, and_(
                    VideoProgress.video_id == Video.id,
                    VideoProgress.user_id == user.id
                ))\
                .filter(
                    Video.theory_module_ref.like(f"{module_id}.%"),
                    Video.is_active == True,
                    or_(
                        VideoProgress.completed == False,
                        VideoProgress.completed.is_(None)  # Never watched
                    )
                )\
                .order_by(Video.theory_module_ref, Video.sequence_order)\
                .first()
            
            if incomplete_video:
                logger.info(f"Module {module_id}: Found incomplete video {incomplete_video.id} in {incomplete_video.theory_module_ref}")
                return {
                    'video_id': incomplete_video.id,
                    'submodule_id': incomplete_video.theory_module_ref,
                    'last_position_seconds': 0,
                    'continuation_type': 'incomplete_video'
                }
            
            # Step 4: Everything complete in this module - find first video of next submodule
            # Get the highest submodule number in this module
            highest_submodule = db.session.query(Video.theory_module_ref)\
                .filter(
                    Video.theory_module_ref.like(f"{module_id}.%"),
                    Video.is_active == True
                )\
                .order_by(Video.theory_module_ref.desc())\
                .first()
            
            if highest_submodule:
                # Try to find next submodule (e.g., if highest is 1.3, look for 1.4)
                current_sub = float(highest_submodule[0])
                next_sub = round(current_sub + 0.1, 1)
                
                next_submodule_video = Video.query.filter(
                    Video.theory_module_ref == str(next_sub),
                    Video.is_active == True
                ).order_by(Video.sequence_order).first()
                
                if next_submodule_video:
                    logger.info(f"Module {module_id}: All complete, moving to next submodule {next_sub}")
                    return {
                        'video_id': next_submodule_video.id,
                        'submodule_id': next_submodule_video.theory_module_ref,
                        'last_position_seconds': 0,
                        'continuation_type': 'next_submodule'
                    }
            
            # Step 5: No next submodule - restart from first video in module
            first_video = Video.query.filter(
                Video.theory_module_ref.like(f"{module_id}.%"),
                Video.is_active == True
            ).order_by(Video.theory_module_ref, Video.sequence_order).first()
            
            if first_video:
                logger.info(f"Module {module_id}: Restarting from first video {first_video.id}")
                return {
                    'video_id': first_video.id,
                    'submodule_id': first_video.theory_module_ref,
                    'last_position_seconds': 0,
                    'continuation_type': 'restart_module'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting smart video position for module {module_id}: {str(e)}")
            return None
    
    @staticmethod
    def _get_video_button_text(status):
        """Get appropriate button text for video mode based on module status"""
        if status == 'completed':
            return 'Se videoer igjen'
        elif status == 'in_progress':
            return 'Fortsett videoer'
        else:
            return 'Start videoer'
