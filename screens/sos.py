"""SOS-дыхание (F.07): вдох 4 с, выдох 6 с — 6 циклов в минуту. Всегда бесплатно.
Квадратное дыхание и 4-7-8 доступны в Akii Plus."""
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic.audio_player import AudioPlayer, load_library
from screens.widgets import Chip

# фазы: (ключ подписи, длительность, целевой размер круга)
TECHNIQUES = {
    "sos": {"premium": False, "phases": [("inhale", 4, 1.0), ("exhale", 6, 0.62)]},
    "square": {"premium": True, "phases": [("inhale", 4, 1.0), ("hold", 4, 1.0),
                                           ("exhale", 4, 0.62), ("hold", 4, 0.62)]},
    "478": {"premium": True, "phases": [("inhale", 4, 1.0), ("hold", 7, 1.0), ("exhale", 8, 0.62)]},
}
SESSION_SECONDS = 120

Builder.load_string('''
#:import W screens.widgets

<SosScreen>:
    canvas.before:
        Color:
            rgba: W.DEEP
        Rectangle:
            pos: 0, 0
            size: self.size
        Color:
            rgba: 0.24, 0.43, 0.84, 1
        Ellipse:
            size: self.width * 1.4, self.width * 1.4
            pos: self.center_x - self.width * 0.7, self.height * 0.55 - self.width * 0.7
        Color:
            rgba: 1, 1, 1, 0.08
        Ellipse:
            size: dp(300) * root.scale, dp(300) * root.scale
            pos: self.center_x - dp(150) * root.scale, self.height * 0.55 - dp(150) * root.scale
        Color:
            rgba: 1, 1, 1, 0.12
        Ellipse:
            size: dp(250) * root.scale, dp(250) * root.scale
            pos: self.center_x - dp(125) * root.scale, self.height * 0.55 - dp(125) * root.scale
        Color:
            rgba: 0.93, 0.95, 1, 1
        Ellipse:
            size: dp(180) * root.scale, dp(180) * root.scale
            pos: self.center_x - dp(90) * root.scale, self.height * 0.55 - dp(90) * root.scale
    BoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(28), dp(20), dp(20)
        Label:
            text: app.t("sos_kicker", app.lang)
            font_name: W.SANS
            font_size: "12sp"
            color: 1, 1, 1, 0.8
            size_hint_y: None
            height: dp(18)
        Label:
            text: app.t("sos_title", app.lang)
            font_name: W.SERIF
            font_size: "22sp"
            color: W.WHITE
            size_hint_y: None
            height: dp(34)
        AnchorLayout:
            size_hint_y: None
            height: dp(42)
            BoxLayout:
                id: techniques
                size_hint_x: None
                width: self.minimum_width
                spacing: dp(8)
        Widget:
    BoxLayout:
        orientation: "vertical"
        size_hint: None, None
        size: dp(170), dp(70)
        center: root.center_x, root.height * 0.55
        Label:
            text: root.phase_text
            font_name: W.SERIF
            font_size: "26sp"
            color: W.DEEP
        Label:
            text: root.phase_sub
            font_name: W.SANS
            font_size: "12sp"
            color: W.MUTED
            size_hint_y: None
            height: dp(20)
    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(170)
        padding: dp(28), 0, dp(28), dp(24)
        spacing: dp(6)
        Label:
            text: root.time_text
            font_name: W.SERIF
            font_size: "34sp"
            color: W.WHITE
        Label:
            text: root.rhythm_text
            font_name: W.SANS
            font_size: "12sp"
            color: 1, 1, 1, 0.8
            size_hint_y: None
            height: dp(18)
        Pill:
            text: (app.t("stop", app.lang) if root.running else app.t("start", app.lang)).upper()
            bg: W.WHITE
            fg: W.DEEP
            on_release: root.stop() if root.running else root.start()
''')


class SosScreen(MDScreen):
    scale = NumericProperty(0.62)
    phase_text = StringProperty("")
    phase_sub = StringProperty("")
    time_text = StringProperty("02:00")
    rhythm_text = StringProperty("")
    running = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.technique = "sos"
        self.player = AudioPlayer()
        self._events = []
        App.get_running_app().bind(lang=lambda *a: self._labels())

    def on_pre_enter(self, *_):
        self._labels()

    def on_enter(self, *_):
        if not self.running:
            self.start()          # T5: при открытии сразу запускается дыхание

    def _labels(self):
        app = App.get_running_app()
        box = self.ids.techniques
        box.clear_widgets()
        for key in TECHNIQUES:
            lock = " · Plus" if TECHNIQUES[key]["premium"] and not app.premium else ""
            c = Chip(text=app.t("tech_" + key) + lock, group="tech", allow_no_selection=False,
                     state="down" if key == self.technique else "normal",
                     color_off=(1, 1, 1, 0.15), color_on=(1, 1, 1, 1))
            c.color = (0.12, 0.25, 0.56, 1) if key == self.technique else (1, 1, 1, 1)
            c.bind(on_release=lambda w, k=key: self.choose(k))
            box.add_widget(c)
        phases = TECHNIQUES[self.technique]["phases"]
        self.rhythm_text = " · ".join(f"{app.t(p[0]).lower()} {p[1]} {app.t('sec')}" for p in phases)
        if not self.running:
            self.phase_text = app.t("ready")
            self.phase_sub = app.t("press_start")

    def choose(self, key):
        app = App.get_running_app()
        if TECHNIQUES[key]["premium"] and not app.require_premium():
            self._labels()
            return
        self.stop()
        self.technique = key
        self._labels()
        self.start()

    def start(self):
        self.running = True
        self.left = SESSION_SECONDS
        self.time_text = "02:00"
        self.phase_i = -1
        snd = next(s for s in load_library()["sounds"] if s["id"] == "rain")
        self.player.load(snd["file"], loop=True, volume=0.35)
        self.player.play()
        self._events = [Clock.schedule_interval(self._tick, 1)]
        self._next_phase()

    def _next_phase(self, *_):
        if not self.running:
            return
        app = App.get_running_app()
        phases = TECHNIQUES[self.technique]["phases"]
        self.phase_i = (self.phase_i + 1) % len(phases)
        key, seconds, target = phases[self.phase_i]
        self.phase_text = app.t(key) + "…"
        self.phase_sub = app.t("n_seconds").format(seconds)
        Animation.cancel_all(self, "scale")
        Animation(scale=target, duration=seconds, t="in_out_sine").start(self)
        self._events.append(Clock.schedule_once(self._next_phase, seconds))

    def _tick(self, dt):
        self.left -= 1
        self.time_text = f"{self.left // 60:02d}:{self.left % 60:02d}"
        if self.left <= 0:
            app = App.get_running_app()
            self.stop()
            self.phase_text = app.t("well_done")
            self.phase_sub = ""

    def stop(self):
        self.running = False
        for e in self._events:
            e.cancel()
        self._events = []
        Animation.cancel_all(self, "scale")
        Animation(scale=0.62, duration=0.6).start(self)
        self.player.stop()
        app = App.get_running_app()
        self.phase_text = app.t("ready")
        self.phase_sub = app.t("press_start")
