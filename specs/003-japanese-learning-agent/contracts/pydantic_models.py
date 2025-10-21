"""
Pydantic Models for Japanese Learning Agent
Contract definitions for all data entities with validation

These models define the data contract between:
- Services (business logic)
- Repositories (database access)
- CLI scripts (user interface)

All database operations MUST use these validated models.
"""

from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime, timedelta
from typing import List, Optional, Literal
from pathlib import Path
import json


# =============================================================================
# SUB-MODELS
# =============================================================================

class ExtractedTextSegment(BaseModel):
    """
    A single text segment extracted from OCR
    Represents one continuous text block with position and confidence
    """
    text: str = Field(..., min_length=1, description="Extracted Japanese text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    bounds: dict = Field(..., description="Bounding box: {x, y, width, height}")
    character_type: Literal['kanji', 'hiragana', 'katakana', 'romaji', 'mixed'] = Field(
        ..., description="Character classification"
    )

    @validator('bounds')
    def validate_bounds(cls, v):
        required_keys = {'x', 'y', 'width', 'height'}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"bounds must contain: {required_keys}")
        if any(v[k] < 0 for k in required_keys):
            raise ValueError("bounds coordinates must be non-negative")
        return v

    class Config:
        schema_extra = {
            "example": {
                "text": "ポケモン",
                "confidence": 0.95,
                "bounds": {"x": 120, "y": 45, "width": 180, "height": 24},
                "character_type": "katakana"
            }
        }


# =============================================================================
# MAIN ENTITIES
# =============================================================================

class Screenshot(BaseModel):
    """
    Processed game screenshot with OCR extraction results
    Maps to: screenshots table
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    file_path: str = Field(..., min_length=1, description="Absolute path to image file")
    processed_at: datetime = Field(default_factory=datetime.now, description="OCR processing timestamp")
    ocr_confidence: float = Field(..., ge=0.0, le=1.0, description="Average OCR confidence")
    extracted_text: List[ExtractedTextSegment] = Field(
        ..., min_items=1, description="OCR extracted text segments"
    )

    @validator('file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("file_path must be absolute")
        if not path.exists():
            raise ValueError(f"file does not exist: {v}")
        if path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            raise ValueError("file must be PNG or JPEG")
        return str(path)

    @validator('extracted_text')
    def validate_extracted_text(cls, v):
        if len(v) == 0:
            raise ValueError("At least one text segment required (use empty array to indicate OCR failure)")
        return v

    def to_db_dict(self) -> dict:
        """Convert to database-compatible dictionary"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'processed_at': self.processed_at,
            'ocr_confidence': self.ocr_confidence,
            'extracted_text_json': json.dumps([seg.dict() for seg in self.extracted_text])
        }

    @classmethod
    def from_db_dict(cls, data: dict) -> 'Screenshot':
        """Create from database dictionary"""
        extracted_text_json = data.pop('extracted_text_json')
        segments = [ExtractedTextSegment(**seg) for seg in json.loads(extracted_text_json)]
        return cls(**data, extracted_text=segments)

    class Config:
        schema_extra = {
            "example": {
                "file_path": "/screenshots/pokemon_red_001.png",
                "ocr_confidence": 0.93,
                "extracted_text": [
                    {
                        "text": "ポケモンずかん",
                        "confidence": 0.95,
                        "bounds": {"x": 120, "y": 45, "width": 180, "height": 24},
                        "character_type": "katakana"
                    }
                ]
            }
        }


class Vocabulary(BaseModel):
    """
    Unique Japanese word/phrase with translations and learning progress
    Maps to: vocabulary table
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    kanji_form: str = Field(..., min_length=1, description="Word in kanji/kana")
    hiragana_reading: str = Field(..., min_length=1, description="Hiragana reading")
    romaji_reading: Optional[str] = Field(None, description="Optional romaji reading")
    english_meaning: str = Field(..., min_length=1, description="English translation")
    part_of_speech: Optional[str] = Field(None, description="Grammar classification")
    first_seen_at: datetime = Field(default_factory=datetime.now, description="First encounter timestamp")
    last_seen_at: datetime = Field(default_factory=datetime.now, description="Most recent encounter")
    study_status: Literal['new', 'learning', 'known'] = Field('new', description="Learning progress")
    encounter_count: int = Field(1, ge=1, description="Times word appeared")

    @validator('last_seen_at')
    def validate_last_seen_at(cls, v, values):
        if 'first_seen_at' in values and v < values['first_seen_at']:
            raise ValueError("last_seen_at cannot be before first_seen_at")
        return v

    @validator('kanji_form', 'hiragana_reading', 'english_meaning')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    def increment_encounter(self):
        """Increment encounter count and update last_seen_at"""
        self.encounter_count += 1
        self.last_seen_at = datetime.now()

    class Config:
        schema_extra = {
            "example": {
                "kanji_form": "図鑑",
                "hiragana_reading": "ずかん",
                "romaji_reading": "zukan",
                "english_meaning": "encyclopedia, illustrated reference book",
                "part_of_speech": "noun",
                "study_status": "new",
                "encounter_count": 1
            }
        }


class Flashcard(BaseModel):
    """
    Study card for spaced repetition vocabulary review
    Maps to: flashcards table
    Uses SM-2 algorithm for scheduling
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    vocabulary_id: int = Field(..., description="Foreign key to vocabulary")
    screenshot_id: Optional[int] = Field(None, description="Optional screenshot context")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    next_review_at: datetime = Field(default_factory=datetime.now, description="Next review due date")
    ease_factor: float = Field(2.5, ge=1.3, description="SM-2 ease factor (min 1.3)")
    interval_days: float = Field(0.0, ge=0.0, description="SM-2 interval in days")
    review_count: int = Field(0, ge=0, description="Total reviews performed")

    def update_after_review(self, user_response: Literal['again', 'hard', 'medium', 'easy']):
        """
        Update flashcard after review using SM-2 algorithm

        Args:
            user_response: User's recall rating
                - 'again' (0): Complete blackout, need to relearn
                - 'hard' (1): Incorrect but remembered with difficulty
                - 'medium' (2): Correct but required effort
                - 'easy' (3): Perfect recall
        """
        quality_map = {'again': 0, 'hard': 1, 'medium': 2, 'easy': 3}
        quality = quality_map[user_response]

        # Update ease factor
        new_ef = self.ease_factor + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))
        self.ease_factor = max(1.3, new_ef)  # Minimum 1.3

        # Update interval based on quality and review count
        if quality < 2:  # 'again' or 'hard' - reset to beginning
            self.interval_days = 1
        elif self.review_count == 0:  # First review
            self.interval_days = 1
        elif self.review_count == 1:  # Second review
            self.interval_days = 6
        else:  # Subsequent reviews - multiply by ease factor
            self.interval_days = self.interval_days * self.ease_factor

        # Calculate next review date
        self.next_review_at = datetime.now() + timedelta(days=self.interval_days)
        self.review_count += 1

    def is_due(self) -> bool:
        """Check if flashcard is due for review"""
        return datetime.now() >= self.next_review_at

    class Config:
        schema_extra = {
            "example": {
                "vocabulary_id": 1,
                "screenshot_id": 1,
                "ease_factor": 2.5,
                "interval_days": 0.0,
                "review_count": 0
            }
        }


class ReviewSession(BaseModel):
    """
    Individual flashcard review attempt record
    Maps to: review_sessions table
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    flashcard_id: int = Field(..., description="Foreign key to flashcard")
    reviewed_at: datetime = Field(default_factory=datetime.now, description="Review timestamp")
    user_response: Literal['again', 'hard', 'medium', 'easy'] = Field(..., description="User's recall rating")
    response_time_ms: Optional[int] = Field(None, gt=0, description="Response time in milliseconds")
    correct: bool = Field(..., description="Whether answer was correct")

    @root_validator(pre=True)
    def infer_correct_from_response(cls, values):
        """Automatically set correct based on user_response if not provided"""
        if 'correct' not in values and 'user_response' in values:
            values['correct'] = values['user_response'] != 'again'
        return values

    class Config:
        schema_extra = {
            "example": {
                "flashcard_id": 1,
                "user_response": "medium",
                "response_time_ms": 3500,
                "correct": True
            }
        }


# =============================================================================
# STATISTICS MODELS (QUERY RESULTS)
# =============================================================================

class VocabularyStats(BaseModel):
    """Aggregated vocabulary statistics"""
    total_words: int
    new_words: int
    learning_words: int
    known_words: int
    total_encounters: int
    avg_encounters_per_word: float
    most_recent_word: Optional[str] = None
    most_common_word: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "total_words": 150,
                "new_words": 45,
                "learning_words": 80,
                "known_words": 25,
                "total_encounters": 420,
                "avg_encounters_per_word": 2.8,
                "most_recent_word": "図鑑",
                "most_common_word": "の"
            }
        }


class ReviewStats(BaseModel):
    """Aggregated review session statistics"""
    total_reviews: int
    reviews_today: int
    reviews_this_week: int
    correct_count: int
    accuracy_rate: float
    avg_response_time_ms: Optional[float] = None
    flashcards_due: int
    flashcards_overdue: int

    class Config:
        schema_extra = {
            "example": {
                "total_reviews": 342,
                "reviews_today": 15,
                "reviews_this_week": 78,
                "correct_count": 298,
                "accuracy_rate": 0.87,
                "avg_response_time_ms": 4200.0,
                "flashcards_due": 23,
                "flashcards_overdue": 5
            }
        }


class FlashcardWithVocabulary(BaseModel):
    """Flashcard with associated vocabulary details (for review interface)"""
    flashcard: Flashcard
    vocabulary: Vocabulary
    example_screenshot: Optional[str] = None  # File path to screenshot

    class Config:
        schema_extra = {
            "example": {
                "flashcard": {
                    "id": 1,
                    "vocabulary_id": 1,
                    "next_review_at": "2025-10-21T10:30:00",
                    "ease_factor": 2.5,
                    "interval_days": 6.0,
                    "review_count": 3
                },
                "vocabulary": {
                    "id": 1,
                    "kanji_form": "図鑑",
                    "hiragana_reading": "ずかん",
                    "english_meaning": "encyclopedia",
                    "study_status": "learning"
                },
                "example_screenshot": "/screenshots/pokemon_red_001.png"
            }
        }


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_study_status_transition(
    current_status: Literal['new', 'learning', 'known'],
    new_status: Literal['new', 'learning', 'known']
) -> bool:
    """
    Validate study status transitions

    Allowed transitions:
    - new → learning (when flashcard created)
    - learning → known (user marks as mastered)
    - Any status → new (manual reset)
    """
    allowed_transitions = {
        ('new', 'learning'),
        ('learning', 'known'),
        ('new', 'new'),
        ('learning', 'new'),
        ('known', 'new'),
        ('known', 'known'),
        ('learning', 'learning')
    }
    return (current_status, new_status) in allowed_transitions


# =============================================================================
# CONTRACT TESTS (to be implemented in tests/contract/)
# =============================================================================

"""
Contract test requirements:

1. test_screenshot_model_validation():
   - Valid screenshot passes validation
   - Invalid file paths raise ValueError
   - Confidence out of range raises ValueError
   - Empty extracted_text raises ValueError
   - to_db_dict() → from_db_dict() roundtrip preserves data

2. test_vocabulary_model_validation():
   - Valid vocabulary passes validation
   - Empty strings raise ValueError
   - last_seen_at < first_seen_at raises ValueError
   - increment_encounter() updates correctly

3. test_flashcard_sm2_algorithm():
   - update_after_review() implements SM-2 correctly
   - ease_factor minimum enforced (1.3)
   - interval_days calculated correctly
   - is_due() returns correct boolean

4. test_review_session_model_validation():
   - correct is inferred from user_response
   - Invalid user_response raises ValueError

5. test_model_serialization():
   - All models serialize to/from JSON correctly
   - Database conversion methods work (to_db_dict, from_db_dict)
"""
