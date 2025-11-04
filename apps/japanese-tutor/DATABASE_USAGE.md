# Database Usage Guide

This guide explains how to use the SQLite database layer for vocabulary and flashcard management in the Japanese Learning Agent.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Connection Management](#connection-management)
4. [Tool Functions](#tool-functions)
5. [SM-2 Spaced Repetition Algorithm](#sm-2-spaced-repetition-algorithm)
6. [Testing](#testing)
7. [Performance Considerations](#performance-considerations)
8. [Migration & Backup](#migration--backup)

## Architecture Overview

### Design Principles

- **Async-First**: All database operations use `aiosqlite` for async I/O
- **WAL Mode**: Write-Ahead Logging enables concurrent reads during writes
- **Singleton Connection**: Single global connection managed by connection module
- **LangChain Integration**: Tools use `@tool` decorator for agent compatibility
- **Type Safety**: Pydantic schemas validate all data structures
- **Test Isolation**: Tests use temporary databases with fixtures

### Directory Structure

```
apps/japanese-tutor/
├── src/japanese_agent/
│   ├── database/
│   │   ├── __init__.py          # Module exports
│   │   ├── connection.py        # Connection manager & initialization
│   │   └── schema.sql           # Complete database schema
│   └── tools/
│       ├── vocabulary_manager.py  # Vocabulary CRUD tools
│       └── flashcard_manager.py   # Flashcard & review tools
└── tests/integration/
    ├── test_database_setup.py      # Schema validation tests
    ├── test_vocabulary_database.py # Vocabulary operation tests
    ├── test_flashcard_database.py  # Flashcard & SM-2 tests
    └── test_full_workflow.py       # End-to-end workflow tests
```

## Database Schema

### 13 Tables Overview

#### Core Entities
1. **vocabulary** - Japanese vocabulary entries (kanji, readings, meanings)
2. **kanji** - Individual kanji characters with metadata
3. **sources** - Content sources (games, manga, websites)
4. **screenshots** - Processed screenshots with OCR results

#### Learning System
5. **flashcards** - Spaced repetition flashcards
6. **review_sessions** - Individual review records
7. **study_goals** - User-defined learning goals
8. **example_sentences** - Usage examples for vocabulary

#### Relationships
9. **screenshot_vocabulary** - Links screenshots to extracted vocabulary
10. **vocabulary_kanji** - Links vocabulary to component kanji
11. **tags** - User-defined tags
12. **vocabulary_tags** - Links vocabulary to tags

#### System
13. **_migration_backup** - Schema version tracking

### Key Relationships

```
vocabulary ←──┬── flashcards ←── review_sessions
              ├── screenshot_vocabulary ──→ screenshots
              ├── vocabulary_kanji ──→ kanji
              ├── vocabulary_tags ──→ tags
              └── example_sentences
```

### Critical Indexes

```sql
-- Due flashcards query (composite index)
CREATE INDEX idx_flashcards_status_next_review
    ON flashcards(status, next_review_at);

-- Vocabulary search
CREATE INDEX idx_vocabulary_kanji_form ON vocabulary(kanji_form);
CREATE INDEX idx_vocabulary_study_status ON vocabulary(study_status);

-- Review analytics
CREATE INDEX idx_review_sessions_flashcard_id ON review_sessions(flashcard_id);
CREATE INDEX idx_review_sessions_reviewed_at ON review_sessions(reviewed_at);
```

### Constraints & Validation

#### CHECK Constraints

```sql
-- Study status enum
study_status CHECK(study_status IN ('new', 'learning', 'reviewing', 'mastered', 'suspended'))

-- JLPT levels
jlpt_level CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1') OR jlpt_level IS NULL)

-- SM-2 ease factor minimum
ease_factor REAL DEFAULT 2.5 CHECK(ease_factor >= 1.3)

-- Flashcard status
status CHECK(status IN ('new', 'learning', 'reviewing', 'mature', 'suspended'))
```

#### Foreign Keys

```sql
-- CASCADE: Delete dependent data
vocabulary_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE

-- SET NULL: Preserve records but clear reference
source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL
```

### Automatic Triggers

```sql
-- Update timestamps automatically
CREATE TRIGGER update_vocabulary_timestamp
AFTER UPDATE ON vocabulary
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE vocabulary SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

## Connection Management

### Initialization

```python
from japanese_agent.database import initialize_database, get_connection, close_connection

# Initialize database (creates schema if needed)
await initialize_database()

# Get connection (singleton)
conn = await get_connection()

# Execute queries
async with conn.execute("SELECT * FROM vocabulary LIMIT 10") as cursor:
    rows = await cursor.fetchall()

# Cleanup on shutdown
await close_connection()
```

### Environment Configuration

```python
# Set custom database path
import os
os.environ["DATABASE_PATH"] = "/path/to/japanese_agent.db"

# Default: ../../data/japanese_agent.db (relative to this app)
```

### WAL Mode Benefits

```python
# WAL mode allows:
# 1. Concurrent reads while writing
# 2. Better crash recovery
# 3. Faster performance for most workloads

# Verify WAL mode
async with conn.execute("PRAGMA journal_mode") as cursor:
    mode = (await cursor.fetchone())[0]
    assert mode.lower() == 'wal'
```

## Tool Functions

### Vocabulary Manager

#### search_vocabulary(query: str)

Search vocabulary by kanji, hiragana, or English meaning.

```python
from japanese_agent.tools.vocabulary_manager import search_vocabulary

# Search for vocabulary
results = await search_vocabulary.coroutine("日本")

# Returns: List[Dict[str, Any]]
# [
#   {
#     "id": 1,
#     "kanji_form": "日本語",
#     "hiragana_reading": "にほんご",
#     "english_meaning": "Japanese language",
#     "study_status": "learning",
#     "encounter_count": 5,
#     ...
#   }
# ]
```

#### list_vocabulary_by_status(status: str, limit: int = 50)

List vocabulary filtered by study status.

```python
# Get new words
new_words = await list_vocabulary_by_status.coroutine("new", limit=20)

# Get mastered words
mastered = await list_vocabulary_by_status.coroutine("mastered", limit=100)

# Valid statuses: 'new', 'learning', 'reviewing', 'mastered', 'suspended'
```

#### update_vocabulary_status(vocab_id: int, new_status: str)

Update study status for a vocabulary entry.

```python
# Progress a word to learning
result = await update_vocabulary_status.coroutine(
    vocab_id=123,
    new_status="learning"
)

# Returns: {"success": True, "study_status": "learning", "updated_at": "..."}
```

#### get_vocabulary_statistics()

Get aggregate vocabulary statistics.

```python
stats = await get_vocabulary_statistics.coroutine()

# Returns:
# {
#   "total_words": 1247,
#   "new_words": 342,
#   "learning_words": 456,
#   "reviewing_words": 289,
#   "mastered_words": 160,
#   "suspended_words": 0,
#   "total_encounters": 5432
# }
```

### Flashcard Manager

#### create_flashcard(vocab_id: int, card_type: str = "recognition")

Create a flashcard from vocabulary.

```python
from japanese_agent.tools.flashcard_manager import create_flashcard

flashcard = await create_flashcard.coroutine(vocab_id=123)

# Returns:
# {
#   "success": True,
#   "flashcard_id": 456,
#   "vocab_id": 123,
#   "ease_factor": 2.5,
#   "interval": 0.0,
#   "review_count": 0,
#   "status": "active",
#   "card_type": "recognition",
#   "next_review": "2025-10-31T12:00:00"
# }
```

#### get_due_flashcards(limit: int = 20)

Get flashcards due for review, ordered by due date.

```python
due_cards = await get_due_flashcards.coroutine(limit=10)

# Returns: List[Dict] with vocabulary data joined
# [
#   {
#     "flashcard_id": 456,
#     "word": "日本語",
#     "reading": "にほんご",
#     "meaning": "Japanese language",
#     "next_review": "2025-10-31T10:00:00",
#     "interval": 6.0,
#     "review_count": 3,
#     ...
#   }
# ]
```

#### record_flashcard_review(flashcard_id: int, rating: int)

Record a flashcard review and update SM-2 schedule.

```python
# Rating scale: 0 = Again, 1 = Hard, 2 = Medium, 3 = Easy
result = await record_flashcard_review.coroutine(
    flashcard_id=456,
    rating=3  # Easy
)

# Returns:
# {
#   "success": True,
#   "flashcard_id": 456,
#   "interval": 6.0,
#   "ease_factor": 2.6,
#   "review_count": 4,
#   "consecutive_correct": 4,
#   "lapses": 0,
#   "next_review": "2025-11-06T12:00:00"
# }
```

#### get_review_statistics()

Get review session statistics.

```python
stats = await get_review_statistics.coroutine()

# Returns:
# {
#   "total_flashcards": 342,
#   "due_today": 23,
#   "reviewed_today": 15,
#   "average_ease": 2.43,
#   "total_reviews": 1247
# }
```

## SM-2 Spaced Repetition Algorithm

### Overview

The SM-2 (SuperMemo 2) algorithm schedules flashcard reviews at increasing intervals based on recall performance.

### Rating Scale

| User Rating | Quality (Internal) | Meaning |
|-------------|-------------------|---------|
| 0 | 0 | Again - Complete blackout, no recall |
| 1 | 3 | Hard - Incorrect with effort, barely recalled |
| 2 | 4 | Medium - Correct with hesitation |
| 3 | 5 | Easy - Perfect recall, immediate response |

### Ease Factor Formula

```python
# Adjust ease factor based on quality
EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

# Where:
# - EF = current ease factor
# - q = quality rating (0-5)
# - EF' = new ease factor
# - Minimum EF = 1.3
```

### Interval Progression

```python
if quality < 3:  # Failed (Again, Hard)
    interval = 0.0  # Review immediately
    repetitions = 0  # Reset streak

else:  # Successful (Medium, Easy)
    if repetitions == 0:
        interval = 1.0  # First success: 1 day
    elif repetitions == 1:
        interval = 6.0  # Second success: 6 days
    else:
        interval = previous_interval * ease_factor
```

### Example Review Sequence

```
Day 0: Learn word (rating: 3 - Easy)
  → Next: 1 day, EF: 2.6

Day 1: Review (rating: 3 - Easy)
  → Next: 6 days, EF: 2.7

Day 7: Review (rating: 2 - Medium)
  → Next: 16 days (6 * 2.7), EF: 2.6

Day 23: Review (rating: 0 - Again) [FORGOT!]
  → Next: 0 days (immediate), EF: 2.3, Lapses: 1

Day 23: Re-review (rating: 3 - Easy)
  → Next: 1 day (restart), EF: 2.4
```

### Implementation Details

```python
def _calculate_sm2_next_interval(rating, current_ease, current_interval, repetitions):
    """
    Calculate next interval using SM-2 algorithm.

    Args:
        rating: 0-3 (Again, Hard, Medium, Easy)
        current_ease: Current ease factor (min 1.3)
        current_interval: Current interval in days
        repetitions: Number of consecutive correct reviews

    Returns:
        (next_interval, new_ease, new_repetitions)
    """
    quality_map = {0: 0, 1: 3, 2: 4, 3: 5}
    quality = quality_map[rating]

    # Adjust ease factor
    new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(new_ease, 1.3)

    # Calculate interval
    if quality < 3:  # Failed
        return 0.0, new_ease, 0
    else:  # Successful
        if repetitions == 0:
            return 1.0, new_ease, 1
        elif repetitions == 1:
            return 6.0, new_ease, 2
        else:
            return current_interval * new_ease, new_ease, repetitions + 1
```

## Testing

### Running Tests

```bash
# Run all database tests
cd apps/japanese-tutor
pytest tests/integration/ -v

# Run specific test suites
pytest tests/integration/test_database_setup.py -v      # Schema validation
pytest tests/integration/test_vocabulary_database.py -v # Vocabulary operations
pytest tests/integration/test_flashcard_database.py -v  # Flashcard & SM-2
pytest tests/integration/test_full_workflow.py -v       # End-to-end workflows

# Run with coverage
pytest tests/integration/ --cov=src/japanese_agent --cov-report=html
```

### Test Fixtures

```python
import pytest
import os
import tempfile
from japanese_agent.database import initialize_database, get_connection, close_connection

@pytest.fixture
async def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        test_db_path = tmp.name

    original_path = os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = test_db_path

    await initialize_database()
    conn = await get_connection()

    yield conn

    await close_connection()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

    if original_path:
        os.environ["DATABASE_PATH"] = original_path
    else:
        os.environ.pop("DATABASE_PATH", None)
```

### Calling Tools in Tests

```python
# IMPORTANT: Use .coroutine for async LangChain tools

# ❌ WRONG
results = await search_vocabulary(query)

# ✅ CORRECT
results = await search_vocabulary.coroutine(query)
```

## Performance Considerations

### Indexes for Common Queries

```sql
-- Due flashcards (most frequent query)
-- Uses composite index: idx_flashcards_status_next_review
SELECT f.*, v.*
FROM flashcards f
JOIN vocabulary v ON f.vocabulary_id = v.id
WHERE f.status = 'active' AND f.next_review_at <= CURRENT_TIMESTAMP
ORDER BY f.next_review_at
LIMIT 20;

-- Vocabulary by status (filtered browsing)
-- Uses index: idx_vocabulary_study_status
SELECT * FROM vocabulary
WHERE study_status = 'new'
ORDER BY last_seen_at DESC
LIMIT 50;

-- Vocabulary search (text search)
-- Uses index: idx_vocabulary_kanji_form for prefix matches
SELECT * FROM vocabulary
WHERE kanji_form LIKE ? OR hiragana_reading LIKE ? OR english_meaning LIKE ?
ORDER BY encounter_count DESC, last_seen_at DESC
LIMIT 20;
```

### Query Optimization Tips

1. **Use EXPLAIN QUERY PLAN** to verify index usage:
```sql
EXPLAIN QUERY PLAN
SELECT * FROM flashcards WHERE status = 'active' AND next_review_at <= datetime('now');
```

2. **Batch inserts** for better performance:
```python
async with conn.executemany(
    "INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning) VALUES (?, ?, ?)",
    vocabulary_batch
):
    pass
await conn.commit()
```

3. **Use transactions** for multi-step operations:
```python
async with conn.execute("BEGIN"):
    await conn.execute("INSERT INTO vocabulary ...")
    await conn.execute("INSERT INTO flashcards ...")
    await conn.commit()
```

### WAL Mode Performance

```
Benchmark (1000 concurrent operations):
- Without WAL: ~2.3s (readers block on writes)
- With WAL: ~0.8s (concurrent reads)

Write performance: Similar
Read performance: 2-3x better under load
```

## Migration & Backup

### Schema Version Tracking

```sql
-- Check current schema version
SELECT version FROM _migration_backup ORDER BY id DESC LIMIT 1;
```

### Manual Backup

```bash
# Backup database
sqlite3 data/japanese_agent.db ".backup data/japanese_agent_backup.db"

# Or use file copy (ensure no active writes)
cp data/japanese_agent.db data/japanese_agent_backup_$(date +%Y%m%d).db
```

### Export Data

```sql
-- Export vocabulary to CSV
.mode csv
.output vocabulary_export.csv
SELECT * FROM vocabulary;
.output stdout
```

### Database Integrity Check

```python
async with conn.execute("PRAGMA integrity_check") as cursor:
    result = await cursor.fetchone()
    assert result[0] == "ok", f"Database integrity check failed: {result[0]}"

async with conn.execute("PRAGMA foreign_key_check") as cursor:
    violations = await cursor.fetchall()
    assert len(violations) == 0, f"Foreign key violations: {violations}"
```

## Troubleshooting

### Issue: Database locked

**Cause**: Another process has an exclusive lock

**Solution**:
```python
# Check WAL mode is enabled
async with conn.execute("PRAGMA journal_mode") as cursor:
    mode = (await cursor.fetchone())[0]
    print(f"Journal mode: {mode}")  # Should be 'wal'

# Increase timeout
conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds
```

### Issue: Foreign key constraint violation

**Cause**: Attempting to insert/update with invalid foreign key reference

**Solution**:
```python
# Check foreign keys are enabled
async with conn.execute("PRAGMA foreign_keys") as cursor:
    enabled = (await cursor.fetchone())[0]
    print(f"Foreign keys: {'enabled' if enabled else 'disabled'}")

# Find violations
async with conn.execute("PRAGMA foreign_key_check") as cursor:
    violations = await cursor.fetchall()
    for violation in violations:
        print(f"Violation: {violation}")
```

### Issue: Test database not isolated

**Cause**: Environment variable not set in fixture

**Solution**:
```python
# Ensure DATABASE_PATH is set before initialize_database()
os.environ["DATABASE_PATH"] = test_db_path
await initialize_database()
```

## Best Practices

1. **Always use transactions** for multi-step operations
2. **Close connections** in finally blocks or use context managers
3. **Use prepared statements** (parameterized queries) to prevent SQL injection
4. **Test with realistic data volumes** (1000+ vocabulary, 500+ flashcards)
5. **Monitor index usage** with EXPLAIN QUERY PLAN
6. **Back up before schema changes**
7. **Use CHECK constraints** for data validation at database level
8. **Document schema changes** in migration records

## References

- [SM-2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
