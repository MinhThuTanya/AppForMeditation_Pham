"""Дневник настроения: быстрая отметка настроения с заметкой."""
from datetime import date

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from logic import avatar, database
from screens.widgets import Body, Chip, MOOD_COLORS, MOOD_KEYS, MOODS, long_date

Builder.load_string('''
#:import W screens.widgets

<MoodScreen>:
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
            text: app.t("mood_title", app.lang)
        Body:
            text: app.t("mood_sub", app.lang)
        StackLayout:
            id: moods
            size_hint_y: None
            height: dp(84)
            spacing: dp(8)
        Field:
            id: note
            hint_text: app.t("mood_note", app.lang)
        Pill:
            text: app.t("save", app.lang).upper()
            on_release: root.save()
        Body:
            text: app.t("recent", app.lang)
            color: W.NAVY
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: history
                orientation: "vertical"
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height
''')


class MoodScreen(MDScreen):
    selected = StringProperty("")

    def prepare(self, **_):
        app = App.get_running_app()
        self.selected = ""
        self.ids.note.text = ""
        box = self.ids.moods
        box.clear_widgets()
        for m in MOODS:
            c = Chip(text=app.t(MOOD_KEYS[m]), group="mood", value=m, color_on=MOOD_COLORS[m],
                     height="40dp")
            c.bind(on_release=lambda w: setattr(self, "selected", w.value if w.state == "down" else ""))
            box.add_widget(c)
        self.show_history()

    def show_history(self):
        app = App.get_running_app()
        h = self.ids.history
        h.clear_widgets()
        for _, mood, note, day in database.get_moods(15):
            color = "#%02x%02x%02x" % tuple(int(v * 255) for v in MOOD_COLORS.get(mood, (0.6, 0.6, 0.7))[:3])
            text = f"[color={color}]•[/color]  {long_date(date.fromisoformat(day[:10]), app.lang, weekday=False)} — " \
                   f"{app.t(MOOD_KEYS.get(mood, mood))}" + (f": {note}" if note else "")
            h.add_widget(Body(text=text, markup=True))

    def save(self):
        app = App.get_running_app()
        if not self.selected:
            app.toast(app.t("choose_mood"))
            return
        database.add_mood(self.selected, self.ids.note.text.strip() or None)
        state, _ = avatar.update_avatar()
        app.toast(app.t("mood_saved"))
        self.prepare()
