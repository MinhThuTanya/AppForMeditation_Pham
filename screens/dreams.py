"""Запись сна (F.06, упрощённо): аудиозапись на телефоне + теги и эмоция вручную."""
import os
from datetime import date, datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import database
from screens.widgets import Body, Chip, MOOD_COLORS, MOOD_KEYS, MOODS, long_date

Builder.load_string('''
#:import W screens.widgets

<DreamsScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(12), dp(20), dp(20)
        spacing: dp(12)
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            MDIconButton:
                icon: "arrow-left"
                on_release: app.back()
            Widget:
        Title:
            text: app.t("dreams_title", app.lang)
        Body:
            text: app.t("dreams_sub", app.lang)
        Pill:
            text: (app.t("rec_stop", app.lang) if root.recording else app.t("rec_start", app.lang)).upper()
            bg: W.SOS if root.recording else W.DEEP
            on_release: root.toggle_record()
        Body:
            text: root.audio_status
            font_size: "12sp"
        Field:
            id: tags
            hint_text: app.t("dream_tags", app.lang)
        Body:
            text: app.t("dream_emotion", app.lang)
            color: W.NAVY
        StackLayout:
            id: emotions
            size_hint_y: None
            height: dp(84)
            spacing: dp(8)
        Pill:
            text: app.t("save", app.lang).upper()
            on_release: root.save()
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: history
                orientation: "vertical"
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height
''')


class DreamsScreen(MDScreen):
    recording = BooleanProperty(False)
    audio_status = StringProperty("")

    def prepare(self, **_):
        app = App.get_running_app()
        self.emotion = None
        self.audio_path = None
        self.ids.tags.text = ""
        self.audio_status = ""
        box = self.ids.emotions
        box.clear_widgets()
        for m in MOODS:
            c = Chip(text=app.t(MOOD_KEYS[m]), group="dream", value=m, color_on=MOOD_COLORS[m])
            c.bind(on_release=lambda w: setattr(self, "emotion", w.value if w.state == "down" else None))
            box.add_widget(c)
        self.show_history()

    def toggle_record(self):
        """Аудиозапись через Plyer работает на Android/iOS (нужно разрешение на микрофон)."""
        app = App.get_running_app()
        try:
            from plyer import audio
        except ImportError:
            audio = None
        if app.platform not in ("android", "ios") or audio is None:
            app.toast(app.t("rec_phone_only"))
            return
        if not self.recording:
            os.makedirs("data/dreams", exist_ok=True)
            self.audio_path = f"data/dreams/dream_{datetime.now():%Y%m%d_%H%M%S}.3gp"
            audio.file_path = os.path.abspath(self.audio_path)
            audio.start()
            self.started = datetime.now()
            self.recording = True
            self.audio_status = app.t("recording")
        else:
            audio.stop()
            self.recording = False
            self.duration = int((datetime.now() - self.started).total_seconds())
            self.audio_status = app.t("recorded").format(self.duration)

    def save(self):
        app = App.get_running_app()
        tags = self.ids.tags.text.strip()
        if not tags and not self.audio_path:
            app.toast(app.t("dream_empty"))
            return
        mood_id = database.add_mood(self.emotion) if self.emotion else None
        database.add_dream(tags, self.emotion, self.audio_path,
                           getattr(self, "duration", None), mood_id)
        app.toast(app.t("dream_saved"))
        self.prepare()

    def show_history(self):
        app = App.get_running_app()
        h = self.ids.history
        h.clear_widgets()
        for _, tags, emotion, day, audio_path in database.get_dreams(10):
            text = f"{long_date(date.fromisoformat(day), app.lang, weekday=False)} — {tags or ''}"
            if emotion:
                text += f" · {app.t(MOOD_KEYS.get(emotion, emotion))}"
            if audio_path:
                text += " · ♪"
            h.add_widget(Body(text=text))
