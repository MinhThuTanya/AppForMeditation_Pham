"""Дневник дня (F.11): календарь месяца и запись на выбранную дату."""
import calendar
from datetime import date

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivymd.uix.screen import MDScreen

from logic import journal
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from screens.widgets import (ROUND, Body, Card, Chip, FXButton, MONTHS, MOOD_COLORS, MOOD_KEYS,
                             MOODS, NAVY, WD_SHORT, long_date, mood_icon)

Builder.load_string('''
#:import W screens.widgets

<DayCell>:
    font_name: W.ROUND
    font_size: "9sp" if self.icon else "13sp"
    color: W.NAVY
    text_size: self.size if self.icon else (None, None)
    halign: "right"
    valign: "bottom"
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1) if self.icon else (0, 0, 0, 0)
        Rectangle:
            source: self.icon or None
            size: min(self.width, self.height) - dp(6), min(self.width, self.height) - dp(6)
            pos: self.center_x - (min(self.width, self.height) - dp(6)) / 2, self.center_y - (min(self.width, self.height) - dp(6)) / 2
        Color:
            rgba: W.NAVY if self.today else (0, 0, 0, 0)
        Line:
            circle: self.center_x, self.center_y, (min(self.width, self.height) - dp(2)) / 2
            width: 1.4

<JournalScreen>:
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
            padding: dp(20), dp(24), dp(20), dp(90)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height
            Title:
                text: app.t("journal_title", app.lang)
            Card:
                BoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    MDIconButton:
                        icon: "chevron-left"
                        on_release: root.shift_month(-1)
                    Label:
                        text: root.month_title
                        font_name: W.SANS_BOLD
                        font_size: "15sp"
                        color: W.NAVY
                    MDIconButton:
                        icon: "chevron-right"
                        on_release: root.shift_month(1)
                GridLayout:
                    id: grid
                    cols: 7
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: dp(40)
                    row_force_default: True
            GridLayout:
                id: legend
                size_hint_y: None
                height: dp(44)
                spacing: dp(4)
                cols: 3
            BoxLayout:
                id: entries
                orientation: "vertical"
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
    MDFabButton:
        icon: "plus"
        style: "standard"
        pos: root.right - self.width - dp(20), dp(20)
        on_release: app.go("entry", day=None)

<EntryScreen>:
    canvas.before:
        Color:
            rgba: W.WHITE
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(16), dp(12), dp(16), dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            MDIconButton:
                icon: "chevron-left"
                on_release: app.back()
            Label:
                text: root.date_text
                font_name: W.SANS_MED
                font_size: "13sp"
                color: W.MUTED
            Label:
                text: app.t("done", app.lang)
                font_name: W.SANS_BOLD
                font_size: "14sp"
                color: W.BLUE2
                size_hint_x: None
                width: dp(70)
                on_touch_down: if self.collide_point(*args[1].pos): root.save()
        Field:
            id: title
            size_hint_y: None
            height: dp(56)
            hint_text: app.t("entry_title_hint", app.lang)
        Body:
            text: app.t("how_was_day", app.lang)
            font_size: "13sp"
        BoxLayout:
            id: moods
            size_hint_y: None
            height: dp(36)
            spacing: dp(6)
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(58)
            padding: dp(14), dp(8)
            canvas.before:
                Color:
                    rgba: W.BG
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(16)]
            Label:
                text: app.t("hint_label", app.lang).upper()
                font_name: W.SANS_BOLD
                font_size: "10sp"
                color: W.BLUE2
                text_size: self.size
                halign: "left"
            Label:
                text: root.prompt
                font_name: W.SANS
                font_size: "13sp"
                color: W.NAVY
                text_size: self.size
                halign: "left"
        TextInput:
            id: text
            font_name: W.SANS
            font_size: "15sp"
            foreground_color: W.NAVY
            background_color: 0, 0, 0, 0
            cursor_color: W.BLUE2
            hint_text: app.t("entry_text_hint", app.lang)
            hint_text_color: W.MUTED
            on_text: root.chars = str(len(self.text))
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(8)
            Chip:
                text: "↻ " + app.t("another_hint", app.lang)
                on_release: root.next_prompt(); self.state = "normal"
            Widget:
            Label:
                text: app.t("chars", app.lang).format(root.chars)
                font_name: W.SANS
                font_size: "12sp"
                color: W.MUTED
                size_hint_x: None
                width: dp(100)
''')

PROMPTS = ["prompt_1", "prompt_2", "prompt_3", "prompt_4", "prompt_5"]


class DayCell(FXButton, Label):
    """День календаря: смайлик настроения вместо цветного круга."""
    icon = StringProperty("")
    today = BooleanProperty(False)


class EntryCard(FXButton, Card):
    pass


class JournalScreen(MDScreen):
    month_title = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        t = date.today()
        self.year, self.month = t.year, t.month
        App.get_running_app().bind(lang=lambda *a: self.refresh())

    def on_pre_enter(self, *_):
        self.refresh()

    def shift_month(self, step):
        m = self.month + step
        self.year += (m - 1) // 12
        self.month = (m - 1) % 12 + 1
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        lang = app.lang
        self.month_title = f"{MONTHS[lang][self.month - 1]} {self.year}"
        marks = {d: m for d, m in journal.get_month_marks(self.year, self.month)}
        grid = self.ids.grid
        grid.clear_widgets()
        for wd in WD_SHORT[lang]:
            grid.add_widget(Label(text=wd, font_size="11sp", color=(0.42, 0.45, 0.58, 1)))
        first, ndays = calendar.monthrange(self.year, self.month)
        for _ in range(first):
            grid.add_widget(Label())
        today = date.today()
        for day in range(1, ndays + 1):
            d = date(self.year, self.month, day)
            iso = d.isoformat()
            cell = DayCell(text=str(day))
            cell.today = d == today
            if iso in marks:
                if marks[iso]:
                    cell.icon = mood_icon(marks[iso])
                else:                      # запись без отметки настроения
                    cell.color = (0.24, 0.43, 0.84, 1)
                    cell.bold = True
            if d <= today:
                cell.bind(on_release=lambda w, x=iso: app.go("entry", day=x))
            else:
                cell.color = cell.disabled_color = (0.42, 0.45, 0.58, 0.4)
                cell.disabled = True
            grid.add_widget(cell)
        # легенда
        leg = self.ids.legend
        leg.clear_widgets()
        for m in MOODS:
            item = BoxLayout(spacing=dp(3))
            item.add_widget(Image(source=mood_icon(m), size_hint_x=None, width=dp(16), fit_mode="contain"))
            item.add_widget(Label(text=app.t(MOOD_KEYS[m]), font_size="10sp", color=(0.42, 0.45, 0.58, 1),
                                  font_name=ROUND, halign="left", text_size=(None, None)))
            leg.add_widget(item)
        # последние записи
        box = self.ids.entries
        box.clear_widgets()
        rows = journal.get_recent_entries(10)
        if not rows:
            box.add_widget(Body(text=app.t("journal_empty"), halign="center"))
        for entry_date, title, text, mood in rows:
            card = EntryCard()
            head = long_date(date.fromisoformat(entry_date), lang)
            row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(6))
            if mood:
                row.add_widget(Image(source=mood_icon(mood), size_hint_x=None, width=dp(22), fit_mode="contain"))
                head += f"  ·  {app.t(MOOD_KEYS[mood])}"
            row.add_widget(Body(text=head, font_size="11sp", size_hint_y=None, height=dp(22), valign="middle"))
            card.add_widget(row)
            head_lbl = Label(text=title or app.t("no_title"), font_name="assets/fonts/Inter-Bold.otf",
                             font_size="15sp", color=NAVY, size_hint_y=None, height=dp(22),
                             halign="left", shorten=True)
            head_lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
            card.add_widget(head_lbl)
            preview = (text[:110] + "…") if len(text) > 110 else text
            card.add_widget(Body(text=preview, font_size="12sp"))
            card.bind(on_release=lambda w, x=entry_date: app.go("entry", day=x))
            box.add_widget(card)


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in c[:3])


class EntryScreen(MDScreen):
    date_text = StringProperty("")
    prompt = StringProperty("")
    chars = StringProperty("0")

    def prepare(self, day=None):
        app = App.get_running_app()
        self.day = day or date.today().isoformat()
        self.date_text = long_date(date.fromisoformat(self.day), app.lang, year=True)
        entry = journal.get_entry(self.day)
        self.ids.title.text = (entry[1] or "") if entry else ""
        self.ids.text.text = entry[2] if entry else ""
        self.mood = journal.get_entry_mood(self.day)
        self._prompt_i = date.fromisoformat(self.day).toordinal() % len(PROMPTS)
        self.prompt = app.t(PROMPTS[self._prompt_i])
        box = self.ids.moods
        box.clear_widgets()
        for m in MOODS:
            c = Chip(text=app.t(MOOD_KEYS[m]), group="entry_mood", value=m,
                     color_on=MOOD_COLORS[m], color_off=(0.93, 0.95, 0.99, 1),
                     state="down" if m == self.mood else "normal")
            c.bind(on_release=lambda w: setattr(self, "mood", w.value if w.state == "down" else None))
            box.add_widget(c)

    def next_prompt(self):
        self._prompt_i = (self._prompt_i + 1) % len(PROMPTS)
        self.prompt = App.get_running_app().t(PROMPTS[self._prompt_i])

    def save(self):
        app = App.get_running_app()
        text = self.ids.text.text.strip()
        if not text:
            app.toast(app.t("entry_empty"))
            return
        mood_id = journal.mood_for_entry(self.day, self.mood)
        journal.save_entry(self.day, text, title=self.ids.title.text.strip() or None,
                           mood_id=mood_id)
        from logic import avatar
        avatar.update_avatar()
        app.toast(app.t("entry_saved"))
        app.back()
