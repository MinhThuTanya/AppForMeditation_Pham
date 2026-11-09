from datetime import datetime
from logic.database import get_connection, DB_PATH


def save_entry(entry_date, text, title=None, mood_id=None, path=DB_PATH):
    """Создаёт запись дневника дня на дату entry_date (ГГГГ-ММ-ДД)
    или обновляет её, если запись за этот день уже существует."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection(path) as conn:
        conn.execute(
            "INSERT INTO journal_entries"
            " (entry_date, title, text, mood_id, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(entry_date) DO UPDATE SET"
            " title = excluded.title, text = excluded.text,"
            " mood_id = excluded.mood_id, updated_at = excluded.updated_at",
            (entry_date, title, text, mood_id, now, now))


def get_entry(entry_date, path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT entry_date, title, text, mood_id FROM journal_entries"
            " WHERE entry_date = ?", (entry_date,)).fetchone()


def get_month_marks(year, month, path=DB_PATH):
    """Даты месяца с записями и отмеченным настроением — для календаря."""
    prefix = f"{year:04d}-{month:02d}-%"
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT j.entry_date, m.mood FROM journal_entries j"
            " LEFT JOIN moods m ON m.id = j.mood_id"
            " WHERE j.entry_date LIKE ? ORDER BY j.entry_date",
            (prefix,)).fetchall()



def mood_for_entry(entry_date, mood, path=DB_PATH):
    """Возвращает id записи настроения для дневника дня: обновляет уже
    привязанную запись или создаёт новую (F.11.02 «Отметить настроение»)."""
    if not mood:
        return None
    with get_connection(path) as conn:
        row = conn.execute("SELECT mood_id FROM journal_entries WHERE entry_date = ?",
                           (entry_date,)).fetchone()
        if row and row[0]:
            conn.execute("UPDATE moods SET mood = ? WHERE id = ?", (mood, row[0]))
            return row[0]
        cur = conn.execute("INSERT INTO moods (mood, note, date) VALUES (?, ?, ?)",
                           (mood, None, entry_date))
        return cur.lastrowid


def get_recent_entries(limit=20, path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT j.entry_date, j.title, j.text, m.mood FROM journal_entries j"
            " LEFT JOIN moods m ON m.id = j.mood_id"
            " ORDER BY j.entry_date DESC LIMIT ?", (limit,)).fetchall()


def get_entry_mood(entry_date, path=DB_PATH):
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT m.mood FROM journal_entries j JOIN moods m ON m.id = j.mood_id"
            " WHERE j.entry_date = ?", (entry_date,)).fetchone()
    return row[0] if row else None
