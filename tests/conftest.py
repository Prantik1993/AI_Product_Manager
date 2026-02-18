"""
Pytest fixtures and test configuration.

FIX: env vars set BEFORE importing settings, and lru_cache cleared so
     Settings() re-reads them. Previously settings was cached with wrong/empty keys.
FIX: Fixture yields and cleans up env vars after the test session.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Set test env vars BEFORE any src imports — critical for lru_cache
# FIX: sk-test satisfies the updated validator (starts with "sk-")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-pytest")
os.environ.setdefault("TAVILY_API_KEY", "tvly-test-key-for-pytest")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CACHE_BACKEND", "memory")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # suppress noise in test output

# NOW it's safe to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Ensure settings singleton uses test values.
    FIX: Clear lru_cache so Settings() re-initializes with test env vars.
    FIX: yield + cleanup restores original state after session.
    """
    from src.config.settings import get_settings
    get_settings.cache_clear()

    yield

    # Cleanup after all tests
    get_settings.cache_clear()


@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Mocked LLM response")
    mock.ainvoke.return_value = MagicMock(content="Mocked async LLM response")
    return mock


@pytest.fixture
def mock_vector_store():
    mock = MagicMock()
    mock.similarity_search.return_value = []
    mock.similarity_search_with_score.return_value = []
    mock._collection.count.return_value = 5
    return mock


@pytest.fixture
def sample_product_idea():
    return "A mobile app that uses AI to help users track their daily water intake and hydration goals"


@pytest.fixture
def sample_agent_state(sample_product_idea):
    """Full agent state with all analysis fields populated."""
    import json
    return {
        "user_input": sample_product_idea,
        "market_analysis": json.dumps({
            "summary": "Strong market demand",
            "key_findings": ["$2B market", "Growing 15% YoY"],
            "competitors": ["WaterMinder", "Hydro Coach"],
            "market_size_estimate": "$2B TAM",
            "score": 8,
        }),
        "tech_analysis": json.dumps({
            "summary": "Low complexity, standard mobile stack",
            "required_stack": ["React Native", "Firebase", "OpenAI API"],
            "challenges": ["Cross-platform sync"],
            "feasibility": "HIGH",
            "score": 9,
        }),
        "risk_analysis": json.dumps({
            "summary": "Low risk profile",
            "legal_concerns": ["GDPR compliance required"],
            "ethical_risks": ["Data accuracy claims"],
            "mitigation_strategies": ["GDPR audit before launch"],
            "score": 3,
        }),
        "user_feedback_analysis": json.dumps({
            "summary": "Strong user interest",
            "pain_points": ["Forgetting to drink water"],
            "positive_signals": ["Users want AI recommendations"],
            "sentiment": "POSITIVE",
            "score": 8,
        }),
        "final_verdict": None,
    }
