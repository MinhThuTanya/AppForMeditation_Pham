"""Проверка сервера Akii Server (нужны пакеты из server/requirements.txt).
Запуск из папки проекта:  python -m unittest tests.test_server"""
import os
import re
import unittest

try:
    os.environ["AKII_DATABASE_URL"] = "sqlite:///./data/test_server.db"
    from fastapi.testclient import TestClient
    from server.main import app
except ImportError as e:            # серверные библиотеки не установлены
    app = None
    REASON = str(e)


@unittest.skipIf(app is None, "нет серверных библиотек")
class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove("data/test_server.db")
        except OSError:
            pass

    def test_register_confirm_login_sync_delete(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            r = self.c.post("/auth/register", json={"email": "tanya@example.com",
                                                    "password": "12345678", "display_name": "Таня"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.post("/auth/login", json={"email": "tanya@example.com",
                                                          "password": "12345678"}).status_code, 403)
        token = re.search(r"token=([\w-]+)", buf.getvalue()).group(1)
        self.assertEqual(self.c.get("/auth/confirm", params={"token": token}).status_code, 200)
        self.assertEqual(self.c.post("/auth/login", json={"email": "tanya@example.com",
                                                          "password": "wrong-pass"}).status_code, 401)
        data = self.c.post("/auth/login", json={"email": "tanya@example.com",
                                                "password": "12345678"}).json()
        h = {"Authorization": "Bearer " + data["access_token"]}
        entry = {"entry_date": "2026-11-08", "title": "Вечер", "text": "Текст",
                 "created_at": "2026-11-08T20:00:00", "updated_at": "2026-11-08T20:00:00"}
        r = self.c.post("/sync", json={"changes": {"journal_entries": [entry]}}, headers=h).json()
        self.assertEqual(r["changes"]["journal_entries"][0]["text"], "Текст")
        older = dict(entry, text="Старый", updated_at="2026-11-01T10:00:00")
        r = self.c.post("/sync", json={"changes": {"journal_entries": [older]}}, headers=h).json()
        self.assertEqual(r["changes"]["journal_entries"][0]["text"], "Текст")   # побеждает более поздняя
        self.assertEqual(self.c.delete("/account", headers=h).status_code, 200)
        self.assertEqual(self.c.post("/sync", json={"changes": {}}, headers=h).status_code, 401)

    def test_same_email_merges(self):
        from server.auth import link_identity
        from server.models import SessionLocal
        db = SessionLocal()
        a = link_identity(db, "google", "g-1", "same@example.com", "A")
        b = link_identity(db, "vk", "vk-1", "same@example.com", "A")
        self.assertEqual(a["user_id"], b["user_id"])      # случай T21
        db.close()


if __name__ == "__main__":
    unittest.main()
