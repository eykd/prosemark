"""Mock implementations for I/O protocols."""

from pathlib import Path


class MockEditorPort:
    """Mock implementation of EditorPort for testing."""

    def __init__(self, raise_on_nonexistent: bool = True) -> None:
        """Initialize mock editor.
        
        Args:
            raise_on_nonexistent: Whether to raise FileNotFoundError for missing files

        """
        self._opened_files: list[tuple[str, str | None]] = []
        self._raise_on_nonexistent = raise_on_nonexistent
        self.open_called = 0

    def open(self, path: str, *, cursor_hint: str | None = None) -> None:
        """Mock opening file in editor."""
        self.open_called += 1

        if self._raise_on_nonexistent and not Path(path).exists():
            raise FileNotFoundError(f'File not found: {path}')

        self._opened_files.append((path, cursor_hint))

    def get_opened_files(self) -> list[tuple[str, str | None]]:
        """Get list of (path, cursor_hint) tuples for opened files."""
        return self._opened_files.copy()

    def clear_opened_files(self) -> None:
        """Clear the list of opened files."""
        self._opened_files.clear()
        self.open_called = 0

    def was_file_opened(self, path: str) -> bool:
        """Check if a specific file was opened."""
        return any(opened_path == path for opened_path, _ in self._opened_files)

    def get_cursor_hints_for_file(self, path: str) -> list[str | None]:
        """Get all cursor hints used when opening a specific file."""
        return [hint for opened_path, hint in self._opened_files if opened_path == path]


class MockConsolePort:
    """Mock implementation of ConsolePort for testing."""

    def __init__(self) -> None:
        """Initialize mock console."""
        self._printed_messages: list[str] = []
        self.print_called = 0

    def print(self, msg: str) -> None:
        """Mock printing message to console."""
        self.print_called += 1
        self._printed_messages.append(msg)

    def get_printed_messages(self) -> list[str]:
        """Get all printed messages."""
        return self._printed_messages.copy()

    def clear_printed_messages(self) -> None:
        """Clear all printed messages."""
        self._printed_messages.clear()
        self.print_called = 0

    def get_all_output(self) -> str:
        """Get all output as a single string."""
        return '\n'.join(self._printed_messages)

    def was_message_printed(self, message: str) -> bool:
        """Check if an exact message was printed."""
        return message in self._printed_messages

    def was_text_printed(self, text: str) -> bool:
        """Check if any printed message contains the given text."""
        return any(text in msg for msg in self._printed_messages)

    def get_messages_containing(self, text: str) -> list[str]:
        """Get all messages that contain the given text."""
        return [msg for msg in self._printed_messages if text in msg]
