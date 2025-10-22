# User Workflows
**Japanese Learning Application - Common User Journeys**

Version: 1.0  
Last Updated: 2025-10-22  
Target Audience: Product Managers, Developers, Designers

---

## Table of Contents

1. [Overview](#overview)
2. [Core Workflows](#core-workflows)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [User Scenarios](#user-scenarios)
5. [Error Handling](#error-handling)
6. [Optimization Opportunities](#optimization-opportunities)

---

## Overview

This document maps user actions to database operations, showing how users interact with the system and how data flows through the application.

### Workflow Categories

1. **Content Import**: Adding new learning material
2. **Study**: Active learning and review
3. **Progress Tracking**: Monitoring advancement
4. **Content Management**: Organizing learning materials

---

## Core Workflows

### Workflow 1: First-Time User Setup

**User Goal**: Start learning Japanese with the application

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User opens application                    │
│    Database: Empty                           │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. User sees empty state                     │
│    UI: "Get started by adding your first     │
│         learning source"                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 3. User clicks "Add Source"                  │
│    Modal opens with form                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 4. User fills in source details:             │
│    - Name: "Genki Textbook I"               │
│    - Type: "Textbook"                       │
│    - Difficulty: "Beginner"                 │
│    - JLPT Target: "N5"                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 5. System creates source                     │
│    SQL:                                      │
│    INSERT INTO sources (name, type,          │
│      difficulty_level, jlpt_target)          │
│    VALUES ('Genki Textbook I', 'textbook',  │
│      'beginner', 'N5');                      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 6. User uploads first screenshot             │
│    (See Workflow 2)                          │
└─────────────────────────────────────────────┘
```

**Database Operations**:
1. INSERT into `sources` table
2. Returns `source_id` for future use

**Success Criteria**:
- Source appears in sources list
- User can select source for screenshot upload
- `sources.created_at` and `started_at` set to current time

---

### Workflow 2: Screenshot Import & Vocabulary Extraction

**User Goal**: Extract Japanese text from a screenshot

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User navigates to "Import Screenshot"     │
│    UI: Shows upload dropzone                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. User drags image file or clicks upload   │
│    File: manga_page.png                      │
│    UI: Shows file preview                    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 3. User selects source (or creates new)      │
│    Selected: "Yotsuba Manga"                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 4. User clicks "Process"                     │
│    System starts OCR processing              │
│    UI: Shows loading spinner                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 5. OCR Service processes image               │
│    Returns:                                  │
│    - Extracted text blocks                   │
│    - Bounding boxes                          │
│    - Confidence scores                       │
│    - Detected readings (furigana)            │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 6. System calculates checksum                │
│    SHA256(image) → abc123...                 │
│    Checks for duplicates:                    │
│    SELECT COUNT(*) FROM screenshots          │
│    WHERE checksum = 'abc123...'              │
└────────────────┬────────────────────────────┘
                 │
                 ▼ (if not duplicate)
┌─────────────────────────────────────────────┐
│ 7. System creates screenshot record          │
│    SQL:                                      │
│    INSERT INTO screenshots (                 │
│      file_path, source_id,                   │
│      ocr_confidence, extracted_text_json,    │
│      checksum, has_furigana                  │
│    ) VALUES (                                │
│      'uploads/manga_page.png', 1,            │
│      0.87, '[{"text":"日本語",...}]',         │
│      'abc123...', 1                          │
│    );                                        │
│    Returns screenshot_id                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 8. For each detected text block:             │
│    Extract vocabulary words                  │
│    Example: "日本語を勉強します"              │
│    Segmented to: ["日本語", "を", "勉強",    │
│                   "します"]                   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 9. For each word:                            │
│    Check if exists in vocabulary             │
│                                              │
│    SELECT id FROM vocabulary                 │
│    WHERE kanji_form = '日本語'               │
│      AND hiragana_reading = 'にほんご'        │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    [Exists]        [New Word]
         │               │
         ▼               ▼
┌─────────────┐   ┌─────────────┐
│ 10a. Update │   │ 10b. Create │
│              │   │              │
│ UPDATE       │   │ INSERT INTO  │
│ vocabulary   │   │ vocabulary   │
│ SET          │   │ (kanji_form, │
│  encounter_  │   │  hiragana_   │
│  count += 1, │   │  reading,    │
│  last_seen_  │   │  english_    │
│  at = NOW()  │   │  meaning,    │
│ WHERE id = ? │   │  ...) VALUES │
│              │   │ (...);       │
└──────┬───────┘   └──────┬───────┘
       │                  │
       └────────┬─────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ 11. Link vocabulary to screenshot            │
│                                              │
│     INSERT INTO screenshot_vocabulary (      │
│       screenshot_id, vocabulary_id,          │
│       position_in_text, context_snippet      │
│     ) VALUES (                               │
│       ?, ?, ?, ?                             │
│     );                                       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 12. System updates source last_accessed_at   │
│                                              │
│     UPDATE sources                           │
│     SET last_accessed_at = CURRENT_TIMESTAMP │
│     WHERE id = ?;                            │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 13. UI shows results:                        │
│     - Screenshot with bounding boxes         │
│     - List of extracted words                │
│     - Known vs. new word indicators          │
│     - Actions: [Add to flashcards]           │
│                [View details]                │
└─────────────────────────────────────────────┘
```

**Database Operations Summary**:
1. Check duplicate: SELECT from `screenshots` by checksum
2. Create screenshot: INSERT into `screenshots`
3. For each word:
   - Check exists: SELECT from `vocabulary`
   - If exists: UPDATE `vocabulary` (increment encounter)
   - If new: INSERT into `vocabulary`
4. Link words: INSERT into `screenshot_vocabulary`
5. Update source: UPDATE `sources.last_accessed_at`

**Queries Executed** (for 10 words in screenshot):
- 1 duplicate check
- 1 screenshot insert
- 10 vocabulary lookups
- ~5 vocabulary inserts (new words)
- ~5 vocabulary updates (known words)
- 10 screenshot_vocabulary inserts
- 1 source update
**Total**: ~28 queries

**Optimization**: Batch operations in a transaction for atomicity

**Success Criteria**:
- Screenshot saved with OCR data
- All detected words in vocabulary table
- Links created in screenshot_vocabulary
- User can see extracted vocabulary list
- Source last_accessed_at updated

---

### Workflow 3: Creating Flashcards from Vocabulary

**User Goal**: Turn vocabulary words into reviewable flashcards

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User browses vocabulary list              │
│    Shows words with study_status = 'new'     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. User clicks "Create Flashcard" on word    │
│    Word: 日本語 (nihongo)                    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 3. System checks if flashcard exists         │
│                                              │
│    SELECT COUNT(*) FROM flashcards           │
│    WHERE vocabulary_id = ?                   │
│      AND status != 'archived';               │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    [Exists]         [New]
         │               │
         ▼               ▼
┌─────────────┐   ┌─────────────────────────────┐
│ Show error: │   │ 4. Modal shows card options: │
│ "Flashcard  │   │    - Card Type: [Recognition│
│  already    │   │      Recall, Production,     │
│  exists"    │   │      Listening] ▼            │
│             │   │    - Screenshot Context?     │
│             │   │      [ ] Include screenshot  │
│             │   │                              │
│             │   │    [Create]                  │
└─────────────┘   └──────────┬──────────────────┘
                             │
                             ▼
                  ┌─────────────────────────────┐
                  │ 5. System creates flashcard  │
                  │                              │
                  │    INSERT INTO flashcards (  │
                  │      vocabulary_id,          │
                  │      screenshot_id,          │
                  │      card_type,              │
                  │      status,                 │
                  │      next_review_at,         │
                  │      ease_factor,            │
                  │      interval_days           │
                  │    ) VALUES (                │
                  │      ?,                      │
                  │      ?,  -- NULL if no SS    │
                  │      'recognition',          │
                  │      'active',               │
                  │      CURRENT_TIMESTAMP,      │
                  │      2.5,                    │
                  │      0.0                     │
                  │    );                        │
                  └──────────┬──────────────────┘
                             │
                             ▼
                  ┌─────────────────────────────┐
                  │ 6. Update vocabulary status  │
                  │                              │
                  │    UPDATE vocabulary         │
                  │    SET study_status =        │
                  │      'learning'              │
                  │    WHERE id = ?              │
                  │      AND study_status = 'new'│
                  └──────────┬──────────────────┘
                             │
                             ▼
                  ┌─────────────────────────────┐
                  │ 7. UI updates:               │
                  │    - Success message         │
                  │    - Vocabulary badge →      │
                  │      "Learning"              │
                  │    - Button → "Review Now"   │
                  └─────────────────────────────┘
```

**Database Operations**:
1. Check existing: SELECT from `flashcards`
2. Create card: INSERT into `flashcards`
3. Update status: UPDATE `vocabulary`

**Success Criteria**:
- Flashcard created with `status = 'active'`
- `next_review_at` set to NOW (due immediately for first review)
- Vocabulary `study_status` → 'learning'
- User can access card in review queue

**Edge Cases**:
- Duplicate flashcard attempt → Show error
- Card with screenshot context → Link to specific screenshot
- Multiple card types → Allow different types for same vocabulary

---

### Workflow 4: Daily Review Session

**User Goal**: Review due flashcards using spaced repetition

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User opens "Review" section               │
│    System queries due cards                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. System loads due flashcards               │
│                                              │
│    SELECT f.*, v.*                           │
│    FROM flashcards f                         │
│    JOIN vocabulary v ON f.vocabulary_id=v.id │
│    WHERE f.status = 'active'                 │
│      AND f.next_review_at <= CURRENT_TIME    │
│    ORDER BY f.next_review_at                 │
│    LIMIT 100;                                │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    [Has Cards]      [No Cards]
         │               │
         ▼               ▼
┌─────────────┐   ┌─────────────┐
│ Show first  │   │ Show "All   │
│ card        │   │ caught up!" │
└──────┬──────┘   └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│ 3. Display card (Question side)              │
│    UI: Shows kanji form                      │
│                                              │
│    Card Type determines what's hidden:       │
│    - Recognition: Hide reading + meaning     │
│    - Recall: Show meaning, hide kanji        │
│    - Production: Show meaning, type kanji    │
│    - Listening: Play audio, hide text        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 4. User thinks/attempts answer               │
│    (No database interaction)                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 5. User clicks "Show Answer"                 │
│    UI: Reveals reading + meaning             │
│    Shows quality rating buttons              │
│    [Again] [Hard] [Good] [Easy]             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 6. User selects quality (e.g., "Good" = 3)   │
│    System starts transaction                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 7. Calculate next review (SM-2 algorithm)    │
│                                              │
│    if quality >= 3:  // Correct             │
│      interval = interval * ease_factor       │
│      consecutive_correct += 1                │
│    else:  // Incorrect                       │
│      interval = 0 (relearn)                  │
│      consecutive_correct = 0                 │
│      lapses += 1                             │
│                                              │
│    // Adjust ease factor                     │
│    ease_factor = ease_factor +              │
│      (0.1 - (5-quality) * (0.08 + ...))     │
│    ease_factor = max(1.3, ease_factor)       │
│                                              │
│    next_review = NOW + interval_days         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 8. Create review session record              │
│                                              │
│    INSERT INTO review_sessions (             │
│      flashcard_id, session_id,               │
│      quality_rating, user_answer,            │
│      correct, response_time_ms,              │
│      interval_before_days,                   │
│      ease_factor_before,                     │
│      ease_factor_after                       │
│    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 9. Update flashcard                          │
│                                              │
│    UPDATE flashcards SET                     │
│      last_reviewed_at = CURRENT_TIMESTAMP,   │
│      next_review_at = ?,                     │
│      ease_factor = ?,                        │
│      interval_days = ?,                      │
│      review_count = review_count + 1,        │
│      consecutive_correct = ?,                │
│      lapses = ?                              │
│    WHERE id = ?;                             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 10. Update vocabulary                        │
│                                              │
│     UPDATE vocabulary SET                    │
│       last_seen_at = CURRENT_TIMESTAMP       │
│     WHERE id = ?;                            │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 11. Update study goal progress               │
│                                              │
│     UPDATE study_goals SET                   │
│       current_value = current_value + 1      │
│     WHERE goal_type = 'daily_reviews'        │
│       AND is_active = 1                      │
│       AND date('now') BETWEEN                │
│           start_date AND                     │
│           COALESCE(end_date, date('now'));   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 12. Commit transaction                       │
│     Show next card or completion screen      │
└─────────────────────────────────────────────┘
```

**Database Operations per Review**:
1. Load due cards: SELECT with JOIN (done once at start)
2. Create review record: INSERT into `review_sessions`
3. Update flashcard: UPDATE `flashcards`
4. Update vocabulary: UPDATE `vocabulary`
5. Update goals: UPDATE `study_goals`

**Queries per Card**: 4 writes (in transaction)

**For 20 card session**: 
- 1 initial SELECT
- 80 writes (20 cards × 4 operations)
**Total**: 81 queries

**Success Criteria**:
- Each review recorded in `review_sessions`
- Flashcard algorithm state updated correctly
- Next review scheduled appropriately
- Study goals progress incremented
- User sees accurate "Next review" times

---

### Workflow 5: Progress Tracking & Statistics

**User Goal**: View learning progress and statistics

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User opens "Dashboard" or "Statistics"    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. System loads multiple aggregations        │
│    (Parallel queries for performance)        │
└────────────────┬────────────────────────────┘
                 │
    ┌────────────┼────────────┬────────────┐
    │            │            │            │
    ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Due Cards│ │Reviews  │ │Study    │ │Progress │
│Count    │ │Today    │ │Goals    │ │Stats    │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     └───────────┴───────────┴───────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 3. UI renders dashboard with all stats       │
└─────────────────────────────────────────────┘
```

**Query 1: Due Cards**
```sql
SELECT 
  COUNT(CASE WHEN next_review_at < datetime('now') THEN 1 END) as overdue,
  COUNT(CASE WHEN date(next_review_at) = date('now') THEN 1 END) as today,
  COUNT(CASE WHEN next_review_at <= datetime('now', '+7 days') THEN 1 END) as this_week
FROM flashcards
WHERE status = 'active';
```

**Query 2: Today's Reviews**
```sql
SELECT 
  COUNT(*) as total_reviews,
  SUM(CASE WHEN correct THEN 1 ELSE 0 END) as correct_count,
  ROUND(AVG(quality_rating), 2) as avg_quality,
  ROUND(AVG(response_time_ms) / 1000.0, 1) as avg_time_sec
FROM review_sessions
WHERE date(reviewed_at) = date('now');
```

**Query 3: Study Goals Progress**
```sql
SELECT 
  goal_type,
  target_value,
  current_value,
  ROUND(current_value * 100.0 / target_value, 1) as progress_pct,
  CASE 
    WHEN current_value >= target_value THEN 'completed'
    WHEN current_value >= target_value * 0.8 THEN 'almost'
    ELSE 'in_progress'
  END as status
FROM study_goals
WHERE is_active = 1
  AND date('now') BETWEEN start_date AND COALESCE(end_date, date('now'));
```

**Query 4: Vocabulary Progress**
```sql
SELECT 
  study_status,
  COUNT(*) as count
FROM vocabulary
GROUP BY study_status
ORDER BY 
  CASE study_status
    WHEN 'new' THEN 1
    WHEN 'learning' THEN 2
    WHEN 'reviewing' THEN 3
    WHEN 'mastered' THEN 4
    WHEN 'suspended' THEN 5
  END;
```

**Query 5: Review Heatmap (Last 30 Days)**
```sql
SELECT 
  date(reviewed_at) as date,
  COUNT(*) as reviews,
  ROUND(AVG(CASE WHEN correct THEN 100 ELSE 0 END), 1) as accuracy
FROM review_sessions
WHERE reviewed_at >= date('now', '-30 days')
GROUP BY date(reviewed_at)
ORDER BY date;
```

**Database Operations**:
- 5 SELECT queries (can be parallel)
- Mostly aggregations (COUNT, AVG, SUM)
- No writes

**Success Criteria**:
- All statistics display accurately
- Performance: <500ms total load time
- Real-time updates after reviews
- Historical data preserved

---

### Workflow 6: Kanji Study

**User Goal**: Learn kanji characters and their usage

**Steps**:

```
┌─────────────────────────────────────────────┐
│ 1. User clicks on vocabulary word with kanji │
│    Word: 日本語                              │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. System queries kanji breakdown            │
│                                              │
│    SELECT k.*                                │
│    FROM kanji k                              │
│    JOIN vocabulary_kanji vk                  │
│      ON k.id = vk.kanji_id                   │
│    WHERE vk.vocabulary_id = ?                │
│    ORDER BY vk.position;                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 3. Display kanji breakdown                   │
│                                              │
│    日 (sun, day)                             │
│    - On: ニチ、ジツ                          │
│    - Kun: ひ、び                             │
│    - Strokes: 4 | Grade: 1 | N5             │
│                                              │
│    本 (book, origin)                         │
│    - On: ホン                                │
│    - Kun: もと                               │
│    - Strokes: 5 | Grade: 1 | N5             │
│                                              │
│    語 (language, word)                       │
│    - On: ゴ                                  │
│    - Kun: かた-る、かた-らう                  │
│    - Strokes: 14 | Grade: 2 | N5            │
│                                              │
│    [Study These Kanji Separately]            │
└─────────────────────────────────────────────┘
```

**Query: Words Using This Kanji**
```sql
SELECT v.*
FROM vocabulary v
JOIN vocabulary_kanji vk ON v.id = vk.vocabulary_id
WHERE vk.kanji_id = ?
LIMIT 10;
```

**Success Criteria**:
- All kanji in word displayed
- Correct position ordering (via `vocabulary_kanji.position`)
- Related vocabulary shown
- Ability to study individual kanji

---

## Data Flow Diagrams

### Review Session Data Flow

```
┌─────────────┐
│    User     │
│  Answers    │
└──────┬──────┘
       │ quality_rating: 3
       │ response_time: 2500ms
       ▼
┌─────────────────────────────┐
│   Application Logic         │
│  ┌────────────────────────┐ │
│  │ SM-2 Algorithm         │ │
│  │ - Calculate interval   │ │
│  │ - Adjust ease_factor   │ │
│  │ - Determine next_review│ │
│  └────────────────────────┘ │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│      Database (Transaction) │
├─────────────────────────────┤
│ 1. review_sessions ← INSERT │
│    - quality_rating: 3      │
│    - correct: true          │
│    - ease_before: 2.5       │
│    - ease_after: 2.6        │
│                             │
│ 2. flashcards ← UPDATE      │
│    - next_review_at: +4days │
│    - ease_factor: 2.6       │
│    - interval_days: 4       │
│    - review_count: +1       │
│    - consecutive_correct: +1│
│                             │
│ 3. vocabulary ← UPDATE      │
│    - last_seen_at: NOW      │
│                             │
│ 4. study_goals ← UPDATE     │
│    - current_value: +1      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    UI Updates               │
│  - Show next card           │
│  - Update progress bar      │
│  - Update streak counter    │
│  - Update goal progress     │
└─────────────────────────────┘
```

### Screenshot Import Data Flow

```
┌──────────────┐
│  User Uploads│
│  Screenshot  │
└──────┬───────┘
       │ manga_page.png
       ▼
┌─────────────────┐
│  File Storage   │
│  - Save file    │
│  - Calculate SHA│
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│  OCR Service (External)     │
│  - Detect text blocks       │
│  - Extract readings         │
│  - Generate bounding boxes  │
│  - Calculate confidence     │
└──────┬──────────────────────┘
       │ OCR Results
       ▼
┌─────────────────────────────┐
│  NLP Processing             │
│  - Tokenize text            │
│  - Identify vocabulary      │
│  - Extract context          │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│     Database (Transaction)  │
├─────────────────────────────┤
│ 1. screenshots ← INSERT     │
│    - file_path              │
│    - ocr_confidence         │
│    - extracted_text_json    │
│    - checksum (duplicate?)  │
│                             │
│ 2. For each word:           │
│    vocabulary ← INSERT/UPD  │
│    - New: INSERT            │
│    - Exists: UPDATE counter │
│                             │
│ 3. screenshot_vocabulary    │
│    ← INSERT (links)         │
│    - position_in_text       │
│    - context_snippet        │
│                             │
│ 4. sources ← UPDATE         │
│    - last_accessed_at       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│      UI Display             │
│  - Show extracted text      │
│  - Highlight new words      │
│  - Offer flashcard creation │
│  - Show confidence score    │
└─────────────────────────────┘
```

---

## User Scenarios

### Scenario 1: Beginner's First Week

**Background**: New Japanese learner, starting with N5 content

**Day 1**: Setup
- Creates source: "Genki I Textbook"
- Imports 5 screenshots from Chapter 1
- 47 new vocabulary words extracted
- Creates flashcards for 20 words
- Sets daily goal: 10 reviews/day

**Database State**:
```
sources: 1 record
screenshots: 5 records
vocabulary: 47 records (all study_status='new')
flashcards: 20 records (all interval_days=0)
study_goals: 1 record (daily_reviews, target=10)
```

**Day 2**: First review session
- Reviews all 20 cards
- Average quality: 2.8 (mix of again/good)
- Completes daily goal
- Adds 10 more flashcards

**Database Changes**:
```
flashcards: 
  - 20 updated (intervals: 0-1 days)
  - 10 new
review_sessions: 20 new records
study_goals: current_value = 20
```

**Day 3-7**: Building routine
- Daily reviews: 15-25 cards
- Gradual difficulty increase
- Some cards moving to "reviewing" status
- New words added as confidence builds

**Week 1 Summary**:
```
vocabulary: 47 new, 30 learning, 0 reviewing, 0 mastered
flashcards: 30 active cards
review_sessions: 150 reviews
accuracy: 65% → 82% over week
```

### Scenario 2: Intermediate Learner's Anime Study

**Background**: N3 level, learning from anime

**Workflow**:
1. Takes 3-5 screenshots per episode
2. Reviews vocabulary after each episode
3. Focuses on colloquial expressions
4. High encounter rate for common phrases

**Database Pattern**:
- Screenshots tagged by anime series
- Vocabulary encounter_count increases rapidly
- Many words have multiple screenshot contexts
- Example sentences extracted from subtitles

**Queries Used Frequently**:
```sql
-- Find words seen multiple times
SELECT * FROM vocabulary 
WHERE encounter_count >= 5 
  AND study_status = 'new'
ORDER BY encounter_count DESC;

-- Context-rich vocabulary
SELECT v.*, COUNT(sv.screenshot_id) as context_count
FROM vocabulary v
JOIN screenshot_vocabulary sv ON v.id = sv.vocabulary_id
GROUP BY v.id
HAVING context_count >= 3;
```

### Scenario 3: Advanced Learner's News Reading

**Background**: N1 level, studying news articles

**Workflow**:
1. Screenshots of news articles
2. Focus on specialized vocabulary
3. Kanji-intensive content
4. Low-frequency words

**Database Characteristics**:
- Lower encounter_count per word (specialized vocab)
- Higher JLPT levels (N2/N1)
- More kanji per vocabulary word
- Longer example sentences

**Challenges**:
- Many new kanji need to be added to kanji table
- Vocabulary often requires manual meaning entry
- Complex readings (jukugo patterns)

---

## Error Handling

### Common Error Scenarios

#### 1. Duplicate Screenshot Detection

**Trigger**: User uploads same screenshot twice

**Flow**:
```
Upload → Calculate checksum → Query screenshots
  ↓
  SELECT id FROM screenshots WHERE checksum = ?
  ↓
  [Found] → Show error: "This screenshot was already imported on [date]"
           → Offer: "View existing import" (link to screenshot detail)
```

**Database Query**:
```sql
SELECT id, processed_at, source_id 
FROM screenshots 
WHERE checksum = ?;
```

#### 2. OCR Processing Failure

**Trigger**: OCR service returns low confidence or error

**Flow**:
```
OCR Service → Returns confidence < 50%
  ↓
  UI Warning: "Low confidence detection"
  ↓
  Options:
  - "Continue anyway" → Save with flag
  - "Retry with different settings"
  - "Manual entry"
```

**Database Action**:
```sql
-- Still save, but flag for review
INSERT INTO screenshots (..., ocr_confidence, needs_review)
VALUES (..., 0.35, 1);
```

#### 3. Foreign Key Constraint Violation

**Trigger**: Attempting to create flashcard for deleted vocabulary

**Prevention**:
```typescript
// Always check existence first
const vocab = await db.query(
  'SELECT id FROM vocabulary WHERE id = ?',
  [vocabularyId]
);

if (!vocab) {
  throw new Error('Vocabulary not found');
}

// Then create flashcard
await db.query(
  'INSERT INTO flashcards (vocabulary_id, ...) VALUES (?, ...)',
  [vocabularyId, ...]
);
```

#### 4. Study Goal Progress Calculation Error

**Trigger**: Multiple concurrent review submissions

**Solution**: Use transaction with locks
```sql
BEGIN TRANSACTION;

UPDATE study_goals 
SET current_value = current_value + 1
WHERE id = ?
  AND is_active = 1;

COMMIT;
```

---

## Optimization Opportunities

### 1. Batch Operations

**Current**: Individual inserts for each vocabulary word
```typescript
// Slow
for (const word of words) {
  await db.insert('vocabulary', word);
}
```

**Optimized**: Batch insert
```typescript
// Fast
await db.transaction(async (trx) => {
  await trx.insert('vocabulary').values(words);
});
```

### 2. Caching Frequently Accessed Data

**Cacheable Data**:
- Due card count (cache for 5 minutes)
- Study goal progress (cache until review)
- Vocabulary list (cache with filters)
- Source list (cache until modification)

**Implementation**:
```typescript
const cache = new Map();

async function getDueCardCount() {
  const cached = cache.get('due_cards');
  if (cached && Date.now() - cached.timestamp < 300000) { // 5 min
    return cached.value;
  }
  
  const count = await db.query('SELECT COUNT(*) ...');
  cache.set('due_cards', { value: count, timestamp: Date.now() });
  return count;
}
```

### 3. Pagination for Large Lists

**Vocabulary List**:
```typescript
const PAGE_SIZE = 50;

function getVocabularyPage(page: number, filters: Filters) {
  return db.query(`
    SELECT * FROM vocabulary
    WHERE study_status IN (?)
    ORDER BY last_seen_at DESC
    LIMIT ? OFFSET ?
  `, [filters.statuses, PAGE_SIZE, page * PAGE_SIZE]);
}
```

### 4. Denormalization for Statistics

**Problem**: Complex aggregation queries slow down dashboard

**Solution**: Maintain summary table
```sql
CREATE TABLE daily_stats (
  date DATE PRIMARY KEY,
  reviews_count INTEGER,
  accuracy REAL,
  new_words INTEGER,
  study_time_minutes INTEGER
);

-- Update via trigger or scheduled job
```

---

## Next Steps

For implementation:

1. **Start with Core Workflows**
   - Screenshot import (Workflow 2)
   - Flashcard creation (Workflow 3)
   - Review session (Workflow 4)

2. **Add Progress Features**
   - Dashboard (Workflow 5)
   - Statistics
   - Goal tracking

3. **Enhance with Advanced Features**
   - Kanji study (Workflow 6)
   - Tag management
   - Export/import

**Related Documents**:
- [Database Schema Reference](DATABASE_SCHEMA_REFERENCE.md)
- [UI/UX Design Guide](UI_UX_DESIGN_GUIDE.md)
- [API Integration Guide](API_INTEGRATION_GUIDE.md)

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Next Review**: After user testing
