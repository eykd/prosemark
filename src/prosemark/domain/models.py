"""Domain models for prosemark."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

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

    # Expected UUID version for NodeId
    EXPECTED_UUID_VERSION = 7

    value: str

    def __post_init__(self) -> None:
        """Validate that the value is a valid UUIDv7."""
        # Validate type first
        if not isinstance(self.value, str):  # pragma: no cover
            msg = f'NodeId value must be a string, got {type(self.value).__name__}'
            raise NodeIdentityError(msg, self.value)  # pragma: no cover

        if not self.value:
            msg = 'NodeId value cannot be empty'
            raise NodeIdentityError(msg, self.value)

        # Normalize to lowercase (standard UUID format)
        normalized_value = self.value.lower()
        object.__setattr__(self, 'value', normalized_value)

        try:
            parsed_uuid = uuid.UUID(self.value)
        except ValueError as exc:
            msg = 'Invalid UUID format'
            raise NodeIdentityError(msg, self.value) from exc

        # Check that it's specifically a version 7 UUID
        if parsed_uuid.version != self.EXPECTED_UUID_VERSION:
            msg = 'NodeId must be a UUIDv7'
            raise NodeIdentityError(msg, self.value, parsed_uuid.version)

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

    @classmethod
    def generate(cls) -> 'NodeId':
        """Generate a new NodeId with a UUIDv7.

        Returns:
            A new NodeId instance with a freshly generated UUIDv7

        """
        # TODO: Use uuid.uuid7() when available in Python standard library
        # For now, create a UUID7-compliant UUID manually
        import secrets
        import time

        # Get current timestamp in milliseconds (48 bits)
        timestamp_ms = int(time.time() * 1000)

        # Generate 10 random bytes for the rest
        rand_bytes = secrets.token_bytes(10)

        # Build UUID7 according to RFC 9562:
        # 32 bits: timestamp high
        # 16 bits: timestamp mid
        # 4 bits: version (7)
        # 12 bits: timestamp low + random
        # 2 bits: variant (10)
        # 62 bits: random

        # Extract timestamp parts (48 bits total)
        timestamp_high = (timestamp_ms >> 16) & 0xFFFFFFFF  # Upper 32 bits
        timestamp_mid = timestamp_ms & 0xFFFF  # Lower 16 bits

        # Version 7 + 12 random bits
        version_and_rand = 0x7000 | (rand_bytes[0] << 4) | (rand_bytes[1] >> 4)

        # Variant bits (10) + 14 random bits
        variant_and_rand = 0x8000 | ((rand_bytes[1] & 0x0F) << 10) | (rand_bytes[2] << 2) | (rand_bytes[3] >> 6)

        # Remaining 48 random bits
        clock_seq_low = rand_bytes[3] & 0x3F
        node = int.from_bytes(rand_bytes[4:10], 'big')

        # Construct UUID bytes in the proper order
        uuid_int = (
            (timestamp_high << 96)
            | (timestamp_mid << 80)
            | (version_and_rand << 64)
            | (variant_and_rand << 48)
            | (clock_seq_low << 42)
            | node
        )

        # Convert to UUID object
        generated_uuid = uuid.UUID(int=uuid_int)
        return cls(str(generated_uuid))


@dataclass
class BinderItem:
    """Represents an individual node in the binder hierarchy.

    BinderItem can either reference an existing node (with NodeId) or be a
    placeholder (None node_id). Each item has a display title and can contain
    children to form a tree structure.

    Args:
        display_title: Display title for the item
        node_id: Optional NodeId reference (None for placeholders)
        children: List of child BinderItem objects (defaults to empty list)
        parent: Optional parent BinderItem reference

    Examples:
        >>> # Create a placeholder item
        >>> placeholder = BinderItem(display_title='New Section', node_id=None)

        >>> # Create an item with NodeId
        >>> node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> item = BinderItem(display_title='Chapter 1', node_id=node_id)

        >>> # Create hierarchical structure
        >>> parent = BinderItem(display_title='Part 1', node_id=None)
        >>> parent.children.append(item)

    """

    display_title: str
    node_id: NodeId | None = None
    children: list['BinderItem'] = field(default_factory=list)
    parent: 'BinderItem | None' = None

    def __init__(
        self,
        display_title: str,
        node_id: NodeId | None = None,
        children: list['BinderItem'] | None = None,
        parent: 'BinderItem | None' = None,
        id_: NodeId | None = None,  # backward compatibility
    ) -> None:
        """Initialize BinderItem with backward compatibility for 'id_' parameter."""
        # Handle backward compatibility: if 'id_' is provided, use it for node_id
        if id_ is not None and node_id is None:
            node_id = id_
        elif id_ is not None and node_id is not None:
            msg = "Cannot specify both 'id_' and 'node_id' parameters"
            raise ValueError(msg)

        # Validate display_title is not empty or whitespace-only
        if not display_title or not display_title.strip():
            msg = 'display_title cannot be empty or whitespace-only'
            raise ValueError(msg)

        self.display_title = display_title
        self.node_id = node_id
        self.children = children or []
        self.parent = parent

    @property
    def id(self) -> NodeId | None:
        """Compatibility property for id access."""
        return self.node_id

    def is_root(self) -> bool:
        """Check if this item is a root item (no parent)."""
        return self.parent is None

    def is_leaf(self) -> bool:
        """Check if this item is a leaf item (no children)."""
        return len(self.children) == 0

    def is_placeholder(self) -> bool:
        """Check if this item is a placeholder (no node_id)."""
        return self.node_id is None

    def is_materialized(self) -> bool:
        """Check if this item is materialized (has node_id)."""
        return self.node_id is not None

    def materialize(self, node_id: NodeId) -> None:
        """Materialize this placeholder with a real node_id."""
        if self.node_id is not None:
            from prosemark.exceptions import BinderIntegrityError

            msg = 'Cannot materialize item that already has a node_id'
            raise BinderIntegrityError(msg)
        self.node_id = node_id

    def get_depth(self) -> int:
        """Get the depth of this item in the tree (0 for root)."""
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def get_path_to_root(self) -> list['BinderItem']:
        """Get the path from this item to the root as a list of items."""
        path = []
        current: BinderItem | None = self
        while current is not None:
            path.append(current)
            current = current.parent
        return path

    def get_siblings(self) -> list['BinderItem']:
        """Get all sibling items (items with the same parent)."""
        if self.parent is None:
            return []
        return [child for child in self.parent.children if child is not self]

    def add_child(self, child: 'BinderItem') -> None:
        """Add a child item to this item."""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: 'BinderItem') -> None:
        """Remove a child item from this item."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)


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
        project_title: Optional title for the entire project/binder
        original_content: Original file content for round-trip preservation (internal use)
        managed_content: Managed block content (internal use)

    Raises:
        BinderIntegrityError: If tree invariants are violated (e.g., duplicate NodeIds)

    Examples:
        >>> # Create empty binder
        >>> binder = Binder(roots=[])

        >>> # Create binder with items
        >>> item = BinderItem(id=None, display_title='Chapter 1')
        >>> binder = Binder(roots=[item], project_title='My Book')

        >>> # Find node by ID
        >>> found = binder.find_by_id(node_id)

        >>> # Get all NodeIds
        >>> all_ids = binder.get_all_node_ids()

    """

    roots: list[BinderItem] = field(default_factory=list)
    project_title: str | None = field(default=None)
    original_content: str | None = field(default=None, repr=False)
    managed_content: str | None = field(default=None, repr=False)

    @property
    def children(self) -> list[BinderItem]:
        """Compatibility property to allow iteration over roots."""
        return self.roots

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
            if item.node_id == node_id:
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

    def find_item_by_node_id(self, node_id: NodeId) -> BinderItem | None:
        """Find a BinderItem by its NodeId (alias for find_by_id)."""
        return self.find_by_id(node_id)

    def get_all_node_ids(self) -> set[NodeId]:
        """Get all NodeIds present in the tree.

        Returns:
            Set of all NodeIds in the tree (excludes None ids from placeholders)

        """
        node_ids: set[NodeId] = set()

        def _collect_node_ids(item: BinderItem) -> None:
            """Recursively collect all non-None NodeIds."""
            if item.node_id is not None:
                node_ids.add(item.node_id)

            for child in item.children:
                _collect_node_ids(child)

        for root_item in self.roots:
            _collect_node_ids(root_item)

        return node_ids

    def find_placeholder_by_display_title(self, display_title: str) -> BinderItem | None:
        """Find a placeholder (item with None id) by its display title.

        Performs a depth-first search through the tree to locate the first
        placeholder item with the matching display title.

        Args:
            display_title: The display title to search for

        Returns:
            The BinderItem with matching display title and None id, or None if not found

        """

        def _search_item(item: BinderItem) -> BinderItem | None:
            """Recursively search for the placeholder by display title."""
            if item.node_id is None and item.display_title == display_title:
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

    def add_root_item(self, item: BinderItem) -> None:
        """Add a root item to the binder."""
        item.parent = None
        self.roots.append(item)
        self.validate_integrity()

    def remove_root_item(self, item: BinderItem) -> None:
        """Remove a root item from the binder."""
        if item in self.roots:
            self.roots.remove(item)

    def depth_first_traversal(self) -> list[BinderItem]:
        """Perform depth-first traversal of all items in the binder."""
        result = []

        def _traverse(item: BinderItem) -> None:
            result.append(item)
            for child in item.children:
                _traverse(child)

        for root in self.roots:
            _traverse(root)

        return result


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
    created: str | datetime
    updated: str | datetime

    def to_dict(self) -> dict[str, str | None]:
        """Convert NodeMetadata to a dictionary.

        None values for title and synopsis are excluded from the dictionary
        to keep the serialized format clean.

        Returns:
            Dictionary with metadata fields, excluding None values

        """
        from datetime import datetime

        result: dict[str, str | None] = {
            'id': str(self.id),
            'created': self.created.isoformat() if isinstance(self.created, datetime) else self.created,
            'updated': self.updated.isoformat() if isinstance(self.updated, datetime) else self.updated,
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
            msg = 'Missing id field in metadata dictionary'
            raise NodeIdentityError(msg, None)

        node_id = NodeId(id_str)

        # Get optional fields, defaulting to None if not present
        title = data.get('title')
        synopsis = data.get('synopsis')

        # Get required timestamp fields
        created = data.get('created')
        updated = data.get('updated')

        if not created:
            msg = 'Missing created field in metadata dictionary'
            raise ValueError(msg)
        if not updated:
            msg = 'Missing updated field in metadata dictionary'
            raise ValueError(msg)

        return cls(
            id=node_id,
            title=title,
            synopsis=synopsis,
            created=created,
            updated=updated,
        )
