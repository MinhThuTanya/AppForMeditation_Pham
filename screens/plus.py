"""Экран подписки Akii Plus (F.13). На компьютере работает тестовый режим без оплаты;
на телефоне оплата идёт через RuStore (Android) или App Store (iOS) — этап 9.3."""
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import billing

Builder.load_string('''
#:import W screens.widgets

<PlanCard@ButtonBehavior+BoxLayout>:
    selected: False
    title: ""
    sub: ""
    badge: ""
    orientation: "vertical"
    padding: dp(14), dp(10)
    size_hint_y: None
    height: dp(76)
    canvas.before:
        Color:
            rgba: W.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]
        Color:
            rgba: W.BLUE2 if self.selected else (0, 0, 0, 0)
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(18)
            width: 1.6
    Label:
        text: root.title
        font_name: W.SANS_BOLD
        font_size: "15sp"
        color: W.NAVY
        text_size: self.size
        halign: "left"
    Label:
        text: root.sub
        font_name: W.SANS
        font_size: "11sp"
        color: W.MUTED
        text_size: self.size
        halign: "left"

<Feature@BoxLayout>:
    icon: ""
    text: ""
    size_hint_y: None
    height: dp(26)
    spacing: dp(10)
    MDIcon:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: W.BLUE2
        size_hint_x: None
        width: dp(24)
        pos_hint: {"center_y": .5}
    Label:
        text: root.text
        font_name: W.SANS
        font_size: "14sp"
        color: W.NAVY
        text_size: self.size
        halign: "left"
        valign: "middle"

<PlusScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
        Color:
            rgba: W.SUN
        Ellipse:
            size: dp(200), dp(200)
            pos: self.right - dp(120), self.top - dp(250)
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(20), dp(12), dp(20), dp(20)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                MDIconButton:
                    icon: "close"
                    on_release: app.back()
                Widget:
            Label:
                text: "Akii [color=#3D6FD6]Plus[/color]"
                markup: True
                font_name: W.SERIF
                font_size: "34sp"
                color: W.NAVY
                size_hint_y: None
                height: dp(46)
                text_size: self.size
                halign: "left"
            Body:
                text: app.t("plus_sub", app.lang)
            Card:
                spacing: dp(10)
                Feature:
                    icon: "music-note"
                    text: app.t("plus_f1", app.lang)
                Feature:
                    icon: "tune-vertical"
                    text: app.t("plus_f2", app.lang)
                Feature:
                    icon: "flower-tulip-outline"
                    text: app.t("plus_f3", app.lang)
                Feature:
                    icon: "weather-windy"
                    text: app.t("plus_f4", app.lang)
                Feature:
                    icon: "file-chart-outline"
                    text: app.t("plus_f5", app.lang)
                Feature:
                    icon: "tshirt-crew-outline"
                    text: app.t("plus_f6", app.lang)
            Body:
                text: root.status_text
                color: W.BLUE2
                opacity: 1 if root.status_text else 0
            BoxLayout:
                size_hint_y: None
                height: dp(76)
                spacing: dp(12)
                PlanCard:
                    title: app.t("plan_year", app.lang)
                    sub: app.t("plan_year_sub", app.lang)
                    selected: root.plan == "akii_plus_year"
                    on_release: root.plan = "akii_plus_year"
                PlanCard:
                    title: app.t("plan_month", app.lang)
                    sub: app.t("plan_month_sub", app.lang)
                    selected: root.plan == "akii_plus_month"
                    on_release: root.plan = "akii_plus_month"
            Pill:
                text: app.t("try_free", app.lang).upper()
                on_release: root.buy()
            Pill:
                text: app.t("restore", app.lang)
                bg: 0, 0, 0, 0
                fg: W.BLUE2
                height: dp(36)
                on_release: root.restore()
            Body:
                text: app.t("plus_footer", app.lang) + ("\\n" + app.t("plus_test_mode", app.lang) if app.platform not in ("android", "ios") else "")
                halign: "center"
                font_size: "11sp"
''')


class PlusScreen(MDScreen):
    plan = StringProperty("akii_plus_year")
    status_text = StringProperty("")

    def on_pre_enter(self, *_):
        self._status()

    def _status(self):
        app = App.get_running_app()
        sub = billing.get_subscription()
        if billing.is_premium():
            self.status_text = app.t("plus_active").format(sub[2])
        else:
            self.status_text = ""

    def buy(self):
        app = App.get_running_app()
        try:
            billing.purchase(self.plan, app.platform)
        except NotImplementedError:
            app.toast(app.t("store_not_ready"))
            return
        app.refresh_premium()
        self._status()
        app.toast(app.t("plus_thanks"))

    def restore(self):
        app = App.get_running_app()
        try:
            ok = billing.restore(app.platform)
        except NotImplementedError:
            app.toast(app.t("store_not_ready"))
            return
        app.refresh_premium()
        self._status()
        app.toast(app.t("restored") if ok else app.t("nothing_to_restore"))
