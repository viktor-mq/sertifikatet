# app/utils/settings_service.py
"""
Settings service for managing system-wide configuration.
Provides caching, validation, and convenient access to SystemSettings.
"""
import logging
from typing import Dict, List, Any, Optional
from flask import current_app
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service for managing system settings with caching and validation.
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = timedelta(minutes=5)  # Cache settings for 5 minutes
        self._last_cache_update = {}
        
        # ML Settings defaults - these will be used if settings don't exist in DB
        self.ML_SETTINGS_DEFAULTS = {
            'ml_system_enabled': {
                'value': True,
                'type': 'boolean',
                'description': 'Master switch for all machine learning features',
                'category': 'ml'
            },
            'ml_adaptive_learning': {
                'value': True,
                'type': 'boolean',
                'description': 'Enable adaptive question selection based on user skill',
                'category': 'ml'
            },
            'ml_skill_tracking': {
                'value': True,
                'type': 'boolean',
                'description': 'Track and analyze user skill development over time',
                'category': 'ml'
            },
            'ml_difficulty_prediction': {
                'value': True,
                'type': 'boolean',
                'description': 'Predict question difficulty using machine learning',
                'category': 'ml'
            },
            'ml_data_collection': {
                'value': True,
                'type': 'boolean',
                'description': 'Collect response times and behavioral data for ML training',
                'category': 'ml'
            },
            'ml_model_retraining': {
                'value': True,
                'type': 'boolean',
                'description': 'Automatically retrain ML models with new data',
                'category': 'ml'
            },
            'ml_fallback_mode': {
                'value': 'random',
                'type': 'string',
                'description': 'Fallback question selection when ML is disabled: random, difficulty, category, legacy',
                'category': 'ml'
            },
            'ml_learning_rate': {
                'value': 0.05,
                'type': 'float',
                'description': 'Learning rate for ML algorithms (0.01-0.1)',
                'category': 'ml'
            },
            'ml_adaptation_strength': {
                'value': 0.5,
                'type': 'float',
                'description': 'How aggressively to adapt difficulty (0.1-1.0)',
                'category': 'ml'
            },
            'ml_update_frequency': {
                'value': 'real-time',
                'type': 'string',
                'description': 'How often ML models are retrained: real-time, hourly, daily, weekly',
                'category': 'ml'
            }
        }
    
    def _get_from_cache(self, key: str) -> Any:
        """Get setting from cache if valid"""
        if key not in self._cache or key not in self._last_cache_update:
            return None
        
        if datetime.now() - self._last_cache_update[key] > self._cache_timeout:
            # Cache expired
            del self._cache[key]
            del self._last_cache_update[key]
            return None
        
        return self._cache[key]
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        self._cache[key] = value
        self._last_cache_update[key] = datetime.now()
    
    def _clear_cache(self, key: str = None):
        """Clear cache for specific key or all keys"""
        if key:
            self._cache.pop(key, None)
            self._last_cache_update.pop(key, None)
        else:
            self._cache.clear()
            self._last_cache_update.clear()
    
    def get_setting(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        Get a setting value by key.
        
        Args:
            key: Setting key to retrieve
            default: Default value if setting not found
            use_cache: Whether to use cached value
            
        Returns:
            Setting value with proper type conversion
        """
        try:
            # Check cache first
            if use_cache:
                cached_value = self._get_from_cache(key)
                if cached_value is not None:
                    return cached_value
            
            # Import here to avoid circular imports
            from ..models import SystemSettings
            
            setting = SystemSettings.query.filter_by(setting_key=key).first()
            if setting:
                value = setting.get_typed_value()
                if use_cache:
                    self._set_cache(key, value)
                return value
            
            # If not found, check ML defaults
            if key in self.ML_SETTINGS_DEFAULTS:
                default_value = self.ML_SETTINGS_DEFAULTS[key]['value']
                logger.info(f"Setting '{key}' not found in DB, using default: {default_value}")
                return default_value
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting setting '{key}': {e}")
            return default
    
    def set_setting(self, key: str, value: Any, description: str = None, 
                   category: str = 'general', setting_type: str = None, 
                   is_public: bool = False, is_editable: bool = True, 
                   updated_by: int = None) -> bool:
        """
        Set a setting value, creating or updating as needed.
        
        Args:
            key: Setting key
            value: Setting value
            description: Human-readable description
            category: Setting category (ml, quiz, general, etc.)
            setting_type: Value type (boolean, integer, float, string, json)
            is_public: Whether non-admins can view this setting
            is_editable: Whether this setting can be changed via UI
            updated_by: User ID who updated the setting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..models import SystemSettings
            from .. import db
            
            # Auto-detect type if not provided
            if setting_type is None:
                if isinstance(value, bool):
                    setting_type = 'boolean'
                elif isinstance(value, int):
                    setting_type = 'integer'
                elif isinstance(value, float):
                    setting_type = 'float'
                elif isinstance(value, (dict, list)):
                    setting_type = 'json'
                else:
                    setting_type = 'string'
            
            # Validate value for ML settings
            if key.startswith('ml_') and not self._validate_ml_setting(key, value):
                logger.error(f"Invalid value for ML setting '{key}': {value}")
                return False
            
            # Use ML defaults for missing information
            if key in self.ML_SETTINGS_DEFAULTS and not description:
                ml_default = self.ML_SETTINGS_DEFAULTS[key]
                description = ml_default['description']
                category = ml_default['category']
                setting_type = ml_default['type']
            
            SystemSettings.set_setting(
                key=key,
                value=value,
                description=description,
                category=category,
                setting_type=setting_type,
                is_public=is_public,
                is_editable=is_editable,
                updated_by=updated_by
            )
            
            # Clear cache for this key
            self._clear_cache(key)
            
            logger.info(f"Setting '{key}' updated to: {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting '{key}': {e}")
            return False
    
    def get_category_settings(self, category: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get all settings for a specific category.
        
        Args:
            category: Category name (e.g., 'ml', 'quiz')
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary of setting_key -> value
        """
        try:
            # Import here to avoid circular imports
            from ..models import SystemSettings
            
            cache_key = f"category_{category}"
            
            if use_cache:
                cached_value = self._get_from_cache(cache_key)
                if cached_value is not None:
                    return cached_value
            
            settings = SystemSettings.query.filter_by(category=category).all()
            result = {}
            
            for setting in settings:
                result[setting.setting_key] = setting.get_typed_value()
            
            # For ML category, include defaults for missing settings
            if category == 'ml':
                for key, default_info in self.ML_SETTINGS_DEFAULTS.items():
                    if key not in result:
                        result[key] = default_info['value']
                        logger.info(f"ML setting '{key}' not found in DB, using default: {default_info['value']}")
            
            if use_cache:
                self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting category settings for '{category}': {e}")
            return {}
    
    def get_ml_settings(self, use_cache: bool = True) -> Dict[str, Any]:
        """Convenience method to get all ML settings"""
        return self.get_category_settings('ml', use_cache)
    
    def is_ml_enabled(self, use_cache: bool = True) -> bool:
        """Check if ML system is enabled (master switch)"""
        return self.get_setting('ml_system_enabled', default=True, use_cache=use_cache)
    
    def is_feature_enabled(self, feature_name: str, use_cache: bool = True) -> bool:
        """
        Check if a specific ML feature is enabled.
        
        Args:
            feature_name: Feature name (e.g., 'adaptive_learning', 'skill_tracking')
            use_cache: Whether to use cached value
            
        Returns:
            True if feature is enabled, False otherwise
        """
        # First check if ML system is enabled
        if not self.is_ml_enabled(use_cache):
            return False
        
        # Then check specific feature
        setting_key = f"ml_{feature_name}"
        return self.get_setting(setting_key, default=True, use_cache=use_cache)
    
    def _validate_ml_setting(self, key: str, value: Any) -> bool:
        """
        Validate ML setting values.
        
        Args:
            key: Setting key
            value: Setting value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if key == 'ml_learning_rate':
                return isinstance(value, (int, float)) and 0.01 <= value <= 0.1
            elif key == 'ml_adaptation_strength':
                return isinstance(value, (int, float)) and 0.1 <= value <= 1.0
            elif key == 'ml_fallback_mode':
                return value in ['random', 'difficulty', 'category', 'legacy']
            elif key == 'ml_update_frequency':
                return value in ['real-time', 'hourly', 'daily', 'weekly']
            elif key.startswith('ml_') and key.endswith(('_enabled', '_tracking', '_prediction', '_collection', '_retraining')):
                return isinstance(value, bool)
            else:
                return True  # Unknown setting, assume valid
                
        except Exception as e:
            logger.error(f"Error validating ML setting '{key}': {e}")
            return False
    
    def initialize_ml_settings(self, updated_by: int = None) -> bool:
        """
        Initialize ML settings with default values if they don't exist.
        
        Args:
            updated_by: User ID who initialized the settings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing ML settings with defaults...")
            
            for key, default_info in self.ML_SETTINGS_DEFAULTS.items():
                # Only create if doesn't exist
                existing = self.get_setting(key, default=None, use_cache=False)
                if existing is None:
                    self.set_setting(
                        key=key,
                        value=default_info['value'],
                        description=default_info['description'],
                        category=default_info['category'],
                        setting_type=default_info['type'],
                        is_public=False,
                        is_editable=True,
                        updated_by=updated_by
                    )
                    logger.info(f"Initialized ML setting: {key} = {default_info['value']}")
            
            # Clear cache to ensure fresh reads
            self._clear_cache()
            
            logger.info("ML settings initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing ML settings: {e}")
            return False
    
    def get_ml_status(self) -> Dict[str, Any]:
        """
        Get comprehensive ML system status.
        
        Returns:
            Dictionary with ML status information
        """
        try:
            ml_settings = self.get_ml_settings()
            
            return {
                'ml_enabled': ml_settings.get('ml_system_enabled', True),
                'features': {
                    'adaptive_learning': ml_settings.get('ml_adaptive_learning', True),
                    'skill_tracking': ml_settings.get('ml_skill_tracking', True),
                    'difficulty_prediction': ml_settings.get('ml_difficulty_prediction', True),
                    'data_collection': ml_settings.get('ml_data_collection', True),
                    'model_retraining': ml_settings.get('ml_model_retraining', True)
                },
                'configuration': {
                    'fallback_mode': ml_settings.get('ml_fallback_mode', 'random'),
                    'learning_rate': ml_settings.get('ml_learning_rate', 0.05),
                    'adaptation_strength': ml_settings.get('ml_adaptation_strength', 0.5)
                },
                'settings_source': 'database' if ml_settings else 'defaults'
            }
            
        except Exception as e:
            logger.error(f"Error getting ML status: {e}")
            return {
                'ml_enabled': True,  # Safe default
                'features': {},
                'configuration': {},
                'settings_source': 'error',
                'error': str(e)
            }
    
    def export_settings(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Export settings for backup or analysis.
        
        Args:
            category: Category to export (None for all)
            
        Returns:
            List of setting dictionaries
        """
        try:
            # Import here to avoid circular imports
            from ..models import SystemSettings
            
            query = SystemSettings.query
            if category:
                query = query.filter_by(category=category)
            
            settings = query.all()
            
            return [setting.to_dict() for setting in settings]
            
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return []
    
    def clear_cache(self):
        """Clear all cached settings"""
        self._clear_cache()
        logger.info("Settings cache cleared")


# Global settings service instance
settings_service = SettingsService()
