"""Abstract base class for output formatting."""

from abc import ABC, abstractmethod


class ConsolePort(ABC):
    """Abstract base class for output formatting.

    Defines the contract for displaying formatted text output to users.
    This abstract base class enables:

    * Clean separation between business logic and UI presentation
    * Testable output through dependency injection and mocking
    * Support for different output targets (console, GUI, web interface)
    * Hexagonal architecture compliance by isolating presentation concerns
    * Future extensibility to different user interface adapters

    The MVP uses this for displaying binder structure trees, audit results,
    and general command output. Implementations should handle formatting,
    colors, tree rendering, and other presentation concerns.

    Examples:
        >>> class TestConsolePort(ConsolePort):
        ...     def print(self, msg: str) -> None:
        ...         print(f'[TEST] {msg}')
        >>> console = TestConsolePort()
        >>> console.print('Hello, world!')
        [TEST] Hello, world!

    """

    @abstractmethod
    def print(self, msg: str) -> None:
        """Display formatted message to the user.

        This method must be implemented by concrete subclasses to provide
        specific output formatting and targeting (stdout, GUI, web, etc.).

        Implementations should handle all presentation concerns including:
        - Message formatting and styling
        - Color support and terminal detection
        - Tree rendering with appropriate connectors
        - Output stream selection (stdout vs stderr)

        Args:
            msg: The formatted message content to display

        Raises:
            NotImplementedError: If not implemented by a concrete subclass

        """
        raise NotImplementedError('Subclasses must implement the print() method')  # pragma: no cover
