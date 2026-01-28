import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Production-ready application settings with validation.
    Validates environment variables on startup and provides sensible defaults.
    """
    # --- App Info ---
    APP_NAME: str = "Enterprise AI Product Manager"
    ENV: str = Field(default="development", description="Environment: development, staging, or production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # --- LLM Config ---
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key (required)")
    MODEL_NAME: str = Field(default="gpt-4-turbo", description="OpenAI model to use")
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    MAX_TOKENS: int = Field(default=2000, ge=100, le=8000, description="Max tokens for LLM responses")

    # --- Search Config ---
    TAVILY_API_KEY: str = Field(..., description="Tavily API key for web search (required)")
    MAX_SEARCH_RESULTS: int = Field(default=5, ge=1, le=20, description="Max web search results")

    # --- Cache Config ---
    CACHE_BACKEND: str = Field(default="memory", description="Cache backend: memory or redis")
    CACHE_TTL: int = Field(default=300, ge=0, description="Default cache TTL in seconds")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    ENABLE_CACHE: bool = Field(default=True, description="Enable caching")

    # --- Database Config ---
    DATABASE_URL: Optional[str] = Field(default=None, description="Database URL (SQLite or Postgres)")
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=50, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100, description="Max database overflow connections")

    # --- RAG Config ---
    RAG_TOP_K: int = Field(default=3, ge=1, le=10, description="Number of RAG documents to retrieve")
    RAG_SCORE_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0, description="Min similarity score for RAG")
    ENABLE_RERANKING: bool = Field(default=False, description="Enable RAG reranking")

    # --- Retry Config ---
    MAX_RETRIES: int = Field(default=3, ge=0, le=10, description="Max retries for failed operations")
    RETRY_INITIAL_DELAY: float = Field(default=1.0, ge=0.1, le=10.0, description="Initial retry delay in seconds")
    RETRY_BACKOFF_FACTOR: float = Field(default=2.0, ge=1.0, le=5.0, description="Retry backoff multiplier")

    # --- Monitoring Config ---
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")
    STRUCTURED_LOGGING: bool = Field(default=True, description="Enable JSON structured logging")

    # --- Paths ---
    BASE_DIR: str = Field(
        default_factory=lambda: os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        description="Base project directory"
    )

    @property
    def DB_PATH(self) -> str:
        """SQLite database path."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return os.path.join(self.BASE_DIR, "data", "app.db")

    @property
    def PROMPTS_DIR(self) -> str:
        """Prompts templates directory."""
        return os.path.join(self.BASE_DIR, "src", "prompts", "templates")

    @property
    def INTERNAL_DOCS_DIR(self) -> str:
        """Internal documents directory for RAG."""
        return os.path.join(self.BASE_DIR, "data", "internal_docs")

    @property
    def VECTOR_DB_DIR(self) -> str:
        """Vector database directory."""
        return os.path.join(self.BASE_DIR, "data", "chroma_db")

    @property
    def CACHE_DIR(self) -> str:
        """File-based cache directory."""
        return os.path.join(self.BASE_DIR, "data", "cache")

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}, got: {v}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got: {v}")
        return v_upper

    @field_validator("CACHE_BACKEND")
    @classmethod
    def validate_cache_backend(cls, v: str) -> str:
        """Validate cache backend."""
        allowed = {"memory", "redis"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"CACHE_BACKEND must be one of {allowed}, got: {v}")
        return v_lower

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENV == "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

# Singleton Pattern: Create one instance and reuse it
@lru_cache
def get_settings():
    return Settings()

# Global export
settings = get_settings()