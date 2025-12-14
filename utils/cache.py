"""Caching utilities for Code Agent"""
import hashlib
import json
import functools
from typing import Any, Callable, Optional
from pathlib import Path

try:
    import diskcache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    diskcache = None

from config import WORKSPACE_PATH


class CacheManager:
    """Manages caching for LLM responses and other data"""
    
    def __init__(self, cache_dir: Optional[Path] = None, size_limit: int = 2**30):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Cache directory path. Defaults to .cache in workspace
            size_limit: Maximum cache size in bytes (default: 1GB)
        """
        if not CACHE_AVAILABLE:
            raise ImportError(
                "diskcache is required for caching. Install with: pip install diskcache"
            )
        
        if cache_dir is None:
            cache_dir = Path(WORKSPACE_PATH).expanduser().resolve() / ".cache"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(cache_dir), size_limit=size_limit)
        self.enabled = True
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        try:
            return self.cache.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (default: 1 hour)
        """
        if not self.enabled:
            return
        try:
            self.cache.set(key, value, expire=expire)
        except Exception:
            pass  # Silently fail on cache errors
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.cache.delete(key)
        except Exception:
            pass
    
    def clear(self):
        """Clear all cache"""
        try:
            self.cache.clear()
        except Exception:
            pass
    
    def disable(self):
        """Disable caching"""
        self.enabled = False
    
    def enable(self):
        """Enable caching"""
        self.enabled = True


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        if CACHE_AVAILABLE:
            _cache_manager = CacheManager()
        else:
            # Return a dummy cache manager that does nothing
            class DummyCache:
                def get(self, key): return None
                def set(self, key, value, expire=None): pass
                def delete(self, key): pass
                def clear(self): pass
                def disable(self): pass
                def enable(self): pass
            _cache_manager = DummyCache()
    return _cache_manager


def _create_cache_key(prompt: str, model: str, context: Optional[dict] = None) -> str:
    """
    Create a cache key from prompt, model, and context.
    
    Args:
        prompt: The prompt text
        model: Model name
        context: Optional context dictionary
        
    Returns:
        Cache key string
    """
    # Create a hash from prompt, model, and context
    key_data = {
        "prompt": prompt,
        "model": model,
    }
    
    if context:
        # Sort context keys for consistent hashing
        key_data["context"] = json.dumps(context, sort_keys=True)
    
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


def cache_llm_response(ttl: int = 3600, enabled: bool = True):
    """
    Decorator to cache LLM responses.
    
    Works with both instance methods (self.model) and regular functions.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        enabled: Whether caching is enabled
        
    Usage:
        @cache_llm_response(ttl=7200)
        def call_llm(self, prompt, context=None):
            # For instance methods, model should be self.model
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if disabled
            cache = get_cache()
            if not enabled or not hasattr(cache, 'enabled') or not cache.enabled:
                return func(*args, **kwargs)
            
            # Extract prompt and context from arguments
            prompt = kwargs.get('prompt', '') or (args[1] if len(args) > 1 else (args[0] if args else ''))
            context = kwargs.get('context', {})
            
            # Try to get model from kwargs, args, or instance attribute
            model = kwargs.get('model', '')
            if not model:
                # Check if it's an instance method (has self)
                if args and hasattr(args[0], 'model'):
                    model = args[0].model
                elif len(args) > 2:
                    model = args[2]  # Third positional arg might be model
                else:
                    model = 'default'
            
            # Create cache key
            cache_key = _create_cache_key(prompt, model, context)
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire=ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_function_result(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    Generic decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from args/kwargs
        
    Usage:
        @cache_function_result(ttl=1800, key_func=lambda *a, **k: str(a[0]))
        def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            if not hasattr(cache, 'enabled') or not cache.enabled:
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash all arguments
                key_data = {
                    "args": str(args),
                    "kwargs": json.dumps(kwargs, sort_keys=True)
                }
                cache_key = hashlib.sha256(
                    json.dumps(key_data, sort_keys=True).encode()
                ).hexdigest()
            
            # Try cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Call and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire=ttl)
            
            return result
        
        return wrapper
    return decorator

