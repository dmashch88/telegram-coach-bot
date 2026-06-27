import sqlite3
from datetime import datetime, timedelta
import pytz
from contextlib import contextmanager

DB_PATH = "coach_bot.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        # Пользователи
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                goal_text TEXT,
                timezone TEXT DEFAULT 'UTC',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Сессии (утро/вечер)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_type TEXT CHECK(session_type IN ('morning','evening')),
                user_input TEXT,
                bot_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        # Streak (серия дней)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS streak (
                user_id INTEGER PRIMARY KEY,
                current_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        # Совпадения цели по дням
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goal_matches (
                user_id INTEGER,
                date DATE,
                morning_match BOOLEAN DEFAULT 0,
                evening_match BOOLEAN DEFAULT 0,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

# ---- Пользователи ----
def create_user(telegram_id, username=None):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        conn.commit()

def get_user(telegram_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

def update_goal(telegram_id, goal_text):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET goal_text = ? WHERE telegram_id = ?",
            (goal_text, telegram_id)
        )
        conn.commit()

def set_user_timezone(telegram_id, tz_str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET timezone = ? WHERE telegram_id = ?",
            (tz_str, telegram_id)
        )
        conn.commit()

def get_user_timezone(telegram_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT timezone FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ).fetchone()
        return row['timezone'] if row else None

def get_all_users_with_goal():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, telegram_id, goal_text, timezone FROM users WHERE goal_text IS NOT NULL"
        ).fetchall()
        return [dict(row) for row in rows]

def delete_user_data(telegram_id):
    with get_connection() as conn:
        user = get_user(telegram_id)
        if not user:
            return
        user_id = user['id']
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM streak WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM goal_matches WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        conn.commit()

# ---- Сессии ----
def save_session(user_id, session_type, user_input, bot_response):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, session_type, user_input, bot_response) VALUES (?, ?, ?, ?)",
            (user_id, session_type, user_input, bot_response)
        )
        conn.commit()

def get_session_count(user_id, session_type):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sessions WHERE user_id = ? AND session_type = ?",
            (user_id, session_type)
        ).fetchone()
        return row['cnt'] if row else 0

def get_total_sessions(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sessions WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row['cnt'] if row else 0

# ---- Streak ----
def update_streak(user_id, date_str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT current_streak, last_activity_date FROM streak WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row:
            last_date = row['last_activity_date']
            if last_date == date_str:
                return  # уже обновлено сегодня
            elif last_date == str((datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).date()):
                new_streak = row['current_streak'] + 1
            else:
                new_streak = 1
            conn.execute(
                "UPDATE streak SET current_streak = ?, last_activity_date = ? WHERE user_id = ?",
                (new_streak, date_str, user_id)
            )
        else:
            conn.execute(
                "INSERT INTO streak (user_id, current_streak, last_activity_date) VALUES (?, 1, ?)",
                (user_id, date_str)
            )
        conn.commit()

def get_streak(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT current_streak FROM streak WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row['current_streak'] if row else 0

# ---- Совпадения цели ----
def save_goal_match(user_id, date_str, session_type, matched):
    with get_connection() as conn:
        if session_type == "morning":
            conn.execute(
                "INSERT OR REPLACE INTO goal_matches (user_id, date, morning_match) VALUES (?, ?, ?)",
                (user_id, date_str, 1 if matched else 0)
            )
        else:
            conn.execute(
                "INSERT OR REPLACE INTO goal_matches (user_id, date, evening_match) VALUES (?, ?, ?)",
                (user_id, date_str, 1 if matched else 0)
            )
        conn.commit()

def get_goal_match_count(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT SUM(morning_match) + SUM(evening_match) as total FROM goal_matches WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return row['total'] if row and row['total'] else 0