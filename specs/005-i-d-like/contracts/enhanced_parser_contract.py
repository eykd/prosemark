"""Enhanced Binder Parser Contract for Text Preservation.

This contract defines the interface requirements for preserving extraneous text
during binder operations while maintaining backward compatibility.
"""

from dataclasses import dataclass
from typing import Protocol

from prosemark.domain.models import Binder, NodeId


@dataclass
class PreservedText:
    """Represents preserved non-structural text with positioning information."""

    content: str
    line_number: int
    position_anchor: str  # 'before', 'between', 'after', 'inline'
    formatting_preserved: bool = True


@dataclass
class StructuralElement:
    """Represents a valid markdown list item with optional link."""

    indent_level: int
    title: str
    node_id: NodeId | None
    line_number: int


@dataclass
class ParsingMetadata:
    """Metadata about the parsing process and decisions made."""

    malformed_elements_count: int
    uuid_validation_failures: int
    original_line_count: int
    structural_line_count: int


@dataclass
class ParserResult:
    """Complete parsing result with structure and preserved content."""

    binder: Binder
    preserved_text: list[PreservedText]
    parsing_metadata: ParsingMetadata


class EnhancedBinderParserPort(Protocol):
    """Port interface for enhanced binder parsing with text preservation.

    This protocol extends the existing binder parser capabilities to preserve
    extraneous text while maintaining full backward compatibility.
    """

    def parse_with_preservation(self, markdown_content: str) -> ParserResult:
        """Parse markdown content preserving all non-structural text.

        Args:
            markdown_content: Raw markdown text with mixed structural and narrative content

        Returns:
            ParserResult containing binder structure and preserved text

        Raises:
            PreservationError: If text preservation logic fails

        """
        ...

    def render_with_preservation(self, result: ParserResult) -> str:
        """Render parser result back to markdown with preserved text.

        Args:
            result: Complete parser result with structure and preserved content

        Returns:
            Reconstructed markdown with all original text preserved

        Ensures:
            Round-trip integrity: render(parse(text)) == text

        """
        ...

    # Backward compatibility - existing interface maintained
    def parse_to_binder(self, markdown_content: str) -> Binder:
        """Parse markdown content into Binder object (existing interface).

        This method maintains existing behavior for backward compatibility.
        Extraneous text is ignored in this mode.
        """
        ...

    def render_from_binder(self, binder: Binder) -> str:
        """Render Binder object as clean markdown (existing interface).

        This method maintains existing behavior for backward compatibility.
        Only structural elements are rendered.
        """
        ...


class TextPreservationValidatorPort(Protocol):
    """Port for validating text preservation requirements."""

    def validate_uuid7_format(self, link: str) -> bool:
        """Validate if link matches UUID7 format (36 characters)."""
        ...

    def classify_text_element(self, line: str) -> str:
        """Classify line as 'structural', 'malformed', or 'extraneous'."""
        ...

    def verify_round_trip_integrity(self, original: str, rendered: str) -> bool:
        """Verify that rendered text matches original exactly."""
        ...


# Contract test scenarios - these define the expected behavior
CONTRACT_SCENARIOS = [
    {
        'name': 'preserve_narrative_text',
        'input': """**Act I**
Director Kolteo's story begins here.
- [Chapter 1](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
  Some descriptive text about the chapter.
  - [Scene 1](01998718-2674-7ec0-8b34-514c1c5f0c28.md)""",
        'expected_preserved_count': 2,  # "**Act I**" and "Some descriptive text"
        'expected_structural_count': 2,  # Two valid list items
    },
    {
        'name': 'handle_malformed_syntax',
        'input': """- [Broken link(missing-closing-bracket.md)
- [Valid link](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- Malformed list item without brackets""",
        'expected_preserved_count': 2,  # Malformed elements treated as text
        'expected_structural_count': 1,  # Only valid list item
    },
    {
        'name': 'validate_uuid7_links',
        'input': """- [UUID7 link](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- [Non-UUID link](some-other-file.md)
- [Invalid UUID](12345-invalid-uuid.md)""",
        'expected_structural_count': 1,  # Only UUID7 link is structural
        'expected_preserved_count': 2,  # Non-UUID links treated as extraneous
    },
    {
        'name': 'round_trip_integrity',
        'input': """**Bold text**
- [Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
*Italic text*

Empty line above should be preserved.""",
        'requirement': 'render(parse(input)) === input',
    },
]
