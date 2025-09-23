# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Fake console adapter for testing output operations."""

from typing import TYPE_CHECKING

from prosemark.ports.console_port import ConsolePort

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder


class FakeConsolePort(ConsolePort):
    """In-memory fake implementation of ConsolePort for testing.

    Provides minimal console output functionality by collecting messages
    in memory instead of displaying them. Includes test helper methods
    for asserting console output in tests.

    This fake stores all printed messages in order and provides methods
    to inspect the output for test assertions without exposing internal
    implementation details.

    Examples:
        >>> console = FakeConsolePort()
        >>> console.print('Hello, world!')
        >>> console.print('Goodbye!')
        >>> console.get_output()
        ['Hello, world!', 'Goodbye!']
        >>> console.last_output()
        'Goodbye!'
        >>> console.output_contains('Hello')
        True

    """

    def __init__(self) -> None:
        """Initialize empty fake console port."""
        self._output: list[str] = []
        self._tree_calls: list[Binder] = []

    def print(self, msg: str) -> None:
        """Store message in output buffer.

        Args:
            msg: Message to add to the output buffer.

        """
        self._output.append(msg)

    def print_tree(self, binder: 'Binder') -> None:
        """Store binder tree call for testing.

        Args:
            binder: Binder object to store for verification in tests.

        """
        self._tree_calls.append(binder)

    def get_output(self) -> list[str]:
        """Return list of all printed messages.

        Returns:
            List of messages in the order they were printed.

        """
        return self._output.copy()

    def last_output(self) -> str:
        """Return the last printed message.

        Returns:
            The most recently printed message.

        Raises:
            IndexError: If no messages have been printed.

        """
        if not self._output:  # pragma: no cover
            msg = 'No output has been printed'
            raise IndexError(msg)  # pragma: no cover
        return self._output[-1]  # pragma: no cover

    def output_contains(self, text: str) -> bool:
        """Check if any output contains the given text.

        Args:
            text: Text to search for in the output.

        Returns:
            True if any message contains the given text.

        """
        return any(text in msg for msg in self._output)

    def get_tree_calls(self) -> list['Binder']:
        """Return list of all print_tree calls.

        Returns:
            List of Binder objects passed to print_tree in order.

        """
        return self._tree_calls.copy()

    def tree_call_count(self) -> int:
        """Return the number of print_tree calls made.

        Returns:
            Number of times print_tree was called.

        """
        return len(self._tree_calls)
