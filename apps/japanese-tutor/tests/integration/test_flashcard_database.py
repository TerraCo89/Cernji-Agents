"""
Integration tests for flashcard database operations and SM-2 algorithm.

Tests flashcard creation, due card queries, SM-2 spaced repetition algorithm,
review recording, and statistics calculation.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from japanese_agent.database.connection import (
    get_connection,
    initialize_database,
    close_connection
)
from japanese_agent.tools.flashcard_manager import (
    get_due_flashcards,
    create_flashcard,
    record_flashcard_review,
    get_review_statistics,
    _calculate_sm2_next_interval
)


@pytest.fixture
async def test_db_with_flashcards():
    """Create test database with vocabulary and flashcards."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        test_db_path = tmp.name

    original_path = os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = test_db_path

    await initialize_database()
    conn = await get_connection()

    # Insert sample vocabulary
    vocab_data = [
        ('日本語', 'にほんご', 'Japanese language'),
        ('勉強', 'べんきょう', 'study'),
        ('本', 'ほん', 'book'),
    ]

    for kanji, hiragana, meaning in vocab_data:
        await conn.execute(
            """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
               VALUES (?, ?, ?)""",
            (kanji, hiragana, meaning)
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
async def test_create_flashcard_success(test_db_with_flashcards):
    """Test creating a flashcard from vocabulary."""
    result = await create_flashcard.coroutine(vocab_id=1)

    assert result.get('success') is True, f"Flashcard creation failed: {result}"
    assert result['vocab_id'] == 1, "Wrong vocabulary ID"
    assert result['ease_factor'] == 2.5, "Default ease factor should be 2.5"
    assert result['interval'] == 0.0, "Initial interval should be 0.0"
    assert result['review_count'] == 0, "Initial review count should be 0"
    assert result['status'] == 'active', "Status should be 'active'"
    assert result['card_type'] == 'recognition', "Default card type should be 'recognition'"


@pytest.mark.asyncio
async def test_create_flashcard_invalid_vocab(test_db_with_flashcards):
    """Test creating flashcard with non-existent vocabulary ID."""
    result = await create_flashcard.coroutine(vocab_id=9999)

    assert result.get('success') is False, "Should fail for invalid vocab_id"
    assert 'error' in result, "Should contain error message"


@pytest.mark.asyncio
async def test_get_due_flashcards_empty(test_db_with_flashcards):
    """Test getting due flashcards when none exist."""
    results = await get_due_flashcards.coroutine(limit=10)

    assert isinstance(results, list), "Should return list"
    assert len(results) == 0, "Should have no due cards"


@pytest.mark.asyncio
async def test_get_due_flashcards_with_due_cards(test_db_with_flashcards):
    """Test getting due flashcards."""
    conn = await get_connection()

    # Create flashcards with next_review_at in the past
    past_time = (datetime.now() - timedelta(days=1)).isoformat()

    await conn.execute(
        """INSERT INTO flashcards (vocabulary_id, next_review_at, interval_days)
           VALUES (1, ?, 0.0)""",
        (past_time,)
    )
    await conn.execute(
        """INSERT INTO flashcards (vocabulary_id, next_review_at, interval_days)
           VALUES (2, ?, 0.0)""",
        (past_time,)
    )
    await conn.commit()

    results = await get_due_flashcards.coroutine(limit=10)

    assert len(results) == 2, f"Expected 2 due cards, got {len(results)}"
    assert all('flashcard_id' in r for r in results), "Missing flashcard_id"
    assert all('word' in r for r in results), "Missing word from vocabulary"


@pytest.mark.asyncio
async def test_get_due_flashcards_excludes_future(test_db_with_flashcards):
    """Test that future flashcards are not included in due cards."""
    conn = await get_connection()

    # Create one due card and one future card
    past_time = (datetime.now() - timedelta(days=1)).isoformat()
    future_time = (datetime.now() + timedelta(days=1)).isoformat()

    await conn.execute(
        """INSERT INTO flashcards (vocabulary_id, next_review_at, interval_days)
           VALUES (1, ?, 0.0)""",
        (past_time,)
    )
    await conn.execute(
        """INSERT INTO flashcards (vocabulary_id, next_review_at, interval_days)
           VALUES (2, ?, 1.0)""",
        (future_time,)
    )
    await conn.commit()

    results = await get_due_flashcards.coroutine(limit=10)

    assert len(results) == 1, f"Expected only 1 due card, got {len(results)}"


@pytest.mark.asyncio
async def test_sm2_algorithm_rating_0_resets(test_db_with_flashcards):
    """Test that rating 0 (Again) resets interval and increments lapses."""
    # Create flashcard with some progress
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    # Simulate some successful reviews first
    await record_flashcard_review.coroutine(flashcard_id, rating=3)  # Easy
    await record_flashcard_review.coroutine(flashcard_id, rating=3)  # Easy

    # Now fail it
    result = await record_flashcard_review.coroutine(flashcard_id, rating=0)

    assert result.get('success') is True, "Review recording failed"
    assert result['interval'] == 0.0, "Interval should reset to 0"
    assert result['consecutive_correct'] == 0, "Consecutive correct should reset"
    assert result['lapses'] >= 1, "Lapses should increment"


@pytest.mark.asyncio
async def test_sm2_algorithm_rating_3_progression(test_db_with_flashcards):
    """Test SM-2 algorithm interval progression with Easy ratings."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    # First review - should go to 1 day
    result1 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert result1['interval'] == 1.0, f"First interval should be 1.0, got {result1['interval']}"
    assert result1['consecutive_correct'] == 1, "Should have 1 consecutive correct"

    # Second review - should go to 6 days
    result2 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert result2['interval'] == 6.0, f"Second interval should be 6.0, got {result2['interval']}"
    assert result2['consecutive_correct'] == 2, "Should have 2 consecutive correct"

    # Third review - should multiply by ease factor
    result3 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    expected_interval = 6.0 * result3['ease_factor']
    assert abs(result3['interval'] - expected_interval) < 0.1, \
        f"Third interval should be ~{expected_interval}, got {result3['interval']}"


@pytest.mark.asyncio
async def test_sm2_ease_factor_adjustment(test_db_with_flashcards):
    """Test that ease factor adjusts based on ratings."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    initial_ease = flashcard['ease_factor']  # 2.5

    # Easy rating should increase ease
    await record_flashcard_review.coroutine(flashcard_id, rating=3)
    result = await record_flashcard_review.coroutine(flashcard_id, rating=3)

    assert result['ease_factor'] >= initial_ease, \
        f"Ease factor should increase with easy ratings. Was {initial_ease}, now {result['ease_factor']}"


@pytest.mark.asyncio
async def test_sm2_ease_factor_minimum(test_db_with_flashcards):
    """Test that ease factor doesn't go below 1.3."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    # Multiple hard ratings should decrease ease but not below 1.3
    for _ in range(10):
        await record_flashcard_review.coroutine(flashcard_id, rating=1)  # Hard

    result = await record_flashcard_review.coroutine(flashcard_id, rating=1)

    assert result['ease_factor'] >= 1.3, \
        f"Ease factor should not go below 1.3, got {result['ease_factor']}"


@pytest.mark.asyncio
async def test_review_session_created(test_db_with_flashcards):
    """Test that review sessions are recorded."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    await record_flashcard_review.coroutine(flashcard_id, rating=2)

    # Check that review session was created
    conn = await get_connection()
    async with conn.execute(
        "SELECT * FROM review_sessions WHERE flashcard_id = ?",
        (flashcard_id,)
    ) as cursor:
        sessions = await cursor.fetchall()

    assert len(sessions) == 1, "Review session should be created"
    session = dict(sessions[0])
    assert session['quality_rating'] == 4, "Rating 2 should map to quality 4"
    assert session['correct'] == 1, "Should be marked as correct"


@pytest.mark.asyncio
async def test_review_count_increments(test_db_with_flashcards):
    """Test that review_count increments with each review."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    assert flashcard['review_count'] == 0, "Initial review count should be 0"

    result1 = await record_flashcard_review.coroutine(flashcard_id, rating=2)
    assert result1['review_count'] == 1, "Review count should be 1"

    result2 = await record_flashcard_review.coroutine(flashcard_id, rating=2)
    assert result2['review_count'] == 2, "Review count should be 2"


@pytest.mark.asyncio
async def test_invalid_rating_rejected(test_db_with_flashcards):
    """Test that invalid ratings are rejected."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    result = await record_flashcard_review.coroutine(flashcard_id, rating=5)

    assert result.get('success') is False, "Invalid rating should be rejected"
    assert 'error' in result, "Should contain error message"


@pytest.mark.asyncio
async def test_get_review_statistics_empty(test_db_with_flashcards):
    """Test statistics with no flashcards."""
    stats = await get_review_statistics.coroutine()

    assert stats['total_flashcards'] == 0, "Should have 0 total flashcards"
    assert stats['due_today'] == 0, "Should have 0 due today"
    assert stats['reviewed_today'] == 0, "Should have 0 reviewed today"
    assert stats['average_ease'] == 2.5, "Default average ease should be 2.5"


@pytest.mark.asyncio
async def test_get_review_statistics_with_data(test_db_with_flashcards):
    """Test statistics with flashcards and reviews."""
    # Create flashcards
    flashcard1 = await create_flashcard.coroutine(vocab_id=1)
    flashcard2 = await create_flashcard.coroutine(vocab_id=2)
    flashcard3 = await create_flashcard.coroutine(vocab_id=3)

    # Review some today
    await record_flashcard_review.coroutine(flashcard1['flashcard_id'], rating=3)
    await record_flashcard_review.coroutine(flashcard2['flashcard_id'], rating=2)

    stats = await get_review_statistics.coroutine()

    assert stats['total_flashcards'] == 3, f"Expected 3 flashcards, got {stats['total_flashcards']}"
    assert stats['reviewed_today'] == 2, f"Expected 2 reviewed today, got {stats['reviewed_today']}"
    assert stats['average_ease'] > 0, "Average ease should be calculated"


@pytest.mark.asyncio
async def test_calculate_sm2_next_interval_unit():
    """Unit test for SM-2 interval calculation function."""
    # Test first review (repetitions=0) with easy rating
    interval, ease, reps = _calculate_sm2_next_interval(
        rating=3,  # Easy
        current_ease=2.5,
        current_interval=0.0,
        repetitions=0
    )

    assert interval == 1.0, f"First interval should be 1.0, got {interval}"
    assert reps == 1, f"Repetitions should be 1, got {reps}"
    assert ease > 2.5, f"Ease should increase with easy rating, got {ease}"

    # Test second review (repetitions=1) with easy rating
    interval2, ease2, reps2 = _calculate_sm2_next_interval(
        rating=3,
        current_ease=ease,
        current_interval=1.0,
        repetitions=1
    )

    assert interval2 == 6.0, f"Second interval should be 6.0, got {interval2}"
    assert reps2 == 2, f"Repetitions should be 2, got {reps2}"

    # Test failure (rating=0)
    interval3, ease3, reps3 = _calculate_sm2_next_interval(
        rating=0,
        current_ease=2.5,
        current_interval=6.0,
        repetitions=2
    )

    assert interval3 == 0.0, f"Failed review should reset interval to 0, got {interval3}"
    assert reps3 == 0, f"Failed review should reset repetitions to 0, got {reps3}"


@pytest.mark.asyncio
async def test_next_review_date_calculation(test_db_with_flashcards):
    """Test that next_review_at is correctly calculated from interval."""
    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    before_review = datetime.now()
    result = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    after_review = datetime.now()

    # Parse next_review timestamp
    next_review = datetime.fromisoformat(result['next_review'])

    # Expected: now + 1 day (first review with rating 3)
    expected_min = before_review + timedelta(days=1)
    expected_max = after_review + timedelta(days=1, seconds=1)

    assert expected_min <= next_review <= expected_max, \
        f"next_review_at not correctly calculated. Got {next_review}, expected between {expected_min} and {expected_max}"


@pytest.mark.asyncio
async def test_flashcard_ordering_by_due_date(test_db_with_flashcards):
    """Test that due flashcards are returned in order of next_review_at."""
    conn = await get_connection()

    # Create flashcards with different due dates
    times = [
        (datetime.now() - timedelta(days=3)).isoformat(),
        (datetime.now() - timedelta(days=1)).isoformat(),
        (datetime.now() - timedelta(days=2)).isoformat(),
    ]

    for i, time in enumerate(times, 1):
        await conn.execute(
            """INSERT INTO flashcards (vocabulary_id, next_review_at, interval_days)
               VALUES (?, ?, 0.0)""",
            (i, time)
        )
    await conn.commit()

    results = await get_due_flashcards.coroutine(limit=10)

    # Should be ordered by next_review_at (oldest first)
    assert len(results) == 3, "Should return all 3 due cards"

    # Verify ordering
    for i in range(len(results) - 1):
        current = datetime.fromisoformat(results[i]['next_review'])
        next_card = datetime.fromisoformat(results[i + 1]['next_review'])
        assert current <= next_card, f"Cards not properly ordered. {current} should be <= {next_card}"
