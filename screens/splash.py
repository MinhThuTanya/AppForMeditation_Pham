"""Анимированная заставка (простая версия: «дышащее» солнце и волны).
Её можно заменить своей анимацией — главное в конце вызвать app.after_splash()."""
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivymd.uix.screen import MDScreen

Builder.load_string('''
#:import W screens.widgets

<SplashScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
        # солнце: три круга, внешний «дышит»
        Color:
            rgba: W.SUN[0], W.SUN[1], W.SUN[2], 0.35
        Ellipse:
            size: dp(300) * root.pulse, dp(300) * root.pulse
            pos: self.center_x - dp(150) * root.pulse, self.height * 0.58 - dp(150) * root.pulse
        Color:
            rgba: W.SUN[0], W.SUN[1], W.SUN[2], 0.6
        Ellipse:
            size: dp(244), dp(244)
            pos: self.center_x - dp(122), self.height * 0.58 - dp(122)
        Color:
            rgba: W.SUN2
        Ellipse:
            size: dp(188), dp(188)
            pos: self.center_x - dp(94), self.height * 0.58 - dp(94)
        # волны
        Color:
            rgba: 0.74, 0.83, 0.95, 0.8
        Ellipse:
            size: self.width * 2.2, dp(260)
            pos: self.center_x - self.width * 1.1 + root.wave, dp(130)
        Color:
            rgba: 0.56, 0.71, 0.93, 0.85
        Ellipse:
            size: self.width * 2.4, dp(260)
            pos: self.center_x - self.width * 1.2 - root.wave, dp(80)
        Color:
            rgba: 0.48, 0.64, 0.90, 1
        Rectangle:
            pos: 0, 0
            size: self.width, dp(170)
    BoxLayout:
        orientation: "vertical"
        size_hint: 1, None
        height: dp(120)
        y: dp(40)
        opacity: root.text_opacity
        Label:
            text: "Akii"
            font_name: W.SERIF
            font_size: "48sp"
            color: W.WHITE
        Label:
            text: "дыши спокойно · breathe calmly"
            font_name: W.SANS
            font_size: "13sp"
            color: 1, 1, 1, 0.9
            size_hint_y: None
            height: dp(24)
''')


class SplashScreen(MDScreen):
    pulse = NumericProperty(1.0)
    wave = NumericProperty(0)
    text_opacity = NumericProperty(0)

    def start(self):
        breathe = Animation(pulse=1.12, duration=1.1, t="in_out_sine") + \
            Animation(pulse=1.0, duration=1.1, t="in_out_sine")
        breathe.repeat = True
        breathe.start(self)
        Animation(wave=40, duration=2.2, t="in_out_sine").start(self)
        Animation(text_opacity=1, duration=0.9).start(self)
        Clock.schedule_once(self._next, 2.4)

    def _next(self, *_):
        Animation.cancel_all(self)
        App.get_running_app().after_splash()
