"""Tests for BinderItem value object."""

import pytest
from uuid_extension import uuid7

from prosemark.domain.value_objects import BinderItem, NodeId


class TestBinderItem:
    """Test suite for BinderItem value object."""

    def test_create_with_node_id(self) -> None:
        """BinderItem can be created with a NodeId."""
        node_id = NodeId(uuid7())
        display_title = 'Chapter 1'

        item = BinderItem(id=node_id, display_title=display_title, children=[])

        assert item.id == node_id
        assert item.display_title == display_title
        assert item.children == []

    def test_create_placeholder(self) -> None:
        """BinderItem can be created as placeholder (None id)."""
        display_title = 'Placeholder Chapter'

        item = BinderItem(id=None, display_title=display_title, children=[])

        assert item.id is None
        assert item.display_title == display_title
        assert item.children == []
        assert item.is_placeholder()

    def test_create_with_children(self) -> None:
        """BinderItem can be created with children."""
        parent_id = NodeId(uuid7())
        child1_id = NodeId(uuid7())
        child2_id = NodeId(uuid7())

        child1 = BinderItem(id=child1_id, display_title='Section 1.1', children=[])
        child2 = BinderItem(id=child2_id, display_title='Section 1.2', children=[])

        parent = BinderItem(id=parent_id, display_title='Chapter 1', children=[child1, child2])

        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2

    def test_nested_hierarchy(self) -> None:
        """BinderItem supports nested hierarchies."""
        root_id = NodeId(uuid7())
        chapter_id = NodeId(uuid7())
        section_id = NodeId(uuid7())

        section = BinderItem(id=section_id, display_title='Section 1.1.1', children=[])
        chapter = BinderItem(id=chapter_id, display_title='Chapter 1.1', children=[section])
        root = BinderItem(id=root_id, display_title='Part 1', children=[chapter])

        assert len(root.children) == 1
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0] == section

    def test_immutability(self) -> None:
        """BinderItem is immutable (frozen dataclass)."""
        node_id = NodeId(uuid7())
        item = BinderItem(id=node_id, display_title='Chapter', children=[])

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            item.id = NodeId(uuid7())

        with pytest.raises(AttributeError):
            item.display_title = 'New Title'

        with pytest.raises(AttributeError):
            item.children = []

    def test_equality(self) -> None:
        """BinderItem equality is based on all attributes."""
        node_id1 = NodeId(uuid7())
        node_id2 = NodeId(uuid7())

        item1 = BinderItem(id=node_id1, display_title='Chapter', children=[])
        item2 = BinderItem(id=node_id1, display_title='Chapter', children=[])
        item3 = BinderItem(id=node_id2, display_title='Chapter', children=[])
        item4 = BinderItem(id=node_id1, display_title='Different', children=[])

        assert item1 == item2
        assert item1 != item3  # Different ID
        assert item1 != item4  # Different title

    def test_is_placeholder(self) -> None:
        """is_placeholder correctly identifies placeholders."""
        placeholder = BinderItem(id=None, display_title='Placeholder', children=[])
        concrete = BinderItem(id=NodeId(uuid7()), display_title='Concrete', children=[])

        assert placeholder.is_placeholder() is True
        assert concrete.is_placeholder() is False

    def test_has_children(self) -> None:
        """has_children correctly identifies items with children."""
        parent = BinderItem(
            id=NodeId(uuid7()),
            display_title='Parent',
            children=[BinderItem(id=None, display_title='Child', children=[])],
        )

        leaf = BinderItem(id=NodeId(uuid7()), display_title='Leaf', children=[])

        assert parent.has_children() is True
        assert leaf.has_children() is False

    def test_collect_all_ids(self) -> None:
        """collect_all_ids returns all non-None NodeIds in hierarchy."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())

        root = BinderItem(
            id=id1,
            display_title='Root',
            children=[
                BinderItem(id=id2, display_title='Child 1', children=[]),
                BinderItem(id=None, display_title='Placeholder', children=[]),  # Should be skipped
                BinderItem(
                    id=id3,
                    display_title='Child 2',
                    children=[BinderItem(id=None, display_title='Nested placeholder', children=[])],
                ),
            ],
        )

        all_ids = root.collect_all_ids()

        assert len(all_ids) == 3
        assert id1 in all_ids
        assert id2 in all_ids
        assert id3 in all_ids

    def test_find_by_id(self) -> None:
        """find_by_id locates items in hierarchy."""
        id1 = NodeId(uuid7())
        id2 = NodeId(uuid7())
        id3 = NodeId(uuid7())
        target_id = NodeId(uuid7())

        target_item = BinderItem(id=target_id, display_title='Target', children=[])

        root = BinderItem(
            id=id1,
            display_title='Root',
            children=[
                BinderItem(id=id2, display_title='Child 1', children=[]),
                BinderItem(id=id3, display_title='Child 2', children=[target_item]),
            ],
        )

        found = root.find_by_id(target_id)
        assert found == target_item

        not_found = root.find_by_id(NodeId(uuid7()))
        assert not_found is None

    def test_repr(self) -> None:
        """BinderItem has a useful repr."""
        node_id = NodeId(uuid7())
        item = BinderItem(id=node_id, display_title='Chapter 1', children=[])

        repr_str = repr(item)
        assert 'BinderItem' in repr_str
        assert 'Chapter 1' in repr_str
        assert str(node_id) in repr_str
