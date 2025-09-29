"""PlaceholderPattern value object for placeholder syntax handling and validation."""

import re
from typing import Self

from prosemark.templates.domain.exceptions.template_exceptions import InvalidPlaceholderError


class PlaceholderPattern:
    """Immutable value object representing a validated placeholder pattern.

    This value object encapsulates a placeholder pattern like '{{variable_name}}'
    and provides parsing and validation capabilities.
    """

    # Regex for valid placeholder patterns: {{valid_identifier}}
    PLACEHOLDER_REGEX = re.compile(r'^\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}$')

    def __init__(self, pattern: str) -> None:
        """Initialize a placeholder pattern with validation.

        Args:
            pattern: The placeholder pattern string (e.g., "{{variable_name}}")

        Raises:
            InvalidPlaceholderError: If the pattern has invalid syntax

        """
        if not isinstance(pattern, str):
            raise InvalidPlaceholderError('Placeholder pattern must be a string', placeholder_pattern=str(pattern))

        if not pattern.strip():
            raise InvalidPlaceholderError('Placeholder pattern cannot be empty', placeholder_pattern=pattern)

        match = self.PLACEHOLDER_REGEX.match(pattern)
        if not match:
            raise InvalidPlaceholderError(
                'Invalid placeholder pattern syntax. Must be {{valid_identifier}}', placeholder_pattern=pattern
            )

        self._pattern = pattern
        self._name = match.group(1)

    @property
    def raw(self) -> str:
        """Get the raw placeholder pattern string."""
        return self._pattern

    @property
    def name(self) -> str:
        """Get the extracted variable name from the pattern."""
        return self._name

    @property
    def is_valid(self) -> bool:
        """Check if the pattern is valid (always True for constructed instances)."""
        return True

    def matches_text(self, text: str) -> bool:
        """Check if this pattern appears in the given text.

        Args:
            text: Text to search for this placeholder pattern

        Returns:
            True if the pattern is found in the text

        """
        return self._pattern in text

    def extract_from_text(self, text: str) -> list[str]:
        """Extract all occurrences of this pattern from text.

        Args:
            text: Text to extract patterns from

        Returns:
            List of pattern occurrences (may contain duplicates)

        """
        return re.findall(re.escape(self._pattern), text)

    def replace_in_text(self, text: str, replacement: str) -> str:
        """Replace all occurrences of this pattern in text.

        Args:
            text: Text to perform replacement in
            replacement: String to replace the pattern with

        Returns:
            Text with all occurrences of the pattern replaced

        """
        return text.replace(self._pattern, replacement)

    @classmethod
    def from_name(cls, variable_name: str) -> Self:
        """Create a placeholder pattern from a variable name.

        Args:
            variable_name: The variable name (without braces)

        Returns:
            New PlaceholderPattern instance

        Raises:
            InvalidPlaceholderError: If the variable name is invalid

        """
        if not variable_name:
            raise InvalidPlaceholderError('Variable name cannot be empty')

        # Validate that the name would be a valid Python identifier
        if (
            not variable_name.replace('_', 'a')
            .replace('0', 'a')
            .replace('1', 'a')
            .replace('2', 'a')
            .replace('3', 'a')
            .replace('4', 'a')
            .replace('5', 'a')
            .replace('6', 'a')
            .replace('7', 'a')
            .replace('8', 'a')
            .replace('9', 'a')
            .isalpha()
        ):
            msg = f'Invalid variable name: {variable_name}. Must be a valid Python identifier'
            raise InvalidPlaceholderError(msg, placeholder_pattern=f'{{{{{variable_name}}}}}')

        if variable_name[0].isdigit():
            msg = f'Variable name cannot start with a digit: {variable_name}'
            raise InvalidPlaceholderError(msg, placeholder_pattern=f'{{{{{variable_name}}}}}')

        pattern = f'{{{{{variable_name}}}}}'
        return cls(pattern)

    @classmethod
    def extract_all_from_text(cls, text: str) -> list[Self]:
        """Extract all valid placeholder patterns from text.

        Args:
            text: Text to extract placeholder patterns from

        Returns:
            List of PlaceholderPattern instances found in text

        Raises:
            InvalidPlaceholderError: If malformed patterns are found

        """
        # Find all potential placeholder patterns
        potential_patterns = re.findall(r'\{\{[^}]*\}\}', text)

        patterns = []
        for pattern in potential_patterns:
            try:
                patterns.append(cls(pattern))
            except InvalidPlaceholderError as e:
                # Re-raise with more context about where the invalid pattern was found
                msg = f'Found malformed placeholder pattern in text: {pattern}'
                raise InvalidPlaceholderError(msg, placeholder_pattern=pattern) from e

        return patterns

    @classmethod
    def is_valid_pattern(cls, pattern: str) -> bool:
        """Check if a string is a valid placeholder pattern without raising exceptions.

        Args:
            pattern: Pattern string to validate

        Returns:
            True if the pattern is valid, False otherwise

        """
        try:
            cls(pattern)
        except InvalidPlaceholderError:
            return False
        else:
            return True

    def __str__(self) -> str:
        """String representation of the placeholder pattern."""
        return self._pattern

    def __repr__(self) -> str:
        """Developer representation of the placeholder pattern."""
        return f'PlaceholderPattern({self._pattern!r})'

    def __eq__(self, other: object) -> bool:
        """Check equality with another PlaceholderPattern."""
        if not isinstance(other, PlaceholderPattern):
            return NotImplemented
        return self._pattern == other._pattern

    def __hash__(self) -> int:
        """Hash based on the pattern value."""
        return hash(self._pattern)
