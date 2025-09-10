"""Domain value objects for Prosemark."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping


@dataclass(frozen=True, order=True)
class NodeId:
    """Immutable UUIDv7 wrapper with validation."""

    value: str

    def __init__(self, value: str | uuid.UUID) -> None:
        """Initialize NodeId with validation.

        Args:
            value: UUIDv7 string or UUID object

        Raises:
            ValueError: If value is not a valid UUIDv7

        """
        if isinstance(value, uuid.UUID):
            uuid_str = str(value)
            uuid_obj = value
        else:
            uuid_str = str(value)
            try:
                uuid_obj = uuid.UUID(uuid_str)
            except ValueError as exc:
                msg = f'Invalid UUID: {value}'
                raise ValueError(msg) from exc

        # Check if it's UUIDv7
        if uuid_obj.version != 7:
            msg = f'NodeId must be UUIDv7, got version {uuid_obj.version}: {value}'
            raise ValueError(msg)

        # Use object.__setattr__ to bypass frozen dataclass
        object.__setattr__(self, 'value', uuid_str)

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return repr representation."""
        return f"NodeId('{self.value}')"


@dataclass(frozen=True)
class Timestamp:
    """UTC ISO8601 string wrapper with validation."""

    value: str

    def __init__(self, value: str | datetime) -> None:
        """Initialize Timestamp with validation.

        Args:
            value: ISO8601 string or datetime object

        Raises:
            ValueError: If value is not a valid ISO8601 timestamp

        """
        iso_str = value.isoformat() if isinstance(value, datetime) else str(value)

        # Validate by parsing
        try:
            datetime.fromisoformat(iso_str)
        except ValueError as exc:
            msg = f'Invalid timestamp: {value}'
            raise ValueError(msg) from exc

        # Use object.__setattr__ to bypass frozen dataclass
        object.__setattr__(self, 'value', iso_str)

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return repr representation."""
        return f"Timestamp('{self.value}')"

    def __lt__(self, other: 'Timestamp') -> bool:
        """Compare timestamps chronologically."""
        return self.to_datetime() < other.to_datetime()

    def __le__(self, other: 'Timestamp') -> bool:
        """Compare timestamps chronologically."""
        return self.to_datetime() <= other.to_datetime()

    def __gt__(self, other: 'Timestamp') -> bool:
        """Compare timestamps chronologically."""
        return self.to_datetime() > other.to_datetime()

    def __ge__(self, other: 'Timestamp') -> bool:
        """Compare timestamps chronologically."""
        return self.to_datetime() >= other.to_datetime()

    def to_datetime(self) -> datetime:
        """Convert to datetime object."""
        return datetime.fromisoformat(self.value)


@dataclass(frozen=True)
class NodeMetadata:
    """Contains node id, title, synopsis, created/updated timestamps."""

    id: NodeId
    title: str | None
    synopsis: str | None
    created: Timestamp
    updated: Timestamp

    def with_updated(self, updated: Timestamp) -> 'NodeMetadata':
        """Create new instance with updated timestamp."""
        return NodeMetadata(id=self.id, title=self.title, synopsis=self.synopsis, created=self.created, updated=updated)

    def with_title(self, title: str | None) -> 'NodeMetadata':
        """Create new instance with updated title and timestamp."""
        return NodeMetadata(
            id=self.id,
            title=title,
            synopsis=self.synopsis,
            created=self.created,
            updated=Timestamp(datetime.now(UTC).isoformat()),
        )

    def with_synopsis(self, synopsis: str | None) -> 'NodeMetadata':
        """Create new instance with updated synopsis and timestamp."""
        return NodeMetadata(
            id=self.id,
            title=self.title,
            synopsis=synopsis,
            created=self.created,
            updated=Timestamp(datetime.now(UTC).isoformat()),
        )

    def to_frontmatter_dict(self) -> dict[str, Any]:
        """Convert to frontmatter dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'synopsis': self.synopsis,
            'created': str(self.created),
            'updated': str(self.updated),
        }

    @classmethod
    def from_frontmatter_dict(cls, data: 'Mapping[str, Any]') -> 'NodeMetadata':
        """Create from frontmatter dictionary."""
        return cls(
            id=NodeId(data['id']),
            title=data.get('title'),
            synopsis=data.get('synopsis'),
            created=Timestamp(data['created']),
            updated=Timestamp(data['updated']),
        )


@dataclass(frozen=True)
class BinderItem:
    """Dataclass representing binder hierarchy items."""

    id: NodeId | None
    display_title: str
    children: list['BinderItem']

    def is_placeholder(self) -> bool:
        """Check if this is a placeholder (None id)."""
        return self.id is None

    def has_children(self) -> bool:
        """Check if this item has children."""
        return len(self.children) > 0

    def collect_all_ids(self) -> list[NodeId]:
        """Collect all non-None NodeIds in this hierarchy."""
        ids = []

        # Add this item's ID if not None
        if self.id is not None:
            ids.append(self.id)

        # Recursively collect from children
        for child in self.children:
            ids.extend(child.collect_all_ids())

        return ids

    def find_by_id(self, node_id: NodeId) -> Optional['BinderItem']:
        """Find item with given NodeId in hierarchy."""
        # Check this item
        if self.id == node_id:
            return self

        # Recursively search children
        for child in self.children:
            found = child.find_by_id(node_id)
            if found is not None:
                return found

        return None
