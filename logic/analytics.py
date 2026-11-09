from datetime import date, timedelta
from logic.database import (get_connection, get_streak, get_total_time,
                            get_session_count, DB_PATH)

# Оценка настроения для графика «Настроение за неделю» (1 — плохо, 5 — отлично)
MOOD_SCORE = {"радость": 5, "спокойствие": 4, "усталость": 2,
              "грусть": 1, "тревога": 1}

# Достижения: код, условие, описание
ACHIEVEMENTS = [
    ("first_session", lambda s: s["sessions"] >= 1, "Первая медитация"),
    ("streak_3", lambda s: s["streak"] >= 3, "3 дня подряд"),
    ("streak_7", lambda s: s["streak"] >= 7, "7 дней подряд"),
    ("minutes_100", lambda s: s["total"] >= 100, "100 минут практики"),
]


def summary(path=DB_PATH):
    return {"streak": get_streak(path), "total": get_total_time(path),
            "sessions": get_session_count(path)}


def week_moods(path=DB_PATH, today=None):
    """Средняя оценка настроения за каждый из последних 7 дней
    (0 — записей не было)."""
    today = today or date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    with get_connection(path) as conn:
        rows = conn.execute(
            "SELECT date, mood FROM moods WHERE date >= ?",
            (days[0].isoformat(),)).fetchall()
    result = []
    for d in days:
        scores = [MOOD_SCORE.get(m, 3) for (dd, m) in rows
                  if dd[:10] == d.isoformat()]
        result.append((d, round(sum(scores) / len(scores), 1) if scores else 0))
    return result


def practice_days(year, month, path=DB_PATH):
    """Дни месяца, в которые была практика — для календаря статистики."""
    prefix = f"{year:04d}-{month:02d}-%"
    with get_connection(path) as conn:
        return {int(r[0][8:10]) for r in conn.execute(
            "SELECT DISTINCT date FROM sessions WHERE date LIKE ?", (prefix,))}


def check_achievements(session_id=None, path=DB_PATH):
    """Выдаёт новые значки. Возвращает список описаний полученных значков."""
    stats = summary(path)
    new = []
    with get_connection(path) as conn:
        have = {r[0] for r in conn.execute("SELECT badge FROM achievements")}
        for badge, rule, description in ACHIEVEMENTS:
            if badge not in have and rule(stats):
                cur = conn.execute(
                    "INSERT INTO achievements (session_id, badge, date,"
                    " description) VALUES (?, ?, ?, ?)",
                    (session_id, badge, date.today().isoformat(), description))
                conn.execute("UPDATE settings SET achievement_id = ?"
                             " WHERE id = 1", (cur.lastrowid,))
                new.append(description)
    return new


def get_achievements(path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT badge, date, description FROM achievements"
            " ORDER BY date, id").fetchall()
