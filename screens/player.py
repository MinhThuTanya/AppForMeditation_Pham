"""Экран сессии медитации: длительность, голос, фоновый звук, таймер (F.03)."""
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import analytics, avatar, database
from logic.audio_player import AudioPlayer, load_library
from screens.widgets import Chip, ask

Builder.load_string('''
#:import W screens.widgets

<PlayerScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
        Color:
            rgba: W.SKY
        Rectangle:
            pos: 0, 0
            size: self.width, self.height * 0.35
    BoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(12), dp(20), dp(16)
        spacing: dp(8)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            MDIconButton:
                icon: "arrow-left"
                on_release: app.tab("library")
            Widget:
        Label:
            text: root.kind_text
            font_name: W.SANS
            font_size: "12sp"
            color: W.MUTED
            size_hint_y: None
            height: dp(18)
        Label:
            text: root.title
            font_name: W.SERIF
            font_size: "24sp"
            color: W.NAVY
            size_hint_y: None
            height: dp(34)
        # --- круг с прогрессом ---
        Widget:
            id: ring
            canvas:
                Color:
                    rgba: W.WHITE
                Line:
                    circle: self.center_x, self.center_y, min(self.width, self.height) / 2 - dp(8)
                    width: dp(7)
                Color:
                    rgba: W.BLUE2
                Line:
                    circle: self.center_x, self.center_y, min(self.width, self.height) / 2 - dp(8), 0, 360 * root.progress
                    width: dp(7)
                    cap: "round"
                Color:
                    rgba: W.SUN
                Ellipse:
                    size: (min(self.width, self.height) - dp(48)) * root.breath, (min(self.width, self.height) - dp(48)) * root.breath
                    pos: self.center_x - (min(self.width, self.height) - dp(48)) * root.breath / 2, self.center_y - (min(self.width, self.height) - dp(48)) * root.breath / 2
            MDIcon:
                icon: "flower-tulip"
                theme_font_size: "Custom"
                font_size: "72sp"
                size_hint: None, None
                size: dp(90), dp(90)
                halign: "center"
                valign: "middle"
                theme_text_color: "Custom"
                text_color: W.BLUE
                center: ring.center
        Label:
            text: root.guide_text
            font_name: W.SANS
            font_size: "13sp"
            color: W.MUTED
            size_hint_y: None
            height: dp(36)
            text_size: self.width, None
            halign: "center"
        Label:
            text: root.time_text
            font_name: W.SERIF
            font_size: "40sp"
            color: W.NAVY
            size_hint_y: None
            height: dp(50)
        # --- параметры (до начала сессии) ---
        BoxLayout:
            id: options
            orientation: "vertical"
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            opacity: 0 if root.started else 1
            disabled: root.started
            AnchorLayout:
                size_hint_y: None
                height: dp(36)
                BoxLayout:
                    id: durations
                    size_hint_x: None
                    width: self.minimum_width
                    spacing: dp(8)
            AnchorLayout:
                size_hint_y: None
                height: dp(36)
                BoxLayout:
                    id: voices
                    size_hint_x: None
                    width: self.minimum_width
                    spacing: dp(8)
            AnchorLayout:
                size_hint_y: None
                height: dp(36)
                BoxLayout:
                    id: sounds
                    size_hint_x: None
                    width: self.minimum_width
                    spacing: dp(8)
        # --- управление ---
        AnchorLayout:
            size_hint_y: None
            height: dp(84)
            BoxLayout:
                size_hint: None, None
                size: dp(250), dp(76)
                spacing: dp(24)
                MDIconButton:
                    icon: "rewind-15"
                    style: "tonal"
                    pos_hint: {"center_y": .5}
                    disabled: not root.started
                    on_release: root.shift(-15)
                MDIconButton:
                    icon: "pause" if root.running else "play"
                    style: "filled"
                    theme_font_size: "Custom"
                    font_size: "34sp"
                    size_hint: None, None
                    size: dp(76), dp(76)
                    radius: [dp(38)]
                    on_release: root.toggle()
                MDIconButton:
                    icon: "fast-forward-15"
                    style: "tonal"
                    pos_hint: {"center_y": .5}
                    disabled: not root.started
                    on_release: root.shift(15)
''')


class PlayerScreen(MDScreen):
    title = StringProperty("")
    kind_text = StringProperty("")
    time_text = StringProperty("10:00")
    guide_text = StringProperty("")
    progress = NumericProperty(0)
    breath = NumericProperty(0.8)
    started = BooleanProperty(False)
    running = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.music = AudioPlayer()
        self.ambient = AudioPlayer()
        self._event = None
        self.item = None
        self.mood_before = None
        App.get_running_app().bind(lang=lambda *a: self._texts())

    # ---------- подготовка ----------
    def prepare(self, item_id="anxiety"):
        self.stop(save=False)
        lib = load_library()
        self.lib = lib
        self.item = next(i for i in lib["items"] if i["id"] == item_id)
        s = database.get_settings()
        self.duration = s["default_duration"]
        self.voice = s["default_voice"]
        self.sound = s["default_sound"]
        self.remaining = self.duration * 60
        self._build_chips()
        self._texts()

    def _texts(self):
        if not self.item:
            return
        app = App.get_running_app()
        self.title = self.item["title"][app.lang]
        self.kind_text = app.t("kind_" + self.item["type"]) + " · " + \
            app.t("minutes_short").format(self.duration)
        self._show_time()
        if not self.started:
            self.guide_text = app.t("player_hint")
        self._build_chips()

    def _build_chips(self):
        app = App.get_running_app()

        def fill(box, values, current, label, setter, group):
            box.clear_widgets()
            for v in values:
                c = Chip(text=label(v), group=group, allow_no_selection=False,
                         state="down" if v == current else "normal")
                c.bind(on_release=lambda w, val=v: setter(val))
                box.add_widget(c)

        fill(self.ids.durations, self.lib["durations"], self.duration,
             lambda v: app.t("minutes_short").format(v), self.set_duration, "dur")
        fill(self.ids.voices, self.lib["voices"], self.voice,
             lambda v: app.t("voice_" + v), self.set_voice, "voice")
        fill(self.ids.sounds, [s["id"] for s in self.lib["sounds"]], self.sound,
             lambda v: next(s["title"][app.lang] for s in self.lib["sounds"] if s["id"] == v),
             self.set_sound, "sound")

    def set_duration(self, v):
        self.duration = v
        self.remaining = v * 60
        database.update_setting("default_duration", v)
        self._texts()

    def set_voice(self, v):
        self.voice = v
        database.update_setting("default_voice", v)

    def set_sound(self, v):
        self.sound = v
        database.update_setting("default_sound", v)

    # ---------- воспроизведение ----------
    def toggle(self):
        if not self.started:
            app = App.get_running_app()
            ask(app.t("mood_before_q"), [(i, str(i)) for i in range(1, 6)],
                self._start, subtitle=app.t("scale_hint"), skip_text=app.t("skip"))
        elif self.running:
            self.pause()
        else:
            self.resume()

    def _start(self, mood_before):
        self.mood_before = mood_before
        self.started = True
        sound = next(s for s in self.lib["sounds"] if s["id"] == self.sound)
        self.music.load(self.item["file"], loop=True, volume=0.8)
        if sound["file"] and sound["file"] != self.item["file"]:
            if not self.ambient.load(sound["file"], loop=True, volume=0.5):
                App.get_running_app().toast(App.get_running_app().t("sound_missing")
                                            .format(os.path.basename(sound["file"])))
        self.resume()

    def resume(self):
        self.running = True
        self.music.play()
        self.ambient.play()
        self._event = Clock.schedule_interval(self._tick, 1)

    def pause(self):
        self.running = False
        self.music.pause()
        self.ambient.pause()
        if self._event:
            self._event.cancel()

    def shift(self, seconds):
        total = self.duration * 60
        self.remaining = max(1, min(total, self.remaining - seconds))
        self._show_time()

    def _tick(self, dt):
        self.remaining -= 1
        total = self.duration * 60
        elapsed = total - self.remaining
        # дыхательный ритм круга: вдох 4 с, выдох 6 с
        phase = elapsed % 10
        self.breath = 0.8 + 0.2 * (phase / 4 if phase < 4 else (10 - phase) / 6)
        guides = ["guide_1", "guide_2", "guide_3", "guide_4", "guide_5"]
        self.guide_text = App.get_running_app().t(guides[(elapsed // 20) % len(guides)])
        self._show_time()
        if self.remaining <= 0:
            self.finish()

    def _show_time(self):
        r = max(0, int(self.remaining))
        self.time_text = f"{r // 60:02d}:{r % 60:02d}"
        total = self.duration * 60
        self.progress = (total - r) / total if total else 0

    def finish(self):
        self.pause()
        app = App.get_running_app()
        ask(app.t("mood_after_q"), [(i, str(i)) for i in range(1, 6)],
            self._save, subtitle=app.t("scale_hint"), skip_text=app.t("skip"))

    def _save(self, mood_after):
        app = App.get_running_app()
        minutes = max(1, round((self.duration * 60 - self.remaining) / 60))
        sid = database.add_session(minutes, self.item["id"], self.voice, self.sound,
                                   self.mood_before, mood_after)
        new = analytics.check_achievements(sid)
        avatar.update_avatar()
        self.stop(save=False)
        app.toast(app.t("session_saved") + (" · " + ", ".join(new) if new else ""))
        app.tab("avatar")

    def stop(self, save=False):
        if self._event:
            self._event.cancel()
        self.music.stop()
        self.ambient.stop()
        self.running = False
        self.started = False
        if self.item:
            self.remaining = self.duration * 60
            self._show_time()
