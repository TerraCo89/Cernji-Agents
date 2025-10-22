#!/usr/bin/env python3
"""
RAG Pipeline Database Migration Script

Creates the necessary database tables for the Website RAG Pipeline feature:
- website_sources: Stores fetched websites (job postings, blogs, company pages)
- website_chunks: Stores semantically chunked content from websites and metadata
- website_chunks_fts: Full-text search virtual table (FTS5) for keyword matching

Vector embeddings are stored in Qdrant (external Docker container).
See: apps/resume-agent/docs/qdrant-setup.md

Usage:
    uv run apps/resume-agent/scripts/create_rag_tables.py

This script is idempotent - safe to run multiple times.
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "resume_agent.db"


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all RAG pipeline tables."""
    cursor = conn.cursor()

    # Table 1: website_sources
    print("Creating table: website_sources...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            content_type TEXT NOT NULL CHECK(content_type IN ('job_posting', 'blog_article', 'company_page')),
            language TEXT NOT NULL CHECK(language IN ('en', 'ja', 'mixed')),
            raw_html TEXT NOT NULL,
            metadata_json TEXT,
            fetch_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed')),
            error_message TEXT
        )
    """)
    print("[OK] Created table: website_sources")

    # Table 2: website_chunks
    print("Creating table: website_chunks...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES website_sources(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL CHECK(LENGTH(content) >= 50 AND LENGTH(content) <= 5000),
            char_count INTEGER NOT NULL CHECK(char_count >= 50 AND char_count <= 5000),
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(source_id, chunk_index)
        )
    """)
    print("[OK] Created table: website_chunks")

    # Virtual Table 3: website_chunks_fts (FTS5)
    print("Creating virtual table: website_chunks_fts...")
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS website_chunks_fts USING fts5(
            chunk_id UNINDEXED,
            content,
            tokenize='porter unicode61'
        )
    """)
    print("[OK] Created virtual table: website_chunks_fts (FTS5)")

    conn.commit()


def create_indexes(conn: sqlite3.Connection) -> None:
    """Create performance indexes."""
    cursor = conn.cursor()

    print("\nCreating indexes...")

    indexes = [
        ("idx_ws_url", "CREATE INDEX IF NOT EXISTS idx_ws_url ON website_sources(url)"),
        ("idx_ws_status", "CREATE INDEX IF NOT EXISTS idx_ws_status ON website_sources(processing_status)"),
        ("idx_ws_content_type", "CREATE INDEX IF NOT EXISTS idx_ws_content_type ON website_sources(content_type)"),
        ("idx_ws_fetch_time", "CREATE INDEX IF NOT EXISTS idx_ws_fetch_time ON website_sources(fetch_timestamp)"),
        ("idx_wc_source_id", "CREATE INDEX IF NOT EXISTS idx_wc_source_id ON website_chunks(source_id)"),
        ("idx_wc_char_count", "CREATE INDEX IF NOT EXISTS idx_wc_char_count ON website_chunks(char_count)"),
    ]

    for name, sql in indexes:
        cursor.execute(sql)
        print(f"[OK] Created index: {name}")

    conn.commit()


def verify_tables(conn: sqlite3.Connection) -> None:
    """Verify all tables were created successfully."""
    cursor = conn.cursor()

    required_tables = [
        "website_sources",
        "website_chunks",
        "website_chunks_fts"
    ]

    print("\nVerifying tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' OR type='table' ORDER BY name")
    existing_tables = [row[0] for row in cursor.fetchall()]

    for table in required_tables:
        if table in existing_tables:
            print(f"[OK] Verified: {table}")
        else:
            print(f"[ERROR] Missing: {table}")
            sys.exit(1)

    print(f"\nNote: Vector embeddings are stored in Qdrant (not SQLite)")
    print(f"      See: apps/resume-agent/docs/qdrant-setup.md")


def main():
    """Main migration execution."""
    print(f"RAG Pipeline Database Migration")
    print(f"Database: {DB_PATH.absolute()}\n")

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

    try:
        # Run migrations
        create_tables(conn)
        create_indexes(conn)
        verify_tables(conn)

        print(f"\n{'='*60}")
        print(f"[OK] Migration complete!")
        print(f"Database ready: {DB_PATH.absolute()}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
