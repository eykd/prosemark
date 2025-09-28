"""Enhanced binder parser port interface.

This module defines the port interface for enhanced binder parsing capabilities
that preserve extraneous text during binder operations.
"""

from abc import ABC, abstractmethod

from prosemark.domain.models import Binder
from prosemark.domain.parser_result import ParserResult


class EnhancedBinderParserPort(ABC):
    """Port interface for enhanced binder parsing with text preservation.

    This port extends basic binder parsing capabilities to support preservation
    of extraneous text during parse and render operations, enabling full
    round-trip integrity for mixed structural and narrative content.
    """

    @abstractmethod
    def parse_with_preservation(self, markdown_content: str) -> ParserResult:
        """Parse markdown content preserving all non-structural text.

        Args:
            markdown_content: Raw markdown text with mixed structural and narrative content

        Returns:
            ParserResult containing binder structure and preserved text

        Raises:
            BinderFormatError: If structural parsing fails

        """

    @abstractmethod
    def render_with_preservation(self, parser_result: ParserResult) -> str:
        """Render ParserResult back to markdown preserving all text positioning.

        Args:
            parser_result: Result from parse_with_preservation containing binder and preserved text

        Returns:
            Markdown text with structural elements and preserved text

        """

    @abstractmethod
    def parse_to_binder(self, markdown_content: str) -> Binder:
        """Parse markdown content into a Binder object (legacy method).

        Args:
            markdown_content: Markdown text with unordered list structure

        Returns:
            Binder object with parsed hierarchy

        Raises:
            BinderFormatError: If markdown format is invalid or malformed

        """

    @abstractmethod
    def render_from_binder(self, binder: Binder) -> str:
        """Render Binder object as markdown list content (legacy method).

        Args:
            binder: Binder object to render

        Returns:
            Markdown text with unordered list structure

        """
