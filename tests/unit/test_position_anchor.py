"""Unit tests for PositionAnchor enum.

Tests the PositionAnchor enum for defining where preserved text
appears in relation to structural elements.
"""

from prosemark.domain.position_anchor import PositionAnchor


class TestPositionAnchor:
    """Unit tests for PositionAnchor enum."""

    def test_position_anchor_values(self) -> None:
        """Test that all expected PositionAnchor values exist."""
        # Verify all expected enum values exist
        assert PositionAnchor.BEFORE_STRUCTURE
        assert PositionAnchor.BETWEEN_ELEMENTS
        assert PositionAnchor.AFTER_STRUCTURE
        assert PositionAnchor.INLINE_WITH_ELEMENT

    def test_position_anchor_string_representation(self) -> None:
        """Test string representation of PositionAnchor values."""
        assert str(PositionAnchor.BEFORE_STRUCTURE) == 'BEFORE_STRUCTURE'
        assert str(PositionAnchor.BETWEEN_ELEMENTS) == 'BETWEEN_ELEMENTS'
        assert str(PositionAnchor.AFTER_STRUCTURE) == 'AFTER_STRUCTURE'
        assert str(PositionAnchor.INLINE_WITH_ELEMENT) == 'INLINE_WITH_ELEMENT'

    def test_position_anchor_equality(self) -> None:
        """Test equality comparison between PositionAnchor values."""
        assert PositionAnchor.BEFORE_STRUCTURE == PositionAnchor.BEFORE_STRUCTURE
        assert PositionAnchor.BEFORE_STRUCTURE != PositionAnchor.AFTER_STRUCTURE  # type: ignore[comparison-overlap]

    def test_position_anchor_ordering_semantics(self) -> None:
        """Test that PositionAnchor values have logical ordering semantics."""
        # Test that the enum values represent a logical flow
        all_anchors = list(PositionAnchor)
        assert len(all_anchors) == 4

        # Verify specific values are present
        assert PositionAnchor.BEFORE_STRUCTURE in all_anchors
        assert PositionAnchor.BETWEEN_ELEMENTS in all_anchors
        assert PositionAnchor.AFTER_STRUCTURE in all_anchors
        assert PositionAnchor.INLINE_WITH_ELEMENT in all_anchors
