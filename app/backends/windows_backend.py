"""
Windows input backend using ctypes SendInput.

Preferred over pywin32 — no extra dependency, works in any Python env.
Media keys use the KEYEVENTF_EXTENDEDKEY flag required by Windows for
consumer/multimedia virtual key codes.
"""

import ctypes
import ctypes.wintypes as wt
from ctypes import Structure, Union, POINTER, pointer, sizeof

from .base import InputBackend

# ── Win32 constants ────────────────────────────────────────────────────────

INPUT_KEYBOARD = 1
INPUT_MOUSE    = 0

KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_UNICODE     = 0x0004

MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_WHEEL      = 0x0800
WHEEL_DELTA            = 120

# Virtual key codes
VK_MAP: dict[str, int] = {
    # Media
    "play_pause": 0xB3,
    "stop":       0xB2,
    "next":       0xB0,
    "prev":       0xB1,
    "vol_up":     0xAF,
    "vol_down":   0xAE,
    "mute":       0xAD,
    # Navigation
    "up":         0x26,
    "down":       0x28,
    "left":       0x25,
    "right":      0x27,
    "ok":         0x0D,  # VK_RETURN
    "back":       0x1B,  # VK_ESCAPE
    "home":       0x24,  # VK_HOME
    "menu":       0x79,  # VK_F10
    # Editing
    "backspace":  0x08,  # VK_BACK
    # Numbers
    **{str(n): 0x30 + n for n in range(10)},
}

# Media VKs need EXTENDEDKEY; navigation keys don't
_EXTENDED_VKS = {0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2, 0xB3}


# ── SendInput structures ───────────────────────────────────────────────────

class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx",          wt.LONG),
        ("dy",          wt.LONG),
        ("mouseData",   wt.DWORD),
        ("dwFlags",     wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", POINTER(wt.ULONG)),
    ]


class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk",         wt.WORD),
        ("wScan",       wt.WORD),
        ("dwFlags",     wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", POINTER(wt.ULONG)),
    ]


class _INPUT_UNION(Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(Structure):
    _fields_ = [("type", wt.DWORD), ("_input", _INPUT_UNION)]


_send = ctypes.windll.user32.SendInput


def _kbd_input(vk: int, flags: int = 0) -> INPUT:
    if vk in _EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    i = INPUT(type=INPUT_KEYBOARD)
    i._input.ki = KEYBDINPUT(wVk=vk, dwFlags=flags)
    return i


def _unicode_input(char: str, flags: int = 0) -> INPUT:
    i = INPUT(type=INPUT_KEYBOARD)
    i._input.ki = KEYBDINPUT(wScan=ord(char), dwFlags=KEYEVENTF_UNICODE | flags)
    return i


def _mouse_input(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> INPUT:
    i = INPUT(type=INPUT_MOUSE)
    i._input.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags)
    return i


def _send_inputs(*inputs: INPUT) -> None:
    arr = (INPUT * len(inputs))(*inputs)
    _send(len(inputs), arr, sizeof(INPUT))


# ── Backend ────────────────────────────────────────────────────────────────

class WindowsBackend(InputBackend):

    def press_key(self, key_name: str) -> None:
        vk = VK_MAP.get(key_name)
        if vk is None:
            return
        _send_inputs(_kbd_input(vk), _kbd_input(vk, KEYEVENTF_KEYUP))

    def type_text(self, text: str) -> None:
        inputs: list[INPUT] = []
        for ch in text:
            inputs.append(_unicode_input(ch))
            inputs.append(_unicode_input(ch, KEYEVENTF_KEYUP))
        if inputs:
            _send_inputs(*inputs)

    def move_mouse(self, dx: int, dy: int) -> None:
        _send_inputs(_mouse_input(MOUSEEVENTF_MOVE, dx=dx, dy=dy))

    def click(self, button: str) -> None:
        down_up = {
            "left":   (MOUSEEVENTF_LEFTDOWN,   MOUSEEVENTF_LEFTUP),
            "right":  (MOUSEEVENTF_RIGHTDOWN,  MOUSEEVENTF_RIGHTUP),
            "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }.get(button, (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP))
        _send_inputs(_mouse_input(down_up[0]), _mouse_input(down_up[1]))

    def scroll(self, dx: int, dy: int) -> None:
        if dy:
            _send_inputs(_mouse_input(MOUSEEVENTF_WHEEL, data=dy * WHEEL_DELTA))
