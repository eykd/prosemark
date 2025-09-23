"""Abstract base class for output formatting."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder, BinderItem


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
        msg = 'Subclasses must implement the print() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    def print_info(self, msg: str) -> None:
        """Display an informational message.

        Args:
            msg: The informational message content to display

        """
        self.print(f'INFO: {msg}')

    def print_success(self, msg: str) -> None:
        """Display a success message.

        Args:
            msg: The success message content to display

        """
        self.print(f'SUCCESS: {msg}')

    def print_warning(self, msg: str) -> None:
        """Display a warning message.

        Args:
            msg: The warning message content to display

        """
        self.print(f'WARNING: {msg}')

    def print_error(self, msg: str) -> None:
        """Display an error message.

        Args:
            msg: The error message content to display

        """
        self.print(f'ERROR: {msg}')

    def print_tree(self, binder: 'Binder') -> None:
        """Display a formatted tree representation of a binder structure.

        Default implementation provides basic tree rendering. Subclasses can
        override for custom formatting and visual styles.

        Args:
            binder: The Binder object containing the hierarchical structure

        """
        # Basic implementation - just print a simple representation
        self.print(f'Binder: {binder.project_title}')
        for item in binder.children:
            self._print_item(item, indent=0)

    def _print_item(self, item: 'BinderItem', indent: int) -> None:
        """Helper method to print a binder item with indentation."""
        prefix = '  ' * indent + '- '
        display = f'{item.display_title}'
        if item.node_id:
            display += f' ({item.node_id})'
        self.print(f'{prefix}{display}')

        for child in item.children:
            self._print_item(child, indent + 1)
