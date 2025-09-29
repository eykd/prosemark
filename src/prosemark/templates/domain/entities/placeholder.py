"""Placeholder entity and related value objects for template placeholders."""

from dataclasses import dataclass

from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    InvalidPlaceholderValueError,
)
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


@dataclass(frozen=True)
class Placeholder:
    """Represents a placeholder within a template that requires user input.

    A placeholder is defined by its pattern (e.g., "{{variable_name}}") and
    metadata about how it should be handled during template instantiation.
    """

    name: str
    pattern_obj: PlaceholderPattern
    required: bool = True
    default_value: str | None = None
    description: str | None = None

    @property
    def pattern(self) -> str:
        """Get the string representation of the pattern."""
        return self.pattern_obj.raw

    def __post_init__(self) -> None:
        """Validate placeholder properties after initialization."""
        # Validate the pattern
        if not self.pattern_obj.name:
            msg = f'Invalid placeholder pattern: {self.pattern}'
            raise InvalidPlaceholderError(msg, placeholder_pattern=self.pattern)

        # Ensure name matches pattern
        if self.pattern_obj.name != self.name:
            msg = f"Placeholder name '{self.name}' does not match pattern '{self.pattern}'"
            raise InvalidPlaceholderError(msg, placeholder_pattern=self.pattern)

        # Validate required/default_value consistency
        if self.required and self.default_value is not None:
            msg = f"Required placeholder '{self.name}' cannot have a default value"
            raise InvalidPlaceholderError(msg, placeholder_pattern=self.pattern)

        if not self.required and self.default_value is None:
            # Optional placeholders should have defaults, but we'll allow None
            # and treat it as an empty string default
            object.__setattr__(self, 'default_value', '')

        # Validate default value if provided
        if self.default_value is not None and not isinstance(self.default_value, str):
            msg = f"Default value for placeholder '{self.name}' must be a string"
            raise InvalidPlaceholderError(msg, placeholder_pattern=self.pattern)

    @property
    def has_default(self) -> bool:
        """Check if this placeholder has a default value."""
        return self.default_value is not None

    @classmethod
    def from_pattern(
        cls,
        pattern: str,
        *,  # keyword-only arguments for clarity and to prevent default behavior confusion
        required: bool = True,  # Controls whether this placeholder must have a value
        default_value: str | None = None,  # Optional default if not required
        description: str | None = None,  # Optional human-readable explanation
    ) -> 'Placeholder':
        """Create a Placeholder from a pattern string.

        Args:
            pattern: The placeholder pattern (e.g., "{{variable_name}}")
            required: Whether this placeholder requires user input
            default_value: Optional default value if not required
            description: Optional human-readable description

        Returns:
            New Placeholder instance

        Raises:
            InvalidPlaceholderError: If the pattern is invalid

        """
        pattern_obj = PlaceholderPattern(pattern)
        return cls(
            name=pattern_obj.name,
            pattern_obj=pattern_obj,
            required=required,
            default_value=default_value,
            description=description,
        )

    @classmethod
    def from_name(
        cls,
        name: str,
        *,  # keyword-only arguments for clarity and to prevent default behavior confusion
        required: bool = True,  # Controls whether this placeholder must have a value
        default_value: str | None = None,  # Optional default if not required
        description: str | None = None,  # Optional human-readable explanation
    ) -> 'Placeholder':
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
        pattern_obj = PlaceholderPattern.from_name(name)
        return cls(
            name=name, pattern_obj=pattern_obj, required=required, default_value=default_value, description=description
        )

    @classmethod
    def from_frontmatter(cls, name: str, frontmatter: dict[str, str], pattern_obj: PlaceholderPattern) -> 'Placeholder':
        """Create a Placeholder from frontmatter data.

        Args:
            name: The placeholder name
            frontmatter: The frontmatter dictionary containing placeholder metadata
            pattern_obj: The PlaceholderPattern object for this placeholder

        Returns:
            New Placeholder instance

        """
        # Check for default value in frontmatter
        default_key = f'{name}_default'
        default_value = frontmatter.get(default_key)

        # Check for description in frontmatter
        description_key = f'{name}_description'
        description = frontmatter.get(description_key)

        # Determine if required (no default value means required)
        required = default_value is None

        return cls(
            name=name, pattern_obj=pattern_obj, required=required, default_value=default_value, description=description
        )

    def validate_value(self, value: str) -> bool:
        """Validate a potential value for this placeholder.

        Args:
            value: The value to validate

        Returns:
            True if the value is valid for this placeholder

        Raises:
            InvalidPlaceholderValueError: If the value is invalid

        """
        if not isinstance(value, str):
            msg = f'Placeholder value must be a string, got {type(value).__name__}'
            raise InvalidPlaceholderValueError(msg, placeholder_name=self.name, provided_value=str(value))

        if self.required and not value.strip():
            msg = f'Empty value for required placeholder: {self.name}'
            raise InvalidPlaceholderValueError(msg, placeholder_name=self.name, provided_value=value)

        # Additional validation could be added here based on placeholder type
        # For now, any non-empty string is valid for required placeholders
        return True

    def get_effective_value(self, provided_value: str | None = None) -> str:
        """Get the effective value for this placeholder.

        Args:
            provided_value: Value provided by user (optional)

        Returns:
            The value to use (provided value, default, or empty string)

        Raises:
            InvalidPlaceholderValueError: If required placeholder has no value

        """
        if provided_value is not None:
            self.validate_value(provided_value)
            return provided_value

        if self.required:
            msg = f'Missing value for required placeholder: {self.name}'
            raise InvalidPlaceholderValueError(msg, placeholder_name=self.name)

        return self.default_value or ''


@dataclass(frozen=True)
class PlaceholderValue:
    """Represents a value provided for a placeholder during template instantiation."""

    placeholder_name: str
    value: str
    source: str = 'user_input'

    def __post_init__(self) -> None:
        """Validate placeholder value properties."""
        if not isinstance(self.placeholder_name, str) or not self.placeholder_name:
            raise InvalidPlaceholderValueError(
                'Placeholder name must be a non-empty string', placeholder_name=self.placeholder_name
            )

        if not isinstance(self.value, str):
            msg = f'Placeholder value must be a string, got {type(self.value).__name__}'
            raise InvalidPlaceholderValueError(
                msg, placeholder_name=self.placeholder_name, provided_value=str(self.value)
            )

        valid_sources = {'user_input', 'default', 'config', 'computed'}
        if self.source not in valid_sources:
            msg = f"Invalid value source '{self.source}'. Must be one of: {', '.join(valid_sources)}"
            raise InvalidPlaceholderValueError(msg, placeholder_name=self.placeholder_name)

    @property
    def is_user_provided(self) -> bool:
        """Check if this value was provided by the user."""
        return self.source == 'user_input'

    @property
    def is_default_value(self) -> bool:
        """Check if this value is a default value."""
        return self.source == 'default'

    @property
    def is_empty(self) -> bool:
        """Check if this value is empty."""
        return not self.value.strip()

    @classmethod
    def from_user_input(cls, placeholder_name: str, value: str) -> 'PlaceholderValue':
        """Create a PlaceholderValue from user input.

        Args:
            placeholder_name: Name of the placeholder
            value: Value provided by user

        Returns:
            New PlaceholderValue instance

        """
        return cls(placeholder_name=placeholder_name, value=value, source='user_input')

    @classmethod
    def from_default(cls, placeholder_name: str, value: str) -> 'PlaceholderValue':
        """Create a PlaceholderValue from a default value.

        Args:
            placeholder_name: Name of the placeholder
            value: Default value

        Returns:
            New PlaceholderValue instance

        """
        return cls(placeholder_name=placeholder_name, value=value, source='default')

    @classmethod
    def from_config(cls, placeholder_name: str, value: str) -> 'PlaceholderValue':
        """Create a PlaceholderValue from configuration.

        Args:
            placeholder_name: Name of the placeholder
            value: Value from configuration

        Returns:
            New PlaceholderValue instance

        """
        return cls(placeholder_name=placeholder_name, value=value, source='config')

    def matches_placeholder(self, placeholder: Placeholder) -> bool:
        """Check if this value matches the given placeholder.

        Args:
            placeholder: Placeholder to check against

        Returns:
            True if this value is for the given placeholder

        """
        return self.placeholder_name == placeholder.name
