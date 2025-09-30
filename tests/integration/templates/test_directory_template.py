from unittest.mock import Mock

"""Integration tests for creating nodes from directory templates.

These tests verify the complete workflow of creating multiple related nodes
from a template directory structure.
"""

from pathlib import Path

import pytest

from prosemark.templates.application.use_cases.create_from_template_use_case import CreateFromTemplateUseCase


class TestDirectoryTemplateIntegration:
    """Integration tests for directory template node creation."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with directory templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create project setup template directory
        project_dir = templates_dir / 'project-setup'
        project_dir.mkdir()

        overview_template = project_dir / 'overview.md'
        overview_template.write_text(
            '---\n'
            'project: {{project_name}}\n'
            'type: overview\n'
            'description: {{project_description}}\n'
            '---\n\n'
            '# {{project_name}} Overview\n\n'
            '**Description**: {{project_description}}\n'
            '**Owner**: {{project_owner}}\n'
            '**Start Date**: {{start_date}}\n\n'
            '## Goals\n'
            '{{project_goals}}\n\n'
            '## Success Criteria\n'
            '{{success_criteria}}'
        )

        tasks_template = project_dir / 'tasks.md'
        tasks_template.write_text(
            '---\n'
            'project: {{project_name}}\n'
            'type: tasks\n'
            '---\n\n'
            '# {{project_name}} - Tasks\n\n'
            '## Backlog\n'
            '- [ ] {{first_task}}\n'
            '- [ ] {{second_task}}\n\n'
            '## In Progress\n'
            '\n\n'
            '## Done\n'
            '\n'
        )

        notes_template = project_dir / 'notes.md'
        notes_template.write_text(
            '---\n'
            'project: {{project_name}}\n'
            'type: notes\n'
            '---\n\n'
            '# {{project_name}} - Notes\n\n'
            '## Research\n'
            '{{research_notes}}\n\n'
            '## Decisions\n'
            '{{decision_log}}\n\n'
            '## Resources\n'
            '{{resource_links}}'
        )

        # Create nested directory structure
        design_dir = project_dir / 'design'
        design_dir.mkdir()

        wireframes_template = design_dir / 'wireframes.md'
        wireframes_template.write_text(
            '---\n'
            'project: {{project_name}}\n'
            'type: design\n'
            'subtype: wireframes\n'
            '---\n\n'
            '# {{project_name}} - Wireframes\n\n'
            '## User Flow\n'
            '{{user_flow}}\n\n'
            '## Key Screens\n'
            '{{key_screens}}'
        )

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self) -> Mock:
        """Create a mock user prompter for testing."""
        prompter = Mock()

        # This will fail until PlaceholderValue is implemented
        try:
            from prosemark.templates.domain.entities.placeholder import PlaceholderValue  # type: ignore[import-untyped]

            prompter.prompt_for_placeholder_values.return_value = {
                'project_name': PlaceholderValue('project_name', 'My Awesome Project', 'user_input'),
                'project_description': PlaceholderValue('project_description', 'A revolutionary new app', 'user_input'),
                'project_owner': PlaceholderValue('project_owner', 'John Doe', 'user_input'),
                'start_date': PlaceholderValue('start_date', '2025-10-01', 'user_input'),
                'project_goals': PlaceholderValue('project_goals', 'Improve user productivity', 'user_input'),
                'success_criteria': PlaceholderValue('success_criteria', '10k active users', 'user_input'),
                'first_task': PlaceholderValue('first_task', 'Set up development environment', 'user_input'),
                'second_task': PlaceholderValue('second_task', 'Design database schema', 'user_input'),
                'research_notes': PlaceholderValue('research_notes', 'Market analysis complete', 'user_input'),
                'decision_log': PlaceholderValue('decision_log', 'Using React for frontend', 'user_input'),
                'resource_links': PlaceholderValue('resource_links', 'docs.example.com', 'user_input'),
                'user_flow': PlaceholderValue('user_flow', 'Login → Dashboard → Action', 'user_input'),
                'key_screens': PlaceholderValue('key_screens', 'Login, Dashboard, Settings', 'user_input'),
            }
        except ImportError:
            # Expected failure for TDD
            pass

        return prompter

    def test_create_nodes_from_directory_template_success(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test successfully creating multiple nodes from directory template."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            # Create nodes from directory template
            result = use_case.create_from_template_directory(
                template_directory_name='project-setup', templates_directory=temp_templates_dir
            )

            assert result.success is True
            assert result.created_nodes is not None
            assert len(result.created_nodes) >= 4  # 3 root files + 1 nested file

            # Check that all expected nodes were created
            node_names = [node.name for node in result.created_nodes]
            assert any('overview' in name for name in node_names)
            assert any('tasks' in name for name in node_names)
            assert any('notes' in name for name in node_names)
            assert any('wireframes' in name for name in node_names)

            # Check that placeholders were replaced consistently
            for node in result.created_nodes:
                assert 'My Awesome Project' in node.content
                assert '{{project_name}}' not in node.content

    def test_create_nodes_preserves_directory_structure(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test that created nodes preserve the original directory structure."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            use_case.create_from_template_directory(
                template_directory_name='project-setup', templates_directory=temp_templates_dir
            )

            # Check that directory structure is preserved in output
            assert (output_dir / 'overview.md').exists()
            assert (output_dir / 'tasks.md').exists()
            assert (output_dir / 'notes.md').exists()
            assert (output_dir / 'design').exists()
            assert (output_dir / 'design' / 'wireframes.md').exists()

    def test_create_nodes_shared_placeholders_consistency(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test that shared placeholders are replaced consistently across all files."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            result = use_case.create_from_template_directory(
                template_directory_name='project-setup', templates_directory=temp_templates_dir
            )

            # All nodes should have consistent project name
            project_name = 'My Awesome Project'
            for node in result.created_nodes:
                assert project_name in node.content

                # Check frontmatter consistency
                if 'project:' in node.content:
                    assert f'project: {project_name}' in node.content

    def test_create_nodes_directory_template_not_found(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test creating nodes from non-existent directory template."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateDirectoryNotFoundError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            with pytest.raises(TemplateDirectoryNotFoundError):
                use_case.create_from_template_directory(
                    template_directory_name='nonexistent-directory', templates_directory=temp_templates_dir
                )

    def test_create_nodes_empty_directory_template(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test creating nodes from empty directory template."""
        # Create empty directory
        empty_dir = temp_templates_dir / 'empty-template'
        empty_dir.mkdir()

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                EmptyTemplateDirectoryError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            with pytest.raises(EmptyTemplateDirectoryError):
                use_case.create_from_template_directory(
                    template_directory_name='empty-template', templates_directory=temp_templates_dir
                )

    def test_create_nodes_invalid_template_in_directory(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test handling directory with some invalid templates."""
        # Add invalid template to project directory
        project_dir = temp_templates_dir / 'project-setup'
        invalid_template = project_dir / 'invalid.md'
        invalid_template.write_text(
            '---\n'
            'title: {{title}\n'  # Invalid YAML
            '---\n\n'
            'Content'
        )

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateValidationError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_user_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            # Should halt on first invalid template (fail-fast behavior)
            with pytest.raises(TemplateValidationError):
                use_case.create_from_template_directory(
                    template_directory_name='project-setup', templates_directory=temp_templates_dir
                )

    def test_create_nodes_user_cancellation_during_directory_processing(
        self, temp_templates_dir: Path, tmp_path: Path
    ) -> None:
        """Test handling user cancellation during directory template processing."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                UserCancelledError,  # type: ignore[import-untyped]
            )

            # Mock prompter that raises cancellation
            mock_prompter = Mock()
            mock_prompter.prompt_for_placeholder_values.side_effect = UserCancelledError('User cancelled')

            repository = FileTemplateRepository(temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            template_service = TemplateService(repository, validator, mock_prompter)
            use_case = CreateFromTemplateUseCase(template_service)

            with pytest.raises(UserCancelledError):
                use_case.create_from_template_directory(
                    template_directory_name='project-setup', templates_directory=temp_templates_dir
                )
