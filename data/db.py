"""
Data & storage layer.

This is the single source of truth for the schema and connection
handling that every core service reads and writes through. In the
architecture diagram this is the "PostgreSQL (main DB)" box — today
it's SQLite for simplicity, but every service already only talks to
its own tables through its own repository module (see
services/*/repository.py), so swapping the engine later means editing
this file, not the services themselves.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "auro.db")


def get_db():
    # Make sure the data directory exists on every connection, not just at
    # init_db() time — Render's ephemeral filesystem can wipe it on a
    # cold-start restart even after the app has been running fine before.
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL mode creates sidecar -wal/-shm files that don't survive Render's
    # ephemeral disk reliably and can throw disk I/O errors mid-write.
    # DELETE (the default) is slower under heavy concurrency but far more
    # reliable on this kind of storage.
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db():
    """Creates every table used by every service. Owned centrally so the
    schema stays in one place even though each service only touches its
    own slice of it."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    # --- user_service tables ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            age INTEGER,
            sex TEXT,
            email TEXT,
            location TEXT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            date_of_birth TEXT,
            occupation TEXT,
            marital_status TEXT,
            blood_group TEXT,
            medical_conditions TEXT,
            medications TEXT,
            allergies TEXT,
            therapist_name TEXT,
            smoking TEXT,
            alcohol TEXT,
            diet_type TEXT,
            activity_level TEXT,
            work_schedule TEXT,
            emergency_contact_name TEXT,
            emergency_contact_relation TEXT,
            emergency_contact_phone TEXT,
            goals TEXT,             -- JSON list of strings
            preferences TEXT,       -- JSON dict: units, theme, notifications, age_guidance_enabled
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # --- health_data_service tables ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            mood_score INTEGER NOT NULL,     -- 1 (very low) to 10 (excellent)
            anxiety_score INTEGER,           -- 1 to 10
            sleep_hours REAL,
            exercise_minutes INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, log_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cbt_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            exercise_type TEXT NOT NULL,     -- e.g. 'thought_record', 'gratitude', 'reframe'
            situation TEXT,
            automatic_thought TEXT,
            evidence_for TEXT,
            evidence_against TEXT,
            balanced_thought TEXT,
            mood_before INTEGER,
            mood_after INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
