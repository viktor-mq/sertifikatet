# app/services/content_validator.py
import os
import logging
import yaml
import markdown
from flask import current_app

logger = logging.getLogger(__name__)

class ContentValidator:
    """Service for validating learning content files and structure"""
    
    @staticmethod
    def validate_yaml_content(yaml_content):
        """Validate YAML content structure"""
        try:
            data = yaml.safe_load(yaml_content)
            
            # Check required top-level fields
            required_fields = ['id', 'title', 'description']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Validate submodules if present
            if 'submodules' in data:
                if not isinstance(data['submodules'], list):
                    return False, "Submodules must be a list"
                
                for i, submodule in enumerate(data['submodules']):
                    if not isinstance(submodule, dict):
                        return False, f"Submodule {i} must be an object"
                    
                    if 'id' not in submodule:
                        return False, f"Submodule {i} missing required field 'id'"
                    
                    if 'title' not in submodule:
                        return False, f"Submodule {i} missing required field 'title'"
            
            return True, "YAML content is valid"
            
        except yaml.YAMLError as e:
            return False, f"Invalid YAML format: {str(e)}"
        except Exception as e:
            return False, f"YAML validation error: {str(e)}"
    
    @staticmethod
    def validate_markdown_content(markdown_content):
        """Validate markdown content"""
        try:
            # Basic markdown validation
            if not markdown_content.strip():
                return False, "Markdown content is empty"
            
            # Try to parse markdown
            md = markdown.Markdown()
            html = md.convert(markdown_content)
            
            # Check for basic structure (at least one heading)
            if '#' not in markdown_content:
                return False, "Markdown should contain at least one heading (#)"
            
            # Check for potentially dangerous content
            dangerous_patterns = ['<script', 'javascript:', 'onclick=', 'onload=']
            for pattern in dangerous_patterns:
                if pattern.lower() in markdown_content.lower():
                    return False, f"Potentially dangerous content detected: {pattern}"
            
            return True, "Markdown content is valid"
            
        except Exception as e:
            return False, f"Markdown validation error: {str(e)}"
    
    @staticmethod
    def validate_video_file(file_obj):
        """Validate video file"""
        try:
            # Check file extension
            if not file_obj.filename:
                return False, "No filename provided"
            
            allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
            file_ext = os.path.splitext(file_obj.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return False, f"Invalid video format. Allowed: {', '.join(allowed_extensions)}"
            
            # Check file size (get size without affecting file position)
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            
            max_size = 300 * 1024 * 1024  # 300MB
            if file_size > max_size:
                return False, f"File too large. Maximum size: {max_size // (1024 * 1024)}MB"
            
            if file_size == 0:
                return False, "File is empty"
            
            return True, "Video file is valid"
            
        except Exception as e:
            return False, f"Video validation error: {str(e)}"
    
    @staticmethod
    def validate_directory_structure(base_path):
        """Validate learning content directory structure"""
        try:
            issues = []
            
            if not os.path.exists(base_path):
                return False, f"Base directory does not exist: {base_path}"
            
            # Check for module directories
            module_dirs = [d for d in os.listdir(base_path) 
                          if os.path.isdir(os.path.join(base_path, d)) and 
                          d.startswith(('1.', '2.', '3.', '4.', '5.'))]
            
            if not module_dirs:
                issues.append("No module directories found")
            
            for module_dir in module_dirs:
                module_path = os.path.join(base_path, module_dir)
                
                # Check for module.yaml
                yaml_path = os.path.join(module_path, 'module.yaml')
                if not os.path.exists(yaml_path):
                    issues.append(f"Missing module.yaml in {module_dir}")
                else:
                    # Validate YAML content
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            yaml_content = f.read()
                            is_valid, message = ContentValidator.validate_yaml_content(yaml_content)
                            if not is_valid:
                                issues.append(f"Invalid module.yaml in {module_dir}: {message}")
                    except Exception as e:
                        issues.append(f"Cannot read module.yaml in {module_dir}: {str(e)}")
                
                # Check for submodule directories
                submodule_dirs = [d for d in os.listdir(module_path) 
                                if os.path.isdir(os.path.join(module_path, d)) and 
                                '.' in d and d[0].isdigit()]
                
                for submodule_dir in submodule_dirs:
                    submodule_path = os.path.join(module_path, submodule_dir)
                    
                    # Check for content files
                    expected_files = ['long.md', 'short.md']
                    for expected_file in expected_files:
                        file_path = os.path.join(submodule_path, expected_file)
                        if os.path.exists(file_path):
                            # Validate markdown content
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    md_content = f.read()
                                    is_valid, message = ContentValidator.validate_markdown_content(md_content)
                                    if not is_valid:
                                        issues.append(f"Invalid {expected_file} in {module_dir}/{submodule_dir}: {message}")
                            except Exception as e:
                                issues.append(f"Cannot read {expected_file} in {module_dir}/{submodule_dir}: {str(e)}")
                    
                    # Check for videos directory
                    videos_path = os.path.join(submodule_path, 'videos')
                    if os.path.exists(videos_path):
                        video_files = [f for f in os.listdir(videos_path) 
                                     if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
                        if not video_files:
                            issues.append(f"Videos directory exists but no video files found in {module_dir}/{submodule_dir}")
            
            if issues:
                return False, "; ".join(issues)
            
            return True, "Directory structure is valid"
            
        except Exception as e:
            return False, f"Directory validation error: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        import re
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Keep only alphanumeric characters, dots, hyphens, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Remove multiple dots
        filename = re.sub(r'\.+', '.', filename)
        
        # Ensure filename is not empty
        if not filename or filename == '.':
            filename = 'untitled'
        
        return filename
    
    @staticmethod
    def check_path_traversal(file_path):
        """Check for path traversal attacks"""
        # Normalize the path and check for dangerous patterns
        normalized = os.path.normpath(file_path)
        
        # Check for directory traversal attempts
        dangerous_patterns = ['..', '~', '/', '\\\\']
        for pattern in dangerous_patterns:
            if pattern in file_path:
                return False, f"Dangerous path pattern detected: {pattern}"
        
        return True, "Path is safe"
