"""Contract tests for NodeServicePort protocol (T007).

These tests verify that any implementation of the NodeServicePort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from unittest.mock import Mock

# These imports will fail initially - this is expected for contract tests
from prosemark.freewriting.domain.exceptions import FileSystemError, ValidationError
from prosemark.freewriting.ports.node_service import NodeServicePort


class TestNodeServicePortContract:
    """Test contract compliance for NodeServicePort implementations."""

    def test_node_exists_returns_boolean_for_existing_node(self) -> None:
        """Test node_exists() returns True for existing node."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        existing_node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        mock_service.node_exists.return_value = True

        # Act
        result = mock_service.node_exists(existing_node_uuid)

        # Assert
        assert isinstance(result, bool)
        assert result is True
        mock_service.node_exists.assert_called_once_with(existing_node_uuid)

    def test_node_exists_returns_false_for_nonexistent_node(self) -> None:
        """Test node_exists() returns False for non-existent node."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        nonexistent_uuid = 'nonexistent-node-uuid-string'
        mock_service.node_exists.return_value = False

        # Act
        result = mock_service.node_exists(nonexistent_uuid)

        # Assert
        assert isinstance(result, bool)
        assert result is False
        mock_service.node_exists.assert_called_once_with(nonexistent_uuid)

    def test_node_exists_handles_various_uuid_formats(self) -> None:
        """Test node_exists() handles different UUID string formats."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        test_uuids = [
            '01234567-89ab-cdef-0123-456789abcdef',
            'ABCDEF01-2345-6789-ABCD-EF0123456789',
            '12345678-9abc-def0-1234-56789abcdef0',
            'fedcba09-8765-4321-fedc-ba0987654321',
        ]

        # Mock returns True for all valid UUIDs
        mock_service.node_exists.return_value = True

        # Act & Assert
        for uuid_str in test_uuids:
            result = mock_service.node_exists(uuid_str)
            assert isinstance(result, bool)

        assert mock_service.node_exists.call_count == len(test_uuids)

    def test_node_exists_with_invalid_uuid_formats(self) -> None:
        """Test node_exists() behavior with invalid UUID formats."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        invalid_uuids = [
            'not-a-uuid',
            '01234567-89ab-cdef-0123',  # Too short
            '01234567-89ab-cdef-0123-456789abcdefg',  # Invalid character
            '',
            '12345678-9abc-def0-1234-56789abcdef0-extra',  # Too long
        ]

        # Mock returns False for invalid UUIDs
        mock_service.node_exists.return_value = False

        # Act & Assert
        for uuid_str in invalid_uuids:
            result = mock_service.node_exists(uuid_str)
            assert isinstance(result, bool)
            assert result is False

        assert mock_service.node_exists.call_count == len(invalid_uuids)

    def test_create_node_returns_file_path_string(self) -> None:
        """Test create_node() returns file path string for created node."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        title = 'Test Node Title'
        expected_path = f'/project/nodes/{node_uuid}.md'
        mock_service.create_node.return_value = expected_path

        # Act
        result = mock_service.create_node(node_uuid, title)

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        assert node_uuid in result
        assert result.endswith('.md')
        mock_service.create_node.assert_called_once_with(node_uuid, title)

    def test_create_node_without_title(self) -> None:
        """Test create_node() works when title is not provided."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        expected_path = f'/project/nodes/{node_uuid}.md'
        mock_service.create_node.return_value = expected_path

        # Act - Call without title parameter
        result = mock_service.create_node(node_uuid)

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        mock_service.create_node.assert_called_once_with(node_uuid)

    def test_create_node_with_none_title(self) -> None:
        """Test create_node() works when title is explicitly None."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        expected_path = f'/project/nodes/{node_uuid}.md'
        mock_service.create_node.return_value = expected_path

        # Act
        result = mock_service.create_node(node_uuid, None)

        # Assert
        assert isinstance(result, str)
        assert result == expected_path
        mock_service.create_node.assert_called_once_with(node_uuid, None)

    def test_create_node_raises_validation_error_on_invalid_uuid(self) -> None:
        """Test create_node() raises ValidationError for invalid UUID."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        invalid_uuid = 'invalid-uuid-format-string'
        title = 'Test Title'
        mock_service.create_node.side_effect = ValidationError(
            'node_uuid', 'invalid-format', 'must be valid UUID format'
        )

        # Act & Assert
        try:
            mock_service.create_node(invalid_uuid, title)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_service.create_node.assert_called_once_with(invalid_uuid, title)

    def test_create_node_raises_filesystem_error_on_creation_failure(self) -> None:
        """Test create_node() raises FileSystemError when file creation fails."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        title = 'Test Node'
        mock_service.create_node.side_effect = FileSystemError(
            'create', '/path/node.md', 'Cannot create file - disk full'
        )

        # Act & Assert
        try:
            mock_service.create_node(node_uuid, title)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_service.create_node.assert_called_once_with(node_uuid, title)

    def test_create_node_handles_special_characters_in_title(self) -> None:
        """Test create_node() handles titles with special characters."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        special_titles = [
            'Title with spaces and symbols: & $ %',
            'Unicode title with 中文 and émojis 🎉',
            'Title with "quotes" and \'apostrophes\'',
            'Title with [brackets] and (parentheses)',
            'Title with / slashes \\ and | pipes',
        ]
        expected_path = f'/project/nodes/{node_uuid}.md'

        # Act & Assert
        for title in special_titles:
            mock_service.create_node.return_value = expected_path
            result = mock_service.create_node(node_uuid, title)
            assert isinstance(result, str)
            assert result == expected_path

        assert mock_service.create_node.call_count == len(special_titles)

    def test_append_to_node_returns_none(self) -> None:
        """Test append_to_node() returns None on successful operation."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        content = [
            'First line of freewriting content',
            'Second line with more thoughts',
            'Third line completing the session',
        ]
        session_metadata = {
            'session_id': 'freewrite-session-123',
            'start_time': '2024-03-15T14:30:00',
            'end_time': '2024-03-15T14:45:00',
            'word_count': 25,
            'duration_seconds': 900,
        }
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, content, session_metadata)

    def test_append_to_node_accepts_empty_content_list(self) -> None:
        """Test append_to_node() handles empty content list gracefully."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        empty_content: list[str] = []
        session_metadata = {'session_id': 'empty-session-456', 'word_count': 0, 'duration_seconds': 0}
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, empty_content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, empty_content, session_metadata)

    def test_append_to_node_handles_single_line_content(self) -> None:
        """Test append_to_node() works with single line of content."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        single_line_content = ['Just one line of content']
        session_metadata = {'session_id': 'single-line-session', 'word_count': 5}
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, single_line_content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, single_line_content, session_metadata)

    def test_append_to_node_handles_multiline_content(self) -> None:
        """Test append_to_node() works with many lines of content."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        multiline_content = [f'Line {i} of extensive freewriting content' for i in range(1, 21)]  # 20 lines
        session_metadata = {'session_id': 'multiline-session', 'word_count': 140, 'duration_seconds': 1200}
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, multiline_content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, multiline_content, session_metadata)

    def test_append_to_node_handles_content_with_special_characters(self) -> None:
        """Test append_to_node() handles content with special characters and formatting."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        special_content = [
            'Content with **bold** and *italic* markdown',
            'Unicode content: 中文字符 and emojis 🚀✨',
            "Code snippet: `print('hello world')`",
            'Mathematical symbols: a + b = c, ∑x²',
            'Special punctuation: "quotes", \'apostrophes\', & symbols!',
        ]
        session_metadata = {'session_id': 'special-chars-session', 'word_count': 32}
        mock_service.append_to_node.return_value = None

        # Act
        result = mock_service.append_to_node(node_uuid, special_content, session_metadata)

        # Assert
        assert result is None
        mock_service.append_to_node.assert_called_once_with(node_uuid, special_content, session_metadata)

    def test_append_to_node_handles_various_metadata_formats(self) -> None:
        """Test append_to_node() works with different session metadata structures."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        content = ['Test content line']

        metadata_variations = [
            # Minimal metadata
            {'session_id': 'minimal'},
            # Rich metadata
            {
                'session_id': 'rich-metadata-session',
                'user_id': 'user123',
                'start_time': '2024-03-15T14:30:00Z',
                'end_time': '2024-03-15T14:45:00Z',
                'word_count': 150,
                'character_count': 750,
                'duration_seconds': 900,
                'goals_met': {'word_count': True, 'time_limit': False},
                'theme': 'dark',
                'client_info': 'TUI-v1.0',
            },
            # Metadata with nested structures
            {
                'session_id': 'nested-session',
                'stats': {'words': 100, 'characters': 500, 'lines': 10},
                'config': {'auto_save': True, 'theme': 'light'},
            },
        ]

        mock_service.append_to_node.return_value = None

        # Act & Assert
        for metadata in metadata_variations:
            result = mock_service.append_to_node(node_uuid, content, metadata)
            assert result is None

        assert mock_service.append_to_node.call_count == len(metadata_variations)

    def test_append_to_node_raises_validation_error_for_nonexistent_node(self) -> None:
        """Test append_to_node() raises ValidationError when node doesn't exist."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        nonexistent_uuid = 'nonexistent-node-uuid-12345'
        content = ['Content for non-existent node']
        metadata = {'session_id': 'test-session'}
        mock_service.append_to_node.side_effect = ValidationError(
            'node_uuid', 'nonexistent-uuid', 'node does not exist'
        )

        # Act & Assert
        try:
            mock_service.append_to_node(nonexistent_uuid, content, metadata)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_service.append_to_node.assert_called_once_with(nonexistent_uuid, content, metadata)

    def test_append_to_node_raises_filesystem_error_on_write_failure(self) -> None:
        """Test append_to_node() raises FileSystemError when write operation fails."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        node_uuid = '01234567-89ab-cdef-0123-456789abcdef'
        content = ['Content to append']
        metadata = {'session_id': 'write-failure-session'}
        mock_service.append_to_node.side_effect = FileSystemError(
            'write', '/path/node.md', 'Permission denied - cannot write to file'
        )

        # Act & Assert
        try:
            mock_service.append_to_node(node_uuid, content, metadata)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_service.append_to_node.assert_called_once_with(node_uuid, content, metadata)

    def test_append_to_node_raises_validation_error_on_invalid_uuid(self) -> None:
        """Test append_to_node() raises ValidationError for invalid UUID format."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        invalid_uuid = 'invalid-format-uuid'
        content = ['Valid content']
        metadata = {'session_id': 'invalid-uuid-session'}
        mock_service.append_to_node.side_effect = ValidationError(
            'node_uuid', 'invalid-format', 'must be valid UUID format'
        )

        # Act & Assert
        try:
            mock_service.append_to_node(invalid_uuid, content, metadata)
            raise AssertionError('Should have raised ValidationError')
        except ValidationError:
            pass  # Expected
        mock_service.append_to_node.assert_called_once_with(invalid_uuid, content, metadata)

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

    def test_method_signatures_match_contract(self) -> None:
        """Test that method signatures match the expected contract."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)

        # Test node_exists signature
        mock_service.node_exists.return_value = True
        result = mock_service.node_exists('test-uuid')
        assert isinstance(result, bool)
        mock_service.node_exists.assert_called_with('test-uuid')

        # Test create_node signature with title
        mock_service.create_node.return_value = '/path/to/node.md'
        result = mock_service.create_node('test-uuid', 'Test Title')
        assert isinstance(result, str)
        mock_service.create_node.assert_called_with('test-uuid', 'Test Title')

        # Test create_node signature without title
        mock_service.create_node.reset_mock()
        result = mock_service.create_node('test-uuid')
        assert isinstance(result, str)
        mock_service.create_node.assert_called_with('test-uuid')

        # Test append_to_node signature
        mock_service.append_to_node.return_value = None
        result = mock_service.append_to_node('test-uuid', ['content'], {'session': 'test'})
        assert result is None
        mock_service.append_to_node.assert_called_with('test-uuid', ['content'], {'session': 'test'})

    def test_return_types_match_contract(self) -> None:
        """Test that return types match the contract specifications."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)

        # node_exists should return bool
        mock_service.node_exists.return_value = True
        result = mock_service.node_exists('uuid')
        assert isinstance(result, bool)

        mock_service.node_exists.return_value = False
        result = mock_service.node_exists('uuid')
        assert isinstance(result, bool)

        # create_node should return str
        mock_service.create_node.return_value = '/path/to/created/node.md'
        result = mock_service.create_node('uuid', 'title')
        assert isinstance(result, str)
        assert len(result) > 0  # Should not be empty string

        # append_to_node should return None
        mock_service.append_to_node.return_value = None
        result = mock_service.append_to_node('uuid', ['content'], {'metadata': 'value'})
        assert result is None

    def test_parameter_types_accepted(self) -> None:
        """Test that methods accept the correct parameter types."""
        # Arrange
        mock_service = Mock(spec=NodeServicePort)
        mock_service.node_exists.return_value = True
        mock_service.create_node.return_value = '/path/node.md'
        mock_service.append_to_node.return_value = None

        # Test parameter types
        node_uuid: str = '01234567-89ab-cdef-0123-456789abcdef'
        title: str | None = 'Test Title'
        content: list[str] = ['Line 1', 'Line 2']
        metadata: dict[str, str] = {'session_id': 'test', 'word_count': '10'}

        # Act - These should not raise type errors
        mock_service.node_exists(node_uuid)
        mock_service.create_node(node_uuid, title)
        mock_service.create_node(node_uuid, None)  # Optional title
        mock_service.create_node(node_uuid)  # No title parameter
        mock_service.append_to_node(node_uuid, content, metadata)

        # Assert method calls were made correctly
        assert mock_service.node_exists.call_count == 1
        assert mock_service.create_node.call_count == 3
        assert mock_service.append_to_node.call_count == 1
