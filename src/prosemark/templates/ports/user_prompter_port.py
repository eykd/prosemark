"""User Prompter Port Contract.

Defines the interface for user interaction during template instantiation.
"""

from abc import ABC, abstractmethod

from prosemark.templates.domain.entities.placeholder import Placeholder, PlaceholderValue


class UserPrompterPort(ABC):
    """Port for user interaction during template instantiation."""

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def confirm_template_selection(self, template_name: str) -> bool:
        """Confirm with user that they want to use the selected template.

        Args:
            template_name: Name of template to confirm

        Returns:
            True if user confirms, False otherwise

        """

    @abstractmethod
    def display_template_list(self, templates: list[str]) -> None:
        """Display list of available templates to user.

        Args:
            templates: List of template names to display

        """

    @abstractmethod
    def show_error_message(self, message: str) -> None:
        """Display error message to user.

        Args:
            message: Error message to display

        """

    @abstractmethod
    def show_success_message(self, message: str) -> None:
        """Display success message to user.

        Args:
            message: Success message to display

        """
