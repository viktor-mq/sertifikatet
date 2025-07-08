# app/learning/content_manager.py
import os
import yaml
import markdown
from typing import Dict, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages file-based learning content (markdown files, YAML configs)"""
    
    BASE_CONTENT_DIR = "learning"
    MODULES_DIR = ""
    TEMPLATES_DIR = "templates"
    
    @classmethod
    def load_module_config(cls, module_id: int) -> Optional[Dict]:
        """Load module configuration from YAML file"""
        try:
            # Find module directory by ID using your naming convention
            modules_path = Path(cls.BASE_CONTENT_DIR)
            
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir() and module_dir.name.startswith(f"{module_id}."):
                    config_file = module_dir / "module.yaml"
                    
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as file:
                            return yaml.safe_load(file)
            
            logger.warning(f"Module config not found for module_id: {module_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading module config for {module_id}: {str(e)}")
            return None
    
    @classmethod
    def get_submodule_content(cls, submodule_id: float) -> Optional[Dict]:
        """Get all content for a submodule (long.md, short.md, metadata.yaml)"""
        try:
            # Parse submodule_id to get module and submodule numbers
            module_id = int(submodule_id)
            
            # Find the submodule directory
            submodule_path = cls._find_submodule_path(submodule_id)
            
            if not submodule_path:
                logger.warning(f"Submodule path not found for: {submodule_id}")
                return None
            
            content_data = {}
            
            # Load long.md (detailed content)
            long_file = submodule_path / "long.md"
            content_file = submodule_path / "content.md"  # Fallback to old naming
            
            if long_file.exists():
                content_data['detailed'] = cls._load_markdown_file(long_file)
                content_data['content'] = content_data['detailed']  # Backward compatibility
            elif content_file.exists():
                content_data['detailed'] = cls._load_markdown_file(content_file)
                content_data['content'] = content_data['detailed']  # Backward compatibility
            
            # Load short.md (summary content)
            short_file = submodule_path / "short.md"
            summary_file = submodule_path / "summary.md"  # Fallback to old naming
            
            if short_file.exists():
                content_data['kort'] = cls._load_markdown_file(short_file)
                content_data['summary'] = content_data['kort']  # Backward compatibility
            elif summary_file.exists():
                content_data['kort'] = cls._load_markdown_file(summary_file)
                content_data['summary'] = content_data['kort']  # Backward compatibility
            
            # Load metadata.yaml
            metadata_file = submodule_path / "metadata.yaml"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as file:
                    content_data['metadata'] = yaml.safe_load(file)
            
            # Get video shorts info (videos are directly in submodule folder)
            if submodule_path:
                video_files = [f for f in submodule_path.iterdir() if f.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi']]
                content_data['shorts_available'] = len(video_files) > 0
                content_data['shorts_count'] = len(video_files)
            else:
                content_data['shorts_available'] = False
                content_data['shorts_count'] = 0
            
            return content_data
        except Exception as e:
            logger.error(f"Error getting submodule content for {submodule_id}: {str(e)}")
            return None
    
    @classmethod
    def _find_submodule_path(cls, submodule_id: float) -> Optional[Path]:
        """Find the filesystem path for a submodule using your naming convention"""
        try:
            module_id = int(submodule_id)
            modules_path = Path(cls.BASE_CONTENT_DIR)
            
            # Find module directory (e.g., "1.basic_traffic_theory")
            module_dir = None
            for dir_path in modules_path.iterdir():
                if dir_path.is_dir() and dir_path.name.startswith(f"{module_id}."):
                    module_dir = dir_path
                    break
            
            if not module_dir:
                return None
            
            # Find submodule directory (e.g., "1.2_right_of_way_rules")
            submodule_str = f"{submodule_id:.1f}"
            for subdir in module_dir.iterdir():
                if subdir.is_dir() and subdir.name.startswith(f"{submodule_str}_"):
                    return subdir
            
            return None
        except Exception as e:
            logger.error(f"Error finding submodule path for {submodule_id}: {str(e)}")
            return None
    
    @classmethod
    def _load_markdown_file(cls, file_path: Path) -> Dict:
        """Load and parse a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Use markdown library to convert to HTML
            md = markdown.Markdown(extensions=['meta', 'tables', 'fenced_code', 'toc'])
            html_content = md.convert(content)
            
            return {
                'raw_content': content,
                'html_content': html_content,
                'metadata': md.Meta if hasattr(md, 'Meta') else {},
                'file_path': str(file_path),
                'word_count': len(content.split()),
                'last_modified': file_path.stat().st_mtime
            }
        except Exception as e:
            logger.error(f"Error loading markdown file {file_path}: {str(e)}")
            return {}
