"""
Structured Logging Module.

Provides JSON-structured logging with consistent format across the application.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info[1] else None
            }

        if hasattr(record, 'extra_data') and record.extra_data:
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Structured logger with consistent JSON output."""

    def __init__(self, name: str = "synthesis-prime", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def _log_with_context(self, level: int, message: str, exc_info: bool = False, **kwargs):
        extra = kwargs.pop('extra_data', {})
        self.logger.log(level, message, exc_info=exc_info, extra={"extra_data": extra})

    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = True, **kwargs):
        self._log_with_context(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = True, **kwargs):
        self._log_with_context(logging.CRITICAL, message, exc_info=exc_info, **kwargs)


def log_execution_time(logger: StructuredLogger, operation_name: str):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"{operation_name} completed", extra_data={"execution_time_ms": round(elapsed, 2)})
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{operation_name} failed",
                    extra_data={
                        "execution_time_ms": round(elapsed, 2),
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise
        return wrapper
    return decorator


def get_logger(name: str = "synthesis-prime") -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
