"""Cernji Logging - Standardized structured logging for Cernji Agents."""

import logging
import sys
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from .config import LogConfig, get_config
from .context import (
    correlation_id_processor,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    with_correlation_id,
)
from .timing import TimingContext, timed

__version__ = "0.1.0"

__all__ = [
    "get_logger",
    "configure_logging",
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id",
    "with_correlation_id",
    "timed",
    "TimingContext",
    "BoundLogger",
]

_configured = False


def _ecs_timestamp_processor(logger, method_name, event_dict):
    """Convert timestamp to ECS format (@timestamp)."""
    if "timestamp" in event_dict:
        event_dict["@timestamp"] = event_dict.pop("timestamp")
    return event_dict


def _ecs_level_processor(logger, method_name, event_dict):
    """Convert log level to ECS format (log.level)."""
    if "level" in event_dict:
        event_dict["log.level"] = event_dict.pop("level")
    return event_dict


def _service_info_processor(logger, method_name, event_dict):
    """Add service information to log records."""
    config = get_config()
    event_dict["service.name"] = config.service_name
    if config.service_version:
        event_dict["service.version"] = config.service_version
    event_dict["service.environment"] = config.environment
    event_dict["ecs.version"] = "8.11.0"
    return event_dict


def _event_module_processor(logger, method_name, event_dict):
    """Add module information to log records."""
    if hasattr(logger, "name"):
        event_dict["event.module"] = logger.name
    return event_dict


def configure_logging(config: LogConfig | None = None, **kwargs: Any) -> None:
    """Configure structlog with ECS format and correlation ID tracking.

    This function is automatically called on first logger creation.
    You can call it manually to reconfigure logging.

    Args:
        config: LogConfig object. If None, loads from environment.
        **kwargs: Override specific config values.
    """
    global _configured

    if config is None:
        config = get_config()

    # Override config with kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout if config.file_path is None else open(config.file_path, "a"),
        level=getattr(logging, config.level),
    )

    # Determine processors based on format
    if config.format == "json":
        renderer = structlog.processors.JSONRenderer()
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Custom ECS processors
            correlation_id_processor,
            _service_info_processor,
            _event_module_processor,
            _ecs_timestamp_processor,
            _ecs_level_processor,
            renderer,
        ]
    else:
        # Human-readable format for development
        renderer = structlog.dev.ConsoleRenderer()
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            correlation_id_processor,
            _service_info_processor,
            _event_module_processor,
            renderer,
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str | None = None) -> BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name. Typically __name__ of the calling module.

    Returns:
        A BoundLogger instance configured for structured logging.

    Example:
        ```python
        from cernji_logging import get_logger

        logger = get_logger(__name__)
        logger.info("Application started", version="1.0.0")
        ```
    """
    if not _configured:
        configure_logging()

    return structlog.get_logger(name)
