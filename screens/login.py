"""Экран входа (F.14) и форма входа / регистрации по почте.
Аккаунт необязателен: «Продолжить без аккаунта» открывает все функции."""
import secrets
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivymd.uix.screen import MDScreen

from logic import account

Builder.load_string('''
#:import W screens.widgets

<LangSwitch@BoxLayout>:
    size_hint: None, None
    size: dp(96), dp(34)
    padding: dp(3)
    canvas.before:
        Color:
            rgba: W.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]
    Chip:
        text: "RU"
        group: "lang"
        allow_no_selection: False
        state: "down" if app.lang == "ru" else "normal"
        color_on: W.NAVY
        size_hint: 0.5, 1
        width: 0
        on_release: app.set_language("ru")
    Chip:
        text: "EN"
        group: "lang"
        allow_no_selection: False
        state: "down" if app.lang == "en" else "normal"
        color_on: W.NAVY
        size_hint: 0.5, 1
        width: 0
        on_release: app.set_language("en")

<LoginScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
        Color:
            rgba: W.SUN
        Ellipse:
            size: dp(230), dp(230)
            pos: self.right - dp(150), self.top - dp(330)
    LangSwitch:
        pos: root.right - dp(116), root.top - dp(60)
    BoxLayout:
        orientation: "vertical"
        padding: dp(24), dp(24), dp(24), dp(24)
        spacing: dp(10)
        Widget:
            size_hint_y: None
            height: dp(70)
        Title:
            text: app.t("welcome_title", app.lang)
            font_size: "34sp" if app.lang == "en" else "30sp"
            size_hint_x: 0.75
        Body:
            text: app.t("welcome_sub", app.lang)
            size_hint_x: 0.55
        Widget:
        BoxLayout:
            id: providers
            orientation: "vertical"
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
        Pill:
            text: app.t("signup_email", app.lang).upper()
            on_release: app.go("email", register=True)
        BoxLayout:
            size_hint_y: None
            height: dp(32)
            Label:
                text: app.t("have_account", app.lang) + "  [color=#3D6FD6][b]" + app.t("log_in", app.lang) + "[/b][/color]"
                markup: True
                font_name: W.SANS
                font_size: "13sp"
                color: W.MUTED
                on_touch_down: if self.collide_point(*args[1].pos): app.go("email", register=False)
        Label:
            text: "[u]" + app.t("continue_without", app.lang) + "[/u]"
            markup: True
            font_name: W.SANS_BOLD
            font_size: "14sp"
            color: W.NAVY
            size_hint_y: None
            height: dp(36)
            on_touch_down: if self.collide_point(*args[1].pos): app.finish_onboarding()

<EmailScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(14)
        MDIconButton:
            icon: "arrow-left"
            on_release: app.back()
        Title:
            text: app.t("signup_title" if root.register else "login_title", app.lang)
        Body:
            text: app.t("account_why", app.lang)
        Field:
            id: name
            opacity: 1 if root.register else 0
            disabled: not root.register
            size_hint_y: None
            height: dp(56) if root.register else 0
            hint_text: app.t("your_name", app.lang)
        Field:
            id: email
            hint_text: app.t("email", app.lang)
        Field:
            id: password
            password: True
            hint_text: app.t("password", app.lang)
        Pill:
            text: app.t("signup_btn" if root.register else "login_btn", app.lang).upper()
            on_release: root.submit()
        Label:
            text: "[u]" + app.t("to_login" if root.register else "to_signup", app.lang) + "[/u]"
            markup: True
            font_name: W.SANS_MED
            font_size: "13sp"
            color: W.BLUE2
            size_hint_y: None
            height: dp(30)
            on_touch_down: if self.collide_point(*args[1].pos): root.register = not root.register
        Widget:
''')

PROVIDER_STYLE = {   # цвет кнопки, цвет текста, ключ перевода
    "apple": ((0.07, 0.07, 0.07, 1), (1, 1, 1, 1), "with_apple"),
    "google": ((1, 1, 1, 1), (0.106, 0.122, 0.294, 1), "with_google"),
    "vk": ((0, 0.467, 1, 1), (1, 1, 1, 1), "with_vk"),
}


class LoginScreen(MDScreen):
    def on_pre_enter(self, *_):
        from screens.widgets import Pill
        app = App.get_running_app()
        box = self.ids.providers
        box.clear_widgets()
        for p in account.available_providers(app.platform, app.region):
            bg, fg, key = PROVIDER_STYLE[p]
            btn = Pill(bg=bg, fg=fg)
            btn.text = app.t(key).upper()
            btn.bind(on_release=lambda w, prov=p: self.oauth(prov))
            app.bind(lang=lambda *a, b=btn, k=key: setattr(b, "text", app.t(k).upper()))
            box.add_widget(btn)

    def oauth(self, provider):
        """Вход через сервис по OAuth 2.0 + PKCE во внешнем браузере (рисунок 8)."""
        app = App.get_running_app()
        client_id = account.CLIENT_IDS.get(provider)
        if not client_id:
            app.toast(app.t("oauth_not_configured"))
            return
        verifier, challenge = account.make_pkce()
        self._pending = (provider, verifier, secrets.token_urlsafe(16))
        webbrowser.open(account.build_auth_url(provider, client_id, challenge,
                                               self._pending[2]))


class EmailScreen(MDScreen):
    register = BooleanProperty(True)

    def prepare(self, register=True):
        self.register = register

    def submit(self):
        app = App.get_running_app()
        email = self.ids.email.text.strip()
        password = self.ids.password.text
        if "@" not in email or len(password) < 8:
            app.toast(app.t("email_invalid"))
            return
        try:
            if self.register:
                account.register_email(email, password, self.ids.name.text.strip())
                app.toast(app.t("check_email"))
                self.register = False
            else:
                account.sign_in_email(email, password)
                try:
                    account.sync()
                except account.ServerError:
                    pass
                app.toast(app.t("signed_in"))
                app.finish_onboarding()
        except account.ServerError as e:
            msg = str(e)
            app.toast(app.t(msg) if msg in ("server_unavailable",) else msg)
