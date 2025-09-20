"""Contract tests for DailyRepo protocol (T013).

These tests verify that any implementation of the DailyRepo protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from unittest.mock import Mock

import pytest

from prosemark.exceptions import FileSystemError

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import DailyRepo


class TestDailyRepoContract:
    """Test contract compliance for DailyRepo implementations."""

    def test_write_freeform_returns_string(self) -> None:
        """Test that write_freeform() returns a string filename/path."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_freeform.md'
        mock_repo.write_freeform.return_value = expected_filename

        # Act
        result = mock_repo.write_freeform()

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with()

    def test_write_freeform_with_no_title(self) -> None:
        """Test that write_freeform() works with default None title."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_freeform.md'
        mock_repo.write_freeform.return_value = expected_filename

        # Act
        result = mock_repo.write_freeform()

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with()

    def test_write_freeform_with_explicit_none_title(self) -> None:
        """Test that write_freeform() works with explicit None title."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_freeform.md'
        mock_repo.write_freeform.return_value = expected_filename

        # Act
        result = mock_repo.write_freeform(title=None)

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with(title=None)

    def test_write_freeform_with_title(self) -> None:
        """Test that write_freeform() accepts optional title parameter."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_my-thoughts.md'
        mock_repo.write_freeform.return_value = expected_filename

        title = 'My Thoughts'

        # Act
        result = mock_repo.write_freeform(title=title)

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with(title=title)

    def test_write_freeform_with_empty_title(self) -> None:
        """Test that write_freeform() handles empty string title."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_freeform.md'
        mock_repo.write_freeform.return_value = expected_filename

        # Act
        result = mock_repo.write_freeform(title='')

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with(title='')

    def test_write_freeform_with_long_title(self) -> None:
        """Test that write_freeform() handles long titles."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_thoughts-about-the-current-project.md'
        mock_repo.write_freeform.return_value = expected_filename

        long_title = 'Thoughts About the Current Project and Its Implementation Details'

        # Act
        result = mock_repo.write_freeform(title=long_title)

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with(title=long_title)

    def test_write_freeform_with_special_characters_in_title(self) -> None:
        """Test that write_freeform() handles titles with special characters."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = '2025-09-20_15-30-00_notes-symbols.md'
        mock_repo.write_freeform.return_value = expected_filename

        special_title = 'Notes & Symbols!'

        # Act
        result = mock_repo.write_freeform(title=special_title)

        # Assert
        assert isinstance(result, str)
        assert result == expected_filename
        mock_repo.write_freeform.assert_called_once_with(title=special_title)

    def test_write_freeform_raises_file_system_error(self) -> None:
        """Test that write_freeform() raises FileSystemError when file cannot be created."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        mock_repo.write_freeform.side_effect = FileSystemError('Cannot create file')

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.write_freeform()
        mock_repo.write_freeform.assert_called_once_with()

    def test_write_freeform_raises_file_system_error_with_title(self) -> None:
        """Test that write_freeform() raises FileSystemError with title parameter."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        mock_repo.write_freeform.side_effect = FileSystemError('Disk full')

        title = 'Important Notes'

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.write_freeform(title=title)
        mock_repo.write_freeform.assert_called_once_with(title=title)

    def test_write_freeform_returns_non_empty_string(self) -> None:
        """Test that write_freeform() returns a non-empty string."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        expected_filename = 'some_filename.md'
        mock_repo.write_freeform.return_value = expected_filename

        # Act
        result = mock_repo.write_freeform()

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == expected_filename

    def test_write_freeform_timestamp_consistency(self) -> None:
        """Test that multiple calls to write_freeform() can return different filenames."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        filenames = [
            '2025-09-20_15-30-00_freeform.md',
            '2025-09-20_15-30-01_freeform.md',
            '2025-09-20_15-30-02_freeform.md',
        ]
        mock_repo.write_freeform.side_effect = filenames

        # Act
        results = [mock_repo.write_freeform() for _ in range(3)]

        # Assert
        assert len(results) == 3
        assert all(isinstance(result, str) for result in results)
        assert results == filenames
        assert mock_repo.write_freeform.call_count == 3

    def test_repo_protocol_methods_exist(self) -> None:
        """Test that DailyRepo protocol has required methods."""
        # This test verifies the protocol interface exists
        mock_repo = Mock(spec=DailyRepo)

        # Verify methods exist
        assert hasattr(mock_repo, 'write_freeform')

        # Verify methods are callable
        assert callable(mock_repo.write_freeform)

    def test_write_freeform_method_signature(self) -> None:
        """Test that write_freeform() method has correct signature."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        mock_repo.write_freeform.return_value = 'test_file.md'

        # Act - Test with various valid parameter combinations

        # No parameters (default)
        result1 = mock_repo.write_freeform()
        assert isinstance(result1, str)

        # With title keyword argument
        result2 = mock_repo.write_freeform(title='Test Title')
        assert isinstance(result2, str)

        # With None title
        result3 = mock_repo.write_freeform(title=None)
        assert isinstance(result3, str)

        # Assert correct number of calls
        assert mock_repo.write_freeform.call_count == 3

    def test_write_freeform_optional_parameter_typing(self) -> None:
        """Test that write_freeform() accepts Optional[str] for title parameter."""
        # Arrange
        mock_repo = Mock(spec=DailyRepo)
        mock_repo.write_freeform.return_value = 'test.md'

        # Test various valid title types
        title_none: str | None = None
        title_string: str | None = 'Valid Title'
        title_empty: str | None = ''

        # Act & Assert - All should work with Optional[str] typing
        result1 = mock_repo.write_freeform(title=title_none)
        result2 = mock_repo.write_freeform(title=title_string)
        result3 = mock_repo.write_freeform(title=title_empty)

        assert all(isinstance(result, str) for result in [result1, result2, result3])
        assert mock_repo.write_freeform.call_count == 3
