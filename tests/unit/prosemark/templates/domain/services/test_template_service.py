"""Unit tests for TemplateService."""

from unittest.mock import Mock

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateNotFoundError,
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
