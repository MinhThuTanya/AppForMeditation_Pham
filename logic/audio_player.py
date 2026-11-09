import json
import os

LIBRARY_PATH = "assets/library.json"


def load_library(path=LIBRARY_PATH):
    """Каталог медитаций, историй для сна, музыки и фоновых звуков."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class AudioPlayer:
    """Обёртка над SoundLoader из Kivy: play(), pause(), stop().
    Kivy импортируется внутри методов, чтобы остальной модуль
    можно было проверять без графической части."""

    def __init__(self):
        self.sound = None
        self._pos = 0

    def load(self, filename, loop=True, volume=1.0):
        self.stop()
        if not filename or not os.path.exists(filename):
            return False
        from kivy.core.audio import SoundLoader
        self.sound = SoundLoader.load(filename)
        if self.sound is None:
            return False
        self.sound.loop = loop
        self.sound.volume = volume
        self._pos = 0
        return True

    def play(self):
        if self.sound:
            self.sound.play()
            if self._pos:
                self.sound.seek(self._pos)

    def pause(self):
        if self.sound and self.sound.state == "play":
            self._pos = self.sound.get_pos()
            self.sound.stop()

    def stop(self):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
        self.sound = None
        self._pos = 0

    @property
    def playing(self):
        return bool(self.sound and self.sound.state == "play")
