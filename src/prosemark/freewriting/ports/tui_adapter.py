"""TUI adapter port interfaces for freewriting interface.

This module defines the port interfaces for the terminal user interface
components of the freewriting feature.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig
    from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort


@dataclass(frozen=True)
class UIState:
    """Current state of the TUI interface."""

    session: FreewriteSession | None
    input_text: str
    display_lines: list[str]
    word_count: int
    elapsed_time: int
    time_remaining: int | None
    progress_percent: float | None
    error_message: str | None
    is_paused: bool


@dataclass(frozen=True)
class TUIConfig:
    """Configuration for TUI appearance and behavior."""

    theme: str
    content_height_percent: int = 80
    input_height_percent: int = 20
    show_word_count: bool = True
    show_timer: bool = True
    auto_scroll: bool = True
    max_display_lines: int = 1000


class TUIAdapterPort(ABC):
    """Port interface for TUI operations.

    This port defines the contract for main TUI operations such as
    session management and content handling.
    """

    @property
    @abstractmethod
    def freewrite_service(self) -> FreewriteServicePort:
        """Freewrite service instance for session operations.

        Returns:
            The freewrite service instance used by this TUI adapter.

        """

    @abstractmethod
    def initialize_session(self, config: SessionConfig) -> FreewriteSession:
        """Initialize a new freewriting session.

        Args:
            config: Session configuration from CLI.

        Returns:
            Created session object.

        Raises:
            ValidationError: If configuration is invalid.

        """

    @abstractmethod
    def handle_input_submission(self, session: FreewriteSession, input_text: str) -> FreewriteSession:
        """Handle user pressing ENTER in input box.

        Args:
            session: Current session state.
            input_text: Text from input box.

        Returns:
            Updated session after content is appended.

        Raises:
            FileSystemError: If save operation fails.

        """

    @abstractmethod
    def get_display_content(self, session: FreewriteSession, max_lines: int) -> list[str]:
        """Get content lines to display in content area.

        Args:
            session: Current session.
            max_lines: Maximum lines to return (for bottom of file view).

        Returns:
            List of content lines for display.

        """

    @abstractmethod
    def calculate_progress(self, session: FreewriteSession) -> dict[str, Any]:
        """Calculate session progress metrics.

        Args:
            session: Current session.

        Returns:
            Dictionary with progress information:
            - word_count: int
            - elapsed_time: int
            - time_remaining: Optional[int]
            - progress_percent: Optional[float]
            - goals_met: Dict[str, bool]

        """

    @abstractmethod
    def handle_error(self, error: Exception, session: FreewriteSession) -> UIState:
        """Handle errors during session operations.

        Args:
            error: The exception that occurred.
            session: Current session state.

        Returns:
            Updated UI state with error information.

        """


class TUIEventPort(ABC):
    """Port interface for TUI event handling.

    This port defines the contract for handling various TUI events
    such as user input and session state changes.
    """

    @abstractmethod
    def on_input_change(self, callback: Callable[[str], None]) -> None:
        """Register callback for input text changes.

        Args:
            callback: Function to call when input changes.

        """

    @abstractmethod
    def on_input_submit(self, callback: Callable[[str], None]) -> None:
        """Register callback for input submission (ENTER key).

        Args:
            callback: Function to call when input is submitted.

        """

    @abstractmethod
    def on_session_pause(self, callback: Callable[[], None]) -> None:
        """Register callback for session pause events.

        Args:
            callback: Function to call when session is paused.

        """

    @abstractmethod
    def on_session_resume(self, callback: Callable[[], None]) -> None:
        """Register callback for session resume events.

        Args:
            callback: Function to call when session is resumed.

        """

    @abstractmethod
    def on_session_exit(self, callback: Callable[[], None]) -> None:
        """Register callback for session exit events.

        Args:
            callback: Function to call when session exits.

        """


class TUIDisplayPort(ABC):
    """Port interface for TUI display operations.

    This port defines the contract for updating the TUI display
    components such as content area and status display.
    """

    @abstractmethod
    def update_content_area(self, lines: list[str]) -> None:
        """Update the main content display area.

        Args:
            lines: Content lines to display.

        """

    @abstractmethod
    def update_stats_display(self, stats: dict[str, Any]) -> None:
        """Update statistics display (word count, timer, etc.).

        Args:
            stats: Statistics to display.

        """

    @abstractmethod
    def clear_input_area(self) -> None:
        """Clear the input text box."""

    @abstractmethod
    def show_error_message(self, message: str) -> None:
        """Display error message to user.

        Args:
            message: Error message to show.

        """

    @abstractmethod
    def hide_error_message(self) -> None:
        """Hide any currently displayed error message."""

    @abstractmethod
    def set_theme(self, theme_name: str) -> None:
        """Apply UI theme.

        Args:
            theme_name: Name of theme to apply.

        """


# UI Event Data Classes
@dataclass(frozen=True)
class InputSubmittedEvent:
    """Event fired when user submits input."""

    content: str
    timestamp: str


@dataclass(frozen=True)
class SessionProgressEvent:
    """Event fired when session progress updates."""

    word_count: int
    elapsed_time: int
    progress_percent: float | None


@dataclass(frozen=True)
class ErrorEvent:
    """Event fired when an error occurs."""

    error_type: str
    message: str
    recoverable: bool


@dataclass(frozen=True)
class SessionCompletedEvent:
    """Event fired when session completes."""

    final_word_count: int
    total_time: int
    output_file: str
