"""PlaceholderSummary value object for discovered placeholder information."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceholderSummary:
    """Represents discovered placeholder information before materialization.

    This value object captures the essential information about a placeholder
    discovered in the binder, used for planning and executing batch materialization.

    Args:
        display_title: Title of the placeholder
        position: Position in binder hierarchy (e.g., "[0][1]")
        parent_title: Parent item title if applicable
        depth: Nesting level in binder hierarchy

    Raises:
        ValueError: If validation rules are violated during construction

    """

    display_title: str
    position: str
    parent_title: str | None
    depth: int

    def __post_init__(self) -> None:
        """Validate the placeholder summary after construction."""
        # Validate display_title is non-empty
        if not self.display_title or not self.display_title.strip():
            msg = 'Display title must be non-empty string'
            raise ValueError(msg)

        # Validate position follows hierarchical format
        if not self.position or not self._is_valid_position(self.position):
            msg = f"Position must follow hierarchical format, got '{self.position}'"
            raise ValueError(msg)

        # Validate depth is non-negative
        if self.depth < 0:
            msg = f'Depth must be non-negative integer, got {self.depth}'
            raise ValueError(msg)

        # Validate parent_title consistency with depth
        if self.depth == 0 and self.parent_title is not None:
            msg = f"Root level items (depth=0) cannot have parent_title, got '{self.parent_title}'"
            raise ValueError(msg)

        # Note: We don't enforce that depth > 0 requires parent_title because
        # parent information might not always be available during discovery

    @staticmethod
    def _is_valid_position(position: str) -> bool:
        """Check if position follows the expected hierarchical format."""
        # Pattern: [0][1][2]... (one or more bracketed integers)
        import re

        pattern = r'^(\[[0-9]+\])+$'
        return bool(re.match(pattern, position))

    @property
    def is_root_level(self) -> bool:
        """Check if this is a root-level placeholder."""
        return self.depth == 0

    @property
    def hierarchy_path(self) -> str:
        """Generate a human-readable hierarchy path."""
        if self.parent_title:
            return f'{self.parent_title} > {self.display_title}'
        return self.display_title

    @property
    def position_indices(self) -> list[int]:
        """Extract position indices from the position string."""
        import re

        # Extract numbers from [n][m] format
        indices = re.findall(r'\[(\d+)\]', self.position)
        return [int(idx) for idx in indices]

    def with_updated_position(self, new_position: str) -> 'PlaceholderSummary':
        """Create a new instance with updated position."""
        return PlaceholderSummary(
            display_title=self.display_title, position=new_position, parent_title=self.parent_title, depth=self.depth
        )

    def __str__(self) -> str:
        """Generate human-readable string representation."""
        if self.parent_title:
            return f"'{self.display_title}' (under '{self.parent_title}', depth={self.depth})"
        return f"'{self.display_title}' (depth={self.depth})"
