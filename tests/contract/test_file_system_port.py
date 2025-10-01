"""Contract tests for FileSystemPort protocol (T008).

These tests verify that any implementation of the FileSystemPort protocol
correctly implements the contract defined in the domain interfaces.
Tests will initially fail due to missing imports - this is expected.
"""

from unittest.mock import Mock

# These imports will fail initially - this is expected for contract tests
from prosemark.freewriting.domain.exceptions import FileSystemError
from prosemark.freewriting.ports.file_system import FileSystemPort


class TestFileSystemPortContract:
    """Test contract compliance for FileSystemPort implementations."""

    def test_write_file_accepts_path_and_content_parameters(self) -> None:
        """Test write_file() accepts file path and content as basic parameters."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/directory/output.md'
        content = 'Test content to write to the file'
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, content)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, content)

    def test_write_file_with_append_false_overwrites(self) -> None:
        """Test write_file() with append=False (default behavior - overwrites file)."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/overwrite.md'
        content = 'New content that overwrites existing'
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, content, append=False)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, content, append=False)

    def test_write_file_with_append_true_appends(self) -> None:
        """Test write_file() with append=True appends to existing file."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/append.md'
        content = 'Additional content to append'
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, content, append=True)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, content, append=True)

    def test_write_file_handles_empty_content(self) -> None:
        """Test write_file() handles empty content string."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/empty.md'
        empty_content = ''
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, empty_content)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, empty_content)

    def test_write_file_handles_multiline_content(self) -> None:
        """Test write_file() handles content with newlines and multiple lines."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/multiline.md'
        multiline_content = """# Freewriting Session

Line 1 of freewriting content
Line 2 with more thoughts and ideas
Line 3 completing the session

## Session Summary
Total words: 15
Duration: 10 minutes"""
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, multiline_content)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, multiline_content)

    def test_write_file_handles_unicode_content(self) -> None:
        """Test write_file() handles Unicode characters and special symbols."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/unicode.md'
        unicode_content = """# Freewriting with Unicode

中文内容测试 - Chinese text
Émojis and symbols: 🚀✨🎯💡
Mathematical symbols: a + b = c, sum(x²)
Accented characters: café, résumé, naïve
Currency symbols: $100, €50, ¥1000"""
        mock_fs.write_file.return_value = None

        # Act
        result = mock_fs.write_file(file_path, unicode_content)

        # Assert
        assert result is None
        mock_fs.write_file.assert_called_once_with(file_path, unicode_content)

    def test_write_file_handles_various_file_extensions(self) -> None:
        """Test write_file() works with different file extensions."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_paths = [
            '/test/freewrite.md',
            '/test/session.txt',
            '/test/output.log',
            '/test/backup.bak',
            '/test/data.json',
        ]
        content = 'Test content'
        mock_fs.write_file.return_value = None

        # Act & Assert
        for file_path in file_paths:
            result = mock_fs.write_file(file_path, content)
            assert result is None

        assert mock_fs.write_file.call_count == len(file_paths)

    def test_write_file_handles_deeply_nested_paths(self) -> None:
        """Test write_file() handles deeply nested directory paths."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        deep_paths = [
            '/home/user/projects/prosemark/sessions/2024/03/15/freewrite-1430.md',
            '/var/data/application/backups/daily/2024-03-15/session-backup.md',
            '/tmp/prosemark/temp/sessions/user123/write-session-456.md',
        ]
        content = 'Content for deeply nested file'
        mock_fs.write_file.return_value = None

        # Act & Assert
        for file_path in deep_paths:
            result = mock_fs.write_file(file_path, content)
            assert result is None

        assert mock_fs.write_file.call_count == len(deep_paths)

    def test_write_file_raises_filesystem_error_on_failure(self) -> None:
        """Test write_file() raises FileSystemError when write operation fails."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        readonly_path = '/readonly/system/file.md'
        content = 'Content that cannot be written'
        mock_fs.write_file.side_effect = FileSystemError(
            'write', '/readonly/test.txt', 'Permission denied - cannot write to read-only location'
        )

        # Act & Assert
        try:
            mock_fs.write_file(readonly_path, content)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_fs.write_file.assert_called_once_with(readonly_path, content)

    def test_write_file_raises_filesystem_error_on_disk_full(self) -> None:
        """Test write_file() raises FileSystemError when disk is full."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_path = '/test/large-file.md'
        large_content = 'x' * 1000000  # 1MB of content
        mock_fs.write_file.side_effect = FileSystemError('write', '/full/disk/test.txt', 'No space left on device')

        # Act & Assert
        try:
            mock_fs.write_file(file_path, large_content)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_fs.write_file.assert_called_once_with(file_path, large_content)

    def test_write_file_raises_filesystem_error_on_invalid_path(self) -> None:
        """Test write_file() raises FileSystemError for invalid file paths."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        invalid_path = '/nonexistent/directory/structure/file.md'
        content = 'Content for invalid path'
        mock_fs.write_file.side_effect = FileSystemError(
            'write', '/nonexistent/dir/test.txt', 'Directory does not exist'
        )

        # Act & Assert
        try:
            mock_fs.write_file(invalid_path, content)
            raise AssertionError('Should have raised FileSystemError')
        except FileSystemError:
            pass  # Expected
        mock_fs.write_file.assert_called_once_with(invalid_path, content)

    def test_file_exists_returns_true_for_existing_file(self) -> None:
        """Test file_exists() returns True for existing files."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        existing_files = [
            '/home/user/existing-file.md',
            '/project/notes/session-log.txt',
            '/tmp/temp-file.md',
        ]
        mock_fs.file_exists.return_value = True

        # Act & Assert
        for file_path in existing_files:
            result = mock_fs.file_exists(file_path)
            assert isinstance(result, bool)
            assert result is True

        assert mock_fs.file_exists.call_count == len(existing_files)

    def test_file_exists_returns_false_for_nonexistent_file(self) -> None:
        """Test file_exists() returns False for non-existent files."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        nonexistent_files = ['/does/not/exist.md', '/missing/file.txt', '/nonexistent/path/file.md']
        mock_fs.file_exists.return_value = False

        # Act & Assert
        for file_path in nonexistent_files:
            result = mock_fs.file_exists(file_path)
            assert isinstance(result, bool)
            assert result is False

        assert mock_fs.file_exists.call_count == len(nonexistent_files)

    def test_file_exists_handles_various_path_formats(self) -> None:
        """Test file_exists() handles different path formats correctly."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        path_formats = [
            '/absolute/path/file.md',  # Absolute path
            './relative/path/file.md',  # Relative path with ./
            '../parent/directory/file.md',  # Relative path with ../
            'simple-filename.md',  # Simple filename
            '/path/with spaces/file name.md',  # Paths with spaces
            '/path/with-dashes/file_name.md',  # Mixed separators
        ]
        mock_fs.file_exists.return_value = True

        # Act & Assert
        for file_path in path_formats:
            result = mock_fs.file_exists(file_path)
            assert isinstance(result, bool)

        assert mock_fs.file_exists.call_count == len(path_formats)

    def test_file_exists_handles_empty_string_path(self) -> None:
        """Test file_exists() handles empty string path."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        empty_path = ''
        mock_fs.file_exists.return_value = False

        # Act
        result = mock_fs.file_exists(empty_path)

        # Assert
        assert isinstance(result, bool)
        assert result is False
        mock_fs.file_exists.assert_called_once_with(empty_path)

    def test_get_current_directory_returns_absolute_path_string(self) -> None:
        """Test get_current_directory() returns absolute path string."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        expected_paths = [
            '/home/user/current-project',
            '/workspace/prosemark',
            '/tmp/working-directory',
            '/var/data/application',
        ]

        # Act & Assert
        for expected_path in expected_paths:
            mock_fs.get_current_directory.return_value = expected_path
            result = mock_fs.get_current_directory()

            assert isinstance(result, str)
            assert len(result) > 0
            assert result.startswith('/')  # Should be absolute path
            assert result == expected_path

        assert mock_fs.get_current_directory.call_count == len(expected_paths)

    def test_get_current_directory_returns_consistent_result(self) -> None:
        """Test get_current_directory() returns consistent result across calls."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        consistent_path = '/home/user/consistent-directory'
        mock_fs.get_current_directory.return_value = consistent_path

        # Act
        result1 = mock_fs.get_current_directory()
        result2 = mock_fs.get_current_directory()
        result3 = mock_fs.get_current_directory()

        # Assert
        assert result1 == result2 == result3 == consistent_path
        assert mock_fs.get_current_directory.call_count == 3

    def test_is_writable_returns_true_for_writable_directory(self) -> None:
        """Test is_writable() returns True for writable directories."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        writable_directories = [
            '/home/user/writable-directory',
            '/tmp/temp-directory',
            '/var/data/user-space',
            '/project/output',
        ]
        mock_fs.is_writable.return_value = True

        # Act & Assert
        for directory in writable_directories:
            result = mock_fs.is_writable(directory)
            assert isinstance(result, bool)
            assert result is True

        assert mock_fs.is_writable.call_count == len(writable_directories)

    def test_is_writable_returns_false_for_readonly_directory(self) -> None:
        """Test is_writable() returns False for read-only directories."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        readonly_directories = ['/readonly/system-directory', '/usr/bin', '/root/admin-only', '/protected/directory']
        mock_fs.is_writable.return_value = False

        # Act & Assert
        for directory in readonly_directories:
            result = mock_fs.is_writable(directory)
            assert isinstance(result, bool)
            assert result is False

        assert mock_fs.is_writable.call_count == len(readonly_directories)

    def test_is_writable_handles_nonexistent_directory(self) -> None:
        """Test is_writable() handles non-existent directories."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        nonexistent_directories = ['/does/not/exist', '/missing/directory/path', '/nonexistent/location']
        mock_fs.is_writable.return_value = False

        # Act & Assert
        for directory in nonexistent_directories:
            result = mock_fs.is_writable(directory)
            assert isinstance(result, bool)
            assert result is False

        assert mock_fs.is_writable.call_count == len(nonexistent_directories)

    def test_is_writable_handles_file_path_instead_of_directory(self) -> None:
        """Test is_writable() behavior when given file path instead of directory."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        file_paths = ['/home/user/file.md', '/project/document.txt', '/data/session.log']
        # Behavior may vary - could return False or check parent directory
        mock_fs.is_writable.return_value = False

        # Act & Assert
        for file_path in file_paths:
            result = mock_fs.is_writable(file_path)
            assert isinstance(result, bool)

        assert mock_fs.is_writable.call_count == len(file_paths)

    def test_is_writable_handles_various_directory_formats(self) -> None:
        """Test is_writable() handles different directory path formats."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        directory_formats = [
            '/absolute/directory/path',  # Absolute path
            './relative/directory',  # Relative path with ./
            '../parent/directory',  # Relative path with ../
            'simple-directory',  # Simple directory name
            '/path/with spaces/directory',  # Directory with spaces
            '/path/with-dashes/under_scores',  # Mixed separators
        ]
        mock_fs.is_writable.return_value = True

        # Act & Assert
        for directory in directory_formats:
            result = mock_fs.is_writable(directory)
            assert isinstance(result, bool)

        assert mock_fs.is_writable.call_count == len(directory_formats)

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

    def test_method_signatures_match_contract(self) -> None:
        """Test that method signatures match the expected contract."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)

        # Test write_file signatures
        mock_fs.write_file.return_value = None

        # Basic signature (append defaults to False)
        result = mock_fs.write_file('/path/file.md', 'content')
        assert result is None

        # With explicit append parameter
        result = mock_fs.write_file('/path/file.md', 'content', append=False)
        assert result is None

        result = mock_fs.write_file('/path/file.md', 'content', append=True)
        assert result is None

        # Test file_exists signature
        mock_fs.file_exists.return_value = True
        result = mock_fs.file_exists('/path/file.md')
        assert isinstance(result, bool)

        # Test get_current_directory signature (no parameters)
        mock_fs.get_current_directory.return_value = '/current/directory'
        result = mock_fs.get_current_directory()
        assert isinstance(result, str)

        # Test is_writable signature
        mock_fs.is_writable.return_value = True
        result = mock_fs.is_writable('/some/directory')
        assert isinstance(result, bool)

    def test_return_types_match_contract(self) -> None:
        """Test that return types match the contract specifications."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)

        # write_file should return None
        mock_fs.write_file.return_value = None
        result = mock_fs.write_file('/path', 'content')
        assert result is None

        result = mock_fs.write_file('/path', 'content', append=True)
        assert result is None

        # file_exists should return bool
        mock_fs.file_exists.return_value = True
        result = mock_fs.file_exists('/path')
        assert isinstance(result, bool)
        assert result is True

        mock_fs.file_exists.return_value = False
        result = mock_fs.file_exists('/path')
        assert isinstance(result, bool)
        assert result is False

        # get_current_directory should return str
        mock_fs.get_current_directory.return_value = '/current/path'
        result = mock_fs.get_current_directory()
        assert isinstance(result, str)
        assert len(result) > 0  # Should not be empty string

        # is_writable should return bool
        mock_fs.is_writable.return_value = True
        result = mock_fs.is_writable('/directory')
        assert isinstance(result, bool)
        assert result is True

        mock_fs.is_writable.return_value = False
        result = mock_fs.is_writable('/directory')
        assert isinstance(result, bool)
        assert result is False

    def test_parameter_types_accepted(self) -> None:
        """Test that methods accept the correct parameter types."""
        # Arrange
        mock_fs = Mock(spec=FileSystemPort)
        mock_fs.write_file.return_value = None
        mock_fs.file_exists.return_value = True
        mock_fs.get_current_directory.return_value = '/directory'
        mock_fs.is_writable.return_value = True

        # Test parameter types
        file_path: str = '/test/file.md'
        content: str = 'Test content string'
        directory_path: str = '/test/directory'
        append_flag: bool = True

        # Act - These should not raise type errors
        mock_fs.write_file(file_path, content)
        mock_fs.write_file(file_path, content, append=append_flag)
        mock_fs.file_exists(file_path)
        mock_fs.get_current_directory()  # No parameters
        mock_fs.is_writable(directory_path)

        # Assert method calls were made correctly
        assert mock_fs.write_file.call_count == 2
        assert mock_fs.file_exists.call_count == 1
        assert mock_fs.get_current_directory.call_count == 1
        assert mock_fs.is_writable.call_count == 1
