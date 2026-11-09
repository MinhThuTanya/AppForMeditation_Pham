"""Комната Аватара (F.08): 2D-персонаж меняется по стрику и настроению."""
from kivy.animation import Animation
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import analytics, avatar
from screens.widgets import WD_SHORT, bind_bars

Builder.load_string('''
#:import W screens.widgets

<AvatarScreen>:
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
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height
            Title:
                text: app.t("avatar_title", app.lang)
            RelativeLayout:
                size_hint_y: None
                height: dp(250)
                canvas.before:
                    StencilPush
                    RoundedRectangle:
                        pos: 0, 0
                        size: self.size
                        radius: [dp(24)]
                    StencilUse
                    Color:
                        rgba: W.SKY
                    Rectangle:
                        pos: 0, 0
                        size: self.size
                    Color:
                        rgba: (W.SUN2 if root.state_name == "glowing" else W.SUN)
                    Ellipse:
                        pos: self.width - dp(80), self.height - dp(80)
                        size: dp(54), dp(54)
                    Color:
                        rgba: 0.74, 0.83, 0.95, 1
                    Ellipse:
                        pos: -self.width * 0.3, -dp(60)
                        size: self.width * 1.6, dp(120)
                    StencilUnUse
                    RoundedRectangle:
                        pos: 0, 0
                        size: self.size
                        radius: [dp(24)]
                    StencilPop
                Image:
                    source: root.sprite
                    size_hint: None, None
                    size: dp(190), dp(190)
                    pos: self.parent.width / 2 - dp(95), dp(28) + root.bounce
            Label:
                text: app.t("state_label", app.lang) + "  [b]" + root.state_text + "[/b]"
                markup: True
                font_name: W.SANS
                font_size: "14sp"
                color: W.NAVY
                size_hint_y: None
                height: dp(24)
            Body:
                text: root.state_hint
                halign: "center"
                font_size: "12sp"
            Card:
                BoxLayout:
                    size_hint_y: None
                    height: dp(22)
                    Label:
                        text: app.t("week_mood", app.lang)
                        font_name: W.SANS_BOLD
                        font_size: "13sp"
                        color: W.NAVY
                        text_size: self.size
                        halign: "left"
                    Label:
                        text: root.trend
                        font_name: W.SANS_MED
                        font_size: "12sp"
                        color: W.BLUE2
                        text_size: self.size
                        halign: "right"
                Bars:
                    id: bars
                    size_hint_y: None
                    height: dp(120)
                    values: root.week
                    labels: root.week_labels
            BoxLayout:
                size_hint_y: None
                height: dp(52)
                spacing: dp(12)
                Pill:
                    text: app.t("how_are_you", app.lang).upper()
                    on_release: root.how_are_you()
                Pill:
                    text: app.t("calm_down", app.lang).upper()
                    bg: W.WHITE
                    fg: W.NAVY
                    on_release: app.tab("sos")
            Pill:
                text: app.t("open_stats", app.lang)
                bg: 0, 0, 0, 0
                fg: W.BLUE2
                height: dp(40)
                on_release: app.go("stats")
''')

STATE_KEYS = {"calm": "st_calm", "glowing": "st_glowing", "sad": "st_sad",
              "anxious": "st_anxious", "tired": "st_tired"}


class AvatarScreen(MDScreen):
    sprite = StringProperty("assets/images/avatar/calm.png")
    state_name = StringProperty("calm")
    state_text = StringProperty("")
    state_hint = StringProperty("")
    trend = StringProperty("")
    week = ListProperty([])
    week_labels = ListProperty([])
    bounce = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        bind_bars(self.ids.bars)
        App.get_running_app().bind(lang=lambda *a: self.refresh())
        anim = Animation(bounce=8, duration=1.6, t="in_out_sine") + \
            Animation(bounce=0, duration=1.6, t="in_out_sine")
        anim.repeat = True
        anim.start(self)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        state, sprite = avatar.update_avatar()
        self.state_name, self.sprite = state, sprite
        self.state_text = app.t(STATE_KEYS[state])
        self.state_hint = app.t(STATE_KEYS[state] + "_hint")
        data = analytics.week_moods()
        self.week = [v for _, v in data]
        self.week_labels = [WD_SHORT[app.lang][d.weekday()] for d, _ in data]
        filled = [v for v in self.week if v]
        if len(filled) >= 2:
            self.trend = app.t("trend_up") if filled[-1] >= filled[0] else app.t("trend_down")
        else:
            self.trend = ""

    def how_are_you(self):
        app = App.get_running_app()
        self.refresh()
        app.toast(self.state_hint)
