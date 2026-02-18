"""Structured JSON logging with trace ID support."""

import logging
import json
import sys
import uuid
from contextvars import ContextVar
from typing import Optional
from datetime import datetime, timezone

from src.config.settings import settings

trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        obj: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "app": settings.APP_NAME,
            "env": settings.ENV,
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        trace_id = trace_id_var.get()
        if trace_id:
            obj["trace_id"] = trace_id

        if hasattr(record, "extra_fields"):
            obj.update(record.extra_fields)

        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
            obj["exception_type"] = record.exc_info[0].__name__

        return json.dumps(obj)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that emits JSON to stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        logger.propagate = False
    return logger


class log_context:
    """Context manager to attach a trace ID to all logs within scope."""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self._token = None

    def __enter__(self):
        self._token = trace_id_var.set(self.trace_id)
        return self

    def __exit__(self, *_):
        if self._token:
            trace_id_var.reset(self._token)
