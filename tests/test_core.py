"""Tests for core utilities: exceptions and retry logic."""

import time
import pytest

from src.core.exceptions import AIProductManagerError, AgentError, RAGError, CacheError
from src.core.retry import retry_with_backoff


def test_base_exception_with_details():
    err = AIProductManagerError("Test error", details={"code": 42})
    assert "Test error" in str(err)
    assert err.details == {"code": 42}


def test_base_exception_no_details():
    err = AIProductManagerError("Simple error")
    assert str(err) == "Simple error"


def test_agent_error_includes_name():
    err = AgentError("market", "LLM timeout")
    assert "market" in str(err)
    assert "LLM timeout" in str(err)
    assert err.agent_name == "market"


def test_rag_error():
    err = RAGError("ChromaDB offline")
    assert "ChromaDB offline" in str(err)


def test_cache_error():
    err = CacheError("Redis connection refused")
    assert "Redis" in str(err)


def test_retry_succeeds_first_try():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def fn():
        nonlocal call_count
        call_count += 1
        return "ok"

    assert fn() == "ok"
    assert call_count == 1


def test_retry_eventual_success():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")
        return "success"

    result = flaky()
    assert result == "success"
    assert call_count == 3


def test_retry_exhausted_raises():
    @retry_with_backoff(max_retries=2, initial_delay=0.01)
    def always_fails():
        raise RuntimeError("permanent")

    with pytest.raises(RuntimeError, match="permanent"):
        always_fails()


def test_retry_only_catches_specified_exceptions():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
    def raises_type_error():
        nonlocal call_count
        call_count += 1
        raise TypeError("not retried")

    # TypeError is not in the caught exceptions, so it should propagate immediately
    with pytest.raises(TypeError):
        raises_type_error()

    assert call_count == 1  # No retries
