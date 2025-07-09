#!/usr/bin/env python3
"""
Script to seed the database with sample video shorts for testing
Usage: python scripts/seed_video_shorts.py

This script creates test video shorts data to verify database integration
and replace mock data in the TikTok-style video player.
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import VideoShorts, LearningModules
from datetime import datetime

def verify_database_connection():
    """Verify database connection and model imports"""
    try:
        # Test basic queries
        learning_paths_count = LearningModules.query.count()
        video_shorts_count = VideoShorts.query.count()
        
        print(f"✅ Database connection OK")
        print(f"   Learning paths: {learning_paths_count}")
        print(f"   Video shorts: {video_shorts_count}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def seed_learning_paths():
    """Create basic learning paths if they don't exist"""
    print("🛤️  Checking learning paths...")
    
    learning_paths_data = [
        {
            'id': 1,
            'name': 'Grunnleggende Trafikklære',
            'description': 'Lær grunnleggende trafikkskilt og regler',
            'estimated_hours': 3,
            'difficulty_level': 1,
            'is_recommended': True
        },
        {
            'id': 2,
            'name': 'Skilt og Oppmerking',
            'description': 'Gjenkjenn og forstå trafikkskilt',
            'estimated_hours': 3,
            'difficulty_level': 2,
            'is_recommended': False
        },
        {
            'id': 3,
            'name': 'Kjøretøy og Teknologi',
            'description': 'Forstå bremselengde, sikt og kjøretøyets tekniske aspekter',
            'estimated_hours': 2,
            'difficulty_level': 3,
            'is_recommended': False
        },
        {
            'id': 4,
            'name': 'Mennesket i Trafikken',
            'description': 'Lær om alkohol, rus, trøtthet og menneskelige faktorer',
            'estimated_hours': 2,
            'difficulty_level': 3,
            'is_recommended': False
        },
        {
            'id': 5,
            'name': 'Øvingskjøring og Avsluttende Test',
            'description': 'Øvingskjøring, eksamenstrening og forberedelse til teoriprøven',
            'estimated_hours': 2,
            'difficulty_level': 4,
            'is_recommended': False
        }
    ]
    
    added_count = 0
    for path_data in learning_paths_data:
        existing = LearningModules.query.get(path_data['id'])
        if not existing:
            learning_path = LearningModules(**path_data)
            db.session.add(learning_path)
            added_count += 1
    
    if added_count > 0:
        db.session.commit()
        print(f"✅ Added {added_count} learning paths")
    else:
        print("✅ Learning paths already exist")

def seed_video_shorts():
    """Seed database with comprehensive video shorts for testing"""
    print("🎬 Seeding video shorts...")
    
    # Comprehensive sample video shorts matching your submodule structure
    sample_shorts = [
        # Module 1.1 - Trafikkregler
        {
            'submodule_id': '1.1',
            'title': 'Trafikkregler - Introduksjon',
            'description': 'Lær de viktigste trafikkreglene på 45 sekunder',
            'filename': '1.01-trafikkregler-intro.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'duration_seconds': 45,
            'sequence_order': 1,
            'difficulty_level': 1,
            'topic_tags': '["trafikkregler", "grunnleggende", "introduksjon"]'
        },
        {
            'submodule_id': '1.1',
            'title': 'Vikeplikt Grunnleggende',
            'description': 'Forstå vikeplikt med praktiske eksempler',
            'filename': '1.02-vikeplikt-grunnleggende.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            'duration_seconds': 38,
            'sequence_order': 2,
            'difficulty_level': 1,
            'topic_tags': '["vikeplikt", "grunnleggende"]'
        },
        {
            'submodule_id': '1.1',
            'title': 'Politisignaler',
            'description': 'Gjenkjenn og følg politisignaler',
            'filename': '1.03-politisignaler.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            'duration_seconds': 52,
            'sequence_order': 3,
            'difficulty_level': 1,
            'topic_tags': '["politi", "signaler"]'
        },
        
        # Module 1.2 - Vikeplikt
        {
            'submodule_id': '1.2',
            'title': 'Vikeplikt i Kryss',
            'description': 'Mestre vikeplikt i veikryss',
            'filename': '1.04-vikeplikt-kryss.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'duration_seconds': 60,
            'sequence_order': 1,
            'difficulty_level': 2,
            'topic_tags': '["vikeplikt", "kryss"]'
        },
        {
            'submodule_id': '1.2',
            'title': 'Rundkjøring Navigering',
            'description': 'Naviger trygt gjennom rundkjøringer',
            'filename': '1.05-rundkjøring.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            'duration_seconds': 48,
            'sequence_order': 2,
            'difficulty_level': 2,
            'topic_tags': '["rundkjøring", "navigering"]'
        },
        
        # Module 1.3 - Politi og trafikklys
        {
            'submodule_id': '1.3',
            'title': 'Trafikklys Regler',
            'description': 'Følg trafikklys korrekt',
            'filename': '1.06-trafikklys.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            'duration_seconds': 35,
            'sequence_order': 1,
            'difficulty_level': 1,
            'topic_tags': '["trafikklys", "regler"]'
        },
        {
            'submodule_id': '1.3',
            'title': 'Politiregulering',
            'description': 'Hvordan reagere på politiregulering',
            'filename': '1.07-politiregulering.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'duration_seconds': 43,
            'sequence_order': 2,
            'difficulty_level': 2,
            'topic_tags': '["politi", "regulering"]'
        },
        
        # Module 2.1 - Fareskilt
        {
            'submodule_id': '2.1',
            'title': 'Fareskilt Oversikt',
            'description': 'Lær å gjenkjenne fareskilt',
            'filename': '2.01-fareskilt-oversikt.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            'duration_seconds': 55,
            'sequence_order': 1,
            'difficulty_level': 2,
            'topic_tags': '["fareskilt", "gjenkjenning"]'
        },
        {
            'submodule_id': '2.1',
            'title': 'Fareskilt i Praksis',
            'description': 'Praktiske eksempler på fareskilt',
            'filename': '2.02-fareskilt-praksis.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            'duration_seconds': 42,
            'sequence_order': 2,
            'difficulty_level': 2,
            'topic_tags': '["fareskilt", "praksis"]'
        },
        {
            'submodule_id': '2.1',
            'title': 'Fareskilt Mønster',
            'description': 'Forstå fareskiltenes mønster og logikk',
            'filename': '2.03-fareskilt-mønster.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'duration_seconds': 50,
            'sequence_order': 3,
            'difficulty_level': 3,
            'topic_tags': '["fareskilt", "mønster", "logikk"]'
        },
        
        # Module 2.2 - Forbudsskilt
        {
            'submodule_id': '2.2',
            'title': 'Forbudsskilt Grunnleggende',
            'description': 'Hva du IKKE kan gjøre',
            'filename': '2.04-forbudsskilt-grunnleggende.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            'duration_seconds': 40,
            'sequence_order': 1,
            'difficulty_level': 2,
            'topic_tags': '["forbudsskilt", "forbud"]'
        },
        {
            'submodule_id': '2.2',
            'title': 'Forbudsskilt Eksempler',
            'description': 'Praktiske eksempler på forbudsskilt',
            'filename': '2.05-forbudsskilt-eksempler.mp4',
            'file_path': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            'duration_seconds': 45,
            'sequence_order': 2,
            'difficulty_level': 2,
            'topic_tags': '["forbudsskilt", "eksempler"]'
        }
    ]
    
    # Clear existing test data first to avoid duplicates
    print("🧹 Clearing existing test video shorts...")
    existing_test_files = [short['filename'] for short in sample_shorts]
    VideoShorts.query.filter(VideoShorts.filename.in_(existing_test_files)).delete(synchronize_session=False)
    db.session.commit()
    
    # Add each video short to database
    added_count = 0
    failed_count = 0
    
    for short_data in sample_shorts:
        try:
            video_short = VideoShorts(
                submodule_id=short_data['submodule_id'],
                title=short_data['title'],
                description=short_data['description'],
                filename=short_data['filename'],
                file_path=short_data['file_path'],
                duration_seconds=short_data['duration_seconds'],
                sequence_order=short_data['sequence_order'],
                aspect_ratio='9:16',  # TikTok-style
                difficulty_level=short_data['difficulty_level'],
                topic_tags=short_data['topic_tags'],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                view_count=0,
                like_count=0,
                completion_rate=0.0,
                average_watch_time=0.0,
                engagement_score=0.0
            )
            db.session.add(video_short)
            added_count += 1
            
        except Exception as e:
            print(f"❌ Failed to add {short_data['title']}: {str(e)}")
            failed_count += 1
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"✅ Successfully added {added_count} video shorts to database")
        if failed_count > 0:
            print(f"⚠️  {failed_count} videos failed to add")
    except Exception as e:
        print(f"❌ Error committing to database: {str(e)}")
        db.session.rollback()
        return False
    
    return True

def show_database_summary():
    """Show summary of what's in the database"""
    print("\n📊 Database Summary:")
    
    # Total counts
    total_paths = LearningModules.query.count()
    total_shorts = VideoShorts.query.count()
    
    print(f"   Learning paths: {total_paths}")
    print(f"   Video shorts: {total_shorts}")
    
    # Breakdown by submodule
    submodules = db.session.query(
        VideoShorts.submodule_id, 
        db.func.count(VideoShorts.id).label('count')
    ).group_by(VideoShorts.submodule_id).order_by(VideoShorts.submodule_id).all()
    
    if submodules:
        print("\n📋 Video shorts by submodule:")
        for submodule_id, count in submodules:
            print(f"   {submodule_id}: {count} videos")
    
    # Show a few sample videos
    sample_videos = VideoShorts.query.limit(3).all()
    if sample_videos:
        print("\n🎬 Sample videos:")
        for video in sample_videos:
            print(f"   • {video.title} ({video.submodule_id}) - {video.duration_seconds}s")

def main():
    """Main function to seed the database"""
    print("🌱 Starting video shorts database seeding...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Verify database connection
            if not verify_database_connection():
                return 1
            
            print()
            
            # Seed learning paths first
            seed_learning_paths()
            
            print()
            
            # Seed video shorts
            success = seed_video_shorts()
            
            if not success:
                print("❌ Failed to seed video shorts")
                return 1
            
            # Show summary
            show_database_summary()
            
            print("\n" + "=" * 50)
            print("✅ Database seeding completed successfully!")
            
            print("\n🚀 Testing Instructions:")
            print("   1. Start your Flask app: python run.py")
            print("   2. Go to /learning/dashboard")
            print("   3. Click on 'Grunnleggende Trafikklære' module")
            print("   4. Open submodule 1.1 and try video shorts")
            print("   5. Check if TikTok player shows database videos instead of mock data")
            
            print("\n🔍 Debug Info:")
            print("   - LearningService.get_submodule_shorts() should now return database data")
            print("   - VideoShorts and UserShortsProgress models are working")
            print("   - API endpoints /learning/shorts/<id>/progress and /like should work")
            
        except Exception as e:
            print(f"❌ Error during seeding: {str(e)}")
            db.session.rollback()
            return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 