"""Главный экран: уровень стресса, рекомендация, стрик, SOS."""
from datetime import date, datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import DictProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import analytics, database
from logic.audio_player import load_library
from screens.widgets import long_date

Builder.load_string('''
#:import W screens.widgets

<QuickAction@ButtonBehavior+BoxLayout>:
    icon: ""
    text: ""
    orientation: "vertical"
    size_hint_y: None
    height: dp(74)
    padding: 0, dp(8)
    canvas.before:
        Color:
            rgba: W.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]
    MDIcon:
        icon: root.icon
        pos_hint: {"center_x": .5}
        theme_text_color: "Custom"
        text_color: W.BLUE2
    Label:
        text: root.text
        font_name: W.SANS_MED
        font_size: "11sp"
        color: W.NAVY
        size_hint_y: None
        height: dp(20)

<HomeScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(20), dp(24), dp(20), dp(20)
            spacing: dp(14)
            size_hint_y: None
            height: self.minimum_height
            Body:
                text: root.today_text
                font_size: "13sp"
            Title:
                text: root.greeting
            # --- уровень стресса ---
            ClickBox:
                orientation: "vertical"
                size_hint_y: None
                height: dp(132)
                padding: dp(18)
                spacing: dp(4)
                on_release: app.go("stress")
                canvas.before:
                    Color:
                        rgba: W.BLUE2
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(24)]
                    StencilPush
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(24)]
                    StencilUse
                    Color:
                        rgba: W.SUN[0], W.SUN[1], W.SUN[2], 0.9
                    Ellipse:
                        pos: self.right - dp(90), self.top - dp(80)
                        size: dp(130), dp(130)
                    StencilUnUse
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(24)]
                    StencilPop
                Label:
                    text: app.t("stress_level", app.lang)
                    font_name: W.SANS
                    font_size: "12sp"
                    color: 1, 1, 1, 0.85
                    text_size: self.size
                    halign: "left"
                    size_hint_y: None
                    height: dp(18)
                Label:
                    text: root.stress_title
                    font_name: W.SERIF
                    font_size: "24sp"
                    color: W.WHITE
                    text_size: self.size
                    halign: "left"
                    valign: "middle"
                Label:
                    text: root.stress_sub
                    font_name: W.SANS
                    font_size: "12sp"
                    color: 1, 1, 1, 0.85
                    text_size: self.size
                    halign: "left"
                    size_hint_y: None
                    height: dp(18)
                Widget:
                    size_hint_y: None
                    height: dp(10)
                    canvas:
                        Color:
                            rgba: 1, 1, 1, 0.3
                        RoundedRectangle:
                            pos: self.x, self.y + dp(2)
                            size: self.width, dp(6)
                            radius: [dp(3)]
                        Color:
                            rgba: W.SUN2
                        RoundedRectangle:
                            pos: self.x, self.y + dp(2)
                            size: self.width * root.stress_score / 10.0, dp(6)
                            radius: [dp(3)]
            # --- рекомендация ---
            ClickCard:
                orientation: "horizontal"
                spacing: dp(14)
                on_release: root.open_recommendation()
                Widget:
                    size_hint: None, None
                    size: dp(56), dp(56)
                    pos_hint: {"center_y": .5}
                    canvas:
                        Color:
                            rgba: W.SKY
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(16)]
                    MDIcon:
                        icon: "flower-tulip-outline"
                        theme_text_color: "Custom"
                        text_color: W.BLUE2
                        center: self.parent.center
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    pos_hint: {"center_y": .5}
                    Body:
                        text: app.t("recommended_today", app.lang)
                        font_size: "11sp"
                    Label:
                        text: root.rec_title
                        font_name: W.SANS_BOLD
                        font_size: "15sp"
                        color: W.NAVY
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None
                    Body:
                        text: root.rec_sub
                        font_size: "12sp"
            # --- стрик и время ---
            BoxLayout:
                size_hint_y: None
                height: dp(84)
                spacing: dp(12)
                ClickCard:
                    height: dp(84)
                    on_release: app.go("stats")
                    Label:
                        text: str(root.streak)
                        size_hint_y: None
                        height: dp(34)
                        font_name: W.SERIF
                        font_size: "26sp"
                        color: W.BLUE2
                        text_size: self.size
                        halign: "left"
                    Body:
                        text: app.t("days_in_row", app.lang)
                        font_size: "12sp"
                ClickCard:
                    height: dp(84)
                    on_release: app.go("stats")
                    Label:
                        text: str(root.total)
                        size_hint_y: None
                        height: dp(34)
                        font_name: W.SERIF
                        font_size: "26sp"
                        color: W.BLUE2
                        text_size: self.size
                        halign: "left"
                    Body:
                        text: app.t("minutes_total", app.lang)
                        font_size: "12sp"
            # --- быстрые действия ---
            GridLayout:
                cols: 4
                spacing: dp(10)
                size_hint_y: None
                height: dp(74)
                QuickAction:
                    icon: "emoticon-outline"
                    text: app.t("qa_mood", app.lang)
                    on_release: app.go("mood")
                QuickAction:
                    icon: "weather-night"
                    text: app.t("qa_sleep", app.lang)
                    on_release: app.go("dreams")
                QuickAction:
                    icon: "chart-bar"
                    text: app.t("qa_stats", app.lang)
                    on_release: app.go("stats")
                QuickAction:
                    icon: "cog-outline"
                    text: app.t("qa_settings", app.lang)
                    on_release: app.go("settings")
            Pill:
                text: app.t("sos_button", app.lang).upper()
                bg: W.SOS
                on_release: app.tab("sos")
''')

# Рекомендация по уровню стресса (персонализированный подбор, задача 2 ТЗ)
RECOMMEND = {"высокий": "anxiety", "умеренный": "evening_calm", "низкий": "focus", None: "anxiety"}
STRESS_KEYS = {"высокий": "stress_high", "умеренный": "stress_moderate", "низкий": "stress_low"}


class HomeScreen(MDScreen):
    today_text = StringProperty("")
    greeting = StringProperty("")
    stress_title = StringProperty("")
    stress_sub = StringProperty("")
    stress_score = NumericProperty(0)
    streak = NumericProperty(0)
    total = NumericProperty(0)
    rec = DictProperty({})
    rec_title = StringProperty("")
    rec_sub = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        App.get_running_app().bind(lang=lambda *a: self.refresh())

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        lang = app.lang
        self.today_text = long_date(date.today(), lang)
        h = datetime.now().hour
        self.greeting = app.t("good_morning" if 5 <= h < 12 else "good_day" if h < 18
                              else "good_evening")
        last = database.get_last_stress()
        if last:
            score, category, _ = last
            self.stress_score = score
            self.stress_title = app.t(STRESS_KEYS[category])
            self.stress_sub = app.t("stress_index").format(str(score).replace(".", "," if lang == "ru" else "."))
        else:
            category = None
            self.stress_score = 0
            self.stress_title = app.t("stress_unknown")
            self.stress_sub = app.t("take_test")
        s = analytics.summary()
        self.streak, self.total = s["streak"], s["total"]
        item = next(i for i in load_library()["items"] if i["id"] == RECOMMEND[category])
        settings = database.get_settings()
        self.rec = {"id": item["id"], "title": item["title"][lang],
                    "subtitle": app.t("rec_sub").format(settings["default_duration"],
                                                        app.t("voice_" + settings["default_voice"]).lower())}
        self.rec_title, self.rec_sub = self.rec["title"], self.rec["subtitle"]

    def open_recommendation(self):
        App.get_running_app().tab("player", item_id=self.rec["id"])
