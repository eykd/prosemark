"""Domain models for prosemark."""

import uuid
from dataclasses import dataclass, field

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


@dataclass
class BinderItem:
    """Represents an individual node in the binder hierarchy.

    BinderItem can either reference an existing node (with NodeId) or be a
    placeholder (None id). Each item has a display title and can contain
    children to form a tree structure.

    Args:
        id: Optional NodeId reference (None for placeholders)
        display_title: Display title for the item
        children: List of child BinderItem objects (defaults to empty list)

    Examples:
        >>> # Create a placeholder item
        >>> placeholder = BinderItem(id=None, display_title='New Section')

        >>> # Create an item with NodeId
        >>> node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> item = BinderItem(id=node_id, display_title='Chapter 1')

        >>> # Create hierarchical structure
        >>> parent = BinderItem(id=None, display_title='Part 1')
        >>> parent.children.append(item)

    """

    id: NodeId | None
    display_title: str
    children: list['BinderItem'] = field(default_factory=list)


@dataclass
class Binder:
    """Aggregate root for document hierarchy with tree invariants.

    The Binder maintains a collection of root-level BinderItems and enforces
    critical tree invariants:
    - No duplicate NodeIds across the entire tree
    - Tree structure integrity
    - Provides methods for tree operations and validation

    Args:
        roots: List of root-level BinderItem objects

    Raises:
        BinderIntegrityError: If tree invariants are violated (e.g., duplicate NodeIds)

    Examples:
        >>> # Create empty binder
        >>> binder = Binder(roots=[])

        >>> # Create binder with items
        >>> item = BinderItem(id=None, display_title='Chapter 1')
        >>> binder = Binder(roots=[item])

        >>> # Find node by ID
        >>> found = binder.find_by_id(node_id)

        >>> # Get all NodeIds
        >>> all_ids = binder.get_all_node_ids()

    """

    roots: list[BinderItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate tree integrity during initialization."""
        self.validate_integrity()

    def validate_integrity(self) -> None:
        """Validate all tree invariants using domain policies.

        Raises:
            BinderIntegrityError: If any invariant is violated

        """
        # Import policies locally to avoid circular import
        from prosemark.domain.policies import (
            validate_no_duplicate_ids,
            validate_placeholder_handling,
            validate_tree_structure,
        )

        # Apply all domain policies
        validate_no_duplicate_ids(self.roots)
        validate_tree_structure(self.roots)
        validate_placeholder_handling(self.roots)

    def find_by_id(self, node_id: NodeId) -> BinderItem | None:
        """Find a BinderItem by its NodeId.

        Performs a depth-first search through the tree to locate the item
        with the matching NodeId.

        Args:
            node_id: The NodeId to search for

        Returns:
            The BinderItem with matching NodeId, or None if not found

        """

        def _search_item(item: BinderItem) -> BinderItem | None:
            """Recursively search for the NodeId in the tree."""
            if item.id == node_id:
                return item

            for child in item.children:
                result = _search_item(child)
                if result is not None:
                    return result

            return None

        for root_item in self.roots:
            result = _search_item(root_item)
            if result is not None:
                return result

        return None

    def get_all_node_ids(self) -> set[NodeId]:
        """Get all NodeIds present in the tree.

        Returns:
            Set of all NodeIds in the tree (excludes None ids from placeholders)

        """
        node_ids: set[NodeId] = set()

        def _collect_node_ids(item: BinderItem) -> None:
            """Recursively collect all non-None NodeIds."""
            if item.id is not None:
                node_ids.add(item.id)

            for child in item.children:
                _collect_node_ids(child)

        for root_item in self.roots:
            _collect_node_ids(root_item)

        return node_ids


@dataclass(frozen=True)
class NodeMetadata:
    """Metadata for a node document.

    NodeMetadata tracks essential information about each node including
    its identity, title, timestamps, and optional synopsis. The class is immutable
    (frozen) to ensure data integrity.

    Args:
        id: Unique identifier for the node (UUIDv7)
        title: Optional title of the node document
        synopsis: Optional synopsis/summary of the node content
        created: ISO 8601 formatted creation timestamp string
        updated: ISO 8601 formatted last update timestamp string

    Examples:
        >>> # Create new metadata with all fields
        >>> node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> metadata = NodeMetadata(
        ...     id=node_id,
        ...     title='Chapter One',
        ...     synopsis='Introduction to the story',
        ...     created='2025-09-10T10:00:00-07:00',
        ...     updated='2025-09-10T10:30:00-07:00',
        ... )

        >>> # Create with minimal fields (None values)
        >>> metadata = NodeMetadata(
        ...     id=node_id,
        ...     title=None,
        ...     synopsis=None,
        ...     created='2025-09-10T10:00:00-07:00',
        ...     updated='2025-09-10T10:00:00-07:00',
        ... )

        >>> # Serialize to dictionary
        >>> data = metadata.to_dict()

        >>> # Deserialize from dictionary
        >>> restored = NodeMetadata.from_dict(data)

    """

    id: NodeId
    title: str | None
    synopsis: str | None
    created: str
    updated: str

    def to_dict(self) -> dict[str, str | None]:
        """Convert NodeMetadata to a dictionary.

        None values for title and synopsis are excluded from the dictionary
        to keep the serialized format clean.

        Returns:
            Dictionary with metadata fields, excluding None values

        """
        result: dict[str, str | None] = {
            'id': str(self.id),
            'created': self.created,
            'updated': self.updated,
        }

        # Only include title and synopsis if they are not None
        if self.title is not None:
            result['title'] = self.title
        if self.synopsis is not None:
            result['synopsis'] = self.synopsis

        return result

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> 'NodeMetadata':
        """Create NodeMetadata from a dictionary.

        Handles missing optional fields by defaulting them to None.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            New NodeMetadata instance

        Raises:
            NodeIdentityError: If the id field contains an invalid NodeId

        """
        # Get the id and create a NodeId from it
        id_str = data.get('id')
        if not id_str:
            raise NodeIdentityError('Missing id field in metadata dictionary', None)

        node_id = NodeId(id_str)

        # Get optional fields, defaulting to None if not present
        title = data.get('title')
        synopsis = data.get('synopsis')

        # Get required timestamp fields
        created = data.get('created')
        updated = data.get('updated')

        if not created:
            raise ValueError('Missing created field in metadata dictionary')
        if not updated:
            raise ValueError('Missing updated field in metadata dictionary')

        return cls(
            id=node_id,
            title=title,
            synopsis=synopsis,
            created=created,
            updated=updated,
        )
