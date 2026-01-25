import os
import yaml
from functools import lru_cache
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("prompt_manager")

@lru_cache(maxsize=20)
def load_prompt(agent_name: str) -> str:
    """
    Loads a prompt template from a YAML file in src/prompts/templates.
    Cached to improve performance.
    """
    # Construct file path: src/prompts/templates/<agent_name>.yaml
    file_path = os.path.join(settings.PROMPTS_DIR, f"{agent_name}.yaml")
    
    try:
        if not os.path.exists(file_path):
            error_msg = f"CRITICAL: Prompt file missing at {file_path}"
            logger.error(error_msg)
            # Fallback to prevent crash, but log heavily
            return "You are a helpful AI assistant."

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        # Handle both simple string YAML and structured dict YAML
        if isinstance(data, dict):
            # Look for 'system_prompt' key first
            return data.get("system_prompt", str(data))
        elif isinstance(data, str):
            return data
        else:
            raise ValueError(f"Invalid YAML format in {agent_name}.yaml")

    except Exception as e:
        logger.error(f"Failed to load prompt for {agent_name}: {e}")
        return "Error loading prompt."