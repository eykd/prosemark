"""Prosemark-specific template validator adapter."""

from typing import Any

import yaml

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import InvalidPlaceholderValueError
from prosemark.templates.ports.template_validator_port import TemplateValidatorPort


class ProsemarkTemplateValidator(TemplateValidatorPort):
    """Prosemark-specific implementation of template validator."""

    def validate_template(self, template: Template) -> list[str]:
        """Validate a single template against prosemark standards.

        Args:
            template: Template to validate

        Returns:
            List of validation error messages (empty if valid)

        """
        errors: list[str] = []

        # Validate basic template structure
        errors.extend(self._validate_template_structure(template))

        # Validate prosemark-specific requirements
        errors.extend(self._validate_prosemark_format(template))

        # Validate placeholder consistency
        errors.extend(self._validate_placeholder_consistency(template))

        return errors

    def validate_template_directory(self, template_directory: TemplateDirectory) -> list[str]:
        """Validate a template directory against prosemark standards.

        Args:
            template_directory: Template directory to validate

        Returns:
            List of validation error messages (empty if valid)

        """
        errors: list[str] = []

        # Validate each template in the directory
        for template in template_directory.templates:
            template_errors = self.validate_template(template)
            errors.extend(f"Template '{template.name}': {error}" for error in template_errors)

        # Validate directory-specific requirements
        errors.extend(self._validate_directory_consistency(template_directory))

        return errors

    @staticmethod
    def validate_placeholder_values(template: Template, values: dict[str, str]) -> list[str]:
        """Validate placeholder values for a template.

        Args:
            template: Template to validate values against
            values: Dictionary of placeholder values to validate

        Returns:
            List of validation error messages (empty if valid)

        """
        errors: list[str] = []

        # Check that all required placeholders have values
        for placeholder in template.required_placeholders:
            if placeholder.name not in values:
                errors.append(f'Missing value for required placeholder: {placeholder.name}')
            else:
                # Validate the value
                try:
                    placeholder.validate_value(values[placeholder.name])
                except (InvalidPlaceholderValueError, ValueError) as e:
                    errors.append(str(e))

        # Check for unexpected placeholder values
        template_placeholder_names = {p.name for p in template.placeholders}
        errors.extend(f'Unknown placeholder: {name}' for name in values if name not in template_placeholder_names)

        return errors

    def _validate_template_structure(self, template: Template) -> list[str]:
        """Validate basic template structure.

        Args:
            template: Template to validate

        Returns:
            List of validation errors

        """
        errors: list[str] = []

        # Must have frontmatter
        if not template.frontmatter:
            errors.append('Template must have YAML frontmatter')

        # Must have body content
        if not template.body.strip():
            errors.append('Template must have body content')

        # Content must be valid markdown structure
        errors.extend(self._validate_content_structure(template))

        return errors

    def _validate_prosemark_format(self, template: Template) -> list[str]:
        """Validate prosemark-specific format requirements.

        Args:
            template: Template to validate

        Returns:
            List of validation errors

        """
        errors: list[str] = []

        # Validate YAML frontmatter structure
        if template.frontmatter:
            errors.extend(self._validate_yaml_frontmatter(template.frontmatter))

        # Validate that body starts with a heading (prosemark convention)
        if template.body.strip():
            lines = [line.strip() for line in template.body.strip().split('\n') if line.strip()]
            if lines and not lines[0].startswith('#'):
                # This is a warning for prosemark, not a hard error
                # Could be made configurable based on strictness level
                pass

        return errors

    def _validate_placeholder_consistency(self, template: Template) -> list[str]:
        """Validate placeholder usage consistency.

        Args:
            template: Template to validate

        Returns:
            List of validation errors

        """
        # Validate that all placeholders in frontmatter have corresponding patterns in content
        frontmatter_str = yaml.safe_dump(template.frontmatter)
        all_content = frontmatter_str + template.body

        errors = [
            f"Placeholder '{placeholder.name}' defined but not used in template"
            for placeholder in template.placeholders
            if not placeholder.pattern_obj.matches_text(all_content)
        ]

        # Validate placeholder naming conventions
        errors.extend(
            f"Placeholder name '{placeholder.name}' violates naming conventions"
            for placeholder in template.placeholders
            if not self._is_valid_placeholder_name(placeholder.name)
        )

        return errors

    @staticmethod
    def _validate_directory_consistency(template_directory: TemplateDirectory) -> list[str]:
        """Validate directory-specific consistency requirements.

        Args:
            template_directory: Template directory to validate

        Returns:
            List of validation errors

        """
        errors: list[str] = []

        # Check for shared placeholder consistency
        shared_placeholders = template_directory.shared_placeholders

        for shared_placeholder in shared_placeholders:
            # Find all instances of this placeholder across templates
            placeholder_instances = []
            for template in template_directory.templates:
                placeholder = template.get_placeholder_by_name(shared_placeholder.name)
                if placeholder:
                    placeholder_instances.append((template.name, placeholder))

            # Validate consistency across instances
            if len(placeholder_instances) > 1:
                first_template_name, first_placeholder = placeholder_instances[0]

                for template_name, placeholder in placeholder_instances[1:]:
                    # Check required/optional consistency
                    if placeholder.required != first_placeholder.required:
                        errors.append(
                            f"Placeholder '{placeholder.name}' has inconsistent required status "
                            f"between templates '{first_template_name}' and '{template_name}'"
                        )

                    # Check default value consistency
                    if placeholder.default_value != first_placeholder.default_value:
                        errors.append(
                            f"Placeholder '{placeholder.name}' has inconsistent default values "
                            f"between templates '{first_template_name}' and '{template_name}'"
                        )

        return errors

    @staticmethod
    def _validate_content_structure(template: Template) -> list[str]:
        """Validate markdown content structure.

        Args:
            template: Template to validate

        Returns:
            List of validation errors

        """
        errors: list[str] = []

        # Check for malformed markdown structures
        content = template.body

        # Basic markdown validation could be added here
        # For now, we'll keep it simple and just check for basic issues

        # Check for unclosed code blocks
        if content.count('```') % 2 != 0:
            errors.append('Template contains unclosed code blocks')

        # Check for malformed placeholder patterns
        import re

        malformed_patterns = re.findall(r'\{[^{}]*\}(?!\})', content)
        malformed_patterns.extend(re.findall(r'(?<!\{)\{[^{}]*\}', content))

        # Filter out valid patterns
        valid_pattern = re.compile(r'\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}')
        truly_malformed = [pattern for pattern in malformed_patterns if not valid_pattern.match(pattern)]

        if truly_malformed:
            errors.append(f'Template contains malformed placeholder patterns: {truly_malformed}')

        return errors

    def _validate_yaml_frontmatter(self, frontmatter: dict[str, Any]) -> list[str]:
        """Validate YAML frontmatter structure.

        Args:
            frontmatter: Parsed frontmatter dictionary

        Returns:
            List of validation errors

        """
        errors: list[str] = []

        # Validate that frontmatter is a dictionary
        if not isinstance(frontmatter, dict):
            errors.append('YAML frontmatter must be a dictionary')
            return errors

        # Check for reserved keys that might conflict with prosemark
        reserved_keys = {'id', 'created', 'modified', 'type'}
        errors.extend(f'Frontmatter contains reserved key: {key}' for key in frontmatter if key in reserved_keys)

        # Validate placeholder-related keys
        for key, value in frontmatter.items():
            if key.endswith('_default'):
                placeholder_name = key[:-8]  # Remove '_default'
                if not self._is_valid_placeholder_name(placeholder_name):
                    errors.append(f'Invalid placeholder name in default key: {placeholder_name}')
                if not isinstance(value, str):
                    errors.append(f'Default value for {placeholder_name} must be a string')

            elif key.endswith('_description'):
                placeholder_name = key[:-12]  # Remove '_description'
                if not self._is_valid_placeholder_name(placeholder_name):
                    errors.append(f'Invalid placeholder name in description key: {placeholder_name}')
                if not isinstance(value, str):
                    errors.append(f'Description for {placeholder_name} must be a string')

        return errors

    @staticmethod
    def _is_valid_placeholder_name(name: str) -> bool:
        """Check if a placeholder name follows naming conventions.

        Args:
            name: Placeholder name to validate

        Returns:
            True if name is valid, False otherwise

        """
        import re

        # Must start with letter or underscore, followed by letters, digits, or underscores
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        return bool(pattern.match(name))

    @staticmethod
    def validate_template_structure(content: str) -> bool:
        """Validate that template content has valid structure.

        Args:
            content: Raw template content

        Returns:
            True if structure is valid

        """
        # Basic structure checks
        if not content.startswith('---'):
            return False

        try:
            # Try to split and parse frontmatter
            parts = content.split('---', 2)
            min_frontmatter_parts = 3
            if len(parts) < min_frontmatter_parts:
                return False

            frontmatter_text = parts[1].strip()
            body_text = parts[2].lstrip('\n')

            # Parse YAML frontmatter
            if frontmatter_text:
                try:
                    parsed_frontmatter = yaml.safe_load(frontmatter_text)
                    if parsed_frontmatter is None:
                        parsed_frontmatter = {}
                    if not isinstance(parsed_frontmatter, dict):
                        return False
                except yaml.YAMLError:
                    return False

            # Must have body content
            return bool(body_text.strip())
        except (ValueError, yaml.YAMLError, AttributeError):
            return False

    def validate_prosemark_format(self, content: str) -> bool:
        """Validate that template follows prosemark node format.

        Args:
            content: Raw template content

        Returns:
            True if format is valid

        """
        try:
            # Basic format validation - should have frontmatter and body
            # Additional prosemark-specific checks could go here
            return self.validate_template_structure(content)
        except (ValueError, yaml.YAMLError, AttributeError):
            return False

    @staticmethod
    def extract_placeholders(content: str) -> list[Placeholder]:
        """Extract all placeholders from template content.

        Args:
            content: Template content containing placeholders

        Returns:
            List of Placeholder instances found in content

        """
        from prosemark.templates.domain.services.placeholder_service import PlaceholderService

        service = PlaceholderService()
        return service.extract_placeholders_from_text(content)

    @staticmethod
    def validate_placeholder_syntax(placeholder_text: str) -> bool:
        """Validate that a placeholder has correct syntax.

        Args:
            placeholder_text: Placeholder pattern (e.g., "{{variable_name}}")

        Returns:
            True if syntax is valid

        """
        try:
            from prosemark.templates.domain.services.placeholder_service import PlaceholderService

            service = PlaceholderService()
            return service.validate_placeholder_pattern(placeholder_text)
        except (ValueError, yaml.YAMLError, AttributeError):
            return False

    def validate_template_dependencies(self, template: Template) -> bool:
        """Validate that template dependencies are resolvable.

        Args:
            template: Template to validate dependencies for

        Returns:
            True if all dependencies are valid

        """
        # Basic dependency validation - check that placeholders are well-formed
        try:
            return all(self.validate_placeholder_syntax(placeholder.pattern) for placeholder in template.placeholders)
        except (ValueError, yaml.YAMLError, AttributeError):
            return False
