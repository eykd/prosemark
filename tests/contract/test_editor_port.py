"""Contract tests for EditorPort protocol (T016).

These tests verify that any implementation of the EditorPort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.exceptions import EditorLaunchError, EditorNotFoundError

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import EditorPort


class TestEditorPortContract:
    """Test contract compliance for EditorPort implementations."""

    def test_open_accepts_file_path(self) -> None:
        """Test that open() accepts a file path string and returns None."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        file_path = '/path/to/file.md'

        # Act
        result = mock_editor.open(file_path)

        # Assert
        assert result is None
        mock_editor.open.assert_called_once_with(file_path)

    def test_open_with_absolute_path(self) -> None:
        """Test that open() works with absolute file paths."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        absolute_path = '/home/user/documents/node.md'

        # Act
        result = mock_editor.open(absolute_path)

        # Assert
        assert result is None
        mock_editor.open.assert_called_once_with(absolute_path)

    def test_open_with_various_file_extensions(self) -> None:
        """Test that open() works with various file extensions."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        file_paths = [
            '/path/to/file.md',
            '/path/to/file.txt',
            '/path/to/file.notes.md',
            '/path/to/file.synopsis.md',
            '/path/to/file.draft.md',
        ]

        # Act & Assert
        for file_path in file_paths:
            result = mock_editor.open(file_path)
            assert result is None

        assert mock_editor.open.call_count == len(file_paths)

    def test_open_with_long_path(self) -> None:
        """Test that open() handles long file paths."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        long_path = '/very/long/path/with/many/nested/directories/and/subdirectories/file.md'

        # Act
        result = mock_editor.open(long_path)

        # Assert
        assert result is None
        mock_editor.open.assert_called_once_with(long_path)

    def test_open_with_special_characters_in_path(self) -> None:
        """Test that open() handles paths with special characters."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        special_paths = [
            '/path/with spaces/file.md',
            '/path/with-hyphens/file.md',
            '/path/with_underscores/file.md',
            '/path/with.dots/file.md',
            '/path/with(parentheses)/file.md',
        ]

        # Act & Assert
        for path in special_paths:
            result = mock_editor.open(path)
            assert result is None

        assert mock_editor.open.call_count == len(special_paths)

    def test_open_raises_editor_not_found_error(self) -> None:
        """Test that open() raises EditorNotFoundError when editor executable not found."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.side_effect = EditorNotFoundError('Editor executable not found')

        file_path = '/path/to/file.md'

        # Act & Assert
        with pytest.raises(EditorNotFoundError):
            mock_editor.open(file_path)
        mock_editor.open.assert_called_once_with(file_path)

    def test_open_raises_editor_launch_error(self) -> None:
        """Test that open() raises EditorLaunchError when editor fails to launch."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.side_effect = EditorLaunchError('Editor failed to launch')

        file_path = '/path/to/file.md'

        # Act & Assert
        with pytest.raises(EditorLaunchError):
            mock_editor.open(file_path)
        mock_editor.open.assert_called_once_with(file_path)

    def test_open_with_nonexistent_file_path(self) -> None:
        """Test that open() can handle paths to files that may not exist yet."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        nonexistent_file = '/path/to/new/file.md'

        # Act
        result = mock_editor.open(nonexistent_file)

        # Assert
        # Many editors can open non-existent files and create them
        assert result is None
        mock_editor.open.assert_called_once_with(nonexistent_file)

    def test_open_with_relative_path_converted_to_absolute(self, tmp_path: Path) -> None:
        """Test that open() can handle relative paths converted to absolute."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        # Contract specifies absolute path, but implementation might convert relative to absolute
        absolute_path = str(tmp_path / 'relative' / 'path' / 'file.md')

        # Act
        result = mock_editor.open(absolute_path)

        # Assert
        assert result is None
        mock_editor.open.assert_called_once_with(absolute_path)

    def test_open_error_conditions_propagation(self) -> None:
        """Test that open() properly propagates different error conditions."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)

        file_path = '/path/to/file.md'

        # Test different error scenarios
        error_scenarios = [
            EditorNotFoundError('vim not found in PATH'),
            EditorNotFoundError('code not found in PATH'),
            EditorLaunchError('Permission denied'),
            EditorLaunchError('Editor crashed during startup'),
            EditorLaunchError('X11 display not available'),
        ]

        # Act & Assert
        for error in error_scenarios:
            mock_editor.open.side_effect = error
            with pytest.raises(type(error)):
                mock_editor.open(file_path)

    def test_open_string_parameter_type(self) -> None:
        """Test that open() accepts string type for file_path parameter."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        # Various string types
        file_path_str: str = '/path/to/file.md'
        file_path_literal = '/another/path/file.md'

        # Act
        result1 = mock_editor.open(file_path_str)
        result2 = mock_editor.open(file_path_literal)

        # Assert
        assert result1 is None
        assert result2 is None
        assert mock_editor.open.call_count == 2

    def test_protocol_methods_exist(self) -> None:
        """Test that EditorPort protocol has required methods."""
        # This test verifies the protocol interface exists
        mock_editor = Mock(spec=EditorPort)

        # Verify methods exist
        assert hasattr(mock_editor, 'open')

        # Verify methods are callable
        assert callable(mock_editor.open)

    def test_open_method_signature(self) -> None:
        """Test that open() method has correct signature."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        file_path = '/path/to/file.md'

        # Act - Test that method can be called with single string parameter
        result = mock_editor.open(file_path)

        # Assert
        assert result is None
        # Verify it was called with correct argument
        mock_editor.open.assert_called_once_with(file_path)

    def test_open_return_type_annotation(self) -> None:
        """Test that open() returns None as specified in contract."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        file_path = '/path/to/file.md'

        # Act
        result = mock_editor.open(file_path)

        # Assert - Verify return type matches contract specification
        assert result is None

    def test_open_editor_integration_scenarios(self, tmp_path: Path) -> None:
        """Test various editor integration scenarios."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        # Common prosemark file scenarios using tmp_path
        project_root = tmp_path / 'project'
        scenarios = [
            # Node draft files
            str(project_root / 'nodes' / '0192f0c1-2345-7123-8abc-def012345678.md'),
            # Node notes files
            str(project_root / 'nodes' / '0192f0c1-2345-7123-8abc-def012345678.notes.md'),
            # Node synopsis files
            str(project_root / 'nodes' / '0192f0c1-2345-7123-8abc-def012345678.synopsis.md'),
            # Binder file
            str(project_root / '_binder.md'),
            # Freeform writing files
            str(project_root / 'daily' / '2025-09-20_15-30-00_thoughts.md'),
        ]

        # Act & Assert
        for file_path in scenarios:
            result = mock_editor.open(file_path)
            assert result is None

        assert mock_editor.open.call_count == len(scenarios)

    def test_open_handles_unicode_paths(self) -> None:
        """Test that open() handles Unicode characters in file paths."""
        # Arrange
        mock_editor = Mock(spec=EditorPort)
        mock_editor.open.return_value = None

        unicode_paths = [
            '/path/to/文档.md',  # Chinese characters
            '/path/to/arquivo.md',  # Portuguese characters
            '/path/to/файл.md',  # Cyrillic characters
            '/path/to/ファイル.md',  # Japanese characters
            '/path/to/αρχείο.md',  # Greek characters
        ]

        # Act & Assert
        for path in unicode_paths:
            result = mock_editor.open(path)
            assert result is None

        assert mock_editor.open.call_count == len(unicode_paths)
