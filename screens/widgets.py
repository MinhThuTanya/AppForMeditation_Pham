"""Общие виджеты и цвета приложения Akii (спокойная голубая палитра)."""
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, ColorProperty, ListProperty,
                             NumericProperty, StringProperty)
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hx

# Палитра (совпадает с макетом в Figma и подразделом 2.9 курсовой)
BG = hx("#E6EEF9")      # фон — светло-голубой
SKY = hx("#CFE0F7")     # небо, второй фон
BLUE = hx("#5B8DEF")    # акцент
BLUE2 = hx("#3D6FD6")   # кнопки
DEEP = hx("#1F3F8F")    # тёмно-синий (SOS)
NAVY = hx("#1B1F4B")    # текст
MUTED = hx("#6A7493")   # второстепенный текст
SUN = hx("#F5E6A8")     # солнце
SUN2 = hx("#F2D97A")
WHITE = (1, 1, 1, 1)
SOS = hx("#E8706A")

# Цвета настроений: радость, спокойствие, усталость, тревога, грусть
MOODS = ["радость", "спокойствие", "усталость", "тревога", "грусть"]
MOOD_KEYS = {"радость": "mood_joy", "спокойствие": "mood_calm",
             "усталость": "mood_tired", "тревога": "mood_anxious",
             "грусть": "mood_sad"}
MOOD_COLORS = {"радость": hx("#F2D06B"), "спокойствие": hx("#7FA6F0"),
               "усталость": hx("#B9A7E8"), "тревога": hx("#E8706A"),
               "грусть": hx("#9DB0CF")}

SERIF = "assets/fonts/AkiiSerif-Bold.ttf"
SANS = "assets/fonts/Inter-Regular.otf"
SANS_MED = "assets/fonts/Inter-Medium.otf"
SANS_BOLD = "assets/fonts/Inter-Bold.otf"


class Title(Label):
    pass


class Body(Label):
    pass


class Card(BoxLayout):
    bg = ColorProperty(WHITE)
    radius = NumericProperty(24)


class Pill(ButtonBehavior, Label):
    """Кнопка-«таблетка» как в макете."""
    bg = ColorProperty(BLUE2)
    fg = ColorProperty(WHITE)
    radius = NumericProperty(28)
    disabled_look = BooleanProperty(False)


class Chip(ToggleButtonBehavior, Label):
    """Переключатель-«чип» (голос, звук, длительность, настроение)."""
    value = StringProperty("")
    color_on = ColorProperty(BLUE2)
    color_off = ColorProperty(WHITE)


class IconText(ButtonBehavior, BoxLayout):
    icon = StringProperty("")
    text = StringProperty("")


class Spacer(Widget):
    pass


from kivy.uix.textinput import TextInput  # noqa: E402


class Field(TextInput):
    """Поле ввода в стиле приложения (белое, со скруглёнными углами)."""
    pass


class Bars(Widget):
    """Столбчатая диаграмма «Настроение за неделю» (значения 0..5)."""
    values = ListProperty([])
    labels = ListProperty([])


Builder.load_string('''
#:import hx kivy.utils.get_color_from_hex
#:import W screens.widgets

<Title>:
    font_name: W.SERIF
    color: W.NAVY
    font_size: "26sp"
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1]
    halign: "left"

<Body>:
    font_name: W.SANS
    color: W.MUTED
    font_size: "14sp"
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1]
    halign: "left"

<Card>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "8dp"
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: 0.24, 0.43, 0.84, 0.08
        RoundedRectangle:
            pos: self.x, self.y - dp(3)
            size: self.size
            radius: [dp(self.radius)]
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(self.radius)]

<Pill>:
    font_name: W.SANS_BOLD
    font_size: "14sp"
    color: self.fg
    size_hint_y: None
    height: "52dp"
    halign: "center"
    valign: "middle"
    text_size: self.width - dp(20), None
    canvas.before:
        Color:
            rgba: (self.bg[0], self.bg[1], self.bg[2], self.bg[3] * (0.75 if self.state == "down" else 1))
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [min(dp(self.radius), self.height / 2)]

<Chip>:
    font_name: W.SANS_MED
    font_size: "13sp"
    color: W.WHITE if self.state == "down" else W.NAVY
    size_hint: None, None
    height: "36dp"
    width: self.texture_size[0] + dp(28)
    canvas.before:
        Color:
            rgba: self.color_on if self.state == "down" else self.color_off
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]

<IconText>:
    orientation: "vertical"
    MDIcon:
        icon: root.icon
        halign: "center"
        theme_text_color: "Custom"
        text_color: W.BLUE2

<Field>:
    font_name: W.SANS
    font_size: "15sp"
    multiline: False
    write_tab: False
    size_hint_y: None
    height: dp(52)
    padding: dp(16), (self.height - self.line_height) / 2 if not self.multiline else dp(14)
    foreground_color: W.NAVY
    hint_text_color: W.MUTED
    cursor_color: W.BLUE2
    background_normal: ""
    background_active: ""
    background_color: 0, 0, 0, 0
    canvas.before:
        Color:
            rgba: W.WHITE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
        Color:
            rgba: W.BLUE2 if self.focus else (0.80, 0.85, 0.94, 1)
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(16)
            width: 1.2 if self.focus else 1
        Color:
            rgba: self.hint_text_color if not self.text else self.foreground_color

<ClickBox@ButtonBehavior+BoxLayout>:

<ClickCard@ButtonBehavior+Card>:

<Bars>:
    canvas:
        Color:
            rgba: W.SKY
        Line:
            points: self.x, self.y + dp(18), self.right, self.y + dp(18)
            width: 1
''')


def draw_bars(widget, *_):
    """Перерисовка диаграммы (вызывается при изменении размеров или данных)."""
    from kivy.graphics import Color, RoundedRectangle
    from kivy.core.text import Label as CoreLabel
    from kivy.metrics import dp
    widget.canvas.after.clear()
    n = len(widget.values) or 1
    slot = widget.width / n
    bw = min(dp(22), slot * 0.6)
    top = widget.height - dp(26)
    with widget.canvas.after:
        for i, v in enumerate(widget.values):
            x = widget.x + slot * i + (slot - bw) / 2
            h = max(dp(6), top * (v / 5.0)) if v else dp(6)
            Color(*(BLUE2 if i == n - 1 else BLUE)[:3], 1 if v else 0.25)
            RoundedRectangle(pos=(x, widget.y + dp(22)), size=(bw, h), radius=[dp(8)])
            if i < len(widget.labels):
                lbl = CoreLabel(text=widget.labels[i], font_size=dp(11), font_name=SANS)
                lbl.refresh()
                Color(*MUTED)
                tex = lbl.texture
                from kivy.graphics import Rectangle
                Rectangle(texture=tex, size=tex.size,
                          pos=(widget.x + slot * i + (slot - tex.width) / 2, widget.y))


def bind_bars(widget):
    widget.bind(pos=lambda *a: draw_bars(widget), size=lambda *a: draw_bars(widget),
                values=lambda *a: draw_bars(widget), labels=lambda *a: draw_bars(widget))


# ---- Даты на русском и английском ----
WEEKDAYS = {"ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
            "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
WD_SHORT = {"ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
            "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]}
MONTHS = {"ru": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
                 "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August",
                 "September", "October", "November", "December"]}
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря"]


def long_date(d, lang, weekday=True, year=False):
    """«Пятница, 30 октября» / «Friday, October 30»."""
    if lang == "ru":
        s = f"{d.day} {MONTHS_GEN[d.month - 1]}" + (f" {d.year}" if year else "")
    else:
        s = f"{MONTHS['en'][d.month - 1]} {d.day}" + (f", {d.year}" if year else "")
    return f"{WEEKDAYS[lang][d.weekday()]}, {s}" if weekday else s


def ask(title, options, callback, subtitle="", skip_text=None):
    """Простой диалог выбора: options — список (значение, подпись).
    callback(value) вызывается после выбора (None — «пропустить»)."""
    from kivy.metrics import dp
    from kivy.uix.modalview import ModalView
    from kivy.uix.gridlayout import GridLayout
    view = ModalView(size_hint=(0.88, None), background_color=(0.1, 0.12, 0.3, 0.35),
                     background="", auto_dismiss=False)
    card = Card(padding=dp(20), spacing=dp(12))
    card.add_widget(Title(text=title, font_size="20sp"))
    if subtitle:
        card.add_widget(Body(text=subtitle))
    grid = GridLayout(cols=min(len(options), 5), spacing=dp(8), size_hint_y=None, height=dp(44))

    def choose(value):
        view.dismiss()
        callback(value)

    for value, label in options:
        b = Pill(text=label, height=dp(44), bg=SKY, fg=NAVY, font_size="13sp")
        b.bind(on_release=lambda w, v=value: choose(v))
        grid.add_widget(b)
    card.add_widget(grid)
    if skip_text:
        s = Pill(text=skip_text, bg=(0, 0, 0, 0), fg=MUTED, height=dp(36))
        s.bind(on_release=lambda w: choose(None))
        card.add_widget(s)
    view.add_widget(card)
    card.bind(minimum_height=lambda w, h: setattr(view, "height", h))
    view.open()
    return view


def toast(text, duration=2.6):
    """Короткое сообщение внизу экрана."""
    from kivy.animation import Animation
    from kivy.core.window import Window
    from kivy.metrics import dp
    lbl = Label(text=text, font_name=SANS_MED, font_size="13sp", color=WHITE,
                halign="center", valign="middle", size_hint=(None, None),
                padding=(dp(16), dp(12)))
    lbl.text_size = (Window.width * 0.82 - dp(32), None)
    lbl.texture_update()
    lbl.size = (Window.width * 0.82, lbl.texture_size[1] + dp(4))
    lbl.pos = ((Window.width - lbl.width) / 2, dp(100))
    with lbl.canvas.before:
        from kivy.graphics import Color, RoundedRectangle
        Color(*NAVY[:3], 0.92)
        rr = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[dp(16)])
    lbl.bind(pos=lambda w, v: setattr(rr, "pos", v))
    lbl.opacity = 0
    Window.add_widget(lbl)
    anim = Animation(opacity=1, duration=0.2) + Animation(duration=duration) + \
        Animation(opacity=0, duration=0.4)
    anim.bind(on_complete=lambda *a: Window.remove_widget(lbl))
    anim.start(lbl)
