#!/usr/bin/env python3
"""
Cleanup Mock Videos Script
Removes all mock video records (ID >= 9000) from the database.
Also removes associated video_progress records via CASCADE.
"""

import sys
import os

# Add the parent directory to Python path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Video, VideoProgress
from datetime import datetime


def cleanup_mock_videos():
    """Remove all mock videos and associated progress records"""
    
    print("🧹 Starting Mock Video Cleanup...")
    
    try:
        # Get counts before deletion
        mock_videos = Video.query.filter(Video.id >= 9000).all()
        video_count = len(mock_videos)
        
        # Get associated progress records count
        mock_video_ids = [v.id for v in mock_videos]
        progress_count = VideoProgress.query.filter(VideoProgress.video_id.in_(mock_video_ids)).count() if mock_video_ids else 0
        
        if video_count == 0:
            print("✨ No mock videos found to clean up")
            return True
            
        print(f"📊 Found {video_count} mock videos")
        print(f"📈 Found {progress_count} associated progress records")
        
        # Show breakdown by module
        print(f"\n📋 Mock Videos by Module:")
        for module_num in range(1, 6):
            module_videos = [v for v in mock_videos if v.theory_module_ref and v.theory_module_ref.startswith(f"{module_num}.")]
            if module_videos:
                print(f"   Module {module_num}: {len(module_videos)} videos")
                for video in module_videos[:3]:  # Show first 3 as examples
                    print(f"      - {video.id}: {video.title}")
                if len(module_videos) > 3:
                    print(f"      ... and {len(module_videos) - 3} more")
        
        # Ask for confirmation
        print(f"\n⚠️  This will permanently delete:")
        print(f"   • {video_count} mock videos (IDs 9000+)")
        print(f"   • {progress_count} progress records (CASCADE)")
        
        response = input(f"\nContinue with deletion? (y/n): ").lower().strip()
        if response != 'y':
            print("❌ Cancelled - no videos deleted")
            return False
            
        # Perform deletion
        print(f"\n🗑️  Deleting mock videos...")
        
        # Delete videos (progress records will be deleted automatically via CASCADE)
        deleted_videos = Video.query.filter(Video.id >= 9000).delete()
        db.session.commit()
        
        print(f"✅ Successfully deleted {deleted_videos} mock videos!")
        print(f"📈 Associated progress records deleted automatically (CASCADE)")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error during cleanup: {str(e)}")
        return False


def verify_cleanup():
    """Verify that mock videos were deleted correctly"""
    try:
        remaining_videos = Video.query.filter(Video.id >= 9000).count()
        remaining_progress = VideoProgress.query.filter(VideoProgress.video_id >= 9000).count()
        
        print(f"\n🔍 Verification Results:")
        print(f"   Remaining mock videos: {remaining_videos}")
        print(f"   Remaining mock progress records: {remaining_progress}")
        
        if remaining_videos == 0 and remaining_progress == 0:
            print("✅ Cleanup completed successfully!")
            return True
        else:
            print("⚠️  Some mock data may still remain")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying cleanup: {str(e)}")
        return False


def show_current_state():
    """Show current state of mock videos in database"""
    try:
        mock_videos = Video.query.filter(Video.id >= 9000).count()
        mock_progress = VideoProgress.query.filter(VideoProgress.video_id >= 9000).count()
        
        print(f"📊 Current Database State:")
        print(f"   Mock videos (ID >= 9000): {mock_videos}")
        print(f"   Mock progress records: {mock_progress}")
        
        if mock_videos > 0:
            # Show some examples
            sample_videos = Video.query.filter(Video.id >= 9000).limit(5).all()
            print(f"\n📋 Sample Mock Videos:")
            for video in sample_videos:
                print(f"   • {video.id}: {video.title} (Module {video.theory_module_ref})")
        
        return mock_videos > 0
        
    except Exception as e:
        print(f"❌ Error checking database state: {str(e)}")
        return False


if __name__ == '__main__':
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("🧹 Mock Video Cleanup Script")
        print("=" * 50)
        
        # Show current state
        has_mock_videos = show_current_state()
        
        if has_mock_videos:
            print()
            # Perform cleanup
            if cleanup_mock_videos():
                # Verify cleanup
                verify_cleanup()
                print(f"\n🎉 Mock video cleanup complete!")
                print(f"💡 Use 'python scripts/seed_mock_videos.py' to recreate mock videos")
            else:
                print(f"\n💥 Mock video cleanup failed!")
                sys.exit(1)
        else:
            print(f"\n✨ No cleanup needed - database is clean!")