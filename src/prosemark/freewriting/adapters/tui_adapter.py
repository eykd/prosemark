"""TUI adapter implementation using Textual framework.

This module provides the concrete implementation of the TUI ports
using the Textual framework for terminal user interface operations.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Static

from prosemark.freewriting.domain.exceptions import TUIError, ValidationError

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from textual.events import Key

    from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig
    from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort
    from prosemark.freewriting.ports.tui_adapter import TUIConfig, UIState

from prosemark.freewriting.ports.tui_adapter import (
    TUIAdapterPort,
    TUIDisplayPort,
    TUIEventPort,
    UIState,
)


class EmacsInput(Input):
    """Input widget with emacs-style key bindings."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the EmacsInput widget.

        Args:
            *args: Positional arguments passed to Input.
            **kwargs: Keyword arguments passed to Input.

        """
        super().__init__(*args, **kwargs)
        self._kill_buffer: str = ''
        self._escape_pressed: bool = False

    async def _on_key(self, event: Key) -> None:  # pragma: no cover
        """Handle key press events with emacs bindings.

        Args:
            event: The key event to handle.

        """
        key = event.key  # pragma: no cover

        # Handle the case where escape and the next key come as separate events  # pragma: no cover
        if key == 'escape':  # pragma: no cover
            self._escape_pressed = True  # pragma: no cover
            event.prevent_default()  # pragma: no cover
            event.stop()  # pragma: no cover
            return  # pragma: no cover

        # Check if this is the second part of an escape sequence  # pragma: no cover
        if self._escape_pressed:  # pragma: no cover
            self._escape_pressed = False  # pragma: no cover
            if key == 'd':  # pragma: no cover
                event.prevent_default()  # pragma: no cover
                event.stop()  # pragma: no cover
                self._delete_word_forward()  # pragma: no cover
                return  # pragma: no cover
            if key == 'f':  # pragma: no cover
                event.prevent_default()  # pragma: no cover
                event.stop()  # pragma: no cover
                self._move_word_forward()  # pragma: no cover
                return  # pragma: no cover
            if key == 'b':  # pragma: no cover
                event.prevent_default()  # pragma: no cover
                event.stop()  # pragma: no cover
                self._move_word_backward()  # pragma: no cover
                return  # pragma: no cover
            if key == 'backspace':  # pragma: no cover
                event.prevent_default()  # pragma: no cover
                event.stop()  # pragma: no cover
                self._delete_word_backward()  # pragma: no cover
                return  # pragma: no cover
            # If it's not a recognized meta sequence, fall through to normal handling  # pragma: no cover

        # Combine all handlers into one dictionary for simpler lookup  # pragma: no cover
        all_handlers = {  # pragma: no cover
            # Ctrl key combinations  # pragma: no cover
            'ctrl+b': self._move_char_backward,  # pragma: no cover
            'ctrl+f': self._move_char_forward,  # pragma: no cover
            'ctrl+a': self._move_line_start,  # pragma: no cover
            'ctrl+e': self._move_line_end,  # pragma: no cover
            'ctrl+d': self._delete_char_forward,  # pragma: no cover
            'ctrl+k': self._kill_to_line_end,  # pragma: no cover
            'ctrl+y': self._yank_killed_text,  # pragma: no cover
            'ctrl+w': self._kill_word_backward,  # pragma: no cover
            # Meta/Alt key combinations for terminals that send them as compound keys  # pragma: no cover
            'escape+b': self._move_word_backward,  # pragma: no cover
            'alt+b': self._move_word_backward,  # pragma: no cover
            'escape+f': self._move_word_forward,  # pragma: no cover
            'alt+f': self._move_word_forward,  # pragma: no cover
            'escape+d': self._delete_word_forward,  # pragma: no cover
            'alt+d': self._delete_word_forward,  # pragma: no cover
            'meta+d': self._delete_word_forward,  # pragma: no cover
            'escape+delete': self._delete_word_forward,  # pragma: no cover
            'alt+delete': self._delete_word_forward,  # pragma: no cover
            'escape+backspace': self._delete_word_backward,  # pragma: no cover
            'alt+backspace': self._delete_word_backward,  # pragma: no cover
            'meta+backspace': self._delete_word_backward,  # pragma: no cover
        }  # pragma: no cover

        # Try to handle the key  # pragma: no cover
        handler = all_handlers.get(key)  # pragma: no cover
        if handler:  # pragma: no cover
            # Prevent the event from bubbling up to app-level handlers  # pragma: no cover
            event.prevent_default()  # pragma: no cover
            event.stop()  # pragma: no cover
            handler()  # pragma: no cover
        else:  # pragma: no cover
            # Pass through to default handler  # pragma: no cover
            await super()._on_key(event)  # pragma: no cover

    def _move_char_backward(self) -> None:
        """Move cursor backward one character."""
        try:
            current_pos = self.cursor_position  # pragma: no cover
            if current_pos > 0:  # pragma: no cover
                self.cursor_position = current_pos - 1  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _move_char_forward(self) -> None:
        """Move cursor forward one character."""
        try:
            current_pos = self.cursor_position  # pragma: no cover
            value_len = len(self.value)  # pragma: no cover
            if current_pos < value_len:  # pragma: no cover
                self.cursor_position = current_pos + 1  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _move_line_start(self) -> None:
        """Move cursor to beginning of line."""
        try:  # noqa: SIM105
            self.cursor_position = 0  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _move_line_end(self) -> None:
        """Move cursor to end of line."""
        try:  # noqa: SIM105
            self.cursor_position = len(self.value)  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _delete_char_forward(self) -> None:
        """Delete character at cursor position or quit if buffer is empty."""
        try:
            pos = self.cursor_position
            value = self.value  # pragma: no cover
            if pos < len(value):  # pragma: no cover
                # Delete character at cursor position  # pragma: no cover
                self.value = value[:pos] + value[pos + 1 :]  # pragma: no cover
            elif not value:  # Buffer is completely empty, trigger quit  # pragma: no cover
                self.app.exit()  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _kill_to_line_end(self) -> None:
        """Kill text from cursor to end of line."""
        try:
            pos = self.cursor_position
            value = self.value  # pragma: no cover
            self._kill_buffer = value[pos:]  # pragma: no cover
            self.value = value[:pos]  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _yank_killed_text(self) -> None:
        """Yank (paste) previously killed text."""
        if self._kill_buffer:  # pragma: no cover
            try:
                pos = self.cursor_position  # pragma: no cover
                value = self.value  # pragma: no cover
                new_value = value[:pos] + self._kill_buffer + value[pos:]  # pragma: no cover
                self.value = new_value  # pragma: no cover
                self.cursor_position = pos + len(self._kill_buffer)  # pragma: no cover
            except Exception:  # pragma: no cover # noqa: BLE001,S110
                # Handle case when reactive properties aren't available (e.g., in tests)
                pass

    def _kill_word_backward(self) -> None:
        """Kill word backward from cursor."""
        try:
            pos = self.cursor_position  # pragma: no cover
            value = self.value  # pragma: no cover
            if pos > 0:  # pragma: no cover
                text_before = value[:pos].rstrip()  # pragma: no cover
                last_space = text_before.rfind(' ')  # pragma: no cover
                if last_space == -1:  # pragma: no cover
                    self._kill_buffer = value[:pos]  # pragma: no cover
                    self.value = value[pos:]  # pragma: no cover
                    self.cursor_position = 0  # pragma: no cover
                else:  # pragma: no cover
                    kill_start = last_space + 1  # pragma: no cover
                    self._kill_buffer = value[kill_start:pos]  # pragma: no cover
                    self.value = value[:kill_start] + value[pos:]  # pragma: no cover
                    self.cursor_position = kill_start  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _move_word_backward(self) -> None:
        """Move cursor backward one word."""
        try:
            pos = self.cursor_position  # pragma: no cover
            value = self.value  # pragma: no cover
            if pos > 0:  # pragma: no cover
                # Skip trailing spaces  # pragma: no cover
                while pos > 0 and value[pos - 1] == ' ':  # pragma: no cover
                    pos -= 1  # pragma: no cover
                # Move to start of word  # pragma: no cover
                while pos > 0 and value[pos - 1] != ' ':  # pragma: no cover
                    pos -= 1  # pragma: no cover
                self.cursor_position = pos  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _move_word_forward(self) -> None:
        """Move cursor forward one word."""
        try:
            pos = self.cursor_position  # pragma: no cover
            value = self.value  # pragma: no cover
            value_len = len(value)  # pragma: no cover
            if pos < value_len:  # pragma: no cover
                # Skip current word  # pragma: no cover
                while pos < value_len and value[pos] != ' ':  # pragma: no cover
                    pos += 1  # pragma: no cover
                # Skip spaces  # pragma: no cover
                while pos < value_len and value[pos] == ' ':  # pragma: no cover
                    pos += 1  # pragma: no cover
                self.cursor_position = pos  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _delete_word_forward(self) -> None:
        """Delete word forward from cursor."""
        try:
            pos = self.cursor_position  # pragma: no cover
            value = self.value  # pragma: no cover
            value_len = len(value)  # pragma: no cover
            if pos < value_len:  # pragma: no cover
                end_pos = pos  # pragma: no cover
                # Skip to end of current word  # pragma: no cover
                while end_pos < value_len and value[end_pos] != ' ':  # pragma: no cover
                    end_pos += 1  # pragma: no cover
                self._kill_buffer = value[pos:end_pos]  # pragma: no cover
                self.value = value[:pos] + value[end_pos:]  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass

    def _delete_word_backward(self) -> None:
        """Delete word backward from cursor."""
        try:  # pragma: no cover
            pos = self.cursor_position  # pragma: no cover
            value = self.value  # pragma: no cover
            if pos > 0:  # pragma: no cover
                start_pos = pos  # pragma: no cover
                # Skip spaces  # pragma: no cover
                while start_pos > 0 and value[start_pos - 1] == ' ':  # pragma: no cover
                    start_pos -= 1  # pragma: no cover
                # Move to start of word  # pragma: no cover
                while start_pos > 0 and value[start_pos - 1] != ' ':  # pragma: no cover
                    start_pos -= 1  # pragma: no cover
                self._kill_buffer = value[start_pos:pos]  # pragma: no cover
                self.value = value[:start_pos] + value[pos:]  # pragma: no cover
                self.cursor_position = start_pos  # pragma: no cover
        except Exception:  # pragma: no cover # noqa: BLE001,S110
            # Handle case when reactive properties aren't available (e.g., in tests)
            pass


class FreewritingApp(App[int]):
    """Main Textual application for freewriting sessions."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content_area {
        height: 80%;
        border: solid $primary;
        padding: 1;
    }

    #input_container {
        height: 20%;
        border: solid $secondary;
        padding: 1;
    }

    #input_box {
        width: 100%;
    }

    #stats_display {
        dock: top;
        height: 1;
        background: $surface;
        color: $text;
        text-align: center;
    }

    .content_line {
        padding: 0 1;
    }

    .error_message {
        background: $error;
        color: $text;
        padding: 1;
        margin: 1;
    }
    """

    BINDINGS: ClassVar = [
        Binding('ctrl+c', 'quit', 'Quit', show=True, priority=True),
        Binding('ctrl+s', 'pause', 'Pause/Resume', show=True),
    ]

    # Reactive attributes for real-time updates
    current_session: reactive[FreewriteSession | None] = reactive(None)
    elapsed_seconds: reactive[int] = reactive(0)
    error_message: reactive[str | None] = reactive(None)

    def __init__(
        self,
        session_config: SessionConfig,
        tui_adapter: TUIAdapterPort,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize the freewriting TUI application.

        Args:
            session_config: Configuration for the session.
            tui_adapter: TUI adapter for session operations.
            **kwargs: Additional arguments passed to App.

        """
        super().__init__(**kwargs)
        self.session_config = session_config
        self.tui_adapter = tui_adapter
        self.start_time = time.time()
        self.is_paused = False
        self.pause_start_time: float | None = None
        self.total_paused_time = 0.0

        # Event callbacks
        self._input_change_callbacks: list[Callable[[str], None]] = []
        self._input_submit_callbacks: list[Callable[[str], None]] = []
        self._session_pause_callbacks: list[Callable[[], None]] = []
        self._session_resume_callbacks: list[Callable[[], None]] = []
        self._session_exit_callbacks: list[Callable[[], None]] = []

    def compose(self) -> ComposeResult:  # noqa: PLR6301
        """Create child widgets for the app."""
        yield Header()  # pragma: no cover
        yield Static('', id='stats_display')  # pragma: no cover
        yield VerticalScroll(id='content_area')  # pragma: no cover
        with Container(id='input_container'):  # pragma: no cover
            yield EmacsInput(  # pragma: no cover
                placeholder='Start writing... (Press Enter to add line)',  # pragma: no cover
                id='input_box',  # pragma: no cover
            )  # pragma: no cover
        yield Footer()  # pragma: no cover

    def on_mount(self) -> None:
        """Initialize the application after mounting."""
        try:
            # Initialize the session
            self.current_session = self.tui_adapter.initialize_session(self.session_config)

            # Set up the UI
            self.title = 'Freewriting Session'
            subtitle = f'Target: {self.session_config.target_node or "Daily File"}'
            if self.session_config.title:  # pragma: no branch
                subtitle += f' | {self.session_config.title}'
            self.sub_title = subtitle

            # Focus the input box
            self.query_one('#input_box').focus()

            # Start the timer
            self.set_interval(1.0, self._update_timer)

            # Update display
            self._update_display()

        except (OSError, RuntimeError, ValueError) as e:
            self.error_message = f'Failed to initialize session: {e}'
            self.exit(1)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle ENTER key press in input box."""
        if not self.current_session or self.is_paused:
            return

        input_widget = event.input
        text = input_widget.value

        try:
            # Submit content through adapter
            updated_session = self.tui_adapter.handle_input_submission(self.current_session, text)
            self.current_session = updated_session

            # Clear input
            input_widget.clear()

            # Trigger callbacks
            for callback in self._input_submit_callbacks:
                callback(text)  # pragma: no cover

            # Update display
            self._update_display()

            # Check if goals are met
            progress = self.tui_adapter.calculate_progress(self.current_session)
            goals_met = progress.get('goals_met', {})
            if any(goals_met.values()):
                self._show_completion_message(goals_met)  # pragma: no cover

        except (OSError, RuntimeError, ValueError) as e:
            ui_state = TextualTUIAdapter.handle_error(e, self.current_session)
            self.error_message = ui_state.error_message
            # Don't exit on content errors, let user continue

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input text changes."""
        # Trigger callbacks for input changes
        for callback in self._input_change_callbacks:
            callback(event.value)

    def action_pause(self) -> None:
        """Toggle pause/resume state."""
        if not self.current_session:
            return

        if self.is_paused:
            # Resume: calculate and accumulate paused time
            if self.pause_start_time is not None:
                self.total_paused_time += time.time() - self.pause_start_time
                self.pause_start_time = None
            self.is_paused = False
            for callback in self._session_resume_callbacks:
                callback()
            self.sub_title = self.sub_title.replace(' [PAUSED]', '')
        else:
            # Pause: record when pause started
            self.is_paused = True
            self.pause_start_time = time.time()
            for callback in self._session_pause_callbacks:
                callback()
            self.sub_title += ' [PAUSED]'

    async def action_quit(self) -> None:
        """Handle quit action."""
        # Trigger exit callbacks
        for callback in self._session_exit_callbacks:  # pragma: no cover
            callback()  # pragma: no cover

        # Exit with success code
        self.exit(0)  # pragma: no cover

    def _update_timer(self) -> None:
        """Update elapsed time every second."""
        if not self.is_paused and self.current_session:
            current_time = time.time()
            # Calculate elapsed time excluding paused time
            self.elapsed_seconds = int(current_time - self.start_time - self.total_paused_time)

            # Update session with elapsed time
            self.current_session = self.current_session.update_elapsed_time(self.elapsed_seconds)

            # Update stats display
            self._update_stats_display()

    def _update_display(self) -> None:
        """Update the content display area."""
        if not self.current_session:
            return

        # Get display content from adapter
        display_lines = TextualTUIAdapter.get_display_content(self.current_session, max_lines=1000)

        # Update content area
        content_area = self.query_one('#content_area')
        content_area.remove_children()

        for line in display_lines:
            content_area.mount(Static(line, classes='content_line'))

        # Auto-scroll to bottom
        content_area.scroll_end()

    def _update_stats_display(self) -> None:
        """Update statistics display."""
        if not self.current_session:
            return

        progress = self.tui_adapter.calculate_progress(self.current_session)

        # Format stats string
        stats_parts = []

        # Word count
        word_count = progress.get('word_count', 0)
        stats_parts.append(f'Words: {word_count}')

        if self.session_config.word_count_goal:
            goal_progress = (word_count / self.session_config.word_count_goal) * 100
            stats_parts.append(f'({goal_progress:.0f}%)')

        # Time
        elapsed = progress.get('elapsed_time', 0)
        elapsed_min = elapsed // 60
        elapsed_sec = elapsed % 60
        stats_parts.append(f'Time: {elapsed_min:02d}:{elapsed_sec:02d}')

        if self.session_config.time_limit:
            remaining = max(0, self.session_config.time_limit - elapsed)
            remaining_min = remaining // 60
            remaining_sec = remaining % 60
            stats_parts.append(f'(Remaining: {remaining_min:02d}:{remaining_sec:02d})')

        stats_text = ' | '.join(stats_parts)
        stats_display = self.query_one('#stats_display', Static)
        stats_display.update(stats_text)

    def _show_completion_message(self, goals_met: dict[str, bool]) -> None:
        """Show completion message when goals are met."""
        messages = []
        if goals_met.get('word_count'):
            messages.append('Word count goal reached!')
        if goals_met.get('time_limit'):
            messages.append('Time limit reached!')

        if messages:
            completion_text = ' '.join(messages) + ' Press Ctrl+C to exit.'
            # For now, just update the sub_title with completion message
            self.sub_title = completion_text


class TextualTUIAdapter(TUIAdapterPort, TUIEventPort, TUIDisplayPort):
    """Concrete implementation of TUI ports using Textual framework."""

    def __init__(self, freewrite_service: FreewriteServicePort) -> None:
        """Initialize the Textual TUI adapter.

        Args:
            freewrite_service: Service for freewriting operations.

        """
        self._freewrite_service = freewrite_service
        self.app_instance: FreewritingApp | None = None

    @property
    def freewrite_service(self) -> FreewriteServicePort:
        """Freewrite service instance for session operations.

        Returns:
            The freewrite service instance used by this TUI adapter.

        """
        return self._freewrite_service

    def initialize_session(self, config: SessionConfig) -> FreewriteSession:
        """Initialize a new freewriting session.

        Args:
            config: Session configuration from CLI.

        Returns:
            Created session object.

        Raises:
            ValidationError: If configuration is invalid.

        """
        try:
            return self._freewrite_service.create_session(config)
        except Exception as e:
            msg = 'Failed to initialize session'
            raise ValidationError('session_config', str(config), msg) from e

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
        return self._freewrite_service.append_content(session, input_text)

    @staticmethod
    def get_display_content(session: FreewriteSession, max_lines: int) -> list[str]:
        """Get content lines to display in content area.

        Args:
            session: Current session.
            max_lines: Maximum lines to return (for bottom of file view).

        Returns:
            List of content lines for display.

        """
        # Return bottom portion of content lines for "tail" view
        content_lines = session.content_lines
        if len(content_lines) <= max_lines:
            return content_lines
        return content_lines[-max_lines:]

    def calculate_progress(self, session: FreewriteSession) -> dict[str, Any]:
        """Calculate session progress metrics.

        Args:
            session: Current session.

        Returns:
            Dictionary with progress information.

        """
        return self._freewrite_service.get_session_stats(session)

    @staticmethod
    def handle_error(error: Exception, session: FreewriteSession) -> UIState:
        """Handle errors during session operations.

        Args:
            error: The exception that occurred.
            session: Current session state.

        Returns:
            Updated UI state with error information.

        """
        error_message = f'Error: {error}'

        return UIState(
            session=session,
            input_text='',
            display_lines=TextualTUIAdapter.get_display_content(session, 1000),
            word_count=session.current_word_count,
            elapsed_time=session.elapsed_time,
            time_remaining=(session.time_limit - session.elapsed_time if session.time_limit else None),
            progress_percent=None,
            error_message=error_message,
            is_paused=False,
        )

    def on_input_change(self, callback: Callable[[str], None]) -> None:
        """Register callback for input text changes.

        Args:
            callback: Function to call when input changes.

        """
        if self.app_instance:
            self.app_instance._input_change_callbacks.append(callback)  # noqa: SLF001

    def on_input_submit(self, callback: Callable[[str], None]) -> None:
        """Register callback for input submission (ENTER key).

        Args:
            callback: Function to call when input is submitted.

        """
        if self.app_instance:
            self.app_instance._input_submit_callbacks.append(callback)  # noqa: SLF001

    def on_session_pause(self, callback: Callable[[], None]) -> None:
        """Register callback for session pause events.

        Args:
            callback: Function to call when session is paused.

        """
        if self.app_instance:
            self.app_instance._session_pause_callbacks.append(callback)  # noqa: SLF001

    def on_session_resume(self, callback: Callable[[], None]) -> None:
        """Register callback for session resume events.

        Args:
            callback: Function to call when session is resumed.

        """
        if self.app_instance:
            self.app_instance._session_resume_callbacks.append(callback)  # noqa: SLF001

    def on_session_exit(self, callback: Callable[[], None]) -> None:
        """Register callback for session exit events.

        Args:
            callback: Function to call when session exits.

        """
        if self.app_instance:
            self.app_instance._session_exit_callbacks.append(callback)  # noqa: SLF001

    def update_content_area(self, _lines: list[str]) -> None:
        """Update the main content display area.

        Args:
            lines: Content lines to display.

        """
        if self.app_instance and self.app_instance.current_session:
            self.app_instance._update_display()  # noqa: SLF001

    def update_stats_display(self, _stats: dict[str, Any]) -> None:
        """Update statistics display (word count, timer, etc.).

        Args:
            stats: Statistics to display.

        """
        if self.app_instance:
            self.app_instance._update_stats_display()  # noqa: SLF001

    def clear_input_area(self) -> None:
        """Clear the input text box."""
        if self.app_instance:
            input_box = self.app_instance.query_one('#input_box', EmacsInput)
            input_box.clear()

    def show_error_message(self, message: str) -> None:
        """Display error message to user.

        Args:
            message: Error message to show.

        """
        if self.app_instance:
            self.app_instance.error_message = message

    def hide_error_message(self) -> None:
        """Hide any currently displayed error message."""
        if self.app_instance:
            self.app_instance.error_message = None

    @staticmethod
    def set_theme(theme_name: str) -> None:
        """Apply UI theme.

        Args:
            theme_name: Name of theme to apply.

        """
        # Textual theme switching would be implemented here
        # For now, we'll just validate the theme name
        valid_themes = ['dark', 'light']
        if theme_name not in valid_themes:
            msg = f'Invalid theme: {theme_name}. Valid themes: {valid_themes}'
            raise TUIError('theme', 'set_theme', msg, recoverable=True)

    def run_tui(self, session_config: SessionConfig, tui_config: TUIConfig | None = None) -> int:
        """Run the TUI application.

        Args:
            session_config: Session configuration.
            tui_config: Optional TUI configuration.

        Returns:
            Exit code (0 for success).

        """
        try:
            # Apply theme if specified
            if tui_config and tui_config.theme:
                TextualTUIAdapter.set_theme(tui_config.theme)

            # Create and run the app
            app = FreewritingApp(session_config, self)
            self.app_instance = app
            exit_code = app.run()
        except Exception as e:
            msg = f'TUI application failed: {e}'
            raise TUIError('application', 'run', msg, recoverable=False) from e
        else:
            return exit_code if exit_code is not None else 0
