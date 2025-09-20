"""Contract tests for NodeRepo protocol (T012).

These tests verify that any implementation of the NodeRepo protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from prosemark.domain.models import NodeId
from prosemark.exceptions import (
    EditorError,
    FileSystemError,
    FrontmatterFormatError,
    InvalidPartError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
)

# These imports will fail initially - this is expected for contract tests
from prosemark.ports import NodeRepo


class TestNodeRepoContract:
    """Test contract compliance for NodeRepo implementations."""

    def test_create_with_all_parameters(self) -> None:
        """Test that create() accepts all required parameters."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.create.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        title = 'Test Node'
        synopsis = 'A test node for testing'

        # Act
        result = mock_repo.create(node_id, title, synopsis)

        # Assert
        assert result is None
        mock_repo.create.assert_called_once_with(node_id, title, synopsis)

    def test_create_with_optional_parameters_none(self) -> None:
        """Test that create() handles None for optional parameters."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.create.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act
        result = mock_repo.create(node_id, None, None)

        # Assert
        assert result is None
        mock_repo.create.assert_called_once_with(node_id, None, None)

    def test_create_raises_node_already_exists_error(self) -> None:
        """Test that create() raises NodeAlreadyExistsError when node files already exist."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.create.side_effect = NodeAlreadyExistsError('Node files already exist')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(NodeAlreadyExistsError):
            mock_repo.create(node_id, 'Title', 'Synopsis')
        mock_repo.create.assert_called_once_with(node_id, 'Title', 'Synopsis')

    def test_create_raises_file_system_error(self) -> None:
        """Test that create() raises FileSystemError when files cannot be created."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.create.side_effect = FileSystemError('Cannot create files')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.create(node_id, 'Title', 'Synopsis')

    def test_read_frontmatter_returns_dict(self) -> None:
        """Test that read_frontmatter() returns a dictionary."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        expected_frontmatter = {'title': 'Test Node', 'synopsis': 'A test node', 'created': '2025-09-20T15:30:00Z'}
        mock_repo.read_frontmatter.return_value = expected_frontmatter

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act
        result = mock_repo.read_frontmatter(node_id)

        # Assert
        assert isinstance(result, dict)
        assert result == expected_frontmatter
        mock_repo.read_frontmatter.assert_called_once_with(node_id)

    def test_read_frontmatter_raises_node_not_found_error(self) -> None:
        """Test that read_frontmatter() raises NodeNotFoundError when node doesn't exist."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.read_frontmatter.side_effect = NodeNotFoundError("Node files don't exist")

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(NodeNotFoundError):
            mock_repo.read_frontmatter(node_id)

    def test_read_frontmatter_raises_frontmatter_format_error(self) -> None:
        """Test that read_frontmatter() raises FrontmatterFormatError when YAML is malformed."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.read_frontmatter.side_effect = FrontmatterFormatError('Invalid YAML format')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(FrontmatterFormatError):
            mock_repo.read_frontmatter(node_id)

    def test_write_frontmatter_accepts_dict(self) -> None:
        """Test that write_frontmatter() accepts a dictionary and returns None."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.write_frontmatter.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        frontmatter = {'title': 'Updated Title', 'synopsis': 'Updated synopsis', 'modified': '2025-09-20T16:00:00Z'}

        # Act
        result = mock_repo.write_frontmatter(node_id, frontmatter)

        # Assert
        assert result is None
        mock_repo.write_frontmatter.assert_called_once_with(node_id, frontmatter)

    def test_write_frontmatter_raises_node_not_found_error(self) -> None:
        """Test that write_frontmatter() raises NodeNotFoundError when node doesn't exist."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.write_frontmatter.side_effect = NodeNotFoundError("Node files don't exist")

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        frontmatter = {'title': 'Test'}

        # Act & Assert
        with pytest.raises(NodeNotFoundError):
            mock_repo.write_frontmatter(node_id, frontmatter)

    def test_write_frontmatter_raises_file_system_error(self) -> None:
        """Test that write_frontmatter() raises FileSystemError when files cannot be written."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.write_frontmatter.side_effect = FileSystemError('Cannot write files')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        frontmatter = {'title': 'Test'}

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.write_frontmatter(node_id, frontmatter)

    def test_open_in_editor_with_valid_parts(self) -> None:
        """Test that open_in_editor() accepts valid part values."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.open_in_editor.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        valid_parts = ['draft', 'notes', 'synopsis']

        # Act & Assert
        for part in valid_parts:
            result = mock_repo.open_in_editor(node_id, part)
            assert result is None

        assert mock_repo.open_in_editor.call_count == len(valid_parts)

    def test_open_in_editor_raises_node_not_found_error(self) -> None:
        """Test that open_in_editor() raises NodeNotFoundError when node doesn't exist."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.open_in_editor.side_effect = NodeNotFoundError("Node files don't exist")

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(NodeNotFoundError):
            mock_repo.open_in_editor(node_id, 'draft')

    def test_open_in_editor_raises_invalid_part_error(self) -> None:
        """Test that open_in_editor() raises InvalidPartError for unsupported parts."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.open_in_editor.side_effect = InvalidPartError('Invalid part')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(InvalidPartError):
            mock_repo.open_in_editor(node_id, 'invalid_part')

    def test_open_in_editor_raises_editor_error(self) -> None:
        """Test that open_in_editor() raises EditorError when editor cannot be launched."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.open_in_editor.side_effect = EditorError('Editor launch failed')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(EditorError):
            mock_repo.open_in_editor(node_id, 'draft')

    def test_delete_with_default_parameter(self) -> None:
        """Test that delete() works with default delete_files parameter."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.delete.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act
        result = mock_repo.delete(node_id)

        # Assert
        assert result is None
        mock_repo.delete.assert_called_once_with(node_id)

    def test_delete_with_explicit_delete_files_false(self) -> None:
        """Test that delete() accepts delete_files=False."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.delete.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act
        result = mock_repo.delete(node_id, delete_files=False)

        # Assert
        assert result is None
        mock_repo.delete.assert_called_once_with(node_id, delete_files=False)

    def test_delete_with_explicit_delete_files_true(self) -> None:
        """Test that delete() accepts delete_files=True."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.delete.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act
        result = mock_repo.delete(node_id, delete_files=True)

        # Assert
        assert result is None
        mock_repo.delete.assert_called_once_with(node_id, delete_files=True)

    def test_delete_raises_file_system_error(self) -> None:
        """Test that delete() raises FileSystemError when files cannot be deleted."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.delete.side_effect = FileSystemError('Cannot delete files')

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Act & Assert
        with pytest.raises(FileSystemError):
            mock_repo.delete(node_id, delete_files=True)

    def test_repo_protocol_methods_exist(self) -> None:
        """Test that NodeRepo protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_repo = Mock(spec=NodeRepo)

        # Verify methods exist
        assert hasattr(mock_repo, 'create')
        assert hasattr(mock_repo, 'read_frontmatter')
        assert hasattr(mock_repo, 'write_frontmatter')
        assert hasattr(mock_repo, 'open_in_editor')
        assert hasattr(mock_repo, 'delete')

        # Verify methods are callable
        assert callable(mock_repo.create)
        assert callable(mock_repo.read_frontmatter)
        assert callable(mock_repo.write_frontmatter)
        assert callable(mock_repo.open_in_editor)
        assert callable(mock_repo.delete)

    def test_method_signatures_type_hints(self) -> None:
        """Test that methods accept the correct parameter types."""
        # Arrange
        mock_repo = Mock(spec=NodeRepo)
        mock_repo.create.return_value = None
        mock_repo.read_frontmatter.return_value = {}
        mock_repo.write_frontmatter.return_value = None
        mock_repo.open_in_editor.return_value = None
        mock_repo.delete.return_value = None

        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        title: str | None = 'Test Title'
        synopsis: str | None = 'Test Synopsis'
        frontmatter: dict[str, Any] = {'title': 'Test'}
        part = 'draft'
        delete_files = True

        # Act - These should all work with correct types
        mock_repo.create(node_id, title, synopsis)
        mock_repo.read_frontmatter(node_id)
        mock_repo.write_frontmatter(node_id, frontmatter)
        mock_repo.open_in_editor(node_id, part)
        mock_repo.delete(node_id, delete_files)

        # Assert - Verify calls were made
        assert mock_repo.create.call_count == 1
        assert mock_repo.read_frontmatter.call_count == 1
        assert mock_repo.write_frontmatter.call_count == 1
        assert mock_repo.open_in_editor.call_count == 1
        assert mock_repo.delete.call_count == 1
