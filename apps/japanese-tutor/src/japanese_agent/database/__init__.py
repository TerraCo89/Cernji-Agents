"""
Database layer for Japanese Learning Agent.

Provides async SQLite connection management with WAL mode,
complete schema implementation, and data access utilities.
"""

from japanese_agent.database.connection import (
    get_connection,
    initialize_database,
    close_connection,
)

__all__ = [
    "get_connection",
    "initialize_database",
    "close_connection",
]
