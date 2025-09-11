"""Tests for domain models."""

import pytest

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import NodeIdentityError


class TestNodeId:
    """Test NodeId value object."""

    def test_nodeid_creates_from_valid_uuid7(self) -> None:
        """Test NodeId accepts valid UUIDv7 strings."""
        valid_uuid7 = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(valid_uuid7)
        assert str(node_id) == valid_uuid7

    def test_nodeid_rejects_invalid_uuid(self) -> None:
        """Test NodeId raises exception for invalid UUIDs."""
        with pytest.raises(NodeIdentityError):
            NodeId('not-a-uuid')

    def test_nodeid_equality_and_hashing(self) -> None:
        """Test NodeId equality and hashable behavior."""
        uuid_str = '0192f0c1-2345-7123-8abc-def012345678'
        id1 = NodeId(uuid_str)
        id2 = NodeId(uuid_str)
        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_nodeid_immutability(self) -> None:
        """Test NodeId cannot be modified after creation."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        # Should not have settable attributes
        with pytest.raises(AttributeError):
            node_id.value = 'different-uuid'  # type: ignore[misc]

    def test_nodeid_rejects_non_uuid7_format(self) -> None:
        """Test NodeId rejects UUIDs that aren't version 7."""
        # This is a valid UUID4 but not UUID7
        uuid4 = '550e8400-e29b-41d4-a716-446655440000'
        with pytest.raises(NodeIdentityError):
            NodeId(uuid4)

    def test_nodeid_can_be_used_in_sets(self) -> None:
        """Test NodeId can be used in sets due to being hashable."""
        uuid1 = '0192f0c1-2345-7123-8abc-def012345678'
        uuid2 = '0192f0c1-2345-7456-8abc-def012345678'

        node_id1 = NodeId(uuid1)
        node_id2 = NodeId(uuid2)
        node_id3 = NodeId(uuid1)  # Same as id1

        id_set = {node_id1, node_id2, node_id3}
        assert len(id_set) == 2  # Only two unique IDs

    def test_nodeid_can_be_used_in_dicts(self) -> None:
        """Test NodeId can be used as dictionary keys."""
        uuid1 = '0192f0c1-2345-7123-8abc-def012345678'
        uuid2 = '0192f0c1-2345-7456-8abc-def012345678'

        node_id1 = NodeId(uuid1)
        node_id2 = NodeId(uuid2)

        id_dict = {node_id1: 'value1', node_id2: 'value2'}
        assert len(id_dict) == 2
        assert id_dict[node_id1] == 'value1'
        assert id_dict[node_id2] == 'value2'

    def test_nodeid_string_representation(self) -> None:
        """Test NodeId string representation returns the UUID string."""
        uuid_str = '0192f0c1-2345-7123-8abc-def012345678'
        node_id = NodeId(uuid_str)
        assert str(node_id) == uuid_str
        assert repr(node_id) == f'NodeId({uuid_str!r})'

    def test_nodeid_rejects_empty_string(self) -> None:
        """Test NodeId rejects empty strings."""
        with pytest.raises(NodeIdentityError):
            NodeId('')

    def test_nodeid_rejects_none(self) -> None:
        """Test NodeId rejects None values."""
        with pytest.raises(NodeIdentityError):
            NodeId(None)  # type: ignore[arg-type]

    def test_nodeid_inequality_with_different_types(self) -> None:
        """Test NodeId inequality with non-NodeId objects."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        assert node_id != 'not-a-nodeid'
        assert node_id != 123
        assert node_id != None  # noqa: E711


class TestBinderItem:
    """Test BinderItem dataclass for hierarchical structure."""

    def test_binder_item_with_node_id(self) -> None:
        """Test creating BinderItem with NodeId."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        assert item.id == node_id
        assert item.display_title == 'Chapter 1'
        assert item.children == []

    def test_binder_item_placeholder(self) -> None:
        """Test creating placeholder BinderItem."""
        item = BinderItem(id=None, display_title='New Placeholder', children=[])
        assert item.id is None
        assert item.display_title == 'New Placeholder'
        assert item.children == []

    def test_binder_item_hierarchy(self) -> None:
        """Test BinderItem with children."""
        parent = BinderItem(id=None, display_title='Part 1', children=[])
        child1 = BinderItem(id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])
        parent.children.append(child1)
        assert len(parent.children) == 1
        assert parent.children[0] == child1

    def test_binder_item_equality(self) -> None:
        """Test BinderItem equality comparison."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        assert item1 == item2

    def test_binder_item_equality_with_different_children(self) -> None:
        """Test BinderItem equality includes children comparison."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child = BinderItem(id=NodeId('0192f0c1-2345-7456-8abc-def012345678'), display_title='Sub Chapter', children=[])

        item1 = BinderItem(id=node_id, display_title='Chapter 1', children=[child])
        item2 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        item3 = BinderItem(id=node_id, display_title='Chapter 1', children=[child])

        assert item1 != item2
        assert item1 == item3

    def test_binder_item_inequality_with_different_ids(self) -> None:
        """Test BinderItem inequality with different ids."""
        item1 = BinderItem(id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])
        item2 = BinderItem(id=NodeId('0192f0c1-2345-7456-8abc-def012345678'), display_title='Chapter 1', children=[])
        assert item1 != item2

    def test_binder_item_inequality_with_different_titles(self) -> None:
        """Test BinderItem inequality with different display_titles."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id=node_id, display_title='Chapter 2', children=[])
        assert item1 != item2

    def test_binder_item_children_mutability(self) -> None:
        """Test that BinderItem children list can be modified."""
        parent = BinderItem(id=None, display_title='Parent', children=[])
        child1 = BinderItem(id=None, display_title='Child 1', children=[])
        child2 = BinderItem(id=None, display_title='Child 2', children=[])

        # Test appending children
        parent.children.append(child1)
        parent.children.append(child2)
        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2

        # Test removing children
        parent.children.remove(child1)
        assert len(parent.children) == 1
        assert parent.children[0] == child2

    def test_binder_item_default_empty_children(self) -> None:
        """Test BinderItem has default empty children list."""
        item = BinderItem(id=None, display_title='Test')
        assert item.children == []
        assert isinstance(item.children, list)

    def test_binder_item_deep_hierarchy(self) -> None:
        """Test BinderItem supports deep hierarchical structures."""
        # Create a 3-level hierarchy
        grandparent = BinderItem(id=None, display_title='Book', children=[])
        parent = BinderItem(id=None, display_title='Part 1', children=[])
        child = BinderItem(id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])

        parent.children.append(child)
        grandparent.children.append(parent)

        assert len(grandparent.children) == 1
        assert len(grandparent.children[0].children) == 1
        assert grandparent.children[0].children[0] == child
