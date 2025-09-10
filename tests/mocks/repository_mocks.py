"""Mock implementations for repository protocols."""

import uuid
from datetime import UTC, datetime
from typing import Any

from prosemark.domain.aggregates import Binder
from prosemark.domain.value_objects import NodeId


class MockBinderRepo:
    """Mock implementation of BinderRepo for testing."""

    def __init__(self, initial_binder: Binder | None = None) -> None:
        """Initialize with optional initial binder state."""
        self._binder = initial_binder or Binder(roots=[])
        self.load_called = 0
        self.save_called = 0
        self.last_saved_binder: Binder | None = None

    def load(self) -> Binder:
        """Load the stored binder."""
        self.load_called += 1
        return self._binder

    def save(self, binder: Binder) -> None:
        """Save binder to mock storage."""
        self.save_called += 1
        self._binder = binder
        self.last_saved_binder = binder


class MockNodeRepo:
    """Mock implementation of NodeRepo for testing."""

    def __init__(self) -> None:
        """Initialize empty mock repository."""
        self._frontmatters: dict[str, dict[str, Any]] = {}
        self._files_created: set[str] = set()
        self._files_deleted: set[str] = set()
        self._editor_opened: list[tuple[str, str]] = []

        # Call tracking
        self.create_called = 0
        self.read_frontmatter_called = 0
        self.write_frontmatter_called = 0
        self.open_in_editor_called = 0
        self.delete_called = 0

    def create(self, node_id: NodeId, title: str | None, synopsis: str | None) -> None:
        """Create mock node with frontmatter."""
        self.create_called += 1

        if str(node_id) in self._frontmatters:
            msg = f'Node {node_id} already exists'
            raise FileExistsError(msg)

        now = datetime.now(UTC).isoformat()
        self._frontmatters[str(node_id)] = {
            'id': str(node_id),
            'title': title,
            'synopsis': synopsis,
            'created': now,
            'updated': now,
        }
        self._files_created.add(str(node_id))

    def read_frontmatter(self, node_id: NodeId) -> dict[str, Any]:
        """Read mock frontmatter."""
        self.read_frontmatter_called += 1

        if str(node_id) not in self._frontmatters:
            msg = f'Node {node_id} not found'
            raise FileNotFoundError(msg)

        return self._frontmatters[str(node_id)].copy()

    def write_frontmatter(self, node_id: NodeId, frontmatter: dict[str, Any]) -> None:
        """Write mock frontmatter."""
        self.write_frontmatter_called += 1

        if str(node_id) not in self._frontmatters:
            msg = f'Node {node_id} not found'
            raise FileNotFoundError(msg)

        # Update timestamp
        frontmatter = frontmatter.copy()
        frontmatter['updated'] = datetime.now(UTC).isoformat()
        self._frontmatters[str(node_id)] = frontmatter

    def open_in_editor(self, node_id: NodeId, part: str) -> None:
        """Mock opening in editor."""
        self.open_in_editor_called += 1

        if str(node_id) not in self._frontmatters:
            msg = f'Node {node_id} not found'
            raise FileNotFoundError(msg)

        if part not in ('draft', 'notes'):
            msg = f'Invalid part: {part}'
            raise ValueError(msg)

        self._editor_opened.append((str(node_id), part))

    def delete(self, node_id: NodeId, *, delete_files: bool) -> None:
        """Mock node deletion."""
        self.delete_called += 1

        if str(node_id) not in self._frontmatters:
            msg = f'Node {node_id} not found'
            raise FileNotFoundError(msg)

        if delete_files:
            del self._frontmatters[str(node_id)]
            self._files_deleted.add(str(node_id))

    def get_created_files(self) -> set[str]:
        """Get list of created file IDs."""
        return self._files_created.copy()

    def get_deleted_files(self) -> set[str]:
        """Get list of deleted file IDs."""
        return self._files_deleted.copy()

    def get_editor_opens(self) -> list[tuple[str, str]]:
        """Get list of (node_id, part) tuples opened in editor."""
        return self._editor_opened.copy()


class MockDailyRepo:
    """Mock implementation of DailyRepo for testing."""

    def __init__(self) -> None:
        """Initialize empty mock repository."""
        self._created_files: list[tuple[str, str | None]] = []
        self.write_freeform_called = 0

    def write_freeform(self, title: str | None) -> str:
        """Create mock freewrite file."""
        self.write_freeform_called += 1

        # Generate mock filename with timestamp and UUID
        now = datetime.now(UTC)
        timestamp = now.strftime('%Y%m%dT%H%M')
        file_uuid = str(uuid.uuid4())[:8]
        filename = f'{timestamp}_{file_uuid}.md'

        self._created_files.append((filename, title))
        return filename

    def get_created_files(self) -> list[tuple[str, str | None]]:
        """Get list of (filename, title) tuples for created files."""
        return self._created_files.copy()
