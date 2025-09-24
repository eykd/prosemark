from typing import Protocol

class TUIAdapterPort(Protocol):
    def some_method(self) -> object: ...
