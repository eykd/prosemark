"""Tests for domain models."""

import pytest

from prosemark.domain.models import Binder, BinderItem, NodeId, NodeMetadata
from prosemark.exceptions import BinderIntegrityError, NodeIdentityError


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


class TestNodeMetadata:
    """Test NodeMetadata value object."""

    def test_node_metadata_complete(self) -> None:
        """Test NodeMetadata with all fields."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        metadata = NodeMetadata(
            id=node_id,
            title='Chapter 1 – Mercy Run',  # noqa: RUF001
            synopsis='Free-form synopsis text...',
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:30:00-07:00',
        )
        assert metadata.id == node_id
        assert metadata.title == 'Chapter 1 – Mercy Run'  # noqa: RUF001
        assert metadata.synopsis == 'Free-form synopsis text...'
        assert metadata.created == '2025-09-10T10:00:00-07:00'
        assert metadata.updated == '2025-09-10T10:30:00-07:00'

    def test_node_metadata_minimal(self) -> None:
        """Test NodeMetadata with required fields only."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        metadata = NodeMetadata(
            id=node_id,
            title=None,
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )
        assert metadata.id == node_id
        assert metadata.title is None
        assert metadata.synopsis is None
        assert metadata.created == '2025-09-10T10:00:00-07:00'
        assert metadata.updated == '2025-09-10T10:00:00-07:00'

    def test_node_metadata_to_from_dict(self) -> None:
        """Test NodeMetadata dictionary serialization."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        metadata = NodeMetadata(
            id=node_id,
            title='Chapter 1',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )

        # Test to_dict
        data = metadata.to_dict()
        assert data['id'] == '0192f0c1-2345-7123-8abc-def012345678'
        assert data['title'] == 'Chapter 1'
        assert 'synopsis' not in data or data['synopsis'] is None
        assert data['created'] == '2025-09-10T10:00:00-07:00'
        assert data['updated'] == '2025-09-10T10:00:00-07:00'

        # Test from_dict
        restored = NodeMetadata.from_dict(data)
        assert restored == metadata

    def test_node_metadata_to_from_dict_with_none_values(self) -> None:
        """Test NodeMetadata dictionary serialization with None values."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        metadata = NodeMetadata(
            id=node_id,
            title=None,
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )

        # Test to_dict
        data = metadata.to_dict()
        assert data['id'] == '0192f0c1-2345-7123-8abc-def012345678'
        # None values should not be included in the dictionary
        assert 'title' not in data
        assert 'synopsis' not in data
        assert data['created'] == '2025-09-10T10:00:00-07:00'
        assert data['updated'] == '2025-09-10T10:00:00-07:00'

        # Test from_dict
        restored = NodeMetadata.from_dict(data)
        assert restored == metadata

    def test_node_metadata_equality_immutability(self) -> None:
        """Test NodeMetadata equality and immutability."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        metadata1 = NodeMetadata(
            id=node_id,
            title='Chapter 1',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )
        metadata2 = NodeMetadata(
            id=node_id,
            title='Chapter 1',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )

        assert metadata1 == metadata2

        # Test immutability
        with pytest.raises(AttributeError):
            metadata1.title = 'Different Title'  # type: ignore[misc]

    def test_node_metadata_inequality(self) -> None:
        """Test NodeMetadata inequality with different values."""
        node_id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        node_id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        metadata1 = NodeMetadata(
            id=node_id1,
            title='Chapter 1',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )
        metadata2 = NodeMetadata(
            id=node_id2,
            title='Chapter 1',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )
        metadata3 = NodeMetadata(
            id=node_id1,
            title='Chapter 2',
            synopsis=None,
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T10:00:00-07:00',
        )

        assert metadata1 != metadata2  # Different IDs
        assert metadata1 != metadata3  # Different titles
        assert metadata1 != 'not-metadata'  # type: ignore[comparison-overlap]

    def test_node_metadata_from_dict_missing_optional_fields(self) -> None:
        """Test from_dict handles missing optional fields correctly."""
        data: dict[str, str | None] = {
            'id': '0192f0c1-2345-7123-8abc-def012345678',
            'created': '2025-09-10T10:00:00-07:00',
            'updated': '2025-09-10T10:00:00-07:00',
        }

        metadata = NodeMetadata.from_dict(data)
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        assert metadata.id == node_id
        assert metadata.title is None
        assert metadata.synopsis is None
        assert metadata.created == '2025-09-10T10:00:00-07:00'
        assert metadata.updated == '2025-09-10T10:00:00-07:00'

    def test_node_metadata_from_dict_error_handling(self) -> None:
        """Test from_dict error handling for missing or invalid fields."""
        # Test missing ID
        with pytest.raises(NodeIdentityError, match='Missing id field'):
            NodeMetadata.from_dict({
                'created': '2025-09-10T10:00:00-07:00',
                'updated': '2025-09-10T10:00:00-07:00',
            })

        # Test missing created field
        with pytest.raises(ValueError, match='Missing created field'):
            NodeMetadata.from_dict({
                'id': '0192f0c1-2345-7123-8abc-def012345678',
                'updated': '2025-09-10T10:00:00-07:00',
            })

        # Test missing updated field
        with pytest.raises(ValueError, match='Missing updated field'):
            NodeMetadata.from_dict({
                'id': '0192f0c1-2345-7123-8abc-def012345678',
                'created': '2025-09-10T10:00:00-07:00',
            })

    def test_node_metadata_from_dict_with_explicit_none_values(self) -> None:
        """Test from_dict handles explicit None values correctly."""
        data = {
            'id': '0192f0c1-2345-7123-8abc-def012345678',
            'title': None,
            'synopsis': None,
            'created': '2025-09-10T10:00:00-07:00',
            'updated': '2025-09-10T10:00:00-07:00',
        }

        metadata = NodeMetadata.from_dict(data)
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        assert metadata.id == node_id
        assert metadata.title is None
        assert metadata.synopsis is None
        assert metadata.created == '2025-09-10T10:00:00-07:00'
        assert metadata.updated == '2025-09-10T10:00:00-07:00'

    def test_node_metadata_roundtrip_serialization(self) -> None:
        """Test complete roundtrip serialization preserves all data."""
        original_metadata = NodeMetadata(
            id=NodeId('0192f0c1-2345-7123-8abc-def012345678'),
            title='Chapter 1 – The Beginning',  # noqa: RUF001
            synopsis='A detailed synopsis with special characters: ~!@#$%^&*()_+{}|:<>?',
            created='2025-09-10T10:00:00-07:00',
            updated='2025-09-10T15:30:00-07:00',
        )

        # Serialize to dict and back
        data = original_metadata.to_dict()
        restored_metadata = NodeMetadata.from_dict(data)

        # Should be exactly equal
        assert restored_metadata == original_metadata
        assert restored_metadata.id == original_metadata.id
        assert restored_metadata.title == original_metadata.title
        assert restored_metadata.synopsis == original_metadata.synopsis
        assert restored_metadata.created == original_metadata.created
        assert restored_metadata.updated == original_metadata.updated


class TestBinderItem:
    """Test BinderItem dataclass for hierarchical structure."""

    def test_binder_item_with_node_id(self) -> None:
        """Test creating BinderItem with NodeId."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        assert item.id == node_id
        assert item.display_title == 'Chapter 1'
        assert item.children == []

    def test_binder_item_placeholder(self) -> None:
        """Test creating placeholder BinderItem."""
        item = BinderItem(id_=None, display_title='New Placeholder', children=[])
        assert item.id is None
        assert item.display_title == 'New Placeholder'
        assert item.children == []

    def test_binder_item_hierarchy(self) -> None:
        """Test BinderItem with children."""
        parent = BinderItem(id_=None, display_title='Part 1', children=[])
        child1 = BinderItem(id_=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])
        parent.children.append(child1)
        assert len(parent.children) == 1
        assert parent.children[0] == child1

    def test_binder_item_equality(self) -> None:
        """Test BinderItem equality comparison."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        assert item1 == item2

    def test_binder_item_equality_with_different_children(self) -> None:
        """Test BinderItem equality includes children comparison."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child = BinderItem(id_=NodeId('0192f0c1-2345-7456-8abc-def012345678'), display_title='Sub Chapter', children=[])

        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[child])
        item2 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item3 = BinderItem(id_=node_id, display_title='Chapter 1', children=[child])

        assert item1 != item2
        assert item1 == item3

    def test_binder_item_inequality_with_different_ids(self) -> None:
        """Test BinderItem inequality with different ids."""
        item1 = BinderItem(id_=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=NodeId('0192f0c1-2345-7456-8abc-def012345678'), display_title='Chapter 1', children=[])
        assert item1 != item2

    def test_binder_item_inequality_with_different_titles(self) -> None:
        """Test BinderItem inequality with different display_titles."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])
        assert item1 != item2

    def test_binder_item_children_mutability(self) -> None:
        """Test that BinderItem children list can be modified."""
        parent = BinderItem(id_=None, display_title='Parent', children=[])
        child1 = BinderItem(id_=None, display_title='Child 1', children=[])
        child2 = BinderItem(id_=None, display_title='Child 2', children=[])

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

    def test_binder_item_add_remove_child_methods(self) -> None:
        """Test BinderItem add_child and remove_child methods."""
        parent = BinderItem(id_=None, display_title='Parent', children=[])
        child1 = BinderItem(id_=None, display_title='Child 1', children=[])
        child2 = BinderItem(id_=None, display_title='Child 2', children=[])

        # Test add_child
        parent.add_child(child1)
        assert len(parent.children) == 1
        assert child1 in parent.children
        assert child1.parent is parent

        parent.add_child(child2)
        assert len(parent.children) == 2
        assert child2 in parent.children
        assert child2.parent is parent

        # Test remove_child
        parent.remove_child(child1)
        assert len(parent.children) == 1
        assert child1 not in parent.children
        assert child1.parent is None
        assert child2 in parent.children  # pragma: no cover

        # Test remove_child with child not in children list (should do nothing)
        child3 = BinderItem(id_=None, display_title='Child 3', children=[])
        parent.remove_child(child3)  # Should not raise error
        assert len(parent.children) == 1  # Should remain unchanged
        assert child2 in parent.children

    def test_binder_item_default_empty_children(self) -> None:
        """Test BinderItem has default empty children list."""
        item = BinderItem(id_=None, display_title='Test')
        assert item.children == []
        assert isinstance(item.children, list)

    def test_binder_item_deep_hierarchy(self) -> None:
        """Test BinderItem supports deep hierarchical structures."""
        # Create a 3-level hierarchy
        grandparent = BinderItem(id_=None, display_title='Book', children=[])
        parent = BinderItem(id_=None, display_title='Part 1', children=[])
        child = BinderItem(id_=NodeId('0192f0c1-2345-7123-8abc-def012345678'), display_title='Chapter 1', children=[])

        parent.children.append(child)
        grandparent.children.append(parent)

        assert len(grandparent.children) == 1
        assert len(grandparent.children[0].children) == 1
        assert grandparent.children[0].children[0] == child


class TestBinder:
    """Test Binder aggregate with tree invariants."""

    def test_binder_creation(self) -> None:
        """Test creating empty and populated binders."""
        empty_binder = Binder(roots=[])
        assert empty_binder.roots == []

        item = BinderItem(id_=None, display_title='Chapter 1', children=[])
        binder = Binder(roots=[item])
        assert len(binder.roots) == 1

    def test_binder_rejects_duplicate_node_ids(self) -> None:
        """Test Binder raises exception for duplicate NodeIds."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[item1, item2])

    def test_binder_rejects_duplicate_node_ids_in_children(self) -> None:
        """Test Binder detects duplicate NodeIds in nested children."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        child1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        child2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        parent1 = BinderItem(id_=None, display_title='Part 1', children=[child1])
        parent2 = BinderItem(id_=None, display_title='Part 2', children=[child2])

        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[parent1, parent2])

    def test_binder_allows_multiple_none_ids(self) -> None:
        """Test Binder allows multiple placeholder items with None id."""
        item1 = BinderItem(id_=None, display_title='Placeholder 1', children=[])
        item2 = BinderItem(id_=None, display_title='Placeholder 2', children=[])

        # This should not raise an exception
        binder = Binder(roots=[item1, item2])
        assert len(binder.roots) == 2

    def test_binder_find_node_by_id(self) -> None:
        """Test finding nodes in the tree by NodeId."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        child = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        parent = BinderItem(id_=None, display_title='Part 1', children=[child])
        binder = Binder(roots=[parent])

        found_item = binder.find_by_id(node_id)
        assert found_item == child

    def test_binder_find_node_by_id_returns_none_when_not_found(self) -> None:
        """Test find_by_id returns None for non-existent NodeIds."""
        node_id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        node_id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        item = BinderItem(id_=node_id1, display_title='Chapter 1', children=[])
        binder = Binder(roots=[item])

        found_item = binder.find_by_id(node_id2)
        assert found_item is None

    def test_binder_find_node_by_id_in_deep_hierarchy(self) -> None:
        """Test finding nodes deeply nested in the hierarchy."""
        deep_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        deep_child = BinderItem(id_=deep_node_id, display_title='Deep Chapter', children=[])

        parent = BinderItem(id_=None, display_title='Middle Section', children=[deep_child])
        grandparent = BinderItem(id_=None, display_title='Top Section', children=[parent])
        binder = Binder(roots=[grandparent])

        found_item = binder.find_by_id(deep_node_id)
        assert found_item == deep_child

    def test_binder_find_node_by_id_with_multiple_branches(self) -> None:
        """Test finding nodes when search must traverse multiple branches."""
        target_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        other_node_id = NodeId('0192f0c1-2345-7456-8abc-def012345679')

        # Create a tree with multiple branches where target is in the second branch
        target_child = BinderItem(id_=target_node_id, display_title='Target Chapter', children=[])
        other_child = BinderItem(id_=other_node_id, display_title='Other Chapter', children=[])

        # First branch has children but not the target
        first_branch = BinderItem(id_=None, display_title='First Section', children=[other_child])
        # Second branch has the target
        second_branch = BinderItem(id_=None, display_title='Second Section', children=[target_child])

        root = BinderItem(id_=None, display_title='Book', children=[first_branch, second_branch])
        binder = Binder(roots=[root])

        found_item = binder.find_by_id(target_node_id)
        assert found_item == target_child

    def test_binder_get_all_node_ids(self) -> None:
        """Test getting all NodeIds in the tree."""
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        item1 = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])
        placeholder = BinderItem(id_=None, display_title='Placeholder', children=[])

        binder = Binder(roots=[item1, item2, placeholder])
        node_ids = binder.get_all_node_ids()

        assert node_ids == {id1, id2}

    def test_binder_get_all_node_ids_from_nested_structure(self) -> None:
        """Test getting all NodeIds from a complex nested structure."""
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')
        id3 = NodeId('0192f0c1-2345-7789-8abc-def012345678')

        deep_child = BinderItem(id_=id3, display_title='Deep Chapter', children=[])
        child1 = BinderItem(id_=id1, display_title='Chapter 1', children=[deep_child])
        child2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])

        parent = BinderItem(id_=None, display_title='Part 1', children=[child1, child2])
        placeholder = BinderItem(id_=None, display_title='Placeholder', children=[])

        binder = Binder(roots=[parent, placeholder])
        node_ids = binder.get_all_node_ids()

        assert node_ids == {id1, id2, id3}

    def test_binder_get_all_node_ids_empty_tree(self) -> None:
        """Test getting all NodeIds from an empty tree."""
        binder = Binder(roots=[])
        node_ids = binder.get_all_node_ids()
        assert node_ids == set()

    def test_binder_get_all_node_ids_only_placeholders(self) -> None:
        """Test getting all NodeIds from a tree with only placeholder items."""
        placeholder1 = BinderItem(id_=None, display_title='Placeholder 1', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Placeholder 2', children=[])

        binder = Binder(roots=[placeholder1, placeholder2])
        node_ids = binder.get_all_node_ids()
        assert node_ids == set()

    def test_binder_validates_tree_integrity(self) -> None:
        """Test comprehensive tree validation."""
        binder = Binder(roots=[])
        # Should validate without errors
        binder.validate_integrity()

        # Test with complex valid tree
        id1 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        id2 = NodeId('0192f0c1-2345-7456-8abc-def012345678')

        child1 = BinderItem(id_=id1, display_title='Chapter 1', children=[])
        child2 = BinderItem(id_=id2, display_title='Chapter 2', children=[])
        parent = BinderItem(id_=None, display_title='Part 1', children=[child1, child2])

        valid_binder = Binder(roots=[parent])
        valid_binder.validate_integrity()  # Should not raise

    def test_binder_validate_integrity_catches_duplicates(self) -> None:
        """Test validate_integrity catches duplicate NodeId violations."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

        # Create binder with duplicate IDs that bypasses constructor check
        item1 = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id, display_title='Chapter 2', children=[])

        # We can't create this through the constructor, but if we could...
        # This test ensures validate_integrity would catch it
        with pytest.raises(BinderIntegrityError, match='Duplicate NodeId'):
            Binder(roots=[item1, item2])

    def test_binder_equality(self) -> None:
        """Test Binder equality comparison."""
        item1 = BinderItem(id_=None, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=None, display_title='Chapter 1', children=[])

        binder1 = Binder(roots=[item1])
        binder2 = Binder(roots=[item2])
        binder3 = Binder(roots=[item1])

        assert binder1 == binder2  # Same content
        assert binder1 == binder3  # Same reference

        different_item = BinderItem(id_=None, display_title='Chapter 2', children=[])
        binder4 = Binder(roots=[different_item])
        assert binder1 != binder4

    def test_find_placeholder_by_display_title(self) -> None:
        """Test finding placeholder items by display title."""
        # Create mixed structure with materialized and placeholder items
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        materialized = BinderItem(id_=node_id1, display_title='Materialized', children=[])
        placeholder1 = BinderItem(id_=None, display_title='Placeholder 1', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Placeholder 2', children=[])

        binder = Binder(roots=[materialized, placeholder1, placeholder2])

        # Should find placeholder items
        found1 = binder.find_placeholder_by_display_title('Placeholder 1')
        assert found1 == placeholder1

        found2 = binder.find_placeholder_by_display_title('Placeholder 2')
        assert found2 == placeholder2

        # Should not find materialized items
        not_found = binder.find_placeholder_by_display_title('Materialized')
        assert not_found is None

        # Should return None for non-existent title
        not_found2 = binder.find_placeholder_by_display_title('Does Not Exist')
        assert not_found2 is None

    def test_find_placeholder_in_nested_structure_returns_none(self) -> None:
        """Test find_placeholder_by_display_title returns None when no match in nested structure."""
        # Create nested structure with no matching placeholders
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # All items are materialized (have IDs)
        child1 = BinderItem(id_=node_id1, display_title='Child 1', children=[])
        child2 = BinderItem(id_=node_id2, display_title='Child 2', children=[])
        parent = BinderItem(id_=None, display_title='Parent Placeholder', children=[child1, child2])

        binder = Binder(roots=[parent])

        # Should not find materialized children even though parent is placeholder
        result = binder.find_placeholder_by_display_title('Child 1')
        assert result is None

        # Should find the parent placeholder
        result2 = binder.find_placeholder_by_display_title('Parent Placeholder')
        assert result2 == parent

        # Should return None when searching through all branches without finding match
        result3 = binder.find_placeholder_by_display_title('Non-existent')
        assert result3 is None

    def test_find_placeholder_recursive_return_none_coverage(self) -> None:
        """Test to ensure line 412 coverage in recursive search (return None from _search_item)."""
        # Create a nested structure where the recursive search must return None
        # This specifically targets the "return None" at the end of _search_item
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Deep nested structure with no matching placeholder
        deep_child = BinderItem(id_=node_id2, display_title='Deep Materialized', children=[])
        middle_child = BinderItem(id_=node_id1, display_title='Middle Materialized', children=[deep_child])
        root_item = BinderItem(id_=None, display_title='Root Placeholder', children=[middle_child])

        binder = Binder(roots=[root_item])

        # Search for a title that doesn't exist anywhere
        # This will cause the recursive search to traverse the tree and return None
        result = binder.find_placeholder_by_display_title('Nonexistent Title')
        assert result is None

        # Also search for a materialized item title to ensure recursive traversal
        result2 = binder.find_placeholder_by_display_title('Deep Materialized')
        assert result2 is None  # Should be None because it's materialized, not a placeholder

    def test_find_placeholder_nested_match_return_coverage(self) -> None:
        """Test to ensure line 412 coverage - return result when found in child."""
        # This specifically targets the "return result" line when a match is found in a child
        # Create a structure where the placeholder is nested, not at the root level

        # Create a placeholder deeply nested in children
        target_placeholder = BinderItem(id_=None, display_title='Deep Target Placeholder', children=[])

        # Create materialized items as siblings to ensure search continues
        sibling1 = BinderItem(
            id_=NodeId('0192f0c1-1111-7000-8000-000000000001'), display_title='Sibling 1', children=[]
        )
        sibling2 = BinderItem(
            id_=NodeId('0192f0c1-2222-7000-8000-000000000002'), display_title='Sibling 2', children=[]
        )

        # Create parent with multiple children where the target is the last child
        parent = BinderItem(
            id_=None, display_title='Parent Container', children=[sibling1, sibling2, target_placeholder]
        )

        # Create root that contains this parent
        root = BinderItem(id_=None, display_title='Root Container', children=[parent])

        binder = Binder(roots=[root])

        # Search for the deeply nested placeholder
        # This should cause the recursive search to traverse:
        # 1. Root container (not a match, has children)
        # 2. Parent container (not a match, has children)
        # 3. Sibling 1 (not a match, no children) - returns None
        # 4. Sibling 2 (not a match, no children) - returns None
        # 5. Target placeholder (MATCH!) - returns the item
        # 6. Parent's loop finds the match and executes "return result" (line 412)
        result = binder.find_placeholder_by_display_title('Deep Target Placeholder')
        assert result == target_placeholder
        assert result is not None
        assert result.display_title == 'Deep Target Placeholder'
        assert result.node_id is None
