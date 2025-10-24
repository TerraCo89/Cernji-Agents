"""Unit tests for configuration management."""

import pytest
from src.resume_agent.config import get_settings, reset_settings


def test_settings_defaults():
    """Verify default values."""
    # Reset settings to ensure clean state
    reset_settings()

    # Get settings instance
    settings = get_settings()

    # Verify default values exist (may be overridden by .env)
    assert settings.llm_provider in ["claude", "openai"]
    assert settings.temperature >= 0.0 and settings.temperature <= 1.0
    assert settings.max_tokens > 0
    assert settings.max_iterations > 0
    assert settings.ats_score_threshold > 0

    # Verify model names exist (exact values may come from .env)
    assert settings.claude_model is not None and len(settings.claude_model) > 0
    assert settings.openai_model is not None and len(settings.openai_model) > 0


def test_settings_singleton():
    """Verify get_settings returns same instance."""
    # Reset settings first
    reset_settings()

    # Get settings twice
    settings1 = get_settings()
    settings2 = get_settings()

    # Verify they are the same instance
    assert settings1 is settings2

    # Reset and verify new instance is created
    reset_settings()
    settings3 = get_settings()

    # New instance should be different
    assert settings3 is not settings1
