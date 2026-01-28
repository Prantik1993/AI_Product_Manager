"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["ENV"] = "development"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["TAVILY_API_KEY"] = "test-tavily-key"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["CACHE_BACKEND"] = "memory"


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from src.config.settings import Settings

    return Settings(
        OPENAI_API_KEY="test-key",
        TAVILY_API_KEY="test-key",
        ENV="development",
        DATABASE_URL="sqlite:///:memory:",
    )


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    mock = Mock()
    mock.invoke.return_value = Mock(content="Mocked LLM response")
    return mock


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock = MagicMock()
    mock.similarity_search.return_value = []
    mock.similarity_search_with_score.return_value = []
    return mock


@pytest.fixture
def sample_product_idea():
    """Sample product idea for testing."""
    return "A mobile app that helps users track their daily water intake"


@pytest.fixture
def sample_agent_report():
    """Sample agent report for testing."""
    return {
        "verdict": "GO",
        "confidence": 0.85,
        "rationale": "Strong market demand and feasibility",
        "key_findings": ["Market size: $10B", "Low technical complexity"],
    }


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    from unittest.mock import MagicMock

    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session
