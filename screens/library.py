"""Вкладка «Медитация»: библиотека медитаций, историй для сна, музыки и курсов."""
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.screen import MDScreen

from logic.audio_player import load_library
from screens.widgets import Card, Chip

Builder.load_string('''
#:import W screens.widgets

<LibraryItem>:
    orientation: "horizontal"
    spacing: dp(14)
    Widget:
        size_hint: None, None
        size: dp(52), dp(52)
        pos_hint: {"center_y": .5}
        canvas:
            Color:
                rgba: W.SUN if root.premium else W.SKY
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(16)]
        MDIcon:
            icon: root.icon
            theme_text_color: "Custom"
            text_color: W.BLUE2
            center: self.parent.center
    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: self.minimum_height
        pos_hint: {"center_y": .5}
        Label:
            text: root.title
            font_name: W.SANS_BOLD
            font_size: "15sp"
            color: W.NAVY
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
        Body:
            text: root.subtitle
            font_size: "12sp"
    MDIcon:
        icon: "lock-outline" if root.locked else "play-circle-outline"
        theme_text_color: "Custom"
        text_color: W.MUTED if root.locked else W.BLUE2
        size_hint_x: None
        width: dp(30)
        pos_hint: {"center_y": .5}

<LibraryScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(24), dp(20), 0
        spacing: dp(12)
        Title:
            text: app.t("library_title", app.lang)
        Body:
            text: app.t("library_sub", app.lang)
        ScrollView:
            size_hint_y: None
            height: dp(40)
            do_scroll_y: False
            BoxLayout:
                id: filters
                size_hint_x: None
                width: self.minimum_width
                spacing: dp(8)
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: item_list
                orientation: "vertical"
                spacing: dp(12)
                padding: 0, 0, 0, dp(16)
                size_hint_y: None
                height: self.minimum_height
''')

FILTERS = [("all", "filter_all"), ("meditation", "filter_meditation"), ("sleep", "filter_sleep"),
           ("music", "filter_music"), ("course", "filter_course")]


class LibraryItem(ButtonBehavior, Card):
    item_id = StringProperty()
    title = StringProperty()
    subtitle = StringProperty()
    icon = StringProperty("leaf")
    premium = BooleanProperty(False)
    locked = BooleanProperty(False)


class LibraryScreen(MDScreen):
    current_filter = StringProperty("all")

    def __init__(self, **kw):
        super().__init__(**kw)
        app = App.get_running_app()
        app.bind(lang=lambda *a: self.build_list(), premium=lambda *a: self.build_list())
        self.build_list()

    def on_pre_enter(self, *_):
        self.build_list()

    def build_list(self):
        app = App.get_running_app()
        lang = app.lang
        f = self.ids.filters
        f.clear_widgets()
        for key, label in FILTERS:
            chip = Chip(text=app.t(label), group="lib_filter", allow_no_selection=False,
                        state="down" if key == self.current_filter else "normal")
            chip.bind(on_release=lambda w, k=key: self.set_filter(k))
            f.add_widget(chip)
        box = self.ids.item_list
        box.clear_widgets()
        for it in load_library()["items"]:
            if self.current_filter != "all" and it["type"] != self.current_filter:
                continue
            w = LibraryItem(item_id=it["id"], title=it["title"][lang],
                            subtitle=("Akii Plus · " if it["premium"] else "") + it["subtitle"][lang],
                            icon=it["icon"], premium=it["premium"],
                            locked=it["premium"] and not app.premium)
            w.bind(on_release=self.open_item)
            box.add_widget(w)

    def set_filter(self, key):
        self.current_filter = key
        self.build_list()

    def open_item(self, w):
        app = App.get_running_app()
        if w.locked and not app.require_premium():
            return
        app.tab("player", item_id=w.item_id)
