"""Preserved text value object for text preservation.

This module defines the PreservedText value object for storing extraneous text
with positioning information during binder operations.
"""

from dataclasses import dataclass

from prosemark.domain.position_anchor import PositionAnchor

__all__ = ['PositionAnchor', 'PreservedText']


@dataclass(frozen=True)
class PreservedText:
    """Store extraneous text with positioning information.

    This value object represents non-structural content that must be preserved
    during binder operations, maintaining exact formatting and positioning.
    """

    content: str
    line_number: int
    position_anchor: PositionAnchor
    formatting_preserved: bool = True

    def __post_init__(self) -> None:
        """Validate PreservedText field constraints."""
        if self.content is None:
            raise ValueError('content must not be None')

        if self.line_number <= 0:
            raise ValueError('line_number must be positive')

        if not isinstance(self.position_anchor, PositionAnchor):
            raise TypeError('position_anchor must be valid enum value')
