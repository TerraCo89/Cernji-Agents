#!/usr/bin/env python3
"""Create the events database with proper schema, indexes, and WAL mode."""

import sqlite3
from pathlib import Path

# Calculate project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Database path
DB_PATH = DATA_DIR / "events.db"

print(f"Creating events database at: {DB_PATH}")

# Connect and create schema
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Create events table
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp       TEXT NOT NULL,
  source_app      TEXT NOT NULL,
  event_type      TEXT NOT NULL,
  tool_name       TEXT,
  summary         TEXT,
  session_id      TEXT,
  metadata        TEXT,
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Create indexes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_source_app ON events(source_app)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")

# Enable WAL mode and set busy timeout
cursor.execute("PRAGMA journal_mode=WAL")
cursor.execute("PRAGMA busy_timeout=5000")

# Commit and verify
conn.commit()

# Verify table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
result = cursor.fetchone()

if result:
    print("[OK] Events table created successfully")

    # Verify indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'")
    indexes = cursor.fetchall()
    print(f"[OK] Created {len(indexes)} indexes: {[idx[0] for idx in indexes]}")

    # Verify WAL mode
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"[OK] Journal mode: {mode}")

    print(f"\n[OK] Database ready at: {DB_PATH}")
else:
    print("[ERROR] Failed to create events table")
    exit(1)

conn.close()
