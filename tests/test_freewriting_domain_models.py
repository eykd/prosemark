"""Tests for freewriting domain models."""

from datetime import UTC, datetime

import pytest

from prosemark.freewriting.domain.models import (
    FreewriteSession,
    SessionConfig,
    SessionState,
)


class TestSessionState:
    """Test the SessionState enumeration."""

    def test_all_expected_states_exist(self) -> None:
        """Test that all expected session states are defined."""
        expected_states = {
            'INITIALIZING',
            'ACTIVE',
            'PAUSED',
            'COMPLETED',
            'ARCHIVED',
        }

        actual_states = {state.name for state in SessionState}
        assert actual_states == expected_states

    def test_state_values(self) -> None:
        """Test that session state values are correctly defined."""
        assert SessionState.INITIALIZING.value == 'initializing'
        assert SessionState.ACTIVE.value == 'active'
        assert SessionState.PAUSED.value == 'paused'
        assert SessionState.COMPLETED.value == 'completed'
        assert SessionState.ARCHIVED.value == 'archived'


class TestFreewriteSession:
    """Test the FreewriteSession domain model."""

    def test_creates_session_with_minimal_data(self) -> None:
        """Test that session can be created with minimal required data."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
        )

        assert session.session_id == '01234567-89ab-cdef-0123-456789abcdef'
        assert session.target_node is None
        assert session.title is None
        assert session.start_time == start_time
        assert session.word_count_goal is None
        assert session.time_limit is None
        assert session.current_word_count == 0
        assert session.elapsed_time == 0
        assert session.output_file_path == '/test/path/output.md'
        assert session.content_lines == []
        assert session.state == SessionState.INITIALIZING

    def test_creates_session_with_full_data(self) -> None:
        """Test that session can be created with all optional data."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
        content = ['Line 1', 'Line 2', 'Line 3']

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title='Test Session',
            start_time=start_time,
            word_count_goal=1000,
            time_limit=3600,
            current_word_count=150,
            elapsed_time=900,
            output_file_path='/test/path/output.md',
            content_lines=content,
            state=SessionState.ACTIVE,
        )

        assert session.session_id == '01234567-89ab-cdef-0123-456789abcdef'
        assert session.target_node == '01234567-89ab-cdef-0123-456789abcdef'
        assert session.title == 'Test Session'
        assert session.start_time == start_time
        assert session.word_count_goal == 1000
        assert session.time_limit == 3600
        assert session.current_word_count == 150
        assert session.elapsed_time == 900
        assert session.output_file_path == '/test/path/output.md'
        assert session.content_lines == content
        assert session.state == SessionState.ACTIVE

    def test_validates_session_id_format(self) -> None:
        """Test that invalid session IDs raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='Invalid session_id format'):
            FreewriteSession(
                session_id='invalid-uuid',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=None,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_target_node_format_when_provided(self) -> None:
        """Test that invalid target node UUIDs raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='Invalid target_node UUID format'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node='invalid-uuid',
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=None,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_start_time_not_in_future(self) -> None:
        """Test that future start times raise validation error."""
        # Set start time far in the future
        future_time = datetime(2030, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='start_time cannot be in the future'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=future_time,
                word_count_goal=None,
                time_limit=None,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_negative_word_count_goal(self) -> None:
        """Test that negative word count goals raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='word_count_goal must be positive'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=-100,
                time_limit=None,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_negative_time_limit(self) -> None:
        """Test that negative time limits raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='time_limit must be positive'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=-3600,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_negative_current_word_count(self) -> None:
        """Test that negative current word counts raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='current_word_count cannot be negative'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=None,
                current_word_count=-10,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validates_negative_elapsed_time(self) -> None:
        """Test that negative elapsed times raise validation errors."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='elapsed_time cannot be negative'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=None,
                current_word_count=0,
                elapsed_time=-900,
                output_file_path='/test/path/output.md',
            )

    def test_frozen_dataclass_immutability(self) -> None:
        """Test that FreewriteSession is immutable."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
        )

        # Should raise an error when trying to modify
        with pytest.raises(AttributeError):
            session.current_word_count = 100  # type: ignore[misc]

    def test_calculate_word_count_with_empty_content(self) -> None:
        """Test word count calculation with no content."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
            content_lines=[],
        )

        assert session.calculate_word_count() == 0

    def test_calculate_word_count_with_content(self) -> None:
        """Test word count calculation with content lines."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
        content = ['Hello world', 'This is a test', 'Multiple words here']

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
            content_lines=content,
        )

        # "Hello world" (2) + "This is a test" (4) + "Multiple words here" (3) = 9 words
        assert session.calculate_word_count() == 9


class TestSessionConfig:
    """Test the SessionConfig domain model."""

    def test_creates_config_with_minimal_data(self) -> None:
        """Test that config can be created with minimal required data."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        assert config.target_node is None
        assert config.title is None
        assert config.word_count_goal is None
        assert config.time_limit is None
        assert config.theme == 'default'
        assert config.current_directory == '/test/project'

    def test_creates_config_with_full_data(self) -> None:
        """Test that config can be created with all optional data."""
        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title='Test Session',
            word_count_goal=1000,
            time_limit=3600,
            theme='dark',
            current_directory='/test/project',
        )

        assert config.target_node == '01234567-89ab-cdef-0123-456789abcdef'
        assert config.title == 'Test Session'
        assert config.word_count_goal == 1000
        assert config.time_limit == 3600
        assert config.theme == 'dark'
        assert config.current_directory == '/test/project'

    def test_validates_target_node_format_when_provided(self) -> None:
        """Test that invalid target node UUIDs raise validation errors."""
        with pytest.raises(ValueError, match='Invalid target_node UUID format'):
            SessionConfig(
                target_node='invalid-uuid',
                title=None,
                word_count_goal=None,
                time_limit=None,
                theme='default',
                current_directory='/test/project',
            )

    def test_validates_negative_word_count_goal(self) -> None:
        """Test that negative word count goals raise validation errors."""
        with pytest.raises(ValueError, match='word_count_goal must be positive'):
            SessionConfig(
                target_node=None,
                title=None,
                word_count_goal=-100,
                time_limit=None,
                theme='default',
                current_directory='/test/project',
            )

    def test_validates_negative_time_limit(self) -> None:
        """Test that negative time limits raise validation errors."""
        with pytest.raises(ValueError, match='time_limit must be positive'):
            SessionConfig(
                target_node=None,
                title=None,
                word_count_goal=None,
                time_limit=-3600,
                theme='default',
                current_directory='/test/project',
            )

    def test_has_goals_with_word_count_goal(self) -> None:
        """Test has_goals() returns True when word count goal is set."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=1000,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        assert config.has_goals() is True

    def test_has_goals_with_time_limit(self) -> None:
        """Test has_goals() returns True when time limit is set."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=3600,
            theme='default',
            current_directory='/test/project',
        )

        assert config.has_goals() is True

    def test_has_goals_with_both_goals(self) -> None:
        """Test has_goals() returns True when both goals are set."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=1000,
            time_limit=3600,
            theme='default',
            current_directory='/test/project',
        )

        assert config.has_goals() is True

    def test_has_goals_with_no_goals(self) -> None:
        """Test has_goals() returns False when no goals are set."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        assert config.has_goals() is False

    def test_is_node_targeted_with_node(self) -> None:
        """Test is_node_targeted() returns True when target node is set."""
        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        assert config.is_node_targeted() is True

    def test_is_node_targeted_without_node(self) -> None:
        """Test is_node_targeted() returns False when no target node is set."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        assert config.is_node_targeted() is False

    def test_frozen_dataclass_immutability(self) -> None:
        """Test that SessionConfig is immutable."""
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='default',
            current_directory='/test/project',
        )

        # Should raise an error when trying to modify
        with pytest.raises(AttributeError):
            config.theme = 'dark'  # type: ignore[misc]
