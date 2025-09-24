"""CLI adapter port interface for freewriting command line operations."""  # pragma: no cover

from typing import Protocol  # pragma: no cover


class CLIAdapterPort(Protocol):  # pragma: no cover
    """Port interface for command line interface operations."""

    def some_method(self) -> object:  # pragma: no cover
        """Placeholder method for CLI operations.

        Returns:
            Object result from CLI operation.

        """
        ...  # pragma: no cover
