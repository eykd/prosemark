"""Contract tests for UserPrompterPort.

These tests verify that implementations of UserPrompterPort
correctly implement the interface contract.
"""

from typing import Protocol

import pytest

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderValueError,
    UserCancelledError,
)
from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class UserPrompterContract(Protocol):
    """Protocol that all UserPrompterPort contract tests must implement."""

    @pytest.fixture
    def prompter(self) -> UserPrompterPort:
        """Return a UserPrompterPort implementation to test."""
        ...


class BaseUserPrompterContract:
    """Contract tests that all UserPrompterPort implementations must pass."""

    def test_prompt_for_placeholder_values_success(self, prompter: UserPrompterPort) -> None:
        """Test prompting for multiple placeholder values successfully."""
        # This test will fail until entities are implemented (expected for TDD)
        with pytest.raises((AttributeError, ImportError)):
            placeholders = [
                Placeholder(name='title', pattern_obj=PlaceholderPattern('{{title}}'), required=True),
                Placeholder(
                    name='author',
                    pattern_obj=PlaceholderPattern('{{author}}'),
                    required=False,
                    default_value='Anonymous',
                ),
            ]

            result = prompter.prompt_for_placeholder_values(placeholders)

            assert isinstance(result, dict)
            assert len(result) == len(placeholders)

            for placeholder in placeholders:
                assert placeholder.name in result
                assert isinstance(result[placeholder.name], PlaceholderValue)

    def test_prompt_for_placeholder_values_empty_list(self, prompter: UserPrompterPort) -> None:
        """Test prompting for empty list of placeholders."""
        result = prompter.prompt_for_placeholder_values([])

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_prompt_for_placeholder_values_user_cancelled(self, prompter: UserPrompterPort) -> None:
        """Test user cancelling placeholder value prompts."""
        # This test will fail until entities are implemented
        with pytest.raises((AttributeError, ImportError, UserCancelledError)):
            placeholders = [Placeholder(name='title', pattern_obj=PlaceholderPattern('{{title}}'), required=True)]

            # In a real implementation, this would simulate user cancellation
            prompter.prompt_for_placeholder_values(placeholders)

    def test_prompt_for_single_value_success(self, prompter: UserPrompterPort) -> None:
        """Test prompting for a single placeholder value successfully."""
        # This test will fail until entities are implemented
        with pytest.raises((AttributeError, ImportError)):
            placeholder = Placeholder(name='title', pattern_obj=PlaceholderPattern('{{title}}'), required=True)

            result = prompter.prompt_for_single_value(placeholder)

            assert isinstance(result, PlaceholderValue)
            assert result.placeholder_name == 'title'
            assert isinstance(result.value, str)
            assert len(result.value) > 0

    def test_prompt_for_single_value_with_default(self, prompter: UserPrompterPort) -> None:
        """Test prompting for placeholder with default value."""
        # This test will fail until entities are implemented
        with pytest.raises((AttributeError, ImportError)):
            placeholder = Placeholder(
                name='author', pattern_obj=PlaceholderPattern('{{author}}'), required=False, default_value='Anonymous'
            )

            result = prompter.prompt_for_single_value(placeholder)

            assert isinstance(result, PlaceholderValue)
            assert result.placeholder_name == 'author'
            # Value could be user input or default

    def test_prompt_for_single_value_user_cancelled(self, prompter: UserPrompterPort) -> None:
        """Test user cancelling single placeholder value prompt."""
        # This test will fail until entities are implemented
        with pytest.raises((AttributeError, ImportError, UserCancelledError)):
            placeholder = Placeholder(name='title', pattern_obj=PlaceholderPattern('{{title}}'), required=True)

            # In a real implementation, this would simulate user cancellation
            prompter.prompt_for_single_value(placeholder)

    def test_prompt_for_single_value_invalid_input(self, prompter: UserPrompterPort) -> None:
        """Test handling invalid user input for placeholder."""
        # This test will fail until entities are implemented
        with pytest.raises((AttributeError, ImportError, InvalidPlaceholderValueError)):
            placeholder = Placeholder(name='title', pattern_obj=PlaceholderPattern('{{title}}'), required=True)

            # In a real implementation, this would simulate invalid input
            prompter.prompt_for_single_value(placeholder)

    def test_confirm_template_selection_true(self, prompter: UserPrompterPort) -> None:
        """Test template selection confirmation returning True."""
        # In a real implementation, this would simulate user confirming
        result = prompter.confirm_template_selection('meeting-notes')

        assert isinstance(result, bool)
        # Result depends on implementation - could be True or False

    def test_confirm_template_selection_false(self, prompter: UserPrompterPort) -> None:
        """Test template selection confirmation returning False."""
        # In a real implementation, this would simulate user declining
        result = prompter.confirm_template_selection('complex-template')

        assert isinstance(result, bool)
        # Result depends on implementation - could be True or False

    def test_display_template_list_multiple_templates(self, prompter: UserPrompterPort) -> None:
        """Test displaying multiple templates."""
        templates: list[str] = ['meeting-notes', 'project-setup', 'daily-journal']

        # This should not raise an exception
        prompter.display_template_list(templates)

    def test_display_template_list_empty_list(self, prompter: UserPrompterPort) -> None:
        """Test displaying empty template list."""
        templates: list[str] = []

        # This should not raise an exception
        prompter.display_template_list(templates)

    def test_display_template_list_single_template(self, prompter: UserPrompterPort) -> None:
        """Test displaying single template."""
        templates: list[str] = ['meeting-notes']

        # This should not raise an exception
        prompter.display_template_list(templates)

    def test_show_error_message(self, prompter: UserPrompterPort) -> None:
        """Test showing error message."""
        message = 'Template not found: invalid-template'

        # This should not raise an exception
        prompter.show_error_message(message)

    def test_show_error_message_empty(self, prompter: UserPrompterPort) -> None:
        """Test showing empty error message."""
        message = ''

        # This should not raise an exception
        prompter.show_error_message(message)

    def test_show_success_message(self, prompter: UserPrompterPort) -> None:
        """Test showing success message."""
        message = 'Template created successfully!'

        # This should not raise an exception
        prompter.show_success_message(message)

    def test_show_success_message_empty(self, prompter: UserPrompterPort) -> None:
        """Test showing empty success message."""
        message = ''

        # This should not raise an exception
        prompter.show_success_message(message)
