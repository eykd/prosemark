"""Unit tests for PreservedText value object.

Tests the PreservedText value object for storing extraneous text
with positioning information.
"""

import pytest

from prosemark.domain.preserved_text import PositionAnchor, PreservedText


class TestPreservedText:
    """Unit tests for PreservedText value object."""

    def test_preserved_text_creation(self) -> None:
        """Test creating a PreservedText instance with valid data."""
        preserved_text = PreservedText(
            content="**Act I**\nDirector Kolteo's story begins here.",
            line_number=1,
            position_anchor=PositionAnchor.BEFORE_STRUCTURE,
            formatting_preserved=True,
        )

        assert preserved_text.content == "**Act I**\nDirector Kolteo's story begins here."
        assert preserved_text.line_number == 1
        assert preserved_text.position_anchor == PositionAnchor.BEFORE_STRUCTURE
        assert preserved_text.formatting_preserved is True

    def test_preserved_text_validation_rules(self) -> None:
        """Test validation rules for PreservedText fields."""
        # None content should raise validation error
        with pytest.raises(ValueError, match='content must not be None'):
            PreservedText(
                content=None,  # type: ignore[arg-type]
                line_number=1,
                position_anchor=PositionAnchor.BEFORE_STRUCTURE,
            )

        # Empty strings and whitespace should be allowed for empty lines
        empty_line = PreservedText(content='', line_number=1, position_anchor=PositionAnchor.BETWEEN_ELEMENTS)
        assert empty_line.content == ''

        # Line number must be positive
        with pytest.raises(ValueError, match='line_number must be positive'):
            PreservedText(content='Some text', line_number=0, position_anchor=PositionAnchor.BEFORE_STRUCTURE)

        # Position anchor must be valid enum value
        with pytest.raises(TypeError, match='position_anchor must be valid enum value'):
            PreservedText(
                content='Some text',
                line_number=1,
                position_anchor='invalid_anchor',  # type: ignore[arg-type]
            )

    def test_preserved_text_equality(self) -> None:
        """Test equality comparison between PreservedText instances."""
        text1 = PreservedText(content='Same content', line_number=1, position_anchor=PositionAnchor.BEFORE_STRUCTURE)
        text2 = PreservedText(content='Same content', line_number=1, position_anchor=PositionAnchor.BEFORE_STRUCTURE)
        text3 = PreservedText(
            content='Different content', line_number=1, position_anchor=PositionAnchor.BEFORE_STRUCTURE
        )

        assert text1 == text2
        assert text1 != text3
