"""Tests for Node Service adapter implementation.

These tests cover the NodeServiceAdapter class which integrates
freewriting functionality with the existing prosemark node system.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.domain.models import NodeId
from prosemark.freewriting.adapters.node_service_adapter import NodeServiceAdapter
from prosemark.freewriting.domain.exceptions import FileSystemError, NodeError, ValidationError
from prosemark.ports.binder_repo import BinderRepo
from prosemark.ports.clock import Clock
from prosemark.ports.node_repo import NodeRepo


class TestNodeServiceAdapter:
    """Test the Node Service adapter implementation."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initializes with required dependencies."""
        # Arrange
        project_path = Path('/test/project')
        mock_node_repo = Mock(spec=NodeRepo)
        mock_binder_repo = Mock(spec=BinderRepo)
        mock_clock = Mock(spec=Clock)

        # Act
        adapter = NodeServiceAdapter(project_path, mock_node_repo, mock_binder_repo, mock_clock)

        # Assert
        assert adapter.project_path == project_path
        assert adapter.node_repo == mock_node_repo
        assert adapter.binder_repo == mock_binder_repo
        assert adapter.clock == mock_clock
        assert isinstance(adapter.frontmatter_codec, FrontmatterCodec)

    def test_validate_node_uuid_valid(self) -> None:
        """Test validate_node_uuid with valid UUID."""
        # Arrange
        valid_uuid = str(NodeId.generate())

        # Act
        result = NodeServiceAdapter.validate_node_uuid(valid_uuid)

        # Assert
        assert result is True

    def test_validate_node_uuid_invalid(self) -> None:
        """Test validate_node_uuid with invalid UUID."""
        # Act & Assert
        assert NodeServiceAdapter.validate_node_uuid('invalid-uuid') is False
        assert NodeServiceAdapter.validate_node_uuid('') is False
        assert NodeServiceAdapter.validate_node_uuid(None) is False  # type: ignore[arg-type]

    def test_node_exists_valid_uuid_existing_file(self) -> None:
        """Test node_exists returns True for existing file with valid UUID."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            test_file = project_path / f'{test_uuid}.md'
            test_file.write_text('# Test Node')

            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            # Act
            result = adapter.node_exists(test_uuid)

            # Assert
            assert result is True

    def test_node_exists_valid_uuid_nonexistent_file(self) -> None:
        """Test node_exists returns False for non-existent file."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            # Act
            result = adapter.node_exists(test_uuid)

            # Assert
            assert result is False

    def test_node_exists_invalid_uuid(self) -> None:
        """Test node_exists returns False for invalid UUID."""
        # Arrange
        project_path = Path('/test')
        adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

        # Act
        result = adapter.node_exists('invalid-uuid')

        # Assert
        assert result is False

    def test_node_exists_os_error(self) -> None:
        """Test node_exists handles OS errors gracefully."""
        # Arrange
        project_path = Path('/test')
        adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())
        test_uuid = str(NodeId.generate())

        with patch.object(Path, 'exists', side_effect=OSError('Permission denied')):
            # Act
            result = adapter.node_exists(test_uuid)

            # Assert
            assert result is False

    def test_create_node_success(self) -> None:
        """Test successful node creation."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())

            mock_node_repo = Mock(spec=NodeRepo)
            mock_binder_repo = Mock(spec=BinderRepo)
            mock_clock = Mock(spec=Clock)

            adapter = NodeServiceAdapter(project_path, mock_node_repo, mock_binder_repo, mock_clock)

            with patch.object(adapter, 'add_to_binder') as mock_add_to_binder:
                # Act
                result = adapter.create_node(test_uuid, 'Test Title')

                # Assert
                expected_path = str(project_path / f'{test_uuid}.md')
                assert result == expected_path
                mock_node_repo.create.assert_called_once_with(NodeId(test_uuid), 'Test Title', None)
                mock_add_to_binder.assert_called_once_with(test_uuid, 'Test Title')

    def test_create_node_invalid_uuid(self) -> None:
        """Test create_node raises ValidationError for invalid UUID."""
        # Arrange
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        # Act & Assert
        with pytest.raises(ValidationError, match='must be valid UUID format'):
            adapter.create_node('invalid-uuid', 'Test Title')

    def test_create_node_already_exists(self) -> None:
        """Test create_node handles existing node error."""
        # Arrange
        mock_node_repo = Mock(spec=NodeRepo)
        mock_node_repo.create.side_effect = Exception('Node already exists')

        adapter = NodeServiceAdapter(Path('/test'), mock_node_repo, Mock(), Mock())
        test_uuid = str(NodeId.generate())

        # Act & Assert
        with pytest.raises(NodeError, match='already exists'):
            adapter.create_node(test_uuid)

    def test_create_node_filesystem_error(self) -> None:
        """Test create_node handles filesystem errors."""
        # Arrange
        mock_node_repo = Mock(spec=NodeRepo)
        mock_node_repo.create.side_effect = OSError('Disk full')

        adapter = NodeServiceAdapter(Path('/test'), mock_node_repo, Mock(), Mock())
        test_uuid = str(NodeId.generate())

        # Act & Assert
        with pytest.raises(FileSystemError, match='File system operation failed'):
            adapter.create_node(test_uuid)

    def test_create_node_binder_error_suppressed(self) -> None:
        """Test create_node continues if binder addition fails."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())

            mock_node_repo = Mock(spec=NodeRepo)
            adapter = NodeServiceAdapter(project_path, mock_node_repo, Mock(), Mock())

            with patch.object(adapter, 'add_to_binder', side_effect=NodeError(test_uuid, 'add', 'Binder failed')):
                # Act - should not raise despite binder error
                result = adapter.create_node(test_uuid, 'Test Title')

                # Assert
                expected_path = str(project_path / f'{test_uuid}.md')
                assert result == expected_path
                mock_node_repo.create.assert_called_once()

    def test_create_node_validation_error_reraise(self) -> None:
        """Test create_node re-raises ValidationError from node_repo."""
        # Arrange
        mock_node_repo = Mock(spec=NodeRepo)
        mock_node_repo.create.side_effect = ValidationError('node', 'invalid', 'Node validation failed')

        adapter = NodeServiceAdapter(Path('/test'), mock_node_repo, Mock(), Mock())
        test_uuid = str(NodeId.generate())

        # Act & Assert - ValidationError should be re-raised (line 116)
        with pytest.raises(ValidationError, match='Node validation failed'):
            adapter.create_node(test_uuid)

    def test_append_to_node_success(self) -> None:
        """Test successful content appending to node."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'

            # Create initial node content
            initial_content = """---
title: Test Node
created: "2023-01-01T10:00:00Z"
updated: "2023-01-01T10:00:00Z"
---

# Test Node

Initial content here."""
            node_file.write_text(initial_content)

            mock_clock = Mock(spec=Clock)
            mock_clock.now_iso.return_value = '2023-12-01T12:00:00Z'

            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), mock_clock)

            content = ['First line of freewriting', 'Second line of content']
            session_metadata = {'timestamp': '2023-12-01T12:00:00Z', 'word_count': '15'}

            # Act
            adapter.append_to_node(test_uuid, content, session_metadata)

            # Assert
            updated_content = node_file.read_text()
            assert 'Freewrite Session - 2023-12-01T12:00:00Z' in updated_content
            assert 'First line of freewriting' in updated_content
            assert 'Second line of content' in updated_content
            assert 'Session completed: 15 words' in updated_content
            assert 'updated:' in updated_content
            assert '2023-12-01T12:00:00Z' in updated_content

    def test_append_to_node_invalid_uuid(self) -> None:
        """Test append_to_node raises ValidationError for invalid UUID."""
        # Arrange
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        # Act & Assert
        with pytest.raises(ValidationError, match='must be valid UUID format'):
            adapter.append_to_node('invalid-uuid', [], {})

    def test_append_to_node_nonexistent_node(self) -> None:
        """Test append_to_node raises ValidationError for non-existent node."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            # Act & Assert
            with pytest.raises(ValidationError, match='node must exist'):
                adapter.append_to_node(test_uuid, [], {})

    def test_append_to_node_read_error(self) -> None:
        """Test append_to_node handles read errors."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'
            node_file.write_text('# Test')  # Create the file so it exists

            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            with (
                patch.object(Path, 'read_text', side_effect=OSError('Read failed')),
                pytest.raises(FileSystemError, match='File system operation failed'),
            ):
                adapter.append_to_node(test_uuid, [], {})

    def test_append_to_node_write_error(self) -> None:
        """Test append_to_node handles write errors."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'
            node_file.write_text('---\ntitle: Test\n---\n\n# Test')

            mock_clock = Mock(spec=Clock)
            mock_clock.now_iso.return_value = '2023-12-01T12:00:00Z'
            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), mock_clock)

            with (
                patch.object(Path, 'write_text', side_effect=OSError('Write failed')),
                pytest.raises(FileSystemError, match='File system operation failed'),
            ):
                adapter.append_to_node(test_uuid, ['content'], {})

    def test_append_to_node_with_default_timestamp(self) -> None:
        """Test append_to_node uses clock default when timestamp not provided."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'
            node_file.write_text('---\ntitle: Test\n---\n\n# Test')

            mock_clock = Mock(spec=Clock)
            mock_clock.now_iso.return_value = '2023-12-01T15:30:00Z'
            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), mock_clock)

            # Act
            adapter.append_to_node(test_uuid, ['test content'], {})  # No timestamp in metadata

            # Assert
            updated_content = node_file.read_text()
            assert '2023-12-01T15:30:00Z' in updated_content
            # Clock should be called twice - once for session header, once for frontmatter
            assert mock_clock.now_iso.call_count == 2

    def test_append_to_node_unexpected_error(self) -> None:
        """Test append_to_node handles unexpected errors."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'
            node_file.write_text('---\ntitle: Test\n---\n\n# Test')  # Create valid file

            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            # Mock an unexpected error in the main try block (not caught by specific handlers)
            with (
                patch.object(adapter.clock, 'now_iso', side_effect=RuntimeError('Unexpected error')),
                pytest.raises(NodeError, match='Failed to append to node'),
            ):
                adapter.append_to_node(test_uuid, [], {})

    def test_get_node_path_valid_uuid(self) -> None:
        """Test get_node_path returns correct path for valid UUID."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), Mock())

            # Act
            result = adapter.get_node_path(test_uuid)

            # Assert
            expected_path = str((project_path / f'{test_uuid}.md').resolve())
            assert result == expected_path

    def test_get_node_path_invalid_uuid(self) -> None:
        """Test get_node_path raises ValidationError for invalid UUID."""
        # Arrange
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        # Act & Assert
        with pytest.raises(ValidationError, match='must be valid UUID format'):
            adapter.get_node_path('invalid-uuid')

    def test_add_to_binder_node_already_exists(self) -> None:
        """Test add_to_binder when node already exists in binder."""
        # Arrange
        test_uuid = str(NodeId.generate())

        mock_binder = Mock()
        mock_binder.get_all_node_ids.return_value = [NodeId(test_uuid)]

        mock_binder_repo = Mock(spec=BinderRepo)
        mock_binder_repo.load.return_value = mock_binder

        adapter = NodeServiceAdapter(Path('/test'), Mock(), mock_binder_repo, Mock())

        # Act
        adapter.add_to_binder(test_uuid, 'Test Title')

        # Assert - should return early without error
        mock_binder_repo.load.assert_called_once()

    def test_add_to_binder_new_node(self) -> None:
        """Test add_to_binder with new node."""
        # Arrange
        test_uuid = str(NodeId.generate())
        different_uuid = str(NodeId.generate())

        mock_binder = Mock()
        mock_binder.get_all_node_ids.return_value = [NodeId(different_uuid)]

        mock_binder_repo = Mock(spec=BinderRepo)
        mock_binder_repo.load.return_value = mock_binder

        adapter = NodeServiceAdapter(Path('/test'), Mock(), mock_binder_repo, Mock())

        # Act - should not raise error (passes with current implementation)
        adapter.add_to_binder(test_uuid, 'Test Title')

        # Assert
        mock_binder_repo.load.assert_called_once()

    def test_add_to_binder_load_error_suppressed(self) -> None:
        """Test add_to_binder suppresses binder load errors."""
        # Arrange
        test_uuid = str(NodeId.generate())

        mock_binder_repo = Mock(spec=BinderRepo)
        mock_binder_repo.load.side_effect = Exception('Binder load failed')

        adapter = NodeServiceAdapter(Path('/test'), Mock(), mock_binder_repo, Mock())

        # Act - should not raise error due to suppress for the binder load
        adapter.add_to_binder(test_uuid, 'Test Title')

    def test_add_to_binder_validation_error_propagated(self) -> None:
        """Test add_to_binder propagates ValidationError."""
        # Arrange
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        # Act & Assert - invalid UUID should cause NodeError, not ValidationError
        # because the NodeId creation fails and gets caught by the except block
        with pytest.raises(NodeError, match='Failed to add node to binder'):
            adapter.add_to_binder('invalid-uuid', 'Test Title')

    def test_add_to_binder_unexpected_error(self) -> None:
        """Test add_to_binder handles unexpected errors."""
        # Arrange
        test_uuid = str(NodeId.generate())
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        with (
            patch.object(NodeId, '__init__', side_effect=RuntimeError('Unexpected error')),
            pytest.raises(NodeError, match='Failed to add node to binder'),
        ):
            adapter.add_to_binder(test_uuid, 'Test Title')


class TestNodeServiceAdapterIntegration:
    """Integration tests for Node Service adapter."""

    def test_complete_node_workflow(self) -> None:
        """Test complete workflow from creation to content appending."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())

            mock_node_repo = Mock(spec=NodeRepo)
            mock_binder_repo = Mock(spec=BinderRepo)
            mock_clock = Mock(spec=Clock)
            mock_clock.now_iso.return_value = '2023-12-01T12:00:00Z'

            adapter = NodeServiceAdapter(project_path, mock_node_repo, mock_binder_repo, mock_clock)

            # Mock binder operations to avoid errors
            with patch.object(adapter, 'add_to_binder'):
                # Act - Create node
                created_path = adapter.create_node(test_uuid, 'Integration Test Node')

                # Manually create the file since we're mocking the repo
                node_file = project_path / f'{test_uuid}.md'
                initial_content = """---
title: Integration Test Node
created: "2023-12-01T10:00:00Z"
updated: "2023-12-01T10:00:00Z"
---

# Integration Test Node

Initial content."""
                node_file.write_text(initial_content)

                # Verify node exists
                assert adapter.node_exists(test_uuid) is True

                # Get node path
                node_path = adapter.get_node_path(test_uuid)
                assert node_path == str(node_file.resolve())

                # Append content
                content = ['This is freewriting content', 'Multiple lines of text']
                metadata = {'timestamp': '2023-12-01T14:00:00Z', 'word_count': '7'}
                adapter.append_to_node(test_uuid, content, metadata)

                # Assert
                assert created_path == str(node_file)
                updated_content = node_file.read_text()
                assert 'This is freewriting content' in updated_content
                assert 'Multiple lines of text' in updated_content
                assert 'Freewrite Session - 2023-12-01T14:00:00Z' in updated_content
                assert 'Session completed: 7 words' in updated_content

    def test_error_recovery_workflow(self) -> None:
        """Test error handling in various workflow scenarios."""
        # Arrange
        adapter = NodeServiceAdapter(Path('/test'), Mock(), Mock(), Mock())

        # Test invalid UUID in all methods
        invalid_uuid = 'not-a-valid-uuid-format-at-all'

        # Act & Assert
        assert adapter.node_exists(invalid_uuid) is False

        with pytest.raises(ValidationError):
            adapter.create_node(invalid_uuid)

        with pytest.raises(ValidationError):
            adapter.append_to_node(invalid_uuid, [], {})

        with pytest.raises(ValidationError):
            adapter.get_node_path(invalid_uuid)

        # add_to_binder raises NodeError, not ValidationError due to NodeId exception handling
        with pytest.raises(NodeError, match='Node operation failed'):
            adapter.add_to_binder(invalid_uuid)

    def test_frontmatter_codec_integration(self) -> None:
        """Test integration with FrontmatterCodec for content parsing."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            test_uuid = str(NodeId.generate())
            node_file = project_path / f'{test_uuid}.md'

            # Create content with complex frontmatter
            initial_content = """---
title: "Complex Node"
tags: ["freewriting", "test"]
created: "2023-01-01T10:00:00Z"
updated: "2023-01-01T10:00:00Z"
custom_field: "custom_value"
---

# Complex Node

Existing body content with **markdown**.

- Item 1
- Item 2"""
            node_file.write_text(initial_content)

            mock_clock = Mock(spec=Clock)
            mock_clock.now_iso.return_value = '2023-12-01T12:00:00Z'

            adapter = NodeServiceAdapter(project_path, Mock(), Mock(), mock_clock)

            # Act
            adapter.append_to_node(test_uuid, ['New freewrite content'], {})

            # Assert
            updated_content = node_file.read_text()

            # Verify frontmatter is preserved and updated
            assert 'title:' in updated_content
            assert 'Complex Node' in updated_content
            assert 'tags:' in updated_content
            assert 'freewriting' in updated_content
            assert 'test' in updated_content
            assert 'custom_field:' in updated_content
            assert 'custom_value' in updated_content
            assert 'updated:' in updated_content
            assert '2023-12-01T12:00:00Z' in updated_content

            # Verify body content is preserved and extended
            assert 'Existing body content with **markdown**' in updated_content
            assert '- Item 1' in updated_content
            assert '- Item 2' in updated_content
            assert 'New freewrite content' in updated_content
            assert 'Freewrite Session' in updated_content
