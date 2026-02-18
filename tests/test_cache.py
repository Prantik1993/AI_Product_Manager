"""Tests for cache backends."""

import time
import pytest

from src.cache.cache import MemoryCache, cached


def test_set_and_get():
    cache = MemoryCache()
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_get_missing_returns_none():
    cache = MemoryCache()
    assert cache.get("nonexistent") is None


def test_exists():
    cache = MemoryCache()
    cache.set("x", 1)
    assert cache.exists("x") is True
    assert cache.exists("y") is False


def test_delete():
    cache = MemoryCache()
    cache.set("k", "v")
    assert cache.delete("k") is True
    assert cache.get("k") is None
    assert cache.delete("k") is False  # already gone


def test_ttl_expiry():
    cache = MemoryCache()
    cache.set("k", "v", ttl=1)
    assert cache.get("k") == "v"
    time.sleep(1.1)
    assert cache.get("k") is None


def test_cached_decorator_caches_result():
    call_count = 0

    @cached(ttl=60, key_prefix="test")
    def compute(n: int) -> int:
        nonlocal call_count
        call_count += 1
        return n * 2

    assert compute(5) == 10
    assert call_count == 1

    # Second call with same arg — should hit cache
    assert compute(5) == 10
    assert call_count == 1

    # Different arg — should call function
    assert compute(7) == 14
    assert call_count == 2


def test_cache_stores_different_types():
    cache = MemoryCache()
    cache.set("int_val", 42)
    cache.set("list_val", [1, 2, 3])
    cache.set("dict_val", {"a": 1})

    assert cache.get("int_val") == 42
    assert cache.get("list_val") == [1, 2, 3]
    assert cache.get("dict_val") == {"a": 1}
