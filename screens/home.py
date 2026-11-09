"""Главный экран: уровень стресса, рекомендация, стрик, SOS."""
from datetime import date, datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.properties import DictProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import analytics, database
from logic.audio_player import load_library
from screens.widgets import long_date

Builder.load_string('''
#:import W screens.widgets

# Кнопка-облачко в горошек (быстрые действия)
<CloudAction@ClickBox>:
    icon: ""
    text: ""
    orientation: "vertical"
    size_hint_y: None
    height: dp(92)
    padding: 0, dp(14), 0, dp(18)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            source: "assets/images/buttons/cloud.png"
            pos: self.pos
            size: self.size
    MDIcon:
        icon: root.icon
        pos_hint: {"center_x": .55}
        theme_text_color: "Custom"
        text_color: W.BLUE2
    Label:
        text: root.text
        font_name: W.ROUND
        font_size: "12sp"
        color: W.NAVY
        size_hint_y: None
        height: dp(18)

# Плитка с числом на фоне-картинке (овал со стрелками, каракули)
<ArtTile@ClickBox>:
    value: ""
    caption: ""
    bg_source: ""
    orientation: "vertical"
    padding: dp(18), dp(22), dp(18), dp(16)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            source: self.bg_source
            pos: self.pos
            size: self.size
    Label:
        text: root.value
        font_name: W.DISPLAY
        font_size: "30sp"
        color: W.BLUE2
    Label:
        text: root.caption
        font_name: W.ROUND
        font_size: "12sp"
        color: W.NAVY
        size_hint_y: None
        height: dp(18)

# Декоративная картинка (заменяется своими артами в assets/images/deco/)
<Deco@Image>:
    size_hint: None, None
    fit_mode: "contain"

<HomeScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    # плавающие пузыри и рыбка на фоне
    Deco:
        source: "assets/images/deco/bubble.png"
        size: dp(46), dp(46)
        pos: root.width - dp(70), root.height * 0.42 + root.bob
        opacity: 0.8
    Deco:
        source: "assets/images/deco/bubble.png"
        size: dp(26), dp(26)
        pos: root.width - dp(40), root.height * 0.36 - root.bob * 0.6
        opacity: 0.7
    Deco:
        source: "assets/images/deco/bubble.png"
        size: dp(20), dp(20)
        pos: dp(14), root.height * 0.30 + root.bob * 0.8
        opacity: 0.7
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(20), dp(22), dp(20), 0
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height
            # --- приветствие с персонажем ---
            RelativeLayout:
                size_hint_y: None
                height: dp(78)
                Label:
                    text: root.today_text
                    font_name: W.ROUND
                    font_size: "13sp"
                    color: W.MUTED
                    size_hint: None, None
                    size: self.texture_size
                    pos: 0, dp(56)
                Label:
                    text: root.greeting
                    font_name: W.DISPLAY
                    font_size: "30sp"
                    color: W.BLUE2
                    size_hint: None, None
                    size: self.texture_size
                    pos: 0, dp(6)
                Deco:
                    source: "assets/images/deco/face_spiky.png"
                    size: dp(70), dp(70)
                    pos: self.parent.width - dp(70), dp(4)
                Deco:
                    source: "assets/images/deco/arrow.png"
                    size: dp(46), dp(34)
                    pos: self.parent.width - dp(118), dp(40)
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
                    Color:
                        rgba: 1, 1, 1, 0.55
                    Rectangle:
                        source: "assets/images/deco/swirl.png"
                        pos: self.right - dp(150), self.y - dp(18)
                        size: dp(120), dp(80)
                    StencilUnUse
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(24)]
                    StencilPop
                Label:
                    text: app.t("stress_level", app.lang)
                    font_name: W.ROUND
                    font_size: "12sp"
                    color: 1, 1, 1, 0.9
                    text_size: self.size
                    halign: "left"
                    size_hint_y: None
                    height: dp(18)
                Label:
                    text: root.stress_title
                    font_name: W.DISPLAY
                    font_size: "24sp"
                    color: W.WHITE
                    text_size: self.size
                    halign: "left"
                    valign: "middle"
                Label:
                    text: root.stress_sub
                    font_name: W.ROUND
                    font_size: "12sp"
                    color: 1, 1, 1, 0.9
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
            # --- рекомендация: рваная бумага на клетчатой ткани ---
            ClickBox:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(112)
                padding: dp(40), dp(36), dp(14), dp(22)
                spacing: dp(12)
                on_release: root.open_recommendation()
                canvas.before:
                    Color:
                        rgba: 1, 1, 1, 1
                    Rectangle:
                        source: "assets/images/buttons/paper.png"
                        pos: self.pos
                        size: self.size
                Deco:
                    source: "assets/images/deco/face_curly.png"
                    size: dp(50), dp(50)
                    pos_hint: {"center_y": .5}
                BoxLayout:
                    orientation: "vertical"
                    Label:
                        text: app.t("recommended_today", app.lang)
                        font_name: W.ROUND
                        font_size: "11sp"
                        color: W.MUTED
                        text_size: self.size
                        halign: "left"
                        valign: "bottom"
                    Label:
                        text: root.rec_title
                        font_name: W.DISPLAY
                        font_size: "17sp"
                        color: W.NAVY
                        text_size: self.size
                        halign: "left"
                        valign: "middle"
                    Label:
                        text: root.rec_sub
                        font_name: W.ROUND
                        font_size: "11sp"
                        color: W.MUTED
                        text_size: self.size
                        halign: "left"
                        valign: "top"
            # --- стрик и время ---
            BoxLayout:
                size_hint_y: None
                height: dp(112)
                spacing: dp(8)
                ArtTile:
                    value: str(root.streak)
                    caption: app.t("days_in_row", app.lang)
                    bg_source: "assets/images/buttons/oval.png"
                    padding: dp(18), dp(30), dp(18), dp(14)
                    on_release: app.go("stats")
                ArtTile:
                    value: str(root.total)
                    caption: app.t("minutes_total", app.lang)
                    bg_source: "assets/images/buttons/scribble.png"
                    on_release: app.go("stats")
            # --- быстрые действия: облачка ---
            GridLayout:
                cols: 4
                spacing: dp(6)
                size_hint_y: None
                height: dp(92)
                CloudAction:
                    icon: "emoticon-outline"
                    text: app.t("qa_mood", app.lang)
                    on_release: app.go("mood")
                CloudAction:
                    icon: "weather-night"
                    text: app.t("qa_sleep", app.lang)
                    on_release: app.go("dreams")
                CloudAction:
                    icon: "chart-bar"
                    text: app.t("qa_stats", app.lang)
                    on_release: app.go("stats")
                CloudAction:
                    icon: "cog-outline"
                    text: app.t("qa_settings", app.lang)
                    on_release: app.go("settings")
            Pill:
                text: app.t("sos_button", app.lang).upper()
                font_name: W.ROUND
                font_size: "15sp"
                bg: W.SOS
                on_release: app.tab("sos")
            # --- нижний декор: рыбки и облака-волны ---
            RelativeLayout:
                size_hint_y: None
                height: dp(120)
                Image:
                    source: "assets/images/deco/clouds.png"
                    fit_mode: "fill"
                    size_hint: None, None
                    size: self.parent.width + dp(40), dp(90)
                    pos: -dp(20), 0
                Deco:
                    source: "assets/images/deco/fish.png"
                    size: dp(70), dp(36)
                    pos: root.fish_x, dp(70)
                Deco:
                    source: "assets/images/deco/face_sleepy.png"
                    size: dp(48), dp(48)
                    pos: self.parent.width - dp(56), dp(66)
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

    bob = NumericProperty(0)        # покачивание пузырей
    fish_x = NumericProperty(-80)   # рыбка плывёт по волнам

    def __init__(self, **kw):
        super().__init__(**kw)
        App.get_running_app().bind(lang=lambda *a: self.refresh())
        bob = Animation(bob=14, duration=2.2, t="in_out_sine") + Animation(bob=0, duration=2.2, t="in_out_sine")
        bob.repeat = True
        bob.start(self)
        self._swim()

    def _swim(self, *_):
        self.fish_x = -80
        anim = Animation(fish_x=self.width + 20, duration=14, t="linear")
        anim.bind(on_complete=self._swim)
        anim.start(self)

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
