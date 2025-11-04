"""Pytest configuration and fixtures for Japanese Learning Agent tests."""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_screenshot_dict() -> Dict[str, Any]:
    """Sample screenshot data for testing."""
    return {
        "id": 1,
        "file_path": "/test/screenshot.png",
        "processed_at": "2025-10-31T00:00:00Z",
        "extracted_text": [
            {
                "text": "ポケモン",
                "reading": "pokemon",
                "confidence": 0.95,
            }
        ],
        "translation": "Pokemon",
        "context": "Game title screen",
        "ocr_method": "hybrid",
    }


@pytest.fixture
def sample_vocabulary_dict() -> Dict[str, Any]:
    """Sample vocabulary entry for testing."""
    return {
        "id": 1,
        "word": "ポケモン",
        "reading": "ぽけもん",
        "meaning": "Pokemon (pocket monsters)",
        "part_of_speech": "noun",
        "jlpt_level": "N5",
        "encounter_count": 1,
        "study_status": "new",
        "first_seen": "2025-10-31T00:00:00Z",
    }


@pytest.fixture
def sample_flashcard_dict() -> Dict[str, Any]:
    """Sample flashcard for testing."""
    return {
        "id": 1,
        "vocab_id": 1,
        "word": "ポケモン",
        "reading": "ぽけもん",
        "meaning": "Pokemon",
        "interval": 1,
        "ease_factor": 2.5,
        "repetitions": 0,
        "next_review": "2025-11-01T00:00:00Z",
    }
