"""Configuration management for Cernji Logging."""

import os
from dataclasses import dataclass
from typing import Literal

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
LogFormat = Literal["json", "text"]
Environment = Literal["dev", "development", "staging", "production", "prod"]


@dataclass
class LogConfig:
    """Logging configuration."""

    level: LogLevel
    format: LogFormat
    file_path: str | None
    service_name: str
    service_version: str | None
    environment: Environment

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Create configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),  # type: ignore
            format=os.getenv("LOG_FORMAT", "json").lower(),  # type: ignore
            file_path=os.getenv("LOG_FILE"),
            service_name=os.getenv("SERVICE_NAME", "unknown-service"),
            service_version=os.getenv("SERVICE_VERSION"),
            environment=os.getenv("ENVIRONMENT", "dev").lower(),  # type: ignore
        )


def get_config() -> LogConfig:
    """Get the current logging configuration."""
    return LogConfig.from_env()
