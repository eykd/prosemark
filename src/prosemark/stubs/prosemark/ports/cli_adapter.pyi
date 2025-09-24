from typing import Protocol

class CLIAdapterPort(Protocol):
    def some_method(self) -> object: ...
