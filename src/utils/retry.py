"""Retry decorator for resilient function execution.

Provides a configurable retry mechanism with exponential backoff,
designed primarily for database operations that may encounter
transient failures.
"""

import functools
import logging
import time
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff_sec: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that retries a function on specified exceptions.

    Uses linear backoff: wait = backoff_sec * attempt_number.

    Args:
        max_attempts: Maximum number of attempts before giving up.
        backoff_sec: Base backoff duration in seconds.
        exceptions: Tuple of exception types to catch and retry.

    Returns:
        A decorator function.

    Example:
        @retry(max_attempts=3, backoff_sec=1.0,
               exceptions=(sqlite3.OperationalError,))
        def execute_query(self, sql):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts:
                        wait = backoff_sec * attempt
                        logger.warning(
                            "%s attempt %d/%d failed: %s — "
                            "retrying in %.1f s",
                            func.__name__, attempt, max_attempts,
                            exc, wait,
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, exc,
                        )
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator
