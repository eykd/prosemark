"""Structural element value object for binder parsing.

This module defines the StructuralElement value object for representing
valid markdown list items with optional links.
"""

from dataclasses import dataclass

from prosemark.domain.models import NodeId


@dataclass(frozen=True)
class StructuralElement:
    """Represent a valid markdown list item with optional link.

    This value object represents structural elements that define the binder
    organization hierarchy, such as list items with UUID7 links.
    """

    indent_level: int
    title: str
    node_id: NodeId | None
    line_number: int

    def __post_init__(self) -> None:
        """Validate StructuralElement field constraints."""
        if self.indent_level < 0:
            raise ValueError('indent_level must be non-negative')

        if not self.title.strip():
            raise ValueError('title must not be empty')

        if self.line_number <= 0:
            raise ValueError('line_number must be positive')
