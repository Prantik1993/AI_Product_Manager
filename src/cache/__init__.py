"""Cache module with Memory and Redis fallback support."""

from .cache import CacheBackend, MemoryCache, RedisCache, get_cache, cached

__all__ = ["CacheBackend", "MemoryCache", "RedisCache", "get_cache", "cached"]
