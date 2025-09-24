"""Freewrite service port interface for core domain operations."""

from typing import Protocol


class FreewriteServicePort(Protocol):
    """Port interface for freewriting service operations."""

    def some_method(self) -> object:
        """Placeholder method for freewrite operations.

        Returns:
            Object result from freewrite operation.

        """
        ...
