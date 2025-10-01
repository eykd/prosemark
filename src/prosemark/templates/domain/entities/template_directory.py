"""TemplateDirectory entity representing a collection of related templates."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.exceptions.template_exceptions import (
    EmptyTemplateDirectoryError,
    InvalidPlaceholderValueError,
    InvalidTemplateDirectoryError,
    TemplateParseError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.directory_path import DirectoryPath


@dataclass(frozen=True)
class TemplateDirectory:
    """Represents a collection of related templates organized as a directory.

    A template directory contains multiple template files that can be used together
    to create a structured set of related nodes with consistent placeholders.
    """

    name: str
    path: DirectoryPath
    templates: list[Template] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate template directory after initialization."""
        # Load templates if not provided
        if not self.templates:
            self._load_templates()

        # Validate the directory
        self._validate()

        # Build structure representation
        if not self.structure:
            self._build_structure()

    def _load_templates(self) -> None:
        """Load all template files from the directory."""
        if not self.path.is_valid_template_directory:
            raise EmptyTemplateDirectoryError(str(self.path))

        templates = []
        invalid_templates = []

        # Load templates recursively
        for template_file in self.path.list_template_files(recursive=True):
            try:
                template = Template.from_file(template_file)
                # Mark as directory template
                object.__setattr__(template, 'is_directory_template', True)
                templates.append(template)
            except (TemplateParseError, TemplateValidationError) as e:
                invalid_templates.append(f'{template_file.name}: {e}')

        if invalid_templates:
            raise InvalidTemplateDirectoryError(str(self.path), invalid_templates)

        if not templates:  # pragma: no cover - defensive check, already validated by is_valid_template_directory
            raise EmptyTemplateDirectoryError(str(self.path))

        object.__setattr__(self, 'templates', templates)

    def _validate(self) -> None:
        """Validate the template directory."""
        if not self.templates:  # pragma: no cover - defensive check, templates loaded by __post_init__
            raise EmptyTemplateDirectoryError(str(self.path))

        # Validate that all templates are valid
        for template in self.templates:
            if not template.path.exists:
                msg = f'Template file no longer exists: {template.path}'
                raise TemplateValidationError(msg, template_path=str(template.path))

        # Check for placeholder consistency across templates
        self._validate_placeholder_consistency()

    def _validate_placeholder_consistency(self) -> None:
        """Validate that shared placeholders are used consistently."""
        # Collect all placeholders by name
        all_placeholders: dict[str, list[Placeholder]] = {}

        for template in self.templates:
            for placeholder in template.placeholders:
                if placeholder.name not in all_placeholders:
                    all_placeholders[placeholder.name] = []
                all_placeholders[placeholder.name].append(placeholder)

        # Check for consistency issues
        for placeholder_name, placeholder_list in all_placeholders.items():
            if len(placeholder_list) > 1:
                # Multiple templates use this placeholder - check consistency
                first_placeholder = placeholder_list[0]

                for placeholder in placeholder_list[1:]:
                    # Check that required/optional status is consistent
                    if placeholder.required != first_placeholder.required:
                        msg = (
                            f"Placeholder '{placeholder_name}' has inconsistent required status "
                            f'across templates in directory'
                        )
                        raise TemplateValidationError(msg, template_path=str(self.path))

                    # Check that default values are consistent
                    if placeholder.default_value != first_placeholder.default_value:
                        msg = (
                            f"Placeholder '{placeholder_name}' has inconsistent default values "
                            f'across templates in directory'
                        )
                        raise TemplateValidationError(msg, template_path=str(self.path))

    def _build_structure(self) -> None:
        """Build a representation of the directory structure."""
        structure: dict[str, Any] = {
            'name': self.name,
            'path': str(self.path),
            'template_count': len(self.templates),
            'templates': [],
            'subdirectories': {},
        }

        # Group templates by their relative paths
        for template in self.templates:
            relative_path = self.path.get_relative_path_to(template.file_path)
            if relative_path:
                # Determine the directory structure
                parts = relative_path.parts
                current_level = structure

                # Navigate to the correct subdirectory level
                for part in parts[:-1]:  # All parts except the filename
                    if 'subdirectories' not in current_level:  # pragma: no cover - defensive check, always initialized
                        current_level['subdirectories'] = {}

                    current_subdirs: dict[str, dict[str, Any]] = current_level['subdirectories']
                    if part not in current_subdirs:
                        current_subdirs[part] = {'name': part, 'templates': [], 'subdirectories': {}}

                    current_level = current_subdirs[part]

                # Add template to the appropriate level
                template_info = {
                    'name': template.name,
                    'path': str(relative_path),
                    'placeholder_count': len(template.placeholders),
                    'required_placeholders': [p.name for p in template.required_placeholders],
                }

                if 'templates' not in current_level:  # pragma: no cover - defensive check, always initialized
                    current_level['templates'] = []
                current_level['templates'].append(template_info)

        object.__setattr__(self, 'structure', structure)

    @property
    def directory_name(self) -> str:
        """Get the directory name (alias for name property)."""
        return self.name

    @property
    def directory_path(self) -> Path:
        """Get the file system path to the directory."""
        return self.path.value

    @property
    def template_count(self) -> int:
        """Get the total number of templates in this directory."""
        return len(self.templates)

    @property
    def all_placeholders(self) -> list[Placeholder]:
        """Get all unique placeholders across all templates."""
        unique_placeholders = {}

        for template in self.templates:
            for placeholder in template.placeholders:
                if placeholder.name not in unique_placeholders:
                    unique_placeholders[placeholder.name] = placeholder

        return list(unique_placeholders.values())

    @property
    def shared_placeholders(self) -> list[Placeholder]:
        """Get placeholders that are used by multiple templates."""
        placeholder_counts: dict[str, int] = {}

        for template in self.templates:
            for placeholder in template.placeholders:
                placeholder_counts[placeholder.name] = placeholder_counts.get(placeholder.name, 0) + 1

        shared: list[Placeholder] = []
        unique_placeholders: dict[str, Placeholder] = {p.name: p for p in self.all_placeholders}

        for name, count in placeholder_counts.items():
            if count > 1:
                shared.append(unique_placeholders[name])

        return shared

    @property
    def required_placeholders(self) -> list[Placeholder]:
        """Get all required placeholders across all templates."""
        return [p for p in self.all_placeholders if p.required]

    @property
    def optional_placeholders(self) -> list[Placeholder]:
        """Get all optional placeholders across all templates."""
        return [p for p in self.all_placeholders if not p.required]

    @classmethod
    def from_directory(cls, path: Path | str) -> 'TemplateDirectory':
        """Create a TemplateDirectory by scanning a directory.

        Args:
            path: Path to the template directory

        Returns:
            New TemplateDirectory instance

        Raises:
            TemplateDirectoryNotFoundError: If directory does not exist
            EmptyTemplateDirectoryError: If directory contains no templates
            InvalidTemplateDirectoryError: If directory contains invalid templates

        """
        directory_path = DirectoryPath(path)
        name = directory_path.name

        return cls(name=name, path=directory_path)

    def get_template_by_name(self, name: str) -> Template | None:
        """Get a template by its name.

        Args:
            name: Template name to search for

        Returns:
            Template if found, None otherwise

        """
        for template in self.templates:
            if template.name == name:
                return template
        return None

    def get_templates_in_subdirectory(self, subdirectory: str) -> list[Template]:
        """Get all templates in a specific subdirectory.

        Args:
            subdirectory: Name of subdirectory

        Returns:
            List of templates in the subdirectory

        """
        subdirectory_path = self.path.value / subdirectory
        return [t for t in self.templates if subdirectory_path in t.file_path.parents]

    def validate_placeholder_values(self, values: dict[str, str]) -> list[str]:
        """Validate placeholder values against all templates.

        Args:
            values: Dictionary of placeholder names to values

        Returns:
            List of validation error messages (empty if valid)

        """
        errors = []

        # Check that all required placeholders have values
        for placeholder in self.required_placeholders:
            if placeholder.name not in values:
                errors.append(f'Missing value for required placeholder: {placeholder.name}')
            else:
                try:
                    placeholder.validate_value(values[placeholder.name])
                except (InvalidPlaceholderValueError, ValueError) as e:
                    errors.append(str(e))

        return errors

    def replace_placeholders_in_all(self, values: dict[str, str]) -> dict[str, str]:
        """Replace placeholders in all templates with provided values.

        Args:
            values: Dictionary mapping placeholder names to replacement values

        Returns:
            Dictionary mapping template names to their content with placeholders replaced

        Raises:
            InvalidPlaceholderValueError: If placeholder validation fails

        """
        # Validate values first
        validation_errors = self.validate_placeholder_values(values)
        if validation_errors:
            msg = f'Placeholder validation failed: {"; ".join(validation_errors)}'
            raise TemplateValidationError(msg, template_path=str(self.path))

        # Replace placeholders in each template
        results = {}
        for template in self.templates:
            try:
                results[template.name] = template.replace_placeholders(values)
            except Exception as e:
                msg = f"Failed to replace placeholders in template '{template.name}': {e}"
                raise TemplateValidationError(msg, template_path=str(template.path)) from e

        return results

    def to_dict(self) -> dict[str, Any]:
        """Convert template directory to dictionary representation.

        Returns:
            Dictionary containing directory data

        """
        return {
            'name': self.name,
            'path': str(self.path),
            'template_count': self.template_count,
            'templates': [t.to_dict() for t in self.templates],
            'structure': self.structure,
            'all_placeholders': [p.name for p in self.all_placeholders],
            'shared_placeholders': [p.name for p in self.shared_placeholders],
            'required_placeholders': [p.name for p in self.required_placeholders],
            'optional_placeholders': [p.name for p in self.optional_placeholders],
        }
