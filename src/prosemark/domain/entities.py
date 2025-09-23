"""Domain entities for prosemark - aliases and additional entity definitions."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Import existing entities from models
from prosemark.domain.models import Binder, BinderItem, NodeId, NodeMetadata
from prosemark.exceptions import FreeformContentValidationError, NodeValidationError


@dataclass(frozen=True)
class Node:
    """Entity representing a content node with file references.

    Node extends NodeMetadata with file path information to create
    a complete entity for content management.

    Args:
        node_id: Unique identifier for the node (UUIDv7)
        title: Optional title of the node document
        synopsis: Optional synopsis/summary of the node content
        created: Creation timestamp as datetime object (accepts datetime or ISO string)
        updated: Last update timestamp as datetime object (accepts datetime or ISO string)
        draft_path: Path to the {node_id}.md file
        notes_path: Path to the {node_id}.notes.md file

    """

    id: NodeId
    title: str | None
    synopsis: str | None
    created: datetime
    updated: datetime
    draft_path: Path
    notes_path: Path

    def __init__(
        self,
        node_id: NodeId,
        title: str | None,
        synopsis: str | None,
        created: datetime | str,
        updated: datetime | str,
        draft_path: Path,
        notes_path: Path,
    ) -> None:
        # Validate required fields
        if node_id is None:
            msg = 'node_id cannot be None'
            raise NodeValidationError(msg)
        if draft_path is None:
            msg = 'draft_path cannot be None'
            raise NodeValidationError(msg)
        if notes_path is None:
            msg = 'notes_path cannot be None'
            raise NodeValidationError(msg)

        # Convert string timestamps to datetime objects
        created_datetime = datetime.fromisoformat(created) if isinstance(created, str) else created
        updated_datetime = datetime.fromisoformat(updated) if isinstance(updated, str) else updated

        # Validate timestamp ordering
        if updated_datetime < created_datetime:
            msg = 'Updated timestamp must be >= created timestamp'
            raise NodeValidationError(msg)

        object.__setattr__(self, 'id', node_id)
        object.__setattr__(self, 'title', title)
        object.__setattr__(self, 'synopsis', synopsis)
        object.__setattr__(self, 'created', created_datetime)
        object.__setattr__(self, 'updated', updated_datetime)
        object.__setattr__(self, 'draft_path', draft_path)
        object.__setattr__(self, 'notes_path', notes_path)

    def get_expected_draft_path(self) -> Path:
        """Return the expected draft file path based on node ID prefix."""
        # Use first 8 characters of the UUID for filename
        prefix = str(self.id)[:8]
        return Path(f'{prefix}.md')

    def get_expected_notes_path(self) -> Path:
        """Return the expected notes file path based on node ID prefix."""
        # Use first 8 characters of the UUID for filename
        prefix = str(self.id)[:8]
        return Path(f'{prefix}.notes.md')

    def touch(self, new_time: datetime | str | None = None) -> None:
        """Update the updated timestamp.

        Args:
            new_time: Optional datetime or datetime string. Defaults to current time.

        """
        if new_time is None:
            new_time = datetime.now(UTC)

        new_time_datetime = datetime.fromisoformat(new_time) if isinstance(new_time, str) else new_time
        object.__setattr__(self, 'updated', new_time_datetime)

    def update_metadata(
        self,
        title: str | None = None,
        synopsis: str | None = None,
        updated: datetime | str | None = None,
    ) -> None:
        """Update the node's metadata and optionally its timestamp.

        Args:
            title: Optional new title
            synopsis: Optional new synopsis
            updated: Optional timestamp for update

        """
        if title is not None:
            object.__setattr__(self, 'title', title)

        if synopsis is not None:
            object.__setattr__(self, 'synopsis', synopsis)

        if updated is not None:
            self.touch(updated)

    @classmethod
    def from_metadata(cls, metadata: NodeMetadata, project_root: Path) -> 'Node':
        """Create Node from NodeMetadata and project root.

        Args:
            metadata: NodeMetadata with id, title, synopsis, timestamps
            project_root: Root directory of the prosemark project

        Returns:
            Node entity with computed file paths

        """
        draft_path = project_root / f'{metadata.id}.md'
        notes_path = project_root / f'{metadata.id}.notes.md'

        return cls(
            node_id=metadata.id,
            title=metadata.title,
            synopsis=metadata.synopsis,
            created=metadata.created,
            updated=metadata.updated,
            draft_path=draft_path,
            notes_path=notes_path,
        )

    def to_metadata(self) -> NodeMetadata:
        """Convert Node to NodeMetadata.

        Returns:
            NodeMetadata with id, title, synopsis, and timestamps

        """
        return NodeMetadata(
            id=self.id,
            title=self.title,
            synopsis=self.synopsis,
            created=self.created,
            updated=self.updated,
        )

    def __str__(self) -> str:
        """Return a meaningful string representation of the Node.

        If title is present, use it. Otherwise, use node ID.
        """
        display = self.title or str(self.id)
        return f'Node({display})'

    def __eq__(self, other: object) -> bool:
        """Compare Node instances based on ID."""
        if not isinstance(other, Node):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Return hash based on ID for use in sets and dicts."""
        return hash(self.id)


@dataclass(frozen=True)
class FreeformContent:
    """Entity representing timestamped freeform writing file.

    FreeformContent represents files created for quick writing that
    don't fit into the structured project hierarchy. Files follow
    the naming pattern: YYYYMMDDTHHMM_{uuid7}.md

    Args:
        id: UUIDv7 identifier as string
        title: Optional content title
        created: Creation timestamp (must match filename timestamp)
        file_path: Path to the timestamped file

    """

    # Constants for validation
    EXPECTED_UUID_VERSION = 7
    TIMESTAMP_LENGTH = 13
    TIMESTAMP_T_POSITION = 8
    MIN_MONTH = 1
    MAX_MONTH = 12
    MIN_DAY = 1
    MAX_DAY = 31
    MIN_HOUR = 0
    MAX_HOUR = 23
    MIN_MINUTE = 0
    MAX_MINUTE = 59

    id: str
    title: str | None
    created: str
    file_path: Path

    def __post_init__(self) -> None:
        """Validate freeform content constraints."""
        self._validate_required_fields()
        self._validate_uuid_format()
        self._validate_filename_pattern()

    def _validate_required_fields(self) -> None:
        """Validate that required fields are not None."""
        if self.created is None:
            msg = 'created timestamp cannot be None'
            raise FreeformContentValidationError(msg)
        if self.id is None:
            msg = 'id cannot be None'
            raise FreeformContentValidationError(msg)

    def _validate_uuid_format(self) -> None:
        """Validate that ID is a properly formatted UUIDv7."""
        try:
            import uuid

            parsed_uuid = uuid.UUID(self.id)
            if parsed_uuid.version != self.EXPECTED_UUID_VERSION:
                FreeformContent._raise_uuid_version_error(parsed_uuid.version or 0)
        except ValueError as exc:
            from prosemark.exceptions import FreeformContentValidationError

            msg = f'Invalid UUID format for FreeformContent ID: {self.id}'
            raise FreeformContentValidationError(msg) from exc

    def _validate_filename_pattern(self) -> None:
        """Validate filename follows YYYYMMDDTHHMM_{uuid7}.md pattern."""
        filename = self.file_path.name
        if not filename.endswith('.md'):
            msg = f'FreeformContent file must end with .md: {filename}'
            raise FreeformContentValidationError(msg)

        timestamp_part, uuid_part = FreeformContent._extract_filename_parts(filename)
        self._validate_uuid_match(uuid_part)
        self._validate_timestamp_format(timestamp_part)
        self._validate_timestamp_consistency(timestamp_part)

    @staticmethod
    def _extract_filename_parts(filename: str) -> tuple[str, str]:
        """Extract timestamp and UUID parts from filename."""
        if '_' not in filename:
            msg = f'FreeformContent filename must contain underscore: {filename}'
            raise FreeformContentValidationError(msg)

        timestamp_part, uuid_part = filename.rsplit('_', 1)
        uuid_part = uuid_part.removesuffix('.md')
        return timestamp_part, uuid_part

    def _validate_uuid_match(self, uuid_part: str) -> None:
        """Validate UUID in filename matches the id."""
        if uuid_part != self.id:
            msg = f"UUID in filename ({uuid_part}) doesn't match id ({self.id})"
            raise FreeformContentValidationError(msg)

    def _validate_timestamp_format(self, timestamp_part: str) -> None:
        """Validate timestamp format YYYYMMDDTHHMM."""
        if len(timestamp_part) != self.TIMESTAMP_LENGTH or timestamp_part[self.TIMESTAMP_T_POSITION] != 'T':
            msg = f'Invalid timestamp format in filename: {timestamp_part}'
            raise FreeformContentValidationError(msg)

        self._validate_timestamp_components(timestamp_part)

    def _validate_timestamp_components(self, timestamp_part: str) -> None:
        """Validate individual timestamp components are valid."""
        try:
            int(timestamp_part[0:4])
            month = int(timestamp_part[4:6])
            day = int(timestamp_part[6:8])
            hour = int(timestamp_part[9:11])
            minute = int(timestamp_part[11:13])

            self._validate_time_ranges(month, day, hour, minute)

        except ValueError as exc:
            msg = f'Invalid timestamp components in filename: {timestamp_part}'
            raise FreeformContentValidationError(msg) from exc

    def _validate_time_ranges(self, month: int, day: int, hour: int, minute: int) -> None:
        """Validate time component ranges."""
        if not (self.MIN_MONTH <= month <= self.MAX_MONTH):
            msg = f'Invalid month in timestamp: {month}'
            raise FreeformContentValidationError(msg)
        if not (self.MIN_DAY <= day <= self.MAX_DAY):
            msg = f'Invalid day in timestamp: {day}'
            raise FreeformContentValidationError(msg)
        if not (self.MIN_HOUR <= hour <= self.MAX_HOUR):
            msg = f'Invalid hour in timestamp: {hour}'
            raise FreeformContentValidationError(msg)
        if not (self.MIN_MINUTE <= minute <= self.MAX_MINUTE):
            msg = f'Invalid minute in timestamp: {minute}'
            raise FreeformContentValidationError(msg)

    def _validate_timestamp_consistency(self, timestamp_part: str) -> None:
        """Validate that filename timestamp matches created timestamp."""
        from datetime import datetime

        # Parse the created timestamp
        try:
            created_dt = datetime.fromisoformat(self.created)
        except ValueError as exc:
            msg = f'Invalid created timestamp format: {self.created}'
            raise FreeformContentValidationError(msg) from exc

        # Format it as YYYYMMDDTHHMM
        expected_timestamp = created_dt.strftime('%Y%m%dT%H%M')

        if timestamp_part != expected_timestamp:
            msg = f'Filename timestamp ({timestamp_part}) does not match created timestamp ({expected_timestamp})'
            raise FreeformContentValidationError(msg)

    @staticmethod
    def _raise_uuid_version_error(version: int) -> None:
        """Raise error for invalid UUID version."""
        msg = f'FreeformContent ID must be UUIDv7, got version {version}'
        raise FreeformContentValidationError(msg)

    def get_expected_filename(self) -> str:
        """Return the expected filename based on created timestamp and ID."""
        # Parse the ISO timestamp and format it as YYYYMMDDTHHMM
        from datetime import datetime

        created_dt = datetime.fromisoformat(self.created)
        timestamp_part = created_dt.strftime('%Y%m%dT%H%M')
        return f'{timestamp_part}_{self.id}.md'

    def parse_filename(self) -> dict[str, str]:
        """Parse the current file's filename into components.

        Returns:
            Dictionary with 'timestamp', 'uuid', and 'extension' keys

        """
        filename = self.file_path.name

        if not filename.endswith('.md'):
            msg = f'Filename must end with .md: {filename}'
            raise FreeformContentValidationError(msg)

        base_name = filename.removesuffix('.md')
        if '_' not in base_name:
            msg = f'Filename must contain underscore: {filename}'
            raise FreeformContentValidationError(msg)

        timestamp_part, uuid_part = base_name.rsplit('_', 1)
        return {'timestamp': timestamp_part, 'uuid': uuid_part, 'extension': '.md'}

    def update_title(self, new_title: str | None) -> None:
        """Update the title of the content.

        Args:
            new_title: New title or None to clear the title

        """
        object.__setattr__(self, 'title', new_title)

    def __eq__(self, other: object) -> bool:
        """Compare FreeformContent instances based on ID."""
        if not isinstance(other, FreeformContent):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Return hash based on ID for use in sets and dicts."""
        return hash(self.id)

    @classmethod
    def get_filename_pattern(cls) -> str:
        """Return the regex pattern for validating freeform content filenames."""
        return r'\d{8}T\d{4}_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.md'


# Re-export all entities for convenient importing
__all__ = [
    'Binder',
    'BinderItem',
    'FreeformContent',
    'Node',
    'NodeId',
    'NodeMetadata',  # Include for backward compatibility
]
