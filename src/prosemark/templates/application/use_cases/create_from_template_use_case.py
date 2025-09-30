"""Use case for creating content from templates."""

from typing import Any

from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderError,
    InvalidPlaceholderValueError,
    PlaceholderProcessingError,
    TemplateDirectoryNotFoundError,
    TemplateNotFoundError,
    TemplateParseError,
    TemplateValidationError,
    UserCancelledError,
)
from prosemark.templates.domain.services.template_service import TemplateService


class CreateFromTemplateUseCase:
    """Use case orchestrating template content creation."""

    def __init__(self, template_service: TemplateService) -> None:
        """Initialize use case with template service.

        Args:
            template_service: Service providing template operations

        """
        self._template_service = template_service

    @staticmethod
    def _raise_missing_placeholder_error(missing_placeholders: list[str]) -> None:
        """Raise an error for missing placeholder values.

        Args:
            missing_placeholders: List of missing placeholder names

        Raises:
            InvalidPlaceholderValueError: Always raised with context

        """
        msg = f'Missing values for required placeholders: {", ".join(missing_placeholders)}'
        raise InvalidPlaceholderValueError(
            msg,
            placeholder_name=missing_placeholders[0],  # Use first for error context
        )

    def create_single_template(
        self,
        template_name: str,
        placeholder_values: dict[str, str] | None = None,
        *,
        interactive: bool = True,
    ) -> dict[str, Any]:
        """Create content from a single template.

        Args:
            template_name: Name of template to use
            placeholder_values: Optional predefined placeholder values
            interactive: Whether to prompt user for missing values

        Returns:
            Dictionary containing generated content and metadata

        """
        try:
            # Generate content using template service
            if interactive:
                content = self._template_service.create_from_template(template_name, placeholder_values)
            else:
                # In non-interactive mode, we must have all required values
                template_info = self._template_service.get_template_info(template_name)
                required_placeholders = template_info.get('required_placeholders', [])

                provided_values = placeholder_values or {}
                missing_placeholders = [name for name in required_placeholders if name not in provided_values]

                if missing_placeholders:
                    CreateFromTemplateUseCase._raise_missing_placeholder_error(missing_placeholders)
                else:
                    content = self._template_service.create_from_template(template_name, provided_values)

        except (
            TemplateNotFoundError,
            InvalidPlaceholderValueError,
            TemplateValidationError,
            PlaceholderProcessingError,
            UserCancelledError,
            TemplateParseError,
            InvalidPlaceholderError,
        ) as e:
            return {
                'success': False,
                'template_name': template_name,
                'template_type': 'single',
                'error': str(e),
                'error_type': type(e).__name__,
            }
        else:
            # Get template metadata
            template_info = self._template_service.get_template_info(template_name)

            return {
                'success': True,
                'template_name': template_name,
                'template_type': 'single',
                'content': content,
                'metadata': template_info,
                'placeholder_values': placeholder_values or {},
            }

    def create_directory_template(
        self,
        template_directory_name: str,
        placeholder_values: dict[str, str] | None = None,
        *,
        interactive: bool = True,
    ) -> dict[str, Any]:
        """Create content from a directory template.

        Args:
            template_directory_name: Name of template directory to use
            placeholder_values: Optional predefined placeholder values
            interactive: Whether to prompt user for missing values

        Returns:
            Dictionary containing generated content and metadata

        """
        try:
            # Generate content using template service
            if interactive:
                content_map = self._template_service.create_from_directory_template(
                    template_directory_name, placeholder_values
                )
            else:
                # In non-interactive mode, we must have all required values
                directory_info = self._template_service.get_directory_template_info(template_directory_name)
                required_placeholders = directory_info.get('required_placeholders', [])

                provided_values = placeholder_values or {}
                missing_placeholders = [name for name in required_placeholders if name not in provided_values]

                if missing_placeholders:
                    CreateFromTemplateUseCase._raise_missing_placeholder_error(missing_placeholders)
                else:
                    content_map = self._template_service.create_from_directory_template(
                        template_directory_name, provided_values
                    )

        except (
            TemplateDirectoryNotFoundError,
            InvalidPlaceholderValueError,
            TemplateValidationError,
            PlaceholderProcessingError,
            UserCancelledError,
            TemplateParseError,
            InvalidPlaceholderError,
        ) as e:
            return {
                'success': False,
                'template_name': template_directory_name,
                'template_type': 'directory',
                'error': str(e),
                'error_type': type(e).__name__,
            }
        else:
            # Get directory metadata
            directory_info = self._template_service.get_directory_template_info(template_directory_name)

            return {
                'success': True,
                'template_name': template_directory_name,
                'template_type': 'directory',
                'content': content_map,
                'file_count': len(content_map),
                'metadata': directory_info,
                'placeholder_values': placeholder_values or {},
            }

    def validate_template_before_creation(self, template_name: str) -> dict[str, Any]:
        """Validate a template before attempting to create content from it.

        Args:
            template_name: Name of template to validate

        Returns:
            Dictionary containing validation results

        """
        try:
            # Get template info to validate it exists and is valid
            template_info = self._template_service.get_template_info(template_name)

        except TemplateNotFoundError as e:
            return {
                'success': False,
                'template_name': template_name,
                'template_type': 'single',
                'valid': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }
        else:
            # Check if it has placeholders that would require user input
            required_placeholders = template_info.get('required_placeholders', [])
            optional_placeholders = template_info.get('optional_placeholders', [])
            placeholder_count = template_info.get('placeholder_count', 0)

            return {
                'success': True,
                'template_name': template_name,
                'template_type': 'single',
                'valid': True,
                'has_placeholders': placeholder_count > 0,
                'required_placeholders': required_placeholders,
                'optional_placeholders': optional_placeholders,
                'placeholder_count': placeholder_count,
                'metadata': template_info,
            }

    def validate_directory_template_before_creation(self, template_directory_name: str) -> dict[str, Any]:
        """Validate a directory template before attempting to create content from it.

        Args:
            template_directory_name: Name of template directory to validate

        Returns:
            Dictionary containing validation results

        """
        try:
            # Get directory info to validate it exists and is valid
            directory_info = self._template_service.get_directory_template_info(template_directory_name)

            # Check if it has placeholders that would require user input
            required_placeholders = directory_info.get('required_placeholders', [])
            optional_placeholders = directory_info.get('optional_placeholders', [])
            template_count = directory_info.get('template_count', 0)

            return {
                'success': True,
                'template_name': template_directory_name,
                'template_type': 'directory',
                'valid': True,
                'template_count': template_count,
                'required_placeholders': required_placeholders,
                'optional_placeholders': optional_placeholders,
                'shared_placeholders': directory_info.get('shared_placeholders', []),
                'metadata': directory_info,
            }

        except TemplateDirectoryNotFoundError as e:
            return {
                'success': False,
                'template_name': template_directory_name,
                'template_type': 'directory',
                'valid': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }

    def get_template_preview(
        self,
        template_name: str,
        placeholder_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Get a preview of what would be generated from a template.

        Args:
            template_name: Name of template to preview
            placeholder_values: Optional placeholder values for preview

        Returns:
            Dictionary containing preview information

        """
        try:
            # Get template info
            template_info = self._template_service.get_template_info(template_name)

            # Identify what placeholders would need values
            required_placeholders = template_info.get('required_placeholders', [])
            optional_placeholders = template_info.get('optional_placeholders', [])
            provided_values = placeholder_values or {}

            missing_required = [name for name in required_placeholders if name not in provided_values]

            return {
                'success': True,
                'template_name': template_name,
                'template_type': 'single',
                'can_generate': len(missing_required) == 0,
                'missing_required_placeholders': missing_required,
                'provided_placeholders': list(provided_values.keys()),
                'all_required_placeholders': required_placeholders,
                'all_optional_placeholders': optional_placeholders,
                'placeholder_values': provided_values,
                'metadata': template_info,
            }

        except TemplateNotFoundError as e:
            return {
                'success': False,
                'template_name': template_name,
                'template_type': 'single',
                'error': str(e),
                'error_type': type(e).__name__,
            }
