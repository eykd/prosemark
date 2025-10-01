"""Tests for ListTemplatesUseCase to achieve 100% coverage.

These tests target uncovered code paths in the list templates use case.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.templates.application.use_cases.list_templates_use_case import ListTemplatesUseCase
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class TestListTemplatesUseCaseErrorHandling:
    """Test error handling in list templates use case."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with valid and invalid templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a valid template
        valid_template = templates_dir / 'valid.md'
        valid_template.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        # Create an invalid template (missing frontmatter end marker)
        invalid_template = templates_dir / 'invalid.md'
        invalid_template.write_text('---\ntitle: "{{title}}"\n# Missing frontmatter end\n')

        # Create a valid directory template
        valid_dir = templates_dir / 'valid-dir'
        valid_dir.mkdir()
        (valid_dir / 'file.md').write_text('---\nname: "{{name}}"\n---\n\n# {{name}}\n')

        # Create an invalid directory template (with invalid file)
        invalid_dir = templates_dir / 'invalid-dir'
        invalid_dir.mkdir()
        (invalid_dir / 'bad.md').write_text('---\nincomplete frontmatter')

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_list_all_templates_skips_failed_templates(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test that list_all_templates skips templates that fail to load."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.list_all_templates()

        assert result['success'] is True
        # Should only include valid templates
        assert result['single_templates']['count'] == 1
        assert result['directory_templates']['count'] == 1
        # Invalid templates are skipped, not included

    def test_list_single_templates_records_failed_templates(self, mock_user_prompter: UserPrompterPort) -> None:
        """Test that list_single_templates records failed templates."""
        from unittest.mock import Mock

        from prosemark.templates.domain.exceptions.template_exceptions import TemplateNotFoundError
        from prosemark.templates.domain.services.template_service import TemplateService

        # Mock template service that returns template names but fails on one
        mock_service = Mock(spec=TemplateService)
        mock_service.list_templates.return_value = ['valid', 'invalid']

        # First call succeeds, second fails
        def get_template_info_side_effect(name: str) -> dict[str, object]:
            if name == 'valid':
                return {
                    'name': 'valid',
                    'path': '/tmp/valid.md',
                    'placeholder_count': 0,
                    'required_placeholders': [],
                    'optional_placeholders': [],
                }
            raise TemplateNotFoundError(template_name='invalid', search_path='/tmp')

        mock_service.get_template_info.side_effect = get_template_info_side_effect

        use_case = ListTemplatesUseCase(mock_service)

        result = use_case.list_single_templates()

        assert result['success'] is True
        assert result['count'] == 1  # Only valid template
        assert len(result['failed']) == 1  # One failed template recorded
        assert result['failed'][0]['name'] == 'invalid'

    def test_list_directory_templates_records_failed_directories(self, mock_user_prompter: UserPrompterPort) -> None:
        """Test that list_directory_templates records failed directories."""
        from unittest.mock import Mock

        from prosemark.templates.domain.exceptions.template_exceptions import TemplateDirectoryNotFoundError
        from prosemark.templates.domain.services.template_service import TemplateService

        # Mock template service that returns directory names but fails on one
        mock_service = Mock(spec=TemplateService)
        mock_service.list_template_directories.return_value = ['valid-dir', 'invalid-dir']

        # First call succeeds, second fails
        def get_directory_info_side_effect(name: str) -> dict[str, object]:
            if name == 'valid-dir':
                return {
                    'name': 'valid-dir',
                    'path': '/tmp/valid-dir',
                    'template_count': 1,
                    'templates': [],
                    'required_placeholders': [],
                    'optional_placeholders': [],
                }
            raise TemplateDirectoryNotFoundError(directory_path='/tmp/invalid-dir')

        mock_service.get_directory_template_info.side_effect = get_directory_info_side_effect

        use_case = ListTemplatesUseCase(mock_service)

        result = use_case.list_directory_templates()

        assert result['success'] is True
        assert result['count'] == 1  # Only valid directory
        assert len(result['failed']) == 1  # One failed directory recorded
        assert result['failed'][0]['name'] == 'invalid-dir'


class TestListTemplatesUseCaseSearch:
    """Test search functionality."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create templates for search testing."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Template with "meeting" in name
        meeting_template = templates_dir / 'meeting-notes.md'
        meeting_template.write_text(
            '---\ntitle: "{{title}}"\ndescription: "Template for taking meeting notes"\n---\n\n# {{title}}\n'
        )

        # Template with "journal" in name
        journal_template = templates_dir / 'daily-journal.md'
        journal_template.write_text(
            '---\ndate: "{{date}}"\nmood: "{{mood}}"\ndescription: "Daily reflection template"\n---\n\n# Journal\n'
        )

        # Directory template
        project_dir = templates_dir / 'project-template'
        project_dir.mkdir()
        (project_dir / 'README.md').write_text(
            '---\n'
            'project_name: "{{project_name}}"\n'
            'description: "Project documentation template"\n'
            '---\n\n'
            '# {{project_name}}\n'
        )

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_search_templates_by_name(self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort) -> None:
        """Test searching templates by name."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('meeting')

        assert result['success'] is True
        assert result['query'] == 'meeting'
        assert result['single_templates']['count'] == 1
        assert result['single_templates']['results'][0]['name'] == 'meeting-notes'

    def test_search_templates_by_placeholder_name(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test searching templates by placeholder name."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('mood')

        assert result['success'] is True
        assert result['single_templates']['count'] == 1
        assert result['single_templates']['results'][0]['name'] == 'daily-journal'

    def test_search_templates_in_descriptions(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test searching templates in descriptions."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('reflection', search_in_descriptions=True)

        assert result['success'] is True
        assert result['search_in_descriptions'] is True
        assert result['single_templates']['count'] == 1
        assert result['single_templates']['results'][0]['name'] == 'daily-journal'

    def test_search_templates_without_descriptions(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test searching templates without searching descriptions."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('reflection', search_in_descriptions=False)

        assert result['success'] is True
        assert result['search_in_descriptions'] is False
        # Should not find anything since "reflection" is only in description
        assert result['total_matches'] == 0


class TestListTemplatesUseCaseDetails:
    """Test get_template_details functionality."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create templates for details testing."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Single template
        single = templates_dir / 'single-template.md'
        single.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        # Directory template
        directory = templates_dir / 'directory-template'
        directory.mkdir()
        (directory / 'file.md').write_text('---\nname: "{{name}}"\n---\n\n# {{name}}\n')

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_get_template_details_single_template(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test getting details for a single template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('single-template')

        assert result['success'] is True
        assert result['template_name'] == 'single-template'
        assert result['template_type'] == 'single'
        assert result['found'] is True
        assert 'details' in result

    def test_get_template_details_directory_template(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test getting details for a directory template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('directory-template')

        assert result['success'] is True
        assert result['template_name'] == 'directory-template'
        assert result['template_type'] == 'directory'
        assert result['found'] is True
        assert 'details' in result

    def test_get_template_details_not_found(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test getting details for a non-existent template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('non-existent')

        assert result['success'] is True
        assert result['template_name'] == 'non-existent'
        assert result['template_type'] == 'unknown'
        assert result['found'] is False
        assert 'not found' in result['error']


class TestListTemplatesUseCasePlaceholders:
    """Test get_templates_with_placeholders functionality."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create templates with and without placeholders."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Template with placeholders
        with_placeholders = templates_dir / 'with-placeholders.md'
        with_placeholders.write_text(
            '---\ntitle: "{{title}}"\nauthor: "{{author}}"\n---\n\n# {{title}}\nBy {{author}}\n'
        )

        # Template without placeholders (all have defaults)
        without_placeholders = templates_dir / 'without-placeholders.md'
        without_placeholders.write_text('---\ntitle: "{{title}}"\ntitle_default: "Default Title"\n---\n\n# {{title}}\n')

        # Directory template with placeholders
        dir_with = templates_dir / 'dir-with-placeholders'
        dir_with.mkdir()
        (dir_with / 'file.md').write_text('---\nname: "{{name}}"\n---\n\n# {{name}}\n')

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> UserPrompterPort:
        """Create a mock user prompter."""
        return Mock(spec=UserPrompterPort)

    def test_get_templates_with_placeholders(
        self, temp_templates_dir: Path, mock_user_prompter: UserPrompterPort
    ) -> None:
        """Test getting templates that have required placeholders."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)

        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_templates_with_placeholders()

        assert result['success'] is True
        # Both templates have placeholders (required or optional)
        assert result['single_templates']['count'] == 2
        assert result['directory_templates']['count'] == 1
        assert result['total_with_placeholders'] == 3
