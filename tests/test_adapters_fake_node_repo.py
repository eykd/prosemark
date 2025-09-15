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
