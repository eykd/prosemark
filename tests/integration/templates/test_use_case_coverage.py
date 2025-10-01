"""Integration tests for CreateFromTemplateUseCase edge cases and error paths.

These tests specifically target uncovered code paths to achieve 100% coverage.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.templates.application.use_cases.create_from_template_use_case import CreateFromTemplateUseCase
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class TestCreateFromTemplateUseCaseNonInteractive:
    """Test non-interactive mode with missing placeholders."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with a simple template."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a template with required placeholders
        template = templates_dir / 'test-template.md'
        template.write_text('---\ntitle: "{{title}}"\nauthor: "{{author}}"\n---\n\n# {{title}}\n\nBy {{author}}')

        return templates_dir

    @pytest.fixture
    def temp_directory_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with a directory template."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a directory template with two .md files
        dir_template = templates_dir / 'project-template'
        dir_template.mkdir()

        readme = dir_template / 'README.md'
        readme.write_text('---\nproject_name: "{{project_name}}"\n---\n\n# {{project_name}}\n')

        config = dir_template / 'config.md'
        config.write_text('---\nproject_name: "{{project_name}}"\n---\n\nProject name: {{project_name}}')

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_create_single_template_non_interactive_missing_placeholders(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test non-interactive mode fails when required placeholders are missing."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        # Call with interactive=False and incomplete placeholder values
        result = use_case.create_single_template(
            'test-template',
            placeholder_values={'title': 'My Title'},  # Missing 'author'
            interactive=False,
        )

        assert result['success'] is False
        assert result['template_name'] == 'test-template'
        assert result['template_type'] == 'single'
        assert 'Missing values for required placeholders' in result['error']
        assert result['error_type'] == 'InvalidPlaceholderValueError'

    def test_create_single_template_non_interactive_all_values_provided(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test non-interactive mode succeeds when all required placeholders are provided."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        # Call with interactive=False and all placeholder values
        result = use_case.create_single_template(
            'test-template',
            placeholder_values={'title': 'My Title', 'author': 'John Doe'},
            interactive=False,
        )

        assert result['success'] is True
        assert result['template_name'] == 'test-template'
        assert result['template_type'] == 'single'
        assert 'My Title' in result['content']
        assert 'John Doe' in result['content']

    def test_create_directory_template_non_interactive_missing_placeholders(
        self, temp_directory_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test non-interactive directory template fails when required placeholders are missing."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_directory_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        # Call with interactive=False and no placeholder values
        result = use_case.create_directory_template(
            'project-template',
            placeholder_values={},  # Missing 'project_name'
            interactive=False,
        )

        assert result['success'] is False
        assert result['template_name'] == 'project-template'
        assert result['template_type'] == 'directory'
        assert 'Missing values for required placeholders' in result['error']
        assert result['error_type'] == 'InvalidPlaceholderValueError'

    def test_create_directory_template_non_interactive_all_values_provided(
        self, temp_directory_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test non-interactive directory template succeeds when all required placeholders are provided."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_directory_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        # Call with interactive=False and all placeholder values
        result = use_case.create_directory_template(
            'project-template',
            placeholder_values={'project_name': 'MyProject'},
            interactive=False,
        )

        assert result['success'] is True
        assert result['template_name'] == 'project-template'
        assert result['template_type'] == 'directory'
        assert result['file_count'] == 2
        assert 'README' in result['content']
        assert 'config' in result['content']


class TestCreateFromTemplateUseCaseValidation:
    """Test template validation methods."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a simple template
        template = templates_dir / 'simple.md'
        template.write_text(
            '---\n'
            'title: "{{title}}"\n'
            'description: "{{description}}"\n'
            'description_default: "No description"\n'
            '---\n\n'
            '# {{title}}\n\n'
            '{{description}}'
        )

        # Create a directory template
        dir_template = templates_dir / 'dir-template'
        dir_template.mkdir()

        file1 = dir_template / 'file1.md'
        file1.write_text('---\nname: "{{name}}"\n---\n\n# {{name}}\n')

        file2 = dir_template / 'file2.md'
        file2.write_text('---\nname: "{{name}}"\n---\n\nAuthor: {{name}}\n')

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_validate_template_before_creation_not_found(
        self, tmp_path: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test validation fails for non-existent template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.validate_template_before_creation('non-existent')

        assert result['success'] is False
        assert result['template_name'] == 'non-existent'
        assert result['template_type'] == 'single'
        assert result['valid'] is False
        assert result['error_type'] == 'TemplateNotFoundError'

    def test_validate_template_before_creation_success(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test validation succeeds for valid template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.validate_template_before_creation('simple')

        assert result['success'] is True
        assert result['template_name'] == 'simple'
        assert result['template_type'] == 'single'
        assert result['valid'] is True
        assert result['has_placeholders'] is True
        assert 'title' in result['required_placeholders']
        assert 'description' in result['optional_placeholders']
        assert result['placeholder_count'] == 2

    def test_validate_directory_template_before_creation_success(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test directory template validation succeeds for valid template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.validate_directory_template_before_creation('dir-template')

        assert result['success'] is True
        assert result['template_name'] == 'dir-template'
        assert result['template_type'] == 'directory'
        assert result['valid'] is True
        assert result['template_count'] == 2
        assert 'name' in result['required_placeholders']
        assert 'name' in result['shared_placeholders']

    def test_validate_directory_template_before_creation_not_found(
        self, tmp_path: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test directory validation fails for non-existent template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.validate_directory_template_before_creation('non-existent')

        assert result['success'] is False
        assert result['template_name'] == 'non-existent'
        assert result['template_type'] == 'directory'
        assert result['valid'] is False
        assert result['error_type'] == 'TemplateDirectoryNotFoundError'


class TestCreateFromTemplateUseCasePreview:
    """Test template preview functionality."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a template with required and optional placeholders
        template = templates_dir / 'preview-test.md'
        template.write_text(
            '---\n'
            'title: "{{title}}"\n'
            'author: "{{author}}"\n'
            'author_default: "Anonymous"\n'
            'date: "{{date}}"\n'
            'date_default: "2025-09-30"\n'
            '---\n\n'
            '# {{title}}\n\n'
            'By {{author}} on {{date}}'
        )

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_get_template_preview_all_values_provided(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test preview when all placeholder values are provided."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.get_template_preview(
            'preview-test',
            placeholder_values={'title': 'My Title', 'author': 'John Doe', 'date': '2025-10-01'},
        )

        assert result['success'] is True
        assert result['template_name'] == 'preview-test'
        assert result['template_type'] == 'single'
        assert result['can_generate'] is True
        assert len(result['missing_required_placeholders']) == 0
        assert 'title' in result['provided_placeholders']
        assert 'author' in result['provided_placeholders']
        assert 'date' in result['provided_placeholders']
        assert 'title' in result['all_required_placeholders']
        assert 'author' in result['all_optional_placeholders']
        assert 'date' in result['all_optional_placeholders']

    def test_get_template_preview_missing_required_placeholders(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test preview when required placeholders are missing."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.get_template_preview(
            'preview-test',
            placeholder_values={'author': 'John Doe'},  # Missing 'title'
        )

        assert result['success'] is True
        assert result['template_name'] == 'preview-test'
        assert result['template_type'] == 'single'
        assert result['can_generate'] is False
        assert 'title' in result['missing_required_placeholders']
        assert 'author' in result['provided_placeholders']
        assert 'title' in result['all_required_placeholders']

    def test_get_template_preview_no_values_provided(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test preview when no placeholder values are provided."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.get_template_preview('preview-test', placeholder_values=None)

        assert result['success'] is True
        assert result['template_name'] == 'preview-test'
        assert result['can_generate'] is False
        assert 'title' in result['missing_required_placeholders']
        assert len(result['provided_placeholders']) == 0

    def test_get_template_preview_template_not_found(
        self, tmp_path: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test preview fails for non-existent template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.get_template_preview('non-existent', placeholder_values=None)

        assert result['success'] is False
        assert result['template_name'] == 'non-existent'
        assert result['template_type'] == 'single'
        assert result['error_type'] == 'TemplateNotFoundError'
