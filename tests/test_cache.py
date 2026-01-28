"""Tests for caching functionality."""

import pytest
import time
from src.cache.cache import MemoryCache, cached


def test_memory_cache_basic():
    """Test basic memory cache operations."""
    cache = MemoryCache()

    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test non-existent key
    assert cache.get("key2") is None

    # Test exists
    assert cache.exists("key1") is True
    assert cache.exists("key2") is False


def test_memory_cache_ttl():
    """Test memory cache with TTL."""
    cache = MemoryCache()

    # Set with short TTL
    cache.set("key1", "value1", ttl=1)
    assert cache.get("key1") == "value1"

    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_memory_cache_delete():
    """Test cache deletion."""
    cache = MemoryCache()

    cache.set("key1", "value1")
    assert cache.exists("key1") is True

    cache.delete("key1")
    assert cache.exists("key1") is False


def test_memory_cache_clear():
    """Test clearing all cache entries."""
    cache = MemoryCache()

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cached_decorator():
    """Test caching decorator."""
    call_count = 0

    @cached(ttl=60, key_prefix="test")
    def expensive_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call - should execute function
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count == 1

    # Second call with same argument - should return cached value
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_count == 1  # Function not called again

    # Call with different argument - should execute function
    result3 = expensive_function(10)
    assert result3 == 20
    assert call_count == 2
