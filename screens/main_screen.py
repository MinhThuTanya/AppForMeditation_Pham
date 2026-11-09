"""Главный контейнер: вкладки и нижнее меню
(Главная, Медитация, Дневник, Аватар, SOS)."""
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivymd.uix.navigationbar import MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivy.properties import StringProperty

from screens import home, library, player, journal, avatar_screen, sos

Builder.load_string('''
#:import W screens.widgets

<NavItem>:
    MDNavigationItemIcon:
        icon: root.icon
        theme_icon_color: "Custom"
        icon_color_active: W.SOS if root.name == "sos" else W.BLUE2
        icon_color_normal: W.SOS if root.name == "sos" else (0.6, 0.64, 0.74, 1)
    MDNavigationItemLabel:
        text: app.t(root.label_key, app.lang)
        theme_text_color: "Custom"
        text_color_active: W.SOS if root.name == "sos" else W.BLUE2
        text_color_normal: W.SOS if root.name == "sos" else (0.6, 0.64, 0.74, 1)

<MainScreen>:
    BoxLayout:
        orientation: "vertical"
        ScreenManager:
            id: tabs
        MDNavigationBar:
            id: bar
            theme_bg_color: "Custom"
            md_bg_color: W.WHITE
            on_switch_tabs: root.on_switch_tabs(*args)
            NavItem:
                name: "home"
                icon: "home-variant"
                label_key: "tab_home"
                active: True
            NavItem:
                name: "library"
                icon: "meditation"
                label_key: "tab_meditation"
            NavItem:
                name: "journal"
                icon: "notebook-heart-outline"
                label_key: "tab_journal"
            NavItem:
                name: "avatar"
                icon: "emoticon-happy-outline"
                label_key: "tab_avatar"
            NavItem:
                name: "sos"
                icon: "lifebuoy"
                label_key: "tab_sos"
''')


class NavItem(MDNavigationItem):
    name = StringProperty()
    icon = StringProperty()
    label_key = StringProperty()


TAB_OF = {"player": "library"}   # экран плеера относится к вкладке «Медитация»


class MainScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        tabs = self.ids.tabs
        tabs.transition = FadeTransition(duration=0.15)
        for s in (home.HomeScreen(name="home"), library.LibraryScreen(name="library"),
                  player.PlayerScreen(name="player"), journal.JournalScreen(name="journal"),
                  avatar_screen.AvatarScreen(name="avatar"), sos.SosScreen(name="sos")):
            tabs.add_widget(s)
        self._stack = []

    def on_switch_tabs(self, bar, item, *args):
        if self.ids.tabs.current != item.name and TAB_OF.get(self.ids.tabs.current) != item.name:
            self.switch(item.name, from_bar=True)

    def switch(self, name, from_bar=False, **kwargs):
        tabs = self.ids.tabs
        if tabs.current == "sos" and name != "sos":
            tabs.get_screen("sos").stop()
        if tabs.current == "player" and name != "player":
            tabs.get_screen("player").stop(save=False)
        screen = tabs.get_screen(name)
        if hasattr(screen, "prepare"):
            screen.prepare(**kwargs)
        if name in TAB_OF:
            self._stack.append(tabs.current)
        else:
            self._stack.clear()
        tabs.current = name
        if not from_bar:
            target = TAB_OF.get(name, name)
            for item in self.ids.bar.children:
                if isinstance(item, NavItem) and item.name == target and not item.active:
                    self.ids.bar.set_active_item(item)

    def back(self):
        if self._stack:
            self.switch(self._stack.pop())
            return True
        if self.ids.tabs.current != "home":
            self.switch("home")
            return True
        return False

    def on_pre_enter(self, *_):
        current = self.ids.tabs.current_screen
        if hasattr(current, "on_pre_enter"):
            current.on_pre_enter()
