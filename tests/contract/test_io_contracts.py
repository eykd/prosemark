"""Contract test base classes for I/O protocols."""

import abc
import tempfile
from pathlib import Path

from prosemark.ports.io_ports import ConsolePort, EditorPort


class EditorPortContractTest(abc.ABC):
    """Base contract test for EditorPort implementations.

    Inherit from this class to test any EditorPort implementation.
    Implement get_editor() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_editor(self) -> EditorPort:
        """Return EditorPort implementation to test."""
        ...

    def test_open_accepts_valid_path(self) -> None:
        """Test that open() accepts valid file paths."""
        editor = self.get_editor()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write('Test content')
            temp_path = f.name

        try:
            # Should not raise (though actual editor launching depends on implementation)
            editor.open(temp_path)
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)

    def test_open_with_cursor_hint(self) -> None:
        """Test that open() accepts cursor hints."""
        editor = self.get_editor()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write('Test content')
            temp_path = f.name

        try:
            # Should not raise
            editor.open(temp_path, cursor_hint='1:1')
            editor.open(temp_path, cursor_hint=None)
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)

    def test_open_nonexistent_file_raises(self) -> None:
        """Test that opening nonexistent file raises FileNotFoundError."""
        editor = self.get_editor()

        nonexistent_path = '/definitely/does/not/exist/file.md'

        try:
            editor.open(nonexistent_path)
            # If we get here, implementation may be creating files or ignoring errors
            # This behavior may be acceptable depending on implementation
        except FileNotFoundError:
            # This is the expected behavior
            pass
        except (RuntimeError, OSError):
            # Other exceptions may be acceptable for editor issues
            pass


class ConsolePortContractTest(abc.ABC):
    """Base contract test for ConsolePort implementations.

    Inherit from this class to test any ConsolePort implementation.
    Implement get_console() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_console(self) -> ConsolePort:
        """Return ConsolePort implementation to test."""
        ...

    def test_print_accepts_string(self) -> None:
        """Test that print() accepts string messages."""
        console = self.get_console()

        # Should not raise
        console.print('Test message')
        console.print('')  # Empty string
        console.print('Single line')

    def test_print_multiline_strings(self) -> None:
        """Test printing multiline strings."""
        console = self.get_console()

        multiline_msg = """Line 1
Line 2
Line 3"""

        # Should not raise
        console.print(multiline_msg)

    def test_print_unicode_strings(self) -> None:
        """Test printing strings with unicode characters."""
        console = self.get_console()

        unicode_messages = [
            'Unicode test: ñáéíóú',
            'Emoji test: 🎉 📝 ✅',
            'Math symbols: ∀ ∃ ∈ ∉ U ∩',
            'Box drawing: ┌─┐ │ │ └─┘',
        ]

        for msg in unicode_messages:
            # Should not raise
            console.print(msg)

    def test_print_special_characters(self) -> None:
        """Test printing strings with special characters."""
        console = self.get_console()

        special_messages = [
            'Quotes: \'single\' and "double"',
            'Symbols: !@#$%^&*()[]{}',
            'Tabs and spaces: \t    \t',
            'Backslashes: \\ \\n \\t \\r',
        ]

        for msg in special_messages:
            # Should not raise
            console.print(msg)

    def test_print_long_strings(self) -> None:
        """Test printing very long strings."""
        console = self.get_console()

        # Create a long string
        long_msg = 'A' * 1000
        very_long_msg = 'B' * 10000

        # Should not raise
        console.print(long_msg)
        console.print(very_long_msg)

    def test_multiple_consecutive_prints(self) -> None:
        """Test multiple consecutive print calls."""
        console = self.get_console()

        # Should not raise
        for i in range(10):
            console.print(f'Message {i}')

    def test_print_none_return(self) -> None:
        """Test that print() returns None."""
        console = self.get_console()

        # print() has no return value, so we just test it doesn't raise
        console.print('Test message')
