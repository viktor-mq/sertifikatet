# app/services/file_upload.py
import os
import logging
import json
import yaml
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from .. import db
from ..models import LearningModules, LearningSubmodules, VideoShorts

logger = logging.getLogger(__name__)

class FileUploadService:
    """Service for handling file uploads and directory management for learning content"""
    
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'md', 'txt', 'yaml', 'yml'}
    MAX_VIDEO_SIZE = 300 * 1024 * 1024  # 300MB
    MAX_DOCUMENT_SIZE = 1 * 1024 * 1024  # 1MB
    
    @staticmethod
    def allowed_file(filename, file_type='document'):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        if file_type == 'video':
            return extension in FileUploadService.ALLOWED_VIDEO_EXTENSIONS
        else:
            return extension in FileUploadService.ALLOWED_DOCUMENT_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_obj, file_type='document'):
        """Validate file size"""
        # Get file size
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        max_size = FileUploadService.MAX_VIDEO_SIZE if file_type == 'video' else FileUploadService.MAX_DOCUMENT_SIZE
        
        return file_size <= max_size
    
    @staticmethod
    def create_module_directory(module_number, module_title):
        """Create directory structure for a new module"""
        try:
            # Create safe directory name
            safe_title = secure_filename(module_title.lower().replace(' ', '_'))
            module_dir_name = f"{module_number}.{safe_title}"
            
            # Get learning content directory
            learning_base = os.path.join(current_app.root_path, '..', 'learning')
            module_path = os.path.join(learning_base, module_dir_name)
            
            # Create module directory
            os.makedirs(module_path, exist_ok=True)
            
            # Create images subdirectory
            images_path = os.path.join(module_path, 'images')
            os.makedirs(images_path, exist_ok=True)
            
            logger.info(f"Created module directory: {module_path}")
            return module_path, module_dir_name
            
        except Exception as e:
            logger.error(f"Error creating module directory: {str(e)}")
            raise
    
    @staticmethod
    def create_submodule_directory(module_dir_name, submodule_number, submodule_title):
        """Create directory structure for a new submodule"""
        try:
            # Create safe directory name
            safe_title = secure_filename(submodule_title.lower().replace(' ', '_'))
            submodule_dir_name = f"{submodule_number}-{safe_title}"
            
            # Get learning content directory
            learning_base = os.path.join(current_app.root_path, '..', 'learning')
            module_path = os.path.join(learning_base, module_dir_name)
            submodule_path = os.path.join(module_path, submodule_dir_name)
            
            # Create submodule directory
            os.makedirs(submodule_path, exist_ok=True)
            
            # Create videos subdirectory for shorts
            videos_path = os.path.join(submodule_path, 'videos')
            os.makedirs(videos_path, exist_ok=True)
            
            logger.info(f"Created submodule directory: {submodule_path}")
            return submodule_path, submodule_dir_name
            
        except Exception as e:
            logger.error(f"Error creating submodule directory: {str(e)}")
            raise
    
    @staticmethod
    def upload_module_yaml(module_id, yaml_content):
        """Upload and validate module.yaml file"""
        try:
            # Get module from database
            module = LearningModules.query.get(module_id)
            if not module:
                raise ValueError(f"Module {module_id} not found")
            
            # Parse YAML content
            try:
                yaml_data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format: {str(e)}")
            
            # Validate required fields
            required_fields = ['id', 'title', 'description']
            for field in required_fields:
                if field not in yaml_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create module directory if it doesn't exist
            if not module.content_directory:
                module_path, module_dir_name = FileUploadService.create_module_directory(
                    module.module_number, module.title
                )
                module.content_directory = module_dir_name
            else:
                learning_base = os.path.join(current_app.root_path, '..', 'learning')
                module_path = os.path.join(learning_base, module.content_directory)
            
            # Save YAML file
            yaml_file_path = os.path.join(module_path, 'module.yaml')
            with open(yaml_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
            
            # Update module metadata
            module.last_content_update = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Uploaded module.yaml for module {module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading module YAML: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def upload_markdown_content(submodule_id, content_type, markdown_content):
        """Upload markdown content (long.md or short.md)"""
        try:
            # Get submodule from database
            submodule = LearningSubmodules.query.get(submodule_id)
            if not submodule:
                raise ValueError(f"Submodule {submodule_id} not found")
            
            # Get module
            module = LearningModules.query.get(submodule.module_id)
            if not module or not module.content_directory:
                raise ValueError("Module directory not found")
            
            # Validate content type
            if content_type not in ['long', 'short']:
                raise ValueError("Content type must be 'long' or 'short'")
            
            # Create submodule directory if needed
            if not submodule.content_file_path:
                submodule_path, submodule_dir_name = FileUploadService.create_submodule_directory(
                    module.content_directory, submodule.submodule_number, submodule.title
                )
                # Update submodule paths
                submodule.content_file_path = f"{submodule_dir_name}/long.md"
                submodule.summary_file_path = f"{submodule_dir_name}/short.md"
                submodule.shorts_directory = f"{submodule_dir_name}/videos"
            else:
                learning_base = os.path.join(current_app.root_path, '..', 'learning')
                submodule_dir = os.path.dirname(submodule.content_file_path)
                submodule_path = os.path.join(learning_base, module.content_directory, submodule_dir)
            
            # Save markdown file
            filename = f"{content_type}.md"
            file_path = os.path.join(submodule_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Update submodule metadata
            if content_type == 'long':
                submodule.ai_generated_content = False
            else:
                submodule.ai_generated_summary = False
            
            submodule.last_content_update = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Uploaded {content_type}.md for submodule {submodule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading markdown content: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def upload_video_short(submodule_id, video_file, video_metadata):
        """Upload video short file"""
        try:
            # Get submodule from database
            submodule = LearningSubmodules.query.get(submodule_id)
            if not submodule:
                raise ValueError(f"Submodule {submodule_id} not found")
            
            # Get module
            module = LearningModules.query.get(submodule.module_id)
            if not module or not module.content_directory:
                raise ValueError("Module directory not found")
            
            # Validate file
            if not FileUploadService.allowed_file(video_file.filename, 'video'):
                raise ValueError("Invalid video file format")
            
            if not FileUploadService.validate_file_size(video_file, 'video'):
                raise ValueError("Video file too large")
            
            # Create safe filename
            safe_filename = secure_filename(video_file.filename)
            
            # Ensure submodule directory exists
            if not submodule.shorts_directory:
                submodule_path, submodule_dir_name = FileUploadService.create_submodule_directory(
                    module.content_directory, submodule.submodule_number, submodule.title
                )
                submodule.shorts_directory = f"{submodule_dir_name}/videos"
            
            # Get video directory
            learning_base = os.path.join(current_app.root_path, '..', 'learning')
            video_dir = os.path.join(learning_base, module.content_directory, submodule.shorts_directory)
            os.makedirs(video_dir, exist_ok=True)
            
            # Save video file
            video_path = os.path.join(video_dir, safe_filename)
            video_file.save(video_path)
            
            # Create database record for video short
            next_sequence = VideoShorts.query.filter_by(
                submodule_id=submodule.submodule_number
            ).count() + 1
            
            video_short = VideoShorts(
                submodule_id=float(submodule.submodule_number),
                title=video_metadata.get('title', f'Video {next_sequence}'),
                description=video_metadata.get('description', ''),
                filename=safe_filename,
                file_path=os.path.join(submodule.shorts_directory, safe_filename),
                duration_seconds=video_metadata.get('duration_seconds', 60),
                sequence_order=next_sequence,
                aspect_ratio='9:16',  # Default for shorts
                difficulty_level=video_metadata.get('difficulty_level', 1),
                is_active=True
            )
            
            db.session.add(video_short)
            
            # Update submodule counts
            submodule.has_video_shorts = True
            submodule.shorts_count = VideoShorts.query.filter_by(
                submodule_id=submodule.submodule_number
            ).count() + 1
            submodule.last_content_update = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Uploaded video short for submodule {submodule_id}: {safe_filename}")
            return video_short.id
            
        except Exception as e:
            logger.error(f"Error uploading video short: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def delete_content(content_type, content_id):
        """Delete content and associated files"""
        try:
            if content_type == 'module':
                module = LearningModules.query.get(content_id)
                if module and module.content_directory:
                    # Delete directory
                    learning_base = os.path.join(current_app.root_path, '..', 'learning')
                    module_path = os.path.join(learning_base, module.content_directory)
                    if os.path.exists(module_path):
                        import shutil
                        shutil.rmtree(module_path)
                    
                    # Delete database record
                    db.session.delete(module)
            
            elif content_type == 'submodule':
                submodule = LearningSubmodules.query.get(content_id)
                if submodule:
                    # Delete submodule directory
                    module = LearningModules.query.get(submodule.module_id)
                    if module and module.content_directory and submodule.content_file_path:
                        learning_base = os.path.join(current_app.root_path, '..', 'learning')
                        submodule_dir = os.path.dirname(submodule.content_file_path)
                        submodule_path = os.path.join(learning_base, module.content_directory, submodule_dir)
                        if os.path.exists(submodule_path):
                            import shutil
                            shutil.rmtree(submodule_path)
                    
                    # Delete database record
                    db.session.delete(submodule)
            
            elif content_type == 'video_short':
                video_short = VideoShorts.query.get(content_id)
                if video_short:
                    # Delete video file
                    if video_short.file_path:
                        learning_base = os.path.join(current_app.root_path, '..', 'learning')
                        full_path = os.path.join(learning_base, video_short.file_path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    
                    # Delete database record
                    db.session.delete(video_short)
            
            db.session.commit()
            logger.info(f"Deleted {content_type} {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting content: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def validate_content_structure():
        """Validate that all files exist and database is in sync"""
        try:
            issues = []
            learning_base = os.path.join(current_app.root_path, '..', 'learning')
            
            # Check all modules
            modules = LearningModules.query.filter_by(is_active=True).all()
            for module in modules:
                if module.content_directory:
                    module_path = os.path.join(learning_base, module.content_directory)
                    if not os.path.exists(module_path):
                        issues.append(f"Module directory missing: {module.content_directory}")
                    
                    # Check for module.yaml
                    yaml_path = os.path.join(module_path, 'module.yaml')
                    if not os.path.exists(yaml_path):
                        issues.append(f"module.yaml missing for: {module.title}")
            
            # Check all submodules
            submodules = LearningSubmodules.query.filter_by(is_active=True).all()
            for submodule in submodules:
                if submodule.content_file_path:
                    module = LearningModules.query.get(submodule.module_id)
                    if module and module.content_directory:
                        full_path = os.path.join(learning_base, module.content_directory, submodule.content_file_path)
                        if not os.path.exists(full_path):
                            issues.append(f"Content file missing: {submodule.content_file_path}")
            
            # Check video shorts
            video_shorts = VideoShorts.query.filter_by(is_active=True).all()
            for video in video_shorts:
                if video.file_path:
                    full_path = os.path.join(learning_base, video.file_path)
                    if not os.path.exists(full_path):
                        issues.append(f"Video file missing: {video.file_path}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating content structure: {str(e)}")
            return [f"Validation error: {str(e)}"]
