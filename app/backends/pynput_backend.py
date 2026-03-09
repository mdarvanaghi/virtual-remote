from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

from .base import InputBackend

KEY_MAP: dict[str, Key | str] = {
    # Media
    "play_pause":   Key.media_play_pause,
    "stop":         Key.media_stop,
    "next":         Key.media_next,
    "prev":         Key.media_previous,
    "vol_up":       Key.media_volume_up,
    "vol_down":     Key.media_volume_down,
    "mute":         Key.media_volume_mute,
    # Navigation
    "up":           Key.up,
    "down":         Key.down,
    "left":         Key.left,
    "right":        Key.right,
    "ok":           Key.enter,
    "back":         Key.esc,
    "home":         Key.home,
    "menu":         Key.f10,
    # Editing
    "backspace":    Key.backspace,
    # Number keys
    **{str(n): str(n) for n in range(10)},
}

MOUSE_BUTTON_MAP: dict[str, Button] = {
    "left":   Button.left,
    "right":  Button.right,
    "middle": Button.middle,
}


class PynputBackend(InputBackend):

    def __init__(self) -> None:
        self._kb = KeyboardController()
        self._mouse = MouseController()

    def press_key(self, key_name: str) -> None:
        key = KEY_MAP.get(key_name)
        if key is None:
            return
        self._kb.press(key)
        self._kb.release(key)

    def type_text(self, text: str) -> None:
        self._kb.type(text)

    def move_mouse(self, dx: int, dy: int) -> None:
        self._mouse.move(dx, dy)

    def click(self, button: str) -> None:
        btn = MOUSE_BUTTON_MAP.get(button, Button.left)
        self._mouse.click(btn)

    def scroll(self, dx: int, dy: int) -> None:
        self._mouse.scroll(dx, dy)
