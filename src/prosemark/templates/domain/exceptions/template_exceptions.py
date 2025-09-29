"""Template-specific exceptions for the templates domain.

These exceptions represent various error conditions that can occur
during template operations, validation, and instantiation.
"""


class TemplateError(Exception):
    """Base exception for all template-related errors."""

    def __init__(self, message: str, template_path: str | None = None) -> None:
        """Initialize template error.

        Args:
            message: Human-readable error description
            template_path: Optional path to the template that caused the error

        """
        self.template_path = template_path
        if template_path:
            super().__init__(f'{message} (template: {template_path})')
        else:
            super().__init__(message)


class TemplateNotFoundError(TemplateError):
    """Raised when a requested template cannot be found."""

    def __init__(self, template_name: str, search_path: str | None = None) -> None:
        """Initialize template not found error.

        Args:
            template_name: Name of the template that was not found
            search_path: Directory where template was searched for

        """
        self.template_name = template_name
        self.search_path = search_path

        if search_path:
            message = f"Template '{template_name}' not found in directory '{search_path}'"
        else:
            message = f"Template '{template_name}' not found"

        super().__init__(message)


class TemplateDirectoryNotFoundError(TemplateError):
    """Raised when the templates directory does not exist."""

    def __init__(self, directory_path: str) -> None:
        """Initialize template directory not found error.

        Args:
            directory_path: Path to the directory that does not exist

        """
        self.directory_path = directory_path
        message = f'Templates directory not found: {directory_path}'
        super().__init__(message)


class EmptyTemplateDirectoryError(TemplateError):
    """Raised when a template directory contains no valid templates."""

    def __init__(self, directory_path: str) -> None:
        """Initialize empty template directory error.

        Args:
            directory_path: Path to the empty template directory

        """
        self.directory_path = directory_path
        message = f'Template directory contains no valid templates: {directory_path}'
        super().__init__(message)


class InvalidTemplateDirectoryError(TemplateError):
    """Raised when a template directory contains invalid templates."""

    def __init__(self, directory_path: str, invalid_templates: list[str]) -> None:
        """Initialize invalid template directory error.

        Args:
            directory_path: Path to the template directory
            invalid_templates: List of invalid template file names

        """
        self.directory_path = directory_path
        self.invalid_templates = invalid_templates

        invalid_list = ', '.join(invalid_templates)
        message = f'Template directory contains invalid templates: {invalid_list} (in {directory_path})'
        super().__init__(message)


class TemplateParseError(TemplateError):
    """Raised when template content cannot be parsed."""

    def __init__(self, message: str, template_path: str | None = None, line_number: int | None = None) -> None:
        """Initialize template parse error.

        Args:
            message: Specific parsing error description
            template_path: Path to the template with parse error
            line_number: Optional line number where error occurred

        """
        self.line_number = line_number

        full_message = f'{message} at line {line_number}' if line_number and template_path else message

        super().__init__(full_message, template_path)


class TemplateValidationError(TemplateError):
    """Raised when template content fails validation."""

    def __init__(self, message: str, template_path: str | None = None, validation_rule: str | None = None) -> None:
        """Initialize template validation error.

        Args:
            message: Validation error description
            template_path: Path to the template that failed validation
            validation_rule: Optional name of the validation rule that failed

        """
        self.validation_rule = validation_rule

        full_message = f'{message} (validation rule: {validation_rule})' if validation_rule else message

        super().__init__(full_message, template_path)


class InvalidPlaceholderError(TemplateError):
    """Raised when a placeholder has invalid syntax or properties."""

    def __init__(self, message: str, placeholder_pattern: str | None = None, template_path: str | None = None) -> None:
        """Initialize invalid placeholder error.

        Args:
            message: Placeholder error description
            placeholder_pattern: The invalid placeholder pattern
            template_path: Path to template containing the invalid placeholder

        """
        self.placeholder_pattern = placeholder_pattern

        full_message = f'{message} (placeholder: {placeholder_pattern})' if placeholder_pattern else message

        super().__init__(full_message, template_path)


class InvalidPlaceholderValueError(TemplateError):
    """Raised when a user-provided placeholder value is invalid."""

    def __init__(self, message: str, placeholder_name: str | None = None, provided_value: str | None = None) -> None:
        """Initialize invalid placeholder value error.

        Args:
            message: Value validation error description
            placeholder_name: Name of the placeholder with invalid value
            provided_value: The invalid value that was provided

        """
        self.placeholder_name = placeholder_name
        self.provided_value = provided_value

        if placeholder_name and provided_value:
            full_message = f"{message} (placeholder: {placeholder_name}, value: '{provided_value}')"
        elif placeholder_name:
            full_message = f'{message} (placeholder: {placeholder_name})'
        else:
            full_message = message

        super().__init__(full_message)


class UserCancelledError(TemplateError):
    """Raised when user cancels template operation."""

    def __init__(self, message: str = 'Operation cancelled by user') -> None:
        """Initialize user cancelled error.

        Args:
            message: Cancellation message

        """
        super().__init__(message)


class PlaceholderProcessingError(TemplateError):
    """Raised when placeholder replacement fails."""

    def __init__(self, message: str, placeholder_name: str | None = None, template_path: str | None = None) -> None:
        """Initialize placeholder processing error.

        Args:
            message: Processing error description
            placeholder_name: Name of placeholder that failed processing
            template_path: Path to template being processed

        """
        self.placeholder_name = placeholder_name

        full_message = f'{message} (placeholder: {placeholder_name})' if placeholder_name else message

        super().__init__(full_message, template_path)
