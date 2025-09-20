"""Contract tests for NodeId value object.

These tests define the behavioral contracts that any NodeId implementation must satisfy.
They will fail until the NodeId class is properly implemented.
"""

from typing import Any
from uuid import uuid4

import pytest

# This import will fail until NodeId is implemented
from prosemark.domain.entities import NodeId
from prosemark.exceptions import NodeIdentityError


class TestNodeIdContract:
    """Contract tests for NodeId value object."""

    def test_nodeid_accepts_valid_uuidv7_string(self) -> None:
        """Contract: NodeId must accept valid UUIDv7 strings."""
        # Valid UUIDv7 (version 7, time-ordered)
        valid_uuid7 = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(valid_uuid7)
        assert str(node_id) == valid_uuid7

    def test_nodeid_rejects_invalid_uuid_format(self) -> None:
        """Contract: NodeId must reject strings that aren't valid UUIDs."""
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            '',
            'abc-def-ghi',
            '0192f0c1-2345-7123-8abc',  # Too short
            '0192f0c1-2345-7123-8abc-def012345678-extra',  # Too long
        ]

        for invalid_uuid in invalid_uuids:
            with pytest.raises(NodeIdentityError):
                NodeId(invalid_uuid)

    def test_nodeid_rejects_non_uuidv7_versions(self) -> None:
        """Contract: NodeId must only accept UUIDv7, not other UUID versions."""
        # Valid UUID4 but wrong version
        uuid4_str = str(uuid4())
        with pytest.raises(NodeIdentityError):
            NodeId(uuid4_str)

        # Valid UUID1 format
        uuid1_str = 'f47ac10b-58cc-1372-a567-0e02b2c3d479'
        with pytest.raises(NodeIdentityError):
            NodeId(uuid1_str)

    def test_nodeid_immutability(self) -> None:
        """Contract: NodeId must be immutable after creation."""
        uuid7_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(uuid7_str)

        # Should not be able to modify the value
        with pytest.raises(AttributeError):
            node_id.value = 'different-uuid'  # type: ignore[misc]

    def test_nodeid_equality_semantics(self) -> None:
        """Contract: NodeId equality must be based on UUID value."""
        uuid7_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id1 = NodeId(uuid7_str)
        node_id2 = NodeId(uuid7_str)

        # Same UUID value should be equal
        assert node_id1 == node_id2

        # Different UUID values should not be equal
        different_uuid7 = '0192f0c1-2345-7456-8abc-def012345678'
        node_id3 = NodeId(different_uuid7)
        assert node_id1 != node_id3

    def test_nodeid_hashable_contract(self) -> None:
        """Contract: NodeId must be hashable for use in sets and dicts."""
        uuid7_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id1 = NodeId(uuid7_str)
        node_id2 = NodeId(uuid7_str)

        # Same value should have same hash
        assert hash(node_id1) == hash(node_id2)

        # Should be usable in sets
        node_set = {node_id1, node_id2}
        assert len(node_set) == 1  # Only one unique item

        # Should be usable as dict keys
        node_dict = {node_id1: 'value'}
        assert node_dict[node_id2] == 'value'

    def test_nodeid_string_representation(self) -> None:
        """Contract: NodeId string representation must be the UUID value."""
        uuid7_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(uuid7_str)

        assert str(node_id) == uuid7_str
        assert uuid7_str in repr(node_id)

    def test_nodeid_value_property_access(self) -> None:
        """Contract: NodeId must provide read-only access to UUID value."""
        uuid7_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(uuid7_str)

        # Should be able to read the value
        assert node_id.value == uuid7_str

    @pytest.mark.parametrize(
        'invalid_input',
        [
            None,
            123,
            [],
            {},
            object(),
        ],
    )
    def test_nodeid_type_safety(self, invalid_input: int | list[Any] | dict[Any, Any] | object | None) -> None:
        """Contract: NodeId must only accept string inputs."""
        with pytest.raises((TypeError, NodeIdentityError)):
            NodeId(invalid_input)  # type: ignore[arg-type]

    def test_nodeid_case_sensitivity(self) -> None:
        """Contract: NodeId must be case-sensitive for UUID values."""
        uuid7_lower = '0192f0c1-2345-7123-8abc-def012345678'
        uuid7_upper = '0192F0C1-2345-7123-8ABC-DEF012345678'

        # These should be treated as different (standard UUID format is lowercase)
        node_id_lower = NodeId(uuid7_lower)

        # Uppercase should either be normalized or rejected
        # (The exact behavior depends on implementation choice)
        try:
            node_id_upper = NodeId(uuid7_upper)
            # If accepted, they should be equal after normalization
            assert node_id_lower == node_id_upper
        except NodeIdentityError:
            # If rejected, that's also valid behavior
            pass

    def test_nodeid_uniqueness_within_project(self) -> None:
        """Contract: NodeId values must be unique within a project scope.

        Note: This is a domain rule that will be enforced at the repository level,
        but NodeId should support the uniqueness contract.
        """
        uuid7_1 = '0192f0c1-2345-7123-8abc-def012345678'
        uuid7_2 = '0192f0c1-2345-7456-8abc-def012345678'

        node_id1 = NodeId(uuid7_1)
        node_id2 = NodeId(uuid7_2)

        # Different UUIDs should create different NodeIds
        assert node_id1 != node_id2
        assert hash(node_id1) != hash(node_id2)


@pytest.fixture
def valid_node_id() -> NodeId:
    """Fixture providing a valid NodeId for tests."""
    return NodeId('0192f0c1-2345-7123-8abc-def012345678')


@pytest.fixture
def sample_uuid7_strings() -> list[str]:
    """Fixture providing sample valid UUIDv7 strings."""
    return [
        '0192f0c1-2345-7123-8abc-def012345678',
        '0192f0c1-2345-7456-8abc-def012345678',
        '0192f0c1-2345-7789-8abc-def012345678',
    ]
