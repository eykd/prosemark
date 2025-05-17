"""Session adapter for the Prosemark application.

This module provides a focused writing environment for the Prosemark application,
allowing users to track statistics and focus on forward progress.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    ConditionalContainer,
    Float,
    FloatContainer,
    FormattedTextControl,
    HSplit,
    Layout,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.styles import Style

if TYPE_CHECKING:  # pragma: no cover
    from prompt_toolkit.formatted_text import AnyFormattedText
    from prompt_toolkit.key_binding.key_processor import KeyPressEvent

    from prosemark.domain.nodes import Node
    from prosemark.repositories.project import ProjectRepository


class SessionStats(NamedTuple):
    """Statistics for a writing session.

    Attributes:
        start_time: When the session started.
        end_time: When the session ended (None if still active).
        initial_word_count: Word count at the start of the session.
        final_word_count: Current word count.
        word_goal: Target word count for the session (None if not set).
        time_limit_minutes: Time limit in minutes (None if not set).

    """

    start_time: datetime
    end_time: datetime | None
    initial_word_count: int
    final_word_count: int
    word_goal: int | None
    time_limit_minutes: int | None

    @property
    def elapsed_seconds(self) -> float:
        """Calculate the elapsed time in seconds."""
        end = self.end_time or datetime.now(UTC)
        seconds = (end - self.start_time).total_seconds()
        if seconds <= 0:
            return 0.0
        return seconds

    @property
    def elapsed_minutes(self) -> float:
        """Calculate the elapsed time in minutes."""
        return self.elapsed_seconds / 60

    @property
    def words_written(self) -> int:
        """Calculate the number of words written during the session."""
        return self.final_word_count - self.initial_word_count

    @property
    def words_per_minute(self) -> float:
        """Calculate the words per minute rate."""
        if self.elapsed_minutes > 0:
            return self.words_written / self.elapsed_minutes
        return 0.0

    @property
    def goal_progress(self) -> float:
        """Calculate progress toward the word goal as a percentage."""
        if not self.word_goal:
            return 0.0
        return min(100.0, (self.words_written / self.word_goal) * 100)

    @property
    def time_progress(self) -> float:
        """Calculate progress toward the time limit as a percentage."""
        if not self.time_limit_minutes:
            return 0.0
        return min(100.0, (self.elapsed_minutes / self.time_limit_minutes) * 100)

    @property
    def time_remaining_minutes(self) -> float | None:
        """Calculate the remaining time in minutes."""
        if not self.time_limit_minutes:
            return None
        remaining = self.time_limit_minutes - self.elapsed_minutes
        return max(0.0, remaining)


class SessionService:
    """Service class implementing the writing session for the Prosemark application.

    This class provides methods to start and manage a focused writing session,
    tracking statistics and encouraging forward progress.

    Attributes:
        repository: The project repository used to load and save nodes.

    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the session service.

        Args:
            repository: The project repository to use.

        """
        self.repository = repository

    def start_session(
        self,
        node_id: str,
        word_goal: int | None = None,
        time_limit: int | None = None,
        timer_mode: str = 'visible',
        stats_mode: str = 'minimal',
        *,
        no_prompt: bool = False,
    ) -> tuple[bool, list[str]]:
        """Start a writing session for the specified node.

        Args:
            node_id: The ID of the node to edit.
            word_goal: Optional word count goal for the session.
            time_limit: Optional time limit in minutes.
            timer_mode: How to display the timer ('none', 'visible', 'alert').
            stats_mode: How to display statistics ('none', 'minimal', 'detailed').
            no_prompt: Whether to skip prompting for goals if not specified.

        Returns:
            A tuple with success status and message lines.

        """
        # Load the project and find the node
        project = self.repository.load_project()
        node = project.get_node_by_id(node_id)

        if not node:
            return False, [f"Node with ID '{node_id}' not found"]

        # Load the node content
        self.repository.load_node_content(node)

        # Create and run the session
        session = WritingSession(
            node=node,
            repository=self.repository,
            word_goal=word_goal,
            time_limit=time_limit,
            timer_mode=timer_mode,
            stats_mode=stats_mode,
            no_prompt=no_prompt,
        )

        try:
            session.run()
        except (KeyboardInterrupt, EOFError):  # pragma: no cover
            return True, ['Session ended by user']
        except RuntimeError as e:
            return False, [f'Session error: {e!s}']
        else:
            return True, ['Session completed successfully']


class WritingSession:  # pragma: no cover
    """Manages a focused writing session for a specific node.

    This class provides the UI and interaction logic for a writing session,
    tracking statistics and encouraging forward progress.

    Attributes:
        node: The node being edited.
        repository: The project repository for saving changes.
        word_goal: Target word count for the session.
        time_limit: Time limit in minutes.
        timer_mode: How to display the timer.
        stats_mode: How to display statistics.
        no_prompt: Whether to skip prompting for goals.

    """

    def __init__(
        self,
        node: Node,
        repository: ProjectRepository,
        word_goal: int | None = None,
        time_limit: int | None = None,
        timer_mode: str = 'visible',
        stats_mode: str = 'minimal',
        *,
        no_prompt: bool = False,
    ) -> None:
        """Initialize the writing session.

        Args:
            node: The node to edit.
            repository: The project repository for saving.
            word_goal: Optional word count goal for the session.
            time_limit: Optional time limit in minutes.
            timer_mode: How to display the timer ('none', 'visible', 'alert').
            stats_mode: How to display statistics ('none', 'minimal', 'detailed').
            no_prompt: Whether to skip prompting for goals if not specified.

        """
        self.node = node
        self.repository = repository
        self.word_goal = word_goal
        self.time_limit = time_limit
        self.timer_mode = timer_mode
        self.stats_mode = stats_mode
        self.no_prompt = no_prompt

        # Session state
        self.start_time = datetime.now(UTC)
        self.end_time: datetime | None = None
        self.initial_content = node.text
        self.current_content = node.text
        self.committed_lines = self.current_content.splitlines() if self.current_content else []
        self.initial_word_count = self._count_words(self.initial_content)

        # UI components
        self.input_buffer = Buffer()
        self.app: Application[Any] | None = None
        self.show_help = False
        self.committed_buffer = Buffer()
        self.committed_window: Window | None = None  # Reference to the committed text window

        # Setup refresh timer
        self.last_update_time = time.time()
        self.update_interval = 1.0  # seconds

        # Initialize the committed buffer with current content
        self._update_committed_buffer()

    def run(self) -> None:
        """Run the writing session."""
        # Prompt for goals if needed
        self._prompt_for_goals()

        # Create the application
        self.app = self._create_application()

        # Run the application
        self.app.run()

        # Save the final state
        self._save_session()

    def _prompt_for_goals(self) -> None:
        """Prompt the user for session goals if not specified."""
        if self.no_prompt:
            return

        if self.word_goal is None:
            try:
                word_goal_input = input('Word count goal (leave blank for none): ')
                if word_goal_input.strip():
                    self.word_goal = int(word_goal_input)
            except ValueError:
                # Skip setting word goal on invalid input
                pass

        if self.time_limit is None:
            try:
                time_limit_input = input('Time limit in minutes (leave blank for none): ')
                if time_limit_input.strip():
                    self.time_limit = int(time_limit_input)
            except ValueError:
                # Skip setting time limit on invalid input
                pass

    def _create_application(self) -> Application[Any]:
        """Create the prompt-toolkit application for the session."""
        # Create key bindings
        kb = KeyBindings()

        @kb.add('c-c')
        @kb.add('c-d')
        def exit_app(event: KeyPressEvent) -> None:
            """Exit the application on Ctrl-C or Ctrl-D."""
            event.app.exit()

        @kb.add('enter')
        def commit_line(event: KeyPressEvent) -> None:  # noqa: ARG001
            """Process the current line when Enter is pressed."""
            text = self.input_buffer.text
            self.committed_lines.append(text)
            self.current_content = '\n'.join(self.committed_lines)
            self._save_current_content()
            self.input_buffer.reset()
            self._update_committed_buffer()

        @kb.add('f1')
        def toggle_help(_: KeyPressEvent) -> None:
            """Toggle help screen."""
            self.show_help = not self.show_help

        # Create the layout
        self.committed_window = Window(
            content=BufferControl(buffer=self.committed_buffer, focusable=False),
            wrap_lines=True,
            height=D(weight=1),
        )
        layout = Layout(
            FloatContainer(
                content=HSplit([
                    # Title bar
                    Window(
                        height=1,
                        content=FormattedTextControl(self._get_title_text),
                        align=WindowAlign.CENTER,
                        style='class:title',
                    ),
                    # Committed content area
                    self.committed_window,
                    # Stats bar
                    ConditionalContainer(
                        Window(
                            height=1,
                            content=FormattedTextControl(self._get_stats_text),
                            style='class:stats',
                        ),
                        filter=Condition(lambda: self.stats_mode != 'none'),
                    ),
                    # Input area
                    Window(
                        height=5,
                        content=BufferControl(buffer=self.input_buffer),
                        style='class:input',
                        wrap_lines=True,
                    ),
                    # Status bar
                    Window(
                        height=1,
                        content=FormattedTextControl(self._get_status_text),
                        style='class:status',
                    ),
                ]),
                floats=[
                    Float(
                        ConditionalContainer(
                            Window(
                                content=FormattedTextControl(self._get_help_text),
                                width=60,
                                height=10,
                                style='class:help',
                            ),
                            filter=Condition(lambda: self.show_help),
                        ),
                        top=5,
                        left=10,
                    ),
                ],
            )
        )

        # Define styles
        style = Style.from_dict({
            'title': 'bg:#004400 #ffffff',
            'stats': 'bg:#000044 #ffffff',
            'status': 'bg:#440000 #ffffff',
            'help': 'bg:#222222 #ffffff',
            'input': 'bg:#000000 #ffffff',
            'cursor': 'bg:#000000 #00ff00',  # Add a green cursor indicator
        })

        # Create and return the application
        app: Application[Any] = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=True,
            refresh_interval=0.5,
            mouse_support=True,
        )

        # Add a pre-run callback to refresh stats
        app.pre_run_callables.append(lambda: self._refresh_stats(app))

        return app

    def _get_title_text(self) -> AnyFormattedText:
        """Get the formatted text for the title bar."""
        return [('class:title', f' Writing Session: {self.node.title} ')]

    def _get_stats_text(self) -> AnyFormattedText:
        """Get the formatted text for the stats bar."""
        stats = self._get_current_stats()

        if self.stats_mode == 'minimal':
            return [
                ('class:stats', f' Words: {stats.final_word_count} '),
                ('class:stats', f' Written: +{stats.words_written} '),
                ('class:stats', f' Time: {self._format_time(stats.elapsed_seconds)} '),
            ]
        if self.stats_mode == 'detailed':
            parts: list[tuple[str, str]] = [
                ('class:stats', f' Words: {stats.final_word_count} '),
                ('class:stats', f' Written: +{stats.words_written} '),
                ('class:stats', f' WPM: {stats.words_per_minute:.1f} '),
                ('class:stats', f' Time: {self._format_time(stats.elapsed_seconds)} '),
            ]

            if stats.word_goal:
                parts.append(('class:stats', f' Goal: {stats.goal_progress:.1f}% '))

            if stats.time_limit_minutes:
                parts.append((
                    'class:stats',
                    f' Remaining: {self._format_time(stats.time_remaining_minutes * 60 if stats.time_remaining_minutes else 0)} ',
                ))

            return parts  # type: ignore[return-value]

        return []

    def _get_status_text(self) -> AnyFormattedText:
        """Get the formatted text for the status bar."""
        return [('class:status', ' F1: Help | Enter: Commit line | Ctrl+C: Exit ')]

    def _get_help_text(self) -> AnyFormattedText:
        """Get the formatted text for the help screen."""
        return [
            ('class:help', ' Writing Session Help\n\n'),
            ('class:help', ' Enter: Commit current line (cannot be edited afterward)\n'),
            ('class:help', ' Ctrl+C or Ctrl+D: Exit session and save\n'),
            ('class:help', ' F1: Toggle this help screen\n\n'),
            ('class:help', ' Session encourages forward progress by making\n'),
            ('class:help', ' committed lines read-only. Edit your work later!\n'),
        ]

    def _refresh_stats(self, app: Application[Any]) -> None:
        """Refresh the statistics display."""
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            app.invalidate()

            # Check for time limit if alert mode is on
            if self.timer_mode == 'alert' and self.time_limit:
                stats = self._get_current_stats()
                if stats.time_remaining_minutes is not None and stats.time_remaining_minutes <= 1:
                    app.output.write_raw('\a')  # Terminal bell

    def _get_current_stats(self) -> SessionStats:
        """Get the current session statistics."""
        return SessionStats(
            start_time=self.start_time,
            end_time=self.end_time,
            initial_word_count=self.initial_word_count,
            final_word_count=self._count_words(self.current_content),
            word_goal=self.word_goal,
            time_limit_minutes=self.time_limit,
        )

    def _count_words(self, text: str) -> int:
        """Count the number of words in the text."""
        if not text:
            return 0
        return len(text.split())

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to a readable string."""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f'{hours}:{minutes:02d}:{seconds:02d}'
        return f'{minutes}:{seconds:02d}'

    def _save_current_content(self) -> None:
        """Save the current content to the node."""
        self.node.text = self.current_content
        self.repository.save_node(self.node)

    def _save_session(self) -> None:
        """Save the final session state and update metadata."""
        self.end_time = datetime.now(UTC)

        # Save the final content
        self._save_current_content()

        # Update session metadata
        stats = self._get_current_stats()
        session_data = {
            'start_time': stats.start_time.isoformat(),
            'end_time': stats.end_time.isoformat() if stats.end_time else None,
            'initial_word_count': stats.initial_word_count,
            'final_word_count': stats.final_word_count,
            'words_written': stats.words_written,
            'elapsed_minutes': stats.elapsed_minutes,
            'words_per_minute': stats.words_per_minute,
        }

        # Add session history to node metadata
        if 'session_history' not in self.node.metadata:
            self.node.metadata['session_history'] = []

        sessions = cast('list[dict[str, Any]]', self.node.metadata['session_history'])
        sessions.append(session_data)

        # Save the updated node with metadata
        self.repository.save_node(self.node)

    def _scroll_committed_pane_to_bottom(self) -> None:
        """Invalidate the app to ensure the committed window scrolls to the bottom."""
        if self.app is not None:
            self.app.invalidate()

    def _update_committed_buffer(self) -> None:
        """Update the committed buffer and set cursor to the end to ensure the last line is visible."""
        committed_text = self._get_committed_text()
        self.committed_buffer.text = committed_text
        self.committed_buffer.cursor_position = len(committed_text)

    def _get_committed_text(self) -> str:
        """Get the committed text."""
        return '\n'.join(self.committed_lines) + '\n▏'
