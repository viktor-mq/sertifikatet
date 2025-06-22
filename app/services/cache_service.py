# app/services/cache_service.py - Redis caching service
import redis
import json
import pickle
from functools import wraps
from flask import current_app
from datetime import datetime, timedelta
import hashlib


class CacheService:
    """Redis-based caching service for performance optimization"""
    
    def __init__(self):
        self.redis_client = None
        self.connect()
    
    def connect(self):
        """Establish Redis connection"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            current_app.logger.info("Redis connection established")
        except Exception as e:
            current_app.logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def get(self, key, default=None):
        """Get value from cache"""
        if not self.redis_client:
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return pickle.loads(value.encode('latin1'))
                
        except Exception as e:
            current_app.logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key, value, ttl=3600):
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            # Try JSON serialization first, fallback to pickle
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value).decode('latin1')
            
            return self.redis_client.setex(key, ttl, serialized)
            
        except Exception as e:
            current_app.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            current_app.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return True
        except Exception as e:
            current_app.logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return False


# Global cache instance
cache = CacheService()


def cached(key_prefix, ttl=3600, key_func=None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Default key generation
                key_parts = [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
                key_hash = hashlib.md5("|".join(key_parts).encode()).hexdigest()
                cache_key = f"{key_prefix}:{key_hash}"
            
            # Try to get from cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
