# cache.py
"""Caching utilities for analysis results."""

from cachetools import TTLCache
from typing import Any, Optional
from functools import wraps
import hashlib
import json

from app.config import get_settings


class AnalysisCache:
    """Cache for analysis results."""
    
    _instance: Optional["AnalysisCache"] = None
    _cache: Optional[TTLCache] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._cache = TTLCache(
                maxsize=settings.cache_max_size,
                ttl=settings.cache_ttl
            )
        return cls._instance
    
    @classmethod
    def _make_key(cls, patient_id: str, analysis_type: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_data = {
            "patient_id": patient_id,
            "type": analysis_type,
            **kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    def get(cls, patient_id: str, analysis_type: str, **kwargs) -> Optional[Any]:
        """Get cached result."""
        if cls._cache is None:
            return None
        key = cls._make_key(patient_id, analysis_type, **kwargs)
        return cls._cache.get(key)
    
    @classmethod
    def set(cls, patient_id: str, analysis_type: str, value: Any, **kwargs) -> None:
        """Set cached result."""
        if cls._cache is None:
            settings = get_settings()
            cls._cache = TTLCache(
                maxsize=settings.cache_max_size,
                ttl=settings.cache_ttl
            )
        key = cls._make_key(patient_id, analysis_type, **kwargs)
        cls._cache[key] = value
    
    @classmethod
    def invalidate(cls, patient_id: str) -> None:
        """Invalidate all cache entries for a patient."""
        if cls._cache is None:
            return
        # Since we can't easily filter TTLCache, we'll clear keys that match
        keys_to_delete = [
            key for key in list(cls._cache.keys())
            if patient_id in str(key)
        ]
        for key in keys_to_delete:
            cls._cache.pop(key, None)
    
    @classmethod
    def clear(cls) -> None:
        """Clear entire cache."""
        if cls._cache is not None:
            cls._cache.clear()
    
    @classmethod
    def stats(cls) -> dict:
        """Get cache statistics."""
        if cls._cache is None:
            return {"size": 0, "maxsize": 0}
        return {
            "size": len(cls._cache),
            "maxsize": cls._cache.maxsize,
            "ttl": cls._cache.ttl
        }


def cached_analysis(analysis_type: str):
    """Decorator for caching analysis results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(patient_id: str, *args, **kwargs):
            # Check cache
            cached = AnalysisCache.get(patient_id, analysis_type)
            if cached is not None:
                return cached
            
            # Run analysis
            result = await func(patient_id, *args, **kwargs)
            
            # Cache result
            AnalysisCache.set(patient_id, analysis_type, result)
            
            return result
        return wrapper
    return decorator


# Convenience function
def get_cache() -> AnalysisCache:
    """Get cache instance."""
    return AnalysisCache()
