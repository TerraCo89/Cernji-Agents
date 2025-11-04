#!/usr/bin/env python3
"""Script to update flashcard_manager.py with database implementation and SM-2 algorithm."""

import os

CONTENT = '''"""
Flashcard management tools for Japanese Learning Agent.

Implements SM-2 spaced repetition algorithm for optimal learning.
All functions use async SQLite database operations.
"""

from typing import Dict, Any, List, Literal
from datetime import datetime, timedelta
from langchain_core.tools import tool
from japanese_agent.database.connection import get_connection


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert aiosqlite.Row to dictionary."""
    if row is None:
        return {}
    return dict(row)


def _calculate_sm2_next_interval(
    rating: Literal[0, 1, 2, 3],
    current_ease: float,
    current_interval: float,
    repetitions: int
) -> tuple[float, float, int]:
    """
    Calculate next interval using SM-2 algorithm.

    Rating scale (user input 0-3 maps to quality 0-5):
        0 = Again (didn't remember) → quality 0
        1 = Hard (struggled) → quality 3
        2 = Medium (some effort) → quality 4
        3 = Easy (easily) → quality 5

    Args:
        rating: User rating (0-3)
        current_ease: Current ease factor
        current_interval: Current interval in days
        repetitions: Current repetition count

    Returns:
        Tuple of (new_interval_days, new_ease_factor, new_repetitions)
    """
    # Map rating 0-3 to quality 0-5
    quality_map = {0: 0, 1: 3, 2: 4, 3: 5}
    quality = quality_map.get(rating, 3)

    # Calculate new ease factor
    # Formula: EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
    new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Clamp ease factor to minimum 1.3
    new_ease = max(new_ease, 1.3)

    # Calculate interval and repetitions based on quality
    if quality < 3:
        # Failed review - reset
        new_interval = 0.0
        new_repetitions = 0
    else:
        # Successful review - increase interval
        if repetitions == 0:
            # First successful review
            new_interval = 1.0
        elif repetitions == 1:
            # Second successful review
            new_interval = 6.0
        else:
            # Subsequent reviews: multiply by ease factor
            new_interval = current_interval * new_ease

        new_repetitions = repetitions + 1

    return new_interval, new_ease, new_repetitions


@tool
async def get_due_flashcards(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get flashcards that are due for review.

    Uses composite index on (status, next_review_at) for optimal performance.

    Args:
        limit: Maximum number of flashcards to return (default: 10)

    Returns:
        List of flashcard dictionaries containing:
            - flashcard_id: Flashcard ID
            - vocab_id: Associated vocabulary ID
            - word: Japanese word (kanji_form)
            - reading: Hiragana reading
            - meaning: English translation
            - next_review: When this card is due
            - interval: Current review interval in days
            - ease_factor: Current ease factor
            - review_count: Number of reviews
    """
    conn = await get_connection()

    async with conn.execute(
        """
        SELECT
            f.id as flashcard_id,
            f.vocabulary_id as vocab_id,
            f.interval_days as interval,
            f.ease_factor,
            f.review_count,
            f.next_review_at as next_review,
            v.kanji_form as word,
            v.hiragana_reading as reading,
            v.english_meaning as meaning
        FROM flashcards f
        INNER JOIN vocabulary v ON f.vocabulary_id = v.id
        WHERE f.status = 'active'
          AND f.next_review_at <= datetime('now')
        ORDER BY f.next_review_at ASC
        LIMIT ?
        """,
        (limit,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


@tool
async def create_flashcard(vocab_id: int) -> Dict[str, Any]:
    """
    Create a new flashcard from a vocabulary entry.

    Initializes with SM-2 algorithm defaults:
    - ease_factor: 2.5
    - interval_days: 0.0 (new card)
    - next_review_at: NOW()
    - status: 'active'
    - card_type: 'recognition'

    Args:
        vocab_id: Vocabulary entry ID to create flashcard from

    Returns:
        Newly created flashcard data, or error dict if vocab doesn't exist
    """
    conn = await get_connection()

    # First check if vocabulary exists
    async with conn.execute(
        "SELECT id, kanji_form, hiragana_reading, english_meaning FROM vocabulary WHERE id = ?",
        (vocab_id,)
    ) as cursor:
        vocab_row = await cursor.fetchone()
        if not vocab_row:
            return {
                "success": False,
                "error": f"Vocabulary ID {vocab_id} not found"
            }

    # Create flashcard with SM-2 defaults
    async with conn.execute(
        """
        INSERT INTO flashcards (
            vocabulary_id,
            card_type,
            status,
            ease_factor,
            interval_days,
            review_count,
            consecutive_correct,
            lapses,
            next_review_at
        ) VALUES (?, 'recognition', 'active', 2.5, 0.0, 0, 0, 0, datetime('now'))
        """,
        (vocab_id,)
    ) as cursor:
        await conn.commit()
        flashcard_id = cursor.lastrowid

    # Fetch and return the created flashcard
    async with conn.execute(
        """
        SELECT
            f.id as flashcard_id,
            f.vocabulary_id as vocab_id,
            f.card_type,
            f.status,
            f.ease_factor,
            f.interval_days as interval,
            f.review_count,
            f.next_review_at as next_review,
            f.created_at,
            v.kanji_form as word,
            v.hiragana_reading as reading,
            v.english_meaning as meaning
        FROM flashcards f
        INNER JOIN vocabulary v ON f.vocabulary_id = v.id
        WHERE f.id = ?
        """,
        (flashcard_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            result = _row_to_dict(row)
            result["success"] = True
            return result
        else:
            return {
                "success": False,
                "error": "Failed to fetch created flashcard"
            }


@tool
async def record_flashcard_review(
    flashcard_id: int,
    rating: Literal[0, 1, 2, 3]
) -> Dict[str, Any]:
    """
    Record a flashcard review and update SM-2 algorithm parameters.

    Rating scale:
        0 = Again (didn't remember)
        1 = Hard (struggled to remember)
        2 = Medium (remembered with some effort)
        3 = Easy (remembered easily)

    Args:
        flashcard_id: ID of the flashcard being reviewed
        rating: Review rating (0-3)

    Returns:
        Updated flashcard data with new interval and next review date
    """
    # Validate rating
    if rating not in {0, 1, 2, 3}:
        return {
            "success": False,
            "error": f"Invalid rating. Must be 0, 1, 2, or 3. Got: {rating}"
        }

    conn = await get_connection()

    # Fetch current flashcard state
    async with conn.execute(
        """
        SELECT
            id, ease_factor, interval_days, review_count,
            consecutive_correct, lapses
        FROM flashcards
        WHERE id = ?
        """,
        (flashcard_id,)
    ) as cursor:
        flashcard_row = await cursor.fetchone()

        if not flashcard_row:
            return {
                "success": False,
                "error": f"Flashcard ID {flashcard_id} not found"
            }

        flashcard = dict(flashcard_row)

    # Store values before SM-2 calculation (for review_sessions record)
    ease_before = flashcard['ease_factor']
    interval_before = flashcard['interval_days']

    # Calculate new values using SM-2 algorithm
    new_interval, new_ease, new_repetitions = _calculate_sm2_next_interval(
        rating=rating,
        current_ease=flashcard['ease_factor'],
        current_interval=flashcard['interval_days'],
        repetitions=flashcard['consecutive_correct']
    )

    # Calculate next review date
    next_review = datetime.now() + timedelta(days=new_interval)

    # Update lapse count if failed
    new_lapses = flashcard['lapses'] + (1 if rating < 2 else 0)

    # Update flashcard
    async with conn.execute(
        """
        UPDATE flashcards
        SET ease_factor = ?,
            interval_days = ?,
            review_count = review_count + 1,
            consecutive_correct = ?,
            lapses = ?,
            last_reviewed_at = datetime('now'),
            next_review_at = ?
        WHERE id = ?
        """,
        (new_ease, new_interval, new_repetitions, new_lapses,
         next_review.isoformat(), flashcard_id)
    ) as cursor:
        await conn.commit()

    # Create review session record
    quality_rating = {0: 0, 1: 3, 2: 4, 3: 5}[rating]
    correct = rating >= 2

    async with conn.execute(
        """
        INSERT INTO review_sessions (
            flashcard_id,
            quality_rating,
            correct,
            interval_before_days,
            ease_factor_before,
            ease_factor_after
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (flashcard_id, quality_rating, correct,
         interval_before, ease_before, new_ease)
    ) as cursor:
        await conn.commit()

    # Fetch and return updated flashcard
    async with conn.execute(
        """
        SELECT
            f.id as flashcard_id,
            f.vocabulary_id as vocab_id,
            f.ease_factor,
            f.interval_days as interval,
            f.review_count,
            f.consecutive_correct,
            f.lapses,
            f.next_review_at as next_review,
            f.last_reviewed_at as last_reviewed,
            v.kanji_form as word,
            v.hiragana_reading as reading,
            v.english_meaning as meaning
        FROM flashcards f
        INNER JOIN vocabulary v ON f.vocabulary_id = v.id
        WHERE f.id = ?
        """,
        (flashcard_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            result = _row_to_dict(row)
            result["success"] = True
            result["rating_submitted"] = rating
            return result
        else:
            return {
                "success": False,
                "error": "Failed to fetch updated flashcard"
            }


@tool
async def get_review_statistics() -> Dict[str, Any]:
    """
    Get flashcard review statistics.

    Calculates statistics across all flashcards and reviews:
    - Total flashcard count
    - Due today count
    - Reviewed today count
    - Average ease factor
    - Longest streak (consecutive days with reviews)

    Returns:
        Dictionary containing comprehensive review statistics
    """
    conn = await get_connection()

    # Total flashcards
    async with conn.execute("SELECT COUNT(*) as count FROM flashcards") as cursor:
        total_row = await cursor.fetchone()
        total_flashcards = total_row['count'] if total_row else 0

    # Due today
    async with conn.execute(
        """
        SELECT COUNT(*) as count
        FROM flashcards
        WHERE status = 'active'
          AND next_review_at <= datetime('now')
        """
    ) as cursor:
        due_row = await cursor.fetchone()
        due_today = due_row['count'] if due_row else 0

    # Reviewed today
    async with conn.execute(
        """
        SELECT COUNT(*) as count
        FROM review_sessions
        WHERE DATE(reviewed_at) = DATE('now')
        """
    ) as cursor:
        reviewed_row = await cursor.fetchone()
        reviewed_today = reviewed_row['count'] if reviewed_row else 0

    # Average ease factor
    async with conn.execute(
        "SELECT AVG(ease_factor) as avg_ease FROM flashcards WHERE status = 'active'"
    ) as cursor:
        ease_row = await cursor.fetchone()
        average_ease = round(ease_row['avg_ease'], 2) if ease_row and ease_row['avg_ease'] else 2.5

    # TODO: Implement longest streak calculation (requires day-by-day analysis)
    longest_streak = 0

    return {
        "total_flashcards": total_flashcards,
        "due_today": due_today,
        "reviewed_today": reviewed_today,
        "average_ease": average_ease,
        "longest_streak": longest_streak,
    }


# Export all tools
__all__ = [
    "get_due_flashcards",
    "record_flashcard_review",
    "create_flashcard",
    "get_review_statistics",
]
'''

if __name__ == "__main__":
    target_file = "src/japanese_agent/tools/flashcard_manager.py"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(CONTENT)

    print(f"Updated {target_file} successfully")
