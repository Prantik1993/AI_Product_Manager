"""Unified cache layer: MemoryCache (default) with optional Redis backend."""

import hashlib
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]: ...
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    @abstractmethod
    def delete(self, key: str) -> bool: ...
    @abstractmethod
    def exists(self, key: str) -> bool: ...


class MemoryCache(CacheBackend):
    """In-process cache with TTL support. Zero external dependencies."""

    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[datetime]]] = {}
        logger.info("MemoryCache initialized")

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if expires_at and datetime.now() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
        self._store[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return self.get(key) is not None


class RedisCache(CacheBackend):
    """Redis-backed cache with automatic memory fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._memory = MemoryCache()
        self._redis = None
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=False)
            self._redis.ping()
            logger.info(f"RedisCache connected: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to MemoryCache")

    def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return self._memory.get(key)
        try:
            raw = self._redis.get(key)
            return pickle.loads(raw) if raw else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self._redis:
            return self._memory.set(key, value, ttl)
        try:
            raw = pickle.dumps(value)
            if ttl:
                self._redis.setex(key, ttl, raw)
            else:
                self._redis.set(key, raw)
            self._memory.set(key, value, ttl)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return self._memory.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        if not self._redis:
            return self._memory.delete(key)
        try:
            result = self._redis.delete(key) > 0
            self._memory.delete(key)
            return result
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return self._memory.delete(key)

    def exists(self, key: str) -> bool:
        if not self._redis:
            return self._memory.exists(key)
        try:
            return self._redis.exists(key) > 0
        except Exception:
            return self._memory.exists(key)


_cache_instance: Optional[CacheBackend] = None


def get_cache(backend: str = "memory", **kwargs) -> CacheBackend:
    """Get or create the global cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        if backend == "redis":
            _cache_instance = RedisCache(**kwargs)
        else:
            _cache_instance = MemoryCache()
    return _cache_instance


def cached(ttl: Optional[int] = 300, key_prefix: str = ""):
    """Decorator to cache sync function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            parts = [key_prefix, func.__name__] + [str(a) for a in args]
            parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = hashlib.md5(":".join(filter(None, parts)).encode()).hexdigest()
            cache = get_cache()
            hit = cache.get(cache_key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
