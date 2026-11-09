"""Модульные проверки логики (случаи T1, T2, T6, T7, T13 из курсовой).
Запуск из папки проекта:  python -m unittest discover tests"""
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta

from logic import database, stress, avatar, journal, billing, account, analytics


class LogicTest(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        database.init_db(self.db)

    def tearDown(self):
        os.remove(self.db)

    def _session_on(self, day):
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO sessions (duration, date) VALUES (10, ?)",
                      (day.isoformat(),))

    def test_t1_high_stress(self):
        self.assertEqual(stress.calculate_stress([8, 3, 4, 7, 2]), (7.8, "высокий"))

    def test_t2_moderate_stress(self):
        self.assertEqual(stress.calculate_stress([5] * 5), (5.6, "умеренный"))

    def test_stress_bounds(self):
        self.assertEqual(stress.calculate_stress([1, 10, 10, 1, 10]), (1.0, "низкий"))
        with self.assertRaises(ValueError):
            stress.calculate_stress([0, 5, 5, 5, 5])
        with self.assertRaises(ValueError):
            stress.calculate_stress([5, 5])

    def test_t6_glowing_after_7_days(self):
        for i in range(7):
            self._session_on(date.today() - timedelta(days=i))
        self.assertEqual(database.get_streak(self.db), 7)
        self.assertEqual(avatar.update_avatar(self.db)[0], "glowing")

    def test_t7_sad_after_3_days(self):
        self._session_on(date.today() - timedelta(days=3))
        self.assertEqual(avatar.update_avatar(self.db)[0], "sad")

    def test_avatar_rules(self):
        self.assertEqual(avatar.choose_state(0, None, "тревога"), "anxious")
        self.assertEqual(avatar.choose_state(1, 0, "усталость"), "tired")
        self.assertEqual(avatar.choose_state(1, 0, "радость"), "calm")

    def test_streak_gap(self):
        self._session_on(date.today())
        self._session_on(date.today() - timedelta(days=2))
        self.assertEqual(database.get_streak(self.db), 1)

    def test_t13_journal_one_entry_per_day(self):
        y = (date.today() - timedelta(days=1)).isoformat()
        journal.save_entry(y, "Первый текст", path=self.db)
        journal.save_entry(y, "Исправленный текст", title="Вечер", path=self.db)
        self.assertEqual(journal.get_entry(y, self.db)[1:3], ("Вечер", "Исправленный текст"))
        marks = journal.get_month_marks(int(y[:4]), int(y[5:7]), self.db)
        self.assertEqual(len(marks), 1)

    def test_billing_test_mode(self):
        self.assertFalse(billing.is_premium(self.db))
        billing.purchase("akii_plus_month", "win", self.db)
        self.assertTrue(billing.is_premium(self.db))
        later = (date.today() + timedelta(days=40)).isoformat()
        self.assertFalse(billing.is_premium(self.db, today=later))
        with self.assertRaises(NotImplementedError):
            billing.purchase("akii_plus_year", "android", self.db)

    def test_login_buttons_by_region(self):
        self.assertEqual(account.available_providers("android", "ru"), ["vk"])
        self.assertEqual(account.available_providers("ios", "us"), ["apple", "google", "vk"])

    def test_pkce(self):
        v, c = account.make_pkce()
        self.assertTrue(43 <= len(v) <= 128)
        self.assertNotIn("=", c)

    def test_achievements(self):
        self._session_on(date.today())
        self.assertIn("Первая медитация", analytics.check_achievements(path=self.db))
        self.assertEqual(analytics.check_achievements(path=self.db), [])


if __name__ == "__main__":
    unittest.main()
