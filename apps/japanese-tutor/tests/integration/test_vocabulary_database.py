"""
Integration tests for vocabulary database operations.

Tests all vocabulary management tool functions with real database operations.
"""

import pytest
import os
import tempfile

from japanese_agent.database.connection import (
    get_connection,
    initialize_database,
    close_connection
)
from japanese_agent.tools.vocabulary_manager import (
    search_vocabulary,
    list_vocabulary_by_status,
    update_vocabulary_status,
    get_vocabulary_statistics
)


@pytest.fixture
async def test_db_with_vocab():
    """Create test database with sample vocabulary."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        test_db_path = tmp.name

    original_path = os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = test_db_path

    await initialize_database()
    conn = await get_connection()

    # Insert sample vocabulary
    sample_vocab = [
        ('日本語', 'にほんご', 'nihongo', 'Japanese language', 'noun', 'N5', 'new'),
        ('勉強', 'べんきょう', 'benkyou', 'study', 'noun', 'N5', 'learning'),
        ('難しい', 'むずかしい', 'muzukashii', 'difficult', 'adjective', 'N4', 'reviewing'),
        ('本', 'ほん', 'hon', 'book', 'noun', 'N5', 'mastered'),
        ('猫', 'ねこ', 'neko', 'cat', 'noun', 'N5', 'new'),
    ]

    for kanji, hiragana, romaji, meaning, pos, jlpt, status in sample_vocab:
        await conn.execute(
            """INSERT INTO vocabulary
               (kanji_form, hiragana_reading, romaji_reading, english_meaning,
                part_of_speech, jlpt_level, study_status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (kanji, hiragana, romaji, meaning, pos, jlpt, status)
        )
    await conn.commit()

    yield conn

    await close_connection()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

    if original_path:
        os.environ["DATABASE_PATH"] = original_path
    else:
        os.environ.pop("DATABASE_PATH", None)


@pytest.mark.asyncio
async def test_search_vocabulary_by_japanese(test_db_with_vocab):
    """Test searching vocabulary by Japanese text."""
    results = await search_vocabulary.coroutine("日本")

    assert len(results) > 0, "No results found"
    assert any(r['kanji_form'] == '日本語' for r in results), \
        "Expected vocabulary not found"


@pytest.mark.asyncio
async def test_search_vocabulary_by_english(test_db_with_vocab):
    """Test searching vocabulary by English meaning."""
    results = await search_vocabulary.coroutine("study")

    assert len(results) > 0, "No results found"
    assert any(r['english_meaning'] == 'study' for r in results), \
        "Expected vocabulary not found"


@pytest.mark.asyncio
async def test_list_vocabulary_by_status_new(test_db_with_vocab):
    """Test listing vocabulary with 'new' status."""
    results = await list_vocabulary_by_status.coroutine("new", limit=10)

    assert len(results) == 2, f"Expected 2 new words, got {len(results)}"
    assert all(r['study_status'] == 'new' for r in results), \
        "Some results have wrong status"


@pytest.mark.asyncio
async def test_list_vocabulary_by_status_invalid(test_db_with_vocab):
    """Test that invalid status returns error."""
    results = await list_vocabulary_by_status.coroutine("invalid_status", limit=10)

    assert isinstance(results, list), "Should return list"
    assert len(results) > 0, "Should have error dict"
    assert "error" in results[0], "Should contain error message"


@pytest.mark.asyncio
async def test_update_vocabulary_status_success(test_db_with_vocab):
    """Test successfully updating vocabulary status."""
    # Find a 'new' word
    new_words = await list_vocabulary_by_status.coroutine("new", limit=1)
    assert len(new_words) > 0, "No new words found"

    vocab_id = new_words[0]['id']

    # Update to 'learning'
    result = await update_vocabulary_status.coroutine(vocab_id, "learning")

    assert result.get('success') is True, f"Update failed: {result}"
    assert result['study_status'] == 'learning', "Status not updated"
    assert 'updated_at' in result, "updated_at not returned"


@pytest.mark.asyncio
async def test_update_vocabulary_status_not_found(test_db_with_vocab):
    """Test updating non-existent vocabulary ID."""
    result = await update_vocabulary_status.coroutine(9999, "learning")

    assert result.get('success') is False, "Should fail for non-existent ID"
    assert 'error' in result, "Should contain error message"


@pytest.mark.asyncio
async def test_get_vocabulary_statistics(test_db_with_vocab):
    """Test getting vocabulary statistics."""
    stats = await get_vocabulary_statistics.coroutine()

    assert stats['total_words'] == 5, f"Expected 5 total words, got {stats['total_words']}"
    assert stats['new_words'] == 2, f"Expected 2 new words, got {stats['new_words']}"
    assert stats['learning_words'] == 1, f"Expected 1 learning word, got {stats['learning_words']}"
    assert stats['reviewing_words'] == 1, f"Expected 1 reviewing word, got {stats['reviewing_words']}"
    assert stats['mastered_words'] == 1, f"Expected 1 mastered word, got {stats['mastered_words']}"
    assert stats['total_encounters'] >= 5, "Encounter count should be at least 5"


@pytest.mark.asyncio
async def test_search_vocabulary_ordering(test_db_with_vocab):
    """Test that search results are ordered by encounter_count and last_seen_at."""
    # Update encounter counts
    conn = await get_connection()
    await conn.execute("UPDATE vocabulary SET encounter_count = 10 WHERE kanji_form = '本'")
    await conn.execute("UPDATE vocabulary SET encounter_count = 5 WHERE kanji_form = '猫'")
    await conn.commit()

    results = await search_vocabulary.coroutine("")  # Search all

    # First result should have highest encounter count
    if len(results) >= 2:
        assert results[0]['encounter_count'] >= results[1]['encounter_count'], \
            "Results not properly ordered by encounter_count"
