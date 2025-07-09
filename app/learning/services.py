# app/learning/services.py
from app import db
from app.learning.models import TheoryService
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
            # Return mock data for now to get the system working
            modules_data = [
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
            
            return modules_data
        except Exception as e:
            logger.error(f"Error getting user modules progress: {str(e)}")
            return []
    
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
        """Get video shorts for a submodule with user progress"""
        try:
            # Return mock video data for testing the TikTok-style player
            mock_shorts = [
                {
                    'id': 1,
                    'title': 'Trafikkregler Grunnleggende',
                    'description': 'Lær de viktigste trafikkreglene på 45 sekunder',
                    'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',  # Test video
                    'duration_seconds': 45,
                    'thumbnail_path': '/static/images/thumbnails/traffic-1.jpg',
                    'view_count': 234,
                    'like_count': 18,
                    'sequence_order': 1,
                    'difficulty_level': 1,
                    'topic_tags': ['trafikkregler', 'grunnleggende']
                },
                {
                    'id': 2,
                    'title': 'Vikeplikt Enkelt Forklart',
                    'description': 'Forstå vikeplikt med praktiske eksempler',
                    'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',  # Test video
                    'duration_seconds': 38,
                    'thumbnail_path': '/static/images/thumbnails/traffic-2.jpg',
                    'view_count': 187,
                    'like_count': 23,
                    'sequence_order': 2,
                    'difficulty_level': 2,
                    'topic_tags': ['vikeplikt', 'praksis']
                },
                {
                    'id': 3,
                    'title': 'Rundkjøring Tips',
                    'description': 'Mestre rundkjøring med disse tipsene',
                    'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',  # Test video
                    'duration_seconds': 52,
                    'thumbnail_path': '/static/images/thumbnails/traffic-3.jpg',
                    'view_count': 156,
                    'like_count': 31,
                    'sequence_order': 3,
                    'difficulty_level': 2,
                    'topic_tags': ['rundkjøring', 'avansert']
                }
            ]
            
            # Add mock progress data for each video
            shorts_with_progress = []
            for short in mock_shorts:
                # Simulate some user progress
                progress = {
                    'watch_status': 'not_watched',
                    'watch_percentage': 0,
                    'liked': False,
                    'watch_time_seconds': 0
                }
                
                # Simulate that user has watched first video
                if short['id'] == 1:
                    progress.update({
                        'watch_status': 'completed',
                        'watch_percentage': 100,
                        'watch_time_seconds': short['duration_seconds']
                    })
                elif short['id'] == 2:
                    progress.update({
                        'watch_status': 'started',
                        'watch_percentage': 65,
                        'watch_time_seconds': 25
                    })
                
                shorts_with_progress.append({
                    'short': short,
                    'progress': progress
                })
            
            return shorts_with_progress
            
        except Exception as e:
            logger.error(f"Error getting submodule shorts for {submodule_id}: {str(e)}")
            return None
    
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
        """Update shorts watch progress - simplified for now"""
        return {}
    
    @staticmethod
    def toggle_shorts_like(user, shorts_id):
        """Toggle like on shorts video - simplified for now"""
        return False
