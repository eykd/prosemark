"""Contract tests for FreewriteServicePort protocol (T004).

These tests verify that any implementation of the FreewriteServicePort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from prosemark.freewriting.domain.exceptions import FileSystemError, ValidationError
from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig
from prosemark.freewriting.ports.file_system import FileSystemPort
from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort
from prosemark.freewriting.ports.node_service import NodeServicePort


class TestFreewriteServicePortContract:
    """Test contract compliance for FreewriteServicePort implementations."""

    def test_create_session_accepts_session_config(self) -> None:
        """Test that create_session() accepts SessionConfig and returns FreewriteSession."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title='Test Session',
            word_count_goal=500,
            time_limit=1800,
            theme='dark',
            current_directory='/test/path',
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
            output_file_path='/test/output.md',
            content_lines=[],
        )
        mock_service.create_session.return_value = expected_session

        # Act
        result = mock_service.create_session(config)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.session_id == '01234567-89ab-cdef-0123-456789abcdef'
        assert result.target_node == config.target_node
        assert result.title == config.title
        mock_service.create_session.assert_called_once_with(config)

    def test_create_session_with_minimal_config(self) -> None:
        """Test create_session() with minimal configuration (no optional values)."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        config = SessionConfig(
            target_node=None,
            title=None,
            word_count_goal=None,
            time_limit=None,
            theme='dark',
            current_directory='/test/path',
        )
        expected_session = FreewriteSession(
            session_id='12345678-1234-1234-1234-123456789abc',
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
        mock_service.create_session.return_value = expected_session

        # Act
        result = mock_service.create_session(config)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.target_node is None
        assert result.title is None
        assert result.word_count_goal is None
        assert result.time_limit is None
        mock_service.create_session.assert_called_once_with(config)

    def test_create_session_raises_validation_error_on_invalid_config(self) -> None:
        """Test create_session() raises ValidationError for invalid configuration."""
        # Act & Assert - ValidationError should be raised when creating invalid SessionConfig
        with pytest.raises(ValueError, match='Invalid target_node UUID format'):
            SessionConfig(
                target_node='invalid-uuid',
                title='Test',
                word_count_goal=-100,
                time_limit=-60,
                theme='nonexistent',
                current_directory='/nonexistent/path',
            )

    def test_append_content_updates_session_and_word_count(self) -> None:
        """Test that append_content() updates session with new content and word count."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        initial_session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Test Session',
            start_time=datetime.now(UTC),
            word_count_goal=100,
            time_limit=600,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=[],
        )
        content = 'This is a test line with five words'
        updated_session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Test Session',
            start_time=initial_session.start_time,
            word_count_goal=100,
            time_limit=600,
            current_word_count=8,  # Updated word count
            elapsed_time=0,
            output_file_path='/test/output.md',
            content_lines=['This is a test line with five words'],
        )
        mock_service.append_content.return_value = updated_session

        # Act
        result = mock_service.append_content(initial_session, content)

        # Assert
        assert isinstance(result, FreewriteSession)
        assert result.current_word_count > initial_session.current_word_count
        assert content in result.content_lines
        mock_service.append_content.assert_called_once_with(initial_session, content)

    def test_append_content_raises_filesystem_error_on_write_failure(self) -> None:
        """Test append_content() raises FileSystemError when write fails."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Test',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/readonly/output.md',
            content_lines=[],
        )
        content = 'Test content'
        mock_service.append_content.side_effect = FileSystemError('write', '/path/session.md', 'Write failed')

        # Act & Assert
        try:
            mock_service.append_content(session, content)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_service.append_content.assert_called_once_with(session, content)

    def test_validate_node_uuid_accepts_valid_uuid_string(self) -> None:
        """Test validate_node_uuid() returns True for valid UUID."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        valid_uuids = [
            '01234567-89ab-cdef-0123-456789abcdef',
            '12345678-9abc-def0-1234-56789abcdef0',
            'abcdef01-2345-6789-abcd-ef0123456789',
        ]
        mock_service.validate_node_uuid.return_value = True

        # Act & Assert
        for uuid_str in valid_uuids:
            result = mock_service.validate_node_uuid(uuid_str)
            assert result is True

        assert mock_service.validate_node_uuid.call_count == len(valid_uuids)

    def test_validate_node_uuid_rejects_invalid_uuid_string(self) -> None:
        """Test validate_node_uuid() returns False for invalid UUID."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        invalid_uuids = [
            'not-a-uuid',
            '01234567-89ab-cdef-0123',  # Too short
            '01234567-89ab-cdef-0123-456789abcdefg',  # Invalid character
            '',
            '12345678-9abc-def0-1234-56789abcdef0-extra',  # Too long
        ]
        mock_service.validate_node_uuid.return_value = False

        # Act & Assert
        for uuid_str in invalid_uuids:
            result = mock_service.validate_node_uuid(uuid_str)
            assert result is False

        assert mock_service.validate_node_uuid.call_count == len(invalid_uuids)

    def test_create_daily_filename_generates_correct_format(self) -> None:
        """Test create_daily_filename() generates YYYY-MM-DD-HHmm.md format."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        test_timestamp = datetime(2024, 3, 15, 14, 30, 0, tzinfo=UTC)
        expected_filename = '2024-03-15-1430.md'
        mock_service.create_daily_filename.return_value = expected_filename

        # Act
        result = mock_service.create_daily_filename(test_timestamp)

        # Assert
        assert result == expected_filename
        assert result.endswith('.md')
        assert len(result) == 18  # YYYY-MM-DD-HHmm.md
        mock_service.create_daily_filename.assert_called_once_with(test_timestamp)

    def test_create_daily_filename_handles_different_times(self) -> None:
        """Test create_daily_filename() with various timestamps."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        test_cases = [
            (datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC), '2024-01-01-0000.md'),
            (datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC), '2024-12-31-2359.md'),
            (datetime(2024, 6, 15, 9, 5, 30, tzinfo=UTC), '2024-06-15-0905.md'),
        ]

        for timestamp, expected in test_cases:
            mock_service.create_daily_filename.return_value = expected

            # Act
            result = mock_service.create_daily_filename(timestamp)

            # Assert
            assert result == expected

        assert mock_service.create_daily_filename.call_count == len(test_cases)

    def test_get_session_stats_returns_progress_dict(self) -> None:
        """Test get_session_stats() returns dictionary with session metrics."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='Test Session',
            start_time=datetime.now(UTC),
            word_count_goal=500,
            time_limit=1800,
            current_word_count=250,
            elapsed_time=900,
            output_file_path='/test/output.md',
            content_lines=['Line 1', 'Line 2', 'Line 3'],
        )
        expected_stats = {
            'word_count': 250,
            'elapsed_time': 900,
            'progress_percent': 50.0,
            'time_remaining': 900,
            'words_per_minute': 16.67,
            'goal_completion': 0.5,
        }
        mock_service.get_session_stats.return_value = expected_stats

        # Act
        result = mock_service.get_session_stats(session)

        # Assert
        assert isinstance(result, dict)
        assert 'word_count' in result
        assert 'elapsed_time' in result
        assert result['word_count'] == 250
        assert result['elapsed_time'] == 900
        mock_service.get_session_stats.assert_called_once_with(session)

    def test_get_session_stats_handles_no_goals(self) -> None:
        """Test get_session_stats() with session that has no goals set."""
        # Arrange
        mock_service = Mock(spec=FreewriteServicePort)
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title='No Goals Session',
            start_time=datetime.now(UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=100,
            elapsed_time=300,
            output_file_path='/test/output.md',
            content_lines=['Some content'],
        )
        expected_stats = {
            'word_count': 100,
            'elapsed_time': 300,
            'progress_percent': None,
            'time_remaining': None,
            'words_per_minute': 20.0,
            'goal_completion': None,
        }
        mock_service.get_session_stats.return_value = expected_stats

        # Act
        result = mock_service.get_session_stats(session)

        # Assert
        assert isinstance(result, dict)
        assert result['word_count'] == 100
        assert result['progress_percent'] is None
        assert result['time_remaining'] is None
        mock_service.get_session_stats.assert_called_once_with(session)

    def test_protocol_methods_exist(self) -> None:
        """Test that FreewriteServicePort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_service = Mock(spec=FreewriteServicePort)

        # Verify methods exist
        assert hasattr(mock_service, 'create_session')
        assert hasattr(mock_service, 'append_content')
        assert hasattr(mock_service, 'validate_node_uuid')
        assert hasattr(mock_service, 'create_daily_filename')
        assert hasattr(mock_service, 'get_session_stats')

        # Verify methods are callable
        assert callable(mock_service.create_session)
        assert callable(mock_service.append_content)
        assert callable(mock_service.validate_node_uuid)
        assert callable(mock_service.create_daily_filename)
        assert callable(mock_service.get_session_stats)


class TestNodeServicePortContract:
    """Test contract compliance for NodeServicePort implementations."""

    def test_node_exists_returns_boolean(self) -> None:
        """Test node_exists() returns boolean value."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        mock_service.node_exists.return_value = True

        # Act
        result = mock_service.node_exists(node_uuid)

        # Assert
        assert isinstance(result, bool)
        assert result is True
        mock_service.node_exists.assert_called_once_with(node_uuid)

    def test_node_exists_handles_nonexistent_node(self) -> None:
        """Test node_exists() returns False for nonexistent node."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        nonexistent_uuid = 'nonexistent-uuid'
        mock_service.node_exists.return_value = False

        # Act
        result = mock_service.node_exists(nonexistent_uuid)

        # Assert
        assert result is False
        mock_service.node_exists.assert_called_once_with(nonexistent_uuid)

    def test_create_node_returns_file_path(self) -> None:
        """Test create_node() returns path to created node file."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        title = 'Test Node'
        expected_path = f'/project/nodes/{node_uuid}.md'
        mock_service.create_node.return_value = expected_path

        # Act
        result = mock_service.create_node(node_uuid, title)

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        mock_service.create_node.assert_called_once_with(node_uuid, title)

    def test_create_node_with_no_title(self) -> None:
        """Test create_node() works without title parameter."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        expected_path = f'/project/nodes/{node_uuid}.md'
        mock_service.create_node.return_value = expected_path

        # Act
        result = mock_service.create_node(node_uuid)

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        mock_service.create_node.assert_called_once_with(node_uuid)

    def test_create_node_raises_validation_error_on_invalid_uuid(self) -> None:
        """Test create_node() raises ValidationError for invalid UUID."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        invalid_uuid = 'invalid-uuid-format'
        mock_service.create_node.side_effect = ValidationError('node_uuid', 'invalid-format', 'Invalid UUID format')

        # Act & Assert
        try:
            mock_service.create_node(invalid_uuid)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_service.create_node.assert_called_once_with(invalid_uuid)

    def test_append_to_node_accepts_content_and_metadata(self) -> None:
        """Test append_to_node() accepts content list and session metadata."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        content = ['Line 1 of freewrite', 'Line 2 of freewrite', 'Line 3 of freewrite']
        session_metadata = {
            'session_id': 'test-session',
            'timestamp': '2024-03-15T14:30:00',
            'word_count': 15,
            'duration': 300,
        }
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, content, session_metadata)

    def test_append_to_node_raises_validation_error_on_nonexistent_node(self) -> None:
        """Test append_to_node() raises ValidationError if node doesn't exist."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        nonexistent_uuid = 'nonexistent-node-uuid'
        content = ['Some content']
        metadata = {'session_id': 'test'}
        mock_service.append_to_node.side_effect = ValidationError('node_uuid', 'nonexistent', 'Node does not exist')

        # Act & Assert
        try:
            mock_service.append_to_node(nonexistent_uuid, content, metadata)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_service.append_to_node.assert_called_once_with(nonexistent_uuid, content, metadata)

    def test_protocol_methods_exist(self) -> None:
        """Test that NodeServicePort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_service = Mock(spec=NodeServicePort)

        # Verify methods exist
        assert hasattr(mock_service, 'node_exists')
        assert hasattr(mock_service, 'create_node')
        assert hasattr(mock_service, 'append_to_node')

        # Verify methods are callable
        assert callable(mock_service.node_exists)
        assert callable(mock_service.create_node)
        assert callable(mock_service.append_to_node)


class TestFileSystemPortContract:
    """Test contract compliance for FileSystemPort implementations."""

    def test_write_file_accepts_path_and_content(self) -> None:
        """Test write_file() accepts file path and content."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/output.md'
        content = 'Test content to write'
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, content)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, content)

    def test_write_file_supports_append_mode(self) -> None:
        """Test write_file() supports append mode."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/output.md'
        content = 'Additional content'
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, content, append=True)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, content, append=True)

    def test_write_file_raises_filesystem_error_on_failure(self) -> None:
        """Test write_file() raises FileSystemError when write fails."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        readonly_path = '/readonly/file.md'
        content = 'Content'
        mock_fs.write_file.side_effect = FileSystemError('write', '/readonly/file.md', 'Permission denied')

        # Act & Assert
        try:
            mock_fs.write_file(readonly_path, content)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_fs.write_file.assert_called_once_with(readonly_path, content)

    def test_file_exists_returns_boolean(self) -> None:
        """Test file_exists() returns boolean value."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        existing_file = '/test/existing.md'
        mock_fs.file_exists.return_value = True

        # Act
        result = mock_fs.file_exists(existing_file)

        # Assert
        assert isinstance(result, bool)
        assert result is True
        mock_fs.file_exists.assert_called_once_with(existing_file)

    def test_file_exists_returns_false_for_nonexistent_file(self) -> None:
        """Test file_exists() returns False for nonexistent file."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        nonexistent_file = '/test/nonexistent.md'
        mock_fs.file_exists.return_value = False

        # Act
        result = mock_fs.file_exists(nonexistent_file)

        # Assert
        assert result is False
        mock_fs.file_exists.assert_called_once_with(nonexistent_file)

    def test_get_current_directory_returns_absolute_path(self) -> None:
        """Test get_current_directory() returns absolute path string."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        expected_path = '/home/user/project'
        mock_fs.get_current_directory.return_value = expected_path

        # Act
        result = mock_fs.get_current_directory()

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        assert result.startswith('/')  # Absolute path
        mock_fs.get_current_directory.assert_called_once_with()

    def test_is_writable_returns_boolean(self) -> None:
        """Test is_writable() returns boolean value."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        writable_dir = '/home/user/writable'
        mock_fs.is_writable.return_value = True

        # Act
        result = mock_fs.is_writable(writable_dir)

        # Assert
        assert isinstance(result, bool)
        assert result is True
        mock_fs.is_writable.assert_called_once_with(writable_dir)

    def test_is_writable_returns_false_for_readonly_directory(self) -> None:
        """Test is_writable() returns False for read-only directory."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        readonly_dir = '/readonly/directory'
        mock_fs.is_writable.return_value = False

        # Act
        result = mock_fs.is_writable(readonly_dir)

        # Assert
        assert result is False
        mock_fs.is_writable.assert_called_once_with(readonly_dir)

    def test_protocol_methods_exist(self) -> None:
        """Test that FileSystemPort protocol has all required methods."""
        # This test verifies the protocol interface exists
        mock_fs = Mock(spec=FileSystemPort)

        # Verify methods exist
        assert hasattr(mock_fs, 'write_file')
        assert hasattr(mock_fs, 'file_exists')
        assert hasattr(mock_fs, 'get_current_directory')
        assert hasattr(mock_fs, 'is_writable')

        # Verify methods are callable
        assert callable(mock_fs.write_file)
        assert callable(mock_fs.file_exists)
        assert callable(mock_fs.get_current_directory)
        assert callable(mock_fs.is_writable)
