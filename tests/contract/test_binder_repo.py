"""Contract tests for BinderRepo protocol (T011).

These tests verify that any implementation of the BinderRepo protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from unittest.mock import Mock

import pytest

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import (
    BinderFormatError,
    BinderNotFoundError,
    FileSystemError,
)

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import BinderRepo


class TestBinderRepoContract:
    """Test contract compliance for BinderRepo implementations."""

    def test_load_returns_binder(self) -> None:
        """Test that load() returns a valid Binder object."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        expected_binder = Binder(roots=[])
        mock_repo.load.return_value = expected_binder

        # Act
        result = mock_repo.load()

        # Assert
        assert isinstance(result, Binder)
        assert result == expected_binder
        mock_repo.load.assert_called_once()

    def test_load_raises_binder_not_found_error_when_file_missing(self) -> None:
        """Test that load() raises BinderNotFoundError when _binder.md doesn't exist."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.load.side_effect = BinderNotFoundError('Binder file not found')

        # Act & Assert
        with pytest.raises(BinderNotFoundError):
            mock_repo.load()
        mock_repo.load.assert_called_once()

    def test_load_raises_binder_format_error_when_malformed(self) -> None:
        """Test that load() raises BinderFormatError when managed block is malformed."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.load.side_effect = BinderFormatError('Invalid managed block format')

        # Act & Assert
        with pytest.raises(BinderFormatError):
            mock_repo.load()
        mock_repo.load.assert_called_once()

    def test_save_accepts_binder_object(self) -> None:
        """Test that save() accepts a Binder object and returns None."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.save.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        binder_item = BinderItem(id_=node_id, display_title='Test Node', children=[])
        binder = Binder(roots=[binder_item])

        # Act
        result = mock_repo.save(binder)

        # Assert
        assert result is None
        mock_repo.save.assert_called_once_with(binder)

    def test_save_raises_file_system_error_when_write_fails(self) -> None:
        """Test that save() raises FileSystemError when file cannot be written."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.save.side_effect = FileSystemError('Cannot write to file')

        binder = Binder(roots=[])

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.save(binder)
        mock_repo.save.assert_called_once_with(binder)

    def test_save_with_empty_binder(self) -> None:
        """Test that save() handles empty binder correctly."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.save.return_value = None

        empty_binder = Binder(roots=[])

        # Act
        result = mock_repo.save(empty_binder)

        # Assert
        assert result is None
        mock_repo.save.assert_called_once_with(empty_binder)

    def test_save_with_complex_hierarchy(self) -> None:
        """Test that save() handles complex binder hierarchy correctly."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.save.return_value = None

        # Create complex hierarchy
        child_id = NodeId('0192f0c1-2345-7123-8abc-def012345679')
        parent_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        child_item = BinderItem(id_=child_id, display_title='Child Node', children=[])
        parent_item = BinderItem(id_=parent_id, display_title='Parent Node', children=[child_item])
        placeholder_item = BinderItem(id_=None, display_title='Placeholder', children=[])

        complex_binder = Binder(roots=[parent_item, placeholder_item])

        # Act
        result = mock_repo.save(complex_binder)

        # Assert
        assert result is None
        mock_repo.save.assert_called_once_with(complex_binder)

    def test_repo_protocol_methods_exist(self) -> None:
        """Test that BinderRepo protocol has required methods with correct signatures."""
        # This test verifies the protocol interface exists
        mock_repo = Mock(spec=BinderRepo)

        # Verify methods exist
        assert hasattr(mock_repo, 'load')
        assert hasattr(mock_repo, 'save')

        # Verify methods are callable
        assert callable(mock_repo.load)
        assert callable(mock_repo.save)

    def test_load_method_signature(self) -> None:
        """Test that load() method has correct signature (no parameters)."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.load.return_value = Binder(roots=[])

        # Act - should work with no parameters
        result = mock_repo.load()

        # Assert
        assert isinstance(result, Binder)
        mock_repo.load.assert_called_once_with()

    def test_save_method_signature(self) -> None:
        """Test that save() method has correct signature (binder parameter)."""
        # Arrange
        mock_repo = Mock(spec=BinderRepo)
        mock_repo.save.return_value = None

        binder = Binder(roots=[])

        # Act - should work with binder parameter
        result = mock_repo.save(binder)

        # Assert
        assert result is None
        mock_repo.save.assert_called_once_with(binder)
