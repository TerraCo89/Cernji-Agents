# Data Flow & Quick Reference Guide
**Japanese Learning Application - Visual System Overview**

Version: 1.0  
Last Updated: 2025-10-22  
Target Audience: All stakeholders (technical and non-technical)

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [State Diagrams](#state-diagrams)
5. [Quick Reference Tables](#quick-reference-tables)
6. [Common Query Patterns](#common-query-patterns)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Dashboard │  │ Review   │  │Screenshot│  │Vocabulary│  │
│  │          │  │ Session  │  │ Import   │  │ Browser  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Logic Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Vocabulary   │  │  Flashcard   │  │ Screenshot   │     │
│  │  Service     │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Review    │  │     SRS      │  │     OCR      │     │
│  │   Manager    │  │  Algorithm   │  │  Processor   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Repository Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Vocabulary   │  │  Flashcard   │  │ Screenshot   │     │
│  │ Repository   │  │ Repository   │  │ Repository   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer (SQLite)                   │
│                                                              │
│  [vocabulary] [flashcards] [review_sessions] [screenshots]  │
│  [sources] [kanji] [tags] [study_goals] [...11 more...]    │
│                                                              │
│  Foreign Keys ✓  Indexes ✓  Triggers ✓  Constraints ✓     │
└─────────────────────────────────────────────────────────────┘
```

---

## Entity Relationship Diagram

### Complete ERD

```
                    ┌──────────────────┐
                    │     sources      │
                    │ ──────────────── │
                    │ id (PK)          │
                    │ name             │
                    │ type             │
                    │ difficulty_level │
                    │ jlpt_target      │
                    └────────┬─────────┘
                             │ 1:N
                             │
                    ┌────────▼─────────┐
                    │   screenshots    │◄───────┐
                    │ ──────────────── │        │
                    │ id (PK)          │        │ N:M via
                    │ source_id (FK)   │        │ screenshot_
                    │ file_path        │        │ vocabulary
                    │ ocr_confidence   │        │
                    │ checksum         │        │
                    └──────────────────┘        │
                                                │
┌──────────────────┐                   ┌────────┴─────────┐
│      kanji       │                   │   vocabulary     │
│ ──────────────── │                   │ ──────────────── │
│ id (PK)          │◄──────N:M────────►│ id (PK)          │
│ character (UQ)   │ via vocabulary_   │ kanji_form       │
│ meaning          │     kanji         │ hiragana_reading │
│ on_readings      │                   │ english_meaning  │
│ kun_readings     │                   │ study_status     │
│ stroke_count     │                   │ encounter_count  │
│ jlpt_level       │                   └────────┬─────────┘
└──────────────────┘                            │ 1:N
                                                │
                                       ┌────────┴─────────┐
                                       │   flashcards     │
                                       │ ──────────────── │
                                       │ id (PK)          │
                                       │ vocabulary_id(FK)│
                                       │ card_type        │
                                       │ status           │
                                       │ next_review_at   │
                                       │ ease_factor      │
                                       │ interval_days    │
                                       └────────┬─────────┘
                                                │ 1:N
                                                │
                                       ┌────────▼─────────┐
                                       │ review_sessions  │
                                       │ ──────────────── │
                                       │ id (PK)          │
                                       │ flashcard_id(FK) │
                                       │ quality_rating   │
                                       │ correct          │
                                       │ reviewed_at      │
                                       └──────────────────┘

┌──────────────────┐                   ┌──────────────────┐
│      tags        │                   │  study_goals     │
│ ──────────────── │                   │ ──────────────── │
│ id (PK)          │◄──────N:M────────►│ id (PK)          │
│ name (UQ)        │ via vocabulary_   │ goal_type        │
│ category         │     tags          │ target_value     │
└──────────────────┘                   │ current_value    │
        ▲                              │ is_active        │
        │ N:M                          └──────────────────┘
        │ via vocabulary_tags
        │
┌───────┴──────────┐
│   vocabulary     │
│ (from above)     │
└──────────────────┘

┌──────────────────┐
│ example_sentences│
│ ──────────────── │
│ id (PK)          │
│ vocabulary_id(FK)│──┐
│ japanese_text    │  │
│ english_trans... │  │
│ source_id (FK)   │  │
└──────────────────┘  │
                      │
                      └──► Links to vocabulary (1:N)
```

### Simplified Core ERD (Most Important Tables)

```
┌─────────┐       ┌─────────────┐       ┌──────────────┐
│ sources │──1:N──│ screenshots │──N:M──│  vocabulary  │
└─────────┘       └─────────────┘       └──────┬───────┘
                                               │ 1:N
                                               │
                                         ┌─────▼───────┐
                                         │ flashcards  │
                                         └──────┬──────┘
                                                │ 1:N
                                                │
                                         ┌──────▼────────┐
                                         │review_sessions│
                                         └───────────────┘
```

---

## Data Flow Diagrams

### 1. Screenshot Import Flow

```
┌───────┐
│ User  │
└───┬───┘
    │ 1. Upload Image
    ▼
┌─────────────────┐
│  Application    │
│  - Save file    │
│  - Calculate    │
│    checksum     │
└────────┬────────┘
         │ 2. Image + metadata
         ▼
┌─────────────────┐
│   OCR Service   │
│  - Detect text  │
│  - Extract      │
│    readings     │
│  - Confidence   │
└────────┬────────┘
         │ 3. OCR results
         ▼
┌─────────────────────────────────────┐
│      NLP / Tokenization             │
│  - Split into words                 │
│  - Identify vocabulary              │
│  - Extract context                  │
└────────┬────────────────────────────┘
         │ 4. Parsed words
         ▼
┌─────────────────────────────────────┐
│         Database Logic              │
│                                     │
│  For each word:                     │
│  ┌─────────────────────────────┐   │
│  │ Check if exists             │   │
│  │   SELECT FROM vocabulary    │   │
│  └─────────┬───────────────────┘   │
│            │                        │
│      ┌─────┴─────┐                 │
│      │           │                 │
│   Exists      New                  │
│      │           │                 │
│      ▼           ▼                 │
│  ┌─────┐    ┌──────┐              │
│  │UPDATE│    │INSERT│              │
│  │vocab │    │vocab │              │
│  └──┬──┘    └───┬──┘              │
│     │           │                  │
│     └─────┬─────┘                  │
│           │                        │
│           ▼                        │
│  ┌──────────────────────┐         │
│  │ INSERT screenshot_   │         │
│  │ vocabulary (link)    │         │
│  └──────────────────────┘         │
│                                    │
│  INSERT screenshot                 │
│  UPDATE source.last_accessed       │
└────────┬───────────────────────────┘
         │ 5. Results
         ▼
┌─────────────────┐
│  Application    │
│  - Display      │
│    results      │
│  - Show new     │
│    words        │
└────────┬────────┘
         │ 6. UI update
         ▼
┌───────────────────────┐
│      User sees:       │
│  • Extracted text     │
│  • Known words: 5     │
│  • New words: 3       │
│  • [Add All]  [Skip]  │
└───────────────────────┘
```

### 2. Review Session Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ 1. Open Review
     ▼
┌───────────────────────────────┐
│    Application                │
│    Query due flashcards       │
│                               │
│    SELECT f.*, v.*            │
│    FROM flashcards f          │
│    JOIN vocabulary v          │
│    WHERE status = 'active'    │
│      AND next_review_at <= NOW│
│    ORDER BY next_review_at    │
└────────┬──────────────────────┘
         │ 2. Due cards list
         ▼
┌───────────────────────────────┐
│         UI Layer              │
│  ┌─────────────────────────┐ │
│  │   Card Display          │ │
│  │   日本語                 │ │
│  │   [Show Answer]         │ │
│  └─────────────────────────┘ │
└────────┬──────────────────────┘
         │ 3. User taps
         ▼
┌───────────────────────────────┐
│         UI Layer              │
│  ┌─────────────────────────┐ │
│  │   Answer Revealed       │ │
│  │   にほんご               │ │
│  │   Japanese language     │ │
│  │                         │ │
│  │   [Again] [Hard]        │ │
│  │   [Good]  [Easy]        │ │
│  └─────────────────────────┘ │
└────────┬──────────────────────┘
         │ 4. User selects "Good" (3)
         ▼
┌───────────────────────────────┐
│    SRS Algorithm              │
│  - quality = 3 (correct)      │
│  - interval = 1d * 2.5 = 2.5d │
│  - ease_factor = 2.5 + ...    │
│  - next_review = NOW + 2.5d   │
└────────┬──────────────────────┘
         │ 5. Calculated values
         ▼
┌───────────────────────────────────────┐
│         Database Transaction          │
│                                       │
│  BEGIN TRANSACTION;                   │
│                                       │
│  1. INSERT review_sessions            │
│     (flashcard_id, quality_rating,    │
│      correct, ease_before, ease_after)│
│                                       │
│  2. UPDATE flashcards                 │
│     SET next_review_at = ?,           │
│         ease_factor = ?,              │
│         interval_days = ?,            │
│         review_count = +1             │
│                                       │
│  3. UPDATE vocabulary                 │
│     SET last_seen_at = NOW            │
│                                       │
│  4. UPDATE study_goals                │
│     SET current_value = +1            │
│     WHERE goal_type = 'daily_reviews' │
│                                       │
│  COMMIT;                              │
└────────┬──────────────────────────────┘
         │ 6. Success
         ▼
┌───────────────────────────────┐
│         UI Update             │
│  - Show next card             │
│  - Update progress: 2/20      │
│  - Update goal: 15/50         │
└────────┬──────────────────────┘
         │ 7. Next card
         ▼
   [Repeat from step 2]
```

### 3. Vocabulary Lifecycle Flow

```
┌─────────────────────────────────────────────────────┐
│                  Vocabulary Lifecycle                │
│                                                      │
│  ┌────────┐  encounter   ┌────────┐  flashcard    │
│  │  NEW   │─────────────►│LEARNING│───created────►│
│  └────────┘              └────────┘                │
│      ▲                        │                     │
│      │                        │ multiple            │
│      │ reset                  │ correct             │
│      │                        │ reviews             │
│      │                        ▼                     │
│  ┌────────┐              ┌────────┐                │
│  │SUSPEND │              │REVIEWING                │
│  │  ED    │◄─────user────┤        │                │
│  └────────┘   action     └────┬───┘                │
│      ▲                        │                     │
│      │                        │ high                │
│      │ user                   │ retention           │
│      │ action                 │ (interval>30d)      │
│      │                        ▼                     │
│  ┌────────┐              ┌────────┐                │
│  │  ANY   │◄─────────────│MASTERED│                │
│  │ STATUS │   (rare)     └────────┘                │
│  └────────┘                                         │
│                                                      │
└─────────────────────────────────────────────────────┘

Transitions:
- NEW → LEARNING: First flashcard created
- LEARNING → REVIEWING: After 3+ successful reviews
- REVIEWING → MASTERED: Interval exceeds 30 days
- ANY → SUSPENDED: User manually suspends
- SUSPENDED → (previous): User resumes
```

---

## State Diagrams

### Flashcard Status State Machine

```
┌───────────────────────────────────────────────────────┐
│              Flashcard Status States                  │
│                                                        │
│   ┌────────┐    create    ┌────────┐                 │
│   │  null  │─────────────►│ ACTIVE │                 │
│   └────────┘              └───┬────┘                 │
│                               │                       │
│          ┌────────────────────┼────────────┐         │
│          │                    │            │         │
│          │ suspend            │ bury       │         │
│          │                    │            │         │
│          ▼                    ▼            ▼         │
│   ┌──────────┐         ┌─────────┐  ┌─────────┐    │
│   │SUSPENDED │         │ BURIED  │  │ARCHIVED │    │
│   └────┬─────┘         └────┬────┘  └─────────┘    │
│        │                    │                        │
│        │ resume             │ unbury                 │
│        │                    │                        │
│        └────────────────────┴──────────┐            │
│                                         │            │
│                                         ▼            │
│                                    ┌────────┐        │
│                                    │ ACTIVE │        │
│                                    └────────┘        │
│                                                       │
└───────────────────────────────────────────────────────┘

State Descriptions:
- ACTIVE: Normal review cycle, shown in due queue
- SUSPENDED: User-paused, not shown until resumed
- BURIED: Temporarily hidden (e.g., sibling cards same day)
- ARCHIVED: Essentially deleted, very long intervals
```

### Study Goal State Machine

```
┌─────────────────────────────────────────────┐
│         Study Goal States                   │
│                                             │
│  ┌────────┐  create   ┌────────┐          │
│  │  null  │──────────►│ ACTIVE │          │
│  └────────┘           └───┬────┘          │
│                           │                │
│          ┌────────────────┼──────────┐    │
│          │                │          │    │
│          │ complete       │ fail     │    │
│          │ (reach target) │ (expire) │    │
│          │                │          │    │
│          ▼                ▼          │    │
│    ┌──────────┐    ┌──────────┐    │    │
│    │COMPLETED │    │ EXPIRED  │    │    │
│    └──────────┘    └──────────┘    │    │
│          │                │         │    │
│          └────────┬───────┘         │    │
│                   │ archive         │    │
│                   │                 │    │
│                   ▼                 │    │
│             ┌──────────┐            │    │
│             │ INACTIVE │◄───────────┘    │
│             └──────────┘   user action   │
│                   │                      │
│                   │ reactivate           │
│                   │                      │
│                   ▼                      │
│             ┌────────┐                   │
│             │ ACTIVE │                   │
│             └────────┘                   │
│                                          │
└──────────────────────────────────────────┘
```

---

## Quick Reference Tables

### Table: study_status Values

| Value | Meaning | Typical Interval | Action |
|-------|---------|------------------|--------|
| `new` | Never studied | N/A | Create flashcard |
| `learning` | First reviews | 0-10 days | Active learning |
| `reviewing` | Regular reviews | 10-30 days | Maintenance |
| `mastered` | High retention | 30+ days | Long intervals |
| `suspended` | User paused | N/A | Resume when ready |

### Table: card_type Values

| Type | Front | Back | Difficulty |
|------|-------|------|------------|
| `recognition` | Kanji | Reading + Meaning | Easy |
| `recall` | Meaning | Kanji + Reading | Medium |
| `production` | Meaning | Type Kanji | Hard |
| `listening` | Audio | Meaning/Reading | Medium |

### Table: quality_rating Scale

| Rating | Label | Meaning | Effect |
|--------|-------|---------|--------|
| 0 | Blackout | Complete failure | Reset to 0 |
| 1 | Wrong | Incorrect but familiar | Reset to 0 |
| 2 | Hard | Correct with great difficulty | Slightly increase |
| 3 | Good | Correct with effort | Normal increase |
| 4 | Easy | Correct with ease | Faster increase |
| 5 | Perfect | Instant recall | Maximum increase |

### Table: JLPT Levels

| Level | Kanji | Vocabulary | Description |
|-------|-------|------------|-------------|
| N5 | 100 | 800 | Basic, beginner |
| N4 | 300 | 1,500 | Elementary |
| N3 | 650 | 3,750 | Intermediate |
| N2 | 1,000 | 6,000 | Pre-advanced |
| N1 | 2,000+ | 10,000+ | Advanced, near-native |

### Table: Common SQL Patterns

| Operation | Pattern | Index Used |
|-----------|---------|------------|
| Find due cards | `WHERE status='active' AND next_review_at<=NOW` | `idx_flashcards_status_next_review` |
| Lookup vocabulary | `WHERE kanji_form=?` | `idx_vocabulary_kanji_form` |
| Filter by status | `WHERE study_status=?` | `idx_vocabulary_study_status` |
| Recent activity | `WHERE date(reviewed_at)=date('now')` | `idx_review_sessions_reviewed_at` |
| Find by checksum | `WHERE checksum=?` | `idx_screenshots_checksum` |

---

## Common Query Patterns

### Pattern 1: Get Vocabulary with All Related Data

```sql
-- Get vocabulary
SELECT * FROM vocabulary WHERE id = ?;

-- Get flashcards for this vocabulary
SELECT * FROM flashcards WHERE vocabulary_id = ?;

-- Get examples
SELECT * FROM example_sentences WHERE vocabulary_id = ? LIMIT 5;

-- Get kanji breakdown
SELECT k.*, vk.position
FROM kanji k
JOIN vocabulary_kanji vk ON k.id = vk.kanji_id
WHERE vk.vocabulary_id = ?
ORDER BY vk.position;

-- Get contexts (screenshots)
SELECT s.*, sv.context_snippet
FROM screenshots s
JOIN screenshot_vocabulary sv ON s.id = sv.screenshot_id
WHERE sv.vocabulary_id = ?
ORDER BY s.created_at DESC;

-- Get tags
SELECT t.*
FROM tags t
JOIN vocabulary_tags vt ON t.id = vt.tag_id
WHERE vt.vocabulary_id = ?;
```

### Pattern 2: Dashboard Data (Parallel Queries)

```sql
-- Query 1: Due card counts
SELECT 
  SUM(CASE WHEN next_review_at < datetime('now') THEN 1 ELSE 0 END) as overdue,
  SUM(CASE WHEN date(next_review_at) = date('now') THEN 1 ELSE 0 END) as today
FROM flashcards WHERE status = 'active';

-- Query 2: Today's stats
SELECT 
  COUNT(*) as reviews,
  AVG(CASE WHEN correct THEN 100 ELSE 0 END) as accuracy
FROM review_sessions
WHERE date(reviewed_at) = date('now');

-- Query 3: Vocabulary distribution
SELECT study_status, COUNT(*) as count
FROM vocabulary
GROUP BY study_status;

-- Query 4: Active goals
SELECT * FROM study_goals
WHERE is_active = 1
  AND date('now') BETWEEN start_date AND COALESCE(end_date, date('now'));
```

### Pattern 3: Search with Filters

```sql
-- Base query with multiple optional filters
SELECT DISTINCT v.*
FROM vocabulary v
LEFT JOIN vocabulary_tags vt ON v.id = vt.vocabulary_id
LEFT JOIN tags t ON vt.tag_id = t.id
LEFT JOIN flashcards f ON v.id = f.vocabulary_id
WHERE 1=1
  -- Text search (if provided)
  AND (v.kanji_form LIKE ? OR v.english_meaning LIKE ?)
  -- Status filter (if provided)
  AND v.study_status IN (?, ?, ...)
  -- JLPT filter (if provided)
  AND v.jlpt_level = ?
  -- Has flashcard filter (if provided)
  AND (f.id IS NOT NULL OR f.id IS NULL)
  -- Tag filter (if provided)
  AND t.name IN (?, ?, ...)
ORDER BY v.last_seen_at DESC
LIMIT ? OFFSET ?;
```

### Pattern 4: Statistics Over Time

```sql
-- Daily review stats for last 30 days
SELECT 
  date(reviewed_at) as date,
  COUNT(*) as reviews,
  ROUND(AVG(CASE WHEN correct THEN 100 ELSE 0 END), 1) as accuracy,
  ROUND(AVG(quality_rating), 2) as avg_quality
FROM review_sessions
WHERE reviewed_at >= date('now', '-30 days')
GROUP BY date(reviewed_at)
ORDER BY date;

-- Vocabulary growth over time
SELECT 
  date(created_at) as date,
  COUNT(*) as words_added
FROM vocabulary
WHERE created_at >= date('now', '-30 days')
GROUP BY date(created_at)
ORDER BY date;

-- Study goal progress history
SELECT 
  goal_type,
  date(created_at) as date,
  current_value
FROM study_goals
WHERE created_at >= date('now', '-30 days')
ORDER BY goal_type, date;
```

---

## Performance Metrics Reference

### Target Response Times

| Operation | Target | Max Acceptable |
|-----------|--------|----------------|
| Single vocabulary lookup | <10ms | 50ms |
| Vocabulary list (50 items) | <50ms | 200ms |
| Due cards query (100 items) | <100ms | 500ms |
| Dashboard stats (all queries) | <200ms | 1000ms |
| Review submission | <50ms | 200ms |
| Screenshot import | <2s | 10s |
| Complex search | <500ms | 2000ms |

### Database Size Estimates

| Records | Disk Space | Query Time Impact |
|---------|------------|-------------------|
| 1,000 vocabulary | ~500KB | Negligible |
| 5,000 vocabulary | ~2.5MB | Negligible |
| 10,000 vocabulary | ~5MB | Minimal |
| 50,000 reviews | ~10MB | Noticeable |
| 100,000 reviews | ~20MB | Consider archiving |
| 1,000 screenshots | ~2MB | Negligible |

### Index Usage Statistics

Run periodically to verify indexes are being used:

```sql
-- Check if indexes are used
EXPLAIN QUERY PLAN
SELECT * FROM flashcards 
WHERE status = 'active' 
  AND next_review_at <= datetime('now');

-- Should show:
-- SEARCH flashcards USING INDEX idx_flashcards_status_next_review
```

---

## Troubleshooting Guide

### Common Issues

**Issue**: "Foreign key constraint failed"
- **Cause**: Trying to reference non-existent record
- **Solution**: Check parent record exists before insert
- **Example**: Creating flashcard for deleted vocabulary

**Issue**: "CHECK constraint failed"
- **Cause**: Invalid enum value or out-of-range number
- **Solution**: Validate input against allowed values
- **Example**: `study_status = 'unknown'` (not in allowed list)

**Issue**: Slow due cards query
- **Cause**: Missing index or large result set
- **Solution**: Add LIMIT, verify index usage
- **Check**: `EXPLAIN QUERY PLAN SELECT ...`

**Issue**: Screenshot import slow
- **Cause**: Processing each word individually
- **Solution**: Use batch inserts in transaction
- **Performance**: 10x+ improvement

**Issue**: Dashboard loads slowly
- **Cause**: Sequential query execution
- **Solution**: Run queries in parallel
- **Performance**: 5x+ improvement

---

## Migration Checklist

When making schema changes:

- [ ] Update schema version in _migration_backup
- [ ] Test with sample data
- [ ] Backup database before migration
- [ ] Run PRAGMA foreign_key_check after changes
- [ ] Update indexes if query patterns change
- [ ] Run ANALYZE after bulk changes
- [ ] Update this documentation
- [ ] Update application code
- [ ] Test foreign key constraints work
- [ ] Verify performance with production data size

---

## Related Documents

- [Database Schema Reference](DATABASE_SCHEMA_REFERENCE.md) - Complete technical specification
- [UI/UX Design Guide](UI_UX_DESIGN_GUIDE.md) - Interface design patterns
- [User Workflows](USER_WORKFLOWS.md) - Detailed user journeys
- [API Integration Guide](API_INTEGRATION_GUIDE.md) - Code examples and patterns

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Quick Reference Card**: Print pages 5-7 for desk reference

---

## Appendix: ASCII Art Quick Reference

### Table Relationships (Simplified)

```
sources ──┬── screenshots ──┬── vocabulary ──┬── flashcards ── review_sessions
          │                 │                 │
          │                 │                 └── example_sentences
          │                 │
          │                 └── kanji (via vocab_kanji)
          │
          └── (metadata)    tags (via vocab_tags)
```

### Review Loop

```
Due Cards → Show Card → User Answers → Calculate SRS → Update DB → Next Card
    ▲                                                                    │
    └────────────────────────────────────────────────────────────────────┘
```

### Study Status Progression

```
NEW → LEARNING → REVIEWING → MASTERED
 ↕       ↕          ↕           ↕
    SUSPENDED (any state can be suspended)
```

---

**End of Quick Reference Guide**
