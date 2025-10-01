"""Template entity representing a prosemark template file."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    TemplateParseError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern
from prosemark.templates.domain.values.template_path import TemplatePath


@dataclass(frozen=True)
class Template:
    """Represents a template file that can be used to create nodes.

    A template contains YAML frontmatter and markdown content with placeholders
    that can be replaced with user-provided values during instantiation.
    """

    name: str
    path: TemplatePath
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ''
    placeholders: list[Placeholder] = field(default_factory=list)
    is_directory_template: bool = False

    def __post_init__(self) -> None:
        """Parse and validate template content after initialization."""
        # Parse content if frontmatter and body are not provided
        if not self.frontmatter and not self.body and self.content:
            self._parse_content()

        # Validate the template
        self._validate()

    def _parse_content(self) -> None:
        """Parse the template content into frontmatter and body."""
        if not self.content.startswith('---'):
            raise TemplateValidationError('Template must have YAML frontmatter', template_path=str(self.path))

        try:
            # Split content into frontmatter and body
            # We expect exactly 3 parts: content before ---, frontmatter, content after ---
            min_frontmatter_parts = 3
            parts = self.content.split('---', 2)
            if len(parts) < min_frontmatter_parts:
                raise TemplateParseError(
                    'Template must have proper YAML frontmatter delimited by ---', template_path=str(self.path)
                )

            frontmatter_text = parts[1].strip()
            body_text = parts[2].lstrip('\n')

            # Parse YAML frontmatter
            if frontmatter_text:
                try:
                    parsed_frontmatter = yaml.safe_load(frontmatter_text)
                    if parsed_frontmatter is None:
                        parsed_frontmatter = {}
                    if not isinstance(parsed_frontmatter, dict):
                        raise TemplateParseError('YAML frontmatter must be a dictionary', template_path=str(self.path))
                except yaml.YAMLError as e:
                    msg = f'Invalid YAML frontmatter: {e}'
                    raise TemplateParseError(msg, template_path=str(self.path)) from e
            else:
                parsed_frontmatter = {}

            # Update frontmatter first so it's available during placeholder extraction
            object.__setattr__(self, 'frontmatter', parsed_frontmatter)
            object.__setattr__(self, 'body', body_text)

            # Extract placeholders from both frontmatter and body (now that frontmatter is set)
            placeholders = self._extract_placeholders(frontmatter_text + body_text)
            object.__setattr__(self, 'placeholders', placeholders)

        except (ValueError, AttributeError) as e:  # pragma: no cover
            msg = f'Error parsing template content: {e}'
            raise TemplateParseError(msg, template_path=str(self.path)) from e

    def _extract_placeholders(self, text: str) -> list[Placeholder]:
        """Extract all placeholders from template text.

        Args:
            text: The text to extract placeholders from

        Returns:
            List of unique Placeholder objects

        """
        try:
            patterns = PlaceholderPattern.extract_all_from_text(text)
        except InvalidPlaceholderError:
            # Let placeholder errors bubble up as-is
            raise
        except Exception as e:  # pragma: no cover
            msg = f'Error extracting placeholders: {e}'
            raise TemplateParseError(msg, template_path=str(self.path)) from e

        # Convert patterns to Placeholder objects
        placeholders = []
        seen_names = set()

        for pattern in patterns:
            if pattern.name not in seen_names:
                # Check if this placeholder has a default value in frontmatter
                default_key = f'{pattern.name}_default'
                default_value = None
                required = True

                if default_key in self.frontmatter:
                    default_value = str(self.frontmatter[default_key])
                    required = False

                # Check for description in frontmatter
                desc_key = f'{pattern.name}_description'
                description = self.frontmatter.get(desc_key)

                placeholder = Placeholder(
                    name=pattern.name,
                    pattern_obj=pattern,
                    required=required,
                    default_value=default_value,
                    description=description,
                )

                placeholders.append(placeholder)
                seen_names.add(pattern.name)

        return placeholders

    def _validate(self) -> None:
        """Validate the template for prosemark compliance."""
        # Must have frontmatter
        if not self.frontmatter:
            raise TemplateValidationError('Template must have YAML frontmatter', template_path=str(self.path))

        # Must have body content
        if not self.body.strip():
            raise TemplateValidationError('Template must have body content', template_path=str(self.path))

        # Body should start with a heading (prosemark convention)
        body_lines = [line.strip() for line in self.body.strip().split('\n') if line.strip()]
        if body_lines and not body_lines[0].startswith('#'):
            # This is a warning rather than an error for flexibility
            pass

        # Validate that all placeholders in frontmatter have corresponding patterns in content
        frontmatter_str = yaml.safe_dump(self.frontmatter)
        all_patterns_text = frontmatter_str + self.body

        for placeholder in self.placeholders:
            if not placeholder.pattern_obj.matches_text(all_patterns_text):
                msg = f"Placeholder '{placeholder.name}' defined but not used in template"
                raise TemplateValidationError(msg, template_path=str(self.path))

    @property
    def template_name(self) -> str:
        """Get the template name (alias for name property)."""
        return self.name

    @property
    def file_path(self) -> Path:
        """Get the file system path to the template."""
        return self.path.value

    @property
    def has_placeholders(self) -> bool:
        """Check if this template has any placeholders."""
        return len(self.placeholders) > 0

    @property
    def required_placeholders(self) -> list[Placeholder]:
        """Get list of placeholders that require user input."""
        return [p for p in self.placeholders if p.required]

    @property
    def optional_placeholders(self) -> list[Placeholder]:
        """Get list of placeholders with default values."""
        return [p for p in self.placeholders if not p.required]

    @classmethod
    def from_file(cls, path: Path | str) -> 'Template':
        """Create a Template by reading from a file.

        Args:
            path: Path to the template file

        Returns:
            New Template instance

        Raises:
            TemplateNotFoundError: If file does not exist
            TemplateParseError: If file content is invalid
            TemplateValidationError: If template violates prosemark format

        """
        template_path = TemplatePath(path)
        content = template_path.read_content()
        name = template_path.name

        return cls(name=name, path=template_path, content=content)

    @classmethod
    def from_content(
        cls, name: str, content: str, file_path: Path | str | None = None, *, is_directory_template: bool = False
    ) -> 'Template':
        """Create a Template from content string.

        Args:
            name: Template name
            content: Raw template content
            file_path: Optional path to source file
            is_directory_template: Whether this is part of a directory template

        Returns:
            New Template instance

        Raises:
            TemplateParseError: If content is invalid
            TemplateValidationError: If template violates prosemark format

        """
        if file_path:
            path = TemplatePath(file_path)
        else:
            # Create a minimal path object for validation
            from tempfile import NamedTemporaryFile

            with NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_name = temp_file.name

            try:
                path = TemplatePath(temp_file_name)
            finally:
                Path(temp_file_name).unlink()

        return cls(name=name, path=path, content=content, is_directory_template=is_directory_template)

    def get_placeholder_by_name(self, name: str) -> Placeholder | None:
        """Get a placeholder by its name.

        Args:
            name: Placeholder name to search for

        Returns:
            Placeholder if found, None otherwise

        """
        for placeholder in self.placeholders:
            if placeholder.name == name:
                return placeholder
        return None

    def replace_placeholders(self, values: dict[str, str]) -> str:
        """Replace placeholders in template content with provided values.

        Args:
            values: Dictionary mapping placeholder names to replacement values

        Returns:
            Template content with placeholders replaced

        Raises:
            InvalidPlaceholderValueError: If required placeholders are missing

        """
        # Validate that all required placeholders have values
        for placeholder in self.required_placeholders:
            if placeholder.name not in values:
                msg = f"Missing value for required placeholder '{placeholder.name}'"
                raise TemplateParseError(msg, template_path=str(self.path))

        # Start with original content
        result = self.content

        # Replace each placeholder
        for placeholder in self.placeholders:
            value = values[placeholder.name] if placeholder.name in values else placeholder.get_effective_value()

            # Validate the value
            placeholder.validate_value(value)

            # Replace in content
            result = placeholder.pattern_obj.replace_in_text(result, value)

        return result

    def render(self, values: dict[str, str]) -> str:
        """Render template with provided values, using defaults for missing optional placeholders.

        Args:
            values: Dictionary mapping placeholder names to replacement values

        Returns:
            Template content with placeholders replaced

        Raises:
            TemplateValidationError: If required placeholders are missing

        """
        # Validate that all required placeholders have values
        for placeholder in self.required_placeholders:
            if placeholder.name not in values:
                msg = f'Missing value for required placeholder: {placeholder.name}'
                raise TemplateValidationError(msg, template_path=str(self.path))

        # Start with original content
        result = self.content

        # Replace each placeholder
        for placeholder in self.placeholders:
            if placeholder.name in values:
                value = values[placeholder.name]
            elif placeholder.default_value is not None:
                value = placeholder.default_value
            else:  # pragma: no cover
                # This should not happen if validation above passed
                continue

            # Replace in content using the pattern object
            result = placeholder.pattern_obj.replace_in_text(result, value)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary representation.

        Returns:
            Dictionary containing template data

        """
        return {
            'name': self.name,
            'path': str(self.path),
            'has_placeholders': self.has_placeholders,
            'placeholder_count': len(self.placeholders),
            'required_placeholders': [p.name for p in self.required_placeholders],
            'optional_placeholders': [p.name for p in self.optional_placeholders],
            'is_directory_template': self.is_directory_template,
            'frontmatter': self.frontmatter,
        }

    def __str__(self) -> str:
        """Return string representation of template."""
        return f'Template(name={self.name}, path={self.path})'
