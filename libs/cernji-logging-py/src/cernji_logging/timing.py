"""Performance timing utilities for logging."""

import functools
import time
from typing import Any, Callable, TypeVar

from structlog.stdlib import BoundLogger

F = TypeVar("F", bound=Callable[..., Any])


def timed(logger: BoundLogger, level: str = "info"):
    """Decorator to log function execution time.

    Args:
        logger: The logger to use for timing logs.
        level: Log level to use (debug, info, warn, error).

    Example:
        ```python
        @timed(logger)
        def expensive_function():
            # ... slow code ...
            pass

        @timed(logger, level="debug")
        async def async_function():
            # ... async code ...
            pass
        ```
    """

    def decorator(func: F) -> F:
        log_method = getattr(logger, level, logger.info)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter_ns()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ns = time.perf_counter_ns() - start_time
                log_method(
                    f"Function {func.__name__} completed",
                    function=func.__name__,
                    module=func.__module__,
                    duration_ns=duration_ns,
                    duration_ms=duration_ns / 1_000_000,
                )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter_ns()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ns = time.perf_counter_ns() - start_time
                log_method(
                    f"Function {func.__name__} completed",
                    function=func.__name__,
                    module=func.__module__,
                    duration_ns=duration_ns,
                    duration_ms=duration_ns / 1_000_000,
                )

        # Return appropriate wrapper based on whether function is async
        if asyncio_iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if a function is an async coroutine function.

    Uses inspect.iscoroutinefunction but handles edge cases.
    """
    import inspect

    return inspect.iscoroutinefunction(func)


class TimingContext:
    """Context manager for timing code blocks.

    Example:
        ```python
        with TimingContext(logger, "database_query") as timer:
            # ... code to time ...
            pass
        # Automatically logs duration
        ```
    """

    def __init__(self, logger: BoundLogger, operation: str, level: str = "info"):
        """Initialize timing context.

        Args:
            logger: The logger to use.
            operation: Name of the operation being timed.
            level: Log level to use.
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: int = 0
        self.duration_ns: int = 0

    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log duration."""
        self.duration_ns = time.perf_counter_ns() - self.start_time
        log_method = getattr(self.logger, self.level, self.logger.info)

        log_method(
            f"Operation {self.operation} completed",
            operation=self.operation,
            duration_ns=self.duration_ns,
            duration_ms=self.duration_ns / 1_000_000,
            error=exc_type is not None,
        )
