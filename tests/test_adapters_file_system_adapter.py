"""Tests for File System adapter implementation.

These tests cover the FileSystemAdapter class which provides concrete
implementation of file system operations for the freewriting feature.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from prosemark.freewriting.adapters.file_system_adapter import FileSystemAdapter
from prosemark.freewriting.domain.exceptions import FileSystemError


class TestFileSystemAdapter:
    """Test the File System adapter implementation."""

    def test_write_file_create_new_file(self) -> None:
        """Test writing content to a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            file_path = str(Path(temp_dir) / 'test_file.md')
            content = 'Hello, world!'

            # Act
            adapter.write_file(file_path, content, append=False)

            # Assert
            assert Path(file_path).exists()
            assert Path(file_path).read_text(encoding='utf-8') == content

    def test_write_file_overwrite_existing(self) -> None:
        """Test overwriting existing file content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            file_path = str(Path(temp_dir) / 'existing.md')
            original_content = 'Original content'
            new_content = 'New content'

            Path(file_path).write_text(original_content, encoding='utf-8')

            # Act
            adapter.write_file(file_path, new_content, append=False)

            # Assert
            assert Path(file_path).read_text(encoding='utf-8') == new_content

    def test_write_file_append_content(self) -> None:
        """Test appending content to existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            file_path = str(Path(temp_dir) / 'existing.md')
            original_content = 'Original content'
            appended_content = '\nAppended content'

            Path(file_path).write_text(original_content, encoding='utf-8')

            # Act
            adapter.write_file(file_path, appended_content, append=True)

            # Assert
            expected_content = original_content + appended_content
            assert Path(file_path).read_text(encoding='utf-8') == expected_content

    def test_write_file_creates_parent_directories(self) -> None:
        """Test that write_file creates parent directories as needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            nested_path = str(Path(temp_dir) / 'nested' / 'deep' / 'test.md')
            content = 'Test content'

            # Act
            adapter.write_file(nested_path, content)

            # Assert
            assert Path(nested_path).exists()
            assert Path(nested_path).read_text(encoding='utf-8') == content
            assert Path(nested_path).parent.exists()

    def test_write_file_os_error_handling(self) -> None:
        """Test write_file handles OS errors properly."""
        # Arrange
        adapter = FileSystemAdapter()
        invalid_path = '/invalid/path/that/cannot/be/created'

        # Act & Assert - The error is raised from ensure_parent_directory
        with pytest.raises(FileSystemError, match='ensure_parent'):
            adapter.write_file(invalid_path, 'content')

    def test_read_file_success(self) -> None:
        """Test reading file content successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            file_path = str(Path(temp_dir) / 'test.md')
            expected_content = 'Test file content\nWith multiple lines'
            Path(file_path).write_text(expected_content, encoding='utf-8')

            # Act
            content = FileSystemAdapter.read_file(file_path)

            # Assert
            assert content == expected_content

    def test_read_file_not_found(self) -> None:
        """Test reading non-existent file raises FileSystemError."""
        # Arrange
        non_existent_path = '/path/that/does/not/exist.md'

        # Act & Assert
        with pytest.raises(FileSystemError, match='read'):
            FileSystemAdapter.read_file(non_existent_path)

    def test_read_file_permission_error(self) -> None:
        """Test reading file with permission error."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b'content')

        try:
            # Make file unreadable
            Path(temp_path).chmod(0o000)

            # Act & Assert
            with pytest.raises(FileSystemError, match='read'):
                FileSystemAdapter.read_file(temp_path)
        finally:
            # Restore permissions and cleanup
            Path(temp_path).chmod(0o644)
            Path(temp_path).unlink()

    def test_file_exists_true(self) -> None:
        """Test file_exists returns True for existing file."""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Act
            result = FileSystemAdapter.file_exists(temp_file.name)

            # Assert
            assert result is True

    def test_file_exists_false(self) -> None:
        """Test file_exists returns False for non-existent file."""
        # Act
        result = FileSystemAdapter.file_exists('/path/that/does/not/exist')

        # Assert
        assert result is False

    def test_create_directory_success(self) -> None:
        """Test creating directory successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            new_dir = str(Path(temp_dir) / 'new_directory')

            # Act
            FileSystemAdapter.create_directory(new_dir)

            # Assert
            assert Path(new_dir).exists()
            assert Path(new_dir).is_dir()

    def test_create_directory_with_parents(self) -> None:
        """Test creating nested directories with parents=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            nested_dir = str(Path(temp_dir) / 'parent' / 'child' / 'grandchild')

            # Act
            FileSystemAdapter.create_directory(nested_dir, parents=True)

            # Assert
            assert Path(nested_dir).exists()
            assert Path(nested_dir).is_dir()

    def test_create_directory_os_error(self) -> None:
        """Test create_directory handles OS errors."""
        # Arrange - try to create directory in invalid location
        invalid_path = '/proc/invalid_directory_creation'

        # Act & Assert
        with pytest.raises(FileSystemError, match='create_directory'):
            FileSystemAdapter.create_directory(invalid_path)

    def test_get_current_directory(self) -> None:
        """Test getting current working directory."""
        # Act
        current_dir = FileSystemAdapter.get_current_directory()

        # Assert
        assert isinstance(current_dir, str)
        assert Path(current_dir).is_absolute()
        assert Path(current_dir).exists()

    def test_is_writable_existing_writable_directory(self) -> None:
        """Test is_writable returns True for writable directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()

            # Act
            result = adapter.is_writable(temp_dir)

            # Assert
            assert result is True

    def test_is_writable_non_existent_creatable_directory(self) -> None:
        """Test is_writable for non-existent directory that can be created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            non_existent_dir = str(Path(temp_dir) / 'new_dir')

            # Act
            result = adapter.is_writable(non_existent_dir)

            # Assert
            assert result is True

    def test_is_writable_non_creatable_directory(self) -> None:
        """Test is_writable returns False for directory that cannot be created."""
        # Arrange
        adapter = FileSystemAdapter()
        invalid_path = '/proc/cannot_create_here'

        # Act
        result = adapter.is_writable(invalid_path)

        # Assert
        assert result is False

    def test_is_writable_existing_readonly_directory(self) -> None:
        """Test is_writable returns False for read-only directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            adapter = FileSystemAdapter()
            readonly_dir = Path(temp_dir) / 'readonly'
            readonly_dir.mkdir()

            try:
                # Make directory read-only
                readonly_dir.chmod(0o555)

                # Act
                result = adapter.is_writable(str(readonly_dir))

                # Assert
                assert result is False
            finally:
                # Restore write permissions for cleanup
                readonly_dir.chmod(0o755)

    def test_is_writable_os_error_handling(self) -> None:
        """Test is_writable handles OS errors gracefully."""
        # Arrange
        adapter = FileSystemAdapter()

        # Mock Path to raise OSError
        with patch('prosemark.freewriting.adapters.file_system_adapter.Path') as mock_path:
            mock_path.side_effect = OSError('Mocked OS error')

            # Act
            result = adapter.is_writable('/any/path')

            # Assert
            assert result is False

    def test_get_absolute_path(self) -> None:
        """Test converting relative path to absolute path."""
        # Act
        result = FileSystemAdapter.get_absolute_path('.')

        # Assert
        assert Path(result).is_absolute()
        assert Path(result).exists()

    def test_get_absolute_path_already_absolute(self) -> None:
        """Test that absolute paths remain unchanged."""
        # Arrange
        absolute_path = '/absolute/path/test'

        # Act
        result = FileSystemAdapter.get_absolute_path(absolute_path)

        # Assert
        assert result == str(Path(absolute_path).resolve())

    def test_join_paths_multiple_components(self) -> None:
        """Test joining multiple path components."""
        # Act
        result = FileSystemAdapter.join_paths('home', 'user', 'documents', 'file.txt')

        # Assert
        expected = str(Path('home') / 'user' / 'documents' / 'file.txt')
        assert result == expected

    def test_join_paths_empty_input(self) -> None:
        """Test joining paths with empty input."""
        # Act
        result = FileSystemAdapter.join_paths()

        # Assert
        assert result == ''

    def test_join_paths_single_component(self) -> None:
        """Test joining single path component."""
        # Act
        result = FileSystemAdapter.join_paths('single_path')

        # Assert
        assert result == 'single_path'

    def test_get_file_size_success(self) -> None:
        """Test getting file size successfully."""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Arrange
            test_content = 'This is a test file with some content'
            temp_file.write(test_content.encode('utf-8'))
            temp_file.flush()

            # Act
            size = FileSystemAdapter.get_file_size(temp_file.name)

            # Assert
            assert size == len(test_content.encode('utf-8'))

    def test_get_file_size_file_not_found(self) -> None:
        """Test getting file size of non-existent file."""
        # Arrange
        non_existent_path = '/path/that/does/not/exist'

        # Act & Assert
        with pytest.raises(FileSystemError, match='stat'):
            FileSystemAdapter.get_file_size(non_existent_path)

    def test_backup_file_success(self) -> None:
        """Test creating backup file successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            original_file = Path(temp_dir) / 'original.txt'
            content = 'Original file content'
            original_file.write_text(content, encoding='utf-8')

            # Act
            backup_path = FileSystemAdapter.backup_file(str(original_file))

            # Assert
            assert Path(backup_path).exists()
            assert Path(backup_path).read_text(encoding='utf-8') == content
            assert backup_path.endswith('.txt.bak')

    def test_backup_file_custom_suffix(self) -> None:
        """Test creating backup with custom suffix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            original_file = Path(temp_dir) / 'original.txt'
            content = 'Original file content'
            original_file.write_text(content, encoding='utf-8')
            custom_suffix = '.backup'

            # Act
            backup_path = FileSystemAdapter.backup_file(str(original_file), custom_suffix)

            # Assert
            assert Path(backup_path).exists()
            assert backup_path.endswith('.txt.backup')

    def test_backup_file_source_not_found(self) -> None:
        """Test backing up non-existent file."""
        # Arrange
        non_existent_path = '/path/that/does/not/exist'

        # Act & Assert
        with pytest.raises(FileSystemError, match='backup'):
            FileSystemAdapter.backup_file(non_existent_path)

    def test_backup_file_shutil_error(self) -> None:
        """Test backup file handles shutil errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            original_file = Path(temp_dir) / 'original.txt'
            original_file.write_text('content', encoding='utf-8')

            # Mock shutil.copy2 to raise error
            with (
                patch('shutil.copy2', side_effect=shutil.Error('Mocked shutil error')),
                pytest.raises(FileSystemError, match='backup'),
            ):
                FileSystemAdapter.backup_file(str(original_file))

    def test_ensure_parent_directory_creates_missing_parents(self) -> None:
        """Test ensuring parent directory creates missing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            nested_file_path = str(Path(temp_dir) / 'level1' / 'level2' / 'level3' / 'file.txt')

            # Act
            FileSystemAdapter.ensure_parent_directory(nested_file_path)

            # Assert
            expected_parent = Path(nested_file_path).parent
            assert expected_parent.exists()
            assert expected_parent.is_dir()

    def test_ensure_parent_directory_parent_exists(self) -> None:
        """Test ensuring parent directory when parent already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            file_path = str(Path(temp_dir) / 'file.txt')

            # Act - should not raise any error
            FileSystemAdapter.ensure_parent_directory(file_path)

            # Assert
            assert Path(file_path).parent.exists()

    def test_ensure_parent_directory_os_error(self) -> None:
        """Test ensure_parent_directory handles OS errors."""
        # Arrange
        invalid_file_path = '/proc/invalid/nested/file.txt'

        # Act & Assert
        with pytest.raises(FileSystemError, match='ensure_parent'):
            FileSystemAdapter.ensure_parent_directory(invalid_file_path)

    def test_sanitize_title_basic(self) -> None:
        """Test basic title sanitization."""
        # Act
        result = FileSystemAdapter.sanitize_title('Simple Title')

        # Assert
        assert result == 'Simple Title'

    def test_sanitize_title_special_characters(self) -> None:
        """Test sanitizing title with special characters."""
        # Act
        result = FileSystemAdapter.sanitize_title('Title/with\\special:*?"<>|chars')

        # Assert
        assert result == 'Title_with_special_chars'
        assert '/' not in result
        assert '\\' not in result
        assert ':' not in result
        assert '*' not in result

    def test_sanitize_title_whitespace_handling(self) -> None:
        """Test sanitizing title with leading/trailing whitespace."""
        # Act
        result = FileSystemAdapter.sanitize_title('  Title with spaces  ')

        # Assert
        assert result == 'Title with spaces'

    def test_sanitize_title_multiple_underscores(self) -> None:
        """Test collapsing multiple consecutive underscores."""
        # Act
        result = FileSystemAdapter.sanitize_title('Title___with____many_underscores')

        # Assert
        assert result == 'Title_with_many_underscores'
        assert '___' not in result
        assert '__' not in result

    def test_sanitize_title_leading_trailing_underscores(self) -> None:
        """Test removing leading and trailing underscores."""
        # Act
        result = FileSystemAdapter.sanitize_title('_Leading and trailing_')

        # Assert
        assert result == 'Leading and trailing'
        assert not result.startswith('_')
        assert not result.endswith('_')

    def test_sanitize_title_complex_case(self) -> None:
        """Test sanitizing complex title with multiple issues."""
        # Act
        input_title = '  __My/Complex\\Title:*with?"<>|many__issues___  '
        result = FileSystemAdapter.sanitize_title(input_title)

        # Assert
        expected = 'My_Complex_Title_with_many_issues'
        assert result == expected
