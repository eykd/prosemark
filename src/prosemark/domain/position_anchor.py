"""Position anchor enumeration for text preservation.

This module defines where preserved text appears in relation to structural elements.
"""

from enum import Enum


class PositionAnchor(Enum):
    """Define where preserved text appears in relation to structural elements.

    This enum provides positioning context for extraneous text that needs
    to be preserved during binder operations.
    """

    BEFORE_STRUCTURE = 'before_structure'
    """Text appears before any structural elements."""

    BETWEEN_ELEMENTS = 'between_elements'
    """Text appears between structural elements."""

    AFTER_STRUCTURE = 'after_structure'
    """Text appears after all structural elements."""

    INLINE_WITH_ELEMENT = 'inline_with_element'
    """Text on same line as structural element."""

    def __str__(self) -> str:
        """Return string representation of the anchor position."""
        return self.name
