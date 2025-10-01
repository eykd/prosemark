"""Unit tests for TemplateService."""

from unittest.mock import Mock

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderValueError,
    PlaceholderProcessingError,
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    UserCancelledError,
)
from prosemark.templates.domain.services.template_service import TemplateService
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern


class TestTemplateService:
    """Test TemplateService domain service."""

    def test_init_with_dependencies(self) -> None:
        """Test initializing template service with dependencies."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        assert service.repository is repository
        assert service.validator is validator
        assert service.prompter is prompter

    def test_create_content_from_single_template_success(self) -> None:
        """Test successfully creating content from single template."""
        # Mock dependencies
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Mock template
        template = Mock(spec=Template)
        template.name = 'test-template'
        template.render.return_value = '# Test Title\n\nRendered content'

        # Create a title placeholder that requires user input
        title_placeholder = Placeholder(
            name='title',
            pattern_obj=PlaceholderPattern('{{title}}'),
            required=True,
            default_value=None,
            description='The document title',
        )
        template.placeholders = [title_placeholder]

        # Configure mocks
        repository.get_template.return_value = template
        validator.validate_template.return_value = []  # No errors
        prompter.prompt_for_placeholder_values.return_value = {
            'title': PlaceholderValue(placeholder_name='title', value='Test Title')
        }

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('test-template')

        assert result['success'] is True
        assert result['content'] == '# Test Title\n\nRendered content'
        assert result['template_name'] == 'test-template'

        # Verify interactions
        repository.get_template.assert_called_once_with('test-template')
        validator.validate_template.assert_called_once_with(template)
        template.render.assert_called_once_with({'title': 'Test Title'})

    def test_create_content_from_single_template_not_found(self) -> None:
        """Test creating content when template not found."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.get_template.side_effect = TemplateNotFoundError(template_name='missing', search_path='/templates')

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('missing')

        assert result['success'] is False
        assert result['template_name'] == 'missing'
        assert 'TemplateNotFoundError' in result['error_type']

    def test_create_content_from_single_template_validation_error(self) -> None:
        """Test creating content when template validation fails."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'invalid-template'

        repository.get_template.return_value = template
        validator.validate_template.return_value = ['Template has invalid frontmatter']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('invalid-template')

        assert result['success'] is False
        assert result['template_name'] == 'invalid-template'
        assert 'TemplateValidationError' in result['error_type']
        assert 'Template has invalid frontmatter' in result['error']

    def test_create_content_from_single_template_user_cancelled(self) -> None:
        """Test creating content when user cancels prompt."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'test-template'

        # Create a title placeholder that requires user input
        title_placeholder = Placeholder(
            name='title',
            pattern_obj=PlaceholderPattern('{{title}}'),
            required=True,
            default_value=None,
            description='The document title',
        )
        template.placeholders = [title_placeholder]

        repository.get_template.return_value = template
        validator.validate_template.return_value = []
        prompter.prompt_for_placeholder_values.side_effect = UserCancelledError('User cancelled')

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('test-template')

        assert result['success'] is False
        assert result['template_name'] == 'test-template'
        assert 'UserCancelledError' in result['error_type']

    def test_create_content_from_directory_template_success(self) -> None:
        """Test successfully creating content from directory template."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Mock directory template
        template_dir = Mock(spec=TemplateDirectory)
        template_dir.name = 'project-template'

        # Create a name placeholder that requires user input
        name_placeholder = Placeholder(
            name='name',
            pattern_obj=PlaceholderPattern('{{name}}'),
            required=True,
            default_value=None,
            description='The project name',
        )
        template_dir.all_placeholders = [name_placeholder]
        template_dir.validate_placeholder_values.return_value = []  # No validation errors

        # Mock rendered content
        content_map = {'readme.md': '# Project\n\nDescription here', 'setup.md': '# Setup\n\nSetup instructions'}
        template_dir.replace_placeholders_in_all.return_value = content_map

        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = []
        prompter.prompt_for_placeholder_values.return_value = {
            'name': PlaceholderValue(placeholder_name='name', value='MyProject')
        }

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_directory_template('project-template')

        assert result['success'] is True
        assert result['content'] == content_map
        assert result['template_name'] == 'project-template'
        assert result['file_count'] == 2

    def test_create_content_with_predefined_values(self) -> None:
        """Test creating content with predefined placeholder values."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'test-template'
        template.render.return_value = '# Test Title\n\nContent'
        template.required_placeholders = []
        template.optional_placeholders = []

        repository.get_template.return_value = template
        validator.validate_template.return_value = []
        validator.validate_placeholder_values.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        predefined_values = {'title': 'Predefined Title'}
        result = service.create_content_from_single_template(
            'test-template', placeholder_values=predefined_values, interactive=False
        )

        assert result['success'] is True
        template.render.assert_called_once_with(predefined_values)
        # Prompter should not be called in non-interactive mode
        prompter.prompt_for_placeholder_values.assert_not_called()

    def test_create_content_non_interactive_missing_values(self) -> None:
        """Test non-interactive mode with missing required values."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'test-template'

        # Create a title placeholder that requires user input
        title_placeholder = Placeholder(
            name='title',
            pattern_obj=PlaceholderPattern('{{title}}'),
            required=True,
            default_value=None,
            description='The document title',
        )
        template.required_placeholders = [title_placeholder]
        template.optional_placeholders = []

        repository.get_template.return_value = template
        validator.validate_template.return_value = []
        validator.validate_placeholder_values.return_value = ['Missing value for required placeholder: title']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('test-template', placeholder_values={}, interactive=False)

        assert result['success'] is False
        assert 'InvalidPlaceholderValueError' in result['error_type']

    def test_list_all_templates_success(self) -> None:
        """Test listing all available templates."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Create mock templates with name attributes
        mock_template1 = Mock(name='template1')
        mock_template1.name = 'template1'
        mock_template2 = Mock(name='template2')
        mock_template2.name = 'template2'

        mock_dir1 = Mock(name='dir1')
        mock_dir1.name = 'dir1'
        mock_dir2 = Mock(name='dir2')
        mock_dir2.name = 'dir2'

        repository.list_templates.return_value = [mock_template1, mock_template2]
        repository.list_template_directories.return_value = [mock_dir1, mock_dir2]

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.list_all_templates()

        assert result['success'] is True
        assert result['total_templates'] == 4
        assert result['single_templates']['count'] == 2
        assert result['single_templates']['names'] == ['template1', 'template2']
        assert result['directory_templates']['count'] == 2
        assert result['directory_templates']['names'] == ['dir1', 'dir2']

    def test_list_all_templates_empty(self) -> None:
        """Test listing templates when none exist."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.list_templates.return_value = []
        repository.list_template_directories.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.list_all_templates()

        assert result['success'] is True
        assert result['total_templates'] == 0
        assert result['single_templates']['count'] == 0
        assert result['directory_templates']['count'] == 0

    def test_list_all_templates_error(self) -> None:
        """Test listing templates when repository error occurs."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.list_templates.side_effect = Exception('Repository error')

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.list_all_templates()

        assert result['success'] is False
        assert 'error' in result

    def test_validate_single_template_success(self) -> None:
        """Test validating a single template successfully."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        repository.get_template.return_value = template
        validator.validate_template.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_template('test-template')

        assert result['valid'] is True
        assert result['errors'] == []

    def test_validate_single_template_with_errors(self) -> None:
        """Test validating a single template with validation errors."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        repository.get_template.return_value = template
        validator.validate_template.return_value = ['Error 1', 'Error 2']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_template('test-template')

        assert result['valid'] is False
        assert result['errors'] == ['Error 1', 'Error 2']

    def test_validate_directory_template_success(self) -> None:
        """Test validating a directory template successfully."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_directory_template('project-template')

        assert result['valid'] is True
        assert result['errors'] == []

    def test_validate_directory_template_with_errors(self) -> None:
        """Test validating a directory template with validation errors."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = ['Error 1', 'Error 2']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_directory_template('project-template')

        assert result['valid'] is False
        assert result['errors'] == ['Error 1', 'Error 2']

    def test_validate_template_template_error(self) -> None:
        """Test validate_template when repository raises TemplateError."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.get_template.side_effect = TemplateNotFoundError(template_name='missing', search_path='/templates')

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_template('missing')

        assert result['valid'] is False
        assert result['template_name'] == 'missing'
        assert result['error_type'] == 'TemplateNotFoundError'
        assert 'error_message' in result

    def test_validate_directory_template_template_error(self) -> None:
        """Test validate_directory_template when repository raises TemplateError."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.get_template_directory.side_effect = TemplateNotFoundError(
            template_name='missing-dir', search_path='/templates'
        )

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.validate_directory_template('missing-dir')

        assert result['valid'] is False
        assert result['template_directory_name'] == 'missing-dir'
        assert result['error_type'] == 'TemplateNotFoundError'
        assert 'error_message' in result

    def test_create_from_template_validation_error(self) -> None:
        """Test create_from_template raises TemplateValidationError."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.path = Path('/templates/test.md')
        repository.get_template.return_value = template
        validator.validate_template.return_value = ['Invalid frontmatter', 'Missing required field']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        try:
            service.create_from_template('test-template')
            raise AssertionError('Expected TemplateValidationError')
        except TemplateValidationError as e:
            assert 'Template validation failed' in str(e)
            assert 'Invalid frontmatter' in str(e)

    def test_create_from_template_placeholder_processing_error(self) -> None:
        """Test create_from_template raises PlaceholderProcessingError."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.path = Path('/templates/test.md')
        template.placeholders = []
        template.replace_placeholders.side_effect = TemplateError('Failed to replace placeholders')

        repository.get_template.return_value = template
        validator.validate_template.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        try:
            service.create_from_template('test-template', {})
            raise AssertionError('Expected PlaceholderProcessingError')
        except PlaceholderProcessingError as e:
            assert 'Failed to process placeholders' in str(e)

    def test_create_from_directory_template_validation_error(self) -> None:
        """Test create_from_directory_template raises TemplateValidationError."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        template_dir.path = Path('/templates/project')
        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = ['Invalid structure', 'Missing config']

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        try:
            service.create_from_directory_template('project-template')
            raise AssertionError('Expected TemplateValidationError')
        except TemplateValidationError as e:
            assert 'Template directory validation failed' in str(e)
            assert 'Invalid structure' in str(e)

    def test_create_from_directory_template_placeholder_processing_error(self) -> None:
        """Test create_from_directory_template raises PlaceholderProcessingError."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        template_dir.path = Path('/templates/project')
        template_dir.all_placeholders = []
        template_dir.validate_placeholder_values.return_value = []  # No validation errors
        template_dir.replace_placeholders_in_all.side_effect = TemplateError('Failed to replace in directory')

        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        try:
            service.create_from_directory_template('project-template', {})
            raise AssertionError('Expected PlaceholderProcessingError')
        except PlaceholderProcessingError as e:
            assert 'Failed to process placeholders in directory template' in str(e)

    def test_create_content_from_directory_template_template_error(self) -> None:
        """Test create_content_from_directory_template handles TemplateError."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        repository.get_template_directory.side_effect = TemplateNotFoundError(
            template_name='missing', search_path='/templates'
        )

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_directory_template('missing')

        assert result['success'] is False
        assert result['template_name'] == 'missing'
        assert 'TemplateNotFoundError' in result['error_type']

    def test_collect_placeholder_values_with_invalid_value(self) -> None:
        """Test _collect_placeholder_values raises InvalidPlaceholderValueError for invalid values."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Create a template with a placeholder that has validation
        template = Mock(spec=Template)
        template.path = Path('/templates/test.md')

        # Create a placeholder that will fail validation
        title_placeholder = Mock(spec=Placeholder)
        title_placeholder.name = 'title'
        title_placeholder.required = True
        title_placeholder.validate_value.side_effect = TemplateError('Title must not be empty')

        template.placeholders = [title_placeholder]
        template.required_placeholders = [title_placeholder]

        repository.get_template.return_value = template
        validator.validate_template.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        # Provide an invalid value that will trigger validation error
        provided_values = {'title': ''}

        try:
            service._collect_placeholder_values(template, provided_values)
            raise AssertionError('Expected InvalidPlaceholderValueError')
        except InvalidPlaceholderValueError as e:
            assert 'Invalid value for placeholder' in str(e)
            assert 'title' in str(e)

    def test_collect_directory_placeholder_values_with_validation_errors(self) -> None:
        """Test _collect_directory_placeholder_values raises InvalidPlaceholderValueError."""
        from pathlib import Path

        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        template_dir.path = Path('/templates/project')

        # Create optional placeholder
        name_placeholder = Mock(spec=Placeholder)
        name_placeholder.name = 'name'
        name_placeholder.required = False
        name_placeholder.get_effective_value.return_value = 'default-name'

        template_dir.all_placeholders = [name_placeholder]
        template_dir.validate_placeholder_values.return_value = ['Name contains invalid characters']

        repository.get_template_directory.return_value = template_dir
        validator.validate_template_directory.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        try:
            service._collect_directory_placeholder_values(template_dir, {})
            raise AssertionError('Expected InvalidPlaceholderValueError')
        except InvalidPlaceholderValueError as e:
            assert 'Placeholder validation failed' in str(e)
            assert 'Name contains invalid characters' in str(e)

    def test_create_content_from_single_template_with_optional_placeholders_non_interactive(self) -> None:
        """Test non-interactive mode adds default values for optional placeholders."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'test-template'
        template.render.return_value = '# Test\n\nBy Anonymous'

        # Create optional placeholder with default
        author_placeholder = Mock(spec=Placeholder)
        author_placeholder.name = 'author'
        author_placeholder.get_effective_value.return_value = 'Anonymous'

        template.required_placeholders = []
        template.optional_placeholders = [author_placeholder]

        repository.get_template.return_value = template
        validator.validate_template.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.create_content_from_single_template('test-template', {}, interactive=False)

        assert result['success'] is True
        # Verify the default value was added
        template.render.assert_called_once()
        call_args = template.render.call_args[0][0]
        assert 'author' in call_args
        assert call_args['author'] == 'Anonymous'

    def test_get_template_info(self) -> None:
        """Test get_template_info returns template metadata."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.to_dict.return_value = {'name': 'test-template', 'placeholders': []}

        repository.get_template.return_value = template

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.get_template_info('test-template')

        assert result == {'name': 'test-template', 'placeholders': []}
        repository.get_template.assert_called_once_with('test-template')
        template.to_dict.assert_called_once()

    def test_get_directory_template_info(self) -> None:
        """Test get_directory_template_info returns directory metadata."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template_dir = Mock(spec=TemplateDirectory)
        template_dir.to_dict.return_value = {'name': 'project-template', 'templates': []}

        repository.get_template_directory.return_value = template_dir

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        result = service.get_directory_template_info('project-template')

        assert result == {'name': 'project-template', 'templates': []}
        repository.get_template_directory.assert_called_once_with('project-template')
        template_dir.to_dict.assert_called_once()

    def test_collect_placeholder_values_with_optional_defaults(self) -> None:
        """Test _collect_placeholder_values adds default values for optional placeholders."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Create template with both required and optional placeholders
        template = Mock(spec=Template)

        # Required placeholder
        title_placeholder = Mock(spec=Placeholder)
        title_placeholder.name = 'title'
        title_placeholder.required = True
        title_placeholder.validate_value.return_value = None  # Valid

        # Optional placeholder with default
        author_placeholder = Mock(spec=Placeholder)
        author_placeholder.name = 'author'
        author_placeholder.required = False
        author_placeholder.get_effective_value.return_value = 'Anonymous'
        author_placeholder.validate_value.return_value = None  # Valid

        template.placeholders = [title_placeholder, author_placeholder]

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        # Provide only the required value
        provided_values = {'title': 'Test Title'}

        result = service._collect_placeholder_values(template, provided_values)

        # Should have both values - the provided one and the default
        assert 'title' in result
        assert result['title'] == 'Test Title'
        assert 'author' in result
        assert result['author'] == 'Anonymous'

        # Verify default was retrieved
        author_placeholder.get_effective_value.assert_called_once()

    def test_collect_placeholder_values_all_provided(self) -> None:
        """Test _collect_placeholder_values when all values are already provided."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        # Create template with both required and optional placeholders
        template = Mock(spec=Template)

        # Required placeholder
        title_placeholder = Mock(spec=Placeholder)
        title_placeholder.name = 'title'
        title_placeholder.required = True
        title_placeholder.validate_value.return_value = None  # Valid

        # Optional placeholder
        author_placeholder = Mock(spec=Placeholder)
        author_placeholder.name = 'author'
        author_placeholder.required = False
        author_placeholder.validate_value.return_value = None  # Valid

        template.placeholders = [title_placeholder, author_placeholder]

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        # Provide ALL values including the optional one
        provided_values = {'title': 'Test Title', 'author': 'John Doe'}

        result = service._collect_placeholder_values(template, provided_values)

        # Should have both provided values
        assert 'title' in result
        assert result['title'] == 'Test Title'
        assert 'author' in result
        assert result['author'] == 'John Doe'

        # Verify default was NOT retrieved since value was provided
        author_placeholder.get_effective_value.assert_not_called()

        # Verify validation was called for both
        title_placeholder.validate_value.assert_called_once_with('Test Title')
        author_placeholder.validate_value.assert_called_once_with('John Doe')

    def test_create_content_from_single_template_with_provided_optional_value_non_interactive(self) -> None:
        """Test non-interactive mode with provided optional placeholder value."""
        repository = Mock()
        validator = Mock()
        prompter = Mock()

        template = Mock(spec=Template)
        template.name = 'test-template'
        template.render.return_value = '# Test\n\nBy Jane Doe'

        # Create optional placeholder with default
        author_placeholder = Mock(spec=Placeholder)
        author_placeholder.name = 'author'
        author_placeholder.get_effective_value.return_value = 'Anonymous'  # This should NOT be called

        template.required_placeholders = []
        template.optional_placeholders = [author_placeholder]

        repository.get_template.return_value = template
        validator.validate_template.return_value = []

        service = TemplateService(repository=repository, validator=validator, prompter=prompter)

        # Provide a value for the optional placeholder
        result = service.create_content_from_single_template('test-template', {'author': 'Jane Doe'}, interactive=False)

        assert result['success'] is True
        # Verify the provided value was used, NOT the default
        template.render.assert_called_once()
        call_args = template.render.call_args[0][0]
        assert 'author' in call_args
        assert call_args['author'] == 'Jane Doe'

        # Verify default was NOT retrieved since value was provided
        author_placeholder.get_effective_value.assert_not_called()
