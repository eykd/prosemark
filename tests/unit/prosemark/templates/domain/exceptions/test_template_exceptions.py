"""Unit tests for template exceptions."""

from prosemark.templates.domain.exceptions.template_exceptions import (
    PlaceholderProcessingError,
    TemplateNotFoundError,
    TemplateValidationError,
    UserCancelledError,
)


class TestTemplateExceptions:
    """Test template exception classes."""

    def test_template_not_found_error_without_search_path(self) -> None:
        """Test TemplateNotFoundError without search_path."""
        error = TemplateNotFoundError(template_name='meeting-notes')

        assert error.template_name == 'meeting-notes'
        assert error.search_path is None
        assert "Template 'meeting-notes' not found" in str(error)

    def test_template_not_found_error_with_search_path(self) -> None:
        """Test TemplateNotFoundError with search_path."""
        error = TemplateNotFoundError(template_name='meeting-notes', search_path='/templates')

        assert error.template_name == 'meeting-notes'
        assert error.search_path == '/templates'
        assert "Template 'meeting-notes' not found in directory '/templates'" in str(error)

    def test_user_cancelled_error(self) -> None:
        """Test UserCancelledError."""
        error = UserCancelledError()

        assert 'cancelled' in str(error).lower()

    def test_user_cancelled_error_with_custom_message(self) -> None:
        """Test UserCancelledError with custom message."""
        error = UserCancelledError('User aborted operation')

        assert 'User aborted operation' in str(error)

    def test_template_validation_error_with_path(self) -> None:
        """Test TemplateValidationError with template_path."""
        error = TemplateValidationError('Invalid frontmatter', template_path='/templates/test.md')

        assert error.template_path == '/templates/test.md'
        assert 'Invalid frontmatter' in str(error)

    def test_template_validation_error_without_path(self) -> None:
        """Test TemplateValidationError without template_path."""
        error = TemplateValidationError('Missing required field')

        assert error.template_path is None
        assert 'Missing required field' in str(error)

    def test_placeholder_processing_error_with_placeholder_name(self) -> None:
        """Test PlaceholderProcessingError with placeholder name."""
        error = PlaceholderProcessingError(
            'Invalid value for placeholder',
            placeholder_name='title',
            template_path='/templates/test.md',
        )

        assert error.placeholder_name == 'title'
        assert 'Invalid value for placeholder' in str(error)
        assert '(placeholder: title)' in str(error)

    def test_placeholder_processing_error_without_placeholder_name(self) -> None:
        """Test PlaceholderProcessingError without placeholder name."""
        error = PlaceholderProcessingError(
            'General processing error',
            template_path='/templates/test.md',
        )

        assert error.placeholder_name is None
        assert 'General processing error' in str(error)
        assert 'placeholder:' not in str(error)

    def test_placeholder_processing_error_minimal(self) -> None:
        """Test PlaceholderProcessingError with minimal arguments."""
        error = PlaceholderProcessingError('Processing failed')

        assert error.placeholder_name is None
        assert 'Processing failed' in str(error)
