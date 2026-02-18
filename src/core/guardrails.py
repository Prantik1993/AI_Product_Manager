"""Input validation and guardrails for AI Product Manager."""

import re
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from src.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_input: Optional[str] = None


class InputGuardrails:
    """Guardrails for validating and sanitizing user input."""

    MIN_LENGTH = 10
    MAX_LENGTH = 5000
    MAX_WORDS = 1000

    # XSS / injection patterns
    FORBIDDEN_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
    ]

    # Prompt injection keywords
    SUSPICIOUS_KEYWORDS = [
        'ignore previous instructions',
        'ignore above',
        'disregard',
        'new instructions',
        'forget everything',
        'admin mode',
        'developer mode',
        'system prompt',
    ]

    @classmethod
    def validate_input(cls, user_input: str) -> ValidationResult:
        if not user_input or not user_input.strip():
            return ValidationResult(is_valid=False, error_message="Input cannot be empty")

        if len(user_input) < cls.MIN_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Input too short (minimum {cls.MIN_LENGTH} characters)"
            )

        if len(user_input) > cls.MAX_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Input too long (maximum {cls.MAX_LENGTH} characters)"
            )

        if len(user_input.split()) > cls.MAX_WORDS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Too many words (maximum {cls.MAX_WORDS})"
            )

        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Blocked malicious pattern detected")
                return ValidationResult(is_valid=False, error_message="Input contains forbidden patterns")

        lower_input = user_input.lower()
        for keyword in cls.SUSPICIOUS_KEYWORDS:
            if keyword in lower_input:
                logger.warning(f"Prompt injection attempt detected: '{keyword}'")
                return ValidationResult(is_valid=False, error_message="Input contains suspicious content")

        sanitized = cls._sanitize(user_input)
        return ValidationResult(is_valid=True, sanitized_input=sanitized)

    @staticmethod
    def _sanitize(text: str) -> str:
        text = text.replace('\x00', '')
        text = ' '.join(text.split())
        return text.strip()


class RateLimiter:
    """Simple in-memory per-user rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, identifier: str) -> Tuple[bool, str]:
        now = time.time()
        if identifier not in self._requests:
            self._requests[identifier] = []

        # Evict expired timestamps
        self._requests[identifier] = [
            t for t in self._requests[identifier]
            if now - t < self.window_seconds
        ]

        if len(self._requests[identifier]) >= self.max_requests:
            return False, f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s)"

        self._requests[identifier].append(now)
        return True, "OK"


# Module-level singletons
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def validate_product_idea(user_input: str, user_id: str = "default") -> ValidationResult:
    """Main validation entry point combining rate limiting + input validation."""
    allowed, message = _rate_limiter.check(user_id)
    if not allowed:
        return ValidationResult(is_valid=False, error_message=message)
    return InputGuardrails.validate_input(user_input)


def validate_system_health() -> Tuple[bool, str]:
    """Quick system health check at startup."""
    issues = []

    try:
        from src.storage.database import get_db_manager
        get_db_manager().get_statistics()
    except Exception as e:
        issues.append(f"Database: {e}")

    try:
        from src.rag.engine import RAGQueryEngine
        stats = RAGQueryEngine().get_stats()
        if stats.get("status") not in ("online",):
            issues.append(f"RAG: {stats.get('status', 'unknown')}")
    except Exception as e:
        issues.append(f"RAG: {e}")

    if issues:
        return False, "Health check failed: " + "; ".join(issues)
    return True, "All systems operational"
