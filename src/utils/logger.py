import logging
import json
import sys
from src.config.settings import settings

class JsonFormatter(logging.Formatter):
    """
    Formats log records as a JSON string.
    Essential for centralized logging systems (Datadog, Splunk, CloudWatch).
    """
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "app": settings.APP_NAME,
            "module": record.name,
            "message": record.getMessage(),
            "env": settings.ENV
        }
        # Capture stack traces if an error occurs
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def get_logger(name: str) -> logging.Logger:
    """
    Factory function to get a configured logger.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if get_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        
        # Set Log Level based on Environment
        # In PROD, we usually only want INFO or ERROR to save costs
        if settings.ENV == "production":
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
            
    return logger