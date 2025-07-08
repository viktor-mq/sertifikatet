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
                    'estimated_hours': 2,
                    'difficulty_level': 2,
                    'is_recommended': False,
                    'completion_percentage': 0,
                    'progress': 0,
                    'status': 'not_started',
                    'total_items': 3,
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
            if module_id == 1:
                return {
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
                }
            elif module_id == 2:
                return {
                    'id': 2,
                    'module_number': 2,
                    'title': 'Skilt og Oppmerking',
                    'description': 'Gjenkjenn og forstå trafikkskilt',
                    'estimated_hours': 2,
                    'completion_percentage': 0,
                    'status': 'not_started',
                    'time_spent': 0,
                    'learning_objectives': [
                        'Gjenkjenne fareskilt',
                        'Forstå forbudsskilt',
                        'Lese vegoppmerking'
                    ]
                }
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting module details for {module_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_submodules_progress(module_id, user):
        """Get all submodules for a module with user progress"""
        try:
            # Return mock submodule data for testing
            if module_id == 1:  # Grunnleggende Trafikklære
                return [
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
                        'title': 'Rundkjøring',
                        'description': 'Navigering gjennom rundkjøringer',
                        'estimated_minutes': 25,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    }
                ]
            elif module_id == 2:  # Skilt og Oppmerking
                return [
                    {
                        'submodule_number': 2.1,
                        'title': 'Trafikkskilt',
                        'description': 'Gjenkjenn og forstå alle typer trafikkskilt',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.2,
                        'title': 'Veioppmerking',
                        'description': 'Betydningen av ulike veioppmarkinger',
                        'estimated_minutes': 15,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': False
                    }
                ]
            else:
                return []
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
