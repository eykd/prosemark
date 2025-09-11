"""Domain models for prosemark."""

import uuid
from dataclasses import dataclass

from prosemark.exceptions import NodeIdentityError


@dataclass(frozen=True)
class NodeId:
    """Value object representing a node identifier with UUIDv7 validation.

    NodeId serves as the stable identity for all nodes in the system. It ensures:
    - UUIDv7 format for sortability and uniqueness
    - Immutable once created
    - Validated to ensure proper format
    - Used in filenames ({id}.md, {id}.notes.md) and binder links

    Args:
        value: A valid UUIDv7 string

    Raises:
        NodeIdentityError: If the provided value is not a valid UUIDv7

    Examples:
        >>> node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> str(node_id)
        '0192f0c1-2345-7123-8abc-def012345678'

    """

    value: str

    def __post_init__(self) -> None:
        """Validate that the value is a valid UUIDv7."""
        if not self.value:
            raise NodeIdentityError('NodeId value cannot be empty', self.value)

        try:
            parsed_uuid = uuid.UUID(self.value)
        except ValueError as exc:
            raise NodeIdentityError('Invalid UUID format', self.value) from exc

        # Check that it's specifically a version 7 UUID
        if parsed_uuid.version != 7:
            raise NodeIdentityError('NodeId must be a UUIDv7', self.value, parsed_uuid.version)

    def __str__(self) -> str:
        """Return the UUID string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return the canonical string representation."""
        return f'NodeId({self.value!r})'

    def __hash__(self) -> int:
        """Return hash of the UUID value for use in sets and dicts."""
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        """Compare NodeId instances for equality."""
        if not isinstance(other, NodeId):
            return False
        return self.value == other.value
