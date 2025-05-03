"""Tests for the Project class."""

from __future__ import annotations

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project


def test_project_initialization() -> None:
    """Test that a Project can be initialized with default and custom values."""
    # Test with default values
    project1 = Project(name='Test Project')
    assert project1.name == 'Test Project'
    assert project1.description == ''
    assert project1.root_node is not None
    assert project1.root_node.title == 'Test Project'
    assert project1.metadata == {}

    # Test with custom values
    root_node = Node(title='Custom Root')
    metadata = {'author': 'Test Author', 'version': '1.0'}

    project2 = Project(
        name='Custom Project',
        description='A test project',
        root_node=root_node,
        metadata=metadata,
    )

    assert project2.name == 'Custom Project'
    assert project2.description == 'A test project'
    assert project2.root_node is root_node
    assert project2.metadata == metadata


def test_get_node_by_id() -> None:
    """Test retrieving a node by ID."""
    project = Project(name='Test Project')

    # Root node should be retrievable
    root_id = project.root_node.id
    assert project.get_node_by_id(root_id) is project.root_node

    # Add some nodes
    child1 = project.create_node(project.root_node.id, title='Child 1')
    assert child1 is not None  # Type assertion for mypy
    child2 = project.create_node(project.root_node.id, title='Child 2')
    assert child2 is not None  # Type assertion for mypy
    grandchild = project.create_node(child1.id, title='Grandchild')
    assert grandchild is not None  # Type assertion for mypy

    # Test retrieving nodes
    assert project.get_node_by_id(child1.id) is child1
    assert project.get_node_by_id(child2.id) is child2
    assert project.get_node_by_id(grandchild.id) is grandchild

    # Test retrieving non-existent node
    assert project.get_node_by_id('non-existent-id') is None


def test_create_node() -> None:
    """Test creating a new node."""
    project = Project(name='Test Project')
    root_id = project.root_node.id

    # Create node with minimal parameters
    node1 = project.create_node(root_id, title='Node 1')
    assert node1 is not None
    assert node1.title == 'Node 1'
    assert node1.parent is project.root_node
    assert node1 in project.root_node.children

    # Create node with all parameters
    metadata = {'key': 'value'}
    node2 = project.create_node(
        root_id,
        title='Node 2',
        notecard='Test notecard',
        content='Test content',
        notes='Test notes',
        metadata=metadata,
        position=0,
    )

    assert node2 is not None
    assert node2.title == 'Node 2'
    assert node2.notecard == 'Test notecard'
    assert node2.content == 'Test content'
    assert node2.notes == 'Test notes'
    assert node2.metadata == metadata
    assert node2.parent is project.root_node
    assert project.root_node.children[0] is node2

    # Create node with non-existent parent
    node3 = project.create_node('non-existent-id', title='Node 3')
    assert node3 is None


def test_move_node() -> None:
    """Test moving a node to a new parent."""
    project = Project(name='Test Project')
    root_id = project.root_node.id

    # Create some nodes
    folder1 = project.create_node(root_id, title='Folder 1')
    assert folder1 is not None  # Type assertion for mypy
    folder2 = project.create_node(root_id, title='Folder 2')
    assert folder2 is not None  # Type assertion for mypy
    node1 = project.create_node(folder1.id, title='Node 1')
    assert node1 is not None  # Type assertion for mypy

    # Move node to another parent
    result = project.move_node(node1.id, folder2.id)
    assert result is True
    assert node1.parent is folder2
    assert node1 in folder2.children
    assert node1 not in folder1.children

    # Move node to specific position
    node2 = project.create_node(folder2.id, title='Node 2')
    assert node2 is not None  # Type assertion for mypy
    result = project.move_node(node1.id, folder2.id, 0)
    assert result is True
    assert folder2.children[0] is node1
    assert folder2.children[1] is node2

    # Try to move root node
    result = project.move_node(root_id, folder1.id)
    assert result is False

    # Try to move to non-existent parent
    result = project.move_node(node1.id, 'non-existent-id')
    assert result is False

    # Try to move non-existent node
    result = project.move_node('non-existent-id', folder1.id)
    assert result is False

    # Try to create circular reference
    subfolder = project.create_node(folder2.id, title='Subfolder')
    assert subfolder is not None  # Type assertion for mypy
    result = project.move_node(folder2.id, subfolder.id)
    assert result is False


def test_remove_node() -> None:
    """Test removing a node from the project."""
    project = Project(name='Test Project')
    root_id = project.root_node.id

    # Create some nodes
    node1 = project.create_node(root_id, title='Node 1')
    assert node1 is not None  # Type assertion for mypy
    node2 = project.create_node(root_id, title='Node 2')
    assert node2 is not None  # Type assertion for mypy
    child = project.create_node(node1.id, title='Child')
    assert child is not None  # Type assertion for mypy

    # Remove a node
    removed = project.remove_node(node1.id)
    assert removed is node1
    assert node1 not in project.root_node.children
    assert child.parent is None

    # Try to remove root node
    removed = project.remove_node(root_id)
    assert removed is None

    # Try to remove non-existent node
    removed = project.remove_node('non-existent-id')
    assert removed is None


def test_get_node_count() -> None:
    """Test counting the nodes in a project."""
    project = Project(name='Test Project')

    # Initially just the root node
    assert project.get_node_count() == 1

    # Add some nodes
    node1 = project.create_node(project.root_node.id, title='Node 1')
    assert node1 is not None  # Type assertion for mypy
    project.create_node(project.root_node.id, title='Node 2')
    project.create_node(node1.id, title='Child 1')
    project.create_node(node1.id, title='Child 2')

    assert project.get_node_count() == 5

    # Remove a node with children
    project.remove_node(node1.id)
    assert project.get_node_count() == 2


def test_get_structure() -> None:
    """Test getting the structure representation of a project."""
    project = Project(name='Test Project')

    # Create a simple structure
    node1 = project.create_node(project.root_node.id, title='Chapter 1')
    assert node1 is not None  # Type assertion for mypy
    node2 = project.create_node(project.root_node.id, title='Chapter 2')
    assert node2 is not None  # Type assertion for mypy
    project.create_node(node1.id, title='Scene 1')
    project.create_node(node1.id, title='Scene 2')
    project.create_node(node2.id, title='Scene 1')

    structure = project.get_structure()

    # Check the structure format
    assert len(structure) == 1  # Root node
    assert structure[0]['id'] == project.root_node.id
    assert structure[0]['title'] == 'Test Project'
    assert len(structure[0]['children']) == 2  # Two chapters

    # Check first chapter
    chapter1 = next(c for c in structure[0]['children'] if c['title'] == 'Chapter 1')
    assert chapter1['id'] == node1.id
    assert len(chapter1['children']) == 2  # Two scenes

    # Check second chapter
    chapter2 = next(c for c in structure[0]['children'] if c['title'] == 'Chapter 2')
    assert chapter2['id'] == node2.id
    assert len(chapter2['children']) == 1  # One scene


def test_move_node_with_circular_reference() -> None:
    """Test that moving a node to its own descendant fails."""
    project = Project(name='Test Project')
    root_id = project.root_node.id

    # Create a hierarchy
    folder1 = project.create_node(root_id, title='Folder 1')
    assert folder1 is not None  # Type assertion for mypy
    subfolder1 = project.create_node(folder1.id, title='Subfolder 1')
    assert subfolder1 is not None  # Type assertion for mypy

    # Try to move a parent to its own child (which would create a circular reference)
    result = project.move_node(folder1.id, subfolder1.id)
    assert result is False

    # Verify the structure remains unchanged
    assert folder1.parent is project.root_node
    assert subfolder1.parent is folder1


def test_build_structure_with_empty_node() -> None:
    """Test building structure with a node that has no children."""
    project = Project(name='Test Project')

    # Create a node with no children
    leaf_node = project.create_node(project.root_node.id, title='Leaf Node')
    assert leaf_node is not None  # Type assertion for mypy

    # Get the structure
    structure = project.get_structure()

    # Verify the structure
    assert len(structure) == 1  # Root node
    assert structure[0]['id'] == project.root_node.id
    assert len(structure[0]['children']) == 1  # One leaf node

    # Verify the leaf node has an empty children list
    leaf = structure[0]['children'][0]
    assert leaf['id'] == leaf_node.id
    assert leaf['title'] == 'Leaf Node'
    assert leaf['children'] == []  # Empty children list
