"""Tests for NodeRepo abstract base class."""

import inspect
from abc import ABC

import pytest

from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeNotFoundError
from prosemark.ports.node_repo import NodeRepo


def test_node_repo_abstract_base_class_exists() -> None:
    """Test NodeRepo abstract base class is properly defined."""
    # Check it's an abstract base class
    assert issubclass(NodeRepo, ABC)

    # Check required methods exist
    required_methods = ['create', 'read_frontmatter', 'write_frontmatter', 'open_in_editor', 'delete']
    for method in required_methods:
        assert hasattr(NodeRepo, method)

    # Check methods are abstract
    assert getattr(NodeRepo.create, '__isabstractmethod__', False)
    assert getattr(NodeRepo.read_frontmatter, '__isabstractmethod__', False)
    assert getattr(NodeRepo.write_frontmatter, '__isabstractmethod__', False)
    assert getattr(NodeRepo.open_in_editor, '__isabstractmethod__', False)
    assert getattr(NodeRepo.delete, '__isabstractmethod__', False)


def test_node_repo_method_signatures() -> None:
    """Test NodeRepo methods have correct signatures."""
    # create(node_id: NodeId, title: str | None, synopsis: str | None) -> None
    create_sig = inspect.signature(NodeRepo.create)
    params = create_sig.parameters
    assert 'node_id' in params
    assert 'title' in params
    assert 'synopsis' in params
    assert params['node_id'].annotation == 'NodeId'
    assert params['title'].annotation == str | None
    assert params['synopsis'].annotation == str | None
    assert create_sig.return_annotation is None

    # read_frontmatter(node_id: NodeId) -> dict
    read_sig = inspect.signature(NodeRepo.read_frontmatter)
    assert 'node_id' in read_sig.parameters
    assert read_sig.parameters['node_id'].annotation == 'NodeId'
    assert read_sig.return_annotation == dict[str, str | None]

    # write_frontmatter(node_id: NodeId, fm: dict) -> None
    write_sig = inspect.signature(NodeRepo.write_frontmatter)
    write_params = write_sig.parameters
    assert 'node_id' in write_params
    assert 'fm' in write_params
    assert write_params['node_id'].annotation == 'NodeId'
    assert write_params['fm'].annotation == dict[str, str | None]
    assert write_sig.return_annotation is None

    # open_in_editor(node_id: NodeId, part: str) -> None
    editor_sig = inspect.signature(NodeRepo.open_in_editor)
    editor_params = editor_sig.parameters
    assert 'node_id' in editor_params
    assert 'part' in editor_params
    assert editor_params['node_id'].annotation == 'NodeId'
    assert editor_params['part'].annotation is str
    assert editor_sig.return_annotation is None

    # delete(node_id: NodeId, *, delete_files: bool) -> None
    delete_sig = inspect.signature(NodeRepo.delete)
    delete_params = delete_sig.parameters
    assert 'node_id' in delete_params
    assert 'delete_files' in delete_params
    assert delete_params['node_id'].annotation == 'NodeId'
    assert delete_params['delete_files'].annotation is bool
    assert delete_params['delete_files'].kind == inspect.Parameter.KEYWORD_ONLY
    assert delete_sig.return_annotation is None


def test_node_repo_error_documentation() -> None:
    """Test NodeRepo methods document expected exceptions."""
    read_doc = NodeRepo.read_frontmatter.__doc__ or ''

    # Check docstrings mention expected exceptions
    assert 'NodeNotFoundError' in read_doc


def test_cannot_instantiate_abstract_base_class() -> None:
    """Test that NodeRepo cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        NodeRepo()  # type: ignore[abstract]


class NodeRepoContractTests:
    """Base class for testing NodeRepo implementations.

    This class provides standard tests that all NodeRepo implementations
    should pass. Concrete test classes should inherit from this class and
    provide a repo fixture.
    """

    def create_test_node(self, repo: NodeRepo) -> NodeId:
        """Helper to create a test node and return its ID."""
        node_id = NodeId('01930000-0000-7000-8000-000000000001')
        repo.create(node_id, 'Test Title', 'Test synopsis')
        return node_id

    def test_create_and_read_frontmatter(self, repo: NodeRepo) -> None:
        """Test create and read frontmatter cycle."""
        node_id = NodeId('01930000-0000-7000-8000-000000000001')
        title = 'Test Chapter'
        synopsis = 'Test synopsis'

        repo.create(node_id, title, synopsis)
        fm = repo.read_frontmatter(node_id)

        assert fm['id'] == str(node_id)
        assert fm['title'] == title
        assert fm['synopsis'] == synopsis
        assert 'created' in fm
        assert 'updated' in fm

    def test_create_with_none_values(self, repo: NodeRepo) -> None:
        """Test create with None title and synopsis."""
        node_id = NodeId('01930000-0000-7000-8000-000000000002')

        repo.create(node_id, None, None)
        fm = repo.read_frontmatter(node_id)

        assert fm['id'] == str(node_id)
        assert fm.get('title') is None
        assert fm.get('synopsis') is None
        assert 'created' in fm
        assert 'updated' in fm

    def test_write_frontmatter_updates_metadata(self, repo: NodeRepo) -> None:
        """Test frontmatter updates work correctly."""
        node_id = self.create_test_node(repo)

        updated_fm: dict[str, str | None] = {
            'id': str(node_id),
            'title': 'Updated Title',
            'synopsis': 'Updated synopsis',
            'created': '2025-09-10T10:00:00-07:00',
            'updated': '2025-09-10T11:00:00-07:00',
        }

        repo.write_frontmatter(node_id, updated_fm)
        result_fm = repo.read_frontmatter(node_id)

        assert result_fm['title'] == 'Updated Title'
        assert result_fm['synopsis'] == 'Updated synopsis'

    def test_read_nonexistent_node_raises_error(self, repo: NodeRepo) -> None:
        """Test reading nonexistent node raises NodeNotFoundError."""
        nonexistent_id = NodeId('01930000-0000-7000-8000-000000000999')

        with pytest.raises(NodeNotFoundError):
            repo.read_frontmatter(nonexistent_id)

    def test_open_in_editor_accepts_valid_parts(self, repo: NodeRepo) -> None:
        """Test open_in_editor accepts valid part values."""
        node_id = self.create_test_node(repo)

        # Should not raise for valid parts
        valid_parts = ['draft', 'notes', 'synopsis']
        for part in valid_parts:
            repo.open_in_editor(node_id, part)

    def test_delete_with_delete_files_flag(self, repo: NodeRepo) -> None:
        """Test delete method with delete_files parameter."""
        node_id = self.create_test_node(repo)

        # Should not raise
        repo.delete(node_id, delete_files=True)

        # Node should no longer be readable
        with pytest.raises(NodeNotFoundError):
            repo.read_frontmatter(node_id)

    def test_delete_without_delete_files_flag(self, repo: NodeRepo) -> None:
        """Test delete method without deleting files."""
        node_id = self.create_test_node(repo)

        # Should not raise
        repo.delete(node_id, delete_files=False)


# Test helper functions
def create_test_node_id() -> NodeId:
    """Create a test NodeId."""
    return NodeId('01930000-0000-7000-8000-000000000001')


def create_sample_frontmatter(node_id: NodeId) -> dict[str, str | None]:
    """Create sample frontmatter for testing."""
    return {
        'id': str(node_id),
        'title': 'Sample Title',
        'synopsis': 'Sample synopsis',
        'created': '2025-09-10T10:00:00-07:00',
        'updated': '2025-09-10T10:30:00-07:00',
    }
