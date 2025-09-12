"""EditorPort abstract base class for external editor integration.

This module defines the EditorPort abstract base class that provides a contract
for opening files in external editors (VS Code, Vim, Emacs, etc.). The abstract
base class enables:

* Cross-platform editor launching ($EDITOR, OS defaults)
* Testable editor integration through dependency injection
* Support for different editors and launch strategies
* Hexagonal architecture compliance by isolating system editor concerns
* Optional cursor positioning hints for better UX
"""

from abc import ABC, abstractmethod


class EditorPort(ABC):
    """Abstract base class for external editor integration.

    Defines the contract for opening files in external editors with support
    for cross-platform editor launching and optional cursor positioning hints.

    Implementations should handle:
    - System-specific editor launching
    - Editor detection and configuration
    - Error handling for missing files or launch failures

    Raises:
        FileNotFoundError: When the specified file path does not exist
        EditorLaunchError: When the editor cannot be launched or fails to start

    """

    @abstractmethod
    def open(self, path: str, *, cursor_hint: str | None = None) -> None:
        """Open a file in the external editor.

        Args:
            path: Absolute or relative file path to open
            cursor_hint: Optional positioning hint for cursor placement.
                        Could be line number, search pattern, or
                        implementation-specific format.

        Raises:
            FileNotFoundError: When the specified file does not exist
            EditorLaunchError: When editor cannot be launched

        Examples:
            >>> editor.open('/path/to/file.txt')
            >>> editor.open('draft.md', cursor_hint='42')  # Line 42
            >>> editor.open('notes.txt', cursor_hint=':search_term')  # Search pattern

        """
        ...  # pragma: no cover
