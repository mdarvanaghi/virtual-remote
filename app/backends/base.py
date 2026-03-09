from abc import ABC, abstractmethod


class InputBackend(ABC):

    @abstractmethod
    def press_key(self, key_name: str) -> None: ...

    @abstractmethod
    def type_text(self, text: str) -> None: ...

    @abstractmethod
    def move_mouse(self, dx: int, dy: int) -> None: ...

    @abstractmethod
    def click(self, button: str) -> None: ...

    @abstractmethod
    def scroll(self, dx: int, dy: int) -> None: ...
