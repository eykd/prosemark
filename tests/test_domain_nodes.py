from __future__ import annotations

import uuid

from prosemark.domain.nodes import Node


def test_node_initialization() -> None:
    """Test that a Node can be initialized with default and custom values."""
    # Test with default values
    node1 = Node()
    assert isinstance(node1.id, str)
    assert node1.title == ''
    assert node1.notecard == ''
    assert node1.content == ''
    assert node1.notes == ''
    assert node1.metadata == {}
    assert node1.parent is None
    assert node1.children == []

    # Test with custom values
    custom_id = str(uuid.uuid4())
    metadata = {'key1': 'value1', 'key2': 42}
    parent_node = Node()
    child_node = Node()

    node2 = Node(
        id=custom_id,
        title='Test Title',
        notecard='Test Notecard',
        content='Test Content',
        notes='Test Notes',
        metadata=metadata,
        parent=parent_node,
        children=[child_node],
    )

    assert node2.id == custom_id
    assert node2.title == 'Test Title'
    assert node2.notecard == 'Test Notecard'
    assert node2.content == 'Test Content'
    assert node2.notes == 'Test Notes'
    assert node2.metadata == metadata
    assert node2.parent is parent_node
    assert node2.children == [child_node]
    assert child_node.parent is node2  # Child's parent should be set


def test_add_child() -> None:
    """Test adding a child node."""
    parent = Node(title='Parent')
    child = Node(title='Child')

    # Add child at the end
    parent.add_child(child)
    assert child in parent.children
    assert child.parent is parent
    assert len(parent.children) == 1

    # Add child at specific position
    another_child = Node(title='Another Child')
    parent.add_child(another_child, position=0)
    assert parent.children[0] is another_child
    assert parent.children[1] is child
    assert another_child.parent is parent
    assert len(parent.children) == 2


def test_remove_child() -> None:
    """Test removing a child node."""
    parent = Node(title='Parent')
    child1 = Node(title='Child 1')
    child2 = Node(title='Child 2')

    parent.add_child(child1)
    parent.add_child(child2)

    # Remove by node reference
    removed = parent.remove_child(child1)
    assert removed is child1
    assert child1 not in parent.children
    assert child1.parent is None
    assert len(parent.children) == 1

    # Remove by node ID
    removed = parent.remove_child(child2.id)
    assert removed is child2
    assert child2 not in parent.children
    assert child2.parent is None
    assert len(parent.children) == 0

    # Try to remove non-existent child
    non_existent = Node(title='Non-existent')
    removed = parent.remove_child(non_existent)
    assert removed is None

    # Try to remove by non-existent ID
    removed = parent.remove_child('non-existent-id')
    assert removed is None


def test_get_child_by_id() -> None:
    """Test retrieving a child node by ID."""
    parent = Node(title='Parent')
    child1 = Node(title='Child 1')
    child2 = Node(title='Child 2')

    parent.add_child(child1)
    parent.add_child(child2)

    # Get existing child
    found = parent.get_child_by_id(child1.id)
    assert found is child1

    # Try to get non-existent child
    not_found = parent.get_child_by_id('non-existent-id')
    assert not_found is None


def test_get_descendants() -> None:
    """Test retrieving all descendant nodes."""
    root = Node(title='Root')
    child1 = Node(title='Child 1')
    child2 = Node(title='Child 2')
    grandchild1 = Node(title='Grandchild 1')
    grandchild2 = Node(title='Grandchild 2')

    root.add_child(child1)
    root.add_child(child2)
    child1.add_child(grandchild1)
    child2.add_child(grandchild2)

    descendants = root.get_descendants()
    assert len(descendants) == 4
    assert child1 in descendants
    assert child2 in descendants
    assert grandchild1 in descendants
    assert grandchild2 in descendants

    # Test with a leaf node
    leaf_descendants = grandchild1.get_descendants()
    assert len(leaf_descendants) == 0


def test_get_ancestors() -> None:
    """Test retrieving all ancestor nodes."""
    root = Node(title='Root')
    child = Node(title='Child')
    grandchild = Node(title='Grandchild')

    root.add_child(child)
    child.add_child(grandchild)

    ancestors = grandchild.get_ancestors()
    assert len(ancestors) == 2
    assert child in ancestors
    assert root in ancestors

    # Test with a root node
    root_ancestors = root.get_ancestors()
    assert len(root_ancestors) == 0


def test_move_child() -> None:
    """Test moving a child node to a new position."""
    parent = Node(title='Parent')
    child1 = Node(title='Child 1')
    child2 = Node(title='Child 2')
    child3 = Node(title='Child 3')

    parent.add_child(child1)
    parent.add_child(child2)
    parent.add_child(child3)

    # Move by node reference
    result = parent.move_child(child3, 0)
    assert result is True
    assert parent.children[0] is child3
    assert parent.children[1] is child1
    assert parent.children[2] is child2

    # Move by node ID
    result = parent.move_child(child1.id, 2)
    assert result is True
    assert parent.children[0] is child3
    assert parent.children[1] is child2
    assert parent.children[2] is child1

    # Try to move non-existent child
    non_existent = Node(title='Non-existent')
    result = parent.move_child(non_existent, 0)
    assert result is False

    # Try to move by non-existent ID
    result = parent.move_child('non-existent-id', 0)
    assert result is False

    # Try to move to invalid position
    result = parent.move_child(child1, 10)
    assert result is False
