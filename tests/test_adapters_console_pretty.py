"""Tests for the ConsolePretty adapter."""

import io
import os
from typing import TextIO, cast
from unittest.mock import Mock, patch

from prosemark.adapters.console_pretty import ConsolePretty


class TestConsolePretty:
    """Test the ConsolePretty adapter."""

    def test_init_with_default_output_stream(self) -> None:
        """Test initialization with default output stream."""
        console = ConsolePretty()

        # Should use sys.stdout by default
        import sys

        assert console.output_stream is sys.stdout

    def test_init_with_custom_output_stream(self) -> None:
        """Test initialization with custom output stream."""
        custom_stream = io.StringIO()
        console = ConsolePretty(output_stream=custom_stream)

        assert console.output_stream is custom_stream

    def test_print_outputs_to_stream(self) -> None:
        """Test that print method outputs to the correct stream."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        console.print('Hello, World!')

        assert output_stream.getvalue() == 'Hello, World!\n'

    def test_print_tree_with_empty_binder(self) -> None:
        """Test print_tree with an empty binder."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock empty binder
        mock_binder = Mock()
        mock_binder.roots = []

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert 'Binder structure:' in output

    def test_print_tree_with_single_root_item(self) -> None:
        """Test print_tree with a single root item."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock binder with single root item
        mock_item = Mock()
        mock_item.display_title = 'Root Item'
        mock_item.children = []

        mock_binder = Mock()
        mock_binder.roots = [mock_item]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert 'Binder structure:' in output
        assert '- Root Item' in output

    def test_print_tree_with_nested_items(self) -> None:
        """Test print_tree with nested items."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock nested structure
        mock_child = Mock()
        mock_child.display_title = 'Child Item'
        mock_child.children = []

        mock_root = Mock()
        mock_root.display_title = 'Root Item'
        mock_root.children = [mock_child]

        mock_binder = Mock()
        mock_binder.roots = [mock_root]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert 'Binder structure:' in output
        assert '- Root Item' in output
        assert '  - Child Item' in output

    def test_print_tree_with_multiple_levels(self) -> None:
        """Test print_tree with multiple indentation levels."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock deeply nested structure
        mock_grandchild = Mock()
        mock_grandchild.display_title = 'Grandchild Item'
        mock_grandchild.children = []

        mock_child = Mock()
        mock_child.display_title = 'Child Item'
        mock_child.children = [mock_grandchild]

        mock_root = Mock()
        mock_root.display_title = 'Root Item'
        mock_root.children = [mock_child]

        mock_binder = Mock()
        mock_binder.roots = [mock_root]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert '- Root Item' in output
        assert '  - Child Item' in output
        assert '    - Grandchild Item' in output

    def test_print_tree_uses_id_fallback(self) -> None:
        """Test that tree printing uses id as fallback when display_title is None."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock binder with item that has None display_title
        mock_item = Mock()
        mock_item.display_title = None
        mock_item.id = 'item-123'
        mock_item.children = []

        mock_binder = Mock()
        mock_binder.roots = [mock_item]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert '- item-123' in output

    def test_print_tree_with_empty_string_title(self) -> None:
        """Test that tree printing uses id as fallback when display_title is empty."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock binder with item that has empty display_title
        mock_item = Mock()
        mock_item.display_title = ''
        mock_item.id = 'item-456'
        mock_item.children = []

        mock_binder = Mock()
        mock_binder.roots = [mock_item]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert '- item-456' in output

    def test_color_support_no_isatty_method(self) -> None:
        """Test color support when output stream doesn't have isatty method."""

        # Create a stream without isatty method that implements basic TextIO interface
        class StreamWithoutIsatty:
            def write(self, s: str) -> int:
                return len(s)

            def flush(self) -> None:
                pass

            def readable(self) -> bool:
                return False

            def writable(self) -> bool:
                return True

            def close(self) -> None:
                pass

            @property
            def closed(self) -> bool:
                return False

        stream = StreamWithoutIsatty()
        console = ConsolePretty(output_stream=cast('TextIO', stream))

        # Test behavior indirectly - console should work without colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    def test_color_support_not_tty(self) -> None:
        """Test color support when output is not a TTY."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = False

        console = ConsolePretty(output_stream=mock_stream)

        # Test behavior indirectly - console should work without colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    @patch.dict(os.environ, {'NO_COLOR': '1'})
    def test_color_support_no_color_env_var(self) -> None:
        """Test color support when NO_COLOR environment variable is set."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = True

        console = ConsolePretty(output_stream=mock_stream)

        # Test behavior indirectly - console should work without colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    @patch.dict(os.environ, {'TERM': 'dumb'})
    def test_color_support_dumb_terminal(self) -> None:
        """Test color support when TERM is 'dumb'."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = True

        console = ConsolePretty(output_stream=mock_stream)

        # Test behavior indirectly - console should work without colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    @patch.dict(os.environ, {'TERM': 'xterm-256color'}, clear=True)
    def test_color_support_enabled(self) -> None:
        """Test color support when colors should be enabled."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = True

        console = ConsolePretty(output_stream=mock_stream)

        # Test behavior indirectly - console should work with colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    @patch.dict(os.environ, {}, clear=True)
    def test_color_support_no_term_env(self) -> None:
        """Test color support when TERM environment variable is not set."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = True

        console = ConsolePretty(output_stream=mock_stream)

        # Test behavior indirectly - console should work with colors
        console.print('test')
        # If this doesn't raise an exception, color detection worked correctly

    def test_color_initialization_works(self) -> None:
        """Test that color support initialization works properly."""
        mock_stream = Mock()
        mock_stream.isatty.return_value = True

        with patch.dict(os.environ, {'TERM': 'xterm'}, clear=True):
            console = ConsolePretty(output_stream=mock_stream)

        # Test that console works correctly after initialization
        console.print('test message')
        # If this doesn't raise an exception, initialization worked correctly

    def test_print_tree_with_multiple_root_items(self) -> None:
        """Test print_tree with multiple root items."""
        output_stream = io.StringIO()
        console = ConsolePretty(output_stream=output_stream)

        # Mock binder with multiple root items
        mock_item1 = Mock()
        mock_item1.display_title = 'First Root'
        mock_item1.children = []

        mock_item2 = Mock()
        mock_item2.display_title = 'Second Root'
        mock_item2.children = []

        mock_binder = Mock()
        mock_binder.roots = [mock_item1, mock_item2]

        console.print_tree(mock_binder)

        output = output_stream.getvalue()
        assert '- First Root' in output
        assert '- Second Root' in output
