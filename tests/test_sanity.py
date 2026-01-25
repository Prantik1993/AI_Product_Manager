import pytest
import os
from src.config.settings import settings

# 1. Test Environment Setup
def test_environment_variables():
    """Fail if API keys are missing."""
    assert settings.OPENAI_API_KEY is not None, "❌ OpenAI Key is missing!"
    assert settings.OPENAI_API_KEY.startswith("sk-"), "❌ Invalid OpenAI Key format."
    assert settings.ENV in ["development", "production"], "❌ Invalid ENV setting."

# 2. Test File Structure
def test_critical_files_exist():
    """Fail if the brain (data) is missing."""
    # We check if the strategy file exists because without it, RAG fails.
    strategy_path = os.path.join(settings.BASE_DIR, "data", "internal_docs", "strategy.txt")
    pdf_path = os.path.join(settings.BASE_DIR, "data", "internal_docs")
    
    # Check if we have at least one file in internal_docs
    has_files = len(os.listdir(pdf_path)) > 0
    assert has_files, "❌ No strategy documents found in data/internal_docs!"

# 3. Test Agent Loading (Integration Test)
def test_agents_load_correctly():
    """Fail if an Agent crashes on startup."""
    from src.agents.market import MarketAgent
    try:
        agent = MarketAgent()
        assert agent.name == "market"
    except Exception as e:
        pytest.fail(f"❌ MarketAgent failed to initialize: {e}")