import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application Settings & Secrets.
    Validates environment variables on startup.
    """
    # --- App Info ---
    APP_NAME: str = "Enterprise AI Product Manager"
    ENV: str = "development"  # Options: 'development', 'production'
    
    # --- LLM Config ---
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4-turbo"  # Can be overridden by .env
    
    # --- Search Config ---
    TAVILY_API_KEY: str
    
    # --- Paths ---
    # We use absolute paths to avoid "File Not Found" errors
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH: str = os.path.join(BASE_DIR, "data", "app.db")
    PROMPTS_DIR: str = os.path.join(BASE_DIR, "src", "prompts", "templates")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Good practice: ignore extra keys in .env
    )

# Singleton Pattern: Create one instance and reuse it
@lru_cache
def get_settings():
    return Settings()

# Global export
settings = get_settings()