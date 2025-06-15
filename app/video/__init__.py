# app/video/__init__.py
from flask import Blueprint

# Import blueprints
from .routes import video_bp
from .api import video_api_bp

# Import services and utils for external use
from .services import VideoService
from .utils import register_filters

__all__ = ['video_bp', 'video_api_bp', 'VideoService', 'register_filters']
