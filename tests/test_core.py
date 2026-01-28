"""Tests for core utilities (exceptions, retry logic)."""

import pytest
import time
from src.core.exceptions import (
    AIProductManagerError,
    AgentError,
    RAGError,
    CacheError,
)
from src.core.retry import retry_with_backoff


def test_base_exception():
    """Test base exception."""
    error = AIProductManagerError("Test error", details={"key": "value"})
    assert str(error) == "Test error | Details: {'key': 'value'}"
    assert error.details == {"key": "value"}


def test_agent_error():
    """Test agent-specific exception."""
    error = AgentError("market", "Analysis failed")
    assert "market" in str(error)
    assert "Analysis failed" in str(error)


def test_retry_success():
    """Test retry decorator with successful function."""
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_func()
    assert result == "success"
    assert call_count == 1


def test_retry_eventual_success():
    """Test retry decorator with function that eventually succeeds."""
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    start_time = time.time()
    result = flaky_func()
    duration = time.time() - start_time

    assert result == "success"
    assert call_count == 3
    assert duration >= 0.1  # At least one retry delay


def test_retry_max_retries_exceeded():
    """Test retry decorator when max retries is exceeded."""

    @retry_with_backoff(max_retries=2, initial_delay=0.1)
    def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_fails()
