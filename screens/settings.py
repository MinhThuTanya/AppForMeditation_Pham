"""Настройки: язык (F.12), напоминания (F.02), аккаунт (F.14), подписка."""
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import account, billing, database
from screens.widgets import Chip

Builder.load_string('''
#:import W screens.widgets

<SectionTitle@Label>:
    font_name: W.SANS_BOLD
    font_size: "14sp"
    color: W.NAVY
    size_hint_y: None
    height: dp(22)
    text_size: self.size
    halign: "left"

<SettingsScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(16), dp(12), dp(16), 0
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            MDIconButton:
                icon: "arrow-left"
                on_release: app.back()
            Widget:
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(4), 0, dp(4), dp(24)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                Title:
                    text: app.t("settings_title", app.lang)
                Card:
                    SectionTitle:
                        text: app.t("language", app.lang)
                    BoxLayout:
                        size_hint_y: None
                        height: dp(36)
                        spacing: dp(8)
                        Chip:
                            text: "Русский"
                            group: "set_lang"
                            allow_no_selection: False
                            state: "down" if app.lang == "ru" else "normal"
                            on_release: app.set_language("ru")
                        Chip:
                            text: "English"
                            group: "set_lang"
                            allow_no_selection: False
                            state: "down" if app.lang == "en" else "normal"
                            on_release: app.set_language("en")
                        Widget:
                Card:
                    SectionTitle:
                        text: app.t("reminders", app.lang)
                    Body:
                        text: app.t("reminder_text", app.lang)
                    BoxLayout:
                        id: reminder_times
                        size_hint_y: None
                        height: dp(36)
                        spacing: dp(8)
                    Body:
                        text: app.t("reminder_note", app.lang)
                        font_size: "11sp"
                # --- аккаунт ---
                Card:
                    SectionTitle:
                        text: app.t("account", app.lang)
                    Body:
                        text: root.account_text
                    Pill:
                        text: app.t("login_or_signup", app.lang).upper()
                        height: dp(44) if not root.signed_in else 0
                        opacity: 0 if root.signed_in else 1
                        disabled: root.signed_in
                        on_release: app.go("login")
                    BoxLayout:
                        size_hint_y: None
                        height: dp(36) if root.signed_in else 0
                        opacity: 1 if root.signed_in else 0
                        disabled: not root.signed_in
                        spacing: dp(8)
                        Chip:
                            id: sync_journal
                            text: app.t("sync_journal", app.lang)
                            on_release: root.set_sync_journal(self.state == "down")
                        Widget:
                    BoxLayout:
                        size_hint_y: None
                        height: dp(44) if root.signed_in else 0
                        opacity: 1 if root.signed_in else 0
                        disabled: not root.signed_in
                        spacing: dp(8)
                        Pill:
                            text: app.t("sync_now", app.lang)
                            height: dp(44)
                            on_release: root.sync_now()
                        Pill:
                            text: app.t("sign_out", app.lang)
                            height: dp(44)
                            bg: W.SKY
                            fg: W.NAVY
                            on_release: root.sign_out()
                    Pill:
                        text: app.t("delete_account", app.lang)
                        height: dp(40) if root.signed_in else 0
                        opacity: 1 if root.signed_in else 0
                        disabled: not root.signed_in
                        bg: 0, 0, 0, 0
                        fg: W.SOS
                        on_release: root.delete_account()
                # --- подписка ---
                Card:
                    SectionTitle:
                        text: "Akii Plus"
                    Body:
                        text: root.plus_text
                    Pill:
                        text: app.t("open_plus", app.lang).upper()
                        height: dp(44)
                        on_release: app.go("plus")
                    Pill:
                        text: app.t("reset_test_sub", app.lang)
                        height: dp(36) if app.platform not in ("android", "ios") and app.premium else 0
                        opacity: 1 if app.platform not in ("android", "ios") and app.premium else 0
                        bg: 0, 0, 0, 0
                        fg: W.MUTED
                        on_release: root.reset_test_sub()
                Body:
                    text: "Akii 1.0 · " + app.t("about", app.lang)
                    font_size: "11sp"
                    halign: "center"
''')

TIMES = ["off", "08:00", "09:00", "13:00", "21:00"]


class SettingsScreen(MDScreen):
    account_text = StringProperty("")
    plus_text = StringProperty("")
    signed_in = BooleanProperty(False)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        s = database.get_settings()
        box = self.ids.reminder_times
        box.clear_widgets()
        current = s["reminder_time"] if s["reminder_enabled"] else "off"
        for t in TIMES:
            c = Chip(text=app.t("off") if t == "off" else t, group="rem", allow_no_selection=False,
                     state="down" if t == current else "normal")
            c.bind(on_release=lambda w, v=t: self.set_reminder(v))
            box.add_widget(c)
        acc = account.get_account()
        self.signed_in = bool(acc["user_id"])
        if self.signed_in:
            last = acc["last_sync_at"] or app.t("never")
            self.account_text = app.t("signed_in_as").format(acc["email"] or acc["provider"], last)
            self.ids.sync_journal.state = "down" if acc["sync_journal"] else "normal"
        else:
            self.account_text = app.t("no_account")
        sub = billing.get_subscription()
        self.plus_text = app.t("plus_active").format(sub[2]) if app.premium else app.t("plus_inactive")

    def set_reminder(self, value):
        if value == "off":
            database.update_setting("reminder_enabled", 0)
        else:
            database.update_setting("reminder_enabled", 1)
            database.update_setting("reminder_time", value)

    def set_sync_journal(self, on):
        with database.get_connection() as conn:
            conn.execute("UPDATE account SET sync_journal = ? WHERE id = 1", (1 if on else 0,))

    def sync_now(self):
        app = App.get_running_app()
        try:
            account.sync()
            app.toast(app.t("synced"))
        except account.ServerError as e:
            app.toast(app.t(str(e)) if str(e) in ("server_unavailable", "not_signed_in") else str(e))
        self.refresh()

    def sign_out(self):
        account.store_token(None)
        account.sign_out()
        App.get_running_app().toast(App.get_running_app().t("signed_out"))
        self.refresh()

    def delete_account(self):
        app = App.get_running_app()
        from screens.widgets import ask

        def confirm(v):
            if v != "yes":
                return
            try:
                account.delete_account()
                app.toast(app.t("account_deleted"))
            except account.ServerError as e:
                app.toast(app.t(str(e)) if str(e) in ("server_unavailable", "not_signed_in") else str(e))
            self.refresh()
        ask(app.t("delete_q"), [("yes", app.t("delete")), ("no", app.t("cancel"))], confirm,
            subtitle=app.t("delete_sub"))

    def reset_test_sub(self):
        billing.deactivate()
        app = App.get_running_app()
        app.refresh_premium()
        self.refresh()
