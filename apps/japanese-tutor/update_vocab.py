#!/usr/bin/env python3
"""Script to update vocabulary_manager.py with database implementation."""

import os

CONTENT = '''"""
Vocabulary management tools for Japanese Learning Agent.

Provides tools for searching, listing, and managing Japanese vocabulary.
All functions use async SQLite database operations.
"""

from typing import Dict, Any, List, Optional, Literal
from langchain_core.tools import tool
from japanese_agent.database.connection import get_connection


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert aiosqlite.Row to dictionary."""
    if row is None:
        return {}
    return dict(row)


@tool
async def search_vocabulary(query: str) -> List[Dict[str, Any]]:
    """
    Search vocabulary database by Japanese text or English meaning.

    Uses LIKE queries to find partial matches in:
    - kanji_form (Japanese word)
    - hiragana_reading (reading)
    - english_meaning (translation)

    Args:
        query: Search term (Japanese word or English meaning)

    Returns:
        List of matching vocabulary entries with full details
    """
    conn = await get_connection()

    # Search across multiple fields using LIKE
    search_pattern = f"%{query}%"

    async with conn.execute(
        """
        SELECT
            id, kanji_form, hiragana_reading, romaji_reading,
            english_meaning, part_of_speech, jlpt_level,
            study_status, encounter_count,
            first_seen_at, last_seen_at
        FROM vocabulary
        WHERE kanji_form LIKE ?
           OR hiragana_reading LIKE ?
           OR english_meaning LIKE ?
        ORDER BY encounter_count DESC, last_seen_at DESC
        LIMIT 50
        """,
        (search_pattern, search_pattern, search_pattern)
    ) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


@tool
async def list_vocabulary_by_status(
    status: Literal["new", "learning", "reviewing", "mastered", "suspended"],
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    List vocabulary filtered by study status.

    Uses indexed query on study_status for optimal performance.

    Args:
        status: Study status filter (new/learning/reviewing/mastered/suspended)
        limit: Maximum number of results (default: 20, max: 100)

    Returns:
        List of vocabulary entries matching the status
    """
    # Validate status enum
    valid_statuses = {"new", "learning", "reviewing", "mastered", "suspended"}
    if status not in valid_statuses:
        return [{"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}]

    # Cap limit at 100
    limit = min(limit, 100)

    conn = await get_connection()

    async with conn.execute(
        """
        SELECT
            id, kanji_form, hiragana_reading, romaji_reading,
            english_meaning, part_of_speech, jlpt_level,
            study_status, encounter_count,
            first_seen_at, last_seen_at
        FROM vocabulary
        WHERE study_status = ?
        ORDER BY last_seen_at DESC, encounter_count DESC
        LIMIT ?
        """,
        (status, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]


@tool
async def update_vocabulary_status(
    vocab_id: int,
    new_status: Literal["new", "learning", "reviewing", "mastered", "suspended"]
) -> Dict[str, Any]:
    """
    Update the study status of a vocabulary entry.

    Updates the status and automatically triggers updated_at timestamp.
    Also updates last_seen_at to current time.

    Args:
        vocab_id: Vocabulary entry ID
        new_status: New status (new/learning/reviewing/mastered/suspended)

    Returns:
        Updated vocabulary entry, or error dict if vocab_id not found
    """
    # Validate status enum
    valid_statuses = {"new", "learning", "reviewing", "mastered", "suspended"}
    if new_status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        }

    conn = await get_connection()

    # Update status and last_seen_at
    async with conn.execute(
        """
        UPDATE vocabulary
        SET study_status = ?,
            last_seen_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (new_status, vocab_id)
    ) as cursor:
        await conn.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "error": f"Vocabulary ID {vocab_id} not found"
            }

    # Fetch and return updated record
    async with conn.execute(
        """
        SELECT
            id, kanji_form, hiragana_reading, romaji_reading,
            english_meaning, part_of_speech, jlpt_level,
            study_status, encounter_count,
            first_seen_at, last_seen_at, updated_at
        FROM vocabulary
        WHERE id = ?
        """,
        (vocab_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            result = _row_to_dict(row)
            result["success"] = True
            return result
        else:
            return {
                "success": False,
                "error": "Failed to fetch updated record"
            }


@tool
async def get_vocabulary_statistics() -> Dict[str, Any]:
    """
    Get learning statistics for vocabulary progress.

    Calculates aggregate statistics across all vocabulary entries:
    - Total word count
    - Counts by study status
    - Total encounters across all words

    Returns:
        Dictionary containing comprehensive vocabulary statistics
    """
    conn = await get_connection()

    # Get total count
    async with conn.execute("SELECT COUNT(*) as count FROM vocabulary") as cursor:
        total_row = await cursor.fetchone()
        total_words = total_row['count'] if total_row else 0

    # Get counts by status
    async with conn.execute(
        """
        SELECT
            study_status,
            COUNT(*) as count
        FROM vocabulary
        GROUP BY study_status
        """
    ) as cursor:
        status_rows = await cursor.fetchall()

    # Build status counts dictionary
    status_counts = {
        "new": 0,
        "learning": 0,
        "reviewing": 0,
        "mastered": 0,
        "suspended": 0,
    }

    for row in status_rows:
        status = row['study_status']
        count = row['count']
        if status in status_counts:
            status_counts[status] = count

    # Get total encounters
    async with conn.execute(
        "SELECT SUM(encounter_count) as total FROM vocabulary"
    ) as cursor:
        encounter_row = await cursor.fetchone()
        total_encounters = encounter_row['total'] if encounter_row and encounter_row['total'] else 0

    return {
        "total_words": total_words,
        "new_words": status_counts["new"],
        "learning_words": status_counts["learning"],
        "reviewing_words": status_counts["reviewing"],
        "mastered_words": status_counts["mastered"],
        "suspended_words": status_counts["suspended"],
        "total_encounters": total_encounters,
    }


# Export all tools
__all__ = [
    "search_vocabulary",
    "list_vocabulary_by_status",
    "update_vocabulary_status",
    "get_vocabulary_statistics",
]
'''

if __name__ == "__main__":
    target_file = "src/japanese_agent/tools/vocabulary_manager.py"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(CONTENT)

    print(f"Updated {target_file} successfully")
