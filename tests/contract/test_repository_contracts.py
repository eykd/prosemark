"""Contract test base classes for repository protocols."""

import abc

import pytest

from prosemark.domain.aggregates import Binder
from prosemark.domain.value_objects import BinderItem, NodeId
from prosemark.ports.repository_ports import BinderRepo, DailyRepo, NodeRepo


class BinderRepoContractTest(abc.ABC):
    """Base contract test for BinderRepo implementations.
    
    Inherit from this class to test any BinderRepo implementation.
    Implement get_repo() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_repo(self) -> BinderRepo:
        """Return BinderRepo implementation to test."""
        ...

    def test_load_returns_binder(self) -> None:
        """Test that load() returns a Binder instance."""
        repo = self.get_repo()
        binder = repo.load()
        assert isinstance(binder, Binder)

    def test_save_accepts_binder(self) -> None:
        """Test that save() accepts a Binder instance."""
        repo = self.get_repo()
        binder = Binder(roots=[])
        # Should not raise an exception
        repo.save(binder)

    def test_round_trip_preservation(self) -> None:
        """Test that save/load preserves binder structure."""
        repo = self.get_repo()

        # Create test binder with some structure
        test_id = NodeId('0192f0c1-0001-7000-8000-000000000001')
        item = BinderItem(id=test_id, display_title='Test Item', children=[])
        original_binder = Binder(roots=[item])

        # Save and reload
        repo.save(original_binder)
        loaded_binder = repo.load()

        # Verify structure is preserved
        assert len(loaded_binder.roots) == len(original_binder.roots)
        if loaded_binder.roots:
            assert loaded_binder.roots[0].id == original_binder.roots[0].id
            assert loaded_binder.roots[0].display_title == original_binder.roots[0].display_title


class NodeRepoContractTest(abc.ABC):
    """Base contract test for NodeRepo implementations.
    
    Inherit from this class to test any NodeRepo implementation.
    Implement get_repo() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_repo(self) -> NodeRepo:
        """Return NodeRepo implementation to test."""
        ...

    @abc.abstractmethod
    def get_test_node_id(self) -> NodeId:
        """Return a test NodeId that can be used safely."""
        ...

    def test_create_node(self) -> None:
        """Test node creation with frontmatter."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Should not raise an exception
        repo.create(node_id, title='Test Title', synopsis='Test synopsis')

    def test_read_frontmatter_after_create(self) -> None:
        """Test reading frontmatter after creation."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node
        repo.create(node_id, title='Test Title', synopsis='Test synopsis')

        # Read frontmatter
        frontmatter = repo.read_frontmatter(node_id)

        # Verify expected fields
        assert isinstance(frontmatter, dict)
        assert frontmatter.get('id') == str(node_id)
        assert frontmatter.get('title') == 'Test Title'
        assert frontmatter.get('synopsis') == 'Test synopsis'

    def test_write_frontmatter_preserves_data(self) -> None:
        """Test that writing frontmatter preserves data."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node
        repo.create(node_id, title='Original Title', synopsis='Original synopsis')

        # Read original frontmatter
        original_fm = repo.read_frontmatter(node_id)

        # Modify and write back
        modified_fm = original_fm.copy()
        modified_fm['title'] = 'Modified Title'
        modified_fm['custom_field'] = 'Custom Value'

        repo.write_frontmatter(node_id, modified_fm)

        # Read back and verify
        updated_fm = repo.read_frontmatter(node_id)
        assert updated_fm['title'] == 'Modified Title'
        assert updated_fm['custom_field'] == 'Custom Value'
        assert updated_fm['id'] == original_fm['id']  # ID should be preserved

    def test_open_in_editor_valid_parts(self) -> None:
        """Test opening node in editor with valid parts."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node first
        repo.create(node_id, title='Test Title', synopsis=None)

        # Should not raise for valid parts
        repo.open_in_editor(node_id, 'draft')
        repo.open_in_editor(node_id, 'notes')

    def test_open_in_editor_invalid_part_raises(self) -> None:
        """Test that invalid part raises ValueError."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node first
        repo.create(node_id, title='Test Title', synopsis=None)

        # Should raise for invalid part
        with pytest.raises(ValueError):
            repo.open_in_editor(node_id, 'invalid_part')

    def test_delete_with_files(self) -> None:
        """Test deleting node with files."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node
        repo.create(node_id, title='Test Title', synopsis=None)

        # Should not raise
        repo.delete(node_id, delete_files=True)

    def test_delete_without_files(self) -> None:
        """Test deleting node without files."""
        repo = self.get_repo()
        node_id = self.get_test_node_id()

        # Create node
        repo.create(node_id, title='Test Title', synopsis=None)

        # Should not raise
        repo.delete(node_id, delete_files=False)


class DailyRepoContractTest(abc.ABC):
    """Base contract test for DailyRepo implementations.
    
    Inherit from this class to test any DailyRepo implementation.
    Implement get_repo() to return the implementation under test.
    """

    @abc.abstractmethod
    def get_repo(self) -> DailyRepo:
        """Return DailyRepo implementation to test."""
        ...

    def test_write_freeform_returns_path(self) -> None:
        """Test that write_freeform returns a path string."""
        repo = self.get_repo()

        # Without title
        path1 = repo.write_freeform(None)
        assert isinstance(path1, str)
        assert len(path1) > 0

        # With title
        path2 = repo.write_freeform('Test Freewrite')
        assert isinstance(path2, str)
        assert len(path2) > 0

        # Paths should be different
        assert path1 != path2

    def test_write_freeform_creates_unique_files(self) -> None:
        """Test that multiple calls create unique files."""
        repo = self.get_repo()

        paths = []
        for i in range(3):
            path = repo.write_freeform(f'Freewrite {i}')
            paths.append(path)

        # All paths should be unique
        assert len(set(paths)) == len(paths)
