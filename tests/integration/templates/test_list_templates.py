"""Integration tests for listing templates functionality.

These tests verify the complete workflow of listing available templates
from the templates directory.
"""

from pathlib import Path

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
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
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
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
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
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
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
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
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
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.exceptions.template_exceptions import (
        TemplateDirectoryNotFoundError,  # type: ignore[import-untyped]
        )

        with pytest.raises(TemplateDirectoryNotFoundError):
            repository = FileTemplateRepository(templates_root=nonexistent_dir)

    def test_list_templates_with_validation(self, temp_templates_dir: Path) -> None:
        """Test listing templates with content validation."""
        # Add an invalid template file
        invalid_template = temp_templates_dir / 'invalid.md'
        invalid_template.write_text('Invalid content without frontmatter')

        # Test now passes as use case is implemented
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
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
        from prosemark.templates.adapters.file_template_repository import (
        FileTemplateRepository,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
        ProsemarkTemplateValidator,  # type: ignore[import-untyped]
        )
        from prosemark.templates.adapters.cli_user_prompter import (
        CLIUserPrompter,  # type: ignore[import-untyped]
        )
        from prosemark.templates.domain.services.template_service import (
        TemplateService,  # type: ignore[import-untyped]
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
