"""Tests for domain models."""

import pytest

from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeIdentityError


class TestNodeId:
    """Test NodeId value object."""

    def test_nodeid_creates_from_valid_uuid7(self) -> None:
        """Test NodeId accepts valid UUIDv7 strings."""
        valid_uuid7 = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(valid_uuid7)
        assert str(node_id) == valid_uuid7

    def test_nodeid_rejects_invalid_uuid(self) -> None:
        """Test NodeId raises exception for invalid UUIDs."""
        with pytest.raises(NodeIdentityError):
            NodeId('not-a-uuid')

    def test_nodeid_equality_and_hashing(self) -> None:
        """Test NodeId equality and hashable behavior."""
        uuid_str = '0192f0c1-2345-7123-8abc-def012345678'
        id1 = NodeId(uuid_str)
        id2 = NodeId(uuid_str)
        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_nodeid_immutability(self) -> None:
        """Test NodeId cannot be modified after creation."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        # Should not have settable attributes
        with pytest.raises(AttributeError):
            node_id.value = 'different-uuid'  # type: ignore[misc]

    def test_nodeid_rejects_non_uuid7_format(self) -> None:
        """Test NodeId rejects UUIDs that aren't version 7."""
        # This is a valid UUID4 but not UUID7
        uuid4 = '550e8400-e29b-41d4-a716-446655440000'
        with pytest.raises(NodeIdentityError):
            NodeId(uuid4)

    def test_nodeid_can_be_used_in_sets(self) -> None:
        """Test NodeId can be used in sets due to being hashable."""
        uuid1 = '0192f0c1-2345-7123-8abc-def012345678'
        uuid2 = '0192f0c1-2345-7456-8abc-def012345678'

        node_id1 = NodeId(uuid1)
        node_id2 = NodeId(uuid2)
        node_id3 = NodeId(uuid1)  # Same as id1

        id_set = {node_id1, node_id2, node_id3}
        assert len(id_set) == 2  # Only two unique IDs

    def test_nodeid_can_be_used_in_dicts(self) -> None:
        """Test NodeId can be used as dictionary keys."""
        uuid1 = '0192f0c1-2345-7123-8abc-def012345678'
        uuid2 = '0192f0c1-2345-7456-8abc-def012345678'

        node_id1 = NodeId(uuid1)
        node_id2 = NodeId(uuid2)

        id_dict = {node_id1: 'value1', node_id2: 'value2'}
        assert len(id_dict) == 2
        assert id_dict[node_id1] == 'value1'
        assert id_dict[node_id2] == 'value2'

    def test_nodeid_string_representation(self) -> None:
        """Test NodeId string representation returns the UUID string."""
        uuid_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(uuid_str)
        assert str(node_id) == uuid_str
        assert repr(node_id) == f'NodeId({uuid_str!r})'

    def test_nodeid_rejects_empty_string(self) -> None:
        """Test NodeId rejects empty strings."""
        with pytest.raises(NodeIdentityError):
            NodeId('')

    def test_nodeid_rejects_none(self) -> None:
        """Test NodeId rejects None values."""
        with pytest.raises(NodeIdentityError):
            NodeId(None)  # type: ignore[arg-type]

    def test_nodeid_inequality_with_different_types(self) -> None:
        """Test NodeId inequality with non-NodeId objects."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        assert node_id != 'not-a-nodeid'
        assert node_id != 123
        assert node_id != None  # noqa: E711
