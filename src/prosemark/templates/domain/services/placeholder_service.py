"""Placeholder service providing business logic for placeholder operations."""

from typing import Any

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    InvalidPlaceholderValueError,
)
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


class PlaceholderService:
    """Service providing placeholder operations and validation logic."""

    @staticmethod
    def create_placeholder_from_pattern(
        pattern: str,
        frontmatter: dict[str, Any] | None = None,
        *,
        required: bool = True,
        default_value: str | None = None,
        description: str | None = None,
    ) -> Placeholder:
        """Create a Placeholder from a pattern string.

        Args:
            pattern: The placeholder pattern (e.g., "{{variable_name}}")
            frontmatter: Optional frontmatter dictionary for placeholder configuration
            required: Whether this placeholder requires user input (ignored if frontmatter provided)
            default_value: Optional default value if not required (ignored if frontmatter provided)
            description: Optional human-readable description (ignored if frontmatter provided)

        Returns:
            New Placeholder instance

        Raises:
            InvalidPlaceholderError: If the pattern is invalid or inconsistent

        """
        try:
            if frontmatter:
                # Use frontmatter to configure the placeholder
                pattern_obj = PlaceholderPattern(pattern)
                return Placeholder.from_frontmatter(pattern_obj.name, frontmatter, pattern_obj)
            # Use provided arguments
            return Placeholder.from_pattern(
                pattern, required=required, default_value=default_value, description=description
            )
        except Exception as e:
            msg = f"Failed to create placeholder from pattern '{pattern}': {e}"
            raise InvalidPlaceholderError(msg, placeholder_pattern=pattern) from e

    @staticmethod
    def create_placeholder_from_name(
        name: str,
        *,
        required: bool = True,
        default_value: str | None = None,
        description: str | None = None,
    ) -> Placeholder:
        """Create a Placeholder from a variable name.

        Args:
            name: The variable name (without braces)
            required: Whether this placeholder requires user input
            default_value: Optional default value if not required
            description: Optional human-readable description

        Returns:
            New Placeholder instance

        Raises:
            InvalidPlaceholderError: If the name is invalid

        """
        try:
            return Placeholder.from_name(name, required=required, default_value=default_value, description=description)
        except Exception as e:
            msg = f"Failed to create placeholder from name '{name}': {e}"
            raise InvalidPlaceholderError(msg, placeholder_pattern=f'{{{{{name}}}}}') from e

    @staticmethod
    def validate_placeholder_pattern(pattern: str) -> bool:
        """Validate that a pattern is a valid placeholder.

        Args:
            pattern: The pattern to validate

        Returns:
            True if the pattern is valid, False otherwise

        """
        try:
            PlaceholderPattern(pattern)
        except InvalidPlaceholderError:
            return False
        else:
            return True

    @staticmethod
    def extract_placeholders_from_text(text: str, frontmatter: dict[str, Any] | None = None) -> list[Placeholder]:
        """Extract all placeholder patterns from text.

        Args:
            text: The text to extract placeholders from
            frontmatter: Optional frontmatter dictionary for placeholder configuration

        Returns:
            List of unique Placeholder objects found in the text

        Raises:
            InvalidPlaceholderError: If any pattern is invalid

        """
        # Find all potential placeholder patterns manually and filter valid ones
        import re

        potential_patterns = re.findall(r'\{\{[^}]*\}\}', text)

        # Convert patterns to Placeholder objects, skipping invalid ones
        placeholders = []
        seen_names = set()

        for pattern_str in potential_patterns:
            try:
                pattern = PlaceholderPattern(pattern_str)
            except InvalidPlaceholderError:
                # Skip invalid patterns as per test requirements
                continue
            if pattern.name not in seen_names:
                if frontmatter:
                    # Use frontmatter to configure placeholder
                    placeholder = Placeholder.from_frontmatter(pattern.name, frontmatter, pattern)
                else:
                    # Default configuration
                    placeholder = Placeholder(
                        name=pattern.name,
                        pattern_obj=pattern,
                        required=True,  # Default to required
                        default_value=None,
                        description=None,
                    )
                placeholders.append(placeholder)
                seen_names.add(pattern.name)

        return placeholders

    @staticmethod
    def get_placeholder_names_from_text(text: str) -> set[str]:
        """Extract just the placeholder names from text.

        Args:
            text: The text to extract placeholder names from

        Returns:
            Set of unique placeholder names found in the text

        """
        # Find all potential placeholder patterns manually and filter valid ones
        import re

        potential_patterns = re.findall(r'\{\{[^}]*\}\}', text)

        names = set()
        for pattern_str in potential_patterns:
            try:
                pattern = PlaceholderPattern(pattern_str)
                names.add(pattern.name)
            except InvalidPlaceholderError:
                # Skip invalid patterns
                continue

        return names

    def replace_placeholders_in_text(self, text: str, placeholder_values: dict[str, str]) -> str:
        """Replace placeholders in text with provided values.

        Only replaces placeholders for which values are provided.
        Missing placeholders are left unchanged.

        Args:
            text: The text to replace placeholders in
            placeholder_values: Dictionary mapping placeholder names to values

        Returns:
            Text with available placeholders replaced

        Raises:
            InvalidPlaceholderError: If any placeholder pattern is invalid
            InvalidPlaceholderValueError: If any value is invalid

        """
        result = text

        # Extract all placeholders from the text
        placeholders = self.extract_placeholders_from_text(text)

        # Replace each placeholder if a value is available
        for placeholder in placeholders:
            if placeholder.name in placeholder_values:
                value = placeholder_values[placeholder.name]
                result = self.replace_placeholder_in_text(result, placeholder, value)

        return result

    @staticmethod
    def merge_placeholder_lists(placeholder_lists: list[list[Placeholder]]) -> list[Placeholder]:
        """Merge multiple placeholder lists into a single list.

        Args:
            placeholder_lists: List of placeholder lists to merge

        Returns:
            Single merged list with duplicates removed

        Raises:
            ValueError: If conflicting placeholder definitions are found

        """
        merged_placeholders: dict[str, Placeholder] = {}

        for placeholder_list in placeholder_lists:
            for placeholder in placeholder_list:
                if placeholder.name in merged_placeholders:
                    existing = merged_placeholders[placeholder.name]
                    # Check if they are identical
                    if (
                        existing.required != placeholder.required
                        or existing.default_value != placeholder.default_value
                        or existing.description != placeholder.description
                    ):
                        msg = f"Conflicting placeholder definitions for '{placeholder.name}'"
                        raise ValueError(msg)
                    # If identical, keep existing one
                else:
                    merged_placeholders[placeholder.name] = placeholder

        return list(merged_placeholders.values())

    @staticmethod
    def validate_placeholder_value(placeholder: Placeholder, value: str) -> bool:
        """Validate a value against a placeholder's requirements.

        Args:
            placeholder: The placeholder to validate against
            value: The value to validate

        Returns:
            True if the value is valid

        Raises:
            InvalidPlaceholderValueError: If the value is invalid

        """
        try:
            return placeholder.validate_value(value)
        except Exception as e:
            msg = f"Value validation failed for placeholder '{placeholder.name}': {e}"
            raise InvalidPlaceholderValueError(msg, placeholder_name=placeholder.name, provided_value=value) from e

    @staticmethod
    def create_placeholder_value(placeholder_name: str, value: str, source: str = 'user_input') -> PlaceholderValue:
        """Create a PlaceholderValue object.

        Args:
            placeholder_name: Name of the placeholder
            value: Value provided
            source: Source of the value ('user_input', 'default', 'config', 'computed')

        Returns:
            New PlaceholderValue instance

        Raises:
            InvalidPlaceholderValueError: If the value or source is invalid

        """
        try:
            return PlaceholderValue(placeholder_name=placeholder_name, value=value, source=source)
        except Exception as e:
            msg = f"Failed to create placeholder value for '{placeholder_name}': {e}"
            raise InvalidPlaceholderValueError(msg, placeholder_name=placeholder_name, provided_value=value) from e

    @staticmethod
    def get_effective_value(placeholder: Placeholder, provided_value: str | None = None) -> str:
        """Get the effective value for a placeholder.

        Args:
            placeholder: The placeholder to get value for
            provided_value: Value provided by user (optional)

        Returns:
            The value to use (provided value, default, or empty string)

        Raises:
            InvalidPlaceholderValueError: If required placeholder has no value

        """
        try:
            return placeholder.get_effective_value(provided_value)
        except Exception as e:
            msg = f"Failed to get effective value for placeholder '{placeholder.name}': {e}"
            raise InvalidPlaceholderValueError(
                msg, placeholder_name=placeholder.name, provided_value=provided_value
            ) from e

    def replace_placeholder_in_text(self, text: str, placeholder: Placeholder, value: str) -> str:
        """Replace a placeholder in text with a value.

        Args:
            text: The text to replace placeholder in
            placeholder: The placeholder to replace
            value: The replacement value

        Returns:
            Text with placeholder replaced

        Raises:
            InvalidPlaceholderValueError: If value is invalid
            InvalidPlaceholderError: If placeholder pattern is invalid

        """
        # Validate the value first
        self.validate_placeholder_value(placeholder, value)

        try:
            return placeholder.pattern_obj.replace_in_text(text, value)
        except Exception as e:
            msg = f"Failed to replace placeholder '{placeholder.name}' in text: {e}"
            raise InvalidPlaceholderError(msg, placeholder_pattern=placeholder.pattern) from e

    def replace_all_placeholders_in_text(self, text: str, placeholder_values: dict[str, str]) -> str:
        """Replace all placeholders in text with provided values.

        Args:
            text: The text to replace placeholders in
            placeholder_values: Dictionary mapping placeholder names to values

        Returns:
            Text with all placeholders replaced

        Raises:
            InvalidPlaceholderError: If any placeholder pattern is invalid
            InvalidPlaceholderValueError: If any value is invalid

        """
        result = text

        # Extract all placeholders from the text
        placeholders = self.extract_placeholders_from_text(text)

        # Replace each placeholder
        for placeholder in placeholders:
            if placeholder.name in placeholder_values:
                value = placeholder_values[placeholder.name]
                result = self.replace_placeholder_in_text(result, placeholder, value)
            elif placeholder.required:
                msg = f"Missing value for required placeholder '{placeholder.name}'"
                raise InvalidPlaceholderValueError(msg, placeholder_name=placeholder.name)
            else:
                # Use default value for optional placeholder
                default_value = placeholder.get_effective_value()
                result = self.replace_placeholder_in_text(result, placeholder, default_value)

        return result

    @staticmethod
    def get_placeholder_summary(placeholders: list[Placeholder]) -> dict[str, Any]:
        """Get a summary of placeholder information.

        Args:
            placeholders: List of placeholders to summarize

        Returns:
            Dictionary containing placeholder summary information

        """
        required_placeholders = [p for p in placeholders if p.required]
        optional_placeholders = [p for p in placeholders if not p.required]

        return {
            'total_count': len(placeholders),
            'required_count': len(required_placeholders),
            'optional_count': len(optional_placeholders),
            'required_names': [p.name for p in required_placeholders],
            'optional_names': [p.name for p in optional_placeholders],
            'all_names': [p.name for p in placeholders],
            'placeholders_with_defaults': [p.name for p in placeholders if p.has_default],
            'placeholders_with_descriptions': [p.name for p in placeholders if p.description],
        }
