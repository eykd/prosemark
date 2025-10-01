"""Integration tests for listing templates functionality.

These tests verify the complete workflow of listing available templates
from the templates directory.
"""

from pathlib import Path
from typing import Never

import pytest

from prosemark.templates.application.use_cases.list_templates_use_case import ListTemplatesUseCase


class TestListTemplatesIntegration:
    """Integration tests for template listing functionality."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with test templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create individual templates
        simple_template = templates_dir / 'meeting-notes.md'
        simple_template.write_text(
            '---\n'
            'title: "{{meeting_title}}"\n'
            'date: "{{meeting_date}}"\n'
            '---\n\n'
            '# {{meeting_title}}\n\n'
            'Date: {{meeting_date}}\n'
            'Attendees: {{attendees}}\n\n'
            '## Agenda\n'
            '## Notes\n'
            '## Action Items'
        )

        daily_journal = templates_dir / 'daily-journal.md'
        daily_journal.write_text(
            '---\n'
            'date: "{{current_date}}"\n'
            'mood: "{{mood}}"\n'
            '---\n\n'
            '# Daily Journal - {{current_date}}\n\n'
            '**Mood**: {{mood}}\n\n'
            '## What happened today?\n'
            '{{daily_events}}\n\n'
            '## Reflections\n'
            '{{reflections}}'
        )

        # Create template directories
        project_dir = templates_dir / 'project-setup'
        project_dir.mkdir()

        overview_template = project_dir / 'overview.md'
        overview_template.write_text(
            '---\n'
            'project: "{{project_name}}"\n'
            'type: overview\n'
            '---\n\n'
            '# {{project_name}} Overview\n\n'
            '**Description**: {{project_description}}\n\n'
            '## Goals\n'
            '## Timeline\n'
            '## Resources'
        )

        tasks_template = project_dir / 'tasks.md'
        tasks_template.write_text(
            '---\n'
            'project: "{{project_name}}"\n'
            'type: tasks\n'
            '---\n\n'
            '# {{project_name}} - Tasks\n\n'
            '## TODO\n'
            '- [ ] {{first_task}}\n\n'
            '## In Progress\n'
            '## Done'
        )

        return templates_dir

    def test_list_individual_templates_success(self, temp_templates_dir: Path) -> None:
        """Test successfully listing individual templates."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        templates = use_case.list_single_templates()

        assert templates['success'] is True
        assert len(templates['names']) >= 2
        template_names = templates['names']
        assert 'meeting-notes' in template_names
        assert 'daily-journal' in template_names

    def test_list_template_directories_success(self, temp_templates_dir: Path) -> None:
        """Test successfully listing template directories."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        directories = use_case.list_directory_templates()

        assert directories['success'] is True
        assert len(directories['names']) >= 1
        directory_names = directories['names']
        assert 'project-setup' in directory_names

    def test_list_all_templates_success(self, temp_templates_dir: Path) -> None:
        """Test successfully listing all templates (individual + directories)."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        all_templates = use_case.list_all_templates()

        assert 'single_templates' in all_templates
        assert 'directory_templates' in all_templates

        individual = all_templates['single_templates']
        directories = all_templates['directory_templates']

        assert len(individual) >= 2
        assert len(directories) >= 1

    def test_list_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test listing templates in empty directory."""
        empty_dir = tmp_path / 'empty'
        empty_dir.mkdir()

        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(empty_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        templates = use_case.list_single_templates()
        assert templates['success'] is True
        assert len(templates['names']) == 0

        directories = use_case.list_directory_templates()
        assert directories['success'] is True
        assert len(directories['names']) == 0

    def test_list_templates_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test listing templates in nonexistent directory."""
        nonexistent_dir = tmp_path / 'nonexistent'

        # Test now passes as use case is implemented
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.domain.exceptions.template_exceptions import (
            TemplateDirectoryNotFoundError,
        )

        with pytest.raises(TemplateDirectoryNotFoundError):
            FileTemplateRepository(templates_root=nonexistent_dir)

    def test_list_templates_with_validation(self, temp_templates_dir: Path) -> None:
        """Test listing templates with content validation."""
        # Add an invalid template file
        invalid_template = temp_templates_dir / 'invalid.md'
        invalid_template.write_text('Invalid content without frontmatter')

        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Should filter out invalid templates
        templates = use_case.list_single_templates()

        assert templates['success'] is True
        template_names = templates['names']
        assert 'invalid' not in template_names
        assert 'meeting-notes' in template_names
        assert 'daily-journal' in template_names

    def test_list_templates_for_cli_display(self, temp_templates_dir: Path) -> None:
        """Test listing templates in format suitable for CLI display."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import (
            CLIUserPrompter,
        )
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        all_templates = use_case.list_all_templates()

        assert all_templates['success'] is True
        assert 'single_templates' in all_templates
        assert 'directory_templates' in all_templates

        # Check we have individual templates and directories
        single_templates = all_templates['single_templates']['names']
        directory_templates = all_templates['directory_templates']['names']

        assert len(single_templates) >= 2  # 2 individual templates
        assert len(directory_templates) >= 1  # 1 directory

        # Should include directory templates
        assert 'project-setup' in directory_templates

        # Should include individual templates
        assert 'meeting-notes' in single_templates
        assert 'daily-journal' in single_templates

    def test_list_all_templates_with_error_in_get_info(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_all_templates continues when get_template_info fails."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock get_template_info to raise error for one template
        original_get_template_info = template_service.get_template_info

        def mock_get_template_info(name: str) -> dict[str, object]:
            if name == 'meeting-notes':
                raise TemplateError('Simulated error')
            return original_get_template_info(name)

        monkeypatch.setattr(template_service, 'get_template_info', mock_get_template_info)

        all_templates = use_case.list_all_templates()

        assert all_templates['success'] is True
        # Should still have other template
        single_templates = all_templates['single_templates']['details']
        template_names = [t['name'] for t in single_templates]
        assert 'meeting-notes' not in template_names
        assert 'daily-journal' in template_names

    def test_list_all_templates_with_error_in_get_directory_info(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_all_templates continues when get_directory_template_info fails."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock get_directory_template_info to raise error
        def mock_get_directory_info(name: str) -> dict[str, object]:
            raise TemplateError('Simulated error')

        monkeypatch.setattr(template_service, 'get_directory_template_info', mock_get_directory_info)

        all_templates = use_case.list_all_templates()

        assert all_templates['success'] is True
        # Should have no directory templates
        directory_templates = all_templates['directory_templates']['details']
        assert len(directory_templates) == 0

    def test_list_all_templates_with_service_error(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_all_templates handles service errors."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock list_templates to raise error
        def mock_list_templates() -> list[str]:
            raise TemplateError('Service error')

        monkeypatch.setattr(template_service, 'list_templates', mock_list_templates)

        result = use_case.list_all_templates()

        assert result['success'] is False
        assert 'error' in result
        assert 'error_type' in result
        assert result['error_type'] == 'TemplateError'

    def test_list_single_templates_with_error_in_get_info(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_single_templates handles errors in get_template_info."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock get_template_info to raise error for one template
        original_get_template_info = template_service.get_template_info

        def mock_get_template_info(name: str) -> dict[str, object]:
            if name == 'meeting-notes':
                raise TemplateError('Simulated error')
            return original_get_template_info(name)

        monkeypatch.setattr(template_service, 'get_template_info', mock_get_template_info)

        result = use_case.list_single_templates()

        assert result['success'] is True
        assert len(result['failed']) == 1
        assert result['failed'][0]['name'] == 'meeting-notes'
        assert result['failed'][0]['error'] == 'Simulated error'
        assert result['failed'][0]['error_type'] == 'TemplateError'

    def test_list_single_templates_with_service_error(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_single_templates handles service errors."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock list_templates to raise error
        def mock_list_templates() -> list[str]:
            raise TemplateError('Service error')

        monkeypatch.setattr(template_service, 'list_templates', mock_list_templates)

        result = use_case.list_single_templates()

        assert result['success'] is False
        assert result['template_type'] == 'single'
        assert 'error' in result
        assert result['error_type'] == 'TemplateError'

    def test_list_directory_templates_with_error_in_get_info(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_directory_templates handles errors in get_directory_template_info."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock get_directory_template_info to raise error
        def mock_get_directory_info(name: str) -> dict[str, object]:
            raise TemplateError('Simulated error')

        monkeypatch.setattr(template_service, 'get_directory_template_info', mock_get_directory_info)

        result = use_case.list_directory_templates()

        assert result['success'] is True
        assert len(result['failed']) == 1
        assert result['failed'][0]['name'] == 'project-setup'
        assert result['failed'][0]['error'] == 'Simulated error'

    def test_list_directory_templates_with_service_error(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test list_directory_templates handles service errors."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock list_template_directories to raise error
        def mock_list_directories() -> list[str]:
            raise TemplateError('Service error')

        monkeypatch.setattr(template_service, 'list_template_directories', mock_list_directories)

        result = use_case.list_directory_templates()

        assert result['success'] is False
        assert result['template_type'] == 'directory'
        assert 'error' in result
        assert result['error_type'] == 'TemplateError'

    def test_search_templates_by_name(self, temp_templates_dir: Path) -> None:
        """Test searching templates by name."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('meeting')

        assert result['success'] is True
        assert result['query'] == 'meeting'
        assert result['search_in_descriptions'] is True
        assert result['single_templates']['count'] >= 1
        single_results = result['single_templates']['results']
        template_names = [t['name'] for t in single_results]
        assert 'meeting-notes' in template_names

    def test_search_templates_by_placeholder(self, temp_templates_dir: Path) -> None:
        """Test searching templates by placeholder name."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('mood')

        assert result['success'] is True
        assert result['total_matches'] >= 1
        single_results = result['single_templates']['results']
        template_names = [t['name'] for t in single_results]
        assert 'daily-journal' in template_names

    def test_search_templates_in_descriptions(self, temp_templates_dir: Path) -> None:
        """Test searching templates in frontmatter descriptions with string values."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        # Create a template with a description in frontmatter
        template_with_desc = temp_templates_dir / 'documented.md'
        template_with_desc.write_text(
            '---\ntitle: "{{title}}"\ndescription: "This is a special documented template"\n---\n\n# {{title}}\n'
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Search for something in frontmatter description value
        result = use_case.search_templates('special', search_in_descriptions=True)

        assert result['success'] is True
        assert result['search_in_descriptions'] is True
        # Should find the template with "special" in description
        assert result['total_matches'] >= 1
        template_names = [t['name'] for t in result['single_templates']['results']]
        assert 'documented' in template_names

    def test_search_templates_without_descriptions(self, temp_templates_dir: Path) -> None:
        """Test searching templates without searching descriptions."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('meeting', search_in_descriptions=False)

        assert result['success'] is True
        assert result['search_in_descriptions'] is False

    def test_search_templates_no_matches(self, temp_templates_dir: Path) -> None:
        """Test searching with query that matches nothing."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.search_templates('nonexistent-query-xyz')

        assert result['success'] is True
        assert result['total_matches'] == 0

    def test_search_templates_with_service_error(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test search_templates handles service errors."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock list_templates to raise error
        def mock_list_templates() -> list[str]:
            raise TemplateError('Service error')

        monkeypatch.setattr(template_service, 'list_templates', mock_list_templates)

        result = use_case.search_templates('meeting')

        assert result['success'] is False
        assert 'error' in result
        # When list_all_templates fails, it returns early without query key
        # The query is only included in the exception handler at line 221-227

    def test_search_templates_with_template_error_during_search(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test search_templates handles TemplateError during search matching."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock _template_matches_query to raise error
        def mock_matches_query(template: dict[str, object], query_lower: str, *, search_in_descriptions: bool) -> bool:
            raise TemplateError('Matching error')

        monkeypatch.setattr(use_case, '_template_matches_query', mock_matches_query)

        result = use_case.search_templates('meeting')

        assert result['success'] is False
        assert 'error' in result
        assert result['query'] == 'meeting'
        assert result['error_type'] == 'TemplateError'

    def test_get_template_details_single_template(self, temp_templates_dir: Path) -> None:
        """Test getting details for a single template."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('meeting-notes')

        assert result['success'] is True
        assert result['template_name'] == 'meeting-notes'
        assert result['template_type'] == 'single'
        assert result['found'] is True
        assert 'details' in result

    def test_get_template_details_directory_template(self, temp_templates_dir: Path) -> None:
        """Test getting details for a directory template."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('project-setup')

        assert result['success'] is True
        assert result['template_name'] == 'project-setup'
        assert result['template_type'] == 'directory'
        assert result['found'] is True
        assert 'details' in result

    def test_get_template_details_not_found(self, temp_templates_dir: Path) -> None:
        """Test getting details for nonexistent template."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_template_details('nonexistent-template')

        assert result['success'] is True
        assert result['template_name'] == 'nonexistent-template'
        assert result['template_type'] == 'unknown'
        assert result['found'] is False
        assert 'error' in result

    def test_get_templates_with_placeholders(self, temp_templates_dir: Path) -> None:
        """Test listing templates that have placeholders."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        result = use_case.get_templates_with_placeholders()

        assert result['success'] is True
        assert 'single_templates' in result
        assert 'directory_templates' in result
        # All our test templates have placeholders
        assert result['total_with_placeholders'] > 0

    def test_get_templates_with_placeholders_service_error(
        self, temp_templates_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get_templates_with_placeholders handles TemplateError during filtering."""
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import TemplateError
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        use_case = ListTemplatesUseCase(template_service)

        # Mock list_all_templates to return success but with bad data that causes error during filtering
        original_list_all = use_case.list_all_templates

        def mock_list_all_templates() -> dict[str, object]:
            result = original_list_all()
            # Create a mock template detail that will cause an error when accessed

            class ErrorDict(dict):  # type: ignore[type-arg]
                def get(self, key: str, default: object = None) -> Never:
                    raise TemplateError('Error accessing template data')

            result['single_templates']['details'] = [ErrorDict()]
            return result

        monkeypatch.setattr(use_case, 'list_all_templates', mock_list_all_templates)

        result = use_case.get_templates_with_placeholders()

        assert result['success'] is False
        assert 'error' in result
        assert result['error_type'] == 'TemplateError'
