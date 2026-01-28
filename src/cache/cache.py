"""Unified caching layer with Memory and Redis fallback.

Provides a simple caching interface that works with:
- In-memory cache (default, no dependencies)
- Redis cache (production, requires redis-py)

The cache automatically falls back to memory if Redis is unavailable.
"""

import json
import hashlib
import pickle
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

from src.core.exceptions import CacheError
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache with optional TTL in seconds."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass


class MemoryCache(CacheBackend):
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        """Initialize memory cache."""
        self._cache: dict[str, tuple[Any, Optional[datetime]]] = {}
        logger.info("Initialized MemoryCache backend")

    def get(self, key: str) -> Optional[Any]:
        """Get a value from memory cache."""
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]

        # Check if expired
        if expires_at and datetime.now() > expires_at:
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for key: {key}")
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in memory cache."""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = (value, expires_at)
        logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")
        return True

    def delete(self, key: str) -> bool:
        """Delete a key from memory cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
            return True
        return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")
        return True

    def exists(self, key: str) -> bool:
        """Check if a key exists in memory cache."""
        return key in self._cache and (
            self._cache[key][1] is None or datetime.now() <= self._cache[key][1]
        )


class RedisCache(CacheBackend):
    """Redis cache backend with automatic fallback to memory."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", fallback: bool = True):
        """Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            fallback: Whether to fall back to memory cache if Redis fails
        """
        self._fallback = fallback
        self._memory_cache = MemoryCache() if fallback else None
        self._redis_client = None

        try:
            import redis

            self._redis_client = redis.from_url(redis_url, decode_responses=False)
            self._redis_client.ping()
            logger.info(f"Initialized RedisCache backend: {redis_url}")
        except ImportError:
            logger.warning(
                "redis-py not installed. Falling back to MemoryCache. "
                "Install with: pip install redis"
            )
            if not fallback:
                raise CacheError("Redis library not installed and fallback disabled")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis: {e}. Falling back to MemoryCache"
            )
            if not fallback:
                raise CacheError(f"Failed to connect to Redis: {e}")

    def _use_fallback(self) -> bool:
        """Check if we should use fallback cache."""
        return self._redis_client is None and self._fallback

    def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis cache."""
        if self._use_fallback():
            return self._memory_cache.get(key)

        try:
            value = self._redis_client.get(key)
            if value is None:
                return None

            logger.debug(f"Cache hit for key: {key}")
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            if self._fallback:
                return self._memory_cache.get(key)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis cache."""
        if self._use_fallback():
            return self._memory_cache.set(key, value, ttl)

        try:
            serialized = pickle.dumps(value)
            if ttl:
                self._redis_client.setex(key, ttl, serialized)
            else:
                self._redis_client.set(key, serialized)

            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")

            # Also set in memory cache for faster access
            if self._fallback:
                self._memory_cache.set(key, value, ttl)

            return True
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            if self._fallback:
                return self._memory_cache.set(key, value, ttl)
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis cache."""
        if self._use_fallback():
            return self._memory_cache.delete(key)

        try:
            result = self._redis_client.delete(key) > 0
            logger.debug(f"Cache deleted for key: {key}")

            if self._fallback:
                self._memory_cache.delete(key)

            return result
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
            if self._fallback:
                return self._memory_cache.delete(key)
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        if self._use_fallback():
            return self._memory_cache.clear()

        try:
            self._redis_client.flushdb()
            logger.info("Redis cache cleared")

            if self._fallback:
                self._memory_cache.clear()

            return True
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            if self._fallback:
                return self._memory_cache.clear()
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        if self._use_fallback():
            return self._memory_cache.exists(key)

        try:
            return self._redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists check failed for key {key}: {e}")
            if self._fallback:
                return self._memory_cache.exists(key)
            return False


# Global cache instance
_cache_instance: Optional[CacheBackend] = None


def get_cache(backend: str = "memory", **kwargs) -> CacheBackend:
    """Get or create a cache instance.

    Args:
        backend: Cache backend type ("memory" or "redis")
        **kwargs: Additional arguments for the cache backend

    Returns:
        Cache backend instance
    """
    global _cache_instance

    if _cache_instance is None:
        if backend == "redis":
            _cache_instance = RedisCache(**kwargs)
        else:
            _cache_instance = MemoryCache()

    return _cache_instance


def cached(ttl: Optional[int] = 300, key_prefix: str = ""):
    """Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds (default: 300s)
        key_prefix: Optional prefix for cache keys

    Example:
        @cached(ttl=600, key_prefix="market")
        def analyze_market(product_idea: str):
            return expensive_analysis(product_idea)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_str = ":".join(filter(None, key_parts))
            cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Returning cached result for {func.__name__}")
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
