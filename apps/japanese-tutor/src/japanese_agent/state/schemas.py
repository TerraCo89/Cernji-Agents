"""
State schemas for the Japanese Learning Agent LangGraph implementation.

This module defines the state structure using TypedDict and custom reducers.
The state persists across conversation turns via checkpointing.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

# ============================================================================
# STATE REDUCERS
# ============================================================================

def append_unique_vocabulary(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    Custom reducer for vocabulary field.

    Appends only new unique vocabulary entries (based on 'id' or 'word' field).
    This prevents duplicate vocabulary in the state.

    Args:
        existing: Current list of vocabulary
        new: New vocabulary to add

    Returns:
        Combined list with only unique entries
    """
    if not existing:
        return new if new else []

    if not new:
        return existing

    # Build set of existing IDs/words
    existing_ids = set()
    for entry in existing:
        if 'id' in entry and entry['id']:
            existing_ids.add(('id', entry['id']))
        elif 'vocab_id' in entry and entry['vocab_id']:
            existing_ids.add(('vocab_id', entry['vocab_id']))
        elif 'word' in entry and entry['word']:
            existing_ids.add(('word', entry['word']))

    # Filter new entries
    unique_new = []
    for entry in new:
        is_unique = True

        if 'id' in entry and ('id', entry['id']) in existing_ids:
            is_unique = False
        elif 'vocab_id' in entry and ('vocab_id', entry['vocab_id']) in existing_ids:
            is_unique = False
        elif 'word' in entry and ('word', entry['word']) in existing_ids:
            is_unique = False

        if is_unique:
            unique_new.append(entry)

    return existing + unique_new


def append_unique_flashcards(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    Custom reducer for flashcards field.

    Appends only new unique flashcards (based on 'id' or 'flashcard_id').

    Args:
        existing: Current list of flashcards
        new: New flashcards to add

    Returns:
        Combined list with only unique flashcards
    """
    if not existing:
        return new if new else []

    if not new:
        return existing

    existing_ids = {entry.get('id') or entry.get('flashcard_id') for entry in existing}
    unique_new = [
        entry for entry in new
        if (entry.get('id') or entry.get('flashcard_id')) not in existing_ids
    ]

    return existing + unique_new


def replace_with_latest(existing: Optional[Any], new: Optional[Any]) -> Optional[Any]:
    """
    Custom reducer that replaces existing value with new value.

    Used for fields like current_screenshot where we always want the latest value.

    Args:
        existing: Current value (ignored)
        new: New value to replace with

    Returns:
        The new value
    """
    return new if new is not None else existing


# ============================================================================
# DATA STRUCTURE TYPEDDICTS
# ============================================================================

class ExtractedTextDict(TypedDict, total=False):
    """Extracted text segment from OCR."""
    text: str
    reading: Optional[str]  # Furigana or romaji
    confidence: float
    position: Optional[Dict[str, int]]  # {x, y, width, height}


class VocabularyDict(TypedDict, total=False):
    """Japanese vocabulary entry."""
    id: Optional[int]
    vocab_id: Optional[int]
    word: str  # Japanese text
    reading: str  # Hiragana reading
    meaning: str  # English translation
    part_of_speech: Optional[str]
    jlpt_level: Optional[str]
    frequency: Optional[int]
    encounter_count: int
    study_status: Literal["new", "learning", "known"]
    first_seen: str  # ISO timestamp
    last_reviewed: Optional[str]  # ISO timestamp


class FlashcardDict(TypedDict, total=False):
    """Flashcard for spaced repetition."""
    id: Optional[int]
    flashcard_id: Optional[int]
    vocab_id: int
    word: str
    reading: str
    meaning: str
    interval: int  # Days until next review
    ease_factor: float  # SM-2 algorithm ease
    repetitions: int
    next_review: str  # ISO timestamp
    last_review: Optional[str]  # ISO timestamp


class ScreenshotDict(TypedDict, total=False):
    """Screenshot metadata and OCR results."""
    id: Optional[int]
    screenshot_id: Optional[int]
    file_path: str
    base64_data: Optional[str]  # Base64-encoded image data for reliable retrieval
    mime_type: Optional[str]  # MIME type of the image (e.g., "image/png")
    processed_at: str  # ISO timestamp
    extracted_text: List[ExtractedTextDict]
    translation: Optional[str]
    context: Optional[str]  # Game context description
    ocr_method: Literal["claude", "manga-ocr", "hybrid"]


class ReviewSessionDict(TypedDict, total=False):
    """Flashcard review session data."""
    flashcard_id: int
    rating: Literal[0, 1, 2, 3]  # again, hard, medium, easy
    reviewed_at: str  # ISO timestamp
    time_taken_seconds: Optional[int]


# ============================================================================
# WORKFLOW CONTROL TYPES
# ============================================================================

class WorkflowIntent(TypedDict, total=False):
    """User intent classification for workflow routing."""
    intent_type: Literal[
        "analyze_screenshot",
        "review_flashcards",
        "list_vocabulary",
        "search_vocabulary",
        "general_chat",
    ]
    confidence: float  # 0.0 to 1.0
    extracted_params: Dict[str, Any]  # e.g., {"image_path": "/path/to/image.png"}


class WorkflowProgress(TypedDict, total=False):
    """Track progress through multi-step workflows."""
    workflow_type: str  # "screenshot_analysis", "flashcard_review", etc.
    steps_completed: List[str]
    steps_remaining: List[str]
    current_step: Optional[str]
    errors: List[str]


# ============================================================================
# MAIN STATE SCHEMA
# ============================================================================

class JapaneseAgentState(TypedDict):
    """
    Complete state for Japanese Learning Agent LangGraph implementation.

    This state persists across conversation turns via SQLite checkpointing.
    Each field can be updated independently by nodes in the graph.

    Required Fields:
        messages: Conversation history (uses add_messages reducer)

    Optional Fields (learning data):
        current_screenshot: Currently analyzed screenshot
        vocabulary: List of vocabulary entries (append-only with dedup)
        flashcards: List of flashcards (append-only with dedup)
        review_session: Current review session data

    Optional Fields (workflow control):
        current_intent: Classified user intent
        workflow_progress: Multi-step workflow tracking
        requires_user_input: Whether agent is waiting for user input
        error_message: Latest error if any

    Optional Fields (learning stats):
        total_vocabulary: Total vocabulary count
        known_vocabulary: Count of known words
        review_due_count: Count of flashcards due for review
    """

    # ========== REQUIRED FIELDS ==========

    # Conversation history (LangGraph requirement for chat agents)
    messages: Annotated[List[BaseMessage], add_messages]

    # UI components (for generative UI)
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]

    # ========== LEARNING DATA ==========

    # Current screenshot being analyzed
    current_screenshot: Annotated[
        Optional[ScreenshotDict],
        replace_with_latest
    ]

    # Vocabulary list (append unique only)
    vocabulary: Annotated[
        List[VocabularyDict],
        append_unique_vocabulary
    ]

    # Flashcards (append unique only)
    flashcards: Annotated[
        List[FlashcardDict],
        append_unique_flashcards
    ]

    # Current review session data
    review_session: Annotated[
        Optional[Dict[str, Any]],
        replace_with_latest
    ]

    # ========== WORKFLOW CONTROL ==========

    # Current user intent classification
    current_intent: Annotated[
        Optional[WorkflowIntent],
        replace_with_latest
    ]

    # Workflow progress tracking
    workflow_progress: Annotated[
        Optional[WorkflowProgress],
        replace_with_latest
    ]

    # Whether agent needs user input
    requires_user_input: Annotated[
        bool,
        replace_with_latest
    ]

    # Latest error message
    error_message: Annotated[
        Optional[str],
        replace_with_latest
    ]

    # ========== LEARNING STATISTICS ==========

    # Total vocabulary count
    total_vocabulary: Annotated[
        int,
        replace_with_latest
    ]

    # Known vocabulary count
    known_vocabulary: Annotated[
        int,
        replace_with_latest
    ]

    # Flashcards due for review
    review_due_count: Annotated[
        int,
        replace_with_latest
    ]

    # ========== METADATA ==========

    # User ID (for multi-user support)
    user_id: Annotated[
        str,
        replace_with_latest
    ]


# ============================================================================
# STATE INITIALIZATION HELPERS
# ============================================================================

def create_initial_state(user_id: str = "default") -> JapaneseAgentState:
    """
    Create a new initial state for a conversation.

    Args:
        user_id: User identifier (default: "default")

    Returns:
        Initial state dict with required fields populated
    """
    return {
        "messages": [],
        "ui": [],
        "current_screenshot": None,
        "vocabulary": [],
        "flashcards": [],
        "review_session": None,
        "current_intent": None,
        "workflow_progress": None,
        "requires_user_input": False,
        "error_message": None,
        "total_vocabulary": 0,
        "known_vocabulary": 0,
        "review_due_count": 0,
        "user_id": user_id,
    }


def update_state(
    current_state: JapaneseAgentState,
    **updates: Any
) -> Dict[str, Any]:
    """
    Create a state update dict with only the specified fields.

    This is the recommended way to return state updates from nodes.
    Only include fields that you want to update.

    Args:
        current_state: Current state (for reference, not modified)
        **updates: Field names and new values

    Returns:
        Update dict to be returned from node

    Example:
        return update_state(
            state,
            vocabulary=[new_vocab],
            messages=[AIMessage(content="Analysis complete!")]
        )
    """
    return dict(updates.items())


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_screenshot_exists(state: JapaneseAgentState) -> bool:
    """Check if current screenshot exists in state."""
    return state.get("current_screenshot") is not None


def validate_has_vocabulary(state: JapaneseAgentState) -> bool:
    """Check if vocabulary list is not empty."""
    return len(state.get("vocabulary", [])) > 0


def validate_has_due_flashcards(state: JapaneseAgentState) -> bool:
    """Check if there are flashcards due for review."""
    return state.get("review_due_count", 0) > 0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Main state
    "JapaneseAgentState",

    # Data structures
    "ExtractedTextDict",
    "VocabularyDict",
    "FlashcardDict",
    "ScreenshotDict",
    "ReviewSessionDict",

    # Workflow control
    "WorkflowIntent",
    "WorkflowProgress",

    # Reducers
    "append_unique_vocabulary",
    "append_unique_flashcards",
    "replace_with_latest",

    # Helpers
    "create_initial_state",
    "update_state",

    # Validators
    "validate_screenshot_exists",
    "validate_has_vocabulary",
    "validate_has_due_flashcards",
]
