"""Экран оценки стресса (F.01): 5 вопросов со слайдером, расчёт по формулам (1) и (2)."""
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.screen import MDScreen

from logic import avatar, stress

Builder.load_string('''
#:import W screens.widgets

<StressTestScreen>:
    canvas.before:
        Color:
            rgba: W.BG
        Rectangle:
            pos: 0, 0
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(12), dp(20), dp(20)
        spacing: dp(14)
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            MDIconButton:
                icon: "close"
                on_release: app.back()
            Widget:
            Label:
                text: app.t("skip_test", app.lang)
                font_name: W.SANS_MED
                font_size: "13sp"
                color: W.BLUE2
                size_hint_x: None
                width: dp(120)
                opacity: 0 if root.done else 1
                on_touch_down: if self.collide_point(*args[1].pos) and not root.done: root.skip()
        Body:
            text: app.t("question_n", app.lang).format(root.index + 1, root.count) if not root.done else app.t("result", app.lang)
        Widget:
            size_hint_y: None
            height: dp(6)
            canvas:
                Color:
                    rgba: W.SKY
                RoundedRectangle:
                    pos: self.pos
                    size: self.width, dp(6)
                    radius: [dp(3)]
                Color:
                    rgba: W.BLUE2
                RoundedRectangle:
                    pos: self.pos
                    size: self.width * ((root.index + (1 if root.done else 0)) / root.count), dp(6)
                    radius: [dp(3)]
        # --- вопрос ---
        BoxLayout:
            orientation: "vertical"
            spacing: dp(14)
            opacity: 0 if root.done else 1
            disabled: root.done
            size_hint_y: 0.001 if root.done else 1
            Title:
                text: root.question
            Widget:
                size_hint_y: None
                height: dp(20)
            Label:
                text: str(int(slider.value))
                font_name: W.SERIF
                font_size: "54sp"
                color: W.BLUE2
                size_hint_y: None
                height: dp(70)
            MDSlider:
                id: slider
                min: 1
                max: 10
                step: 1
                value: 5
                size_hint_y: None
                height: dp(48)
                MDSliderHandle:
            BoxLayout:
                size_hint_y: None
                height: dp(20)
                Body:
                    text: root.low_hint
                    font_size: "12sp"
                Body:
                    text: root.high_hint
                    font_size: "12sp"
                    halign: "right"
            Widget:
            BoxLayout:
                size_hint_y: None
                height: dp(52)
                spacing: dp(12)
                Pill:
                    text: app.t("back", app.lang).upper()
                    bg: W.WHITE
                    fg: W.NAVY
                    disabled: root.index == 0
                    opacity: 0.4 if root.index == 0 else 1
                    on_release: root.prev()
                Pill:
                    text: (app.t("next", app.lang) if root.index < root.count - 1 else app.t("finish", app.lang)).upper()
                    on_release: root.next()
        # --- результат ---
        Card:
            opacity: 1 if root.done else 0
            disabled: not root.done
            size_hint_y: None
            height: self.minimum_height if root.done else 0
            Label:
                text: root.result_title
                font_name: W.SERIF
                font_size: "28sp"
                color: W.BLUE2
                size_hint_y: None
                height: dp(40)
            Body:
                text: root.result_text
                halign: "center"
            Pill:
                text: app.t("start_recommended", app.lang).upper()
                on_release: root.open_recommended()
            Pill:
                text: app.t("to_home", app.lang).upper()
                bg: W.SKY
                fg: W.NAVY
                on_release: app.tab("home")
''')

LOW_HIGH = ["sq1", "sq2", "sq3", "sq4", "sq5"]
CAT_KEYS = {"высокий": "stress_high", "умеренный": "stress_moderate", "низкий": "stress_low"}
RECOMMEND = {"высокий": "anxiety", "умеренный": "evening_calm", "низкий": "focus"}


class StressTestScreen(MDScreen):
    index = NumericProperty(0)
    count = NumericProperty(len(stress.QUESTIONS))
    question = StringProperty("")
    low_hint = StringProperty("")
    high_hint = StringProperty("")
    done = BooleanProperty(False)
    result_title = StringProperty("")
    result_text = StringProperty("")

    def prepare(self, **_):
        self.answers = [5] * self.count
        self.index = 0
        self.done = False
        self._show()

    def _show(self):
        app = App.get_running_app()
        k = LOW_HIGH[self.index]
        self.question = app.t(k)            # вопросы хранятся по ключам (не зависят от языка)
        self.low_hint = app.t(k + "_low")
        self.high_hint = app.t(k + "_high")
        self.ids.slider.value = self.answers[self.index]

    def next(self):
        self.answers[self.index] = int(self.ids.slider.value)
        if self.index < self.count - 1:
            self.index += 1
            self._show()
        else:
            self.finish()

    def prev(self):
        self.answers[self.index] = int(self.ids.slider.value)
        if self.index > 0:
            self.index -= 1
            self._show()

    def finish(self):
        app = App.get_running_app()
        s, category = stress.save_stress_result(self.answers)
        avatar.update_avatar()
        self.category = category
        self.done = True
        self.result_title = app.t(CAT_KEYS[category])
        score = str(s).replace(".", ",") if app.lang == "ru" else str(s)
        self.result_text = app.t("stress_index").format(score) + "\n\n" + app.t(CAT_KEYS[category] + "_advice")

    def skip(self):
        """F.01.01: тест можно пропустить — показываются стандартные рекомендации."""
        app = App.get_running_app()
        app.toast(app.t("skipped_test"))
        app.tab("home")

    def open_recommended(self):
        App.get_running_app().tab("player", item_id=RECOMMEND[self.category])
