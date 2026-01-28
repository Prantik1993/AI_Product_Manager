#!/usr/bin/env python
"""Health check script for deployment validation.

Verifies that all critical components are working:
- Configuration loading
- Database connectivity
- RAG engine initialization
- API keys validation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


def check_config():
    """Verify configuration is loaded correctly."""
    try:
        assert settings.APP_NAME, "APP_NAME not set"
        assert settings.OPENAI_API_KEY, "OPENAI_API_KEY not set"
        assert settings.TAVILY_API_KEY, "TAVILY_API_KEY not set"
        logger.info("✓ Configuration check passed")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration check failed: {e}")
        return False


def check_database():
    """Verify database connectivity."""
    try:
        from src.storage.database import get_db_manager

        db = get_db_manager()
        stats = db.get_statistics()
        logger.info(f"✓ Database check passed: {stats['total_reports']} reports")
        return True
    except Exception as e:
        logger.error(f"✗ Database check failed: {e}")
        return False


def check_rag():
    """Verify RAG engine initialization."""
    try:
        from src.rag.engine import RAGQueryEngine

        rag = RAGQueryEngine()
        stats = rag.get_stats()
        logger.info(f"✓ RAG check passed: {stats.get('status', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"✗ RAG check failed: {e}")
        return False


def check_cache():
    """Verify cache backend."""
    try:
        from src.cache.cache import get_cache

        cache = get_cache(backend=settings.CACHE_BACKEND)
        cache.set("health_check", "ok", ttl=10)
        assert cache.get("health_check") == "ok"
        logger.info(f"✓ Cache check passed: {settings.CACHE_BACKEND}")
        return True
    except Exception as e:
        logger.error(f"✗ Cache check failed: {e}")
        return False


def main():
    """Run all health checks."""
    print("🏥 Running health checks...")
    print("-" * 50)

    checks = [
        ("Configuration", check_config),
        ("Database", check_database),
        ("RAG Engine", check_rag),
        ("Cache", check_cache),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        try:
            result = check_func()
            results.append(result)
            print("✓" if result else "✗")
        except Exception as e:
            print(f"✗ {e}")
            results.append(False)

    print("-" * 50)

    if all(results):
        print("✅ All health checks passed!")
        sys.exit(0)
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed}/{len(results)} health checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
