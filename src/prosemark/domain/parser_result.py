"""Parser result value objects for enhanced parsing.

This module defines the ParserResult and ParsingMetadata value objects
for complete parsing results with structure and preserved content.
"""

from dataclasses import dataclass

from prosemark.domain.models import Binder
from prosemark.domain.preserved_text import PreservedText


@dataclass(frozen=True)
class ParsingMetadata:
    """Metadata about the parsing process and decisions made.

    This value object tracks statistics about parsing decisions,
    validation results, and content analysis.
    """

    malformed_elements_count: int
    uuid_validation_failures: int
    original_line_count: int
    structural_line_count: int

    def __post_init__(self) -> None:
        """Validate ParsingMetadata field constraints."""
        if self.malformed_elements_count < 0:
            raise ValueError('malformed_elements_count must be non-negative')

        if self.uuid_validation_failures < 0:
            raise ValueError('uuid_validation_failures must be non-negative')

        if self.original_line_count < 0:
            raise ValueError('original_line_count must be non-negative')

        if self.structural_line_count < 0:
            raise ValueError('structural_line_count must be non-negative')

        if self.structural_line_count > self.original_line_count:
            raise ValueError('structural_line_count cannot exceed original_line_count')


@dataclass(frozen=True)
class ParserResult:
    """Complete parsing result with structure and preserved content.

    This value object represents the complete result of enhanced parsing,
    including both the structural binder and all preserved text.
    """

    binder: Binder
    preserved_text: list[PreservedText]
    parsing_metadata: ParsingMetadata
