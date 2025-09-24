"""Tests for Freewrite Service adapter implementation.

These tests cover the FreewriteServiceAdapter class which orchestrates
all freewriting operations by coordinating between file system, node service,
and domain models.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prosemark.freewriting.adapters.freewrite_service_adapter import FreewriteServiceAdapter
from prosemark.freewriting.adapters.node_service_adapter import NodeServiceAdapter
from prosemark.freewriting.domain.exceptions import FileSystemError, ValidationError
from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig, SessionState
from prosemark.freewriting.ports.file_system import FileSystemPort
from prosemark.freewriting.ports.node_service import NodeServicePort


class TestFreewriteServiceAdapter:
    """Test the Freewrite Service adapter implementation."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initializes with required dependencies."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_node_service = Mock(spec=NodeServicePort)

        # Act
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        # Assert
        assert adapter.file_system == mock_file_system
        assert adapter.node_service == mock_node_service

    def test_create_session_daily_file_success(self) -> None:
        """Test creating session for daily file."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.join_paths.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.get_absolute_path.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.write_file.return_value = None
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(
            target_node=None, title='Test Session', word_count_goal=1000, time_limit=3600, current_directory='/test'
        )

        # Act
        with patch.object(Path, 'exists', return_value=True):
            session = adapter.create_session(config)

        # Assert
        assert session.target_node is None
        assert session.title == 'Test Session'
        assert session.word_count_goal == 1000
        assert session.time_limit == 3600
        assert session.current_word_count == 0
        assert session.elapsed_time == 0
        assert session.state == SessionState.ACTIVE
        assert session.output_file_path == '/test/2024-01-15-1430.md'

        # Verify file system calls
        mock_file_system.is_writable.assert_called_with('/test')
        mock_file_system.write_file.assert_called_once()

    def test_create_session_node_file_success(self) -> None:
        """Test creating session for node file."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.get_node_path.return_value = '/test/node-123.md'
        mock_node_service.node_exists.return_value = True

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef', title='Node Session', current_directory='/test'
        )

        # Act
        session = adapter.create_session(config)

        # Assert
        assert session.target_node == '01234567-89ab-cdef-0123-456789abcdef'
        assert session.title == 'Node Session'
        assert session.state == SessionState.ACTIVE
        assert session.output_file_path == '/test/node-123.md'

        # Verify calls
        mock_node_service.get_node_path.assert_called_with('01234567-89ab-cdef-0123-456789abcdef')
        mock_node_service.node_exists.assert_called_with('01234567-89ab-cdef-0123-456789abcdef')

    def test_create_session_invalid_target_node(self) -> None:
        """Test create_session raises ValidationError for invalid node UUID."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_node_service = Mock(spec=NodeServicePort)

        FreewriteServiceAdapter(mock_file_system, mock_node_service)

        # The SessionConfig itself will validate and raise ValueError for invalid UUID
        # Act & Assert
        with pytest.raises(ValueError, match='Invalid target_node UUID format'):
            SessionConfig(target_node='invalid-uuid', current_directory='/test')

    def test_validate_session_config_invalid_target_node_service_level(self) -> None:
        """Test _validate_session_config catches UUID validation at service level."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_node_service = Mock(spec=NodeServicePort)

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        # Create a config where the UUID passes domain validation but fails service validation
        # This tests the specific validation logic in lines 203-204
        config = SessionConfig(
            target_node='12345678-1234-1234-1234-123456789abc',  # Valid UUID format
            current_directory='/test',
        )

        # Mock NodeServiceAdapter.validate_node_uuid to return False
        with (
            patch.object(NodeServiceAdapter, 'validate_node_uuid', return_value=False),
            pytest.raises(ValidationError, match='Invalid UUID format'),
        ):
            adapter._validate_session_config(config)

    def test_create_session_non_writable_directory(self) -> None:
        """Test create_session raises ValidationError for non-writable directory."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = False
        mock_node_service = Mock(spec=NodeServicePort)

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(current_directory='/readonly')

        # Act & Assert
        with pytest.raises(ValidationError, match='Directory is not writable'):
            adapter.create_session(config)

    def test_create_session_node_creation_required(self) -> None:
        """Test creating session when node needs to be created."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.get_node_path.return_value = '/test/new-node.md'
        mock_node_service.node_exists.return_value = False
        mock_node_service.create_node.return_value = '/test/new-node.md'

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef', title='New Node', current_directory='/test'
        )

        # Act
        session = adapter.create_session(config)

        # Assert
        assert session.target_node == '01234567-89ab-cdef-0123-456789abcdef'
        mock_node_service.create_node.assert_called_with('01234567-89ab-cdef-0123-456789abcdef', 'New Node')

    def test_create_session_node_creation_fails(self) -> None:
        """Test create_session handles node creation failure."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True

        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.get_node_path.return_value = '/test/new-node.md'
        mock_node_service.node_exists.return_value = False
        mock_node_service.create_node.side_effect = Exception('Node creation failed')

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(target_node='01234567-89ab-cdef-0123-456789abcdef', current_directory='/test')

        # Act & Assert
        with pytest.raises(FileSystemError, match='Node creation failed'):
            adapter.create_session(config)

    def test_create_session_file_initialization_fails(self) -> None:
        """Test create_session handles file initialization failure."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.join_paths.return_value = '/test/file.md'
        mock_file_system.get_absolute_path.return_value = '/test/file.md'
        mock_file_system.write_file.return_value = None
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(current_directory='/test')

        # Act & Assert
        with patch.object(Path, 'exists', return_value=False), pytest.raises(FileSystemError, match='File not created'):
            adapter.create_session(config)

    def test_create_session_daily_file_parent_not_writable(self) -> None:
        """Test create_session handles non-writable parent directory for daily file."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.side_effect = lambda path: path != '/readonly'
        mock_file_system.join_paths.return_value = '/readonly/file.md'
        mock_file_system.get_absolute_path.return_value = '/readonly/file.md'

        mock_node_service = Mock(spec=NodeServicePort)
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(current_directory='/test')

        # Act & Assert
        with pytest.raises(FileSystemError, match='Parent directory is not writable'):
            adapter.create_session(config)

    def test_append_content_daily_file(self) -> None:
        """Test appending content to daily file."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.write_file.return_value = None
        mock_node_service = Mock(spec=NodeServicePort)

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=5,
            elapsed_time=0,
            output_file_path='/test/file.md',
            content_lines=['Previous line'],
        )

        # Act
        updated_session = adapter.append_content(session, 'New content line')

        # Assert
        assert updated_session.content_lines == ['Previous line', 'New content line']
        assert updated_session.current_word_count == 8  # 5 + 3 new words
        mock_file_system.write_file.assert_called_with('/test/file.md', 'New content line\n', append=True)

    def test_append_content_node_file(self) -> None:
        """Test appending content to node file."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.append_to_node.return_value = None

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node='01234567-89ab-cdef-0123-456789abcdef',
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/node.md',
        )

        # Act
        updated_session = adapter.append_content(session, 'Node content')

        # Assert
        assert updated_session.content_lines == ['Node content']
        assert updated_session.current_word_count == 2
        mock_node_service.append_to_node.assert_called_once()
        # Check that session metadata was included
        call_args = mock_node_service.append_to_node.call_args
        assert call_args[0][0] == '01234567-89ab-cdef-0123-456789abcdef'  # node UUID
        assert call_args[0][1] == ['Node content']  # content
        assert 'timestamp' in call_args[0][2]  # metadata
        assert 'word_count' in call_args[0][2]
        assert 'session_id' in call_args[0][2]

    def test_append_content_empty_content(self) -> None:
        """Test appending empty content is allowed."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.write_file.return_value = None
        mock_node_service = Mock(spec=NodeServicePort)

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/file.md',
        )

        # Act
        updated_session = adapter.append_content(session, '')

        # Assert
        assert updated_session.content_lines == ['']
        assert updated_session.current_word_count == 0
        mock_file_system.write_file.assert_called_with('/test/file.md', '\n', append=True)

    def test_append_content_file_system_error(self) -> None:
        """Test append_content handles file system errors."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.write_file.side_effect = OSError('Write failed')
        mock_node_service = Mock(spec=NodeServicePort)

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/file.md',
        )

        # Act & Assert
        with pytest.raises(FileSystemError, match='Write failed'):
            adapter.append_content(session, 'content')

    def test_append_content_node_missing_target(self) -> None:
        """Test append_content raises error when node append called without target node."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_node_service = Mock(spec=NodeServicePort)

        # Create a scenario where _append_to_node_file is called without target_node
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,  # No target node
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=0,
            elapsed_time=0,
            output_file_path='/test/file.md',
        )

        # Act & Assert - directly test the private method to cover line 335-337
        with pytest.raises(FileSystemError, match='No target node specified'):
            adapter._append_to_node_file(session, 'content')

    @staticmethod
    def test_validate_node_uuid_valid() -> None:
        """Test validate_node_uuid with valid UUID."""
        # Act
        result = FreewriteServiceAdapter.validate_node_uuid('01234567-89ab-cdef-0123-456789abcdef')

        # Assert
        assert result is True

    @staticmethod
    def test_validate_node_uuid_invalid() -> None:
        """Test validate_node_uuid with invalid UUID."""
        # Act & Assert
        assert FreewriteServiceAdapter.validate_node_uuid('invalid-uuid') is False
        assert FreewriteServiceAdapter.validate_node_uuid('') is False
        assert FreewriteServiceAdapter.validate_node_uuid('not-a-uuid') is False

    @staticmethod
    def test_create_daily_filename() -> None:
        """Test create_daily_filename generates correct format."""
        # Arrange
        timestamp = datetime(2024, 1, 15, 14, 30, 45, tzinfo=UTC)

        # Act
        filename = FreewriteServiceAdapter.create_daily_filename(timestamp)

        # Assert
        assert filename == '2024-01-15-1430.md'

    @staticmethod
    def test_get_session_stats_basic() -> None:
        """Test get_session_stats with basic session."""
        # Arrange
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=None,
            time_limit=None,
            current_word_count=50,
            elapsed_time=300,
            output_file_path='/test/file.md',
            content_lines=['Line 1', 'Line 2', 'Line 3'],
        )

        # Act
        stats = FreewriteServiceAdapter.get_session_stats(session)

        # Assert
        assert stats['word_count'] == 50
        assert stats['elapsed_time'] == 300
        assert stats['line_count'] == 3

    @staticmethod
    def test_get_session_stats_with_goals() -> None:
        """Test get_session_stats with word count and time goals."""
        # Arrange
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=100,
            time_limit=1800,  # 30 minutes
            current_word_count=75,
            elapsed_time=900,  # 15 minutes
            output_file_path='/test/file.md',
        )

        # Act
        stats = FreewriteServiceAdapter.get_session_stats(session)

        # Assert
        # Note: word_count and time_limit keys get overwritten by goal results (booleans)
        assert stats['word_count'] is False  # Goal not reached (75 < 100)
        assert stats['time_limit'] is False  # Goal not reached (900 < 1800)
        assert stats['elapsed_time'] == 900
        assert stats['word_progress_percent'] == 75.0
        assert stats['time_progress_percent'] == 50.0
        assert stats['time_remaining'] == 900

    @staticmethod
    def test_get_session_stats_goals_exceeded() -> None:
        """Test get_session_stats when goals are exceeded."""
        # Arrange
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=100,
            time_limit=1800,
            current_word_count=150,  # Exceeds goal
            elapsed_time=2000,  # Exceeds limit
            output_file_path='/test/file.md',
        )

        # Act
        stats = FreewriteServiceAdapter.get_session_stats(session)

        # Assert
        assert stats['word_progress_percent'] == 100.0  # Capped at 100%
        assert stats['time_progress_percent'] == 100.0  # Capped at 100%
        assert stats['time_remaining'] == 0  # No time remaining
        assert stats['word_count'] is True  # Goal reached
        assert stats['time_limit'] is True  # Goal reached

    @staticmethod
    def test_get_session_stats_goals_met_exactly() -> None:
        """Test get_session_stats when goals are met exactly."""
        # Arrange
        session = FreewriteSession(
            session_id='01234567-89ab-cdef-0123-456789abcdef',
            target_node=None,
            title=None,
            start_time=datetime.now(tz=UTC),
            word_count_goal=100,
            time_limit=1800,
            current_word_count=100,
            elapsed_time=1800,
            output_file_path='/test/file.md',
        )

        # Act
        stats = FreewriteServiceAdapter.get_session_stats(session)

        # Assert
        assert stats['word_progress_percent'] == 100.0
        assert stats['time_progress_percent'] == 100.0
        assert stats['time_remaining'] == 0
        assert stats['word_count'] is True
        assert stats['time_limit'] is True


class TestFreewriteServiceAdapterIntegration:
    """Integration tests for Freewrite Service adapter."""

    def test_complete_daily_workflow(self) -> None:
        """Test complete workflow for daily freewriting."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.join_paths.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.get_absolute_path.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.write_file.return_value = None
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(title='Daily Freewrite', word_count_goal=500, current_directory='/test')

        # Act - Create session
        with patch.object(Path, 'exists', return_value=True):
            session = adapter.create_session(config)

        # Act - Add content
        session = adapter.append_content(session, 'First line of content')
        session = adapter.append_content(session, 'Second line with more words')

        # Assert
        assert session.current_word_count == 9  # 4 + 5 words
        assert len(session.content_lines) == 2
        assert session.state == SessionState.ACTIVE

        # Verify file operations
        assert mock_file_system.write_file.call_count == 3  # Initial + 2 appends

    def test_complete_node_workflow(self) -> None:
        """Test complete workflow for node freewriting."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.file_exists.return_value = False  # No existing content
        mock_file_system.read_file.return_value = ''  # Empty file content

        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.get_node_path.return_value = '/test/node-123.md'
        mock_node_service.node_exists.return_value = True
        mock_node_service.append_to_node.return_value = None

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(
            target_node='01234567-89ab-cdef-0123-456789abcdef', title='Node Freewrite', current_directory='/test'
        )

        # Act - Create session
        session = adapter.create_session(config)

        # Act - Add content
        session = adapter.append_content(session, 'Node content line one')
        session = adapter.append_content(session, 'Node content line two')

        # Assert
        assert session.current_word_count == 8  # 4 + 4 words
        assert len(session.content_lines) == 2
        assert session.target_node == '01234567-89ab-cdef-0123-456789abcdef'

        # Verify node service operations
        assert mock_node_service.append_to_node.call_count == 2

    def test_load_existing_content_exception_handling(self) -> None:
        """Test exception handling when loading existing content fails."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.join_paths.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.get_absolute_path.return_value = '/test/2024-01-15-1430.md'
        mock_file_system.write_file.return_value = None
        mock_file_system.file_exists.return_value = True  # File exists
        mock_file_system.read_file.side_effect = OSError('Permission denied')  # File read fails

        mock_node_service = Mock(spec=NodeServicePort)
        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)

        config = SessionConfig(title='Daily Freewrite', current_directory='/test')

        # Act & Assert
        with (
            patch.object(Path, 'exists', return_value=False),
            pytest.raises(FileSystemError, match='File system operation failed: read_existing'),
        ):  # Force file creation path
            adapter.create_session(config)

    def test_filter_frontmatter_with_yaml_content(self) -> None:
        """Test filtering YAML frontmatter from content lines."""
        # Arrange
        content_lines = [
            '---',
            'title: Test Document',
            'author: Test Author',
            '---',
            '# Test Header',
            '',
            'This is content that should be kept.',
            'More content here.',
        ]

        # Act
        filtered_lines = FreewriteServiceAdapter._filter_frontmatter_and_header(content_lines)

        # Assert
        expected_lines = ['This is content that should be kept.', 'More content here.']
        assert filtered_lines == expected_lines

    def test_load_existing_content_node_target_no_filter(self) -> None:
        """Test loading existing content for node target (no frontmatter filtering)."""
        # Arrange
        mock_file_system = Mock(spec=FileSystemPort)
        mock_file_system.is_writable.return_value = True
        mock_file_system.file_exists.return_value = True
        mock_file_system.read_file.return_value = 'Line 1\nLine 2\n'

        mock_node_service = Mock(spec=NodeServicePort)
        mock_node_service.get_node_path.return_value = '/test/node-123.md'
        mock_node_service.node_exists.return_value = True

        adapter = FreewriteServiceAdapter(mock_file_system, mock_node_service)
        config = SessionConfig(target_node='01234567-89ab-cdef-0123-456789abcdef', current_directory='/test')

        # Act
        session = adapter.create_session(config)

        # Assert - For node targets, content should be loaded without filtering
        assert session.current_word_count == 4  # "Line 1" + "Line 2" = 4 words
        assert len(session.content_lines) == 2

    def test_filter_frontmatter_without_yaml_markers(self) -> None:
        """Test filtering when content has no YAML frontmatter markers."""
        # Arrange - Content without YAML frontmatter
        content_lines = ['# Test Header', '', 'This is content that should be kept.', 'More content here.']

        # Act
        filtered_lines = FreewriteServiceAdapter._filter_frontmatter_and_header(content_lines)

        # Assert - Without frontmatter, header is NOT skipped, only leading empty lines
        expected_lines = ['# Test Header', '', 'This is content that should be kept.', 'More content here.']
        assert filtered_lines == expected_lines

    def test_filter_frontmatter_multiple_yaml_markers(self) -> None:
        """Test filtering when there are multiple --- markers after frontmatter is closed."""
        # Arrange - Content with YAML frontmatter and additional --- markers
        content_lines = [
            '---',
            'title: Test Document',
            '---',
            '# Test Header',
            '---',  # This should NOT be treated as frontmatter start
            'Content with triple dashes',
            '---',  # This should also NOT be treated as frontmatter start
            'More content here.',
        ]

        # Act
        filtered_lines = FreewriteServiceAdapter._filter_frontmatter_and_header(content_lines)

        # Assert - After frontmatter is closed, subsequent --- should be kept as content
        expected_lines = ['---', 'Content with triple dashes', '---', 'More content here.']
        assert filtered_lines == expected_lines
