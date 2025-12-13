"""
backend/utils/logging.py

Centralized logging utilities for the application: consistent logger creation, optional JSON formatting, and FastAPI-friendly configuration.
"""

from __future__ import annotations
import logging
import json
from typing import Optional

from backend.config import settings


# Configuration defaults from settings
LOG_LEVEL = getattr(settings, "LOG_LEVEL", "INFO").upper()
LOG_AS_JSON = getattr(settings, "LOG_AS_JSON", False)


class JsonFormatter(logging.Formatter):
    """
    Format logs as compact JSON objects.
    
    Produces structured logs suitable for aggregation tools like ELK, Datadog, or CloudWatch.
    Falls back to plain text if serialization fails.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as a JSON string.
        
        Args:
            record: LogRecord instance to format
        
        Returns:
            JSON-formatted log string
        """
        # Build log entry dict
        log_entry = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Safely serialize to JSON
        try:
            return json.dumps(log_entry, default=str)
        except (TypeError, ValueError):
            # Fallback if serialization fails
            return str(record.msg)


def _get_formatter() -> logging.Formatter:
    """
    Get the appropriate formatter based on configuration.
    
    Returns:
        JsonFormatter if LOG_AS_JSON is True, otherwise standard text formatter
    """
    if LOG_AS_JSON:
        return JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        # Simple text formatter for local development
        return logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger with our standard settings.
    
    Creates loggers with consistent formatting and level settings.
    Safe to call multiple times for the same name - won't create duplicate handlers.
    
    Args:
        name: Logger name (typically __name__ from calling module).
              If None, returns logger named "app"
    
    Returns:
        Configured logging.Logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    logger_name = name or "app"
    logger = logging.getLogger(logger_name)
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Set logger level from config
    logger.setLevel(LOG_LEVEL)
    
    # Create stream handler for stdout
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    
    # Apply formatter
    formatter = _get_formatter()
    handler.setFormatter(formatter)
    
    # Attach handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def configure_logging() -> None:
    """
    Configure root logger for the entire application.
    
    Call this once during application startup (e.g., in main.py) to set up
    consistent logging across all modules. Removes any existing handlers and
    configures a single handler with our standard formatting.
    
    Usage in main.py:
        from backend.utils.logging import configure_logging
        
        configure_logging()
        app = FastAPI()
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove all existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(LOG_LEVEL)
    
    # Create and configure handler
    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    
    # Apply formatter
    formatter = _get_formatter()
    handler.setFormatter(formatter)
    
    # Attach handler to root logger
    root_logger.addHandler(handler)


__all__ = ["get_logger", "configure_logging", "JsonFormatter"]