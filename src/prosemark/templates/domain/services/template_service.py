"""Template service providing core business logic for template operations."""

from typing import Any

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderValueError,
    PlaceholderProcessingError,
    TemplateError,
    TemplateValidationError,
)
from prosemark.templates.ports.template_repository_port import TemplateRepositoryPort
from prosemark.templates.ports.template_validator_port import TemplateValidatorPort
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class TemplateService:
    """Service providing template operations and business logic."""

    def __init__(
        self,
        repository: TemplateRepositoryPort,
        validator: TemplateValidatorPort,
        prompter: UserPrompterPort,
    ) -> None:
        """Initialize template service with required dependencies.

        Args:
            repository: Template storage and retrieval interface
            validator: Template validation interface
            prompter: User interaction interface

        """
        self.repository = repository
        self.validator = validator
        self.prompter = prompter

    def create_from_template(self, template_name: str, placeholder_values: dict[str, str] | None = None) -> str:
        """Create content from a template with placeholder replacement.

        Args:
            template_name: Name of template to use
            placeholder_values: Optional predefined placeholder values

        Returns:
            Generated content with placeholders replaced

        Raises:
            TemplateNotFoundError: If template doesn't exist
            InvalidPlaceholderValueError: If required placeholders missing
            TemplateValidationError: If template is invalid
            PlaceholderProcessingError: If placeholder replacement fails

        """
        # Load template
        template = self.repository.get_template(template_name)

        # Validate template
        validation_errors = self.validator.validate_template(template)
        if validation_errors:
            msg = f'Template validation failed: {"; ".join(validation_errors)}'
            raise TemplateValidationError(msg, template_path=str(template.path))

        # Collect all required placeholder values
        final_values = self._collect_placeholder_values(template, placeholder_values or {})

        # Replace placeholders and return content
        try:
            return template.replace_placeholders(final_values)
        except TemplateError as e:
            msg = f"Failed to process placeholders in template '{template_name}': {e}"
            raise PlaceholderProcessingError(msg, template_path=str(template.path)) from e

    def create_from_directory_template(
        self, template_directory_name: str, placeholder_values: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Create multiple files from a directory template.

        Args:
            template_directory_name: Name of template directory to use
            placeholder_values: Optional predefined placeholder values

        Returns:
            Dictionary mapping relative file paths to generated content

        Raises:
            TemplateDirectoryNotFoundError: If template directory doesn't exist
            InvalidPlaceholderValueError: If required placeholders missing
            TemplateValidationError: If any template is invalid
            PlaceholderProcessingError: If placeholder replacement fails

        """
        # Load template directory
        template_directory = self.repository.get_template_directory(template_directory_name)

        # Validate directory and all templates
        validation_errors = self.validator.validate_template_directory(template_directory)
        if validation_errors:
            msg = f'Template directory validation failed: {"; ".join(validation_errors)}'
            raise TemplateValidationError(msg, template_path=str(template_directory.path))

        # Collect all required placeholder values for the entire directory
        final_values = self._collect_directory_placeholder_values(template_directory, placeholder_values or {})

        # Replace placeholders in all templates
        try:
            return template_directory.replace_placeholders_in_all(final_values)
        except TemplateError as e:
            msg = f"Failed to process placeholders in directory template '{template_directory_name}': {e}"
            raise PlaceholderProcessingError(msg, template_path=str(template_directory.path)) from e

    def get_template_info(self, template_name: str) -> dict[str, Any]:
        """Get detailed information about a template.

        Args:
            template_name: Name of template to inspect

        Returns:
            Dictionary containing template metadata and placeholder information

        Raises:
            TemplateNotFoundError: If template doesn't exist

        """
        template = self.repository.get_template(template_name)
        return template.to_dict()

    def get_directory_template_info(self, template_directory_name: str) -> dict[str, Any]:
        """Get detailed information about a directory template.

        Args:
            template_directory_name: Name of template directory to inspect

        Returns:
            Dictionary containing directory metadata and placeholder information

        Raises:
            TemplateDirectoryNotFoundError: If template directory doesn't exist

        """
        template_directory = self.repository.get_template_directory(template_directory_name)
        return template_directory.to_dict()

    def list_templates(self) -> list[str]:
        """List all available single template names.

        Returns:
            List of template names available for use

        """
        # Use templates root as search path
        templates_root = self.repository.get_templates_root()
        templates = self.repository.list_templates(templates_root)
        return [template.name for template in templates]

    def list_template_directories(self) -> list[str]:
        """List all available template directory names.

        Returns:
            List of template directory names available for use

        """
        # Use templates root as search path
        templates_root = self.repository.get_templates_root()
        template_directories = self.repository.list_template_directories(templates_root)
        return [template_dir.name for template_dir in template_directories]

    def create_content_from_single_template(
        self, template_name: str, placeholder_values: dict[str, str] | None = None, *, interactive: bool = True
    ) -> dict[str, Any]:
        """Create content from a single template with optional interactivity.

        Args:
            template_name: Name of template to use
            placeholder_values: Optional predefined placeholder values
            interactive: Whether to prompt user for missing values

        Returns:
            Dictionary with success status and result/error details

        """
        try:
            # Load template
            template = self.repository.get_template(template_name)

            # Validate template
            validation_errors = self.validator.validate_template(template)
            if validation_errors:
                error_message = f'Template validation failed: {"; ".join(validation_errors)}'
                return {
                    'success': False,
                    'template_name': template_name,
                    'error_type': 'TemplateValidationError',
                    'error_message': error_message,
                    'error': error_message,  # For backward compatibility with some tests
                }

            provided_values = placeholder_values or {}

            if interactive:
                # Collect missing values interactively
                final_values = self._collect_placeholder_values(template, provided_values)
            else:
                # Non-interactive mode - validate we have all required values
                final_values = provided_values.copy()

                # Check for missing required placeholders
                missing_required = [
                    placeholder.name
                    for placeholder in template.required_placeholders
                    if placeholder.name not in final_values
                ]

                if missing_required:
                    error_message = f'Missing values for required placeholders: {", ".join(missing_required)}'
                    return {
                        'success': False,
                        'template_name': template_name,
                        'error_type': 'InvalidPlaceholderValueError',
                        'error_message': error_message,
                        'error': error_message,  # For backward compatibility with some tests
                    }

                # Add default values for optional placeholders
                for placeholder in template.optional_placeholders:
                    if placeholder.name not in final_values:
                        final_values[placeholder.name] = placeholder.get_effective_value()

            # Render template
            content = template.render(final_values)

        except TemplateError as e:
            return {
                'success': False,
                'template_name': template_name,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error': str(e),  # For backward compatibility with some tests
            }
        else:
            return {
                'success': True,
                'content': content,
                'template_name': template_name,
                'placeholder_values': final_values,
            }

    def list_all_templates(self) -> dict[str, Any]:
        """List all available templates (single and directory).

        Returns:
            Dictionary with counts and lists of all template types

        """
        try:
            single_templates = self.list_templates()
            directory_templates = self.list_template_directories()

            return {
                'success': True,
                'total_templates': len(single_templates) + len(directory_templates),
                'single_templates': {'count': len(single_templates), 'names': single_templates},
                'directory_templates': {'count': len(directory_templates), 'names': directory_templates},
            }

        except (TemplateError, Exception) as e:
            return {
                'success': False,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error': str(e),  # For backward compatibility with some tests
            }

    def _collect_placeholder_values(self, template: Template, provided_values: dict[str, str]) -> dict[str, str]:
        """Collect all required placeholder values for a template.

        Args:
            template: Template to collect values for
            provided_values: Values already provided

        Returns:
            Complete set of placeholder values

        Raises:
            InvalidPlaceholderValueError: If required placeholders missing or invalid
            UserCancelledError: If user cancels input

        """
        final_values = provided_values.copy()

        # First, add default values for optional placeholders
        for placeholder in template.placeholders:
            if placeholder.name not in final_values and not placeholder.required:
                final_values[placeholder.name] = placeholder.get_effective_value()

        # Collect missing required placeholders
        missing_required = [
            placeholder
            for placeholder in template.placeholders
            if placeholder.name not in final_values and placeholder.required
        ]

        # If there are missing required placeholders, prompt for them
        if missing_required:
            prompted_values = self.prompter.prompt_for_placeholder_values(missing_required)
            for placeholder_name, placeholder_value in prompted_values.items():
                final_values[placeholder_name] = placeholder_value.value

        # Validate all values
        for placeholder in template.placeholders:
            if placeholder.name in final_values:  # pragma: no branch
                try:
                    placeholder.validate_value(final_values[placeholder.name])
                except TemplateError as e:
                    msg = f"Invalid value for placeholder '{placeholder.name}': {e}"
                    raise InvalidPlaceholderValueError(
                        msg, placeholder_name=placeholder.name, provided_value=final_values[placeholder.name]
                    ) from e

        return final_values

    def _collect_directory_placeholder_values(
        self, template_directory: TemplateDirectory, provided_values: dict[str, str]
    ) -> dict[str, str]:
        """Collect all required placeholder values for a template directory.

        Args:
            template_directory: Template directory to collect values for
            provided_values: Values already provided

        Returns:
            Complete set of placeholder values

        Raises:
            InvalidPlaceholderValueError: If required placeholders missing or invalid
            UserCancelledError: If user cancels input

        """
        final_values = provided_values.copy()

        # First, add default values for optional placeholders
        for placeholder in template_directory.all_placeholders:
            if placeholder.name not in final_values and not placeholder.required:
                final_values[placeholder.name] = placeholder.get_effective_value()

        # Collect missing required placeholders
        missing_required = [
            placeholder
            for placeholder in template_directory.all_placeholders
            if placeholder.name not in final_values and placeholder.required
        ]

        # If there are missing required placeholders, prompt for them
        if missing_required:
            prompted_values = self.prompter.prompt_for_placeholder_values(missing_required)
            for placeholder_name, placeholder_value in prompted_values.items():
                final_values[placeholder_name] = placeholder_value.value

        # Validate all values
        validation_errors = template_directory.validate_placeholder_values(final_values)
        if validation_errors:
            msg = f'Placeholder validation failed: {"; ".join(validation_errors)}'
            raise InvalidPlaceholderValueError(msg, placeholder_name='multiple')

        return final_values

    def create_content_from_directory_template(
        self,
        template_directory_name: str,
        placeholder_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create content from a directory template.

        Args:
            template_directory_name: Name of template directory to use
            placeholder_values: Optional predefined placeholder values

        Returns:
            Dictionary with success status and result/error details

        """
        try:
            content_map = self.create_from_directory_template(template_directory_name, placeholder_values)
            return {
                'success': True,
                'content': content_map,
                'template_name': template_directory_name,
                'file_count': len(content_map),
                'placeholder_values': placeholder_values or {},
            }
        except TemplateError as e:
            return {
                'success': False,
                'template_name': template_directory_name,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error': str(e),  # For backward compatibility with some tests
            }

    def validate_template(self, template_name: str) -> dict[str, Any]:
        """Validate a single template.

        Args:
            template_name: Name of template to validate

        Returns:
            Dictionary with validation results

        """
        try:
            template = self.repository.get_template(template_name)
            validation_errors = self.validator.validate_template(template)

            return {'valid': len(validation_errors) == 0, 'template_name': template_name, 'errors': validation_errors}
        except TemplateError as e:
            return {
                'valid': False,
                'template_name': template_name,
                'error_type': type(e).__name__,
                'error_message': str(e),
            }

    def validate_directory_template(self, template_directory_name: str) -> dict[str, Any]:
        """Validate a directory template.

        Args:
            template_directory_name: Name of template directory to validate

        Returns:
            Dictionary with validation results

        """
        try:
            template_directory = self.repository.get_template_directory(template_directory_name)
            validation_errors = self.validator.validate_template_directory(template_directory)

            return {
                'valid': len(validation_errors) == 0,
                'template_directory_name': template_directory_name,
                'errors': validation_errors,
            }
        except TemplateError as e:
            return {
                'valid': False,
                'template_directory_name': template_directory_name,
                'error_type': type(e).__name__,
                'error_message': str(e),
            }
