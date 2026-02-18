"""Prompt template loader with file-based caching."""

import os
import yaml
from functools import lru_cache

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=20)
def load_prompt(agent_name: str) -> str:
    """
    Load a prompt template from src/prompts/templates/<agent_name>.yaml.
    Results are cached after first load. In development, restart to pick up
    template changes (by design — avoids file I/O on every request).
    """
    file_path = os.path.join(settings.PROMPTS_DIR, f"{agent_name}.yaml")

    if not os.path.exists(file_path):
        logger.error(f"Prompt file missing: {file_path}")
        return "You are a helpful AI assistant. Analyze the given product idea."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict):
            return data.get("system_prompt", str(data))
        if isinstance(data, str):
            return data

        raise ValueError(f"Unexpected YAML format in {agent_name}.yaml")

    except Exception as e:
        logger.error(f"Failed to load prompt '{agent_name}': {e}")
        return "Error loading prompt template."
