"""Configuration management for Resume Agent."""

import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM Configuration
    llm_provider: Literal["claude", "openai"] = Field(
        default="claude",
        description="LLM provider to use"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT models"
    )
    claude_model: str = Field(
        default="claude-sonnet-4-5",
        description="Claude model name"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )

    # LLM Parameters
    temperature: float = Field(
        default=0.7,
        description="LLM temperature"
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens per response"
    )

    # Application Settings
    max_iterations: int = Field(
        default=3,
        description="Maximum optimization iterations"
    )
    ats_score_threshold: int = Field(
        default=80,
        description="Target ATS score"
    )


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
