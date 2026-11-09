import base64
import hashlib
import secrets
from datetime import datetime
from urllib.parse import urlencode
from logic.database import get_connection, DB_PATH

# Адреса страниц входа сервисов (OAuth 2.0, код авторизации + PKCE)
PROVIDERS = {
    "google": "https://accounts.google.com/o/oauth2/v2/auth",
    "vk": "https://id.vk.com/authorize",
    "apple": "https://appleid.apple.com/auth/authorize",
}
REDIRECT_URI = "akii://auth/callback"
SYNC_TABLES = {"moods": "date", "sessions": "date", "dreams": "date",
               "stress_tests": "date", "journal_entries": "updated_at"}


def make_pkce():
    """Пара значений PKCE: code_verifier остаётся в приложении,
    code_challenge передаётся сервису входа."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_auth_url(provider, client_id, challenge, state):
    """Ссылка, которая открывается во внешнем браузере системы."""
    if provider not in PROVIDERS:
        raise ValueError("Неизвестный способ входа")
    params = {"response_type": "code", "client_id": client_id,
              "redirect_uri": REDIRECT_URI, "scope": "openid email",
              "state": state, "code_challenge": challenge,
              "code_challenge_method": "S256"}
    return PROVIDERS[provider] + "?" + urlencode(params)


def save_account(user_id, provider, email, display_name, path=DB_PATH):
    """Сохраняет сведения о входе. Токены хранятся не здесь,
    а в Android Keystore или iOS Keychain."""
    with get_connection(path) as conn:
        conn.execute(
            "UPDATE account SET user_id = ?, provider = ?, email = ?,"
            " display_name = ? WHERE id = 1",
            (user_id, provider, email, display_name))


def is_signed_in(path=DB_PATH):
    with get_connection(path) as conn:
        row = conn.execute("SELECT user_id FROM account WHERE id = 1").fetchone()
    return bool(row and row[0])


def sign_out(path=DB_PATH):
    """Выход из аккаунта: локальные записи пользователя остаются."""
    with get_connection(path) as conn:
        conn.execute(
            "UPDATE account SET user_id = NULL, provider = NULL, email = NULL,"
            " display_name = NULL, last_sync_at = NULL WHERE id = 1")


def collect_changes(path=DB_PATH):
    """Записи, изменённые с последней синхронизации, для отправки на сервер."""
    with get_connection(path) as conn:
        enabled, journal, last = conn.execute(
            "SELECT sync_enabled, sync_journal, last_sync_at"
            " FROM account WHERE id = 1").fetchone()
        if not enabled:
            return {}
        since = (last or "")[:10]
        changes = {}
        for table, column in SYNC_TABLES.items():
            if table == "journal_entries" and not journal:
                continue
            cur = conn.execute(
                f"SELECT * FROM {table} WHERE {column} >= ?", (since,))
            names = [d[0] for d in cur.description]
            changes[table] = [dict(zip(names, row)) for row in cur.fetchall()]
    return changes


def mark_synced(path=DB_PATH):
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection(path) as conn:
        conn.execute("UPDATE account SET last_sync_at = ? WHERE id = 1", (now,))


# ---- Обращение к серверу Akii Server ----
import json
import urllib.error
import urllib.request

SERVER_URL = "http://127.0.0.1:8000"   # адрес сервера; при публикации — HTTPS
# client_id выдаются после регистрации приложения в кабинетах VK ID,
# Google Cloud Console и Apple Developer (этап 9.4 плана)
CLIENT_IDS = {"vk": "", "google": "", "apple": ""}
_token = None                          # токен доступа текущего сеанса


class ServerError(Exception):
    pass


def available_providers(platform, region):
    """Кнопки экрана входа. В России — почта и VK ID (закон 406-ФЗ),
    в других странах — ещё Google; на iOS — вход через Apple (правило 4.8)."""
    providers = []
    if platform == "ios":
        providers.append("apple")
    if region != "ru":
        providers.append("google")
    providers.append("vk")
    return providers


def _request(method, url_path, data=None, token=None, timeout=8):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(SERVER_URL + url_path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail")
        except Exception:
            detail = None
        raise ServerError(detail or f"Ошибка сервера {e.code}")
    except (urllib.error.URLError, OSError):
        raise ServerError("server_unavailable")


def store_token(token):
    """На телефоне токен хранится в Android Keystore / iOS Keychain
    (подключается на этапе 9.4); на компьютере — только в памяти сеанса."""
    global _token
    _token = token


def register_email(email, password, display_name, path=DB_PATH):
    """Регистрация по почте. Сервер отправляет письмо для подтверждения."""
    return _request("POST", "/auth/register",
                    {"email": email, "password": password,
                     "display_name": display_name})


def sign_in_email(email, password, path=DB_PATH):
    data = _request("POST", "/auth/login",
                    {"email": email, "password": password})
    store_token(data["access_token"])
    save_account(data["user_id"], "email", data["email"],
                 data.get("display_name"), path)
    return data


def sign_in_oauth(provider, code, verifier, path=DB_PATH):
    """Передаёт код авторизации и code_verifier на сервер (шаг 7 рисунка 8)."""
    data = _request("POST", f"/auth/oauth/{provider}",
                    {"code": code, "code_verifier": verifier,
                     "redirect_uri": REDIRECT_URI})
    store_token(data["access_token"])
    save_account(data["user_id"], provider, data.get("email"),
                 data.get("display_name"), path)
    return data


def sync(path=DB_PATH):
    """Отправляет изменения на сервер и записывает изменения
    с других устройств в локальную базу."""
    if not _token:
        raise ServerError("not_signed_in")
    changes = collect_changes(path)
    data = _request("POST", "/sync", {"changes": changes}, token=_token)
    apply_changes(data.get("changes", {}), path)
    mark_synced(path)
    return data


def apply_changes(changes, path=DB_PATH):
    """Записи журнала дня сливаются по дате (побеждает более поздняя),
    остальные добавляются, если такой записи ещё нет."""
    with get_connection(path) as conn:
        for row in changes.get("journal_entries", []):
            conn.execute(
                "INSERT INTO journal_entries (entry_date, title, text,"
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(entry_date) DO UPDATE SET title = excluded.title,"
                " text = excluded.text, updated_at = excluded.updated_at"
                " WHERE excluded.updated_at > journal_entries.updated_at",
                (row["entry_date"], row.get("title"), row["text"],
                 row["created_at"], row["updated_at"]))
        for row in changes.get("moods", []):
            if not conn.execute("SELECT 1 FROM moods WHERE mood = ? AND date = ?"
                                " AND IFNULL(note, '') = IFNULL(?, '')",
                                (row["mood"], row["date"], row.get("note"))).fetchone():
                conn.execute("INSERT INTO moods (mood, note, date) VALUES (?, ?, ?)",
                             (row["mood"], row.get("note"), row["date"]))
        for row in changes.get("sessions", []):
            if not conn.execute("SELECT 1 FROM sessions WHERE date = ? AND duration = ?"
                                " AND IFNULL(meditation_type, '') = IFNULL(?, '')",
                                (row["date"], row["duration"],
                                 row.get("meditation_type"))).fetchone():
                conn.execute(
                    "INSERT INTO sessions (duration, date, meditation_type, voice,"
                    " sound, mood_before, mood_after) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["duration"], row["date"], row.get("meditation_type"),
                     row.get("voice"), row.get("sound"), row.get("mood_before"),
                     row.get("mood_after")))


def delete_account(path=DB_PATH):
    """Удаляет аккаунт и все данные на сервере; записи на устройстве остаются."""
    _request("DELETE", "/account", token=_token)
    store_token(None)
    sign_out(path)


def get_account(path=DB_PATH):
    with get_connection(path) as conn:
        cur = conn.execute("SELECT * FROM account WHERE id = 1")
        names = [d[0] for d in cur.description]
        return dict(zip(names, cur.fetchone()))
