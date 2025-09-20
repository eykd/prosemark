"""Contract tests for Binder entity.

These tests define the behavioral contracts that any Binder implementation must satisfy.
They will fail until the Binder class is properly implemented.
"""

import pytest

# These imports will fail until classes are implemented
from prosemark.domain.entities import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderIntegrityError


class TestBinderContract:
    """Contract tests for Binder entity."""

    def test_binder_initialization_with_empty_roots(self) -> None:
        """Contract: Binder can be created with empty root items list."""
        managed_content = '- [Item 1](node1.md)\n- [Item 2](node2.md)'
        binder = Binder(roots=[], managed_content=managed_content)

        assert binder.roots == []
        assert binder.managed_content == managed_content

    def test_binder_initialization_with_root_items(self) -> None:
        """Contract: Binder can be created with root-level BinderItems."""
        root_item = BinderItem(
            display_title='Chapter 1', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        managed_content = '- [Chapter 1](0192f0c1.md)'

        binder = Binder(roots=[root_item], managed_content=managed_content)

        assert len(binder.roots) == 1
        assert binder.roots[0] == root_item
        assert binder.managed_content == managed_content

    def test_binder_maintains_tree_structure_invariant(self) -> None:
        """Contract: Binder must maintain valid tree structure (no cycles)."""
        # Create a valid tree structure
        parent_item = BinderItem(
            display_title='Chapter 1', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        child_item = BinderItem(
            display_title='Section 1.1',
            node_id=NodeId('0192f0c1-2345-7456-8abc-def012345678'),
            children=[],
            parent=parent_item,
        )
        parent_item.children = [child_item]

        managed_content = '- [Chapter 1](0192f0c1.md)\n  - [Section 1.1](0192f0c1-2345-7456.md)'
        binder = Binder(roots=[parent_item], managed_content=managed_content)

        # Verify the tree structure is maintained
        assert len(binder.roots) == 1
        assert binder.roots[0] == parent_item
        assert len(parent_item.children) == 1
        assert parent_item.children[0] == child_item
        assert child_item.parent == parent_item

    def test_binder_rejects_circular_references(self) -> None:
        """Contract: Binder must detect and reject circular references."""
        # This test will need the validation logic in place
        # For now, it documents the expected behavior
        # Implementation will need cycle detection

    def test_binder_enforces_unique_node_ids(self) -> None:
        """Contract: All node IDs in binder must be unique."""
        duplicate_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        item1 = BinderItem(display_title='Chapter 1', node_id=duplicate_id, children=[], parent=None)
        item2 = BinderItem(
            display_title='Chapter 2',
            node_id=duplicate_id,  # Same ID - should be rejected
            children=[],
            parent=None,
        )

        managed_content = '- [Chapter 1](0192f0c1.md)\n- [Chapter 2](0192f0c1.md)'

        # Creating binder with duplicate node IDs should raise an error
        with pytest.raises(BinderIntegrityError):
            Binder(roots=[item1, item2], managed_content=managed_content)

    def test_binder_allows_placeholder_items(self) -> None:
        """Contract: Binder can contain items without node_id (placeholders)."""
        placeholder_item = BinderItem(
            display_title='Future Chapter',
            node_id=None,  # Placeholder has no node ID
            children=[],
            parent=None,
        )

        managed_content = '- [Future Chapter]()'
        binder = Binder(roots=[placeholder_item], managed_content=managed_content)

        assert len(binder.roots) == 1
        assert binder.roots[0].node_id is None
        assert binder.roots[0].display_title == 'Future Chapter'

    def test_binder_parent_child_consistency(self) -> None:
        """Contract: Parent-child relationships must be bidirectionally consistent."""
        parent = BinderItem(
            display_title='Chapter 1', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        child1 = BinderItem(
            display_title='Section 1.1',
            node_id=NodeId('0192f0c1-2345-7456-8abc-def012345678'),
            children=[],
            parent=parent,
        )
        child2 = BinderItem(
            display_title='Section 1.2',
            node_id=NodeId('0192f0c1-2345-7789-8abc-def012345678'),
            children=[],
            parent=parent,
        )

        parent.children = [child1, child2]

        managed_content = """
- [Chapter 1](0192f0c1.md)
  - [Section 1.1](0192f0c1-2345-7456.md)
  - [Section 1.2](0192f0c1-2345-7789.md)
        """.strip()

        Binder(roots=[parent], managed_content=managed_content)

        # Verify bidirectional consistency
        assert child1.parent == parent
        assert child2.parent == parent
        assert child1 in parent.children
        assert child2 in parent.children

    def test_binder_managed_content_preservation(self) -> None:
        """Contract: Binder must preserve managed content exactly."""
        original_content = """- [Chapter 1](node1.md)
  - [Section 1.1](node2.md)
- [Chapter 2](node3.md)"""

        binder = Binder(roots=[], managed_content=original_content)
        assert binder.managed_content == original_content

    def test_binder_get_all_node_ids(self) -> None:
        """Contract: Binder should provide method to get all node IDs."""
        node_id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        node_id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        item1 = BinderItem(display_title='Chapter 1', node_id=node_id1, children=[], parent=None)
        item2 = BinderItem(display_title='Section 1.1', node_id=node_id2, children=[], parent=item1)
        placeholder = BinderItem(display_title='Future Chapter', node_id=None, children=[], parent=None)

        item1.children = [item2]

        binder = Binder(roots=[item1, placeholder], managed_content='test content')

        # Should return all non-None node IDs
        all_node_ids = binder.get_all_node_ids()
        assert node_id1 in all_node_ids
        assert node_id2 in all_node_ids
        assert len(all_node_ids) == 2

    def test_binder_find_item_by_node_id(self) -> None:
        """Contract: Binder should provide method to find items by node ID."""
        target_node_id = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        parent = BinderItem(
            display_title='Chapter 1', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        target_item = BinderItem(display_title='Section 1.1', node_id=target_node_id, children=[], parent=parent)
        parent.children = [target_item]

        binder = Binder(roots=[parent], managed_content='test')

        found_item = binder.find_item_by_node_id(target_node_id)
        assert found_item == target_item

        # Should return None for non-existent node ID
        non_existent_id = NodeId('0192f0c1-2345-7999-8abc-def012345678')
        assert binder.find_item_by_node_id(non_existent_id) is None

    def test_binder_add_root_item(self) -> None:
        """Contract: Binder should provide method to add root items."""
        binder = Binder(roots=[], managed_content='')

        new_item = BinderItem(
            display_title='New Chapter',
            node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'),
            children=[],
            parent=None,
        )

        binder.add_root_item(new_item)

        assert len(binder.roots) == 1
        assert binder.roots[0] == new_item

    def test_binder_remove_root_item(self) -> None:
        """Contract: Binder should provide method to remove root items."""
        item = BinderItem(
            display_title='Chapter 1', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        binder = Binder(roots=[item], managed_content='test')

        binder.remove_root_item(item)

        assert len(binder.roots) == 0

    def test_binder_depth_first_traversal(self) -> None:
        """Contract: Binder should support depth-first traversal of items."""
        # Build a tree structure
        root = BinderItem(
            display_title='Root', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
        )
        child1 = BinderItem(
            display_title='Child 1', node_id=NodeId('0192f0c1-2345-7456-8abc-def012345678'), children=[], parent=root
        )
        child2 = BinderItem(
            display_title='Child 2', node_id=NodeId('0192f0c1-2345-7789-8abc-def012345678'), children=[], parent=root
        )
        grandchild = BinderItem(
            display_title='Grandchild',
            node_id=NodeId('0192f0c1-2345-7abc-8abc-def012345678'),
            children=[],
            parent=child1,
        )

        child1.children = [grandchild]
        root.children = [child1, child2]

        binder = Binder(roots=[root], managed_content='test')

        # Traverse depth-first
        items = list(binder.depth_first_traversal())

        # Should visit in depth-first order: root, child1, grandchild, child2
        expected_titles = ['Root', 'Child 1', 'Grandchild', 'Child 2']
        actual_titles = [item.display_title for item in items]
        assert actual_titles == expected_titles


@pytest.fixture
def sample_node_ids() -> list[NodeId]:
    """Fixture providing sample NodeIds for testing."""
    return [
        NodeId('0192f0c1-2345-7123-8abc-def012345678'),
        NodeId('0192f0c1-2345-7456-8abc-def012345678'),
        NodeId('0192f0c1-2345-7789-8abc-def012345678'),
    ]


@pytest.fixture
def simple_binder() -> Binder:
    """Fixture providing a simple binder for testing."""
    item = BinderItem(
        display_title='Test Chapter', node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), children=[], parent=None
    )
    return Binder(roots=[item], managed_content='- [Test Chapter](0192f0c1.md)')
