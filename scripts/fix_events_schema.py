#!/usr/bin/env python3
"""
Fix events.db schema to match Disler's implementation.
Changes event_type column to hook_event_type.
"""
import sqlite3
from pathlib import Path

# Database path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "events.db"

print(f"Fixing schema for: {DB_PATH}")

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if table exists and get current schema
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events';")
table_exists = cursor.fetchone() is not None

if table_exists:
    print("[OK] Events table exists")

    # Get current schema
    cursor.execute("PRAGMA table_info(events);")
    columns = cursor.fetchall()
    print(f"  Current columns: {[col[1] for col in columns]}")

    # Check if we need to migrate
    has_event_type = any(col[1] == 'event_type' for col in columns)
    has_hook_event_type = any(col[1] == 'hook_event_type' for col in columns)

    if has_hook_event_type:
        print("[OK] Schema already correct (hook_event_type exists)")
        conn.close()
        exit(0)

    if has_event_type:
        print("[WARN] Schema mismatch detected: event_type -> hook_event_type")
        print("  Backing up and recreating table...")

        # Backup existing data
        cursor.execute("SELECT COUNT(*) FROM events;")
        count = cursor.fetchone()[0]
        print(f"  Found {count} existing events")

        if count > 0:
            # Create backup table
            cursor.execute("""
                CREATE TABLE events_backup AS SELECT * FROM events;
            """)
            print("  [OK] Created backup table")

        # Drop old table and indexes
        cursor.execute("DROP TABLE IF EXISTS events;")
        print("  [OK] Dropped old events table")

# Create new table with correct schema (matching Disler's implementation)
print("Creating new events table with correct schema...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_app TEXT NOT NULL,
        session_id TEXT NOT NULL,
        hook_event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        chat TEXT,
        summary TEXT,
        timestamp INTEGER NOT NULL,
        humanInTheLoop TEXT,
        humanInTheLoopStatus TEXT,
        model_name TEXT
    )
""")

# Create indexes
print("Creating indexes...")
cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_app ON events(source_app);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_event_type ON events(hook_event_type);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);')

# Enable WAL mode
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")

# Commit changes
conn.commit()
print("[OK] Schema migration complete!")

# Verify new schema
cursor.execute("PRAGMA table_info(events);")
columns = cursor.fetchall()
print(f"[OK] New columns: {[col[1] for col in columns]}")

# Cleanup
cursor.execute("DROP TABLE IF EXISTS events_backup;")
conn.commit()

conn.close()
print("\n[SUCCESS] Database schema fixed and ready!")
print("   Run: bun run dev (in apps/observability-server)")
