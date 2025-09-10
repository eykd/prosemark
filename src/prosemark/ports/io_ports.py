"""I/O port protocols for external interactions."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EditorPort(Protocol):
    """Protocol for editor integration.

    Handles launching external editors for file editing,
    with support for cursor positioning hints.
    """

    def open(self, path: str, *, cursor_hint: str | None = None) -> None:
        """Open file in configured editor.

        Args:
            path: Path to file to open
            cursor_hint: Optional hint for cursor positioning

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If unable to launch editor

        """
        ...


@runtime_checkable
class ConsolePort(Protocol):
    """Protocol for console output.

    Handles formatted output to the user's console,
    including tree structures and command results.
    """

    def print(self, msg: str) -> None:
        """Print message to console.

        Args:
            msg: Message to display to user

        """
        ...
