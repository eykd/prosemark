"""Tests for edge cases in domain models to achieve 100% coverage."""

import pytest

from prosemark.domain.models import Binder, BinderItem, NodeId


class TestBinderItemEdgeCases:
    """Test edge cases in BinderItem for complete coverage."""

    def test_binder_item_rejects_both_id_and_node_id_parameters(self) -> None:
        """Test that BinderItem raises ValueError when both id_ and node_id are specified."""
        # Arrange
        node_id = NodeId.generate()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot specify both 'id_' and 'node_id' parameters"):
            BinderItem(display_title='Test', id_=node_id, node_id=node_id)


class TestBinderEdgeCases:
    """Test edge cases in Binder for complete coverage."""

    def test_remove_root_item_when_item_not_in_roots(self) -> None:
        """Test remove_root_item does nothing when item is not in roots."""
        # Arrange
        item1 = BinderItem(display_title='Item 1', node_id=None)
        item2 = BinderItem(display_title='Item 2', node_id=None)
        binder = Binder(roots=[item1])

        # Act - try to remove an item that's not in roots
        binder.remove_root_item(item2)

        # Assert - roots should be unchanged
        assert len(binder.roots) == 1
        assert binder.roots[0] is item1

    def test_remove_root_item_successfully_removes_existing_item(self) -> None:
        """Test remove_root_item successfully removes item when it exists in roots."""
        # Arrange
        item1 = BinderItem(display_title='Item 1', node_id=None)
        item2 = BinderItem(display_title='Item 2', node_id=None)
        binder = Binder(roots=[item1, item2])

        # Act - remove item that exists
        binder.remove_root_item(item1)

        # Assert - item1 should be removed, item2 should remain
        assert len(binder.roots) == 1
        assert binder.roots[0] is item2

    def test_binder_children_property_returns_roots(self) -> None:
        """Test that Binder.children property returns the roots list (compatibility)."""
        # Arrange
        item1 = BinderItem(display_title='Item 1', node_id=None)
        item2 = BinderItem(display_title='Item 2', node_id=None)
        binder = Binder(roots=[item1, item2])

        # Act & Assert
        assert binder.children == binder.roots
        assert len(binder.children) == 2
        assert binder.children[0] is item1
        assert binder.children[1] is item2
