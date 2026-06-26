import sqlite3
import datetime
from typing import Optional, List, Dict

DB_PATH = "coach.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                goal_text TEXT,
                goal_deadline TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT,
                bot_response TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_status (
                user_id INTEGER PRIMARY KEY,
                last_morning DATE,
                last_evening DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                timezone TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

def get_user(telegram_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        return dict(row) if row else None

def create_user(telegram_id: int, username: str = None) -> int:
    with get_connection() as conn:
        user = conn.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if user:
            return user['id']
        cursor = conn.execute(
            "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        conn.commit()
        return cursor.lastrowid

def update_goal(telegram_id: int, goal: str, deadline: str = None):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET goal_text = ?, goal_deadline = ? WHERE telegram_id = ?",
            (goal, deadline, telegram_id)
        )
        conn.commit()

def save_session(user_id: int, session_type: str, user_input: str, bot_response: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, session_type, user_input, bot_response) VALUES (?, ?, ?, ?)",
            (user_id, session_type, user_input, bot_response)
        )
        conn.commit()

def get_all_users_with_goal() -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users WHERE goal_text IS NOT NULL").fetchall()
        return [dict(row) for row in rows]

def update_daily_status(user_id: int, session_type: str, date: str):
    with get_connection() as conn:
        if session_type == "morning":
            conn.execute(
                "INSERT OR REPLACE INTO daily_status (user_id, last_morning) VALUES (?, ?)",
                (user_id, date)
            )
        else:
            conn.execute(
                "INSERT OR REPLACE INTO daily_status (user_id, last_evening) VALUES (?, ?)",
                (user_id, date)
            )
        conn.commit()

def get_daily_status(user_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM daily_status WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}

def get_stats(telegram_id: int) -> dict:
    user = get_user(telegram_id)
    if not user:
        return {}
    with get_connection() as conn:
        morning_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND session_type = 'morning'",
            (user['id'],)
        ).fetchone()[0]
        evening_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ? AND session_type = 'evening'",
            (user['id'],)
        ).fetchone()[0]
        return {"morning": morning_count, "evening": evening_count}

def set_user_timezone(telegram_id: int, timezone_str: str):
    user = get_user(telegram_id)
    if not user:
        return
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, timezone) VALUES (?, ?)",
            (user['id'], timezone_str)
        )
        conn.commit()

def get_user_timezone(telegram_id: int) -> Optional[str]:
    user = get_user(telegram_id)
    if not user:
        return None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT timezone FROM user_settings WHERE user_id = ?", (user['id'],)
        ).fetchone()
        return row['timezone'] if row else None

def reset_user(telegram_id: int):
    """Удаляет всю историю и настройки пользователя, оставляя только учётную запись."""
    user = get_user(telegram_id)
    if not user:
        return
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user['id'],))
        conn.execute("DELETE FROM daily_status WHERE user_id = ?", (user['id'],))
        conn.execute("DELETE FROM user_settings WHERE user_id = ?", (user['id'],))
        conn.execute("UPDATE users SET goal_text = NULL, goal_deadline = NULL WHERE id = ?", (user['id'],))
        conn.commit()