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
            from app.models import LearningModules, UserLearningModule
            
            # Get all learning modules from database
            # Note: LearningModules model doesn't have module_type field, so get all active modules
            modules = LearningModules.query.filter_by(is_active=True).order_by(LearningModules.id).all()
            
            modules_data = []
            for module in modules:
                # Get user progress for this module
                user_progress = UserLearningModule.query.filter_by(
                    user_id=user.id,
                    module_id=module.id
                ).first()
                
                # Calculate progress percentage and status
                completion_percentage = 0
                status = 'not_started'
                is_enrolled = False
                
                if user_progress:
                    completion_percentage = user_progress.progress_percentage
                    is_enrolled = True
                    if completion_percentage == 0:
                        status = 'not_started'
                    elif completion_percentage == 100:
                        status = 'completed'
                    else:
                        status = 'in_progress'
                
                # Load submodule count from file or use default
                total_items = LearningService._get_submodule_count(module.id)
                
                module_data = {
                    'id': module.id,
                    'title': module.title,  # Fixed: Use 'title' instead of 'name'
                    'description': module.description,
                    'estimated_hours': module.estimated_hours,
                    'difficulty_level': getattr(module, 'difficulty_level', 1),  # Add safe access
                    'is_recommended': getattr(module, 'is_recommended', False),  # Add safe access
                    'completion_percentage': completion_percentage,
                    'progress': completion_percentage,
                    'status': status,
                    'total_items': total_items,
                    'is_enrolled': is_enrolled
                }
                
                modules_data.append(module_data)
            
            return modules_data
        except Exception as e:
            logger.error(f"Error getting user modules progress: {str(e)}")
            # Return mock data as fallback
            return LearningService._get_mock_modules_data()
    
    @staticmethod
    def _get_mock_modules_data():
        """Fallback mock data if database fails"""
        return [
            {
                'id': 1,
                'title': 'Grunnleggende Trafikklære',
                'description': 'Lær grunnleggende trafikkskilt og regler',
                'estimated_hours': 3,
                'difficulty_level': 1,
                'is_recommended': True,
                'completion_percentage': 0,
                'progress': 0,
                'status': 'not_started',
                'total_items': 5,
                'is_enrolled': False
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
                'is_enrolled': False
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
                'is_enrolled': False
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
                'is_enrolled': False
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
                'is_enrolled': False
            }
        ]
    
    @staticmethod
    def get_user_learning_stats(user):
        """Get comprehensive learning statistics for user"""
        try:
            # Simplified stats for now
            return {
                'modules_completed': 0,
                'total_time_minutes': 0,
                'shorts_watched': 0,
                'current_streak': 0,
                'overall_progress': 0
            }
        except Exception as e:
            logger.error(f"Error getting user learning stats: {str(e)}")
            return {}
    
    @staticmethod
    def get_recommendations(user):
        """Get recommended next steps for user"""
        try:
            # Simplified recommendations for now
            return []
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    @staticmethod
    def get_module_details(module_id, user):
        """Get detailed module information with user progress"""
        try:
            # Return mock module data based on ID
            modules_info = {
                1: {
                    'id': 1,
                    'module_number': 1,
                    'title': 'Grunnleggende Trafikklære',
                    'description': 'Lær grunnleggende trafikkskilt og regler',
                    'estimated_hours': 3,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Forstå grunnleggende trafikkregler',
                        'Mestre vikepliktregler',
                        'Gjenkjenne politisignaler'
                    ]
                },
                2: {
                    'id': 2,
                    'module_number': 2,
                    'title': 'Skilt og Oppmerking',
                    'description': 'Gjenkjenn og forstå trafikkskilt',
                    'estimated_hours': 3,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Gjenkjenne fareskilt',
                        'Forstå forbudsskilt',
                        'Lese vegoppmerking',
                        'Tolke påbudsskilt',
                        'Forstå informasjonsskilt'
                    ]
                },
                3: {
                    'id': 3,
                    'module_number': 3,
                    'title': 'Kjøretøy og Teknologi',
                    'description': 'Forstå bremselengde, sikt og kjøretøyets tekniske aspekter',
                    'estimated_hours': 2,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Beregne bremselengde og reaksjonstid',
                        'Forstå sikt og lysbruk',
                        'Lære om dekk og mønsterdybde',
                        'Utføre kontrollrutiner',
                        'Forstå moderne kjøretøyteknologi'
                    ]
                },
                4: {
                    'id': 4,
                    'module_number': 4,
                    'title': 'Mennesket i Trafikken',
                    'description': 'Lær om alkohol, rus, trøtthet og menneskelige faktorer',
                    'estimated_hours': 2,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Forstå alkohol og rus påvirkning',
                        'Gjenkjenne trøtthet og distraksjoner',
                        'Utvikle risikoforståelse',
                        'Lære grunnleggende førstehjelp'
                    ]
                },
                5: {
                    'id': 5,
                    'module_number': 5,
                    'title': 'Øvingskjøring og Avsluttende Test',
                    'description': 'Øvingskjøring, eksamenstrening og forberedelse til teoriprøven',
                    'estimated_hours': 2,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Forstå ansvar under øvingskjøring',
                        'Mestre eksamenstrening',
                        'Forberede deg til teoriprøven',
                        'Øve på tidspress'
                    ]
                }
            }
            
            return modules_info.get(module_id, None)
        except Exception as e:
            logger.error(f"Error getting module details for {module_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_submodules_progress(module_id, user):
        """Get all submodules for a module with user progress"""
        try:
            # Return mock submodule data for all modules
            submodules_data = {
                1: [  # Grunnleggende Trafikklære
                    {
                        'submodule_number': 1.1,
                        'title': 'Trafikkregler',
                        'description': 'Grunnleggende trafikkregler og forskrifter',
                        'estimated_minutes': 25,
                        'difficulty_level': 1,
                        'completion_percentage': 100,
                        'status': 'completed',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.2,
                        'title': 'Vikeplikt',
                        'description': 'Forstå vikeplikt i ulike trafikksituasjoner',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 65,
                        'status': 'in_progress',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.3,
                        'title': 'Politi og trafikklys',
                        'description': 'Signaler fra politi og trafikklys',
                        'estimated_minutes': 20,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.4,
                        'title': 'Plassering og feltskifte',
                        'description': 'Riktig plassering på veien og feltskifte',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.5,
                        'title': 'Kjøring i rundkjøring',
                        'description': 'Mestre rundkjøring og navigering',
                        'estimated_minutes': 25,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    }
                ],
                2: [  # Skilt og Oppmerking
                    {
                        'submodule_number': 2.1,
                        'title': 'Fareskilt – lær mønstrene',
                        'description': 'Forstå fareskiltene som varsler om spesielle farer',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.2,
                        'title': 'Forbudsskilt – hva du IKKE kan gjøre',
                        'description': 'Lær deg forbudsskiltene som setter begrensninger',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.3,
                        'title': 'Påbudsskilt – følg instruksjonen',
                        'description': 'Forstå påbudsskiltene som gir obligatoriske instrukser',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.4,
                        'title': 'Opplysningsskilt og serviceskilt',
                        'description': 'Lær deg skiltene som gir nyttig informasjon og viser vei til tjenester',
                        'estimated_minutes': 30,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.5,
                        'title': 'Vegoppmerking – linjer og symboler',
                        'description': 'Forstå de ulike linjene og symbolene på veien',
                        'estimated_minutes': 45,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                3: [  # Kjøretøy og Teknologi
                    {
                        'submodule_number': 3.1,
                        'title': 'Bremselengde og reaksjonstid',
                        'description': 'Lær om de kritiske faktorene som bestemmer hvor lang tid og distanse du trenger for å stoppe',
                        'estimated_minutes': 45,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.2,
                        'title': 'Sikt, lysbruk og vær',
                        'description': 'Mestre kunsten å se og bli sett under alle forhold',
                        'estimated_minutes': 40,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.3,
                        'title': 'Dekk, mønsterdybde og grep',
                        'description': 'Forstå hvorfor dekkene er din viktigste forbindelse til veien',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.4,
                        'title': 'Kontrollrutiner før kjøring',
                        'description': 'Lær deg de enkle sjekkene du må gjøre før hver kjøretur',
                        'estimated_minutes': 30,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.5,
                        'title': 'Elbil, hybrid og moderne hjelpemidler',
                        'description': 'Utforsk teknologien som former fremtidens kjøring',
                        'estimated_minutes': 40,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                4: [  # Mennesket i Trafikken
                    {
                        'submodule_number': 4.1,
                        'title': 'Alkohol, rus og reaksjonsevne',
                        'description': 'Forstå hvordan alkohol og andre rusmidler påvirker kjøreevnen',
                        'estimated_minutes': 35,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.2,
                        'title': 'Trøtthet og distraksjoner',
                        'description': 'Lær å gjenkjenne og håndtere trøtthet og distraksjoner under kjøring',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.3,
                        'title': 'Risikoforståelse og kjørestrategi',
                        'description': 'Utvikle god risikoforståelse og defensive kjøreteknikker',
                        'estimated_minutes': 40,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.4,
                        'title': 'Førstehjelp og ulykkesberedskap',
                        'description': 'Lær grunnleggende førstehjelp og hvordan du reagerer ved ulykker',
                        'estimated_minutes': 45,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                5: [  # Øvingskjøring og Avsluttende Test
                    {
                        'submodule_number': 5.1,
                        'title': 'Ansvar og regler under øvingskjøring',
                        'description': 'Forstå ditt ansvar og hvilke regler som gjelder under øvingskjøring',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.2,
                        'title': 'Oppsummeringsquiz',
                        'description': 'Test din kunnskap med en omfattende quiz som dekker alle moduler',
                        'estimated_minutes': 40,
                        'difficulty_level': 4,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': False,
                        'shorts_count': 0,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.3,
                        'title': 'Eksamenstrening med tidspress',
                        'description': 'Øv på teoriprøven under realistiske tidsforhold',
                        'estimated_minutes': 50,
                        'difficulty_level': 4,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.4,
                        'title': 'Hva skjer på teoriprøven?',
                        'description': 'Forbered deg til selve teoriprøven og lær hva du kan forvente',
                        'estimated_minutes': 25,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': False
                    }
                ]
            }
            
            return submodules_data.get(module_id, [])
        except Exception as e:
            logger.error(f"Error getting submodules progress for module {module_id}: {str(e)}")
            return []
    
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
        """Get video shorts for a submodule with user progress from database"""
        try:
            # Import models from main models file
            from app.models import VideoShorts, UserShortsProgress
            
            # Query database for shorts matching this submodule
            # Convert submodule_id to match database format (decimal number)
            shorts = VideoShorts.query.filter_by(
                submodule_id=float(submodule_id),
                is_active=True
            ).order_by(VideoShorts.sequence_order).all()
            
            if not shorts:
                logger.info(f"No video shorts found for submodule {submodule_id} in database, using fallback")
                # Return fallback mock data if no database records exist
                return LearningService._get_mock_shorts_data(submodule_id, user)
            
            # Build response with user progress - flatten structure for JavaScript
            shorts_with_progress = []
            for short in shorts:
                # Get user progress for this short
                progress_record = UserShortsProgress.query.filter_by(
                    user_id=user.id,
                    shorts_id=short.id
                ).first()
                
                # Build flattened video data with progress included at top level
                video_data = {
                    # Video properties at top level for JavaScript compatibility
                    'id': short.id,
                    'title': short.title,
                    'description': short.description,
                    'file_path': short.file_path,
                    'duration_seconds': short.duration_seconds,
                    'thumbnail_path': short.thumbnail_path,
                    'view_count': short.view_count,
                    'like_count': short.like_count,
                    'sequence_order': short.sequence_order,
                    'difficulty_level': short.difficulty_level,
                    'topic_tags': short.get_topic_tags_list() if hasattr(short, 'get_topic_tags_list') else [],
                    
                    # Progress properties at top level for JavaScript compatibility
                    'watch_status': progress_record.watch_status if progress_record else 'not_watched',
                    'watch_percentage': progress_record.watch_percentage if progress_record else 0,
                    'liked': progress_record.liked if progress_record else False,
                    'watch_time_seconds': progress_record.watch_time_seconds if progress_record else 0,
                    'replay_count': progress_record.replay_count if progress_record else 0
                }
                
                shorts_with_progress.append(video_data)
            
            logger.info(f"Found {len(shorts)} video shorts for submodule {submodule_id}")
            return shorts_with_progress
            
        except Exception as e:
            logger.error(f"Error getting submodule shorts for {submodule_id}: {str(e)}")
            # Return fallback mock data on error
            return LearningService._get_mock_shorts_data(submodule_id, user)
    
    @staticmethod
    def _get_mock_shorts_data(submodule_id, user):
        """Fallback mock data if database query fails - flat structure for JavaScript"""
        # Use integer IDs for mock data to match database structure
        mock_video_data = [
            {
                # Video properties at top level
                'id': 999,  # Use integer ID that won't conflict with real data
                'title': f'Modul {submodule_id} - Grunnleggende',
                'description': f'Lær grunnleggende konsepter for modul {submodule_id}',
                'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'duration_seconds': 45,
                'thumbnail_path': '/static/images/thumbnails/default-1.jpg',
                'view_count': 0,
                'like_count': 0,
                'sequence_order': 1,
                'difficulty_level': 1,
                'topic_tags': ['grunnleggende'],
                
                # Progress properties at top level
                'watch_status': 'not_watched',
                'watch_percentage': 0,
                'liked': False,
                'watch_time_seconds': 0,
                'replay_count': 0
            }
        ]
        
        return mock_video_data
    
    @staticmethod
    def track_content_access(user, submodule_id, content_type):
        """Track that user accessed content - simplified for now"""
        try:
            # For now, just log the access
            logger.info(f"User {user.id} accessed {content_type} for submodule {submodule_id}")
        except Exception as e:
            logger.error(f"Error tracking content access: {str(e)}")
    
    # Add missing methods that are called by routes
    @staticmethod
    def get_submodule_details(submodule_id, user):
        """Get submodule details with content from ContentManager"""
        try:
            from app.learning.content_manager import ContentManager
            
            # First, let's return mock data that we know works
            # We'll debug the file loading separately
            logger.info(f"Getting submodule details for {submodule_id}")
            
            # Build submodule details with mock data for now
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
                    'status': 'not_started',
                    'completion_percentage': 0,
                    'time_spent': 0
                },
                'module': {
                    'id': int(submodule_id),
                    'title': f'Modul {int(submodule_id)}',
                    'number': int(submodule_id)
                }
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
    def mark_content_complete(user, content_type, content_id, completion_data):
        """Mark content as completed - simplified for now"""
        return {}
    
    @staticmethod
    def track_time_spent(user, content_type, content_id, time_seconds):
        """Track time spent on content - simplified for now"""
        return {}
    
    @staticmethod
    def get_next_content(user, current_content_type, current_content_id):
        """Get next recommended content - simplified for now"""
        return None
    
    @staticmethod
    def update_shorts_progress(user, shorts_id, watch_data):
        """Update user progress for watching a video short"""
        try:
            # Import models from main models file
            from app.models import VideoShorts, UserShortsProgress
            
            # Find or create progress record
            progress = UserShortsProgress.query.filter_by(
                user_id=user.id,
                shorts_id=shorts_id
            ).first()
            
            if not progress:
                # Create new progress record
                progress = UserShortsProgress(
                    user_id=user.id,
                    shorts_id=shorts_id,
                    first_watched_at=datetime.utcnow()
                )
                db.session.add(progress)
            
            # Update progress data
            if 'watch_percentage' in watch_data:
                progress.watch_percentage = watch_data['watch_percentage']
            
            if 'watch_time_seconds' in watch_data:
                progress.watch_time_seconds = watch_data['watch_time_seconds']
            
            if 'watch_status' in watch_data:
                progress.watch_status = watch_data['watch_status']
            
            # Set completion timestamp if completed
            if progress.watch_percentage >= 100 and not progress.completed_at:
                progress.completed_at = datetime.utcnow()
                progress.watch_status = 'completed'
            
            # Update last watched timestamp
            progress.last_watched_at = datetime.utcnow()
            
            # Increment view count on video
            if not progress.first_watched_at or progress.first_watched_at == progress.last_watched_at:
                video_short = VideoShorts.query.get(shorts_id)
                if video_short:
                    video_short.view_count += 1
            
            db.session.commit()
            
            logger.info(f"Updated shorts progress for user {user.id}, shorts {shorts_id}")
            return {
                'success': True,
                'watch_percentage': progress.watch_percentage,
                'watch_status': progress.watch_status
            }
            
        except Exception as e:
            logger.error(f"Error updating shorts progress: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def toggle_shorts_like(user, shorts_id):
        """Toggle like status for a video short"""
        try:
            # Import models from main models file
            from app.models import VideoShorts, UserShortsProgress
            
            # Find or create progress record
            progress = UserShortsProgress.query.filter_by(
                user_id=user.id,
                shorts_id=shorts_id
            ).first()
            
            if not progress:
                # Create new progress record
                progress = UserShortsProgress(
                    user_id=user.id,
                    shorts_id=shorts_id,
                    first_watched_at=datetime.utcnow()
                )
                db.session.add(progress)
            
            # Toggle like status
            old_liked = progress.liked
            progress.liked = not progress.liked
            
            # Update like count on video
            video_short = VideoShorts.query.get(shorts_id)
            if video_short:
                if progress.liked and not old_liked:
                    # User liked the video
                    video_short.like_count += 1
                elif not progress.liked and old_liked:
                    # User unliked the video
                    video_short.like_count = max(0, video_short.like_count - 1)
            
            db.session.commit()
            
            logger.info(f"Toggled like for user {user.id}, shorts {shorts_id}: {progress.liked}")
            return {
                'success': True,
                'liked': progress.liked,
                'like_count': video_short.like_count if video_short else 0
            }
            
        except Exception as e:
            logger.error(f"Error toggling shorts like: {str(e)}")
            db.session.rollback()
            return {'success': False, 'liked': False}
