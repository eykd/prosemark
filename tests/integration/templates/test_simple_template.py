"""Integration tests for creating nodes from simple templates.

These tests verify the complete workflow of creating a single node
from an individual template file.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.templates.application.use_cases.create_from_template_use_case import CreateFromTemplateUseCase


class TestSimpleTemplateIntegration:
    """Integration tests for simple template node creation."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with simple templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a simple meeting notes template
        meeting_template = templates_dir / 'meeting-notes.md'
        meeting_template.write_text(
            '---\n'
            'title: "{{meeting_title}}"\n'
            'date: "{{meeting_date}}"\n'
            'attendees: "{{attendees}}"\n'
            '---\n\n'
            '# {{meeting_title}}\n\n'
            '**Date**: {{meeting_date}}\n'
            '**Attendees**: {{attendees}}\n\n'
            '## Agenda\n'
            '{{agenda_items}}\n\n'
            '## Notes\n'
            '\n\n'
            '## Action Items\n'
            '- [ ] {{first_action}}\n\n'
            '## Next Meeting\n'
            '**Date**: {{next_meeting_date}}'
        )

        # Create a simple journal template
        journal_template = templates_dir / 'daily-journal.md'
        journal_template.write_text(
            '---\n'
            'date: "{{current_date}}"\n'
            'mood: "{{mood}}"\n'
            'weather: "{{weather}}"\n'
            '---\n\n'
            '# Daily Journal - {{current_date}}\n\n'
            '**Mood**: {{mood}}\n'
            '**Weather**: {{weather}}\n\n'
            '## What happened today?\n'
            '{{daily_events}}\n\n'
            '## Lessons learned\n'
            '{{lessons}}\n\n'
            "## Tomorrow's priorities\n"
            '{{tomorrow_priorities}}'
        )

        return templates_dir

    @pytest.fixture
    def mock_user_prompter(self):
        """Create a mock user prompter for testing."""
        prompter = Mock()

        # This will fail until PlaceholderValue is implemented
        try:
            from prosemark.templates.domain.entities.placeholder import PlaceholderValue  # type: ignore[import-untyped]

            prompter.prompt_for_placeholder_values.return_value = {
                'meeting_title': PlaceholderValue('meeting_title', 'Sprint Planning', 'user_input'),
                'meeting_date': PlaceholderValue('meeting_date', '2025-09-29', 'user_input'),
                'attendees': PlaceholderValue('attendees', 'Alice, Bob, Charlie', 'user_input'),
                'agenda_items': PlaceholderValue('agenda_items', 'Sprint review\nPlanning poker', 'user_input'),
                'first_action': PlaceholderValue('first_action', 'Update user stories', 'user_input'),
                'next_meeting_date': PlaceholderValue('next_meeting_date', '2025-10-06', 'user_input'),
            }
        except ImportError:
            # Expected failure for TDD
            pass

        return prompter

    def test_create_node_from_simple_template_success(
        self, temp_templates_dir: Path, mock_user_prompter, tmp_path: Path
    ) -> None:
        """Test successfully creating a node from a simple template."""
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

            repository = FileTemplateRepository(templates_root=temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            template_service = TemplateService(repository, validator, mock_user_prompter)
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(template_service)

            # Create node from template
            result = use_case.create_single_template(
                template_name='meeting-notes', interactive=False
            )

            assert result.success is True
            assert result.created_nodes is not None
            assert len(result.created_nodes) == 1

            created_node = result.created_nodes[0]
            assert created_node.name == 'Sprint Planning'
            assert 'Sprint Planning' in created_node.content
            assert '2025-09-29' in created_node.content
            assert 'Alice, Bob, Charlie' in created_node.content
            assert '{{meeting_title}}' not in created_node.content  # Placeholders replaced

    def test_create_node_with_default_values(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test creating node with some default placeholder values."""
        # Create template with default values
        template_with_defaults = temp_templates_dir / 'quick-note.md'
        template_with_defaults.write_text(
            '---\n'
            'title: "{{title}}"\n'
            'author: "{{author:Anonymous}}"\n'
            'date: "{{date:today}}"\n'
            '---\n\n'
            '# {{title}}\n\n'
            '**Author**: {{author}}\n'
            '**Date**: {{date}}\n\n'
            '{{content}}'
        )

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.services.template_service import (
                TemplateService,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository(templates_root=temp_templates_dir)
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            template_service = TemplateService(repository, validator, prompter)
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(template_service)

            result = use_case.create_single_template(template_name='quick-note', interactive=False)

            assert result.success is True
            created_node = result.created_nodes[0]

            # Should use default values where user didn't provide input
            assert 'Anonymous' in created_node.content or 'today' in created_node.content

    def test_create_node_template_not_found(self, temp_templates_dir: Path, mock_user_prompter, tmp_path: Path) -> None:
        """Test creating node from non-existent template."""
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
            TemplateNotFoundError,  # type: ignore[import-untyped]
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.create_single_template(
            template_name='nonexistent-template', interactive=False
        )

        assert result['success'] is False
        assert result['error_type'] == 'TemplateNotFoundError'

    def test_create_node_invalid_template_content(
        self, temp_templates_dir: Path, mock_user_prompter, tmp_path: Path
    ) -> None:
        """Test creating node from template with invalid content."""
        # Create invalid template
        invalid_template = temp_templates_dir / 'invalid.md'
        invalid_template.write_text(
            '---\n'
            'title: {{title}\n'  # Invalid YAML
            'type: document\n'
            '---\n\n'
            '# Content'
        )

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

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        template_service = TemplateService(repository, validator, mock_user_prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.create_single_template(template_name='invalid', interactive=False)

        assert result['success'] is False
        assert result['error_type'] in ['TemplateValidationError', 'TemplateParseError']

    def test_create_node_user_cancellation(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test handling user cancellation during placeholder input."""
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

        result = use_case.create_single_template(template_name='meeting-notes', interactive=True)

        assert result['success'] is False
        assert result['error_type'] == 'UserCancelledError'

    def test_create_node_placeholder_validation_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test handling invalid placeholder values from user."""
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
            InvalidPlaceholderValueError,  # type: ignore[import-untyped]
        )

        # Mock prompter that provides invalid values
        mock_prompter = Mock()
        mock_prompter.prompt_for_placeholder_values.side_effect = InvalidPlaceholderValueError(
            'Invalid placeholder value'
        )

        repository = FileTemplateRepository(temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        template_service = TemplateService(repository, validator, mock_prompter)
        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.create_single_template(template_name='meeting-notes', interactive=True)

        assert result['success'] is False
        assert result['error_type'] == 'InvalidPlaceholderValueError'
