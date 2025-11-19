"""Correlation ID context management using contextvars."""

import contextvars
from contextlib import contextmanager
from typing import Generator
from uuid import uuid4

# Context variable to store correlation ID
_correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context.

    Returns:
        The current correlation ID, or None if not set.
    """
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context.

    Args:
        correlation_id: The correlation ID to set.
    """
    _correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID.

    Returns:
        A new UUID-based correlation ID.
    """
    return str(uuid4())


@contextmanager
def with_correlation_id(correlation_id: str | None = None) -> Generator[str, None, None]:
    """Context manager for setting correlation ID.

    Args:
        correlation_id: The correlation ID to use. If None, generates a new one.

    Yields:
        The correlation ID that was set.

    Example:
        ```python
        with with_correlation_id("req-12345") as cid:
            logger.info("Processing request")  # Includes correlation_id
        ```
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()

    token = _correlation_id_var.set(correlation_id)
    try:
        yield correlation_id
    finally:
        _correlation_id_var.reset(token)


def correlation_id_processor(logger, method_name, event_dict):
    """Structlog processor to inject correlation ID into log records.

    This processor is automatically added to the structlog configuration.
    """
    correlation_id = get_correlation_id()
    if correlation_id is not None:
        event_dict["trace.id"] = correlation_id
    return event_dict
