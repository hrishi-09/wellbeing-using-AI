"""
Health data service — data access.

Owns the mood_logs and cbt_entries tables. Nothing outside this
service should query those tables directly — other services (like the
AI engine) go through these functions, the same way a real deployment
would call this service's API instead of reaching into its database.
"""
from datetime import datetime

from data.db import get_db


def upsert_mood_log(user_id, log_date, mood_score, anxiety_score, sleep_hours, exercise_minutes, notes):
    conn = get_db()
    conn.execute("""
        INSERT INTO mood_logs (user_id, log_date, mood_score, anxiety_score, sleep_hours, exercise_minutes, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET
            mood_score=excluded.mood_score,
            anxiety_score=excluded.anxiety_score,
            sleep_hours=excluded.sleep_hours,
            exercise_minutes=excluded.exercise_minutes,
            notes=excluded.notes
    """, (user_id, log_date, mood_score, anxiety_score, sleep_hours, exercise_minutes, notes, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_mood_logs(user_id, limit=90):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM mood_logs WHERE user_id = ?
        ORDER BY log_date ASC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return rows


def add_cbt_entry(user_id, entry_date, exercise_type, situation, automatic_thought,
                   evidence_for, evidence_against, balanced_thought, mood_before, mood_after):
    conn = get_db()
    conn.execute("""
        INSERT INTO cbt_entries (user_id, entry_date, exercise_type, situation, automatic_thought,
            evidence_for, evidence_against, balanced_thought, mood_before, mood_after, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, entry_date, exercise_type, situation, automatic_thought,
          evidence_for, evidence_against, balanced_thought, mood_before, mood_after,
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_cbt_entries(user_id, limit=50):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM cbt_entries WHERE user_id = ?
        ORDER BY entry_date DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return rows
