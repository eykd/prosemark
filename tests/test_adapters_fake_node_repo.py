"""Tests for FakeNodeRepo adapter."""

import pytest

from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeNotFoundError


class TestFakeNodeRepo:
    """Test the FakeNodeRepo implementation."""

    def test_delete_call_tracking_advanced(self) -> None:
        """Test advanced tracking of delete method calls."""
        repo = FakeNodeRepo()
        node_id1 = NodeId.generate()
        node_id2 = NodeId.generate()

        # Create some nodes
        repo.create(node_id1, 'Test Node 1', None)
        repo.create(node_id2, 'Test Node 2', None)

        # Delete nodes with different parameters
        repo.delete(node_id1, delete_files=True)

        # Test delete call tracking methods
        delete_calls = repo.get_delete_calls()
        assert len(delete_calls) == 1
        assert (str(node_id1), True) in delete_calls

        # Reset state
        repo.clear_delete_calls()

        # Delete the other node
        repo.delete(node_id2, delete_files=False)

        # Test delete call tracking methods
        delete_calls = repo.get_delete_calls()
        assert len(delete_calls) == 1
        assert (str(node_id2), False) in delete_calls

    def test_delete_call_tracking_edge_cases(self) -> None:
        """Test delete call tracking with tracking multiple delete calls."""
        repo = FakeNodeRepo()
        node_id = NodeId.generate()

        # First create the node
        repo.create(node_id, 'Test Node', None)

        # Delete calls directly use the method
        repo.delete(node_id, delete_files=True)

        # Re-create the node for another deletion
        repo.create(node_id, 'Test Node Again', None)
        repo.delete(node_id, delete_files=False)

        # Verify calls
        delete_calls = repo.get_delete_calls()
        assert len(delete_calls) == 2
        assert (str(node_id), True) in delete_calls
        assert (str(node_id), False) in delete_calls

        # Clear delete calls
        repo.clear_delete_calls()
        assert len(repo.get_delete_calls()) == 0

    def test_delete_unexisting_node_raises_error(self) -> None:
        """Test that deleting a non-existing node raises an error."""
        repo = FakeNodeRepo()
        node_id = NodeId.generate()

        # Attempt to delete a non-existing node should raise error
        with pytest.raises(NodeNotFoundError) as exc_info:
            repo.delete(node_id, delete_files=False)

        assert str(node_id) in str(exc_info.value)

    def test_set_existing_notes_files(self) -> None:
        """Test set_existing_notes_files method."""
        repo = FakeNodeRepo()

        # Test setting notes files
        file_ids = ['node1', 'node2', 'node3']
        repo.set_existing_notes_files(file_ids)

        # Verify internal state (testing line 279)
        assert repo.get_existing_notes_files() == {'node1', 'node2', 'node3'}

    def test_file_exists_invalid_file_type(self) -> None:
        """Test file_exists method with invalid file_type parameter."""
        repo = FakeNodeRepo()
        node_id = NodeId.generate()

        # Test invalid file_type raises ValueError (lines 313-314)
        with pytest.raises(ValueError, match=r'Invalid file_type: invalid_type\. Must be "draft" or "notes"'):
            repo.file_exists(node_id, 'invalid_type')

    def test_file_exists_draft_type(self) -> None:
        """Test file_exists method for draft file type."""
        repo = FakeNodeRepo()
        node_id = NodeId.generate()

        # Test draft file existence check (line 320)
        # File doesn't exist by default
        assert not repo.file_exists(node_id, 'draft')

        # Set the file to exist
        repo.set_existing_files([str(node_id)])
        assert repo.file_exists(node_id, 'draft')

    def test_file_exists_notes_type(self) -> None:
        """Test file_exists method for notes file type."""
        repo = FakeNodeRepo()
        node_id = NodeId.generate()

        # Test notes file existence check
        # File doesn't exist by default
        assert not repo.file_exists(node_id, 'notes')

        # Set the notes file to exist
        repo.set_existing_notes_files([str(node_id)])
        assert repo.file_exists(node_id, 'notes')

    def test_create_notes_file_already_exists_coverage(self) -> None:
        """Test create_notes_file when notes file already exists (coverage for line 365)."""
        # Test coverage for the branch where node_key is already in _existing_notes_files
        node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        repo = FakeNodeRepo()

        # First call creates the notes file entry
        repo.create_notes_file(node_id)
        assert str(node_id) in repo._existing_notes_files

        # Second call should take the branch where node_key is already present
        initial_count = len(repo._existing_notes_files)
        repo.create_notes_file(node_id)

        # Should still be in the set but no additional entry created
        assert str(node_id) in repo._existing_notes_files
        assert len(repo._existing_notes_files) == initial_count
