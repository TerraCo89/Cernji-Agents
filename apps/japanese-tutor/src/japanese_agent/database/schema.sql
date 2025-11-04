-- ============================================================================
-- Japanese Learning Agent - Database Schema
-- Version: 2.0
-- Based on: DATABASE_SCHEMA_REFERENCE.md
-- SQLite 3 with Write-Ahead Logging (WAL) mode
-- ============================================================================

-- Enable foreign key constraints (must be set per connection)
PRAGMA foreign_keys = ON;

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- 1. VOCABULARY TABLE
-- Central repository for Japanese vocabulary words
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY,
    kanji_form TEXT NOT NULL,
    hiragana_reading TEXT NOT NULL,
    romaji_reading TEXT,
    english_meaning TEXT NOT NULL,
    part_of_speech TEXT,
    jlpt_level TEXT CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1') OR jlpt_level IS NULL),
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

-- 2. KANJI TABLE
-- Individual kanji character database
CREATE TABLE IF NOT EXISTS kanji (
    id INTEGER PRIMARY KEY,
    character TEXT NOT NULL UNIQUE,
    meaning TEXT,
    on_readings TEXT,  -- Comma-separated list
    kun_readings TEXT, -- Comma-separated list
    stroke_count INTEGER CHECK(stroke_count > 0 AND stroke_count <= 30),
    jlpt_level TEXT CHECK(jlpt_level IN ('N5', 'N4', 'N3', 'N2', 'N1') OR jlpt_level IS NULL),
    frequency_rank INTEGER CHECK(frequency_rank > 0 OR frequency_rank IS NULL),
    grade INTEGER CHECK(grade BETWEEN 1 AND 8 OR grade IS NULL),
    radical TEXT,
    radical_number INTEGER CHECK(radical_number BETWEEN 1 AND 214 OR radical_number IS NULL),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. SOURCES TABLE
-- Track learning materials and content sources
CREATE TABLE IF NOT EXISTS sources (
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

-- ============================================================================
-- CONTENT MANAGEMENT
-- ============================================================================

-- 4. SCREENSHOTS TABLE
-- Stores OCR-processed screenshot data
CREATE TABLE IF NOT EXISTS screenshots (
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

-- 5. EXAMPLE SENTENCES TABLE
-- Contextual usage examples for vocabulary
CREATE TABLE IF NOT EXISTS example_sentences (
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

-- ============================================================================
-- LEARNING SYSTEM
-- ============================================================================

-- 6. FLASHCARDS TABLE
-- Implements spaced repetition algorithm (SM-2 based)
CREATE TABLE IF NOT EXISTS flashcards (
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
    difficulty_rating INTEGER CHECK(difficulty_rating BETWEEN 1 AND 5 OR difficulty_rating IS NULL),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE SET NULL
);

-- 7. REVIEW SESSIONS TABLE
-- Detailed history of every flashcard review
CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY,
    flashcard_id INTEGER NOT NULL,
    session_id TEXT,  -- Groups reviews in same study session
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_rating INTEGER NOT NULL CHECK(quality_rating BETWEEN 0 AND 5),
    user_answer TEXT,
    correct BOOLEAN NOT NULL,
    response_time_ms INTEGER CHECK(response_time_ms >= 0 OR response_time_ms IS NULL),
    interval_before_days REAL,
    ease_factor_before REAL,
    ease_factor_after REAL,
    FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
);

-- 8. STUDY GOALS TABLE
-- User-defined learning objectives with progress tracking
CREATE TABLE IF NOT EXISTS study_goals (
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

-- ============================================================================
-- RELATIONSHIP TABLES (JUNCTION TABLES)
-- ============================================================================

-- 9. SCREENSHOT_VOCABULARY TABLE
-- Junction table linking screenshots to extracted vocabulary
CREATE TABLE IF NOT EXISTS screenshot_vocabulary (
    id INTEGER PRIMARY KEY,
    screenshot_id INTEGER NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    position_in_text INTEGER,
    context_snippet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
);

-- 10. VOCABULARY_KANJI TABLE
-- Links vocabulary words to their constituent kanji characters
CREATE TABLE IF NOT EXISTS vocabulary_kanji (
    vocabulary_id INTEGER NOT NULL,
    kanji_id INTEGER NOT NULL,
    position INTEGER,  -- Order within the word
    PRIMARY KEY (vocabulary_id, kanji_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (kanji_id) REFERENCES kanji(id) ON DELETE CASCADE
);

-- 11. TAGS TABLE
-- Reusable tags for flexible categorization
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT,  -- E.g., "grammar", "topic", "difficulty"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. VOCABULARY_TAGS TABLE
-- Junction table for vocabulary tags
CREATE TABLE IF NOT EXISTS vocabulary_tags (
    vocabulary_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (vocabulary_id, tag_id),
    FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ============================================================================
-- UTILITY TABLES
-- ============================================================================

-- 13. MIGRATION BACKUP TABLE
-- Database versioning and migration tracking
CREATE TABLE IF NOT EXISTS _migration_backup (
    id INTEGER PRIMARY KEY,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version TEXT
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Vocabulary indexes
CREATE INDEX IF NOT EXISTS idx_vocabulary_kanji_form ON vocabulary(kanji_form);
CREATE INDEX IF NOT EXISTS idx_vocabulary_study_status ON vocabulary(study_status);
CREATE INDEX IF NOT EXISTS idx_vocabulary_jlpt_level ON vocabulary(jlpt_level);
CREATE INDEX IF NOT EXISTS idx_vocabulary_last_seen_at ON vocabulary(last_seen_at);

-- Kanji indexes
CREATE INDEX IF NOT EXISTS idx_kanji_character ON kanji(character);
CREATE INDEX IF NOT EXISTS idx_kanji_jlpt_level ON kanji(jlpt_level);

-- Sources indexes
CREATE INDEX IF NOT EXISTS idx_sources_is_active ON sources(is_active);
CREATE INDEX IF NOT EXISTS idx_sources_name ON sources(name);

-- Screenshots indexes
CREATE INDEX IF NOT EXISTS idx_screenshots_source_id ON screenshots(source_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_checksum ON screenshots(checksum);
CREATE INDEX IF NOT EXISTS idx_screenshots_processed_at ON screenshots(processed_at);

-- Example sentences indexes
CREATE INDEX IF NOT EXISTS idx_example_sentences_vocabulary_id ON example_sentences(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_example_sentences_source_id ON example_sentences(source_id);

-- Flashcards indexes (CRITICAL FOR PERFORMANCE)
CREATE INDEX IF NOT EXISTS idx_flashcards_next_review_at ON flashcards(next_review_at);
CREATE INDEX IF NOT EXISTS idx_flashcards_status ON flashcards(status);
CREATE INDEX IF NOT EXISTS idx_flashcards_vocabulary_id ON flashcards(vocabulary_id);
-- Composite index for due flashcards query (status + next_review_at)
CREATE INDEX IF NOT EXISTS idx_flashcards_status_next_review ON flashcards(status, next_review_at);

-- Review sessions indexes
CREATE INDEX IF NOT EXISTS idx_review_sessions_flashcard_id ON review_sessions(flashcard_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_session_id ON review_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_reviewed_at ON review_sessions(reviewed_at);

-- Study goals indexes
CREATE INDEX IF NOT EXISTS idx_study_goals_is_active ON study_goals(is_active);

-- Junction table indexes
CREATE INDEX IF NOT EXISTS idx_screenshot_vocabulary_screenshot_id ON screenshot_vocabulary(screenshot_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_vocabulary_vocabulary_id ON screenshot_vocabulary(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_kanji_vocabulary_id ON vocabulary_kanji(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_kanji_kanji_id ON vocabulary_kanji(kanji_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_tags_vocabulary_id ON vocabulary_tags(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_tags_tag_id ON vocabulary_tags(tag_id);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Vocabulary updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_vocabulary_timestamp
AFTER UPDATE ON vocabulary
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE vocabulary SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Kanji updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_kanji_timestamp
AFTER UPDATE ON kanji
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE kanji SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Sources updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_sources_timestamp
AFTER UPDATE ON sources
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE sources SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Screenshots updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_screenshots_timestamp
AFTER UPDATE ON screenshots
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE screenshots SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Flashcards updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_flashcards_timestamp
AFTER UPDATE ON flashcards
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE flashcards SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Study goals updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_study_goals_timestamp
AFTER UPDATE ON study_goals
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at OR NEW.updated_at IS NULL
BEGIN
    UPDATE study_goals SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- INITIAL MIGRATION RECORD
-- ============================================================================

-- Record initial schema version
INSERT INTO _migration_backup (version) VALUES ('2.0 - Full 13-table schema from DATABASE_SCHEMA_REFERENCE.md');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
