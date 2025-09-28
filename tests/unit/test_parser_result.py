"""Unit tests for ParserResult value object.

Tests the ParserResult value object for complete parsing results
with structure and preserved content.
"""

import pytest

from prosemark.domain.models import Binder
from prosemark.domain.parser_result import ParserResult, ParsingMetadata
from prosemark.domain.preserved_text import PositionAnchor, PreservedText


class TestParserResult:
    """Unit tests for ParserResult value object."""

    def test_parser_result_creation(self) -> None:
        """Test creating a ParserResult instance with valid data."""
        binder = Binder(roots=[])
        preserved_text = [
            PreservedText(content='Test content', line_number=1, position_anchor=PositionAnchor.BEFORE_STRUCTURE)
        ]
        metadata = ParsingMetadata(
            malformed_elements_count=0, uuid_validation_failures=0, original_line_count=10, structural_line_count=5
        )

        result = ParserResult(binder=binder, preserved_text=preserved_text, parsing_metadata=metadata)

        assert result.binder == binder
        assert result.preserved_text == preserved_text
        assert result.parsing_metadata == metadata

    def test_parser_result_empty_preserved_text(self) -> None:
        """Test creating a ParserResult with no preserved text."""
        binder = Binder(roots=[])
        metadata = ParsingMetadata(
            malformed_elements_count=0, uuid_validation_failures=0, original_line_count=5, structural_line_count=2
        )

        result = ParserResult(binder=binder, preserved_text=[], parsing_metadata=metadata)

        assert result.binder == binder
        assert result.preserved_text == []
        assert result.parsing_metadata == metadata

    def test_parsing_metadata_creation(self) -> None:
        """Test creating ParsingMetadata with valid counts."""
        metadata = ParsingMetadata(
            malformed_elements_count=2, uuid_validation_failures=1, original_line_count=15, structural_line_count=5
        )

        assert metadata.malformed_elements_count == 2
        assert metadata.uuid_validation_failures == 1
        assert metadata.original_line_count == 15
        assert metadata.structural_line_count == 5

    def test_parsing_metadata_validation(self) -> None:
        """Test validation rules for ParsingMetadata fields."""
        # Test negative malformed elements count
        with pytest.raises(ValueError, match='malformed_elements_count must be non-negative'):
            ParsingMetadata(
                malformed_elements_count=-1, uuid_validation_failures=0, original_line_count=10, structural_line_count=5
            )

        # Test negative uuid validation failures
        with pytest.raises(ValueError, match='uuid_validation_failures must be non-negative'):
            ParsingMetadata(
                malformed_elements_count=0, uuid_validation_failures=-1, original_line_count=10, structural_line_count=5
            )

        # Test negative original line count
        with pytest.raises(ValueError, match='original_line_count must be non-negative'):
            ParsingMetadata(
                malformed_elements_count=0, uuid_validation_failures=0, original_line_count=-1, structural_line_count=5
            )

        # Test negative structural line count
        with pytest.raises(ValueError, match='structural_line_count must be non-negative'):
            ParsingMetadata(
                malformed_elements_count=0, uuid_validation_failures=0, original_line_count=10, structural_line_count=-1
            )

        # Test structural line count exceeding original line count
        with pytest.raises(ValueError, match='structural_line_count cannot exceed original_line_count'):
            ParsingMetadata(
                malformed_elements_count=0, uuid_validation_failures=0, original_line_count=5, structural_line_count=10
            )
