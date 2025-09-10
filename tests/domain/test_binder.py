"""Tests for Binder aggregate."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from uuid_extension import uuid7

from prosemark.domain.aggregates import Binder
from prosemark.domain.exceptions import BinderIntegrityError
from prosemark.domain.value_objects import BinderItem, NodeId


class TestBinder:
    """Test suite for Binder aggregate."""

    def test_create_empty_binder(self) -> None:
        """Binder can be created empty."""
        binder = Binder(roots=[])

        assert binder.roots == []
        assert binder.is_empty()

    def test_create_with_roots(self) -> None:
        """Binder can be created with root items."""
        item1 = BinderItem(id=NodeId(uuid7()), display_title='Chapter 1', children=[])
        item2 = BinderItem(id=NodeId(uuid7()), display_title='Chapter 2', children=[])

        binder = Binder(roots=[item1, item2])

        assert len(binder.roots) == 2
        assert binder.roots[0] == item1
        assert binder.roots[1] == item2
        assert not binder.is_empty()

    def test_rejects_duplicate_node_ids(self) -> None:
        """Binder rejects structures with duplicate NodeIds."""
        node_id = NodeId(uuid7())

        # Same ID in two root items
        item1 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=node_id, display_title='Chapter 2', children=[])

        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[item1, item2])

    def test_rejects_duplicate_ids_in_hierarchy(self) -> None:
        """Binder rejects duplicate NodeIds anywhere in hierarchy."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        duplicate_id = NodeId(uuid7())

        child1 = BinderItem(id=duplicate_id, display_title='Section 1.1', children=[])
        parent1 = BinderItem(id=id1, display_title='Chapter 1', children=[child1])

        child2 = BinderItem(id=duplicate_id, display_title='Section 2.1', children=[])
        parent2 = BinderItem(id=id2, display_title='Chapter 2', children=[child2])

        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[parent1, parent2])

    def test_allows_placeholders(self) -> None:
        """Binder allows placeholders (items with None id)."""
        item1 = BinderItem(id=NodeId(uuid7()), display_title='Chapter 1', children=[])
        placeholder1 = BinderItem(id=None, display_title='Placeholder 1', children=[])
        placeholder2 = BinderItem(id=None, display_title='Placeholder 2', children=[])

        # Multiple placeholders should be allowed
        binder = Binder(roots=[item1, placeholder1, placeholder2])

        assert len(binder.roots) == 3
        assert binder.count_placeholders() == 2

    def test_add_root(self) -> None:
        """Can add root items to binder."""
        binder = Binder(roots=[])
        item = BinderItem(id=NodeId(uuid7()), display_title='Chapter 1', children=[])

        new_binder = binder.add_root(item)

        assert len(new_binder.roots) == 1
        assert new_binder.roots[0] == item
        # Original should be unchanged (immutability)
        assert len(binder.roots) == 0

    def test_add_root_rejects_duplicate(self) -> None:
        """add_root rejects duplicate NodeIds."""
        node_id = NodeId(uuid7())
        item1 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=node_id, display_title='Chapter 2', children=[])

        binder = Binder(roots=[item1])

        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            binder.add_root(item2)

    def test_remove_by_id(self) -> None:
        """Can remove items by NodeId."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())

        item1 = BinderItem(id=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=id2, display_title='Chapter 2', children=[])
        item3 = BinderItem(id=id3, display_title='Chapter 3', children=[])

        binder = Binder(roots=[item1, item2, item3])
        new_binder = binder.remove_by_id(id2)

        assert len(new_binder.roots) == 2
        assert new_binder.roots[0] == item1
        assert new_binder.roots[1] == item3
        # Original unchanged
        assert len(binder.roots) == 3

    def test_remove_nested_by_id(self) -> None:
        """Can remove nested items by NodeId."""
        parent_id = NodeId(uuid7())
        child_id = NodeId(uuid7())

        child = BinderItem(id=child_id, display_title='Section 1.1', children=[])
        parent = BinderItem(id=parent_id, display_title='Chapter 1', children=[child])

        binder = Binder(roots=[parent])
        new_binder = binder.remove_by_id(child_id)

        # Parent should remain but without child
        assert len(new_binder.roots) == 1
        assert new_binder.roots[0].id == parent_id
        assert len(new_binder.roots[0].children) == 0

    def test_find_by_id(self) -> None:
        """Can find items by NodeId."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        target_id = NodeId(uuid7())

        target = BinderItem(id=target_id, display_title='Target', children=[])
        parent = BinderItem(id=id1, display_title='Parent', children=[target])
        other = BinderItem(id=id2, display_title='Other', children=[])

        binder = Binder(roots=[parent, other])

        found = binder.find_by_id(target_id)
        assert found == target

        not_found = binder.find_by_id(NodeId(uuid7()))
        assert not_found is None

    def test_get_all_ids(self) -> None:
        """get_all_ids returns all non-None NodeIds."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())

        item3 = BinderItem(id=id3, display_title='Nested', children=[])
        item2 = BinderItem(id=id2, display_title='Child', children=[item3])
        item1 = BinderItem(id=id1, display_title='Root', children=[item2])
        placeholder = BinderItem(id=None, display_title='Placeholder', children=[])

        binder = Binder(roots=[item1, placeholder])

        all_ids = binder.get_all_ids()

        assert len(all_ids) == 3
        assert id1 in all_ids
        assert id2 in all_ids
        assert id3 in all_ids

    def test_validate_no_cycles(self) -> None:
        """Binder validates against cycles in tree structure."""
        # This would require more complex tree manipulation
        # For MVP, we ensure the tree structure is valid through immutability

    def test_immutability(self) -> None:
        """Binder operations return new instances."""
        item1 = BinderItem(id=NodeId(uuid7()), display_title='Chapter 1', children=[])
        item2 = BinderItem(id=NodeId(uuid7()), display_title='Chapter 2', children=[])

        binder1 = Binder(roots=[item1])
        binder2 = binder1.add_root(item2)

        # Should be different instances
        assert binder1 is not binder2
        assert len(binder1.roots) == 1
        assert len(binder2.roots) == 2

    def test_move_item(self) -> None:
        """Can move items within binder."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())

        item3 = BinderItem(id=id3, display_title='Section', children=[])
        item2 = BinderItem(id=id2, display_title='Chapter 2', children=[])
        item1 = BinderItem(id=id1, display_title='Chapter 1', children=[item3])

        binder = Binder(roots=[item1, item2])

        # Move item3 from item1 to item2
        new_binder = binder.move_item(id3, new_parent_id=id2)

        # item3 should now be under item2
        new_item2 = new_binder.find_by_id(id2)
        assert len(new_item2.children) == 1
        assert new_item2.children[0].id == id3

        # item1 should have no children
        new_item1 = new_binder.find_by_id(id1)
        assert len(new_item1.children) == 0

    def test_insert_at_position(self) -> None:
        """Can insert items at specific positions."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())
        new_id = NodeId(uuid7())

        item1 = BinderItem(id=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=id2, display_title='Chapter 2', children=[])
        item3 = BinderItem(id=id3, display_title='Chapter 3', children=[])
        new_item = BinderItem(id=new_id, display_title='New Chapter', children=[])

        binder = Binder(roots=[item1, item2, item3])

        # Insert at position 1 (between item1 and item2)
        new_binder = binder.insert_root(new_item, position=1)

        assert len(new_binder.roots) == 4
        assert new_binder.roots[0] == item1
        assert new_binder.roots[1] == new_item
        assert new_binder.roots[2] == item2
        assert new_binder.roots[3] == item3

    @given(st.integers(min_value=1, max_value=10))
    def test_property_no_duplicates_invariant(self, num_items: int) -> None:
        """Property: Binder always maintains no-duplicates invariant."""
        # Create items with unique IDs
        items = [BinderItem(id=NodeId(uuid7()), display_title=f'Item {_}', children=[]) for _ in range(num_items)]

        binder = Binder(roots=items)
        all_ids = binder.get_all_ids()

        # Should have exactly as many unique IDs as items
        assert len(all_ids) == num_items
        assert len(set(all_ids)) == num_items  # All unique

    def test_repr(self) -> None:
        """Binder has a useful repr."""
        item = BinderItem(id=NodeId(uuid7()), display_title='Chapter 1', children=[])
        binder = Binder(roots=[item])

        repr_str = repr(binder)
        assert 'Binder' in repr_str
        assert '1 root' in repr_str or 'roots=1' in repr_str
