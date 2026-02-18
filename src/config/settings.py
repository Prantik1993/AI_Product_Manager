import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Production-ready application settings with Pydantic v2 validation.
    All values loaded from environment / .env file.
    """

    # --- App ---
    APP_NAME: str = "Enterprise AI Product Manager"
    ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # --- LLM Config ---
    # FIX: Updated from deprecated gpt-4-turbo to gpt-4o
    # FIX: Added separate cheaper model for parallel analysis agents
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key (required)")
    MODEL_NAME: str = Field(default="gpt-4o", description="Model for DecisionAgent")
    ANALYSIS_MODEL: str = Field(default="gpt-4o-mini", description="Model for parallel analysis agents")
    TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    MAX_TOKENS: int = Field(default=2000, ge=100, le=8000)

    # --- Search ---
    TAVILY_API_KEY: str = Field(..., description="Tavily API key (required)")
    MAX_SEARCH_RESULTS: int = Field(default=5, ge=1, le=20)

    # --- Cache ---
    CACHE_BACKEND: str = Field(default="memory")
    CACHE_TTL: int = Field(default=300, ge=0)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    ENABLE_CACHE: bool = Field(default=True)

    # --- Database ---
    DATABASE_URL: Optional[str] = Field(default=None)
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100)

    # --- RAG ---
    RAG_TOP_K: int = Field(default=3, ge=1, le=10)
    RAG_SCORE_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)

    # --- Retry ---
    MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    RETRY_INITIAL_DELAY: float = Field(default=1.0, ge=0.1)
    RETRY_BACKOFF_FACTOR: float = Field(default=2.0, ge=1.0)

    # --- Monitoring ---
    LOG_LEVEL: str = Field(default="INFO")

    # --- Computed Paths (not from env) ---
    @property
    def BASE_DIR(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @property
    def DB_PATH(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return os.path.join(self.BASE_DIR, "data", "app.db")

    @property
    def PROMPTS_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, "src", "prompts", "templates")

    @property
    def INTERNAL_DOCS_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, "data", "internal_docs")

    @property
    def VECTOR_DB_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, "data", "chroma_db")

    # --- Validators ---
    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper

    @field_validator("CACHE_BACKEND")
    @classmethod
    def validate_cache_backend(cls, v: str) -> str:
        allowed = {"memory", "redis"}
        if v.lower() not in allowed:
            raise ValueError(f"CACHE_BACKEND must be one of {allowed}")
        return v.lower()

    # FIX: Updated OpenAI key validation to support both old sk- and new sk-proj- format
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not (v.startswith("sk-") or v.startswith("sk-proj-")):
            raise ValueError("OPENAI_API_KEY must start with 'sk-' or 'sk-proj-'")
        return v

    def is_production(self) -> bool:
        return self.ENV == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# FIX: lru_cache is correct for production but tests must call get_settings.cache_clear()
# See tests/conftest.py for the correct pattern
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
