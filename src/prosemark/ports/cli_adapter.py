"""CLI adapter port interface for freewriting command line operations."""

from typing import Protocol


class CLIAdapterPort(Protocol):
    """Port interface for command line interface operations."""

    def some_method(self) -> object:
        """Placeholder method for CLI operations.

        Returns:
            Object result from CLI operation.

        """
        ...
