"""MaterializeResult value object for successful placeholder materialization."""

import re
from dataclasses import dataclass

from prosemark.domain.models import NodeId


@dataclass(frozen=True)
class MaterializeResult:
    """Represents a successful individual placeholder materialization.

    This value object captures all the information about a successful
    materialization operation, including the generated node ID and file paths.

    Args:
        display_title: Title of the materialized placeholder
        node_id: Generated UUIDv7 identifier for the new node
        file_paths: Created file paths (main and notes files)
        position: Position in binder hierarchy (e.g., "[0][1]")

    Raises:
        ValueError: If validation rules are violated during construction

    """

    # Expected number of file paths (main and notes)
    EXPECTED_FILE_COUNT = 2

    display_title: str
    node_id: NodeId
    file_paths: list[str]
    position: str

    def __post_init__(self) -> None:
        """Validate the materialization result after construction."""
        # Validate display_title is non-empty
        if not self.display_title or not self.display_title.strip():
            msg = 'Display title must be non-empty string'
            raise ValueError(msg)

        # Validate node_id is a valid UUIDv7
        if not self._is_valid_uuid7(self.node_id.value):
            msg = f'Node ID must be valid UUIDv7, got {self.node_id.value}'
            raise ValueError(msg)

        # Validate file_paths contains exactly 2 paths
        if len(self.file_paths) != self.EXPECTED_FILE_COUNT:
            msg = f'File paths must contain exactly 2 paths (main and notes), got {len(self.file_paths)}'
            raise ValueError(msg)

        # Validate file paths format
        expected_main = f'{self.node_id.value}.md'
        expected_notes = f'{self.node_id.value}.notes.md'
        if expected_main not in self.file_paths or expected_notes not in self.file_paths:
            msg = f'File paths must contain {expected_main} and {expected_notes}, got {self.file_paths}'
            raise ValueError(msg)

        # Validate position format
        if not self._is_valid_position(self.position):
            msg = f"Position must follow '[n][m]...' pattern, got {self.position}"
            raise ValueError(msg)

    @staticmethod
    def _is_valid_uuid7(uuid_str: str) -> bool:
        """Check if string is a valid UUIDv7."""
        # UUIDv7 pattern: 8-4-4-4-12 hex characters with version 7
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_str, re.IGNORECASE))

    @staticmethod
    def _is_valid_position(position: str) -> bool:
        """Check if position follows the expected format."""
        # Pattern: [0][1][2]... (one or more bracketed integers)
        pattern = r'^(\[[0-9]+\])+$'
        return bool(re.match(pattern, position))

    @property
    def main_file_path(self) -> str:
        """Get the main node file path."""
        main_file = f'{self.node_id.value}.md'
        return next(path for path in self.file_paths if path == main_file)

    @property
    def notes_file_path(self) -> str:
        """Get the notes file path."""
        notes_file = f'{self.node_id.value}.notes.md'
        return next(path for path in self.file_paths if path == notes_file)

    def __str__(self) -> str:
        """Generate human-readable string representation."""
        return f"Materialized '{self.display_title}' → {self.node_id.value}"
