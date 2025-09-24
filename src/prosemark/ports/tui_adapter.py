"""TUI adapter port interface for terminal user interface operations."""

from typing import Protocol


class TUIAdapterPort(Protocol):
    """Port interface for terminal user interface operations."""

    def some_method(self) -> object:
        """Placeholder method for TUI operations.

        Returns:
            Object result from TUI operation.

        """
        ...
