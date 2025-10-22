# Data Model: Japanese Learning Agent

**Feature**: 003-japanese-learning-agent
**Date**: 2025-10-21
**Purpose**: Define all data entities, relationships, and validation rules for the Japanese learning system.

## Entity Overview

The system manages four primary entities:

1. **Screenshot** - Game screenshot images with OCR results
2. **Vocabulary** - Unique Japanese words/phrases encountered
3. **Flashcard** - Study cards for spaced repetition
4. **ReviewSession** - Individual flashcard review records

## Entity Definitions

### 1. Screenshot

**Purpose**: Track processed screenshots with OCR extraction results

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique screenshot identifier |
| file_path | TEXT | NOT NULL, UNIQUE | Absolute path to image file |
| processed_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When OCR was performed |
| ocr_confidence | REAL | CHECK(ocr_confidence BETWEEN 0.0 AND 1.0) | Average confidence score from OCR |
| extracted_text_json | TEXT | NOT NULL | JSON array of extracted text segments |

**JSON Structure for extracted_text_json**:
```json
[
  {
    "text": "ポケモンずかん",
    "confidence": 0.95,
    "bounds": {"x": 120, "y": 45, "width": 180, "height": 24},
    "character_type": "katakana"
  },
  {
    "text": "完成",
    "confidence": 0.92,
    "bounds": {"x": 120, "y": 75, "width": 60, "height": 24},
    "character_type": "kanji"
  }
]
```

**Validation Rules**:
- file_path must be absolute and point to existing file (PNG/JPG/JPEG)
- ocr_confidence must be between 0.0 and 1.0
- extracted_text_json must be valid JSON array
- At least one text segment should exist (empty array indicates OCR failure)

**State Transitions**: None (immutable after creation)

**Indexes**:
- UNIQUE INDEX on file_path (prevent duplicate processing)
- INDEX on processed_at (for recent screenshots query)

---

### 2. Vocabulary

**Purpose**: Track unique Japanese words with translations and study status

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique vocabulary identifier |
| kanji_form | TEXT | NOT NULL | Word in kanji/kana form |
| hiragana_reading | TEXT | NOT NULL | Reading in hiragana |
| romaji_reading | TEXT | NULL | Optional romaji reading |
| english_meaning | TEXT | NOT NULL | English translation |
| part_of_speech | TEXT | NULL | Grammar classification (noun, verb, etc.) |
| first_seen_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When first encountered |
| last_seen_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Most recent occurrence |
| study_status | TEXT | NOT NULL, DEFAULT 'new', CHECK(study_status IN ('new', 'learning', 'known')) | Learning progress |
| encounter_count | INTEGER | NOT NULL, DEFAULT 1, CHECK(encounter_count >= 1) | Times word appeared |

**Validation Rules**:
- UNIQUE(kanji_form, hiragana_reading) - Prevent duplicate entries
- kanji_form and hiragana_reading cannot be empty strings
- english_meaning cannot be empty string
- study_status must be one of: 'new', 'learning', 'known'
- encounter_count must be at least 1
- last_seen_at >= first_seen_at

**State Transitions**:
```
new → learning → known
  ↓       ↓        ↓
  ←───────┴────────┘ (manual reset possible)
```

**Indexes**:
- UNIQUE INDEX on (kanji_form, hiragana_reading)
- INDEX on study_status (for filtering by learning status)
- INDEX on last_seen_at (for recently encountered words)

**Business Logic**:
- When word is re-encountered: increment encounter_count, update last_seen_at
- Auto-transition from 'new' to 'learning' when flashcard is created
- User can manually set status to 'known' to skip flashcard reviews

---

### 3. Flashcard

**Purpose**: Study cards for spaced repetition vocabulary review

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique flashcard identifier |
| vocabulary_id | INTEGER | NOT NULL, FOREIGN KEY → vocabulary(id) ON DELETE CASCADE | Associated vocabulary word |
| screenshot_id | INTEGER | NULL, FOREIGN KEY → screenshots(id) ON DELETE SET NULL | Example context (optional) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Flashcard creation time |
| next_review_at | TIMESTAMP | NOT NULL | When card is due for review |
| ease_factor | REAL | NOT NULL, DEFAULT 2.5, CHECK(ease_factor >= 1.3) | SM-2 algorithm ease |
| interval_days | REAL | NOT NULL, DEFAULT 0.0, CHECK(interval_days >= 0) | SM-2 algorithm interval |
| review_count | INTEGER | NOT NULL, DEFAULT 0, CHECK(review_count >= 0) | Total reviews performed |

**Validation Rules**:
- vocabulary_id must reference existing vocabulary entry
- screenshot_id can be NULL (if no context available) or must reference existing screenshot
- ease_factor minimum is 1.3 (SM-2 algorithm constraint)
- interval_days cannot be negative
- next_review_at initially set to created_at (immediately reviewable)

**State Transitions**:
```
created (new) → under_review (active) → mastered (long interval)
     ↓               ↓                       ↓
     └───────────────┴───────────────────────┘ (review updates interval)
```

**Indexes**:
- INDEX on vocabulary_id (for looking up flashcards by word)
- INDEX on next_review_at (for finding due reviews)
- INDEX on created_at (for recent flashcards query)

**Business Logic (SM-2 Algorithm)**:

```python
def update_flashcard_after_review(flashcard, user_response):
    """
    user_response: 'again' (0), 'hard' (1), 'medium' (2), 'easy' (3)
    """
    quality = {'again': 0, 'hard': 1, 'medium': 2, 'easy': 3}[user_response]

    # Update ease factor
    new_ef = flashcard.ease_factor + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))
    flashcard.ease_factor = max(1.3, new_ef)  # Minimum 1.3

    # Update interval
    if quality < 2:  # 'again' or 'hard'
        flashcard.interval_days = 1  # Reset to 1 day
    elif flashcard.review_count == 0:
        flashcard.interval_days = 1
    elif flashcard.review_count == 1:
        flashcard.interval_days = 6
    else:
        flashcard.interval_days = flashcard.interval_days * flashcard.ease_factor

    # Update next review date
    flashcard.next_review_at = datetime.now() + timedelta(days=flashcard.interval_days)
    flashcard.review_count += 1
```

---

### 4. ReviewSession

**Purpose**: Record individual flashcard review attempts for statistics and learning analytics

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique review session identifier |
| flashcard_id | INTEGER | NOT NULL, FOREIGN KEY → flashcards(id) ON DELETE CASCADE | Reviewed flashcard |
| reviewed_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When review occurred |
| user_response | TEXT | NOT NULL, CHECK(user_response IN ('again', 'hard', 'medium', 'easy')) | User's recall rating |
| response_time_ms | INTEGER | NULL, CHECK(response_time_ms > 0) | Time taken to answer (milliseconds) |
| correct | BOOLEAN | NOT NULL | Whether answer was correct |

**Validation Rules**:
- flashcard_id must reference existing flashcard
- user_response must be one of: 'again', 'hard', 'medium', 'easy'
- response_time_ms (if provided) must be positive
- correct is inferred from user_response: 'again' = FALSE, others = TRUE

**State Transitions**: None (immutable records)

**Indexes**:
- INDEX on flashcard_id (for flashcard review history)
- INDEX on reviewed_at (for daily/weekly statistics)

**Business Logic**:
- Each review creates a new ReviewSession record
- ReviewSession records are never deleted (preserved for analytics)
- Aggregate queries provide statistics (FR-015 requirement)

---

## Entity Relationships

```
Screenshot (1) ──────┐
                     │
                     ├─→ (0..N) Vocabulary ──→ (1..N) Flashcard ──→ (0..N) ReviewSession
                     │
Screenshot (N) ──────┘
```

**Relationship Descriptions**:

1. **Screenshot → Vocabulary** (Many-to-Many, implicit via extracted text)
   - A screenshot can contain multiple words
   - A word can appear in multiple screenshots
   - No explicit junction table (relationship inferred via extracted_text_json)

2. **Vocabulary → Flashcard** (One-to-Many)
   - One vocabulary word can have multiple flashcards (e.g., different contexts)
   - Each flashcard belongs to exactly one vocabulary word
   - CASCADE delete: Deleting vocabulary deletes all associated flashcards

3. **Screenshot → Flashcard** (One-to-Many, optional)
   - One screenshot can provide context for multiple flashcards
   - Each flashcard may or may not have screenshot context
   - SET NULL delete: Deleting screenshot removes context reference but keeps flashcard

4. **Flashcard → ReviewSession** (One-to-Many)
   - One flashcard can have many review sessions (review history)
   - Each review session belongs to exactly one flashcard
   - CASCADE delete: Deleting flashcard deletes all review history

## Pydantic Model Definitions

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Literal

class ExtractedTextSegment(BaseModel):
    text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounds: dict = Field(..., description="x, y, width, height")
    character_type: str = Field(..., pattern="^(kanji|hiragana|katakana|romaji|mixed)$")

class Screenshot(BaseModel):
    id: Optional[int] = None
    file_path: str = Field(..., min_length=1)
    processed_at: datetime = Field(default_factory=datetime.now)
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_text: List[ExtractedTextSegment] = Field(..., min_length=1)

    @validator('file_path')
    def validate_file_path(cls, v):
        from pathlib import Path
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("file_path must be absolute")
        if not path.exists():
            raise ValueError(f"file does not exist: {v}")
        if path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            raise ValueError("file must be PNG or JPEG")
        return str(path)

class Vocabulary(BaseModel):
    id: Optional[int] = None
    kanji_form: str = Field(..., min_length=1)
    hiragana_reading: str = Field(..., min_length=1)
    romaji_reading: Optional[str] = None
    english_meaning: str = Field(..., min_length=1)
    part_of_speech: Optional[str] = None
    first_seen_at: datetime = Field(default_factory=datetime.now)
    last_seen_at: datetime = Field(default_factory=datetime.now)
    study_status: Literal['new', 'learning', 'known'] = 'new'
    encounter_count: int = Field(default=1, ge=1)

    @validator('last_seen_at')
    def validate_last_seen_at(cls, v, values):
        if 'first_seen_at' in values and v < values['first_seen_at']:
            raise ValueError("last_seen_at cannot be before first_seen_at")
        return v

class Flashcard(BaseModel):
    id: Optional[int] = None
    vocabulary_id: int
    screenshot_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    next_review_at: datetime = Field(default_factory=datetime.now)
    ease_factor: float = Field(default=2.5, ge=1.3)
    interval_days: float = Field(default=0.0, ge=0.0)
    review_count: int = Field(default=0, ge=0)

class ReviewSession(BaseModel):
    id: Optional[int] = None
    flashcard_id: int
    reviewed_at: datetime = Field(default_factory=datetime.now)
    user_response: Literal['again', 'hard', 'medium', 'easy']
    response_time_ms: Optional[int] = Field(None, gt=0)
    correct: bool

    @validator('correct', always=True)
    def infer_correct_from_response(cls, v, values):
        if 'user_response' in values:
            return values['user_response'] != 'again'
        return v
```

## Database Migrations

**Migration 001 - Initial Schema**:

```sql
-- screenshots table
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ocr_confidence REAL NOT NULL CHECK(ocr_confidence BETWEEN 0.0 AND 1.0),
    extracted_text_json TEXT NOT NULL
);

CREATE INDEX idx_screenshots_processed_at ON screenshots(processed_at);

-- vocabulary table
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji_form TEXT NOT NULL,
    hiragana_reading TEXT NOT NULL,
    romaji_reading TEXT,
    english_meaning TEXT NOT NULL,
    part_of_speech TEXT,
    first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    study_status TEXT NOT NULL DEFAULT 'new' CHECK(study_status IN ('new', 'learning', 'known')),
    encounter_count INTEGER NOT NULL DEFAULT 1 CHECK(encounter_count >= 1),
    UNIQUE(kanji_form, hiragana_reading)
);

CREATE INDEX idx_vocabulary_study_status ON vocabulary(study_status);
CREATE INDEX idx_vocabulary_last_seen_at ON vocabulary(last_seen_at);

-- flashcards table
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocabulary_id INTEGER NOT NULL,
    screenshot_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    next_review_at TIMESTAMP NOT NULL,
    ease_factor REAL NOT NULL DEFAULT 2.5 CHECK(ease_factor >= 1.3),
    interval_days REAL NOT NULL DEFAULT 0.0 CHECK(interval_days >= 0),
    review_count INTEGER NOT NULL DEFAULT 0 CHECK(review_count >= 0),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE SET NULL
);

CREATE INDEX idx_flashcards_vocabulary_id ON flashcards(vocabulary_id);
CREATE INDEX idx_flashcards_next_review_at ON flashcards(next_review_at);
CREATE INDEX idx_flashcards_created_at ON flashcards(created_at);

-- review_sessions table
CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flashcard_id INTEGER NOT NULL,
    reviewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_response TEXT NOT NULL CHECK(user_response IN ('again', 'hard', 'medium', 'easy')),
    response_time_ms INTEGER CHECK(response_time_ms > 0),
    correct BOOLEAN NOT NULL,
    FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
);

CREATE INDEX idx_review_sessions_flashcard_id ON review_sessions(flashcard_id);
CREATE INDEX idx_review_sessions_reviewed_at ON review_sessions(reviewed_at);
```

## Query Patterns

### Common Queries

**1. Get due flashcards for review**:
```sql
SELECT f.*, v.kanji_form, v.hiragana_reading, v.english_meaning
FROM flashcards f
JOIN vocabulary v ON f.vocabulary_id = v.id
WHERE f.next_review_at <= CURRENT_TIMESTAMP
ORDER BY f.next_review_at ASC
LIMIT ?;
```

**2. Get vocabulary by study status**:
```sql
SELECT * FROM vocabulary
WHERE study_status = ?
ORDER BY last_seen_at DESC;
```

**3. Get vocabulary statistics**:
```sql
SELECT
    study_status,
    COUNT(*) as count,
    SUM(encounter_count) as total_encounters
FROM vocabulary
GROUP BY study_status;
```

**4. Get recent review history for a flashcard**:
```sql
SELECT * FROM review_sessions
WHERE flashcard_id = ?
ORDER BY reviewed_at DESC
LIMIT 10;
```

**5. Find or create vocabulary (upsert pattern)**:
```sql
INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, part_of_speech)
VALUES (?, ?, ?, ?)
ON CONFLICT(kanji_form, hiragana_reading) DO UPDATE SET
    last_seen_at = CURRENT_TIMESTAMP,
    encounter_count = encounter_count + 1
RETURNING id;
```

## Data Integrity Rules

1. **Referential Integrity**:
   - All foreign keys must reference existing records
   - Cascade deletes propagate to dependent records
   - SET NULL deletes preserve dependent records with null references

2. **Uniqueness Constraints**:
   - Screenshot file_path must be unique (prevent duplicate processing)
   - Vocabulary (kanji_form, hiragana_reading) must be unique (prevent duplicate words)

3. **Check Constraints**:
   - Confidence scores between 0.0 and 1.0
   - Study status must be valid enum value
   - Encounter counts must be positive
   - Ease factors must be >= 1.3 (SM-2 requirement)
   - Intervals must be non-negative

4. **Timestamp Consistency**:
   - last_seen_at >= first_seen_at for vocabulary
   - next_review_at updated after each review session
   - All timestamps use UTC (avoid timezone issues)

## Performance Optimizations

1. **Indexes**: All foreign keys and frequently queried fields are indexed
2. **JSON Storage**: extracted_text_json stored as TEXT (no JSON parsing in queries)
3. **Batch Operations**: Repository pattern supports bulk inserts
4. **Connection Pooling**: Single SQLite connection per process (no pool overhead)
5. **WAL Mode**: Enable Write-Ahead Logging for concurrent reads during writes

```python
# Enable WAL mode in base repository
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
```

---

This data model satisfies all functional requirements (FR-001 through FR-018) and supports the performance requirements defined in the specification.
