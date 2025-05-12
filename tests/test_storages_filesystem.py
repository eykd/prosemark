"""Tests for the filesystem storage adapter."""

import tempfile
from pathlib import Path

from prosemark.storages.base import NodeStoragePort
from prosemark.storages.filesystem import FilesystemMdNodeStorage


def test_node_storage_port_protocol() -> None:
    """Test that NodeStoragePort is a valid Protocol."""
    # This test verifies the Protocol definition is valid
    assert hasattr(NodeStoragePort, 'read')
    assert hasattr(NodeStoragePort, 'write')


class TestFilesystemMdNodeStorage:
    """Tests for the FilesystemMdNodeStorage class."""

    def test_init_creates_directory(self) -> None:
        """Test that initialization creates the base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'nodes'
            assert not path.exists()

            FilesystemMdNodeStorage(path)
            assert path.exists()
            assert path.is_dir()

    def test_read_nonexistent_file(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test reading a file that doesn't exist returns empty string."""
        content = fs_storage.read('nonexistent')
        assert content == ''

    def test_read_existing_file(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test reading an existing file returns its content."""
        # Setup
        node_id = 'test-node'
        expected_content = '# Test Content\n\nThis is a test.'
        file_path = fs_storage.base_path / f'{node_id}.md'
        file_path.write_text(expected_content, encoding='utf-8')

        # Test
        content = fs_storage.read(node_id)
        assert content == expected_content

    def test_write_creates_file(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test writing creates a file with the correct content."""
        node_id = 'new-node'
        content = '# New Node\n\nThis is a new node.'

        fs_storage.write(node_id, content)

        file_path = fs_storage.base_path / f'{node_id}.md'
        assert file_path.exists()
        assert file_path.read_text(encoding='utf-8') == content

    def test_write_creates_parent_directories(self) -> None:
        """Test writing creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / 'deep' / 'nested' / 'path'
            storage = FilesystemMdNodeStorage(base_path)

            node_id = 'test-node'
            content = '# Test Content'

            storage.write(node_id, content)

            file_path = base_path / f'{node_id}.md'
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == content

    def test_read_file_error_returns_empty_string(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test that read errors are handled by returning an empty string."""
        node_id = 'error-node'

        # Create a directory instead of a file to cause a read error
        file_path = fs_storage.base_path / f'{node_id}.md'
        file_path.mkdir()

        content = fs_storage.read(node_id)
        assert content == ''

    def test_get_file_path(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test that _get_file_path returns the correct path."""
        node_id = 'test-node'
        expected_path = fs_storage.base_path / f'{node_id}.md'

        path = fs_storage._get_file_path(node_id)  # noqa: SLF001
        assert path == expected_path

    def test_get_binder(self, fs_storage: FilesystemMdNodeStorage) -> None:
        """Test that get_binder returns the content of the _binder node."""
        expected_content = '# Binder Content\n\nThis is the binder.'
        file_path = fs_storage.base_path / '_binder.md'
        file_path.write_text(expected_content, encoding='utf-8')

        content = fs_storage.get_binder()
        assert content == expected_content
