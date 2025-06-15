# app/video/utils.py
import os
import subprocess
from werkzeug.utils import secure_filename
from flask import current_app
import hashlib
from datetime import datetime

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'avi'}
ALLOWED_SUBTITLE_EXTENSIONS = {'vtt', 'srt'}


def allowed_video_file(filename):
    """Check if the uploaded file is a valid video format"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_subtitle_file(filename):
    """Check if the uploaded file is a valid subtitle format"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_SUBTITLE_EXTENSIONS


def generate_unique_filename(original_filename, prefix=''):
    """Generate a unique filename using timestamp and hash"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_filename(original_filename))
    
    # Create a hash of the original filename
    hash_object = hashlib.md5(original_filename.encode())
    hash_hex = hash_object.hexdigest()[:8]
    
    # Combine everything
    unique_name = f"{prefix}{timestamp}_{name}_{hash_hex}{ext}"
    return unique_name


def save_video_file(file, folder='videos'):
    """Save uploaded video file"""
    if file and allowed_video_file(file.filename):
        filename = generate_unique_filename(file.filename, 'video_')
        
        # Create directory if it doesn't exist
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        return filename
    return None


def save_subtitle_file(file, folder='videos/subtitles'):
    """Save uploaded subtitle file"""
    if file and allowed_subtitle_file(file.filename):
        filename = generate_unique_filename(file.filename, 'sub_')
        
        # Create directory if it doesn't exist
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        return filename
    return None


def generate_thumbnail(video_filename, folder='videos', thumbnail_folder='videos/thumbnails'):
    """Generate thumbnail from video file using ffmpeg"""
    try:
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, video_filename)
        
        # Create thumbnail directory
        thumbnail_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], thumbnail_folder)
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        # Generate thumbnail filename
        name, _ = os.path.splitext(video_filename)
        thumbnail_filename = f"{name}_thumb.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        
        # Use ffmpeg to extract frame at 5 seconds (or first frame if video is shorter)
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', '00:00:05',
            '-vframes', '1',
            '-vf', 'scale=640:360',
            '-y',
            thumbnail_path
        ]
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return thumbnail_filename
        else:
            current_app.logger.error(f"FFmpeg error: {result.stderr}")
            
            # Try again with first frame if 5 seconds fails
            cmd[4] = '00:00:00'  # Change timestamp to 0
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return thumbnail_filename
                
    except Exception as e:
        current_app.logger.error(f"Thumbnail generation error: {str(e)}")
    
    return None


def get_video_duration(video_filename, folder='videos'):
    """Get video duration in seconds using ffprobe"""
    try:
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, video_filename)
        
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return int(duration)
            
    except Exception as e:
        current_app.logger.error(f"Duration extraction error: {str(e)}")
    
    return None


def convert_srt_to_vtt(srt_filename, folder='videos/subtitles'):
    """Convert SRT subtitle file to WebVTT format"""
    try:
        srt_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, srt_filename)
        vtt_filename = srt_filename.replace('.srt', '.vtt')
        vtt_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, vtt_filename)
        
        with open(srt_path, 'r', encoding='utf-8') as srt_file:
            srt_content = srt_file.read()
        
        # Convert SRT to VTT
        vtt_content = "WEBVTT\n\n"
        
        # Replace commas with dots in timestamps
        srt_content = srt_content.replace(',', '.')
        
        # Split into subtitle blocks
        blocks = srt_content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # Skip the number line
                timestamp = lines[1]
                text = '\n'.join(lines[2:])
                vtt_content += f"{timestamp}\n{text}\n\n"
        
        # Write VTT file
        with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
            vtt_file.write(vtt_content)
        
        return vtt_filename
        
    except Exception as e:
        current_app.logger.error(f"SRT to VTT conversion error: {str(e)}")
        return None


def validate_youtube_url(url):
    """Validate and extract YouTube video ID"""
    import re
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


# Register the format_duration filter for Jinja2
def register_filters(app):
    """Register custom Jinja2 filters"""
    app.jinja_env.filters['format_duration'] = format_duration
