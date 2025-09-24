from typing import Protocol

class FreewriteServicePort(Protocol):
    def some_method(self) -> object: ...
