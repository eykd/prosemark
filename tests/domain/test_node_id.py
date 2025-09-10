"""Tests for NodeId value object."""

import uuid
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st
from uuid_extension import uuid7

from prosemark.domain.value_objects import NodeId


class TestNodeId:
    """Test suite for NodeId value object."""

    def test_create_from_valid_uuid7_string(self) -> None:
        """NodeId accepts valid UUIDv7 strings."""
        # Generate a valid UUIDv7
        uuid7_val = uuid7()
        uuid7_str = str(uuid7_val)

        node_id = NodeId(uuid7_str)

        assert node_id.value == uuid7_str
        assert str(node_id) == uuid7_str

    def test_create_from_uuid_object(self) -> None:
        """NodeId accepts UUID objects."""
        uuid7_val = uuid7()

        node_id = NodeId(uuid7_val)

        assert node_id.value == str(uuid7_val)
        assert str(node_id) == str(uuid7_val)

    def test_rejects_invalid_uuid_format(self) -> None:
        """NodeId rejects invalid UUID formats."""
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            '',
            'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            '123e4567-e89b-12d3',  # Too short
        ]

        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValueError, match='Invalid UUID'):
                NodeId(invalid_uuid)

    def test_rejects_non_uuid7(self) -> None:
        """NodeId rejects non-UUIDv7 UUIDs."""
        # UUID v4 should be rejected
        uuid4 = uuid.uuid4()

        with pytest.raises(ValueError, match='must be UUIDv7'):
            NodeId(uuid4)

    def test_immutability(self) -> None:
        """NodeId is immutable."""
        uuid7_val = uuid7()
        node_id = NodeId(uuid7_val)

        # Should not be able to modify value
        with pytest.raises(AttributeError):
            node_id.value = str(uuid7())  # type: ignore[misc]

    def test_equality(self) -> None:
        """NodeId equality is based on value."""
        uuid7_val = uuid7()
        uuid7_str = str(uuid7_val)

        node_id1 = NodeId(uuid7_str)
        node_id2 = NodeId(uuid7_str)
        node_id3 = NodeId(uuid7())  # Different UUID

        assert node_id1 == node_id2
        assert node_id1 != node_id3
        assert node_id1 != uuid7_str  # type: ignore[comparison-overlap]  # Should not equal plain string

    def test_hashable(self) -> None:
        """NodeId is hashable and can be used in sets/dicts."""
        uuid7_1 = uuid7()
        uuid7_2 = uuid7()

        node_id1 = NodeId(uuid7_1)
        node_id2 = NodeId(uuid7_1)  # Same UUID
        node_id3 = NodeId(uuid7_2)  # Different UUID

        # Should be hashable
        node_set = {node_id1, node_id2, node_id3}
        assert len(node_set) == 2  # node_id1 and node_id2 are the same

        # Should work as dict keys
        node_dict = {node_id1: 'value1', node_id3: 'value2'}
        assert node_dict[node_id2] == 'value1'  # node_id2 equals node_id1

    def test_repr(self) -> None:
        """NodeId has a useful repr."""
        uuid7_val = uuid7()
        node_id = NodeId(uuid7_val)

        assert repr(node_id) == f"NodeId('{uuid7_val!s}')"

    def test_ordering(self) -> None:
        """NodeId supports ordering based on UUID value."""
        # UUIDv7 is time-ordered, so we can test ordering
        # Generate UUIDs with different timestamps to ensure ordering
        uuid1 = uuid7()
        import time

        time.sleep(0.001)  # Small delay to ensure different timestamp
        uuid2 = uuid7()

        node_id1 = NodeId(uuid1)
        node_id2 = NodeId(uuid2)

        # uuid2 was created after uuid1, so should be greater
        assert node_id1 <= node_id2  # Allow equal in case of same timestamp
        # Test that ordering works consistently
        assert (node_id1 < node_id2) or (node_id1 == node_id2)
        assert node_id1 <= node_id2
        assert node_id2 >= node_id1

    @given(st.uuids(version=4))
    def test_property_rejects_non_uuid7(self, uuid_val: UUID) -> None:
        """Property test: NodeId rejects all non-UUIDv7 UUIDs."""
        # UUID v4 from hypothesis should always be rejected
        with pytest.raises(ValueError, match='must be UUIDv7'):
            NodeId(uuid_val)

    def test_serialization(self) -> None:
        """NodeId can be serialized to string."""
        uuid7_val = uuid7()
        node_id = NodeId(uuid7_val)

        # Should be serializable
        serialized = str(node_id)
        deserialized = NodeId(serialized)

        assert deserialized == node_id
        assert deserialized.value == node_id.value
