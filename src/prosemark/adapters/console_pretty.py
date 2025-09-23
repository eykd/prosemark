# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Pretty console output implementation with colors and formatting."""

import os
import sys
from typing import TYPE_CHECKING, TextIO

from prosemark.ports.console_port import ConsolePort

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder, BinderItem


class ConsolePretty(ConsolePort):
    """Production console implementation with rich formatting and colors.

    This implementation provides enhanced console output with:
    - Color support with automatic terminal detection
    - Pretty tree rendering with Unicode box-drawing characters
    - Proper stdout/stderr stream handling
    - Graceful fallback for non-color terminals

    The adapter handles all presentation concerns while keeping the
    business logic focused on content generation.
    """

    def __init__(self, output_stream: TextIO = sys.stdout) -> None:
        """Initialize console with specified output stream.

        Args:
            output_stream: Target stream for output (default: sys.stdout)

        """
        self.output_stream = output_stream
        self._supports_color = self._detect_color_support()

    def print(self, msg: str) -> None:
        """Display formatted message to the console.

        Args:
            msg: The message content to display

        """
        print(msg, file=self.output_stream)

    def print_tree(self, binder: 'Binder') -> None:
        """Display formatted tree representation of binder structure.

        Args:
            binder: The Binder object containing the hierarchical structure

        """
        # For now, implement a simple tree representation
        # This can be enhanced later with proper tree formatting
        self.print('Binder structure:')
        for item in binder.roots:
            self._print_tree_item(item, indent=0)

    def _print_tree_item(self, item: 'BinderItem', indent: int = 0) -> None:
        """Print a single tree item with proper indentation.

        Args:
            item: The BinderItem to print
            indent: Current indentation level

        """
        prefix = '  ' * indent + '- '
        display = item.display_title or str(item.id)
        self.print(f'{prefix}{display}')

        for child in item.children:
            self._print_tree_item(child, indent + 1)

    def _detect_color_support(self) -> bool:
        """Detect if the terminal supports color output.

        Returns:
            True if terminal supports colors, False otherwise

        """
        # Simple color detection - check if stdout is a TTY
        # and not explicitly disabled
        if not hasattr(self.output_stream, 'isatty'):
            return False

        if not self.output_stream.isatty():
            return False

        # Check common environment variables that disable color
        if os.environ.get('NO_COLOR'):
            return False

        return os.environ.get('TERM') != 'dumb'
