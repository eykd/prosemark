"""Freewrite service port interface for core domain operations."""  # pragma: no cover

from typing import Protocol  # pragma: no cover


class FreewriteServicePort(Protocol):  # pragma: no cover
    """Port interface for freewriting service operations."""

    def some_method(self) -> object:  # pragma: no cover
        """Placeholder method for freewrite operations.

        Returns:
            Object result from freewrite operation.

        """
        ...  # pragma: no cover
