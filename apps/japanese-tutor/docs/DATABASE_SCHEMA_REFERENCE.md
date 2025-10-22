# Database Schema Reference
**Japanese Learning Application - Technical Documentation**

Version: 2.0  
Last Updated: 2025-10-22  
Database: SQLite 3  
Location: `data/japanese_agent.db`

---

## Table of Contents

1. [Overview](#overview)
2. [Database Statistics](#database-statistics)
3. [Entity Relationship Diagram](#entity-relationship-diagram)
4. [Core Entities](#core-entities)
5. [Learning System](#learning-system)
6. [Content Management](#content-management)
7. [Relationship Tables](#relationship-tables)
8. [Utility Tables](#utility-tables)
9. [Indexes and Performance](#indexes-and-performance)
10. [Constraints and Validation](#constraints-and-validation)
11. [Triggers and Automation](#triggers-and-automation)

---

## Overview

This database supports a Japanese language learning application with the following key features:
- Screenshot-based vocabulary extraction via OCR
- Spaced repetition flashcard system (SM-2 algorithm)
- Kanji learning with radical decomposition
- Context-based example sentences
- Source material tracking
- Study goal management
- Tag-based organization

### Design Principles

- **Normalized Structure**: Third normal form (3NF) with junction tables
- **Foreign Key Integrity**: All relationships enforced with CASCADE/SET NULL
- **Audit Trail**: Created_at and updated_at timestamps on all entities
- **Performance**: Strategic indexes on high-frequency queries
- **Validation**: CHECK constraints on enums and value ranges
- **Flexibility**: Extensible with tags and notes fields

---

## Database Statistics

```
Total Tables:        13
Foreign Keys:        10 relationships
Indexes:             15+ (user-created)
Triggers:            6+ (auto-update)
CHECK Constraints:   20+ validation rules
```

---

## Entity Relationship Diagram

```
┌─────────────┐
│   sources   │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────┐         ┌──────────────┐
│  screenshots    │────N:M──│  vocabulary  │
└─────────────────┘         └──────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                  1:N            1:N            N:M
                    │              │              │
            ┌───────▼────┐  ┌──────▼────────┐  ┌─▼─────┐
            │ flashcards │  │ example_      │  │ kanji │
            │            │  │ sentences     │  │       │
            └──────┬─────┘  └───────────────┘  └───────┘
                   │
                 1:N
                   │
         ┌─────────▼──────────┐
         │  review_sessions   │
         └────────────────────┘

┌─────────┐         ┌──────────────┐
│  tags   │───N:M───│  vocabulary  │
└─────────┘         └──────────────┘

┌─────────────────┐
│  study_goals    │
└─────────────────┘
```

---

## Core Entities

### 1. vocabulary

**Purpose**: Central repository for Japanese vocabulary words with comprehensive metadata.

**Schema**:
```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY,
    kanji_form TEXT NOT NULL,
    hiragana_reading TEXT NOT NULL,
    romaji_reading TEXT,
    english_meaning TEXT NOT NULL,
    part_of_speech TEXT,
    jlpt_level TEXT CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1', NULL)),
    frequency_rank INTEGER,
    word_type TEXT,
    tags TEXT,  -- Legacy field, use vocabulary_tags table instead
    notes TEXT,
    audio_url TEXT,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    study_status TEXT DEFAULT 'new' CHECK(study_status IN 
        ('new', 'learning', 'reviewing', 'mastered', 'suspended')),
    encounter_count INTEGER DEFAULT 1 CHECK(encounter_count >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields**:
- `kanji_form`: Primary display form (can be hiragana only for kana words)
- `hiragana_reading`: Reading in hiragana (furigana)
- `study_status`: Current learning state in the spaced repetition system
- `encounter_count`: How many times the word has been seen in content
- `frequency_rank`: Word frequency in Japanese (lower = more common)

**Business Rules**:
- New words start with `study_status = 'new'`
- `encounter_count` increments when word appears in new screenshots
- `last_seen_at` updates when word is encountered or reviewed
- JLPT level indicates difficulty (N5 easiest, N1 hardest)

**Indexes**:
- `idx_vocabulary_kanji_form` - Fast lookups by word
- `idx_vocabulary_study_status` - Filter by learning status
- `idx_vocabulary_jlpt_level` - Filter by difficulty
- `idx_vocabulary_last_seen_at` - Recently seen words

---

### 2. kanji

**Purpose**: Individual kanji character database with readings and metadata.

**Schema**:
```sql
CREATE TABLE kanji (
    id INTEGER PRIMARY KEY,
    character TEXT NOT NULL UNIQUE,
    meaning TEXT,
    on_readings TEXT,  -- Comma-separated list
    kun_readings TEXT, -- Comma-separated list
    stroke_count INTEGER CHECK(stroke_count > 0 AND stroke_count <= 30),
    jlpt_level TEXT CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1', NULL)),
    frequency_rank INTEGER CHECK(frequency_rank > 0),
    grade INTEGER CHECK(grade BETWEEN 1 AND 8 OR grade IS NULL),
    radical TEXT,
    radical_number INTEGER CHECK(radical_number BETWEEN 1 AND 214),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields**:
- `character`: Single kanji character (UNIQUE)
- `on_readings`: Chinese-derived readings (音読み)
- `kun_readings`: Japanese readings (訓読み)
- `grade`: Japanese school grade level (1-6 = kyōiku, 8 = jōyō)
- `radical_number`: Kangxi radical number (1-214)

**Business Rules**:
- Each kanji appears only once (UNIQUE constraint)
- Grade 1-6 are elementary school kanji (教育漢字)
- Grade 8 represents jōyō kanji not taught in elementary
- Stroke count typically ranges 1-30

**Indexes**:
- `idx_kanji_character` - Fast lookup by character
- `idx_kanji_jlpt_level` - Filter by level

---

### 3. sources

**Purpose**: Track learning materials and content sources.

**Schema**:
```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('manga', 'anime', 'visual_novel', 
        'light_novel', 'textbook', 'website', 'video', 'other', NULL)),
    genre TEXT,
    difficulty_level TEXT CHECK(difficulty_level IN 
        ('beginner', 'intermediate', 'advanced', 'native', NULL)),
    jlpt_target TEXT CHECK(jlpt_target IN ('N5', 'N4', 'N3', 'N2', 'N1', NULL)),
    notes TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields**:
- `type`: Media type for categorization
- `difficulty_level`: User's assessment of content difficulty
- `jlpt_target`: Which JLPT level this content aligns with
- `is_active`: Whether user is currently studying this source

**Business Rules**:
- `last_accessed_at` updates when screenshots from source are processed
- `is_active = 0` hides source from active content list
- Multiple screenshots can reference the same source

**Indexes**:
- `idx_sources_is_active` - Filter active sources
- `idx_sources_name` - Lookup by name

---

## Learning System

### 4. flashcards

**Purpose**: Implements spaced repetition algorithm (SM-2 based) for vocabulary learning.

**Schema**:
```sql
CREATE TABLE flashcards (
    id INTEGER PRIMARY KEY,
    vocabulary_id INTEGER NOT NULL,
    screenshot_id INTEGER,
    card_type TEXT DEFAULT 'recognition' CHECK(card_type IN 
        ('recognition', 'recall', 'production', 'listening')),
    status TEXT DEFAULT 'active' CHECK(status IN 
        ('active', 'suspended', 'buried', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP NOT NULL,
    ease_factor REAL DEFAULT 2.5 CHECK(ease_factor >= 1.3),
    interval_days REAL DEFAULT 0.0 CHECK(interval_days >= 0),
    review_count INTEGER DEFAULT 0 CHECK(review_count >= 0),
    consecutive_correct INTEGER DEFAULT 0 CHECK(consecutive_correct >= 0),
    lapses INTEGER DEFAULT 0 CHECK(lapses >= 0),
    difficulty_rating INTEGER CHECK(difficulty_rating BETWEEN 1 AND 5),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE SET NULL
);
```

**Card Types**:
- `recognition`: Japanese → English (easiest)
- `recall`: English → Japanese reading
- `production`: English → Japanese writing
- `listening`: Audio → Meaning/Reading

**Status Values**:
- `active`: Normal review cycle
- `suspended`: User-paused, not shown
- `buried`: Temporarily hidden (same-day siblings)
- `archived`: Mastered, very long intervals

**SM-2 Algorithm Fields**:
- `ease_factor`: Multiplier for interval growth (default 2.5)
- `interval_days`: Days until next review
- `consecutive_correct`: Streak counter (resets on failure)
- `lapses`: Number of times forgotten after being learned

**Business Rules**:
- New cards: `interval_days = 0`, shown immediately
- Correct answer: Increase `interval_days` by `ease_factor`
- Wrong answer: Reset `interval_days`, increase `lapses`
- `ease_factor` adjusts based on performance (min 1.3)
- Due cards: `next_review_at <= CURRENT_TIMESTAMP AND status = 'active'`

**Indexes**:
- `idx_flashcards_next_review_at` - Find due cards
- `idx_flashcards_status` - Filter by status
- `idx_flashcards_vocabulary_id` - Cards per vocabulary
- `idx_flashcards_status_next_review` - Composite for due queries

---

### 5. review_sessions

**Purpose**: Detailed history of every flashcard review for analytics and algorithm adjustment.

**Schema**:
```sql
CREATE TABLE review_sessions (
    id INTEGER PRIMARY KEY,
    flashcard_id INTEGER NOT NULL,
    session_id TEXT,  -- Groups reviews in same study session
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_rating INTEGER NOT NULL CHECK(quality_rating BETWEEN 0 AND 5),
    user_answer TEXT,
    correct BOOLEAN NOT NULL,
    response_time_ms INTEGER CHECK(response_time_ms >= 0),
    interval_before_days REAL,
    ease_factor_before REAL,
    ease_factor_after REAL,
    FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
);
```

**Quality Ratings** (0-5 scale):
- `0`: Complete blackout, no recognition
- `1`: Incorrect, but familiar
- `2`: Incorrect, but close
- `3`: Correct with difficulty
- `4`: Correct with hesitation
- `5`: Perfect recall

**Key Fields**:
- `session_id`: Groups reviews from same study session (UUID or timestamp)
- `user_answer`: Actual input for production cards
- `response_time_ms`: Time taken to answer
- `interval_before_days`: Interval before this review (for analytics)
- `ease_factor_before/after`: Track algorithm adjustments

**Business Rules**:
- Record created after every flashcard review
- `correct` determined by quality_rating (≥3 = correct)
- Used for statistics, graphs, and algorithm tuning
- Never deleted (historical data)

**Indexes**:
- `idx_review_sessions_flashcard_id` - Reviews per card
- `idx_review_sessions_session_id` - Group by study session
- `idx_review_sessions_reviewed_at` - Time-based queries

---

### 6. study_goals

**Purpose**: User-defined learning objectives with progress tracking.

**Schema**:
```sql
CREATE TABLE study_goals (
    id INTEGER PRIMARY KEY,
    goal_type TEXT NOT NULL CHECK(goal_type IN ('daily_reviews', 
        'weekly_reviews', 'new_vocabulary', 'vocabulary_mastered', 
        'reading_time', 'custom')),
    target_value INTEGER NOT NULL CHECK(target_value > 0),
    current_value INTEGER DEFAULT 0 CHECK(current_value >= 0),
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(end_date IS NULL OR end_date >= start_date)
);
```

**Goal Types**:
- `daily_reviews`: Number of reviews per day
- `weekly_reviews`: Reviews per week
- `new_vocabulary`: New words learned
- `vocabulary_mastered`: Words reached mastery
- `reading_time`: Minutes spent reading
- `custom`: User-defined goals

**Business Rules**:
- `target_value`: Goal amount (e.g., 50 reviews)
- `current_value`: Progress toward goal
- Date range defines goal period
- `is_active = 0` archives completed/abandoned goals
- Multiple active goals allowed

**Indexes**:
- `idx_study_goals_is_active` - Active goals only

---

## Content Management

### 7. screenshots

**Purpose**: Stores OCR-processed screenshot data with extracted text.

**Schema**:
```sql
CREATE TABLE screenshots (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    source_id INTEGER,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ocr_confidence REAL NOT NULL,
    extracted_text_json TEXT NOT NULL,  -- JSON array of text blocks
    checksum TEXT,  -- MD5/SHA256 for duplicate detection
    language_detected TEXT DEFAULT 'ja',
    has_furigana BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
);
```

**Key Fields**:
- `file_path`: Relative or absolute path to image file
- `extracted_text_json`: JSON with OCR results (text, coordinates, confidence)
- `ocr_confidence`: Average confidence across all detected text (0.0-1.0)
- `checksum`: Hash of image for duplicate prevention
- `has_furigana`: Detected furigana reading above kanji

**JSON Structure** (`extracted_text_json`):
```json
[
  {
    "text": "日本語",
    "reading": "にほんご",
    "bbox": [x, y, width, height],
    "confidence": 0.95
  }
]
```

**Business Rules**:
- OCR processing creates screenshot record
- Duplicate detection via checksum
- Vocabulary extracted and linked via `screenshot_vocabulary`
- Links to source for content tracking

**Indexes**:
- `idx_screenshots_source_id` - Screenshots per source
- `idx_screenshots_checksum` - Duplicate detection
- `idx_screenshots_processed_at` - Chronological order

---

### 8. example_sentences

**Purpose**: Contextual usage examples for vocabulary with translations.

**Schema**:
```sql
CREATE TABLE example_sentences (
    id INTEGER PRIMARY KEY,
    vocabulary_id INTEGER NOT NULL,
    japanese_text TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    source_id INTEGER,
    difficulty_level TEXT,
    has_audio BOOLEAN DEFAULT 0,
    audio_url TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
);
```

**Key Fields**:
- `japanese_text`: Full sentence in Japanese
- `english_translation`: English translation
- `source_id`: Optional link to where sentence came from
- `audio_url`: Link to pronunciation audio

**Business Rules**:
- Multiple sentences per vocabulary word
- Can be user-added or extracted from sources
- Audio enhances listening comprehension
- Deleted when vocabulary is deleted (CASCADE)

**Indexes**:
- `idx_example_sentences_vocabulary_id` - Sentences per word
- `idx_example_sentences_source_id` - Sentences per source

---

## Relationship Tables

### 9. screenshot_vocabulary

**Purpose**: Junction table linking screenshots to extracted vocabulary.

**Schema**:
```sql
CREATE TABLE screenshot_vocabulary (
    id INTEGER PRIMARY KEY,
    screenshot_id INTEGER NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    position_in_text INTEGER,
    context_snippet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
);
```

**Key Fields**:
- `position_in_text`: Word order in original text
- `context_snippet`: Surrounding text for context

**Business Rules**:
- Created during OCR processing
- Tracks where vocabulary was encountered
- Enables "words in context" features
- Both deletes cascade (data integrity)

**Indexes**:
- `idx_screenshot_vocabulary_screenshot_id` - Words per screenshot
- `idx_screenshot_vocabulary_vocabulary_id` - Screenshots per word

---

### 10. vocabulary_kanji

**Purpose**: Links vocabulary words to their constituent kanji characters.

**Schema**:
```sql
CREATE TABLE vocabulary_kanji (
    vocabulary_id INTEGER NOT NULL,
    kanji_id INTEGER NOT NULL,
    position INTEGER,  -- Order within the word
    PRIMARY KEY (vocabulary_id, kanji_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (kanji_id) REFERENCES kanji(id) ON DELETE CASCADE
);
```

**Key Fields**:
- `position`: 0-indexed position of kanji in word

**Business Rules**:
- Composite primary key (vocabulary_id, kanji_id)
- Enables kanji-based vocabulary search
- Position preserves kanji order
- Both deletes cascade

**Indexes**:
- `idx_vocabulary_kanji_vocabulary_id` - Kanji per word
- `idx_vocabulary_kanji_kanji_id` - Words containing kanji

---

### 11. tags / vocabulary_tags

**Purpose**: Normalized tag system for flexible categorization.

**Schema**:
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT,  -- E.g., "grammar", "topic", "difficulty"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vocabulary_tags (
    vocabulary_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (vocabulary_id, tag_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

**Key Fields**:
- `tags.name`: Tag display name (UNIQUE)
- `tags.category`: Optional grouping (e.g., "grammar-point", "topic")
- Many-to-many relationship via junction table

**Business Rules**:
- Tags are reusable across vocabulary
- UNIQUE ensures no duplicate tag names
- Category enables tag organization
- Replaces legacy TEXT field in vocabulary table

**Indexes**:
- `idx_vocabulary_tags_vocabulary_id` - Tags per word
- `idx_vocabulary_tags_tag_id` - Words per tag

---

## Utility Tables

### 12. _migration_backup

**Purpose**: Database versioning and migration tracking.

**Schema**:
```sql
CREATE TABLE _migration_backup (
    id INTEGER PRIMARY KEY,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version TEXT
);
```

**Business Rules**:
- Records each schema migration
- Version string describes changes
- Never deleted (audit trail)
- Used for rollback reference

---

## Indexes and Performance

### Critical Query Patterns

**1. Due Flashcards Query**
```sql
SELECT * FROM flashcards 
WHERE status = 'active' 
  AND next_review_at <= datetime('now')
ORDER BY next_review_at;
```
**Index**: `idx_flashcards_status_next_review` (composite)

**2. Vocabulary Lookup**
```sql
SELECT * FROM vocabulary WHERE kanji_form = '日本語';
```
**Index**: `idx_vocabulary_kanji_form`

**3. Study Status Filter**
```sql
SELECT * FROM vocabulary WHERE study_status = 'learning';
```
**Index**: `idx_vocabulary_study_status`

**4. Screenshot Vocabulary Extraction**
```sql
SELECT v.* FROM vocabulary v
JOIN screenshot_vocabulary sv ON v.id = sv.vocabulary_id
WHERE sv.screenshot_id = ?;
```
**Indexes**: Both foreign key indexes used

### Index Maintenance

- **ANALYZE**: Run after bulk imports (updates query planner statistics)
- **VACUUM**: Monthly to reclaim space and defragment
- Index coverage: 15+ user-created indexes
- Auto-indexes: SQLite creates for PRIMARY KEY and UNIQUE

---

## Constraints and Validation

### CHECK Constraints

**JLPT Levels** (5 tables):
```sql
CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1', NULL))
```

**Study Status** (vocabulary):
```sql
CHECK(study_status IN ('new', 'learning', 'reviewing', 'mastered', 'suspended'))
```

**Card Types** (flashcards):
```sql
CHECK(card_type IN ('recognition', 'recall', 'production', 'listening'))
```

**Quality Ratings** (review_sessions):
```sql
CHECK(quality_rating BETWEEN 0 AND 5)
```

**Value Ranges**:
- `ease_factor >= 1.3` - SM-2 algorithm minimum
- `interval_days >= 0` - No negative intervals
- `stroke_count > 0 AND <= 30` - Reasonable kanji strokes
- `encounter_count >= 0` - Counter minimum
- `target_value > 0` - Goals must be positive

### Foreign Key Actions

**CASCADE Deletes**:
- vocabulary → flashcards
- vocabulary → example_sentences
- flashcards → review_sessions
- screenshots → screenshot_vocabulary
- All junction tables

**SET NULL Deletes**:
- sources → screenshots (preserve screenshot if source deleted)
- sources → example_sentences (preserve sentence)
- flashcards.screenshot_id (optional reference)

---

## Triggers and Automation

### Automatic Timestamp Updates

**Pattern**:
```sql
CREATE TRIGGER update_[table]_timestamp 
AFTER UPDATE ON [table]
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE [table] SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

**Applied To**:
- sources
- screenshots
- vocabulary
- flashcards
- kanji
- study_goals

### Application-Level Triggers

**Not in Database** (implement in application code):
- Increment `vocabulary.encounter_count` on new screenshot match
- Update `vocabulary.last_seen_at` on screenshot or review
- Update `sources.last_accessed_at` on new screenshot
- Increment `study_goals.current_value` on review completion
- Create flashcard automatically on vocabulary creation

---

## Performance Optimization

### Query Optimization Tips

1. **Always enable foreign keys per session**:
   ```sql
   PRAGMA foreign_keys = ON;
   ```

2. **Use prepared statements**:
   ```python
   cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (vocab_id,))
   ```

3. **Batch inserts in transactions**:
   ```python
   with conn:
       conn.executemany("INSERT INTO ...", data)
   ```

4. **Limit result sets**:
   ```sql
   SELECT * FROM flashcards 
   WHERE status = 'active' 
   LIMIT 20;
   ```

### Maintenance Schedule

- **Daily**: None required
- **Weekly**: Check database size
- **Monthly**: `VACUUM` and `ANALYZE`
- **After bulk imports**: `ANALYZE`
- **After schema changes**: Verify foreign keys with `PRAGMA foreign_key_check`

---

## Connection Configuration

### Required PRAGMAs

```sql
PRAGMA foreign_keys = ON;          -- Enable FK constraints
PRAGMA journal_mode = WAL;         -- Write-Ahead Logging (recommended)
PRAGMA synchronous = NORMAL;       -- Balance safety/performance
PRAGMA cache_size = -2000;         -- 2MB cache
PRAGMA temp_store = MEMORY;        -- Faster temp operations
```

### Python Example

```python
import sqlite3

conn = sqlite3.connect('data/japanese_agent.db')
conn.execute('PRAGMA foreign_keys = ON')
conn.execute('PRAGMA journal_mode = WAL')
conn.row_factory = sqlite3.Row  # Dict-like access
```

### Node.js Example

```typescript
import Database from 'better-sqlite3';

const db = new Database('data/japanese_agent.db');
db.pragma('foreign_keys = ON');
db.pragma('journal_mode = WAL');
```

---

## Migration History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Base schema with 11 tables |
| 2.0 | 2025-10-22 | Added FK constraints, CHECK constraints, indexes, updated_at columns, tags normalization |
| 2.0.1 | 2025-10-22 | Cleanup and optimization |

---

## Appendix: Data Types

### SQLite Type Affinity

- **INTEGER**: Whole numbers, dates (Unix timestamp)
- **REAL**: Floating point (ease_factor, ocr_confidence)
- **TEXT**: Strings, JSON, ISO8601 dates
- **BLOB**: Binary data (not used in this schema)
- **NULL**: Absence of value

### Timestamp Format

All timestamps use ISO 8601 format:
```
2025-10-22 14:30:00
```

Generated with:
```sql
CURRENT_TIMESTAMP
datetime('now')
```

---

**End of Schema Reference**

For UI/UX guidelines, see: `UI_UX_DESIGN_GUIDE.md`  
For user workflows, see: `USER_WORKFLOWS.md`  
For API integration, see: `API_INTEGRATION_GUIDE.md`
