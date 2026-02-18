"""Custom exceptions hierarchy for AI Product Manager."""


class AIProductManagerError(Exception):
    """Base exception for all AI Product Manager errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AgentError(AIProductManagerError):
    """Raised when an agent fails to complete its analysis."""

    def __init__(self, agent_name: str, message: str, details: dict | None = None):
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}", details)


class RAGError(AIProductManagerError):
    """Raised when RAG retrieval or ingestion fails."""
    pass


class CacheError(AIProductManagerError):
    """Raised when cache operations fail."""
    pass


class DatabaseError(AIProductManagerError):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AIProductManagerError):
    """Raised when configuration is invalid or missing."""
    pass


class ExternalServiceError(AIProductManagerError):
    """Raised when external services (OpenAI, Tavily, etc.) fail."""

    def __init__(self, service_name: str, message: str, details: dict | None = None):
        self.service_name = service_name
        super().__init__(f"[{service_name}] {message}", details)
