"""Tools for Japanese Learning Agent."""

from .screenshot_analyzer import (
    analyze_screenshot_claude,
    analyze_screenshot_manga_ocr,
    hybrid_screenshot_analysis,
)
from .vocabulary_manager import (
    search_vocabulary,
    list_vocabulary_by_status,
    update_vocabulary_status,
    get_vocabulary_statistics,
)
from .flashcard_manager import (
    get_due_flashcards,
    record_flashcard_review,
    create_flashcard,
    get_review_statistics,
)

__all__ = [
    # Screenshot analysis
    "analyze_screenshot_claude",
    "analyze_screenshot_manga_ocr",
    "hybrid_screenshot_analysis",

    # Vocabulary management
    "search_vocabulary",
    "list_vocabulary_by_status",
    "update_vocabulary_status",
    "get_vocabulary_statistics",

    # Flashcard management
    "get_due_flashcards",
    "record_flashcard_review",
    "create_flashcard",
    "get_review_statistics",
]
