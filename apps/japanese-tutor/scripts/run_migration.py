#!/usr/bin/env python
"""Database migration runner for Japanese Tutor Agent.

Usage:
    python scripts/run_migration.py
"""
import os
import sqlite3
from pathlib import Path

# Get paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "src" / "data" / "japanese_agent.db"
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "japanese_agent" / "database" / "migrations"


def run_migrations():
    """Run all pending migrations."""
    print(f"[INFO] Running migrations on: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at: {DB_PATH}")
        print("        Run the application first to create the database.")
        return

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create migrations tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Get list of applied migrations
    cursor.execute("SELECT migration_name FROM _migrations")
    applied = {row[0] for row in cursor.fetchall()}

    # Get all migration files
    if not MIGRATIONS_DIR.exists():
        print(f"[INFO] No migrations directory found. Creating: {MIGRATIONS_DIR}")
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        print("[INFO] No migration files found.")
        conn.close()
        return

    # Run pending migrations
    pending_count = 0
    for migration_file in migration_files:
        migration_name = migration_file.name

        if migration_name in applied:
            print(f"[SKIP] {migration_name} (already applied)")
            continue

        print(f"[APPLY] Applying migration: {migration_name}")

        try:
            # Read and execute migration SQL
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()
                cursor.executescript(sql)

            # Record migration as applied
            cursor.execute(
                "INSERT INTO _migrations (migration_name) VALUES (?)",
                (migration_name,)
            )
            conn.commit()

            print(f"[SUCCESS] Applied: {migration_name}")
            pending_count += 1

        except Exception as e:
            print(f"[ERROR] Error applying {migration_name}: {e}")
            conn.rollback()
            break

    conn.close()

    if pending_count > 0:
        print(f"\n[SUCCESS] Successfully applied {pending_count} migration(s)")
    else:
        print("\n[INFO] Database is up to date")


if __name__ == "__main__":
    run_migrations()
