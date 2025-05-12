"""Tests for the InMemoryNodeStorage class.

This module contains tests for the in-memory storage adapter implementation.
"""

import pytest

from prosemark.storages.inmemory import InMemoryNodeStorage


class TestInMemoryNodeStorage:
    """Test suite for InMemoryNodeStorage class."""

    @pytest.fixture
    def storage(self) -> InMemoryNodeStorage:
        """Create a fresh storage instance for each test.

        Returns:
            A new InMemoryNodeStorage instance.

        """
        return InMemoryNodeStorage()

    def test_read_returns_empty_string_for_nonexistent_node(self, storage: InMemoryNodeStorage) -> None:
        """Test that reading a nonexistent node returns an empty string."""
        result = storage.read('nonexistent')
        assert result == ''

    def test_write_and_read_node_content(self, storage: InMemoryNodeStorage) -> None:
        """Test that written content can be read back correctly."""
        node_id = 'test_node'
        content = 'Test content'

        storage.write(node_id, content)
        result = storage.read(node_id)

        assert result == content

    def test_overwrite_existing_node(self, storage: InMemoryNodeStorage) -> None:
        """Test that writing to an existing node overwrites its content."""
        node_id = 'test_node'
        initial_content = 'Initial content'
        new_content = 'New content'

        storage.write(node_id, initial_content)
        storage.write(node_id, new_content)
        result = storage.read(node_id)

        assert result == new_content

    def test_get_binder_returns_empty_string_when_not_set(self, storage: InMemoryNodeStorage) -> None:
        """Test that get_binder returns empty string when _binder node is not set."""
        result = storage.get_binder()
        assert result == ''

    def test_get_binder_returns_binder_content(self, storage: InMemoryNodeStorage) -> None:
        """Test that get_binder returns the content of the _binder node."""
        binder_content = 'Project structure metadata'
        storage.write('_binder', binder_content)

        result = storage.get_binder()
        assert result == binder_content
