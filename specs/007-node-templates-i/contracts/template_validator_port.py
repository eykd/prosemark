"""Template Validator Port Contract.

Defines the interface for template content validation operations.
"""

from abc import ABC, abstractmethod

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.entities.template import Template


class TemplateValidatorPort(ABC):
    """Port for template content validation operations."""

    @abstractmethod
    def validate_template_structure(self, content: str) -> bool:
        """Validate that template content has valid structure.

        Args:
            content: Raw template content

        Returns:
            True if structure is valid

        Raises:
            TemplateParseError: If YAML frontmatter is invalid
            TemplateValidationError: If content violates prosemark format

        """

    @abstractmethod
    def validate_prosemark_format(self, content: str) -> bool:
        """Validate that template follows prosemark node format.

        Args:
            content: Raw template content

        Returns:
            True if format is valid

        Raises:
            TemplateValidationError: If content violates prosemark format requirements

        """

    @abstractmethod
    def extract_placeholders(self, content: str) -> list[Placeholder]:
        """Extract all placeholders from template content.

        Args:
            content: Template content containing placeholders

        Returns:
            List of Placeholder instances found in content

        Raises:
            InvalidPlaceholderError: If placeholder syntax is malformed

        """

    @abstractmethod
    def validate_placeholder_syntax(self, placeholder_text: str) -> bool:
        """Validate that a placeholder has correct syntax.

        Args:
            placeholder_text: Placeholder pattern (e.g., "{{variable_name}}")

        Returns:
            True if syntax is valid

        Raises:
            InvalidPlaceholderError: If syntax is malformed

        """

    @abstractmethod
    def validate_template_dependencies(self, template: Template) -> bool:
        """Validate that template dependencies are resolvable.

        Args:
            template: Template to validate dependencies for

        Returns:
            True if all dependencies are valid

        Raises:
            TemplateValidationError: If dependencies cannot be resolved

        """
