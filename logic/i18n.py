import json
import locale
from logic.database import get_connection, DB_PATH

SUPPORTED = ("ru", "en")
_strings = {}
_lang = "ru"


def _system_language():
    code = (locale.getlocale()[0] or "").lower()
    return "ru" if code.startswith("ru") else "en"


def load(lang):
    """Загружает словарь строк выбранного языка из locales/<lang>.json."""
    global _strings, _lang
    if lang not in SUPPORTED:
        lang = "en"
    with open(f"locales/{lang}.json", encoding="utf-8") as f:
        _strings = json.load(f)
    _lang = lang


def tr(key):
    """Возвращает перевод строки; если перевода нет, возвращает ключ."""
    return _strings.get(key, key)


def init_language(path=DB_PATH):
    with get_connection(path) as conn:
        row = conn.execute("SELECT language FROM settings WHERE id = 1").fetchone()
    load(row[0] if row and row[0] else _system_language())


def set_language(lang, path=DB_PATH):
    load(lang)
    with get_connection(path) as conn:
        conn.execute("UPDATE settings SET language = ? WHERE id = 1", (_lang,))
