"""
Configuration management for Resume Agent.

Handles environment variables, API keys, and runtime settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    anthropic_api_key: str
    openai_api_key: Optional[str] = None
    
    # LLM Settings
    model_name: str = "claude-sonnet-4-20250514"
    temperature: float = 0.0
    max_tokens: int = 4096
    
    # Agent Settings
    max_iterations: int = 3
    require_manual_review: bool = True
    ats_score_threshold: int = 80
    
    # Scraping Settings
    scraping_timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Paths
    cache_dir: Path = Path("./cache")
    output_dir: Path = Path("./output")
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global settings
    settings = Settings()
    return settings
