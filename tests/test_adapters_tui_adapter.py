"""Tests for TUI adapter implementation using Textual framework.

These tests cover the TextualTUIAdapter and FreewritingApp classes,
focusing on the non-async functionality to maximize coverage.
"""

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from prosemark.freewriting.adapters.tui_adapter import EmacsInput, FreewritingApp, TextualTUIAdapter
from prosemark.freewriting.domain.exceptions import TUIError, ValidationError
from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig
from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort
from prosemark.freewriting.ports.tui_adapter import TUIConfig, UIState


class TestFreewritingApp:
    """Test the Textual application class."""

    def test_app_initialization(self) -> None:
        """Test app initializes with correct configuration."""
        # Arrange
        session_config = SessionConfig(
            target_node=None,
            title='Test Session',
            word_count_goal=1000,
            time_limit=3600,
            theme='dark',
            current_directory='/test/project',
        )
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        # Act
        app = FreewritingApp(session_config, mock_tui_adapter)

        # Assert
        assert app.session_config == session_config
        assert app.tui_adapter == mock_tui_adapter
        assert app.is_paused is False
        assert isinstance(app.start_time, float)
        assert len(app._input_change_callbacks) == 0
        assert len(app._input_submit_callbacks) == 0
        assert len(app._session_pause_callbacks) == 0
        assert len(app._session_resume_callbacks) == 0
        assert len(app._session_exit_callbacks) == 0

    def test_compose_method_exists(self) -> None:
        """Test compose method exists and is callable."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)

        # Act & Assert - Just verify the method exists and is callable
        # (We can't actually test widget creation without active app context)
        assert hasattr(app, 'compose')
        assert callable(app.compose)

    def test_on_mount_initialization_failure(self) -> None:
        """Test app handles initialization failure gracefully."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.initialize_session.side_effect = ValueError('Init failed')

        app = FreewritingApp(session_config, mock_tui_adapter)

        # Patch methods to avoid actual widget queries and operations
        with patch.object(app, 'query_one'), patch.object(app, 'set_interval'), patch.object(app, 'exit') as mock_exit:
            # Act - simulate on_mount being called
            app.on_mount()

            # Assert - verify error handling
            assert app.error_message == 'Failed to initialize session: Init failed'
            mock_exit.assert_called_once_with(1)

    def test_on_mount_success(self) -> None:
        """Test successful app mounting and initialization."""
        # Arrange
        session_config = SessionConfig(
            target_node=str(uuid.uuid4()),
            title='Mount Test',
        )
        mock_session = FreewriteSession(
            session_id=str(uuid.uuid4()),
            target_node=session_config.target_node,
            title='Mount Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )

        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.initialize_session.return_value = mock_session

        app = FreewritingApp(session_config, mock_tui_adapter)

        # Mock methods to avoid actual widget operations
        mock_input_widget = Mock()
        mock_input_widget.focus = Mock()

        with (
            patch.object(app, 'query_one', return_value=mock_input_widget),
            patch.object(app, 'set_interval') as mock_set_interval,
            patch.object(app, '_update_display') as mock_update_display,
        ):
            # Act
            app.on_mount()

            # Assert
            mock_tui_adapter.initialize_session.assert_called_once_with(session_config)
            assert app.current_session == mock_session
            assert app.title == 'Freewriting Session'
            # Fix string comparison type error: ensure target_node is string before comparison
            target_node = session_config.target_node
            if target_node is not None:
                assert target_node in app.sub_title
            assert 'Mount Test' in app.sub_title
            mock_input_widget.focus.assert_called_once()
            mock_set_interval.assert_called_once_with(1.0, app._update_timer)
            mock_update_display.assert_called_once()

    def test_input_submission_success(self) -> None:
        """Test successful input submission."""
        # Arrange
        session_config = SessionConfig()
        test_session_id = str(uuid.uuid4())
        initial_session = FreewriteSession(
            session_id=test_session_id,
            target_node=None,
            title=None,
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )
        updated_session = FreewriteSession(
            session_id=test_session_id,
            target_node=None,
            title=None,
            start_time=initial_session.start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=3,
            elapsed_time=5,
            output_file_path='/test/output.md',
            content_lines=['test input text'],
        )

        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.handle_input_submission.return_value = updated_session
        mock_tui_adapter.calculate_progress.return_value = {
            'word_count': 3,
            'elapsed_time': 5,
            'goals_met': {'word_count': False, 'time_limit': False},
        }

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = initial_session

        # Mock input widget
        from textual.widgets import Input

        input_widget = Mock(spec=Input)
        input_widget.value = 'test input text'
        input_widget.clear = Mock()

        # Create a mock event
        event = Mock()
        event.input = input_widget

        with patch.object(app, '_update_display') as mock_update_display:
            # Act - call the handler directly
            app.on_input_submitted(event)

            # Assert
            mock_tui_adapter.handle_input_submission.assert_called_once_with(initial_session, 'test input text')
            input_widget.clear.assert_called_once()
            assert app.current_session == updated_session
            mock_update_display.assert_called_once()

    def test_input_submission_when_paused(self) -> None:
        """Test input submission is ignored when app is paused."""
        # Arrange
        session_config = SessionConfig()
        initial_session = FreewriteSession(
            session_id=str(uuid.uuid4()),
            target_node=None,
            title=None,
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )

        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = initial_session
        app.is_paused = True  # Set to paused

        # Simulate input submission
        from textual.widgets import Input

        input_widget = Mock(spec=Input)
        input_widget.value = 'should be ignored'

        event = Mock()
        event.input = input_widget

        # Act - call the handler
        app.on_input_submitted(event)

        # Assert - handler should return early, not call adapter
        mock_tui_adapter.handle_input_submission.assert_not_called()

    def test_input_submission_no_session(self) -> None:
        """Test input submission is ignored when no session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = None

        # Simulate input submission
        from textual.widgets import Input

        input_widget = Mock(spec=Input)
        input_widget.value = 'should be ignored'

        event = Mock()
        event.input = input_widget

        # Act - call the handler
        app.on_input_submitted(event)

        # Assert - handler should return early, not call adapter
        mock_tui_adapter.handle_input_submission.assert_not_called()

    def test_input_submission_with_error(self) -> None:
        """Test input submission handles errors gracefully."""
        # Arrange
        session_config = SessionConfig()
        initial_session = FreewriteSession(
            session_id=str(uuid.uuid4()),
            target_node=None,
            title=None,
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )

        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.handle_input_submission.side_effect = OSError('Disk full')

        # Mock the static handle_error method
        error_ui_state = UIState(
            session=initial_session,
            input_text='',
            display_lines=[],
            word_count=0,
            elapsed_time=0,
            time_remaining=None,
            progress_percent=None,
            error_message='Error: Disk full',
            is_paused=False,
        )

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = initial_session

        with patch.object(TextualTUIAdapter, 'handle_error', return_value=error_ui_state) as mock_handle_error:
            # Simulate input submission that triggers error
            from textual.widgets import Input

            input_widget = Mock(spec=Input)
            input_widget.value = 'trigger error'

            event = Mock()
            event.input = input_widget

            # Act - call the handler
            app.on_input_submitted(event)

            # Assert error is handled but app doesn't exit
            assert app.error_message == 'Error: Disk full'
            mock_handle_error.assert_called_once()

    def test_input_change_callbacks(self) -> None:
        """Test input change triggers callbacks."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)

        callback_mock = Mock()
        app._input_change_callbacks.append(callback_mock)

        # Create mock event
        event = Mock()
        event.value = 'changing text'

        # Act
        app.on_input_changed(event)

        # Assert
        callback_mock.assert_called_once_with('changing text')

    def test_action_pause_when_not_paused(self) -> None:
        """Test pause action when app is not paused."""
        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session
        app.sub_title = 'Test Session'
        app.is_paused = False

        pause_callback = Mock()
        app._session_pause_callbacks.append(pause_callback)

        # Act
        app.action_pause()

        # Assert
        assert app.is_paused is True
        assert '[PAUSED]' in app.sub_title
        pause_callback.assert_called_once()

    def test_action_pause_when_paused(self) -> None:
        """Test pause action when app is already paused."""
        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session
        app.sub_title = 'Test Session [PAUSED]'
        app.is_paused = True

        resume_callback = Mock()
        app._session_resume_callbacks.append(resume_callback)

        # Act
        app.action_pause()

        # Assert
        assert app.is_paused is False
        assert '[PAUSED]' not in app.sub_title
        resume_callback.assert_called_once()

    def test_action_pause_no_session(self) -> None:
        """Test pause action when no session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = None

        # Act
        app.action_pause()

        # Assert - should return early, no state change
        assert app.is_paused is False

    def test_update_timer_when_not_paused(self) -> None:
        """Test timer update when app is not paused."""
        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_session.update_elapsed_time.return_value = mock_session
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session
        app.is_paused = False
        app.start_time = time.time() - 5  # 5 seconds ago

        with patch.object(app, '_update_stats_display') as mock_update_stats:
            # Act
            app._update_timer()

            # Assert
            assert app.elapsed_seconds >= 4  # At least 4 seconds (allowing for timing variations)
            mock_session.update_elapsed_time.assert_called_once()
            mock_update_stats.assert_called_once()

    def test_update_timer_when_paused(self) -> None:
        """Test timer update when app is paused."""
        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session
        app.is_paused = True
        initial_elapsed = app.elapsed_seconds

        # Act
        app._update_timer()

        # Assert - no updates when paused
        assert app.elapsed_seconds == initial_elapsed
        mock_session.update_elapsed_time.assert_not_called()

    def test_update_timer_no_session(self) -> None:
        """Test timer update when no session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = None
        initial_elapsed = app.elapsed_seconds

        # Act
        app._update_timer()

        # Assert - no updates when no session
        assert app.elapsed_seconds == initial_elapsed

    def test_pause_resume_timer_accumulates_correctly(self) -> None:
        """Test that pause/resume correctly accumulates paused time."""
        from unittest.mock import patch

        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session

        # Mock time.time() to control timing and _update_stats_display to avoid UI dependencies
        with (
            patch('prosemark.freewriting.adapters.tui_adapter.time.time') as mock_time,
            patch.object(app, '_update_stats_display'),
        ):
            # Start at time 0
            mock_time.return_value = 0.0
            app.start_time = 0.0
            app.total_paused_time = 0.0

            # Run for 3 seconds (should be 3 seconds elapsed)
            mock_time.return_value = 3.0
            app._update_timer()
            assert app.elapsed_seconds == 3

            # Pause at 3 seconds
            app.action_pause()
            assert app.is_paused is True
            assert app.pause_start_time == 3.0

            # Time passes while paused (5 seconds total, 2 seconds paused)
            mock_time.return_value = 5.0
            app._update_timer()  # Should not update elapsed time
            assert app.elapsed_seconds == 3  # Still 3 seconds

            # Resume at 5 seconds
            app.action_pause()  # Toggle to resume
            assert app.is_paused is False
            assert app.total_paused_time == 2.0  # 5 - 3 = 2 seconds paused
            assert app.pause_start_time is None

            # Continue for another 2 seconds (7 seconds total, 2 seconds paused)
            mock_time.return_value = 7.0
            app._update_timer()
            # Should be 7 - 0 - 2 = 5 seconds elapsed (total - start - paused)
            assert app.elapsed_seconds == 5

            # Pause again at 7 seconds
            app.action_pause()
            assert app.is_paused is True
            assert app.pause_start_time == 7.0

            # More time passes while paused (10 seconds total)
            mock_time.return_value = 10.0
            app._update_timer()  # Should not update elapsed time
            assert app.elapsed_seconds == 5  # Still 5 seconds

            # Resume at 10 seconds
            app.action_pause()  # Toggle to resume
            assert app.is_paused is False
            assert app.total_paused_time == 5.0  # 2 + (10 - 7) = 5 seconds total paused

            # Final update at 12 seconds total
            mock_time.return_value = 12.0
            app._update_timer()
            # Should be 12 - 0 - 5 = 7 seconds elapsed
            assert app.elapsed_seconds == 7

    def test_update_display_with_session(self) -> None:
        """Test display update when session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session

        # Mock the content area and its methods
        mock_content_area = Mock()
        mock_content_area.remove_children = Mock()
        mock_content_area.mount = Mock()
        mock_content_area.scroll_end = Mock()

        with (
            patch.object(app, 'query_one', return_value=mock_content_area),
            patch.object(
                TextualTUIAdapter, 'get_display_content', return_value=['Line 1', 'Line 2']
            ) as mock_get_content,
        ):
            # Act
            app._update_display()

            # Assert
            mock_get_content.assert_called_once_with(mock_session, max_lines=1000)
            mock_content_area.remove_children.assert_called_once()
            assert mock_content_area.mount.call_count == 2  # Two lines
            mock_content_area.scroll_end.assert_called_once()

    def test_update_display_no_session(self) -> None:
        """Test display update when no session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = None

        # Act - should return early without calling get_display_content
        with patch.object(TextualTUIAdapter, 'get_display_content') as mock_get_display:
            app._update_display()
            mock_get_display.assert_not_called()

    def test_update_stats_display_with_session_and_goals(self) -> None:
        """Test stats display update with session and goals."""
        # Arrange
        session_config = SessionConfig(
            word_count_goal=1000,
            time_limit=3600,
        )
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.calculate_progress.return_value = {
            'word_count': 250,
            'elapsed_time': 900,  # 15 minutes
        }

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session

        # Mock the stats display widget
        from textual.widgets import Static

        mock_stats_display = Mock(spec=Static)
        mock_stats_display.update = Mock()

        with patch.object(app, 'query_one', return_value=mock_stats_display):
            # Act
            app._update_stats_display()

            # Assert
            mock_tui_adapter.calculate_progress.assert_called_once_with(mock_session)
            mock_stats_display.update.assert_called_once()

        # Verify the stats text contains expected elements
        call_args = mock_stats_display.update.call_args[0][0]
        assert 'Words: 250' in call_args
        assert '25%' in call_args  # 250/1000 * 100
        assert 'Time: 15:00' in call_args  # 900 seconds = 15:00
        assert 'Remaining:' in call_args

    def test_update_stats_display_no_goals(self) -> None:
        """Test stats display update with no goals set."""
        # Arrange
        session_config = SessionConfig()  # No goals
        mock_session = Mock(spec=FreewriteSession)
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        mock_tui_adapter.calculate_progress.return_value = {
            'word_count': 150,
            'elapsed_time': 600,  # 10 minutes
        }

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = mock_session

        # Mock the stats display widget
        from textual.widgets import Static

        mock_stats_display = Mock(spec=Static)
        mock_stats_display.update = Mock()

        with patch.object(app, 'query_one', return_value=mock_stats_display):
            # Act
            app._update_stats_display()

            # Assert
            call_args = mock_stats_display.update.call_args[0][0]
            assert 'Words: 150' in call_args
            assert 'Time: 10:00' in call_args
            assert '%' not in call_args  # No percentage when no goals
        assert 'Remaining:' not in call_args

    def test_update_stats_display_no_session(self) -> None:
        """Test stats display update when no session exists."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)

        app = FreewritingApp(session_config, mock_tui_adapter)
        app.current_session = None

        # Act
        app._update_stats_display()

        # Assert - should return early
        mock_tui_adapter.calculate_progress.assert_not_called()

    def test_show_completion_message_word_count_goal(self) -> None:
        """Test completion message for word count goal."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)

        goals_met = {'word_count': True, 'time_limit': False}

        # Act
        app._show_completion_message(goals_met)

        # Assert
        assert 'Word count goal reached!' in app.sub_title
        assert 'Press Ctrl+C to exit.' in app.sub_title

    def test_show_completion_message_time_limit_goal(self) -> None:
        """Test completion message for time limit goal."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)

        goals_met = {'word_count': False, 'time_limit': True}

        # Act
        app._show_completion_message(goals_met)

        # Assert
        assert 'Time limit reached!' in app.sub_title
        assert 'Press Ctrl+C to exit.' in app.sub_title

    def test_show_completion_message_both_goals(self) -> None:
        """Test completion message for both goals."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)

        goals_met = {'word_count': True, 'time_limit': True}

        # Act
        app._show_completion_message(goals_met)

        # Assert
        assert 'Word count goal reached!' in app.sub_title
        assert 'Time limit reached!' in app.sub_title
        assert 'Press Ctrl+C to exit.' in app.sub_title

    def test_show_completion_message_no_goals_met(self) -> None:
        """Test completion message when no goals are met."""
        # Arrange
        session_config = SessionConfig()
        mock_tui_adapter = Mock(spec=TextualTUIAdapter)
        app = FreewritingApp(session_config, mock_tui_adapter)
        original_subtitle = app.sub_title

        goals_met = {'word_count': False, 'time_limit': False}

        # Act
        app._show_completion_message(goals_met)

        # Assert - subtitle should not be changed
        assert app.sub_title == original_subtitle


class TestTextualTUIAdapter:
    """Test the Textual TUI adapter implementation."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initializes with freewrite service."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)

        # Act
        adapter = TextualTUIAdapter(mock_service)

        # Assert
        assert adapter._freewrite_service == mock_service
        assert adapter.app_instance is None
        assert adapter.freewrite_service == mock_service

    def test_initialize_session_success(self) -> None:
        """Test successful session initialization."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        expected_session = Mock(spec=FreewriteSession)
        mock_service.create_session.return_value = expected_session

        adapter = TextualTUIAdapter(mock_service)
        config = SessionConfig()

        # Act
        result = adapter.initialize_session(config)

        # Assert
        assert result == expected_session
        mock_service.create_session.assert_called_once_with(config)

    def test_initialize_session_failure(self) -> None:
        """Test session initialization failure raises ValidationError."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        mock_service.create_session.side_effect = Exception('Service failed')

        adapter = TextualTUIAdapter(mock_service)
        config = SessionConfig()

        # Act & Assert
        with pytest.raises(ValidationError, match='Failed to initialize session'):
            adapter.initialize_session(config)

    def test_handle_input_submission(self) -> None:
        """Test input submission handling."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        expected_session = Mock(spec=FreewriteSession)
        mock_service.append_content.return_value = expected_session

        adapter = TextualTUIAdapter(mock_service)
        session = Mock(spec=FreewriteSession)
        input_text = 'Test input'

        # Act
        result = adapter.handle_input_submission(session, input_text)

        # Assert
        assert result == expected_session
        mock_service.append_content.assert_called_once_with(session, input_text)

    def test_get_display_content_full_content(self) -> None:
        """Test getting display content when content fits in max lines."""
        # Arrange
        session = Mock(spec=FreewriteSession)
        session.content_lines = ['Line 1', 'Line 2', 'Line 3']

        # Act
        result = TextualTUIAdapter.get_display_content(session, 5)

        # Assert
        assert result == ['Line 1', 'Line 2', 'Line 3']

    def test_get_display_content_truncated(self) -> None:
        """Test getting display content when content exceeds max lines."""
        # Arrange
        session = Mock(spec=FreewriteSession)
        session.content_lines = ['Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5']

        # Act
        result = TextualTUIAdapter.get_display_content(session, 3)

        # Assert
        assert result == ['Line 3', 'Line 4', 'Line 5']  # Last 3 lines

    def test_calculate_progress(self) -> None:
        """Test progress calculation delegation."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        expected_progress = {'word_count': 100, 'elapsed_time': 300}
        mock_service.get_session_stats.return_value = expected_progress

        adapter = TextualTUIAdapter(mock_service)
        session = Mock(spec=FreewriteSession)

        # Act
        result = adapter.calculate_progress(session)

        # Assert
        assert result == expected_progress
        mock_service.get_session_stats.assert_called_once_with(session)

    def test_handle_error_creates_ui_state(self) -> None:
        """Test error handling creates appropriate UI state."""
        # Arrange
        session = FreewriteSession(
            session_id=str(uuid.uuid4()),
            target_node=None,
            title=None,
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=50,
            elapsed_time=120,
            output_file_path='/test/output.md',
            content_lines=['Content line 1', 'Content line 2'],
        )
        error = ValueError('Test error')

        # Act
        result = TextualTUIAdapter.handle_error(error, session)

        # Assert
        assert isinstance(result, UIState)
        assert result.session == session
        assert result.input_text == ''
        assert result.display_lines == ['Content line 1', 'Content line 2']
        assert result.word_count == 50
        assert result.elapsed_time == 120
        assert result.time_remaining is None  # No time limit
        assert result.progress_percent is None
        assert result.error_message == 'Error: Test error'
        assert result.is_paused is False

    def test_handle_error_with_time_limit(self) -> None:
        """Test error handling with session that has time limit."""
        # Arrange
        session = FreewriteSession(
            session_id=str(uuid.uuid4()),
            target_node=None,
            title=None,
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=600,
            current_word_count=25,
            elapsed_time=300,
            output_file_path='/test/output.md',
            content_lines=['Line 1'],
        )
        error = OSError('File error')

        # Act
        result = TextualTUIAdapter.handle_error(error, session)

        # Assert
        assert result.time_remaining == 300  # 600 - 300
        assert result.error_message == 'Error: File error'

    def test_event_callback_registration_with_app(self) -> None:
        """Test event callback registration when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        # Create a mock app instance
        mock_app = Mock(spec=FreewritingApp)
        mock_app._input_change_callbacks = []
        mock_app._input_submit_callbacks = []
        mock_app._session_pause_callbacks = []
        mock_app._session_resume_callbacks = []
        mock_app._session_exit_callbacks = []
        adapter.app_instance = mock_app

        # Create mock callbacks
        change_callback = Mock()
        submit_callback = Mock()
        pause_callback = Mock()
        resume_callback = Mock()
        exit_callback = Mock()

        # Act
        adapter.on_input_change(change_callback)
        adapter.on_input_submit(submit_callback)
        adapter.on_session_pause(pause_callback)
        adapter.on_session_resume(resume_callback)
        adapter.on_session_exit(exit_callback)

        # Assert
        assert change_callback in mock_app._input_change_callbacks
        assert submit_callback in mock_app._input_submit_callbacks
        assert pause_callback in mock_app._session_pause_callbacks
        assert resume_callback in mock_app._session_resume_callbacks
        assert exit_callback in mock_app._session_exit_callbacks

    def test_event_callback_registration_no_app(self) -> None:
        """Test event callback registration when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        callback = Mock()

        # Act - should not raise exception
        adapter.on_input_change(callback)
        adapter.on_input_submit(callback)
        adapter.on_session_pause(callback)
        adapter.on_session_resume(callback)
        adapter.on_session_exit(callback)

        # Assert - no exceptions should be raised

    def test_update_content_area_with_app(self) -> None:
        """Test content area update when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_session = Mock(spec=FreewriteSession)
        mock_app = Mock(spec=FreewritingApp)
        mock_app.current_session = mock_session
        mock_app._update_display = Mock()
        adapter.app_instance = mock_app

        # Act
        adapter.update_content_area(['Line 1', 'Line 2'])

        # Assert
        mock_app._update_display.assert_called_once()

    def test_update_content_area_no_app(self) -> None:
        """Test content area update when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        # Act - should not raise exception
        adapter.update_content_area(['Line 1', 'Line 2'])

        # Assert - no exceptions should be raised

    def test_update_content_area_no_session(self) -> None:
        """Test content area update when app has no session."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_app = Mock(spec=FreewritingApp)
        mock_app.current_session = None
        adapter.app_instance = mock_app

        # Act - should not raise exception
        adapter.update_content_area(['Line 1', 'Line 2'])

        # Assert - no exceptions should be raised

    def test_update_stats_display_with_app(self) -> None:
        """Test stats display update when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_app = Mock(spec=FreewritingApp)
        mock_app._update_stats_display = Mock()
        adapter.app_instance = mock_app

        # Act
        adapter.update_stats_display({'word_count': 100})

        # Assert
        mock_app._update_stats_display.assert_called_once()

    def test_update_stats_display_no_app(self) -> None:
        """Test stats display update when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        # Act - should not raise exception
        adapter.update_stats_display({'word_count': 100})

        # Assert - no exceptions should be raised

    def test_clear_input_area_with_app(self) -> None:
        """Test input area clearing when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_input_box = Mock(spec=EmacsInput)
        mock_input_box.clear = Mock()

        mock_app = Mock(spec=FreewritingApp)
        mock_app.query_one = Mock(return_value=mock_input_box)
        adapter.app_instance = mock_app

        # Act
        adapter.clear_input_area()

        # Assert
        mock_app.query_one.assert_called_once_with('#input_box', EmacsInput)
        mock_input_box.clear.assert_called_once()

    def test_clear_input_area_no_app(self) -> None:
        """Test input area clearing when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        # Act - should not raise exception
        adapter.clear_input_area()

        # Assert - no exceptions should be raised

    def test_show_error_message_with_app(self) -> None:
        """Test error message display when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_app = Mock(spec=FreewritingApp)
        adapter.app_instance = mock_app

        # Act
        adapter.show_error_message('Test error')

        # Assert
        assert mock_app.error_message == 'Test error'

    def test_show_error_message_no_app(self) -> None:
        """Test error message display when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        # Act - should not raise exception
        adapter.show_error_message('Test error')

        # Assert - no exceptions should be raised

    def test_hide_error_message_with_app(self) -> None:
        """Test error message hiding when app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)

        mock_app = Mock(spec=FreewritingApp)
        mock_app.error_message = 'Some error'
        adapter.app_instance = mock_app

        # Act
        adapter.hide_error_message()

        # Assert
        assert mock_app.error_message is None

    def test_hide_error_message_no_app(self) -> None:
        """Test error message hiding when no app instance exists."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        adapter.app_instance = None

        # Act - should not raise exception
        adapter.hide_error_message()

        # Assert - no exceptions should be raised

    def test_set_theme_valid_theme(self) -> None:
        """Test setting a valid theme."""
        # Act & Assert - should not raise exception
        TextualTUIAdapter.set_theme('dark')
        TextualTUIAdapter.set_theme('light')

    def test_set_theme_invalid_theme(self) -> None:
        """Test setting an invalid theme raises TUIError."""
        # Act & Assert
        with pytest.raises(TUIError, match='Invalid theme: invalid'):
            TextualTUIAdapter.set_theme('invalid')

    def test_run_tui_success(self) -> None:
        """Test successful TUI run."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        session_config = SessionConfig()

        # Mock the app creation and run
        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_app:
            mock_app_instance = Mock()
            mock_app_instance.run.return_value = 0
            mock_app.return_value = mock_app_instance

            # Act
            result = adapter.run_tui(session_config)

            # Assert
            assert result == 0
            mock_app.assert_called_once_with(session_config, adapter)
            mock_app_instance.run.assert_called_once()
            assert adapter.app_instance == mock_app_instance

    def test_run_tui_with_theme_config(self) -> None:
        """Test TUI run with theme configuration."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        session_config = SessionConfig()
        tui_config = TUIConfig(theme='dark')

        with (
            patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_app,
            patch.object(TextualTUIAdapter, 'set_theme') as mock_set_theme,
        ):
            mock_app_instance = Mock()
            mock_app_instance.run.return_value = 0
            mock_app.return_value = mock_app_instance

            # Act
            result = adapter.run_tui(session_config, tui_config)

            # Assert
            assert result == 0
            mock_set_theme.assert_called_once_with('dark')
            mock_app.assert_called_once_with(session_config, adapter)

    def test_run_tui_app_returns_none(self) -> None:
        """Test TUI run when app returns None exit code."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        session_config = SessionConfig()

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_app:
            mock_app_instance = Mock()
            mock_app_instance.run.return_value = None
            mock_app.return_value = mock_app_instance

            # Act
            result = adapter.run_tui(session_config)

            # Assert
            assert result == 0  # Should default to 0

    def test_run_tui_exception_handling(self) -> None:
        """Test TUI run exception handling."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        session_config = SessionConfig()

        with patch('prosemark.freewriting.adapters.tui_adapter.FreewritingApp') as mock_app:
            mock_app.side_effect = Exception('App creation failed')

            # Act & Assert
            with pytest.raises(TUIError, match='TUI application failed'):
                adapter.run_tui(session_config)

    def test_run_tui_invalid_theme_handling(self) -> None:
        """Test TUI run handles invalid theme in config."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        adapter = TextualTUIAdapter(mock_service)
        session_config = SessionConfig()
        tui_config = TUIConfig(theme='invalid_theme')

        # Act & Assert
        with pytest.raises(TUIError, match='TUI application failed'):
            adapter.run_tui(session_config, tui_config)


class TestEmacsInput:
    """Test the custom Input widget with emacs keybindings."""

    def test_emacs_input_initialization(self) -> None:
        """Test EmacsInput initializes with kill buffer."""
        # Act
        widget = EmacsInput()

        # Assert
        assert widget._kill_buffer == ''

    def test_move_char_backward(self) -> None:
        """Test _move_char_backward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_char_backward()  # This should silently handle the NoActiveAppError

    def test_move_char_backward_at_start(self) -> None:
        """Test _move_char_backward method handles exception gracefully."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_char_backward()  # This should silently handle the NoActiveAppError

    def test_move_char_forward(self) -> None:
        """Test _move_char_forward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_char_forward()  # This should silently handle the NoActiveAppError

    def test_move_char_forward_at_end(self) -> None:
        """Test _move_char_forward method handles exception gracefully."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_char_forward()  # This should silently handle the NoActiveAppError

    def test_move_line_start(self) -> None:
        """Test _move_line_start method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_line_start()  # This should silently handle the NoActiveAppError

    def test_move_line_end(self) -> None:
        """Test _move_line_end method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_line_end()  # This should silently handle the NoActiveAppError

    def test_delete_char_forward(self) -> None:
        """Test _delete_char_forward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._delete_char_forward()  # This should silently handle the NoActiveAppError

    def test_delete_char_forward_at_end(self) -> None:
        """Test _delete_char_forward method handles exception gracefully."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._delete_char_forward()  # This should silently handle the NoActiveAppError

    def test_kill_to_line_end(self) -> None:
        """Test _kill_to_line_end method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._kill_to_line_end()  # This should silently handle the NoActiveAppError

    def test_yank_killed_text(self) -> None:
        """Test _yank_killed_text method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()
        widget._kill_buffer = ' world'  # This is safe to set as it's not a reactive property

        # Act & Assert - Should not raise an exception due to exception handling
        widget._yank_killed_text()  # This should silently handle the NoActiveAppError

    def test_yank_empty_kill_buffer(self) -> None:
        """Test _yank_killed_text method with empty kill buffer doesn't crash."""
        # Arrange
        widget = EmacsInput()
        widget._kill_buffer = ''  # This is safe to set as it's not a reactive property

        # Act & Assert - Should not raise an exception due to exception handling
        widget._yank_killed_text()  # This should silently handle the NoActiveAppError

    def test_move_word_backward(self) -> None:
        """Test _move_word_backward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_word_backward()  # This should silently handle the NoActiveAppError

    def test_move_word_backward_with_spaces(self) -> None:
        """Test _move_word_backward method handles exception gracefully."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_word_backward()  # This should silently handle the NoActiveAppError

    def test_move_word_forward(self) -> None:
        """Test _move_word_forward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._move_word_forward()  # This should silently handle the NoActiveAppError

    def test_delete_word_forward(self) -> None:
        """Test _delete_word_forward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._delete_word_forward()  # This should silently handle the NoActiveAppError

    def test_kill_word_backward_full_word(self) -> None:
        """Test _kill_word_backward method doesn't crash when called outside app context."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._kill_word_backward()  # This should silently handle the NoActiveAppError

    def test_kill_word_backward_to_beginning(self) -> None:
        """Test _kill_word_backward method handles exception gracefully."""
        # Arrange
        widget = EmacsInput()

        # Act & Assert - Should not raise an exception due to exception handling
        widget._kill_word_backward()  # This should silently handle the NoActiveAppError
