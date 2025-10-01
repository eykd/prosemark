"""CLI-based user prompter adapter for interactive placeholder input."""

import sys
from typing import Final, TextIO

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue
from prosemark.templates.domain.exceptions.template_exceptions import (
    InvalidPlaceholderValueError,
    UserCancelledError,
)
from prosemark.templates.ports.user_prompter_port import UserPrompterPort

MAX_DISPLAY_LENGTH: Final[int] = 50


class CLIUserPrompter(UserPrompterPort):
    """CLI-based implementation of user prompter for placeholder values."""

    def __init__(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
        error_stream: TextIO = sys.stderr,
    ) -> None:
        """Initialize CLI prompter with I/O streams.

        Args:
            input_stream: Stream to read user input from
            output_stream: Stream to write prompts to
            error_stream: Stream to write errors to

        """
        self._input = input_stream
        self._output = output_stream
        self._error = error_stream
        self.MAX_DISPLAY_LENGTH = MAX_DISPLAY_LENGTH

    @staticmethod
    def _format_placeholder_prompt(placeholder: Placeholder) -> str:
        """Format prompt message for a placeholder.

        Args:
            placeholder: Placeholder to create prompt for

        Returns:
            Formatted prompt message

        """
        prompt_parts = [f"Enter value for '{placeholder.name}'"]

        if placeholder.description:
            prompt_parts.append(f' ({placeholder.description})')

        if not placeholder.required and placeholder.default_value is not None:
            prompt_parts.append(f' [default: {placeholder.default_value}]')
        elif placeholder.required:  # pragma: no branch
            prompt_parts.append(' [required]')

        prompt_parts.append(': ')
        return ''.join(prompt_parts)

    def _get_user_input(self, prompt_message: str) -> str:
        """Get user input with potential keyboard interrupts.

        Args:
            prompt_message: Prompt message to display

        Returns:
            User input string

        Raises:
            UserCancelledError: If user cancels input

        """
        self._output.write(prompt_message)
        self._output.flush()

        try:
            user_input = self._input.readline()
        except KeyboardInterrupt:  # pragma: no cover
            self._output.write('\n')
            self._output.flush()
            raise UserCancelledError('User cancelled input') from None

        if not user_input:  # EOF
            raise UserCancelledError('User cancelled input (EOF)')

        return user_input.strip()

    def prompt_for_placeholder_value(self, placeholder: Placeholder) -> str:
        """Prompt user for a placeholder value.

        Args:
            placeholder: Placeholder to prompt for

        Returns:
            User-provided value

        Raises:
            UserCancelledError: If user cancels input

        """
        prompt_message = self._format_placeholder_prompt(placeholder)

        while True:
            try:
                value = self._get_user_input(prompt_message)

                # Handle empty input
                if not value:
                    if placeholder.required:
                        self._error.write(f"Error: '{placeholder.name}' is required\n")
                        self._error.flush()
                        continue
                    return placeholder.get_effective_value()

                # Validate the value
                placeholder.validate_value(value)
            except (ValueError, InvalidPlaceholderValueError) as e:  # pragma: no cover
                self._error.write(f'Error: {e}\n')
                self._error.flush()
                continue
            else:
                return value

    def prompt_for_single_value(self, placeholder: Placeholder) -> PlaceholderValue:
        """Prompt user for a single placeholder value.

        Args:
            placeholder: Placeholder requiring a value

        Returns:
            PlaceholderValue with user input

        Raises:
            UserCancelledError: If user cancels the operation
            InvalidPlaceholderValueError: If user provides invalid value

        """
        value = self.prompt_for_placeholder_value(placeholder)
        return PlaceholderValue.from_user_input(placeholder.name, value)

    def prompt_for_placeholder_values(self, placeholders: list[Placeholder]) -> dict[str, PlaceholderValue]:
        """Prompt user for values for all placeholders.

        Args:
            placeholders: List of placeholders requiring values

        Returns:
            Dictionary mapping placeholder names to their values

        Raises:
            UserCancelledError: If user cancels the operation
            InvalidPlaceholderValueError: If user provides invalid value

        """
        if not placeholders:
            return {}

        self._output.write(f'\nPlease provide values for {len(placeholders)} placeholder(s):\n\n')
        self._output.flush()

        values: dict[str, PlaceholderValue] = {}

        for i, placeholder in enumerate(placeholders, 1):
            self._output.write(f'[{i}/{len(placeholders)}] ')
            self._output.flush()

            try:
                value = self.prompt_for_placeholder_value(placeholder)
                values[placeholder.name] = PlaceholderValue.from_user_input(placeholder.name, value)
            except KeyboardInterrupt:
                self._output.write('\n')
                self._output.flush()
                raise UserCancelledError('User cancelled input') from None

            self._output.write('\n')
            self._output.flush()

        self._output.write('All placeholder values collected successfully.\n\n')
        self._output.flush()
        return values

    def prompt_for_multiple_placeholder_values(self, placeholders: list[Placeholder]) -> dict[str, str]:
        """Prompt user for multiple placeholder values.

        Args:
            placeholders: List of placeholders to prompt for

        Returns:
            Dictionary mapping placeholder names to user-provided values

        Raises:
            UserCancelledError: If user cancels input

        """
        if not placeholders:
            return {}

        self._output.write(f'\nPlease provide values for {len(placeholders)} placeholder(s):\n\n')
        self._output.flush()

        values: dict[str, str] = {}

        for i, placeholder in enumerate(placeholders, 1):
            self._output.write(f'[{i}/{len(placeholders)}] ')
            self._output.flush()

            try:
                value = self.prompt_for_placeholder_value(placeholder)
            except KeyboardInterrupt:
                self._output.write('\n')
                self._output.flush()
                raise UserCancelledError('User cancelled input') from None

            values[placeholder.name] = value
            self._output.write('\n')
            self._output.flush()

        self._output.write('All placeholder values collected successfully.\n\n')
        self._output.flush()
        return values

    def confirm_placeholder_values(self, values: dict[str, str]) -> bool:
        """Show placeholder values and ask user to confirm.

        Args:
            values: Dictionary of placeholder values to confirm

        Returns:
            True if user confirms, False if they want to re-enter

        Raises:
            UserCancelledError: If user cancels

        """
        try:
            if not values:
                return True

            self._output.write('\nPlaceholder values summary:\n')
            self._output.write('-' * 40 + '\n')

            for name, value in values.items():
                # Truncate very long values for display
                display_value = value
                if len(display_value) > self.MAX_DISPLAY_LENGTH:
                    display_value = display_value[:47] + '...'

                self._output.write(f'  {name}: {display_value}\n')

            self._output.write('-' * 40 + '\n')
            self._output.write('Proceed with these values? (y/n) [y]: ')
            self._output.flush()

            try:
                response = self._input.readline()
            except KeyboardInterrupt:
                self._output.write('\n')
                self._output.flush()
                raise UserCancelledError('User cancelled confirmation') from None

            if not response:  # EOF
                raise UserCancelledError('User cancelled confirmation (EOF)')

            response = response.strip().lower()

            # Default to 'yes' if empty
            if not response or response in {'y', 'yes'}:
                return True
            if response in {'n', 'no'}:
                return False
            self._output.write("Please enter 'y' or 'n'\n")
            self._output.flush()
            # Retry
            return self.confirm_placeholder_values(values)

        except KeyboardInterrupt:  # pragma: no cover
            self._output.write('\n')
            self._output.flush()
            raise UserCancelledError('User cancelled confirmation') from None

    def show_error_message(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: Error message to display

        """
        self._error.write(f'Error: {message}\n')
        self._error.flush()

    def show_success_message(self, message: str) -> None:
        """Display success message to user.

        Args:
            message: Success message to display

        """
        self._output.write(f'✓ {message}\n')
        self._output.flush()

    def confirm_template_selection(self, template_name: str) -> bool:
        """Confirm with user that they want to use the selected template.

        Args:
            template_name: Name of template to confirm

        Returns:
            True if user confirms, False otherwise

        """
        return self.prompt_for_yes_no(f"Use template '{template_name}'?", default=True)

    def display_template_list(self, templates: list[str]) -> None:
        """Display list of available templates to user.

        Args:
            templates: List of template names to display

        """
        if not templates:
            self._output.write('No templates available.\n')
            self._output.flush()
            return

        self._output.write('\nAvailable templates:\n')
        for i, template in enumerate(templates, 1):
            self._output.write(f'  {i}. {template}\n')
        self._output.write('\n')
        self._output.flush()

    def show_info_message(self, message: str) -> None:
        """Display an info message to the user.

        Args:
            message: Info message to display

        """
        self._output.write(f'{message}\n')
        self._output.flush()

    def show_warning_message(self, message: str) -> None:
        """Display a warning message to the user.

        Args:
            message: Warning message to display

        """
        self._error.write(f'Warning: {message}\n')
        self._error.flush()

    def prompt_for_yes_no(self, question: str, *, default: bool | None = None) -> bool:
        """Prompt user for a yes/no answer.

        Args:
            question: Question to ask the user
            default: Default answer if user just presses enter

        Returns:
            True for yes, False for no

        Raises:
            UserCancelledError: If user cancels input

        """
        try:
            # Handle default when None is provided
            prompt_default: bool = True if default is None else default
            default_text = 'Y/n' if default is None or default else 'y/N'
            prompt = f'{question} ({default_text}): '

            self._output.write(prompt)
            self._output.flush()

            try:
                response = self._input.readline()
            except KeyboardInterrupt:
                self._output.write('\n')
                self._output.flush()
                raise UserCancelledError('User cancelled input') from None

            if not response:  # EOF
                raise UserCancelledError('User cancelled input (EOF)')

            response = response.strip().lower()

            if not response:
                return prompt_default
            if response in {'y', 'yes'}:
                return True
            if response in {'n', 'no'}:
                return False
            self._output.write("Please enter 'y' or 'n'\n")
            self._output.flush()
            # Retry
            return self.prompt_for_yes_no(question, default=default)

        except KeyboardInterrupt:  # pragma: no cover
            self._output.write('\n')
            self._output.flush()
            raise UserCancelledError('User cancelled input') from None

    def prompt_for_choice(self, question: str, choices: list[str], default: int = 0) -> str:
        """Prompt user to select from a list of choices.

        Args:
            question: Question to ask the user
            choices: List of available choices
            default: Default choice index (0-based)

        Returns:
            Selected choice string

        Raises:
            UserCancelledError: If user cancels input
            ValueError: If choices is empty or default is invalid

        """
        if not choices:
            raise ValueError('Choices list cannot be empty')
        if default < 0 or default >= len(choices):
            msg = f'Default index {default} out of range for choices'
            raise ValueError(msg)

        try:
            self._output.write(f'{question}\n')

            for i, choice in enumerate(choices):
                marker = '*' if i == default else ' '
                self._output.write(f'{marker} {i + 1}. {choice}\n')

            prompt = f'Select (1-{len(choices)}) [{default + 1}]: '
            self._output.write(prompt)
            self._output.flush()

            try:
                response = self._input.readline()
            except KeyboardInterrupt:
                self._output.write('\n')
                self._output.flush()
                raise UserCancelledError('User cancelled input') from None

            if not response:  # EOF
                raise UserCancelledError('User cancelled input (EOF)')

            response = response.strip()

            if not response:
                return choices[default]

            try:
                choice_index = int(response) - 1
                if 0 <= choice_index < len(choices):
                    return choices[choice_index]
                self._output.write(f'Please enter a number between 1 and {len(choices)}\n')
                self._output.flush()
                # Retry
                return self.prompt_for_choice(question, choices, default)
            except ValueError:
                self._output.write('Please enter a valid number\n')
                self._output.flush()
                # Retry
                return self.prompt_for_choice(question, choices, default)

        except KeyboardInterrupt:  # pragma: no cover
            self._output.write('\n')
            self._output.flush()
            raise UserCancelledError('User cancelled input') from None
