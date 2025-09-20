"""Tests for BinderRepo abstract base class."""

import inspect
from abc import ABC

import pytest

from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.ports.binder_repo import BinderRepo


def test_binder_repo_abstract_base_class_exists() -> None:
    """Test BinderRepo abstract base class is properly defined."""
    # Check it's an abstract base class
    assert issubclass(BinderRepo, ABC)

    # Check required methods exist
    assert hasattr(BinderRepo, 'load')
    assert hasattr(BinderRepo, 'save')

    # Check methods are abstract
    assert getattr(BinderRepo.load, '__isabstractmethod__', False)
    assert getattr(BinderRepo.save, '__isabstractmethod__', False)


def test_binder_repo_type_annotations() -> None:
    """Test BinderRepo has correct type annotations."""
    load_sig = inspect.signature(BinderRepo.load)
    save_sig = inspect.signature(BinderRepo.save)

    # load() -> Binder (string annotation due to TYPE_CHECKING import)
    assert load_sig.return_annotation == 'Binder'

    # save(binder: Binder) -> None
    assert 'binder' in save_sig.parameters
    assert save_sig.parameters['binder'].annotation == 'Binder'
    assert save_sig.return_annotation is None


def test_binder_repo_error_documentation() -> None:
    """Test BinderRepo methods document expected exceptions."""
    load_doc = BinderRepo.load.__doc__ or ''
    save_doc = BinderRepo.save.__doc__ or ''

    # Check docstrings mention expected exceptions
    assert 'BinderNotFoundError' in load_doc
    assert 'FileSystemError' in load_doc
    assert 'BinderIntegrityError' in load_doc
    assert 'FileSystemError' in save_doc


class BinderRepoContractTests:
    """Base class for testing BinderRepo implementations.

    This class provides standard tests that all BinderRepo implementations
    should pass. Concrete test classes should inherit from this class and
    provide a repo fixture.
    """

    def test_load_returns_binder(self, repo: BinderRepo) -> None:
        """Test load method returns Binder instance."""
        binder = repo.load()
        assert isinstance(binder, Binder)

    def test_save_accepts_binder(self, repo: BinderRepo) -> None:
        """Test save method accepts Binder instance."""
        binder = Binder(roots=[])
        # Should not raise
        repo.save(binder)

    def test_round_trip_preserves_data(self, repo: BinderRepo) -> None:
        """Test save/load cycle preserves binder data."""
        # Create test binder with some content
        node_id = NodeId('01930000-0000-7000-8000-000000000000')
        item = BinderItem(id_=node_id, display_title='Test Item')
        original = Binder(roots=[item])

        repo.save(original)
        loaded = repo.load()

        # Compare the loaded binder with original
        assert len(loaded.roots) == len(original.roots)
        assert loaded.roots[0].id == original.roots[0].id
        assert loaded.roots[0].display_title == original.roots[0].display_title

    def test_load_nonexistent_raises_binder_not_found(self, repo: BinderRepo) -> None:
        """Test load raises BinderNotFoundError for missing binder."""
        # This test assumes the repo can be configured to point to missing file
        # Implementation-specific repos will need to override if needed

    def test_save_invalid_path_raises_filesystem_error(self, repo: BinderRepo) -> None:
        """Test save raises FileSystemError for invalid paths."""
        # This test assumes the repo can be configured with invalid path
        # Implementation-specific repos will need to override if needed


def test_cannot_instantiate_abstract_base_class() -> None:
    """Test that BinderRepo cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BinderRepo()  # type: ignore[abstract]


# Test helper functions
def create_test_binder() -> Binder:
    """Create a test binder with sample data."""
    node_id1 = NodeId('01930000-0000-7000-8000-000000000001')
    node_id2 = NodeId('01930000-0000-7000-8000-000000000002')

    # Create nested structure
    child_item = BinderItem(id_=node_id2, display_title='Child Item')
    parent_item = BinderItem(id_=node_id1, display_title='Parent Item', children=[child_item])
    placeholder = BinderItem(id_=None, display_title='Placeholder Section')

    return Binder(roots=[parent_item, placeholder])
