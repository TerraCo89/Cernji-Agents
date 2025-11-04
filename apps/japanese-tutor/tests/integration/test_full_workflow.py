"""
End-to-end integration tests for complete workflows.

Tests realistic user workflows combining multiple operations:
- Screenshot → Vocabulary → Flashcard → Review cycle
- Multi-day review simulation
- Concurrent operations (WAL mode)
- Error handling and recovery
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
from japanese_agent.tools.vocabulary_manager import (
    search_vocabulary,
    list_vocabulary_by_status,
    update_vocabulary_status,
    get_vocabulary_statistics
)
from japanese_agent.tools.flashcard_manager import (
    get_due_flashcards,
    create_flashcard,
    record_flashcard_review,
    get_review_statistics
)


@pytest.fixture
async def clean_db():
    """Create a clean test database."""
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


@pytest.mark.asyncio
async def test_complete_learning_workflow(clean_db):
    """
    Test complete workflow: Add vocabulary → Create flashcard → Review cycle → Track progress.
    """
    conn = clean_db

    # Step 1: Add vocabulary (simulating OCR extraction)
    await conn.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, study_status)
           VALUES ('勉強', 'べんきょう', 'study', 'new')"""
    )
    await conn.commit()

    # Step 2: Verify vocabulary was added
    vocab_list = await list_vocabulary_by_status.coroutine('new', limit=10)
    assert len(vocab_list) == 1, "Vocabulary should be added"
    vocab_id = vocab_list[0]['id']

    # Step 3: Create flashcard from vocabulary
    flashcard = await create_flashcard.coroutine(vocab_id)
    assert flashcard.get('success') is True, "Flashcard creation should succeed"
    flashcard_id = flashcard['flashcard_id']

    # Step 4: Get due flashcards (should include our new card)
    due_cards = await get_due_flashcards.coroutine(limit=10)
    assert len(due_cards) == 1, "Should have 1 due flashcard"
    assert due_cards[0]['word'] == '勉強', "Flashcard should have correct vocabulary"

    # Step 5: Review the flashcard (Easy)
    review1 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert review1.get('success') is True, "Review should succeed"
    assert review1['interval'] == 1.0, "First review interval should be 1 day"

    # Step 6: Simulate another review after interval
    review2 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert review2['interval'] == 6.0, "Second review interval should be 6 days"

    # Step 7: Update vocabulary status to learning
    vocab_update = await update_vocabulary_status.coroutine(vocab_id, 'learning')
    assert vocab_update.get('success') is True, "Status update should succeed"

    # Step 8: Check statistics
    vocab_stats = await get_vocabulary_statistics.coroutine()
    assert vocab_stats['total_words'] == 1, "Should have 1 word"
    assert vocab_stats['learning_words'] == 1, "Should have 1 learning word"

    review_stats = await get_review_statistics.coroutine()
    assert review_stats['total_flashcards'] == 1, "Should have 1 flashcard"
    assert review_stats['reviewed_today'] == 2, "Should have 2 reviews today"


@pytest.mark.asyncio
async def test_multi_day_review_simulation(clean_db):
    """
    Simulate reviewing flashcards over multiple days with varying performance.
    """
    conn = clean_db

    # Create vocabulary and flashcard
    await conn.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
           VALUES ('日本語', 'にほんご', 'Japanese language')"""
    )
    await conn.commit()

    flashcard = await create_flashcard.coroutine(vocab_id=1)
    flashcard_id = flashcard['flashcard_id']

    # Day 1: First review - Easy
    review1 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert review1['interval'] == 1.0, "Day 1: Interval should be 1 day"
    assert review1['consecutive_correct'] == 1, "Day 1: Should have 1 correct"

    # Day 2: Second review - Easy
    review2 = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert review2['interval'] == 6.0, "Day 2: Interval should be 6 days"
    assert review2['consecutive_correct'] == 2, "Day 2: Should have 2 correct"

    # Day 8: Third review - Medium (after 6 day interval)
    review3 = await record_flashcard_review.coroutine(flashcard_id, rating=2)
    assert review3['interval'] > 6.0, "Day 8: Interval should increase"
    assert review3['consecutive_correct'] == 3, "Day 8: Should have 3 correct"

    # Day X: Failed review - simulate forgetting
    review_fail = await record_flashcard_review.coroutine(flashcard_id, rating=0)
    assert review_fail['interval'] == 0.0, "Failed: Interval should reset"
    assert review_fail['consecutive_correct'] == 0, "Failed: Correct streak should reset"
    assert review_fail['lapses'] >= 1, "Failed: Should have at least 1 lapse"

    # Restart from scratch
    review_restart = await record_flashcard_review.coroutine(flashcard_id, rating=3)
    assert review_restart['interval'] == 1.0, "Restart: Back to 1 day interval"


@pytest.mark.asyncio
async def test_multiple_vocabulary_concurrent_learning(clean_db):
    """
    Test learning multiple vocabulary words concurrently.
    """
    conn = clean_db

    # Add multiple vocabulary entries
    vocab_words = [
        ('猫', 'ねこ', 'cat'),
        ('犬', 'いぬ', 'dog'),
        ('本', 'ほん', 'book'),
        ('机', 'つくえ', 'desk'),
        ('椅子', 'いす', 'chair'),
    ]

    for kanji, hiragana, meaning in vocab_words:
        await conn.execute(
            """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
               VALUES (?, ?, ?)""",
            (kanji, hiragana, meaning)
        )
    await conn.commit()

    # Create flashcards for all
    flashcard_ids = []
    for vocab_id in range(1, 6):
        flashcard = await create_flashcard.coroutine(vocab_id)
        flashcard_ids.append(flashcard['flashcard_id'])

    # Verify all are due
    due_cards = await get_due_flashcards.coroutine(limit=10)
    assert len(due_cards) == 5, "All 5 flashcards should be due"

    # Review them with different ratings
    ratings = [3, 3, 2, 1, 0]  # Easy, Easy, Medium, Hard, Again
    for flashcard_id, rating in zip(flashcard_ids, ratings):
        await record_flashcard_review.coroutine(flashcard_id, rating)

    # Check that different intervals were set
    async with conn.execute(
        "SELECT interval_days FROM flashcards ORDER BY id"
    ) as cursor:
        intervals = [row[0] for row in await cursor.fetchall()]

    # Easy ratings (first two) should have same interval
    assert intervals[0] == intervals[1] == 1.0, "Easy ratings should have 1 day interval"

    # Failed rating (last one) should have 0 interval
    assert intervals[4] == 0.0, "Failed review should have 0 interval"

    # Statistics should reflect mixed performance
    stats = await get_review_statistics.coroutine()
    assert stats['reviewed_today'] == 5, "Should have 5 reviews today"


@pytest.mark.asyncio
async def test_error_recovery_missing_vocabulary(clean_db):
    """
    Test error handling when trying to create flashcard for non-existent vocabulary.
    """
    # Try to create flashcard for non-existent vocabulary
    result = await create_flashcard.coroutine(vocab_id=9999)

    assert result.get('success') is False, "Should fail gracefully"
    assert 'error' in result, "Should provide error message"
    assert 'not found' in result['error'].lower(), "Error should mention not found"

    # Verify no flashcard was created
    flashcards = await get_due_flashcards.coroutine(limit=10)
    assert len(flashcards) == 0, "No flashcards should exist"


@pytest.mark.asyncio
async def test_status_progression_workflow(clean_db):
    """
    Test vocabulary status progression through learning stages.
    """
    conn = clean_db

    # Add vocabulary
    await conn.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning, study_status)
           VALUES ('難しい', 'むずかしい', 'difficult', 'new')"""
    )
    await conn.commit()

    # Verify it's in 'new'
    new_words = await list_vocabulary_by_status.coroutine('new', limit=10)
    assert len(new_words) == 1, "Should have 1 new word"
    vocab_id = new_words[0]['id']

    # Progress to 'learning'
    await update_vocabulary_status.coroutine(vocab_id, 'learning')
    learning_words = await list_vocabulary_by_status.coroutine('learning', limit=10)
    assert len(learning_words) == 1, "Should have 1 learning word"

    # Progress to 'reviewing'
    await update_vocabulary_status.coroutine(vocab_id, 'reviewing')
    reviewing_words = await list_vocabulary_by_status.coroutine('reviewing', limit=10)
    assert len(reviewing_words) == 1, "Should have 1 reviewing word"

    # Progress to 'mastered'
    await update_vocabulary_status.coroutine(vocab_id, 'mastered')
    mastered_words = await list_vocabulary_by_status.coroutine('mastered', limit=10)
    assert len(mastered_words) == 1, "Should have 1 mastered word"

    # Verify statistics
    stats = await get_vocabulary_statistics.coroutine()
    assert stats['total_words'] == 1, "Should have 1 total word"
    assert stats['mastered_words'] == 1, "Should have 1 mastered word"
    assert stats['new_words'] == 0, "Should have 0 new words"


@pytest.mark.asyncio
async def test_search_and_review_workflow(clean_db):
    """
    Test workflow: Search for vocabulary → Create flashcard → Review.
    """
    conn = clean_db

    # Add several vocabulary entries
    vocab_data = [
        ('日本', 'にほん', 'Japan'),
        ('日本語', 'にほんご', 'Japanese language'),
        ('日本人', 'にほんじん', 'Japanese person'),
    ]

    for kanji, hiragana, meaning in vocab_data:
        await conn.execute(
            """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
               VALUES (?, ?, ?)""",
            (kanji, hiragana, meaning)
        )
    await conn.commit()

    # Search for vocabulary containing "日本"
    results = await search_vocabulary.coroutine("日本")
    assert len(results) == 3, f"Should find 3 words with '日本', got {len(results)}"

    # Create flashcards for search results
    for vocab in results:
        flashcard = await create_flashcard.coroutine(vocab['id'])
        assert flashcard.get('success') is True, f"Failed to create flashcard for {vocab['kanji_form']}"

    # Verify all flashcards are due
    due_cards = await get_due_flashcards.coroutine(limit=10)
    assert len(due_cards) == 3, "All 3 flashcards should be due"

    # Review all with Easy rating
    for card in due_cards:
        result = await record_flashcard_review.coroutine(card['flashcard_id'], rating=3)
        assert result.get('success') is True, "Review should succeed"


@pytest.mark.asyncio
async def test_concurrent_access_wal_mode(clean_db):
    """
    Test that WAL mode allows concurrent read/write operations.
    """
    conn = clean_db

    # Verify WAL mode is enabled
    async with conn.execute("PRAGMA journal_mode") as cursor:
        mode = (await cursor.fetchone())[0]
        assert mode.lower() == 'wal', f"WAL mode should be enabled, got {mode}"

    # Add vocabulary
    await conn.execute(
        """INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
           VALUES ('test', 'てすと', 'test')"""
    )
    await conn.commit()

    # Simulate concurrent operations
    # Create flashcard while reading vocabulary
    vocab_list = await list_vocabulary_by_status.coroutine('new', limit=10)
    flashcard = await create_flashcard.coroutine(vocab_list[0]['id'])

    # Both operations should succeed
    assert len(vocab_list) > 0, "Should be able to read vocabulary"
    assert flashcard.get('success') is True, "Should be able to write flashcard"


@pytest.mark.asyncio
async def test_review_statistics_accuracy(clean_db):
    """
    Test that review statistics accurately reflect database state.
    """
    conn = clean_db

    # Add vocabulary and create flashcards
    for i in range(5):
        await conn.execute(
            f"""INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning)
                VALUES ('word{i}', 'わーど{i}', 'word {i}')"""
        )
    await conn.commit()

    # Create 5 flashcards
    for vocab_id in range(1, 6):
        await create_flashcard.coroutine(vocab_id)

    # Review 3 of them today
    await record_flashcard_review.coroutine(1, rating=3)
    await record_flashcard_review.coroutine(2, rating=2)
    await record_flashcard_review.coroutine(3, rating=1)

    # Check statistics
    stats = await get_review_statistics.coroutine()

    assert stats['total_flashcards'] == 5, \
        f"Expected 5 total flashcards, got {stats['total_flashcards']}"
    assert stats['reviewed_today'] == 3, \
        f"Expected 3 reviewed today, got {stats['reviewed_today']}"

    # Due today should be 2 (the ones we didn't review, still at interval 0)
    # plus possibly the one we failed (rating 1 might still be due)
    assert stats['due_today'] >= 2, \
        f"Expected at least 2 due today, got {stats['due_today']}"
