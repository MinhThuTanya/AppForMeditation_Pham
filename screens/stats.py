"""Статистика (F.04) и достижения (F.09)."""
import calendar
import os
from datetime import date

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.label import Label
from kivymd.uix.screen import MDScreen

from logic import analytics, database, journal
from screens.widgets import BLUE2, Body, MONTHS, MUTED, NAVY, WD_SHORT

Builder.load_string('''
#:import W screens.widgets

<StatTile@Card>:
    value: ""
    caption: ""
    height: dp(84)
    Label:
        text: root.value
        size_hint_y: None
        height: dp(34)
        font_name: W.SERIF
        font_size: "24sp"
        color: W.BLUE2
        text_size: self.size
        halign: "left"
    Body:
        text: root.caption
        font_size: "11sp"

<StatsScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(16), dp(12), dp(16), 0
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            MDIconButton:
                icon: "arrow-left"
                on_release: app.back()
            Widget:
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(4), 0, dp(4), dp(20)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                Title:
                    text: app.t("stats_title", app.lang)
                BoxLayout:
                    size_hint_y: None
                    height: dp(84)
                    spacing: dp(10)
                    StatTile:
                        value: str(root.streak)
                        caption: app.t("days_in_row", app.lang)
                    StatTile:
                        value: str(root.total)
                        caption: app.t("minutes_total", app.lang)
                    StatTile:
                        value: str(root.sessions)
                        caption: app.t("sessions_done", app.lang)
                Card:
                    Label:
                        text: root.month_title
                        font_name: W.SANS_BOLD
                        font_size: "14sp"
                        color: W.NAVY
                        size_hint_y: None
                        height: dp(24)
                    GridLayout:
                        id: grid
                        cols: 7
                        size_hint_y: None
                        height: self.minimum_height
                        row_default_height: dp(30)
                        row_force_default: True
                Card:
                    Label:
                        text: app.t("stress_last", app.lang)
                        font_name: W.SANS_BOLD
                        font_size: "14sp"
                        color: W.NAVY
                        size_hint_y: None
                        height: dp(22)
                        text_size: self.size
                        halign: "left"
                    Body:
                        text: root.stress_text
                    Pill:
                        text: app.t("take_test_btn", app.lang).upper()
                        height: dp(44)
                        on_release: app.go("stress")
                Card:
                    id: badges
                    Label:
                        text: app.t("achievements", app.lang)
                        font_name: W.SANS_BOLD
                        font_size: "14sp"
                        color: W.NAVY
                        size_hint_y: None
                        height: dp(22)
                        text_size: self.size
                        halign: "left"
                Card:
                    Label:
                        text: app.t("plus_reports", app.lang)
                        font_name: W.SANS_BOLD
                        font_size: "14sp"
                        color: W.NAVY
                        size_hint_y: None
                        height: dp(22)
                        text_size: self.size
                        halign: "left"
                    Body:
                        text: app.t("plus_reports_sub", app.lang)
                    Pill:
                        text: app.t("export_journal", app.lang) + ("" if app.premium else " · Plus")
                        height: dp(44)
                        bg: W.SKY
                        fg: W.NAVY
                        on_release: root.export()
''')


class StatsScreen(MDScreen):
    streak = NumericProperty(0)
    total = NumericProperty(0)
    sessions = NumericProperty(0)
    month_title = StringProperty("")
    stress_text = StringProperty("")

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        lang = app.lang
        s = analytics.summary()
        self.streak, self.total, self.sessions = s["streak"], s["total"], s["sessions"]
        today = date.today()
        self.month_title = app.t("practice_days").format(MONTHS[lang][today.month - 1].lower())
        days = analytics.practice_days(today.year, today.month)
        grid = self.ids.grid
        grid.clear_widgets()
        for wd in WD_SHORT[lang]:
            grid.add_widget(Label(text=wd, font_size="10sp", color=MUTED))
        first, n = calendar.monthrange(today.year, today.month)
        for _ in range(first):
            grid.add_widget(Label())
        for d in range(1, n + 1):
            done = d in days
            grid.add_widget(Label(text=("• " if done else "") + str(d), font_size="12sp",
                                  color=BLUE2 if done else NAVY, bold=done))
        last = database.get_last_stress()
        if last:
            self.stress_text = app.t("stress_last_text").format(
                last[0], app.t({"высокий": "stress_high", "умеренный": "stress_moderate",
                                "низкий": "stress_low"}[last[1]]).lower(), last[2])
        else:
            self.stress_text = app.t("stress_none")
        box = self.ids.badges
        for w in list(box.children)[:-1]:
            box.remove_widget(w)
        got = analytics.get_achievements()
        if not got:
            box.add_widget(Body(text=app.t("no_badges")))
        for badge, day, desc in got:
            box.add_widget(Body(text=f"[color=#3D6FD6]★[/color]  {app.t('badge_' + badge)} · {day}",
                                markup=True, color=NAVY))

    def export(self):
        """Akii Plus: выгрузка дневника дня в текстовый файл."""
        app = App.get_running_app()
        if not app.require_premium():
            return
        os.makedirs("data/export", exist_ok=True)
        name = f"data/export/akii_journal_{date.today().isoformat()}.txt"
        with open(name, "w", encoding="utf-8") as f:
            for entry_date, title, text, mood in journal.get_recent_entries(1000):
                f.write(f"{entry_date}  {title or ''}  {mood or ''}\n{text}\n\n")
        app.toast(app.t("exported").format(os.path.abspath(name)))
