"""
User service — data access.

Owns the users and user_profile tables. Other services (the gateway's
auth guard, the AI engine) go through get_user_by_id / get_profile
rather than querying these tables directly.
"""
from datetime import datetime

from db.connection import get_db


def create_user(name, phone, age, sex, email, location, password_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (name, phone, age, sex, email, location, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, age, sex, email, location, password_hash, datetime.utcnow().isoformat()))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id


def get_user_by_phone(phone):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def update_user_basic(user_id, name, age, sex, email, location):
    conn = get_db()
    conn.execute("""
        UPDATE users SET name = ?, age = ?, sex = ?, email = ?, location = ?
        WHERE id = ?
    """, (name, age, sex, email, location, user_id))
    conn.commit()
    conn.close()


def get_profile(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def upsert_profile(user_id, fields):
    """fields: dict matching the writable columns of user_profile (goals and
    preferences should already be JSON-encoded strings)."""
    conn = get_db()
    columns = list(fields.keys())
    col_list = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))
    update_clause = ", ".join(f"{c} = excluded.{c}" for c in columns)
    values = [fields[c] for c in columns]

    conn.execute(f"""
        INSERT INTO user_profile (user_id, {col_list}, updated_at)
        VALUES (?, {placeholders}, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            {update_clause},
            updated_at = excluded.updated_at
    """, [user_id] + values + [datetime.utcnow().isoformat()])
    conn.commit()
    conn.close()
