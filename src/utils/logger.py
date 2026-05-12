"""Structured JSON logger for the E-Commerce Analytics Platform.

Provides a configured logger that outputs JSON-formatted log lines
with automatic log rotation.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Each log line contains: timestamp, level, module, function,
    message, and any extra fields passed via the ``extra`` kwarg.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A single-line JSON string.
        """
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include any extra fields attached to the record
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, default=str)


def setup_logger(
    name: str = "ecommerce_analytics",
    log_dir: str = "logs",
    log_file: str = "pipeline.log",
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """Configure and return a structured JSON logger.

    Args:
        name: Logger name (used as the logging namespace).
        log_dir: Directory for log files.
        log_file: Name of the log file.
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        max_bytes: Maximum size per log file before rotation.
        backup_count: Number of rotated log files to keep.
        console_output: Whether to also log to stderr.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ── File handler with rotation ───────────────────────────────────────
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path / log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # ── Console handler (human-readable) ─────────────────────────────────
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_fmt = logging.Formatter(
            "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "ecommerce_analytics") -> logging.Logger:
    """Retrieve an existing logger by name.

    If the logger has not been configured yet, sets it up with defaults.

    Args:
        name: Logger namespace.

    Returns:
        The logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
