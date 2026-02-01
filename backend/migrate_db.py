"""
Database Migration Script
Adds new columns for processing lock functionality.

Run this script once to update an existing database:
    python migrate_db.py
"""
import sqlite3
from pathlib import Path
from config import DATA_DIR

DATABASE_PATH = DATA_DIR / "database.db"


def migrate():
    """Add new columns to projects table if they don't exist"""
    if not DATABASE_PATH.exists():
        print("Database doesn't exist yet. It will be created on first run.")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check existing columns in projects table
    cursor.execute("PRAGMA table_info(projects)")
    columns = {row[1] for row in cursor.fetchall()}

    migrations = []

    # Add is_processing column
    if "is_processing" not in columns:
        migrations.append(
            "ALTER TABLE projects ADD COLUMN is_processing BOOLEAN DEFAULT 0"
        )

    # Add processing_started_at column
    if "processing_started_at" not in columns:
        migrations.append(
            "ALTER TABLE projects ADD COLUMN processing_started_at DATETIME"
        )

    # Add user_id column (nullable for backward compatibility)
    if "user_id" not in columns:
        migrations.append(
            "ALTER TABLE projects ADD COLUMN user_id INTEGER"
        )

    if not migrations:
        print("Database is up to date. No migrations needed.")
        conn.close()
        return

    print(f"Running {len(migrations)} migration(s)...")

    for sql in migrations:
        print(f"  Executing: {sql}")
        cursor.execute(sql)

    conn.commit()
    conn.close()

    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()
