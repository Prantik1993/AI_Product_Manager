"""Enhanced structured logging with trace IDs and context.

This module provides production-ready logging with:
- JSON structured output for log aggregation systems
- Request/trace ID tracking for distributed tracing
- Contextual metadata for better debugging
- Performance tracking
"""

import logging
import json
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Optional
from datetime import datetime

from src.config.settings import settings

# Context variable for trace ID (thread-safe)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    """Enhanced JSON formatter with trace IDs and structured context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with enhanced metadata."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "app": settings.APP_NAME,
            "env": settings.ENV,
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Add trace ID if available
        trace_id = trace_id_var.get()
        if trace_id:
            log_obj["trace_id"] = trace_id

        # Add custom fields from extra parameter
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            log_obj["exception_type"] = record.exc_info[0].__name__

        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

        # Set log level based on environment
        if settings.ENV == "production":
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

    return logger


class log_context:
    """Context manager for adding trace IDs and structured context to logs.

    Example:
        with log_context(trace_id="abc123", user_id="user456"):
            logger.info("Processing request")
    """

    def __init__(self, trace_id: Optional[str] = None, **kwargs):
        """Initialize log context.

        Args:
            trace_id: Optional trace ID (auto-generated if not provided)
            **kwargs: Additional context fields to include in logs
        """
        self.trace_id = trace_id or str(uuid.uuid4())
        self.context = kwargs
        self.token = None

    def __enter__(self):
        """Enter context and set trace ID."""
        self.token = trace_id_var.set(self.trace_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset trace ID."""
        if self.token:
            trace_id_var.reset(self.token)


class PerformanceLogger:
    """Helper for logging performance metrics."""

    def __init__(self, logger: logging.Logger, operation: str):
        """Initialize performance logger.

        Args:
            logger: Logger instance
            operation: Name of the operation being timed
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        self.logger.debug(
            f"Starting {self.operation}",
            extra={"extra_fields": {"operation": self.operation}},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log execution time."""
        duration = time.time() - self.start_time
        if exc_type:
            self.logger.error(
                f"{self.operation} failed after {duration:.2f}s",
                extra={
                    "extra_fields": {
                        "operation": self.operation,
                        "duration_seconds": duration,
                        "error": str(exc_val),
                    }
                },
                exc_info=True,
            )
        else:
            self.logger.info(
                f"{self.operation} completed in {duration:.2f}s",
                extra={
                    "extra_fields": {
                        "operation": self.operation,
                        "duration_seconds": duration,
                    }
                },
            )


def log_with_context(
    logger: logging.Logger, level: int, message: str, **context
):
    """Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **context: Additional context fields
    """
    logger.log(level, message, extra={"extra_fields": context})
