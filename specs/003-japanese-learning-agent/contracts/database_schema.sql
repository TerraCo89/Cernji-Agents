-- Japanese Learning Agent Database Schema
-- Version: 1.0.0
-- Created: 2025-10-21
-- Database: SQLite 3.x
-- Location: data/japanese_learning.db

-- =============================================================================
-- CONFIGURATION
-- =============================================================================

-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize for performance
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;  -- 64MB cache
PRAGMA foreign_keys=ON;     -- Enable foreign key constraints

-- =============================================================================
-- TABLES
-- =============================================================================

-- Screenshots Table
-- Stores processed game screenshots with OCR extraction results
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ocr_confidence REAL NOT NULL CHECK(ocr_confidence BETWEEN 0.0 AND 1.0),
    extracted_text_json TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary Table
-- Stores unique Japanese words/phrases encountered during learning
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

    -- Constraints
    UNIQUE(kanji_form, hiragana_reading),
    CHECK(last_seen_at >= first_seen_at)
);

-- Flashcards Table
-- Study cards for spaced repetition vocabulary review
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocabulary_id INTEGER NOT NULL,
    screenshot_id INTEGER,  -- Optional: provides example context
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    next_review_at TIMESTAMP NOT NULL,
    ease_factor REAL NOT NULL DEFAULT 2.5 CHECK(ease_factor >= 1.3),
    interval_days REAL NOT NULL DEFAULT 0.0 CHECK(interval_days >= 0),
    review_count INTEGER NOT NULL DEFAULT 0 CHECK(review_count >= 0),

    -- Foreign Keys
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE SET NULL
);

-- Review Sessions Table
-- Records individual flashcard review attempts for statistics
CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flashcard_id INTEGER NOT NULL,
    reviewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_response TEXT NOT NULL CHECK(user_response IN ('again', 'hard', 'medium', 'easy')),
    response_time_ms INTEGER CHECK(response_time_ms > 0),
    correct BOOLEAN NOT NULL,

    -- Foreign Keys
    FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Screenshots Indexes
CREATE INDEX IF NOT EXISTS idx_screenshots_processed_at ON screenshots(processed_at);

-- Vocabulary Indexes
CREATE INDEX IF NOT EXISTS idx_vocabulary_study_status ON vocabulary(study_status);
CREATE INDEX IF NOT EXISTS idx_vocabulary_last_seen_at ON vocabulary(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_vocabulary_encounter_count ON vocabulary(encounter_count DESC);

-- Flashcards Indexes
CREATE INDEX IF NOT EXISTS idx_flashcards_vocabulary_id ON flashcards(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_next_review_at ON flashcards(next_review_at);
CREATE INDEX IF NOT EXISTS idx_flashcards_created_at ON flashcards(created_at);

-- Review Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_review_sessions_flashcard_id ON review_sessions(flashcard_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_reviewed_at ON review_sessions(reviewed_at);

-- =============================================================================
-- VIEWS (OPTIONAL - FOR COMMON QUERIES)
-- =============================================================================

-- View: Due Flashcards
-- Returns all flashcards due for review with vocabulary details
CREATE VIEW IF NOT EXISTS view_due_flashcards AS
SELECT
    f.id AS flashcard_id,
    f.next_review_at,
    f.ease_factor,
    f.interval_days,
    f.review_count,
    v.id AS vocabulary_id,
    v.kanji_form,
    v.hiragana_reading,
    v.romaji_reading,
    v.english_meaning,
    v.part_of_speech,
    s.file_path AS example_screenshot
FROM flashcards f
JOIN vocabulary v ON f.vocabulary_id = v.id
LEFT JOIN screenshots s ON f.screenshot_id = s.id
WHERE f.next_review_at <= CURRENT_TIMESTAMP
ORDER BY f.next_review_at ASC;

-- View: Vocabulary Statistics
-- Provides aggregated statistics by study status
CREATE VIEW IF NOT EXISTS view_vocabulary_stats AS
SELECT
    study_status,
    COUNT(*) as word_count,
    SUM(encounter_count) as total_encounters,
    AVG(encounter_count) as avg_encounters,
    MAX(last_seen_at) as most_recent_encounter
FROM vocabulary
GROUP BY study_status;

-- View: Recent Review Performance
-- Shows recent review sessions with performance metrics
CREATE VIEW IF NOT EXISTS view_recent_reviews AS
SELECT
    rs.id AS review_id,
    rs.reviewed_at,
    rs.user_response,
    rs.response_time_ms,
    rs.correct,
    v.kanji_form,
    v.hiragana_reading,
    v.english_meaning,
    f.review_count AS total_reviews
FROM review_sessions rs
JOIN flashcards f ON rs.flashcard_id = f.id
JOIN vocabulary v ON f.vocabulary_id = v.id
ORDER BY rs.reviewed_at DESC;

-- =============================================================================
-- TRIGGERS (DATA INTEGRITY)
-- =============================================================================

-- Trigger: Auto-update vocabulary.last_seen_at on encounter
-- When vocabulary encounter_count increments, update last_seen_at
CREATE TRIGGER IF NOT EXISTS trg_vocabulary_update_last_seen
AFTER UPDATE OF encounter_count ON vocabulary
FOR EACH ROW
WHEN NEW.encounter_count > OLD.encounter_count
BEGIN
    UPDATE vocabulary
    SET last_seen_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger: Auto-transition vocabulary to 'learning' when flashcard created
CREATE TRIGGER IF NOT EXISTS trg_vocabulary_status_on_flashcard
AFTER INSERT ON flashcards
FOR EACH ROW
WHEN (SELECT study_status FROM vocabulary WHERE id = NEW.vocabulary_id) = 'new'
BEGIN
    UPDATE vocabulary
    SET study_status = 'learning'
    WHERE id = NEW.vocabulary_id;
END;

-- =============================================================================
-- SAMPLE QUERIES (FOR TESTING)
-- =============================================================================

-- Query: Get all due flashcards
-- SELECT * FROM view_due_flashcards LIMIT 20;

-- Query: Get vocabulary by status
-- SELECT * FROM vocabulary WHERE study_status = 'new' ORDER BY encounter_count DESC;

-- Query: Get review statistics for today
-- SELECT
--     COUNT(*) as reviews_today,
--     SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_count,
--     AVG(response_time_ms) as avg_response_time_ms
-- FROM review_sessions
-- WHERE DATE(reviewed_at) = DATE('now');

-- Query: Find vocabulary by text (search)
-- SELECT * FROM vocabulary
-- WHERE kanji_form LIKE '%' || ? || '%'
--    OR hiragana_reading LIKE '%' || ? || '%'
--    OR english_meaning LIKE '%' || ? || '%'
-- ORDER BY encounter_count DESC;

-- =============================================================================
-- VERSION HISTORY
-- =============================================================================

-- Version 1.0.0 (2025-10-21)
-- - Initial schema with 4 tables: screenshots, vocabulary, flashcards, review_sessions
-- - Indexes for common query patterns
-- - Views for aggregated statistics
-- - Triggers for data integrity
