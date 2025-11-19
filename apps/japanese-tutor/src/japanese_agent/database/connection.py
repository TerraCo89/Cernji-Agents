"""
Database connection manager for Japanese Learning Agent.

Provides async SQLite connection management with WAL mode,
automatic schema initialization, and proper PRAGMA configuration.
"""

import os
import aiosqlite
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from cernji_logging import get_logger

# Configure logging
logger = get_logger(__name__)


# Global connection instance
_connection: Optional[aiosqlite.Connection] = None


def get_database_path() -> str:
    """
    Get database path from environment variable or use default.

    Returns:
        Absolute path to database file

    Environment Variables:
        DATABASE_PATH: Custom database location (relative or absolute)
    """
    # Default to app-specific database (DEV-53)
    # Path relative to src/japanese_agent/database/ directory
    # ../../data/japanese_agent.db resolves to apps/japanese-tutor/src/data/japanese_agent.db
    db_path = os.getenv("DATABASE_PATH", "../../data/japanese_agent.db")

    # Convert relative paths to absolute based on this file's location
    if not os.path.isabs(db_path):
        # Get the directory containing this file (src/japanese_agent/database/)
        current_dir = Path(__file__).parent
        # Resolve relative path
        db_path = str((current_dir / db_path).resolve())

    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)

    return db_path


async def get_connection() -> aiosqlite.Connection:
    """
    Get or create async database connection with proper PRAGMA settings.

    This function maintains a singleton connection that persists across calls.
    The connection is configured with:
    - Foreign key constraints enabled
    - WAL (Write-Ahead Logging) mode for concurrent access
    - Optimized synchronous and cache settings

    Returns:
        aiosqlite.Connection: Configured async database connection

    Example:
        conn = await get_connection()
        async with conn.execute("SELECT * FROM vocabulary") as cursor:
            rows = await cursor.fetchall()
    """
    global _connection

    if _connection is None:
        db_path = get_database_path()

        logger.info("Creating database connection", db_path=db_path)

        # Create connection
        _connection = await aiosqlite.connect(db_path)

        # Enable dict-like row access
        _connection.row_factory = aiosqlite.Row

        # Configure PRAGMAs for optimal performance and safety
        await _connection.execute("PRAGMA foreign_keys = ON")
        await _connection.execute("PRAGMA journal_mode = WAL")
        await _connection.execute("PRAGMA synchronous = NORMAL")
        await _connection.execute("PRAGMA cache_size = -2000")  # 2MB cache
        await _connection.execute("PRAGMA temp_store = MEMORY")

        await _connection.commit()

        logger.info("Database connection established with WAL mode", db_path=db_path)

    return _connection


async def initialize_database(force: bool = False) -> None:
    """
    Initialize database schema from schema.sql if needed.

    Reads and executes the schema.sql file to create all tables, indexes,
    triggers, and constraints. Safe to call multiple times - uses IF NOT EXISTS.

    Args:
        force: If True, recreate schema even if tables exist (DESTRUCTIVE)

    Raises:
        FileNotFoundError: If schema.sql cannot be found
        aiosqlite.Error: If schema execution fails
    """
    conn = await get_connection()

    # Check if database is already initialized (unless force=True)
    if not force:
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                # Database already initialized
                logger.debug("Database already initialized, skipping schema creation")
                return

    logger.info("Initializing database schema", force=force)

    # Read schema.sql from same directory as this file
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        logger.error("Schema file not found", schema_path=str(schema_path))
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Read and execute schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Execute schema (split by semicolon for multiple statements)
    await conn.executescript(schema_sql)
    await conn.commit()

    logger.info("Database schema initialized successfully")


async def close_connection() -> None:
    """
    Close the database connection and cleanup.

    Should be called when shutting down the application or in cleanup handlers.
    After calling this, get_connection() will create a new connection.
    """
    global _connection

    if _connection:
        logger.info("Closing database connection")
        await _connection.close()
        _connection = None
        logger.debug("Database connection closed")


@asynccontextmanager
async def transaction():
    """
    Context manager for database transactions.

    Automatically commits on success or rolls back on exception.
    Ensures data consistency for multi-statement operations.

    Example:
        async with transaction():
            conn = await get_connection()
            await conn.execute("INSERT INTO vocabulary (...) VALUES (...)")
            await conn.execute("INSERT INTO flashcards (...) VALUES (...)")
            # Both inserts committed together
    """
    conn = await get_connection()

    try:
        yield conn
        await conn.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        await conn.rollback()
        logger.error("Transaction rolled back", error=str(e), exc_info=True)
        raise


async def execute_query(query: str, params: tuple = ()) -> list[aiosqlite.Row]:
    """
    Execute a SELECT query and return all results.

    Args:
        query: SQL SELECT query
        params: Query parameters (for ? placeholders)

    Returns:
        List of Row objects (dict-like access)

    Example:
        rows = await execute_query(
            "SELECT * FROM vocabulary WHERE study_status = ?",
            ('learning',)
        )
        for row in rows:
            print(row['kanji_form'], row['english_meaning'])
    """
    conn = await get_connection()
    async with conn.execute(query, params) as cursor:
        return await cursor.fetchall()


async def execute_insert(query: str, params: tuple = ()) -> int:
    """
    Execute an INSERT query and return the new row ID.

    Args:
        query: SQL INSERT query
        params: Query parameters (for ? placeholders)

    Returns:
        ID of the newly inserted row

    Example:
        vocab_id = await execute_insert(
            "INSERT INTO vocabulary (kanji_form, hiragana_reading, english_meaning) VALUES (?, ?, ?)",
            ('日本語', 'にほんご', 'Japanese language')
        )
    """
    conn = await get_connection()
    async with conn.execute(query, params) as cursor:
        await conn.commit()
        return cursor.lastrowid


async def execute_update(query: str, params: tuple = ()) -> int:
    """
    Execute an UPDATE or DELETE query and return rows affected.

    Args:
        query: SQL UPDATE or DELETE query
        params: Query parameters (for ? placeholders)

    Returns:
        Number of rows affected

    Example:
        rows_updated = await execute_update(
            "UPDATE vocabulary SET study_status = ? WHERE id = ?",
            ('mastered', 42)
        )
    """
    conn = await get_connection()
    async with conn.execute(query, params) as cursor:
        await conn.commit()
        return cursor.rowcount
