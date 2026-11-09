"""Akii — мобильное приложение для медитации и отслеживания состояния.
Точка входа: класс приложения, ScreenManager, нижнее меню.
Запуск на компьютере: python main.py (из папки проекта)."""
import locale
import os
import sys

# Все пути в приложении относительные (data/, assets/, locales/),
# поэтому рабочей папкой делаем папку проекта.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from kivy.utils import platform  # noqa: E402

if platform == "ios":
    # Пакет приложения на iOS доступен только для чтения: база данных и языковые
    # файлы копируются в папку документов (проверяется при сборке на Mac).
    import shutil
    docs = os.path.expanduser("~/Documents/akii")
    os.makedirs(docs, exist_ok=True)
    if not os.path.isdir(os.path.join(docs, "locales")):
        shutil.copytree(os.path.join(APP_DIR, "locales"), os.path.join(docs, "locales"))
    from kivy.resources import resource_add_path
    resource_add_path(APP_DIR)
    os.chdir(docs)
    for sub in ("assets",):
        if not os.path.exists(sub):
            os.symlink(os.path.join(APP_DIR, sub), sub)

from kivy.config import Config  # noqa: E402

if platform not in ("android", "ios"):
    # На компьютере окно размером с телефон
    Config.set("graphics", "width", "400")
    Config.set("graphics", "height", "820")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.properties import BooleanProperty, StringProperty  # noqa: E402
from kivymd.app import MDApp  # noqa: E402
from kivymd.uix.screenmanager import MDScreenManager  # noqa: E402
from kivy.uix.screenmanager import FadeTransition, SlideTransition  # noqa: E402

from logic import billing, i18n  # noqa: E402
from logic.account import get_account  # noqa: E402
from logic.database import init_db  # noqa: E402
from screens.widgets import BG  # noqa: E402


class AkiiApp(MDApp):
    lang = StringProperty("ru")          # смена языка перерисовывает экраны
    premium = BooleanProperty(False)     # активна ли подписка Akii Plus
    platform = platform

    # ---------- запуск ----------
    def build_config(self, config):
        config.setdefaults("akii", {"onboarded": "0"})

    def build(self):
        self.title = "Akii"
        self.icon = "assets/icons/icon.png"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Royalblue"
        Window.clearcolor = BG
        init_db()
        i18n.init_language()
        self.lang = i18n._lang
        self.premium = billing.is_premium()

        from screens import (splash, login, main_screen, stats, stress_test,
                             mood, journal, plus, settings, dreams)
        sm = MDScreenManager(transition=FadeTransition(duration=0.25))
        for screen in (splash.SplashScreen(name="splash"),
                       login.LoginScreen(name="login"),
                       login.EmailScreen(name="email"),
                       main_screen.MainScreen(name="main"),
                       stats.StatsScreen(name="stats"),
                       stress_test.StressTestScreen(name="stress"),
                       mood.MoodScreen(name="mood"),
                       journal.EntryScreen(name="entry"),
                       plus.PlusScreen(name="plus"),
                       settings.SettingsScreen(name="settings"),
                       dreams.DreamsScreen(name="dreams")):
            sm.add_widget(screen)
        self.sm = sm
        self._history = []
        Window.bind(on_keyboard=self._on_key)
        return sm

    # ---------- перевод ----------
    def t(self, key, *_):
        """В kv: app.t("ключ", app.lang) — строка обновится при смене языка."""
        return i18n.tr(key)

    def set_language(self, lang):
        i18n.set_language(lang)
        self.lang = i18n._lang

    @property
    def region(self):
        code = (locale.getlocale()[0] or "").lower()
        return "ru" if code.startswith("ru") or self.lang == "ru" else "intl"

    # ---------- навигация ----------
    def after_splash(self):
        onboarded = self.config.get("akii", "onboarded") == "1"
        signed_in = bool(get_account()["user_id"])
        self.go("main" if (onboarded or signed_in) else "login", remember=False)

    def finish_onboarding(self):
        self.config.set("akii", "onboarded", "1")
        self.config.write()
        self._history.clear()
        self.go("main", remember=False)

    def go(self, name, remember=True, **kwargs):
        if remember and self.sm.current not in ("splash",):
            self._history.append(self.sm.current)
        screen = self.sm.get_screen(name)
        if hasattr(screen, "prepare"):
            screen.prepare(**kwargs)
        self.sm.current = name

    def back(self):
        if self._history:
            self.sm.current = self._history.pop()
            screen = self.sm.current_screen
            if hasattr(screen, "on_back"):
                screen.on_back()
            return True
        return False

    def tab(self, name, **kwargs):
        """Переход на вкладку нижнего меню."""
        self._history.clear()
        if self.sm.current != "main":
            self.sm.current = "main"
        self.sm.get_screen("main").switch(name, **kwargs)

    def _on_key(self, window, key, *args):
        if key == 27:                     # «Назад» на Android / Esc
            if self.sm.current == "main":
                return self.sm.get_screen("main").back()
            return self.back()
        return False

    # ---------- общие действия ----------
    def toast(self, text):
        from screens.widgets import toast
        toast(text)

    def refresh_premium(self):
        self.premium = billing.is_premium()

    def require_premium(self, item_title=""):
        """Если подписки нет — открывает экран Akii Plus. Возвращает True,
        если контент можно открыть."""
        if self.premium:
            return True
        self.go("plus")
        return False

    def on_start(self):
        Clock.schedule_once(lambda dt: self.sm.get_screen("splash").start(), 0)
        self._reminded = None
        Clock.schedule_interval(self.check_reminder, 30)

    def check_reminder(self, *_):
        """Напоминание «Время для вашей практики» (F.02.01), пока приложение запущено.
        Фоновые уведомления при закрытом приложении настраиваются при сборке под телефон."""
        from datetime import datetime
        from logic.database import get_settings
        s = get_settings()
        now = datetime.now()
        if not s["reminder_enabled"] or now.strftime("%H:%M") != s["reminder_time"]:
            return
        if self._reminded == now.date():
            return
        self._reminded = now.date()
        try:
            from plyer import notification
            notification.notify(title="Akii", message=self.t("reminder_message"),
                                app_name="Akii", timeout=10)
        except Exception:
            self.toast(self.t("reminder_message"))

    def on_pause(self):
        return True


if __name__ == "__main__":
    AkiiApp().run()
