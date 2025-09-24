"""Complete tests for freewriting domain models to achieve 100% coverage.

This module completes the test coverage for all freewriting domain models,
covering all the methods and validation scenarios that were missed.
"""

from datetime import UTC, datetime

import pytest

from prosemark.freewriting.domain.models import (
    FileTarget,
    FreewriteContent,
    FreewriteSession,
    SessionConfig,
    SessionState,
)


class TestFreewriteSessionMethods:
    """Test FreewriteSession methods that were not covered."""

    def test_add_content_line_success(self) -> None:
        """Test adding content line updates word count and content."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=10,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
            content_lines=['Previous line'],
        )

        new_session = session.add_content_line('Hello world test')

        assert new_session.content_lines == ['Previous line', 'Hello world test']
        assert new_session.current_word_count == 13  # 10 + 3 new words
        assert new_session.session_id == session.session_id  # Other fields unchanged

    def test_add_content_line_empty_content(self) -> None:
        """Test adding empty content line."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=5,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
        )

        new_session = session.add_content_line('')

        assert new_session.content_lines == ['']
        assert new_session.current_word_count == 5  # No word count change

    def test_update_elapsed_time_success(self) -> None:
        """Test updating elapsed time with valid value."""
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

        new_session = session.update_elapsed_time(300)

        assert new_session.elapsed_time == 300
        assert new_session.session_id == session.session_id  # Other fields unchanged

    def test_update_elapsed_time_negative_value(self) -> None:
        """Test updating elapsed time with negative value raises error."""
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

        with pytest.raises(ValueError, match='elapsed_seconds cannot be negative'):
            session.update_elapsed_time(-100)

    def test_change_state_success(self) -> None:
        """Test changing session state."""
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
            state=SessionState.INITIALIZING,
        )

        new_session = session.change_state(SessionState.ACTIVE)

        assert new_session.state == SessionState.ACTIVE
        assert new_session.session_id == session.session_id  # Other fields unchanged

    def test_is_goal_reached_no_goals(self) -> None:
        """Test is_goal_reached when no goals are set."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=None,
            current_word_count=100,
            elapsed_time=3600,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {}

    def test_is_goal_reached_word_count_reached(self) -> None:
        """Test is_goal_reached when word count goal is reached."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=100,
            time_limit=None,
            current_word_count=150,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {'word_count': True}

    def test_is_goal_reached_word_count_not_reached(self) -> None:
        """Test is_goal_reached when word count goal is not reached."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=100,
            time_limit=None,
            current_word_count=50,
            elapsed_time=0,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {'word_count': False}

    def test_is_goal_reached_time_limit_reached(self) -> None:
        """Test is_goal_reached when time limit is reached."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=1800,
            current_word_count=0,
            elapsed_time=2000,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {'time_limit': True}

    def test_is_goal_reached_time_limit_not_reached(self) -> None:
        """Test is_goal_reached when time limit is not reached."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=None,
            time_limit=1800,
            current_word_count=0,
            elapsed_time=1000,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {'time_limit': False}

    def test_is_goal_reached_both_goals(self) -> None:
        """Test is_goal_reached when both goals are set."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=start_time,
            word_count_goal=100,
            time_limit=1800,
            current_word_count=150,
            elapsed_time=2000,
            output_file_path='/test/path/output.md',
        )

        result = session.is_goal_reached()
        assert result == {'word_count': True, 'time_limit': True}

    def test_validate_zero_word_count_goal(self) -> None:
        """Test that zero word count goal raises validation error."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='word_count_goal must be positive'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=0,
                time_limit=None,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )

    def test_validate_zero_time_limit(self) -> None:
        """Test that zero time limit raises validation error."""
        start_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='time_limit must be positive'):
            FreewriteSession(
                session_id='01234567-89ab-cdef-0123-456789abcdef',
                target_node=None,
                title=None,
                start_time=start_time,
                word_count_goal=None,
                time_limit=0,
                current_word_count=0,
                elapsed_time=0,
                output_file_path='/test/path/output.md',
            )


class TestSessionConfigMethods:
    """Test SessionConfig methods and validation that were not covered."""

    def test_validate_zero_word_count_goal(self) -> None:
        """Test that zero word count goal raises validation error."""
        with pytest.raises(ValueError, match='word_count_goal must be positive'):
            SessionConfig(
                target_node=None,
                title=None,
                word_count_goal=0,
                time_limit=None,
                theme='default',
                current_directory='/test/project',
            )

    def test_validate_zero_time_limit(self) -> None:
        """Test that zero time limit raises validation error."""
        with pytest.raises(ValueError, match='time_limit must be positive'):
            SessionConfig(
                target_node=None,
                title=None,
                word_count_goal=None,
                time_limit=0,
                theme='default',
                current_directory='/test/project',
            )


class TestFreewriteContent:
    """Test the FreewriteContent domain model."""

    def test_creates_content_with_all_data(self) -> None:
        """Test that content can be created with all required data."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        content = FreewriteContent(
            content='Hello world test',
            timestamp=timestamp,
            line_number=5,
            word_count=3,
        )

        assert content.content == 'Hello world test'
        assert content.timestamp == timestamp
        assert content.line_number == 5
        assert content.word_count == 3

    def test_validate_line_number_negative(self) -> None:
        """Test that negative line numbers raise validation errors."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='line_number must be positive'):
            FreewriteContent(
                content='Test content',
                timestamp=timestamp,
                line_number=-1,
                word_count=2,
            )

    def test_validate_line_number_zero(self) -> None:
        """Test that zero line number raises validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='line_number must be positive'):
            FreewriteContent(
                content='Test content',
                timestamp=timestamp,
                line_number=0,
                word_count=2,
            )

    def test_validate_word_count_mismatch_higher(self) -> None:
        """Test that higher word count than actual raises validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='word_count mismatch: expected 2, got 5'):
            FreewriteContent(
                content='Hello world',
                timestamp=timestamp,
                line_number=1,
                word_count=5,  # Actual is 2
            )

    def test_validate_word_count_mismatch_lower(self) -> None:
        """Test that lower word count than actual raises validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='word_count mismatch: expected 3, got 1'):
            FreewriteContent(
                content='Hello world test',
                timestamp=timestamp,
                line_number=1,
                word_count=1,  # Actual is 3
            )

    def test_from_content_with_timestamp(self) -> None:
        """Test creating content from string with explicit timestamp."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        content = FreewriteContent.from_content(
            content='Hello world test',
            line_number=5,
            timestamp=timestamp,
        )

        assert content.content == 'Hello world test'
        assert content.timestamp == timestamp
        assert content.line_number == 5
        assert content.word_count == 3

    def test_from_content_without_timestamp(self) -> None:
        """Test creating content from string without timestamp (uses current time)."""
        content = FreewriteContent.from_content(
            content='Hello world',
            line_number=1,
            timestamp=None,
        )

        assert content.content == 'Hello world'
        assert content.line_number == 1
        assert content.word_count == 2
        # Timestamp should be recent (within last few seconds)
        now = datetime.now(tz=UTC)
        time_diff = (now - content.timestamp).total_seconds()
        assert 0 <= time_diff < 5  # Should be very recent

    def test_from_content_empty_content(self) -> None:
        """Test creating content from empty string."""
        content = FreewriteContent.from_content(
            content='',
            line_number=1,
        )

        assert content.content == ''
        assert content.line_number == 1
        assert content.word_count == 0

    def test_frozen_dataclass_immutability(self) -> None:
        """Test that FreewriteContent is immutable."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        content = FreewriteContent(
            content='Hello world',
            timestamp=timestamp,
            line_number=1,
            word_count=2,
        )

        # Should raise an error when trying to modify
        with pytest.raises(AttributeError):
            content.content = 'Modified'  # type: ignore[misc]


class TestFileTarget:
    """Test the FileTarget domain model."""

    def test_creates_file_target_with_all_data(self) -> None:
        """Test that file target can be created with all required data."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        target = FileTarget(
            file_path='/test/path/output.md',
            is_node=True,
            node_uuid='01234567-89ab-cdef-0123-456789abcdef',
            created_timestamp=timestamp,
            file_format='markdown',
        )

        assert target.file_path == '/test/path/output.md'
        assert target.is_node is True
        assert target.node_uuid == '01234567-89ab-cdef-0123-456789abcdef'
        assert target.created_timestamp == timestamp
        assert target.file_format == 'markdown'

    def test_validate_node_consistency_missing_uuid(self) -> None:
        """Test that is_node=True without node_uuid raises validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='node_uuid is required when is_node is True'):
            FileTarget(
                file_path='/test/path/output.md',
                is_node=True,
                node_uuid=None,
                created_timestamp=timestamp,
            )

    def test_validate_node_consistency_invalid_uuid(self) -> None:
        """Test that invalid node UUID raises validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='Invalid node_uuid format'):
            FileTarget(
                file_path='/test/path/output.md',
                is_node=True,
                node_uuid='invalid-uuid',
                created_timestamp=timestamp,
            )

    def test_validate_file_format_unsupported(self) -> None:
        """Test that unsupported file formats raise validation error."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        with pytest.raises(ValueError, match='Unsupported file_format'):
            FileTarget(
                file_path='/test/path/output.txt',
                is_node=False,
                node_uuid=None,
                created_timestamp=timestamp,
                file_format='plaintext',
            )

    def test_for_daily_file(self) -> None:
        """Test creating FileTarget for daily file."""
        target = FileTarget.for_daily_file('/test/daily/2024-01-15.md')

        assert target.file_path == '/test/daily/2024-01-15.md'
        assert target.is_node is False
        assert target.node_uuid is None
        assert target.file_format == 'markdown'
        # Timestamp should be recent
        now = datetime.now(tz=UTC)
        time_diff = (now - target.created_timestamp).total_seconds()
        assert 0 <= time_diff < 5

    def test_for_node(self) -> None:
        """Test creating FileTarget for node file."""
        target = FileTarget.for_node(
            '/test/nodes/01234567-89ab-cdef-0123-456789abcdef.md', '01234567-89ab-cdef-0123-456789abcdef'
        )

        assert target.file_path == '/test/nodes/01234567-89ab-cdef-0123-456789abcdef.md'
        assert target.is_node is True
        assert target.node_uuid == '01234567-89ab-cdef-0123-456789abcdef'
        assert target.file_format == 'markdown'
        # Timestamp should be recent
        now = datetime.now(tz=UTC)
        time_diff = (now - target.created_timestamp).total_seconds()
        assert 0 <= time_diff < 5

    def test_frozen_dataclass_immutability(self) -> None:
        """Test that FileTarget is immutable."""
        timestamp = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

        target = FileTarget(
            file_path='/test/path/output.md',
            is_node=False,
            node_uuid=None,
            created_timestamp=timestamp,
        )

        # Should raise an error when trying to modify
        with pytest.raises(AttributeError):
            target.file_path = '/modified/path.md'  # type: ignore[misc]
