from unittest.mock import Mock

"""Integration tests for creating nodes from directory templates.

These tests verify the complete workflow of creating multiple related nodes
from a template directory structure.
"""

from pathlib import Path
from typing import Any, NamedTuple

import pytest

from prosemark.templates.application.use_cases.create_from_template_use_case import CreateFromTemplateUseCase


class MockNode:
    """A mock node for testing template creation."""

    def __init__(self, name: str, content: str) -> None:
        self.name = name
        self.content = content


class TemplateCreationResult(NamedTuple):
    """A stub for mocked template creation result."""

    success: bool
    created_nodes: list[MockNode]


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
            'project: "{{project_name}}"\n'
            'category: overview\n'
            'description: "{{project_description}}"\n'
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
            'project: "{{project_name}}"\n'
            'category: tasks\n'
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
            'project: "{{project_name}}"\n'
            'category: notes\n'
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
            'project: "{{project_name}}"\n'
            'category: design\n'
            'subcategory: wireframes\n'
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
            from prosemark.templates.domain.entities.placeholder import PlaceholderValue

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
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        # Create nodes from directory template
        result = use_case.create_directory_template(template_directory_name='project-setup')

        assert result['success'] is True
        assert 'content' in result
        content_map = result['content']
        assert len(content_map) >= 1  # at least one node

        # Check that all expected nodes were created
        file_names = list(content_map.keys())
        assert any('overview' in name for name in file_names)

        # Check that placeholders were replaced consistently
        for node_content in content_map.values():
            assert 'My Awesome Project' in node_content

    def test_create_nodes_preserves_directory_structure(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test that created nodes preserve the original directory structure."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.create_directory_template(template_directory_name='project-setup')

        # Verify successful creation
        assert result['success'] is True
        content_map = result['content']

        # Check that all files are present in content map
        # Keys are template basenames without .md extension
        assert 'overview' in content_map
        assert 'tasks' in content_map
        assert 'notes' in content_map
        assert 'wireframes' in content_map

        # Verify all placeholders were replaced
        for content in content_map.values():
            assert 'My Awesome Project' in content

    def test_create_nodes_shared_placeholders_consistency(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test that shared placeholders are replaced consistently across all files."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        result: dict[str, Any] = use_case.create_directory_template(template_directory_name='project-setup')

        # Verify successful creation
        assert result['success'] is True

        # All nodes should have consistent project name
        project_name = 'My Awesome Project'
        for node_content in result['content'].values():
            assert project_name in node_content

            # Check frontmatter consistency - the value is quoted in YAML
            if 'project:' in node_content:
                assert f'project: "{project_name}"' in node_content or f'project: {project_name}' in node_content

    def test_create_nodes_directory_template_not_found(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test creating nodes from non-existent directory template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        # Should return error result for non-existent directory (not raise exception)
        result = use_case.create_directory_template(template_directory_name='nonexistent-directory')

        assert result['success'] is False
        assert 'error' in result
        assert 'TemplateDirectoryNotFoundError' in result['error_type']

    def test_create_nodes_empty_directory_template(
        self, temp_templates_dir: Path, mock_user_prompter: Mock, tmp_path: Path
    ) -> None:
        """Test creating nodes from empty directory template."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        # Create empty directory
        empty_dir = temp_templates_dir / 'empty-template'
        empty_dir.mkdir()

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        # Should return error result for empty directory (not raise exception)
        result = use_case.create_directory_template(template_directory_name='empty-template')

        assert result['success'] is False
        assert 'error' in result

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

        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.services.template_service import TemplateService

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_user_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        # Should return error result for invalid template (not raise exception)
        result = use_case.create_directory_template(template_directory_name='project-setup')

        assert result['success'] is False
        assert 'error' in result

    def test_create_nodes_user_cancellation_during_directory_processing(
        self, temp_templates_dir: Path, tmp_path: Path
    ) -> None:
        """Test handling user cancellation during directory template processing."""
        from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
        from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
        from prosemark.templates.domain.exceptions.template_exceptions import UserCancelledError
        from prosemark.templates.domain.services.template_service import TemplateService

        # Mock prompter that raises cancellation
        mock_prompter = Mock()
        mock_prompter.prompt_for_placeholder_values.side_effect = UserCancelledError('User cancelled')

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()

        template_service = TemplateService(repository, validator, mock_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        # Should return error result for user cancellation (not raise exception)
        result = use_case.create_directory_template(template_directory_name='project-setup')

        assert result['success'] is False
        assert 'error' in result
        assert 'UserCancelledError' in result['error_type']
