"""Input validation and guardrails for AI Product Manager.

Provides comprehensive validation and safety checks including:
- Input sanitization
- Length limits
- Content filtering
- Rate limiting
- Safety checks for malicious input
"""

import re
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
    
    # Configuration
    MIN_LENGTH = 10
    MAX_LENGTH = 5000
    MAX_WORDS = 1000
    
    # Forbidden patterns (basic security)
    FORBIDDEN_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS attempts
        r'javascript:',  # JavaScript injection
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # Eval attempts
        r'exec\s*\(',  # Exec attempts
    ]
    
    # Suspicious keywords that might indicate prompt injection
    SUSPICIOUS_KEYWORDS = [
        'ignore previous instructions',
        'ignore above',
        'disregard',
        'system prompt',
        'new instructions',
        'forget everything',
        'admin mode',
        'developer mode',
    ]
    
    @classmethod
    def validate_input(cls, user_input: str) -> ValidationResult:
        """
        Comprehensive input validation.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            ValidationResult with validation status and sanitized input
        """
        if not user_input:
            return ValidationResult(
                is_valid=False,
                error_message="Input cannot be empty"
            )
        
        # 1. Length validation
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
        
        # 2. Word count validation
        word_count = len(user_input.split())
        if word_count > cls.MAX_WORDS:
            return ValidationResult(
                is_valid=False,
                error_message=f"Too many words (maximum {cls.MAX_WORDS} words)"
            )
        
        # 3. Check for malicious patterns
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(
                    f"Blocked malicious pattern: {pattern}",
                    extra={"extra_fields": {"input": user_input[:100]}}
                )
                return ValidationResult(
                    is_valid=False,
                    error_message="Input contains forbidden patterns"
                )
        
        # 4. Check for prompt injection attempts
        lower_input = user_input.lower()
        for keyword in cls.SUSPICIOUS_KEYWORDS:
            if keyword in lower_input:
                logger.warning(
                    f"Suspicious keyword detected: {keyword}",
                    extra={"extra_fields": {"input": user_input[:100]}}
                )
                return ValidationResult(
                    is_valid=False,
                    error_message="Input contains suspicious content"
                )
        
        # 5. Sanitize input
        sanitized = cls._sanitize_input(user_input)
        
        logger.info(
            "Input validation passed",
            extra={
                "extra_fields": {
                    "length": len(user_input),
                    "word_count": word_count
                }
            }
        )
        
        return ValidationResult(
            is_valid=True,
            sanitized_input=sanitized
        )
    
    @staticmethod
    def _sanitize_input(text: str) -> str:
        """
        Sanitize input by removing dangerous characters.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove control characters except newlines
        text = ''.join(char for char in text if char == '\n' or not char.isspace() or char == ' ')
        
        return text.strip()
    
    @staticmethod
    def validate_api_keys() -> Tuple[bool, str]:
        """
        Validate that required API keys are present and properly formatted.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        from src.config.settings import settings
        
        errors = []
        
        # Check OpenAI key
        if not settings.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is missing")
        elif not settings.OPENAI_API_KEY.startswith("sk-"):
            errors.append("OPENAI_API_KEY has invalid format")
        
        # Check Tavily key
        if not settings.TAVILY_API_KEY:
            errors.append("TAVILY_API_KEY is missing")
        elif not settings.TAVILY_API_KEY.startswith("tvly-"):
            errors.append("TAVILY_API_KEY has invalid format")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "All API keys valid"


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, str]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            
        Returns:
            Tuple of (is_allowed, message)
        """
        import time
        
        now = time.time()
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Clean old requests outside window
        self._requests[identifier] = [
            timestamp for timestamp in self._requests[identifier]
            if now - timestamp < self.window_seconds
        ]
        
        # Check limit
        if len(self._requests[identifier]) >= self.max_requests:
            return False, f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s)"
        
        # Add current request
        self._requests[identifier].append(now)
        
        return True, "OK"


# Global rate limiter instance
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def validate_product_idea(user_input: str, user_id: str = "default") -> ValidationResult:
    """
    Main validation function that combines all guardrails.
    
    Args:
        user_input: User's product idea
        user_id: User identifier for rate limiting
        
    Returns:
        ValidationResult
    """
    # 1. Rate limiting
    is_allowed, message = _rate_limiter.check_rate_limit(user_id)
    if not is_allowed:
        return ValidationResult(
            is_valid=False,
            error_message=message
        )
    
    # 2. Input validation
    result = InputGuardrails.validate_input(user_input)
    
    return result


def validate_system_health() -> Tuple[bool, str]:
    """
    Validate system health before processing requests.
    
    Returns:
        Tuple of (is_healthy, status_message)
    """
    issues = []
    
    # Check API keys
    keys_valid, key_message = InputGuardrails.validate_api_keys()
    if not keys_valid:
        issues.append(f"API Keys: {key_message}")
    
    # Check database
    try:
        from src.storage.database import get_db_manager
        db = get_db_manager()
        db.get_statistics()
    except Exception as e:
        issues.append(f"Database: {str(e)}")
    
    # Check RAG
    try:
        from src.rag.engine import RAGQueryEngine
        rag = RAGQueryEngine()
        stats = rag.get_stats()
        if stats.get("status") != "online":
            issues.append(f"RAG: {stats.get('status', 'unknown')}")
    except Exception as e:
        issues.append(f"RAG: {str(e)}")
    
    if issues:
        return False, "System health check failed: " + "; ".join(issues)
    
    return True, "All systems operational"