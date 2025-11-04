"""
Integration tests for database setup and schema validation.

Tests database initialization, table creation, indexes, triggers,
and constraint enforcement.
"""

import pytest
import aiosqlite
import os
from pathlib import Path
import tempfile

from japanese_agent.database.connection import (
    get_connection,
    initialize_database,
    close_connection,
    get_database_path
)


@pytest.fixture
async def test_db():
    """Create a temporary test database."""
    # Use a temporary database for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        test_db_path = tmp.name

    # Set env var to use test database
    original_path = os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = test_db_path

    # Initialize database
    await initialize_database()

    yield await get_connection()

    # Cleanup
    await close_connection()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

    # Restore original env var
    if original_path:
        os.environ["DATABASE_PATH"] = original_path
    else:
        os.environ.pop("DATABASE_PATH", None)


@pytest.mark.asyncio
async def test_database_creation(test_db):
    """Test that database file is created."""
    db_path = get_database_path()
    assert os.path.exists(db_path), f"Database file not created at {db_path}"


@pytest.mark.asyncio
async def test_all_tables_exist(test_db):
    """Test that all 13 tables are created."""
    expected_tables = {
        "vocabulary",
        "kanji",
        "sources",
        "screenshots",
        "example_sentences",
        "flashcards",
        "review_sessions",
        "study_goals",
        "screenshot_vocabulary",
        "vocabulary_kanji",
        "tags",
        "vocabulary_tags",
        "_migration_backup",
    }

    async with test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cursor:
        rows = await cursor.fetchall()
        actual_tables = {row["name"] for row in rows}

    assert expected_tables.issubset(actual_tables), \
        f"Missing tables: {expected_tables - actual_tables}"


@pytest.mark.asyncio
async def test_indexes_exist(test_db):
    """Test that critical indexes are created."""
    # Check for some key indexes
    critical_indexes = [
        "idx_vocabulary_kanji_form",
        "idx_vocabulary_study_status",
        "idx_flashcards_status_next_review",  # Composite index for due cards
        "idx_flashcards_vocabulary_id",
        "idx_review_sessions_flashcard_id",
    ]

    async with test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ) as cursor:
        rows = await cursor.fetchall()
        actual_indexes = {row["name"] for row in rows if row["name"]}

    for index in critical_indexes:
        assert index in actual_indexes, f"Missing critical index: {index}"


@pytest.mark.asyncio
async def test_triggers_exist(test_db):
    """Test that automatic timestamp triggers are created."""
    expected_triggers = [
        "update_vocabulary_timestamp",
        "update_kanji_timestamp",
        "update_sources_timestamp",
        "update_screenshots_timestamp",
        "update_flashcards_timestamp",
        "update_study_goals_timestamp",
    ]

    async with test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    ) as cursor:
        rows = await cursor.fetchall()
        actual_triggers = {row["name"] for row in rows}

    for trigger in expected_triggers:
        assert trigger in actual_triggers, f"Missing trigger: {trigger}"


@pytest.mark.asyncio
async def test_wal_mode_enabled(test_db):
    """Test that WAL (Write-Ahead Logging) mode is enabled."""
    async with test_db.execute("PRAGMA journal_mode") as cursor:
        result = await cursor.fetchone()
        assert result[0].lower() == "wal", \
            f"WAL mode not enabled. Current mode: {result[0]}"


@pytest.mark.asyncio
async def test_foreign_keys_enabled(test_db):
    """Test that foreign key constraints are enabled."""
    async with test_db.execute("PRAGMA foreign_keys") as cursor:
        result = await cursor.fetchone()
        assert result[0] == 1, "Foreign keys not enabled"


@pytest.mark.asyncio
async def test_check_constraint_study_status(test_db):
    """Test that CHECK constraint on study_status works."""
    # Valid status should work
    await test_db.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, study_status)
           VALUES ('test', 'てすと', 'test', 'new')"""
    )
    await test_db.commit()

    # Invalid status should fail
    with pytest.raises(aiosqlite.IntegrityError):
        await test_db.execute(
            """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, study_status)
               VALUES ('test2', 'てすと2', 'test2', 'invalid_status')"""
        )
        await test_db.commit()


@pytest.mark.asyncio
async def test_check_constraint_jlpt_level(test_db):
    """Test that CHECK constraint on jlpt_level works."""
    # Valid JLPT level should work
    await test_db.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, jlpt_level)
           VALUES ('test', 'てすと', 'test', 'N5')"""
    )
    await test_db.commit()

    # Invalid JLPT level should fail
    with pytest.raises(aiosqlite.IntegrityError):
        await test_db.execute(
            """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, jlpt_level)
               VALUES ('test2', 'てすと2', 'test2', 'N6')"""
        )
        await test_db.commit()


@pytest.mark.asyncio
async def test_check_constraint_ease_factor(test_db):
    """Test that CHECK constraint on ease_factor (min 1.3) works."""
    # First create a vocabulary entry
    await test_db.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
           VALUES ('test', 'てすと', 'test')"""
    )
    await test_db.commit()

    # Valid ease factor should work
    await test_db.execute(
        """INSERT INTO flashcards (vocabulary_id, ease_factor, next_review_at)
           VALUES (1, 2.5, datetime('now'))"""
    )
    await test_db.commit()

    # Invalid ease factor (below 1.3) should fail
    with pytest.raises(aiosqlite.IntegrityError):
        await test_db.execute(
            """INSERT INTO flashcards (vocabulary_id, ease_factor, next_review_at)
               VALUES (1, 1.2, datetime('now'))"""
        )
        await test_db.commit()


@pytest.mark.asyncio
async def test_foreign_key_cascade_delete(test_db):
    """Test that foreign key CASCADE delete works."""
    # Create vocabulary
    await test_db.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
           VALUES ('test', 'てすと', 'test')"""
    )
    await test_db.commit()

    # Create flashcard referencing vocabulary
    await test_db.execute(
        """INSERT INTO flashcards (vocabulary_id, next_review_at)
           VALUES (1, datetime('now'))"""
    )
    await test_db.commit()

    # Verify flashcard exists
    async with test_db.execute("SELECT COUNT(*) FROM flashcards") as cursor:
        result = await cursor.fetchone()
        assert result[0] == 1, "Flashcard not created"

    # Delete vocabulary (should cascade to flashcards)
    await test_db.execute("DELETE FROM vocabulary WHERE id = 1")
    await test_db.commit()

    # Verify flashcard was deleted
    async with test_db.execute("SELECT COUNT(*) FROM flashcards") as cursor:
        result = await cursor.fetchone()
        assert result[0] == 0, "Flashcard not deleted on cascade"


@pytest.mark.asyncio
async def test_updated_at_trigger(test_db):
    """Test that updated_at timestamp trigger works."""
    # Create vocabulary
    await test_db.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
           VALUES ('test', 'てすと', 'test')"""
    )
    await test_db.commit()

    # Get initial updated_at
    async with test_db.execute(
        "SELECT updated_at FROM vocabulary WHERE id = 1"
    ) as cursor:
        initial_time = (await cursor.fetchone())[0]

    # Wait a moment (SQLite CURRENT_TIMESTAMP has second precision)
    import asyncio
    await asyncio.sleep(1.1)

    # Update the record
    await test_db.execute(
        "UPDATE vocabulary SET kanji_form = 'updated' WHERE id = 1"
    )
    await test_db.commit()

    # Get new updated_at
    async with test_db.execute(
        "SELECT updated_at FROM vocabulary WHERE id = 1"
    ) as cursor:
        new_time = (await cursor.fetchone())[0]

    # Verify timestamp was updated
    assert new_time > initial_time, \
        f"updated_at not updated by trigger. Initial: {initial_time}, New: {new_time}"


@pytest.mark.asyncio
async def test_migration_backup_record(test_db):
    """Test that initial migration record exists."""
    async with test_db.execute(
        "SELECT version FROM _migration_backup ORDER BY id DESC LIMIT 1"
    ) as cursor:
        result = await cursor.fetchone()
        assert result is not None, "No migration backup record found"
        assert "2.0" in result[0], f"Unexpected version: {result[0]}"
