import os
import sqlite3
from datetime import date, timedelta

DB_PATH = "data/meditation.db"


def get_connection(path=DB_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=DB_PATH):
    with get_connection(path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_id INTEGER REFERENCES moods(id),
            duration INTEGER NOT NULL,
            date TEXT NOT NULL,
            meditation_type TEXT,
            voice TEXT,
            sound TEXT,
            mood_before INTEGER,
            mood_after INTEGER);
        CREATE TABLE IF NOT EXISTS dreams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_id INTEGER REFERENCES moods(id),
            audio_path TEXT, tags TEXT, emotion TEXT,
            date TEXT NOT NULL, duration INTEGER);
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions(id),
            badge TEXT NOT NULL, date TEXT NOT NULL,
            description TEXT);
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            achievement_id INTEGER REFERENCES achievements(id),
            reminder_time TEXT DEFAULT '09:00',
            reminder_enabled INTEGER DEFAULT 0,
            default_voice TEXT DEFAULT 'female',
            default_sound TEXT DEFAULT 'rain',
            default_duration INTEGER DEFAULT 10,
            language TEXT,
            avatar_state TEXT DEFAULT 'calm');
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_id INTEGER REFERENCES moods(id),
            entry_date TEXT NOT NULL UNIQUE,
            title TEXT, text TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS subscription (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            plan TEXT DEFAULT 'free', status TEXT DEFAULT 'inactive',
            purchase_id TEXT, expires_at TEXT, last_checked TEXT);
        INSERT OR IGNORE INTO subscription (id) VALUES (1);
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_id TEXT, provider TEXT, email TEXT, display_name TEXT,
            sync_enabled INTEGER DEFAULT 1, sync_journal INTEGER DEFAULT 1,
            last_sync_at TEXT);
        INSERT OR IGNORE INTO account (id) VALUES (1);
        CREATE TABLE IF NOT EXISTS stress_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, answers TEXT NOT NULL,
            score REAL NOT NULL, category TEXT NOT NULL);
        INSERT OR IGNORE INTO settings (id) VALUES (1);
        """)


def add_session(duration, meditation_type, voice, sound,
                mood_before=None, mood_after=None, mood_id=None,
                path=DB_PATH):
    with get_connection(path) as conn:
        cur = conn.execute(
            "INSERT INTO sessions (mood_id, duration, date, meditation_type,"
            " voice, sound, mood_before, mood_after)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (mood_id, duration, date.today().isoformat(), meditation_type,
             voice, sound, mood_before, mood_after))
        return cur.lastrowid


def get_streak(path=DB_PATH, today=None):
    """Количество дней подряд (до сегодняшнего или вчерашнего дня),
    в которые была хотя бы одна сессия медитации."""
    today = today or date.today()
    with get_connection(path) as conn:
        days = {date.fromisoformat(row[0]) for row in
                conn.execute("SELECT DISTINCT date FROM sessions")}
    current = today if today in days else today - timedelta(days=1)
    streak = 0
    while current in days:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_days_without_practice(path=DB_PATH, today=None):
    today = today or date.today()
    with get_connection(path) as conn:
        row = conn.execute("SELECT MAX(date) FROM sessions").fetchone()
    if row[0] is None:
        return None
    return (today - date.fromisoformat(row[0])).days


def get_total_time(path=DB_PATH):
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(duration), 0) FROM sessions").fetchone()
    return row[0]


def get_last_mood(path=DB_PATH):
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT mood FROM moods ORDER BY date DESC, id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else None


# ---- Дополнительные функции для экранов ----

def add_mood(mood, note=None, day=None, path=DB_PATH):
    """Запись в дневник настроения. mood: радость, спокойствие,
    усталость, тревога, грусть."""
    with get_connection(path) as conn:
        cur = conn.execute(
            "INSERT INTO moods (mood, note, date) VALUES (?, ?, ?)",
            (mood, note, day or date.today().isoformat()))
        return cur.lastrowid


def get_moods(limit=50, path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT id, mood, note, date FROM moods"
            " ORDER BY date DESC, id DESC LIMIT ?", (limit,)).fetchall()


def get_all_sessions(path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT id, duration, date, meditation_type, voice, sound,"
            " mood_before, mood_after FROM sessions ORDER BY date").fetchall()


def get_session_count(path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]


def add_dream(tags, emotion, audio_path=None, duration=None, mood_id=None,
              path=DB_PATH):
    with get_connection(path) as conn:
        cur = conn.execute(
            "INSERT INTO dreams (mood_id, audio_path, tags, emotion, date,"
            " duration) VALUES (?, ?, ?, ?, ?, ?)",
            (mood_id, audio_path, tags, emotion, date.today().isoformat(),
             duration))
        return cur.lastrowid


def get_dreams(limit=30, path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT id, tags, emotion, date, audio_path FROM dreams"
            " ORDER BY date DESC, id DESC LIMIT ?", (limit,)).fetchall()


SETTINGS_FIELDS = ("reminder_time", "reminder_enabled", "default_voice",
                   "default_sound", "default_duration", "language",
                   "avatar_state")


def get_settings(path=DB_PATH):
    with get_connection(path) as conn:
        cur = conn.execute("SELECT * FROM settings WHERE id = 1")
        names = [d[0] for d in cur.description]
        return dict(zip(names, cur.fetchone()))


def update_setting(field, value, path=DB_PATH):
    if field not in SETTINGS_FIELDS:
        raise ValueError("Неизвестная настройка")
    with get_connection(path) as conn:
        conn.execute(f"UPDATE settings SET {field} = ? WHERE id = 1", (value,))


def get_last_stress(path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT score, category, date FROM stress_tests"
            " ORDER BY date DESC, id DESC LIMIT 1").fetchone()
