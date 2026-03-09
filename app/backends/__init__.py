import os

from .base import InputBackend


def get_backend() -> InputBackend:
    backend = os.getenv("INPUT_BACKEND", "pynput").lower()
    if backend == "pynput":
        from .pynput_backend import PynputBackend
        return PynputBackend()
    if backend == "windows":
        from .windows_backend import WindowsBackend
        return WindowsBackend()
    raise ValueError(f"Unknown INPUT_BACKEND: {backend!r}")
