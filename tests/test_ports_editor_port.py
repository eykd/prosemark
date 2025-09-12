"""Tests for the EditorPort abstract base class."""

from abc import ABC
from typing import get_type_hints

import pytest

from prosemark.exceptions import EditorLaunchError
from prosemark.ports.editor_port import EditorPort


class TestEditorPortAbstractClass:
    """Test EditorPort abstract base class definition and behavior."""

    def test_editor_port_is_abstract_base_class(self) -> None:
        """Test that EditorPort is an abstract base class."""
        assert issubclass(EditorPort, ABC)
        assert hasattr(EditorPort, '__abstractmethods__')
        assert 'open' in EditorPort.__abstractmethods__

    def test_editor_port_cannot_be_instantiated(self) -> None:
        """Test that EditorPort cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            EditorPort()  # type: ignore[abstract]

    def test_editor_port_open_method_signature(self) -> None:
        """Test that EditorPort has correct open method signature."""
        # Get type hints for the abstract method
        type_hints = get_type_hints(EditorPort.open)

        # Check return type
        assert type_hints['return'] is type(None)

        # Check parameter types
        assert type_hints['path'] is str
        assert type_hints['cursor_hint'] == str | None

    def test_editor_port_accepts_file_path(self) -> None:
        """Test that EditorPort open method accepts str path parameter."""
        type_hints = get_type_hints(EditorPort.open)
        assert type_hints['path'] is str

    def test_editor_port_accepts_optional_cursor_hint(self) -> None:
        """Test that EditorPort open method accepts optional cursor_hint."""
        type_hints = get_type_hints(EditorPort.open)
        assert type_hints['cursor_hint'] == str | None

    def test_editor_port_method_is_keyword_only_for_cursor_hint(self) -> None:
        """Test that cursor_hint parameter is keyword-only."""
        import inspect

        signature = inspect.signature(EditorPort.open)
        cursor_hint_param = signature.parameters['cursor_hint']
        assert cursor_hint_param.kind == inspect.Parameter.KEYWORD_ONLY

    def test_editor_port_has_comprehensive_docstring(self) -> None:
        """Test that EditorPort has comprehensive documentation."""
        assert EditorPort.__doc__ is not None
        assert 'abstract base class' in EditorPort.__doc__.lower()
        assert 'external editor' in EditorPort.__doc__.lower()

        # Check method docstring
        assert EditorPort.open.__doc__ is not None
        assert 'cursor_hint' in EditorPort.open.__doc__
        assert 'FileNotFoundError' in EditorPort.open.__doc__
        assert 'EditorLaunchError' in EditorPort.open.__doc__


class TestEditorPortConcrete:
    """Test concrete implementations of EditorPort."""

    def test_concrete_implementation_works(self) -> None:
        """Test that concrete implementation of EditorPort works correctly."""

        class MockEditor(EditorPort):
            def __init__(self) -> None:
                self.opened_files: list[tuple[str, str | None]] = []

            def open(self, path: str, *, cursor_hint: str | None = None) -> None:
                self.opened_files.append((path, cursor_hint))

        # Should be able to instantiate concrete implementation
        editor = MockEditor()
        assert isinstance(editor, EditorPort)

        # Should be able to call open method
        editor.open('/path/to/file.txt')
        editor.open('draft.md', cursor_hint='42')

        # Verify calls were recorded
        assert editor.opened_files == [('/path/to/file.txt', None), ('draft.md', '42')]

    def test_concrete_implementation_with_missing_open_fails(self) -> None:
        """Test that concrete implementation must implement open method."""

        class IncompleteEditor(EditorPort):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteEditor()  # type: ignore[abstract]

    def test_editor_port_protocol_supports_mocking(self) -> None:
        """Test that EditorPort abstract base class supports mocking."""
        from unittest.mock import Mock

        # Create a mock that conforms to EditorPort interface
        mock_editor = Mock(spec=EditorPort)

        # Should be able to call open method on mock
        mock_editor.open('/path/to/file.txt')
        mock_editor.open('draft.md', cursor_hint='42')

        # Verify mock was called correctly
        assert mock_editor.open.call_count == 2
        mock_editor.open.assert_any_call('/path/to/file.txt')
        mock_editor.open.assert_any_call('draft.md', cursor_hint='42')

    def test_isinstance_check_with_concrete_implementation(self) -> None:
        """Test isinstance check works with concrete EditorPort implementations."""

        class ConcreteEditor(EditorPort):
            def open(self, path: str, *, cursor_hint: str | None = None) -> None:
                pass

        editor = ConcreteEditor()
        assert isinstance(editor, EditorPort)
        assert isinstance(editor, ABC)


class TestEditorPortExceptions:
    """Test exception handling requirements for EditorPort."""

    def test_editor_launch_error_import(self) -> None:
        """Test that EditorLaunchError can be imported and used."""
        # Should be able to instantiate EditorLaunchError
        error = EditorLaunchError('Editor failed to launch', 'vim', '/usr/bin/vim')
        assert isinstance(error, Exception)
        assert str(error) == "('Editor failed to launch', 'vim', '/usr/bin/vim')"

    def test_concrete_implementation_can_raise_documented_exceptions(self) -> None:
        """Test that concrete implementations can raise documented exceptions."""

        class ExceptionEditor(EditorPort):
            def open(self, path: str, *, cursor_hint: str | None = None) -> None:
                if not path:
                    raise FileNotFoundError('File not found', path)
                if path.startswith('fail'):
                    raise EditorLaunchError('Editor launch failed', path)

        editor = ExceptionEditor()

        # Test FileNotFoundError
        with pytest.raises(FileNotFoundError):
            editor.open('')

        # Test EditorLaunchError
        with pytest.raises(EditorLaunchError):
            editor.open('fail_this_path')

        # Test successful case
        editor.open('valid_path.txt')  # Should not raise
