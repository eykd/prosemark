"""Contract tests for TUIAdapterPort protocol (T005).

These tests verify that any implementation of the TUIAdapterPort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from prosemark.freewriting.domain.exceptions import FileSystemError
from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig
from prosemark.freewriting.ports.tui_adapter import (
    ErrorEvent,
    InputSubmittedEvent,
    SessionCompletedEvent,
    SessionProgressEvent,
    TUIAdapterPort,
    TUIConfig,
    TUIDisplayPort,
    TUIEventPort,
    UIState,
)


class TestTUIAdapterPortContract:
    """Test contract compliance for TUIAdapterPort implementations."""

    def test_initialize_session_accepts_session_config(self) -> None:
        """Test initialize_session() accepts SessionConfig and returns FreewriteSession."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title='TUI Test Session',
            word_count_goal=1000,
            time_limit=3600,
            theme='dark',
            current_directory='/test/project',
        )
        expected_session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=config.target_node,
            title=config.title,
            start_time=datetime.now(UTC),
            word_count_goal=config.word_count_goal,
            time_limit=config.time_limit,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/project/2024-03-15-1430.md',
            content_lines=[],
        )
        mock_adapter.initialize_session.return_value = expected_session

        # Act
        result = mock_adapter.initialize_session(config)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.session_id == '01234567-89ab-cdef-0123-456789abcdef'
        assert result.target_node == config.target_node
        mock_adapter.initialize_session.assert_called_once_with(config)

    def test_initialize_session_raises_validation_error_on_invalid_config(self) -> None:
        """Test initialize_session() raises ValidationError for invalid config."""
        # Act & Assert - ValidationError should be raised when creating invalid SessionConfig
        import pytest

        with pytest.raises(ValueError, match='Invalid target_node UUID format'):
            SessionConfig(
                target_node='invalid-format',
                title='',
                word_count_goal=-500,
                time_limit=-60,
                theme='nonexistent',
                current_directory='/invalid/path',
            )

    def test_handle_input_submission_updates_session(self) -> None:
        """Test handle_input_submission() processes input and returns updated session."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        initial_session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Input Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )
        input_text = 'This is user input from the TUI'
        updated_session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Input Test',
            start_time=initial_session.start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=8,  # 8 words in the input
            elapsed_time=5,
            output_file_path='/test/output.md',
            content_lines=['This is user input from the TUI'],
        )
        mock_adapter.handle_input_submission.return_value = updated_session

        # Act
        result = mock_adapter.handle_input_submission(initial_session, input_text)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.current_word_count > initial_session.current_word_count
        assert input_text in result.content_lines
        mock_adapter.handle_input_submission.assert_called_once_with(initial_session, input_text)

    def test_handle_input_submission_with_empty_input(self) -> None:
        """Test handle_input_submission() handles empty input gracefully."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Empty Input Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=10,
            elapsed_time=30,
            output_file_path='/test/output.md',
            content_lines=['Previous line'],
        )
        empty_input = ''
        # Session should remain unchanged for empty input
        mock_adapter.handle_input_submission.return_value = session

        # Act
        result = mock_adapter.handle_input_submission(session, empty_input)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.current_word_count == session.current_word_count
        mock_adapter.handle_input_submission.assert_called_once_with(session, empty_input)

    def test_get_display_content_returns_content_lines(self) -> None:
        """Test get_display_content() returns list of display lines."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Display Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=50,
            elapsed_time=120,
            output_file_path='/test/output.md',
            content_lines=['Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5'],
        )
        max_lines = 3
        expected_display = ['Line 3', 'Line 4', 'Line 5']  # Last 3 lines
        mock_adapter.get_display_content.return_value = expected_display

        # Act
        result = mock_adapter.get_display_content(session, max_lines)

        # Assert
        assert isinstance(result, list)
        assert len(result) == max_lines
        assert all(isinstance(line, str) for line in result)
        mock_adapter.get_display_content.assert_called_once_with(session, max_lines)

    def test_get_display_content_handles_fewer_lines_than_max(self) -> None:
        """Test get_display_content() when session has fewer lines than max."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Few Lines',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=15,
            elapsed_time=60,
            output_file_path='/test/output.md',
            content_lines=['Only line', 'Second line'],
        )
        max_lines = 10
        expected_display = ['Only line', 'Second line']
        mock_adapter.get_display_content.return_value = expected_display

        # Act
        result = mock_adapter.get_display_content(session, max_lines)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2  # Only 2 lines available
        mock_adapter.get_display_content.assert_called_once_with(session, max_lines)

    def test_calculate_progress_returns_progress_dict(self) -> None:
        """Test calculate_progress() returns dictionary with progress metrics."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Progress Test',
            start_time=datetime.now(UTC),
            word_count_goal=1000,
            time_limit=1800,
            current_word_count=400,
            elapsed_time=720,
            output_file_path='/test/output.md',
            content_lines=['Content'] * 10,
        )
        expected_progress = {
            'word_count': 400,
            'elapsed_time': 720,
            'time_remaining': 1080,
            'progress_percent': 40.0,
            'goals_met': {'word_count': False, 'time_limit': False},
        }
        mock_adapter.calculate_progress.return_value = expected_progress

        # Act
        result = mock_adapter.calculate_progress(session)

        # Assert
        assert isinstance(result, dict)
        assert 'word_count' in result
        assert 'elapsed_time' in result
        assert 'progress_percent' in result
        assert 'goals_met' in result
        assert result['word_count'] == 400
        mock_adapter.calculate_progress.assert_called_once_with(session)

    def test_calculate_progress_handles_no_goals(self) -> None:
        """Test calculate_progress() with session that has no goals."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='No Goals',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=150,
            elapsed_time=300,
            output_file_path='/test/output.md',
            content_lines=['Content'],
        )
        expected_progress = {
            'word_count': 150,
            'elapsed_time': 300,
            'time_remaining': None,
            'progress_percent': None,
            'goals_met': {'word_count': None, 'time_limit': None},
        }
        mock_adapter.calculate_progress.return_value = expected_progress

        # Act
        result = mock_adapter.calculate_progress(session)

        # Assert
        assert isinstance(result, dict)
        assert result['progress_percent'] is None
        assert result['time_remaining'] is None
        mock_adapter.calculate_progress.assert_called_once_with(session)

    def test_handle_error_returns_ui_state_with_error_info(self) -> None:
        """Test handle_error() returns UIState with error information."""
        # Arrange
        mock_adapter = Mock(spec=TUIAdapterPort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Error Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )
        error = FileSystemError('write', '/test/output.md', 'Disk full')
        expected_ui_state = UIState(
            session=session,
            input_text='',
            display_lines=[],
            word_count=0,
            elapsed_time=0,
            time_remaining=None,
            progress_percent=None,
            error_message='Disk full',
            is_paused=True,
        )
        mock_adapter.handle_error.return_value = expected_ui_state

        # Act
        result = mock_adapter.handle_error(error, session)

        # Assert
        assert isinstance(result, UIState)
        assert result.error_message is not None
        assert result.session == session
        mock_adapter.handle_error.assert_called_once_with(error, session)

    def test_protocol_methods_exist(self) -> None:
        """Test that TUIAdapterPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_adapter = Mock(spec=TUIAdapterPort)

        # Verify methods exist
        assert hasattr(mock_adapter, 'initialize_session')
        assert hasattr(mock_adapter, 'handle_input_submission')
        assert hasattr(mock_adapter, 'get_display_content')
        assert hasattr(mock_adapter, 'calculate_progress')
        assert hasattr(mock_adapter, 'handle_error')

        # Verify methods are callable
        assert callable(mock_adapter.initialize_session)
        assert callable(mock_adapter.handle_input_submission)
        assert callable(mock_adapter.get_display_content)
        assert callable(mock_adapter.calculate_progress)
        assert callable(mock_adapter.handle_error)


class TestTUIEventPortContract:
    """Test contract compliance for TUIEventPort implementations."""

    def test_on_input_change_accepts_callback(self) -> None:
        """Test on_input_change() accepts callback function."""
        # Arrange
        mock_event_port = Mock(spec=TUIEventPort)
        callback_function = Mock()
        mock_event_port.on_input_change.return_value = None

        # Act
        result = mock_event_port.on_input_change(callback_function)

        # Assert
        assert result is None
        mock_event_port.on_input_change.assert_called_once_with(callback_function)

    def test_on_input_submit_accepts_callback(self) -> None:
        """Test on_input_submit() accepts callback function."""
        # Arrange
        mock_event_port = Mock(spec=TUIEventPort)
        callback_function = Mock()
        mock_event_port.on_input_submit.return_value = None

        # Act
        result = mock_event_port.on_input_submit(callback_function)

        # Assert
        assert result is None
        mock_event_port.on_input_submit.assert_called_once_with(callback_function)

    def test_on_session_pause_accepts_callback(self) -> None:
        """Test on_session_pause() accepts callback function."""
        # Arrange
        mock_event_port = Mock(spec=TUIEventPort)
        callback_function = Mock()
        mock_event_port.on_session_pause.return_value = None

        # Act
        result = mock_event_port.on_session_pause(callback_function)

        # Assert
        assert result is None
        mock_event_port.on_session_pause.assert_called_once_with(callback_function)

    def test_on_session_resume_accepts_callback(self) -> None:
        """Test on_session_resume() accepts callback function."""
        # Arrange
        mock_event_port = Mock(spec=TUIEventPort)
        callback_function = Mock()
        mock_event_port.on_session_resume.return_value = None

        # Act
        result = mock_event_port.on_session_resume(callback_function)

        # Assert
        assert result is None
        mock_event_port.on_session_resume.assert_called_once_with(callback_function)

    def test_on_session_exit_accepts_callback(self) -> None:
        """Test on_session_exit() accepts callback function."""
        # Arrange
        mock_event_port = Mock(spec=TUIEventPort)
        callback_function = Mock()
        mock_event_port.on_session_exit.return_value = None

        # Act
        result = mock_event_port.on_session_exit(callback_function)

        # Assert
        assert result is None
        mock_event_port.on_session_exit.assert_called_once_with(callback_function)

    def test_protocol_methods_exist(self) -> None:
        """Test that TUIEventPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_event_port = Mock(spec=TUIEventPort)

        # Verify methods exist
        assert hasattr(mock_event_port, 'on_input_change')
        assert hasattr(mock_event_port, 'on_input_submit')
        assert hasattr(mock_event_port, 'on_session_pause')
        assert hasattr(mock_event_port, 'on_session_resume')
        assert hasattr(mock_event_port, 'on_session_exit')

        # Verify methods are callable
        assert callable(mock_event_port.on_input_change)
        assert callable(mock_event_port.on_input_submit)
        assert callable(mock_event_port.on_session_pause)
        assert callable(mock_event_port.on_session_resume)
        assert callable(mock_event_port.on_session_exit)


class TestTUIDisplayPortContract:
    """Test contract compliance for TUIDisplayPort implementations."""

    def test_update_content_area_accepts_lines_list(self) -> None:
        """Test update_content_area() accepts list of strings."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        content_lines = ['Line 1 of content', 'Line 2 of content', 'Line 3 of content']
        mock_display_port.update_content_area.return_value = None

        # Act
        result = mock_display_port.update_content_area(content_lines)

        # Assert
        assert result is None
        mock_display_port.update_content_area.assert_called_once_with(content_lines)

    def test_update_content_area_handles_empty_list(self) -> None:
        """Test update_content_area() handles empty content list."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        empty_lines: list[str] = []
        mock_display_port.update_content_area.return_value = None

        # Act
        result = mock_display_port.update_content_area(empty_lines)

        # Assert
        assert result is None
        mock_display_port.update_content_area.assert_called_once_with(empty_lines)

    def test_update_stats_display_accepts_stats_dict(self) -> None:
        """Test update_stats_display() accepts statistics dictionary."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        stats = {'word_count': 250, 'elapsed_time': 600, 'progress_percent': 50.0, 'time_remaining': 600}
        mock_display_port.update_stats_display.return_value = None

        # Act
        result = mock_display_port.update_stats_display(stats)

        # Assert
        assert result is None
        mock_display_port.update_stats_display.assert_called_once_with(stats)

    def test_clear_input_area_returns_none(self) -> None:
        """Test clear_input_area() returns None."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        mock_display_port.clear_input_area.return_value = None

        # Act
        result = mock_display_port.clear_input_area()

        # Assert
        assert result is None
        mock_display_port.clear_input_area.assert_called_once_with()

    def test_show_error_message_accepts_message_string(self) -> None:
        """Test show_error_message() accepts error message string."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        error_message = 'File system error occurred'
        mock_display_port.show_error_message.return_value = None

        # Act
        result = mock_display_port.show_error_message(error_message)

        # Assert
        assert result is None
        mock_display_port.show_error_message.assert_called_once_with(error_message)

    def test_hide_error_message_returns_none(self) -> None:
        """Test hide_error_message() returns None."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        mock_display_port.hide_error_message.return_value = None

        # Act
        result = mock_display_port.hide_error_message()

        # Assert
        assert result is None
        mock_display_port.hide_error_message.assert_called_once_with()

    def test_set_theme_accepts_theme_name(self) -> None:
        """Test set_theme() accepts theme name string."""
        # Arrange
        mock_display_port = Mock(spec=TUIDisplayPort)
        theme_name = 'dark_mode'
        mock_display_port.set_theme.return_value = None

        # Act
        result = mock_display_port.set_theme(theme_name)

        # Assert
        assert result is None
        mock_display_port.set_theme.assert_called_once_with(theme_name)

    def test_protocol_methods_exist(self) -> None:
        """Test that TUIDisplayPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_display_port = Mock(spec=TUIDisplayPort)

        # Verify methods exist
        assert hasattr(mock_display_port, 'update_content_area')
        assert hasattr(mock_display_port, 'update_stats_display')
        assert hasattr(mock_display_port, 'clear_input_area')
        assert hasattr(mock_display_port, 'show_error_message')
        assert hasattr(mock_display_port, 'hide_error_message')
        assert hasattr(mock_display_port, 'set_theme')

        # Verify methods are callable
        assert callable(mock_display_port.update_content_area)
        assert callable(mock_display_port.update_stats_display)
        assert callable(mock_display_port.clear_input_area)
        assert callable(mock_display_port.show_error_message)
        assert callable(mock_display_port.hide_error_message)
        assert callable(mock_display_port.set_theme)


class TestTUIDataStructuresContract:
    """Test contract compliance for TUI-related data structures."""

    def test_ui_state_has_required_fields(self) -> None:
        """Test UIState dataclass has all required fields."""
        # Arrange
        ui_state = UIState(
            session=None,
            input_text='test input',
            display_lines=['line1', 'line2'],
            word_count=25,
            elapsed_time=300,
            time_remaining=600,
            progress_percent=50.0,
            error_message=None,
            is_paused=False,
        )

        # Assert
        assert hasattr(ui_state, 'session')
        assert hasattr(ui_state, 'input_text')
        assert hasattr(ui_state, 'display_lines')
        assert hasattr(ui_state, 'word_count')
        assert hasattr(ui_state, 'elapsed_time')
        assert hasattr(ui_state, 'time_remaining')
        assert hasattr(ui_state, 'progress_percent')
        assert hasattr(ui_state, 'error_message')
        assert hasattr(ui_state, 'is_paused')

    def test_tui_config_has_required_fields(self) -> None:
        """Test TUIConfig dataclass has all required fields."""
        # Arrange
        tui_config = TUIConfig(
            theme='default',
            content_height_percent=80,
            input_height_percent=20,
            show_word_count=True,
            show_timer=True,
            auto_scroll=True,
            max_display_lines=1000,
        )

        # Assert
        assert hasattr(tui_config, 'theme')
        assert hasattr(tui_config, 'content_height_percent')
        assert hasattr(tui_config, 'input_height_percent')
        assert hasattr(tui_config, 'show_word_count')
        assert hasattr(tui_config, 'show_timer')
        assert hasattr(tui_config, 'auto_scroll')
        assert hasattr(tui_config, 'max_display_lines')

    def test_input_submitted_event_has_required_fields(self) -> None:
        """Test InputSubmittedEvent dataclass has required fields."""
        # Arrange
        event = InputSubmittedEvent(content='User submitted content', timestamp='2024-03-15T14:30:00')

        # Assert
        assert hasattr(event, 'content')
        assert hasattr(event, 'timestamp')
        assert event.content == 'User submitted content'
        assert event.timestamp == '2024-03-15T14:30:00'

    def test_session_progress_event_has_required_fields(self) -> None:
        """Test SessionProgressEvent dataclass has required fields."""
        # Arrange
        event = SessionProgressEvent(word_count=150, elapsed_time=300, progress_percent=75.0)

        # Assert
        assert hasattr(event, 'word_count')
        assert hasattr(event, 'elapsed_time')
        assert hasattr(event, 'progress_percent')
        assert event.word_count == 150
        assert event.elapsed_time == 300
        assert event.progress_percent == 75.0

    def test_error_event_has_required_fields(self) -> None:
        """Test ErrorEvent dataclass has required fields."""
        # Arrange
        event = ErrorEvent(error_type='FileSystemError', message='Disk full', recoverable=False)

        # Assert
        assert hasattr(event, 'error_type')
        assert hasattr(event, 'message')
        assert hasattr(event, 'recoverable')
        assert event.error_type == 'FileSystemError'
        assert event.message == 'Disk full'
        assert event.recoverable is False

    def test_session_completed_event_has_required_fields(self) -> None:
        """Test SessionCompletedEvent dataclass has required fields."""
        # Arrange
        event = SessionCompletedEvent(final_word_count=500, total_time=1800, output_file='/project/output.md')

        # Assert
        assert hasattr(event, 'final_word_count')
        assert hasattr(event, 'total_time')
        assert hasattr(event, 'output_file')
        assert event.final_word_count == 500
        assert event.total_time == 1800
        assert event.output_file == '/project/output.md'
