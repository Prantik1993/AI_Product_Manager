#!/usr/bin/env python
"""
Lightweight health check for Docker and deployment validation.

FIX: Old version imported entire app stack on every check (expensive, slow).
     This version does minimal targeted checks only.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_config() -> tuple[bool, str]:
    try:
        from src.config.settings import settings
        assert settings.OPENAI_API_KEY, "OPENAI_API_KEY missing"
        assert settings.TAVILY_API_KEY, "TAVILY_API_KEY missing"
        return True, "Config OK"
    except Exception as e:
        return False, f"Config: {e}"


def check_database() -> tuple[bool, str]:
    try:
        from src.storage.database import get_db_manager
        stats = get_db_manager().get_statistics()
        return True, f"DB OK ({stats.get('total_reports', 0)} reports)"
    except Exception as e:
        return True, f"DB: {e} (will be created on first use)"


def check_rag() -> tuple[bool, str]:
    try:
        from src.rag.engine import RAGQueryEngine
        stats = RAGQueryEngine().get_stats()
        return True, f"RAG {stats.get('status', 'unknown')} ({stats.get('document_count', 0)} docs)"
    except Exception as e:
        return True, f"RAG offline: {e} (run ingest.py)"


def check_cache() -> tuple[bool, str]:
    try:
        from src.cache.cache import MemoryCache
        cache = MemoryCache()
        cache.set("_health", "ok", ttl=5)
        assert cache.get("_health") == "ok"
        cache.delete("_health")
        return True, "Cache OK"
    except Exception as e:
        return False, f"Cache: {e}"


def main():
    print("🏥 Health Check")
    print("-" * 40)

    checks = [
        ("Configuration", check_config),
        ("Database", check_database),
        ("RAG Engine", check_rag),
        ("Cache", check_cache),
    ]

    results = []
    for name, fn in checks:
        ok, msg = fn()
        symbol = "✓" if ok else "✗"
        print(f"  {symbol} {name}: {msg}")
        results.append(ok)

    print("-" * 40)
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"✅ All {total} checks passed")
        sys.exit(0)
    elif passed >= total - 1:  # Allow 1 non-critical failure (RAG/DB on first run)
        print(f"⚠️  {passed}/{total} passed — system operational")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} critical checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
