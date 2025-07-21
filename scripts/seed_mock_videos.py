#!/usr/bin/env python3
"""
Seed Mock Videos Script
Creates mock video records in the database for testing video progress functionality.
Uses the 9XXX ID system to avoid conflicts with real videos.
"""

import sys
import os

# Add the parent directory to Python path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Video
from datetime import datetime, timezone


def seed_mock_videos():
    """Seed mock videos for all submodules (2-3 videos per submodule)"""
    
    print("🎬 Starting Mock Video Seeding...")
    
    # Define submodule structure
    submodules = [
        '1.1', '1.2', '1.3', '1.4', '1.5',
        '2.1', '2.2', '2.3', '2.4', '2.5', 
        '3.1', '3.2', '3.3', '3.4', '3.5',
        '4.1', '4.2', '4.3', '4.4',
        '5.1', '5.2', '5.3', '5.4'
    ]
    
    # Mock video URLs for variety
    mock_video_files = [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4', 
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4'
    ]
    
    # Titles for Norwegian learning content
    title_templates = [
        "Del {part}: Grunnleggende konsepter",
        "Del {part}: Praktiske eksempler", 
        "Del {part}: Avanserte teknikker",
        "Del {part}: Oppsummering",
        "Del {part}: Øvelser"
    ]
    
    videos_created = 0
    video_counter = 0
    
    try:
        # Check if mock videos already exist
        existing_mock_videos = Video.query.filter(Video.id >= 9000).count()
        if existing_mock_videos > 0:
            print(f"⚠️  Found {existing_mock_videos} existing mock videos")
            response = input("Delete existing mock videos and recreate? (y/n): ").lower().strip()
            if response == 'y':
                # Delete existing mock videos
                deleted_count = Video.query.filter(Video.id >= 9000).delete()
                db.session.commit()
                print(f"🗑️  Deleted {deleted_count} existing mock videos")
            else:
                print("❌ Cancelled - keeping existing mock videos")
                return
        
        for submodule in submodules:
            # Parse submodule (e.g., "1.1" -> module=1, sub=1)
            module_str, sub_str = submodule.split(".")
            module = int(module_str)
            sub = int(sub_str)
            
            # Create 2-3 videos per submodule (varies for realism)
            videos_per_submodule = 2 if float(submodule) % 1 != 0.5 else 3
            
            for i in range(videos_per_submodule):
                video_counter += 1
                video_id = 9000 + (module * 100) + (sub * 10) + (i + 1)  # 9111, 9112, 9113, etc.
                
                # Create video record
                video = Video(
                    id=video_id,
                    title=title_templates[i % len(title_templates)].format(part=i+1),
                    description=f"Mock video {i+1} for submodule {submodule} - Læringsvideo som forklarer viktige konsepter",
                    youtube_url=mock_video_files[video_counter % len(mock_video_files)],
                    thumbnail_filename=f"mock_{video_id}.jpg",
                    duration_seconds=45 + (i * 7),  # Vary duration: 45s, 52s, 59s
                    aspect_ratio='9:16',  # Short/vertical video format
                    theory_module_ref=submodule,
                    sequence_order=i + 1,
                    view_count=0,
                    is_active=True,
                    content_type='short',
                    created_at=datetime.now(timezone.utc)
                )
                
                db.session.add(video)
                videos_created += 1
                
                print(f"  📹 Created video {video_id}: {video.title} (Module {submodule})")
        
        # Commit all videos
        db.session.commit()
        
        print(f"\n✅ Successfully created {videos_created} mock videos!")
        print(f"🎯 Video ID range: 9111 - {9000 + (5 * 100) + (4 * 10) + 3}")
        print(f"📊 Coverage: {len(submodules)} submodules with 2-3 videos each")
        
        # Show breakdown by module
        print(f"\n📋 Mock Video Breakdown:")
        for module_num in range(1, 6):
            module_videos = Video.query.filter(
                Video.theory_module_ref.like(f"{module_num}.%"),
                Video.id >= 9000
            ).count()
            print(f"   Module {module_num}: {module_videos} videos")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding mock videos: {str(e)}")
        return False
        
    return True


def verify_seeded_videos():
    """Verify that mock videos were created correctly"""
    try:
        total_videos = Video.query.filter(Video.id >= 9000).count()
        active_videos = Video.query.filter(Video.id >= 9000, Video.is_active == True).count()
        shorts_videos = Video.query.filter(
            Video.id >= 9000, 
            Video.aspect_ratio == '9:16'
        ).count()
        
        print(f"\n🔍 Verification Results:")
        print(f"   Total mock videos: {total_videos}")
        print(f"   Active videos: {active_videos}")
        print(f"   Short videos (9:16): {shorts_videos}")
        
        # Check each submodule has videos
        submodules_with_videos = Video.query.filter(Video.id >= 9000).with_entities(Video.theory_module_ref).distinct().count()
        print(f"   Submodules with videos: {submodules_with_videos}/23")
        
        if total_videos > 0:
            print("✅ Mock videos seeded successfully!")
            return True
        else:
            print("❌ No mock videos found!")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying videos: {str(e)}")
        return False


if __name__ == '__main__':
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("🚀 Mock Video Seeding Script")
        print("=" * 50)
        
        # Seed videos
        if seed_mock_videos():
            # Verify seeding
            verify_seeded_videos()
            print(f"\n🎉 Mock video seeding complete!")
            print(f"💡 Use 'python scripts/cleanup_mock_videos.py' to remove these videos")
        else:
            print(f"\n💥 Mock video seeding failed!")
            sys.exit(1)