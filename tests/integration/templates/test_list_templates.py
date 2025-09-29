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
            'title: {{meeting_title}}\n'
            'date: {{meeting_date}}\n'
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
            'date: {{current_date}}\n'
            'mood: {{mood}}\n'
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
            'project: {{project_name}}\n'
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
            'project: {{project_name}}\n'
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
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            # Create repository implementation (would fail until implemented)
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            templates = use_case.list_individual_templates(temp_templates_dir)

            assert len(templates) >= 2
            template_names = [t.name for t in templates]
            assert 'meeting-notes' in template_names
            assert 'daily-journal' in template_names

    def test_list_template_directories_success(self, temp_templates_dir: Path) -> None:
        """Test successfully listing template directories."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            directories = use_case.list_template_directories(temp_templates_dir)

            assert len(directories) >= 1
            directory_names = [d.name for d in directories]
            assert 'project-setup' in directory_names

    def test_list_all_templates_success(self, temp_templates_dir: Path) -> None:
        """Test successfully listing all templates (individual + directories)."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            all_templates = use_case.list_all_templates(temp_templates_dir)

            assert 'individual_templates' in all_templates
            assert 'template_directories' in all_templates

            individual = all_templates['individual_templates']
            directories = all_templates['template_directories']

            assert len(individual) >= 2
            assert len(directories) >= 1

    def test_list_templates_empty_directory(self, tmp_path: Path) -> None:
        """Test listing templates in empty directory."""
        empty_dir = tmp_path / 'empty'
        empty_dir.mkdir()

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            templates = use_case.list_individual_templates(empty_dir)
            assert len(templates) == 0

            directories = use_case.list_template_directories(empty_dir)
            assert len(directories) == 0

    def test_list_templates_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test listing templates in nonexistent directory."""
        nonexistent_dir = tmp_path / 'nonexistent'

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateDirectoryNotFoundError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            with pytest.raises(TemplateDirectoryNotFoundError):
                use_case.list_individual_templates(nonexistent_dir)

    def test_list_templates_with_validation(self, temp_templates_dir: Path) -> None:
        """Test listing templates with content validation."""
        # Add an invalid template file
        invalid_template = temp_templates_dir / 'invalid.md'
        invalid_template.write_text('Invalid content without frontmatter')

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            use_case = ListTemplatesUseCase(repository, validator)

            # Should filter out invalid templates
            templates = use_case.list_valid_templates_only(temp_templates_dir)

            template_names = [t.name for t in templates]
            assert 'invalid' not in template_names
            assert 'meeting-notes' in template_names
            assert 'daily-journal' in template_names

    def test_list_templates_for_cli_display(self, temp_templates_dir: Path) -> None:
        """Test listing templates in format suitable for CLI display."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import FileTemplateRepository  # type: ignore[import-untyped]

            repository = FileTemplateRepository()
            use_case = ListTemplatesUseCase(repository)

            cli_list = use_case.get_templates_for_cli_display(temp_templates_dir)

            assert isinstance(cli_list, list)
            assert len(cli_list) >= 3  # 2 individual + 1 directory

            # Should include directory markers
            assert any('project-setup/' in item for item in cli_list)

            # Should include individual templates
            assert any('meeting-notes' in item for item in cli_list)
            assert any('daily-journal' in item for item in cli_list)
