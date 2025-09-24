"""TUI adapter port interface for terminal user interface operations."""  # pragma: no cover

from typing import Protocol  # pragma: no cover


class TUIAdapterPort(Protocol):  # pragma: no cover
    """Port interface for terminal user interface operations."""

    def some_method(self) -> object:  # pragma: no cover
        """Placeholder method for TUI operations.

        Returns:
            Object result from TUI operation.

        """
        ...  # pragma: no cover
